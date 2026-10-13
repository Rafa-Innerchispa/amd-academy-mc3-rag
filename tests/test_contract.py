from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "app.py"
sys.path.insert(0, str(ROOT / "app"))

from parsers import build_index
from retrieval import (
    canonicalize_answer,
    citations_for_answer,
    fallback_answer_from_results,
    rank,
)


def test_parsers_and_retrieval(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "spec.txt").write_text(
        "TQ-40 maximum junction temperature is 94 C\n",
        encoding="utf-8",
    )
    index = build_index(str(corpus))
    results = rank(index["documents"], "maximum junction temperature TQ-40")
    assert results
    assert results[0]["source"] == "spec.txt"
    assert "94" in results[0]["text"]


def test_multihop_scans_zero_overlap_documents():
    index = [
        {
            "source": "logs/device.log",
            "chunk_id": 0,
            "text": "Incident during boot. Failure code E7731 observed.",
        },
        {
            "source": "releases/fixes.csv",
            "chunk_id": 0,
            "text": "E7731 | 4.3.2",
        },
        {
            "source": "notes/unrelated.txt",
            "chunk_id": 0,
            "text": "incident review meeting notes",
        },
    ]

    results = rank(index, "Which firmware fixed the boot incident?", limit=4)
    sources = [item["source"] for item in results]
    assert "logs/device.log" in sources
    assert "releases/fixes.csv" in sources

    answer_hop = next(
        item for item in results if item["source"] == "releases/fixes.csv"
    )
    assert answer_hop["retrieval_kind"] == "hop"
    assert answer_hop["via_identifier"] == "e7731"
    assert answer_hop["via_source"] == "logs/device.log"
    assert citations_for_answer(results, "4.3.2") == [
        "logs/device.log",
        "releases/fixes.csv",
    ]


def test_direct_answer_prefers_single_minimal_citation():
    results = [
        {
            "source": "specs/current.txt",
            "chunk_id": 0,
            "text": "Maximum junction temperature is 94 C",
            "retrieval_kind": "direct",
            "via_identifier": None,
            "via_source": None,
        },
        {
            "source": "notes/copied.txt",
            "chunk_id": 0,
            "text": "For reference: 94 C",
            "retrieval_kind": "hop",
            "via_identifier": "tq-40",
            "via_source": "specs/current.txt",
        },
    ]
    assert citations_for_answer(results, "94") == ["specs/current.txt"]


def test_model_prose_is_canonicalized_for_exact_value_scoring():
    assert canonicalize_answer(
        "Which firmware version fixed the error?",
        "The firmware version is 4.3.2.",
    ) == "4.3.2"
    assert canonicalize_answer(
        "Which roadmap quarter and fiscal year?",
        "It is planned for Q3 FY27.",
    ) == "Q3 FY27"
    assert canonicalize_answer(
        "What is the board revision?",
        "The silkscreen says REV-C2.",
    ) == "REV-C2"


def test_conservative_fallback_extracts_supported_value():
    results = [
        {
            "source": "specs/tq40.txt",
            "chunk_id": 0,
            "text": "TQ-40 maximum junction temperature is 94 C",
            "retrieval_kind": "direct",
            "via_identifier": None,
            "via_source": None,
        }
    ]
    answer = fallback_answer_from_results(
        "What is the maximum junction temperature of TQ-40?",
        results,
    )
    assert answer == "94"
    assert citations_for_answer(results, answer) == ["specs/tq40.txt"]


def _fake_server(sock_path: Path, response: dict):
    try:
        sock_path.unlink()
    except FileNotFoundError:
        pass
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(sock_path))
        server.listen(1)
        conn, _ = server.accept()
        with conn:
            raw = b""
            while not raw.endswith(b"\n"):
                chunk = conn.recv(65536)
                if not chunk:
                    break
                raw += chunk
            request = json.loads(raw.decode("utf-8"))
            assert request["action"] == "query"
            conn.sendall((json.dumps(response) + "\n").encode("utf-8"))


