from __future__ import annotations

import math
import re
from collections import Counter

TOKEN_RE = re.compile(r"[A-Za-z0-9_#.+:/-]+")
IDENT_RE = re.compile(
    r"\b(?:[A-Z]{2,}[A-Z0-9_-]*[-#]?[0-9]{2,}|"
    r"[A-Z]+[0-9]{3,}|[A-Z]{2,}-[0-9]{2,})\b"
)


def tokenize(text: str) -> list[str]:
    return [m.group(0).lower() for m in TOKEN_RE.finditer(text)]


def identifiers(text: str) -> set[str]:
    return {m.group(0).lower() for m in IDENT_RE.finditer(text)}


def _idf(index: list[dict], term: str) -> float:
    n = max(1, len(index))
    df = sum(1 for doc in index if term in set(tokenize(doc["text"])))
    return math.log(1.0 + (n - df + 0.5) / (df + 0.5))


def _lexical_score(index: list[dict], doc: dict, q_counts: Counter) -> float:
    counts = Counter(tokenize(doc["text"]))
    score = 0.0
    for term, qtf in q_counts.items():
        tf = counts.get(term, 0)
        if tf:
            score += (1.0 + math.log(tf)) * _idf(index, term) * qtf
    return score


def rank(index: list[dict], query: str, limit: int = 8) -> list[dict]:
    """Return direct lexical hits plus deterministic identifier-linked hops.

    A critical property of the second pass is that it scans the *entire* index,
    not only documents that matched the original natural-language query. This
    lets a log expose E7731 and a CSV containing only E7731|4.3.2 enter the
    context even when the CSV has zero lexical overlap with the user's words.
    """
    if not index:
        return []

    q_counts = Counter(tokenize(query))
    q_ids = identifiers(query)
    scored: list[tuple[float, dict]] = []

    for doc in index:
        score = _lexical_score(index, doc, q_counts)
        doc_ids = identifiers(doc["text"])
        score += 4.0 * len(q_ids & doc_ids)
        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda item: item[0], reverse=True)

    # Preserve source diversity so one long file does not consume the complete
    # retrieval budget with adjacent chunks.
    direct: list[dict] = []
    per_source: Counter = Counter()
    for score, doc in scored:
        source = doc["source"]
        if per_source[source] >= 2:
            continue
        direct.append(
            dict(
                doc,
                score=score,
                retrieval_kind="direct",
                via_identifier=None,
                via_source=None,
            )
        )
        per_source[source] += 1
        if len(direct) >= limit:
            break

    if not direct:
        return []

    # Build the bridge from rare identifiers found in the strongest direct
    # evidence. Parent ordering matters: first source is the best lexical hit.
    bridge_parent: dict[str, str] = {}
    for doc in direct[:4]:
        for ident in identifiers(doc["text"]):
            bridge_parent.setdefault(ident, doc["source"])

    seen = {(doc["source"], doc["chunk_id"]) for doc in direct}
    hops: list[tuple[float, dict]] = []

    # IMPORTANT: scan every indexed document. A second-hop document may have
    # zero lexical overlap with the original question.
    for doc in index:
        key = (doc["source"], doc["chunk_id"])
        if key in seen:
            continue
        shared = identifiers(doc["text"]) & bridge_parent.keys()
        if not shared:
            continue

        # Prefer the identifier whose parent appears earliest in direct hits,
        # then use lexical score only as a tie-breaker.
        best_ident = min(
            shared,
            key=lambda ident: next(
                (
                    idx
                    for idx, parent in enumerate(direct[:4])
                    if parent["source"] == bridge_parent[ident]
                ),
                999,
            ),
        )
        hop_score = 6.0 + 2.0 * len(shared) + _lexical_score(index, doc, q_counts)
        hops.append(
            (
                hop_score,
                dict(
                    doc,
                    score=hop_score,
                    retrieval_kind="hop",
                    via_identifier=best_ident,
                    via_source=bridge_parent[best_ident],
                ),
            )
        )

    hops.sort(key=lambda item: item[0], reverse=True)
    results = list(direct)
    hop_sources: Counter = Counter()
    for _, hop in hops:
        source = hop["source"]
        if hop_sources[source] >= 2:
            continue
        results.append(hop)
        hop_sources[source] += 1
        if len(results) >= limit + 4:
            break
    return results


def _normalize_value(value: str) -> str:
    return "".join(ch for ch in value.upper() if ch not in " \t\r\n-.·_")


def citations_for_answer(results: list[dict], answer: str) -> list[str]:
    """Derive the minimum evidence set for a verbatim-supported answer.

    Direct answer evidence needs one file. If the answer lives in a deterministic
    second-hop result, include exactly the bridge source plus the answer source.
    This is intentionally stricter than trusting an LLM-generated citation list.
    """
    needle = _normalize_value(answer.strip())
    if not needle:
        return []

    candidates: list[dict] = []
    for item in results:
        if needle in _normalize_value(str(item.get("text") or "")):
            candidates.append(item)
    if not candidates:
        return []

    # Prefer a direct source whenever it alone contains the answer.
    direct = next(
        (item for item in candidates if item.get("retrieval_kind") == "direct"),
        None,
    )
    if direct:
        return [direct["source"]]

    hop = candidates[0]
    parent = str(hop.get("via_source") or "").strip()
    source = str(hop.get("source") or "").strip()
    if parent and source and parent != source:
        return [parent, source]
    return [source] if source else []


def minimal_citations(results: list[dict], answer: str) -> list[str]:
    # Backwards-compatible alias used by earlier tests/callers.
    return citations_for_answer(results, answer)
