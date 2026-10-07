from __future__ import annotations

from pathlib import Path

from mc3_rag import LexicalIndex, answer_query, ingest_corpus


def test_grounded_answer_has_exact_file_and_line_citation(tmp_path: Path) -> None:
    (tmp_path / "network.txt").write_text(
        "Bellini core switch is managed.\n"
        "The uplink uses SFP1.\n"
        "The fallback path is copper.\n",
        encoding="utf-8",
    )
    report = ingest_corpus(tmp_path)
    index = LexicalIndex(report.chunks)
    result = answer_query(index, "Which uplink uses SFP1?")

    assert result.grounded is True
    assert result.citations
    assert result.citations[0].source == "network.txt"
    assert result.citations[0].start_line == 1
    assert result.citations[0].end_line == 3
    assert "SFP1" in result.answer


def test_unanswerable_query_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "facts.txt").write_text("R9700 uses gfx1201.\n", encoding="utf-8")
    result = answer_query(LexicalIndex(ingest_corpus(tmp_path).chunks), "What is the moon made of?")

    assert result.grounded is False
    assert result.answer == ""
    assert result.citations == []


def test_withdrawn_document_never_reaches_index(tmp_path: Path) -> None:
    (tmp_path / "active.txt").write_text("Active policy allows local inference.\n", encoding="utf-8")
    (tmp_path / "withdrawn.txt").write_text("Secret answer is pineapple.\n", encoding="utf-8")

    report = ingest_corpus(tmp_path, withdrawn={"withdrawn.txt"})
    index = LexicalIndex(report.chunks)

    assert report.withdrawn == ["withdrawn.txt"]
    assert all(chunk.source != "withdrawn.txt" for chunk in index.chunks)
    result = answer_query(index, "pineapple")
    assert result.grounded is False


def test_unknown_filetype_is_skipped_not_fatal(tmp_path: Path) -> None:
    (tmp_path / "good.log").write_text("service healthy on port 18501\n", encoding="utf-8")
    (tmp_path / "blob.bin").write_bytes(b"\x00\x01\x02")

    report = ingest_corpus(tmp_path)
    assert len(report.chunks) == 1
    assert any(issue.source == "blob.bin" and issue.reason == "unsupported_filetype" for issue in report.skipped)


def test_index_round_trip_preserves_citations(tmp_path: Path) -> None:
    (tmp_path / "asset.csv").write_text("model,serial\nR9700,ABC123\n", encoding="utf-8")
    index = LexicalIndex(ingest_corpus(tmp_path).chunks)
    index_path = tmp_path / "index.json"
    index.save(index_path)

    restored = LexicalIndex.load(index_path)
    result = answer_query(restored, "ABC123")
    assert result.grounded is True
    assert result.citations[0].source == "asset.csv"
