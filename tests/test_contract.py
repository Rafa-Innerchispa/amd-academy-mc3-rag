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
from retrieval import citations_for_answer, rank


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
