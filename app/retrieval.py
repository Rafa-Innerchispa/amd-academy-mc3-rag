from __future__ import annotations

import math
import re
from collections import Counter

TOKEN_RE = re.compile(r"[A-Za-z0-9_#.+:/-]+")
IDENT_RE = re.compile(r"\b(?:[A-Z]{2,}[A-Z0-9_-]*[-#]?[0-9]{2,}|[A-Z]+[0-9]{3,}|[A-Z]{2,}-[0-9]{2,})\b")


def tokenize(text: str) -> list[str]:
    return [m.group(0).lower() for m in TOKEN_RE.finditer(text)]


def identifiers(text: str) -> set[str]:
    return {m.group(0).lower() for m in IDENT_RE.finditer(text)}


def _idf(index: list[dict], term: str) -> float:
    n = max(1, len(index))
    df = sum(1 for doc in index if term in set(tokenize(doc["text"])))
    return math.log(1.0 + (n - df + 0.5) / (df + 0.5))


def rank(index: list[dict], query: str, limit: int = 8) -> list[dict]:
    if not index:
        return []
    q_tokens = tokenize(query)
    q_counts = Counter(q_tokens)
    q_ids = identifiers(query)
    scored: list[tuple[float, dict]] = []

    for doc in index:
        tokens = tokenize(doc["text"])
        counts = Counter(tokens)
        score = 0.0
        for term, qtf in q_counts.items():
            tf = counts.get(term, 0)
            if tf:
                score += (1.0 + math.log(tf)) * _idf(index, term) * qtf
        doc_ids = identifiers(doc["text"])
        score += 4.0 * len(q_ids & doc_ids)
        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    first = [dict(doc, score=score) for score, doc in scored[:limit]]

    # One deterministic multi-hop expansion: identifiers discovered in the best
    # chunks can pull in a second file that defines the same rare identifier.
    discovered = set()
    for doc in first[:3]:
        discovered |= identifiers(doc["text"])
    seen = {(d["source"], d["chunk_id"]) for d in first}
    for score, doc in scored[limit:]:
        key = (doc["source"], doc["chunk_id"])
        if key in seen:
            continue
        if discovered & identifiers(doc["text"]):
            first.append(dict(doc, score=score + 2.0))
            seen.add(key)
        if len(first) >= limit + 4:
            break
    return first


def minimal_citations(results: list[dict], answer: str) -> list[str]:
    if not answer:
        return []
    needle = answer.strip().lower()
    direct = []
    for item in results:
        if needle and needle in item["text"].lower():
            direct.append(item["source"])
    if direct:
        return list(dict.fromkeys(direct[:2]))
    return []
