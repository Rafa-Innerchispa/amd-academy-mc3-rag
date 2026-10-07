from __future__ import annotations

from .index import LexicalIndex
from .models import Citation, QueryResult


def answer_query(index: LexicalIndex, question: str, *, k: int = 3) -> QueryResult:
    hits = index.search(question, k=k)
    if not hits:
        return QueryResult(
            answer="",
            citations=[],
            matched_chunks=[],
            grounded=False,
        )

    best_chunk, _score = hits[0]
    citations = [
        Citation(
            source=chunk.source,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
            chunk_id=chunk.chunk_id,
        )
        for chunk, _ in hits
    ]

    # Baseline is deliberately extractive and fail-closed. A ROCm model-serving
    # generator can replace this stage later, but only if it consumes the same
    # retrieved chunks and preserves citation/provenance contracts.
    return QueryResult(
        answer=best_chunk.text,
        citations=citations,
        matched_chunks=[chunk.chunk_id for chunk, _ in hits],
        grounded=True,
    )