def test_query_process_writes_grader_json(tmp_path):
    sock_path = tmp_path / "mc3.sock"
    output = tmp_path / "output"
    thread = threading.Thread(
        target=_fake_server,
        args=(sock_path, {
            "answer": "94",
            "citations": ["specs/tq40_datasheet_r2.pdf"],
            "confidence": 0.91,
        }),
        daemon=True,
    )
    thread.start()

    env = os.environ.copy()
    env["MC3_SOCKET"] = str(sock_path)
    env["MC3_OUTPUT_DIR"] = str(output)

    subprocess.run([
        sys.executable, str(APP),
        "--corpus", "/app/corpus",
        "--query-id", "query_01",
        "--query", "What is the maximum junction temperature of the TQ-40?",
    ], check=True, env=env)
    thread.join(timeout=2)

    payload = json.loads(
        (output / "query_01_output.json").read_text(encoding="utf-8")
    )
    assert payload == {
        "answer": "94",
        "citations": ["specs/tq40_datasheet_r2.pdf"],
        "confidence": 0.91,
    }


def test_query_failure_still_writes_valid_refusal(tmp_path):
    output = tmp_path / "output"
    env = os.environ.copy()
    env["MC3_SOCKET"] = str(tmp_path / "missing.sock")
    env["MC3_OUTPUT_DIR"] = str(output)

    subprocess.run([
        sys.executable, str(APP),
        "--query-id", "query_10",
        "--query", "What is the unit price?",
    ], check=True, env=env)

    payload = json.loads(
        (output / "query_10_output.json").read_text(encoding="utf-8")
    )
    assert payload == {
        "answer": "",
        "citations": [],
        "confidence": 0.0,
    }



def test_client_waits_for_delayed_server(tmp_path):
    sock_path = tmp_path / "delayed.sock"
    output = tmp_path / "output"

    def delayed_server():
        import time
        time.sleep(0.25)
        _fake_server(sock_path, {
            "answer": "4.3.2",
            "citations": ["fixes.csv"],
            "confidence": 0.9,
        })

    thread = threading.Thread(target=delayed_server, daemon=True)
    thread.start()

    env = os.environ.copy()
    env["MC3_SOCKET"] = str(sock_path)
    env["MC3_OUTPUT_DIR"] = str(output)

    subprocess.run([
        sys.executable, str(APP),
        "--query-id", "delayed",
        "--query", "Which firmware version fixed the issue?",
    ], check=True, env=env)
    thread.join(timeout=2)

    payload = json.loads(
        (output / "delayed_output.json").read_text(encoding="utf-8")
    )
    assert payload["answer"] == "4.3.2"
    assert payload["citations"] == ["fixes.csv"]



def test_numeric_fallback_prefers_current_constant_over_old_comment():
    results = [
        {
            "source": "engineering/ingest_service.py",
            "chunk_id": 0,
            "text": (
                "# Seconds a batch may sit in the staging queue before it is abandoned.\n"
                "# Raised from 60 after the 2026-08 backlog incident.\n"
                "DEFAULT_BATCH_TIMEOUT_S = 180\n"
                "MAX_INFLIGHT_BATCHES = 12"
            ),
            "retrieval_kind": "direct",
            "via_identifier": None,
            "via_source": None,
        }
    ]
    answer = fallback_answer_from_results(
        "What is the default batch timeout, in seconds, in the ingest service?",
        results,
    )
    assert answer == "180"
    assert citations_for_answer(results, answer) == [
        "engineering/ingest_service.py"
    ]


def test_csv_row_chunking_preserves_true_multihop(tmp_path):
    corpus = tmp_path / "corpus"
    logs = corpus / "logs"
    support = corpus / "support"
    logs.mkdir(parents=True)
    support.mkdir(parents=True)

    (logs / "prod.log").write_text(
        "ERROR E7731: thermal throttle engaged\n"
        "incident logged against ORR-1847\n",
        encoding="utf-8",
    )
    (support / "bug_database.csv").write_text(
        "ticket,component,summary,fixed_in\n"
        "ORR-1847,power,Die sensor high,4.3.2\n"
        "ORR-1755,thermal,Fan curve aggressive,4.2.0\n",
        encoding="utf-8",
    )

    index = build_index(str(corpus))
    query = (
        "The production log shows a thermal throttle incident. "
        "Which firmware release fixed the underlying defect?"
    )
    results = rank(index["documents"], query, limit=8)

    target = next(
        item
        for item in results
        if item["source"] == "support/bug_database.csv"
        and "ORR-1847" in item["text"]
    )
    assert target["retrieval_kind"] == "hop"
    assert target["via_source"] == "logs/prod.log"
    assert citations_for_answer(results, "4.3.2") == [
        "logs/prod.log",
        "support/bug_database.csv",
    ]
