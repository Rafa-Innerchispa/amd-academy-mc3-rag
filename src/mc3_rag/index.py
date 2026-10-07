from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

from .models import Chunk

TOKEN_RE = re.compile(r"[A-Za-z0-9_./:-]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


class LexicalIndex:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = list(chunks)
        self._tokens = [Counter(tokenize(chunk.text)) for chunk in self.chunks]
        self._document_frequency: Counter[str] = Counter()
        for counts in self._tokens:
            self._document_frequency.update(counts.keys())

    def search(self, query: str, k: int = 5) -> list[tuple[Chunk, float]]:
        terms = tokenize(query)
        if not terms or not self.chunks:
            return []

        n_docs = len(self.chunks)
        scored: list[tuple[Chunk, float]] = []
        for chunk, counts in zip(self.chunks, self._tokens):
            score = 0.0
            for term in terms:
                tf = counts.get(term, 0)
                if not tf:
                    continue
                df = self._document_frequency.get(term, 0)
                idf = math.log((n_docs + 1) / (df + 1)) + 1.0
                score += (1.0 + math.log(tf)) * idf
            if score > 0:
                scored.append((chunk, score))

        scored.sort(key=lambda item: (-item[1], item[0].source, item[0].start_line))
        return scored[: max(1, int(k))]

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": "amd-academy-mc3.lexical-index.v1",
            "chunks": [chunk.to_dict() for chunk in self.chunks],
        }
        target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "LexicalIndex":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("schema") != "amd-academy-mc3.lexical-index.v1":
            raise ValueError("unsupported_index_schema")
        return cls([Chunk.from_dict(row) for row in payload.get("chunks", [])])
