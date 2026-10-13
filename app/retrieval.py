from __future__ import annotations

import math
import re
from collections import Counter

TOKEN_RE = re.compile(r"[A-Za-z0-9_#.+:/-]+")
IDENT_RE = re.compile(
    r"\b(?:[A-Z]{2,}[A-Z0-9_-]*[-#]?[0-9]{2,}|"
    r"[A-Z]+[0-9]{3,}|[A-Z]{2,}-[0-9]{2,})\b"
)

VERSION_RE = re.compile(r"\b\d+\.\d+(?:\.\d+){0,2}\b")
QUARTER_RE = re.compile(r"\bQ[1-4]\s*FY\s*\d{2,4}\b", re.I)
PART_RE = re.compile(r"\b[A-Z]{2,}[A-Z0-9]*(?:-[A-Z0-9]+){2,}\b")
ERROR_RE = re.compile(r"\bE\d{3,6}\b", re.I)
REVISION_RE = re.compile(r"\bREV(?:ISION)?[-_ ]?[A-Z0-9][A-Z0-9._-]*\b", re.I)
PIN_RE = re.compile(r"\b[A-Z]{1,3}\d{1,3}\b")
NUMBER_RE = re.compile(r"(?<![A-Za-z0-9])[-+]?\d+(?:\.\d+)?(?![A-Za-z0-9])")


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

    bridge_parent: dict[str, str] = {}
    for doc in direct[:4]:
        for ident in identifiers(doc["text"]):
            bridge_parent.setdefault(ident, doc["source"])

    seen = {(doc["source"], doc["chunk_id"]) for doc in direct}
    hops: list[tuple[float, dict]] = []

    for doc in index:
        key = (doc["source"], doc["chunk_id"])
        if key in seen:
            continue
        shared = identifiers(doc["text"]) & bridge_parent.keys()
        if not shared:
            continue

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
    needle = _normalize_value(answer.strip())
    if not needle:
        return []

    candidates: list[dict] = []
    for item in results:
        if needle in _normalize_value(str(item.get("text") or "")):
            candidates.append(item)
    if not candidates:
        return []

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


def _question_pattern(question: str) -> re.Pattern[str] | None:
    q = question.lower()
    if any(term in q for term in ("quarter", "fiscal", "roadmap")):
        return QUARTER_RE
    if "part number" in q or "part-number" in q or "sku" in q:
        return PART_RE
    if any(term in q for term in ("firmware", "version", "release")):
        return VERSION_RE
    if "error code" in q or "failure code" in q:
        return ERROR_RE
    if "revision" in q or "board rev" in q:
        return REVISION_RE
    if "pin" in q:
        return PIN_RE
    if any(
        term in q
        for term in (
            "maximum",
            "minimum",
            "temperature",
            "voltage",
            "current",
            "default",
            "constant",
            "timeout",
            "limit",
            "speed",
        )
    ):
        return NUMBER_RE
    return None


def canonicalize_answer(question: str, raw_answer: str) -> str:
    answer = (raw_answer or "").strip().strip(chr(96)).strip()
    if not answer:
        return ""
    pattern = _question_pattern(question)
    if pattern is None:
        return answer

    match = pattern.search(answer)
    if not match:
        return answer

    value = match.group(0).strip()
    if pattern is QUARTER_RE:
        value = re.sub(r"\s+", " ", value.upper())
    elif pattern in (ERROR_RE, REVISION_RE, PIN_RE, PART_RE):
        value = value.upper().replace("_", "-")
    return value


def fallback_answer_from_results(question: str, results: list[dict]) -> str:
    pattern = _question_pattern(question)
    if pattern is None:
        return ""

    for item in results:
        text = str(item.get("text") or "")
        match = pattern.search(text)
        if not match:
            continue
        value = canonicalize_answer(question, match.group(0))
        if value and citations_for_answer(results, value):
            return value
    return ""


def minimal_citations(results: list[dict], answer: str) -> list[str]:
    return citations_for_answer(results, answer)
