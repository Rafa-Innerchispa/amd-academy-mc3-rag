from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import Chunk

TEXT_EXTENSIONS = {
    ".txt", ".md", ".log", ".py", ".js", ".ts", ".tsx", ".jsx",
    ".json", ".yaml", ".yml", ".csv", ".toml", ".ini", ".cfg",
}


@dataclass(frozen=True)
class IngestIssue:
    source: str
    reason: str


@dataclass(frozen=True)
class IngestReport:
    chunks: list[Chunk]
    skipped: list[IngestIssue]
    withdrawn: list[str]


def _chunk_lines(source: str, lines: list[str], max_chars: int = 1200) -> list[Chunk]:
    chunks: list[Chunk] = []
    current: list[str] = []
    start_line = 1
    current_chars = 0

    def flush(end_line: int) -> None:
        nonlocal current, start_line, current_chars
        text = "\n".join(current).strip()
        if text:
            chunk_id = f"{source}#L{start_line}-L{end_line}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    source=source,
                    start_line=start_line,
                    end_line=end_line,
                    text=text,
                )
            )
        current = []
        current_chars = 0

    for line_no, line in enumerate(lines, start=1):
        line = line.rstrip("\n")
        projected = current_chars + len(line) + (1 if current else 0)
        if current and projected > max_chars:
            flush(line_no - 1)
            start_line = line_no
        current.append(line)
        current_chars += len(line) + (1 if current_chars else 0)

    if current:
        flush(len(lines))
    return chunks


def ingest_corpus(
    root: str | Path,
    *,
    withdrawn: set[str] | None = None,
    max_chars: int = 1200,
) -> IngestReport:
    base = Path(root)
    withdrawn = {Path(p).as_posix() for p in (withdrawn or set())}
    chunks: list[Chunk] = []
    skipped: list[IngestIssue] = []
    withdrawn_hits: list[str] = []

    if not base.exists() or not base.is_dir():
        return IngestReport(
            chunks=[],
            skipped=[IngestIssue(source=str(base), reason="corpus_root_unavailable")],
            withdrawn=[],
        )

    for path in sorted(p for p in base.rglob("*") if p.is_file()):
        relative = path.relative_to(base).as_posix()
        if relative in withdrawn:
            withdrawn_hits.append(relative)
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            skipped.append(IngestIssue(source=relative, reason="unsupported_filetype"))
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            skipped.append(IngestIssue(source=relative, reason=f"unreadable:{type(exc).__name__}"))
            continue

        lines = text.splitlines()
        chunks.extend(_chunk_lines(relative, lines, max_chars=max_chars))

    return IngestReport(
        chunks=chunks,
        skipped=skipped,
        withdrawn=sorted(withdrawn_hits),
    )
