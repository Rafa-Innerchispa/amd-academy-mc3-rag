from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    source: str
    start_line: int
    end_line: int
    text: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Chunk":
        return cls(**data)


@dataclass(frozen=True)
class Citation:
    source: str
    start_line: int
    end_line: int
    chunk_id: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class QueryResult:
    answer: str
    citations: list[Citation]
    matched_chunks: list[str]
    grounded: bool

    def to_dict(self) -> dict:
        return {
            "answer": self.answer,
            "citations": [c.to_dict() for c in self.citations],
            "matched_chunks": list(self.matched_chunks),
            "grounded": self.grounded,
        }
