import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "app.py"


def test_index_and_query_contract(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "spec.txt").write_text("Maximum junction temperature: 94 C\n", encoding="utf-8")

    output = tmp_path / "output"
    env = {
        "MC3_INDEX_PATH": str(tmp_path / "index.json"),
        "MC3_OUTPUT_DIR": str(output),
    }

    import os
    proc_env = os.environ.copy()
    proc_env.update(env)

    subprocess.run([sys.executable, str(APP), "--index", str(corpus)], check=True, env=proc_env)
    subprocess.run([
        sys.executable, str(APP),
        "--corpus", str(corpus),
        "--query-id", "query_01",
        "--query", "What is the maximum junction temperature?",
    ], check=True, env=proc_env)

    payload = json.loads((output / "query_01_output.json").read_text(encoding="utf-8"))
    assert set(payload) == {"answer", "citations", "confidence"}
    assert payload["citations"] == ["spec.txt"]


def test_unanswerable_fails_closed(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "readme.txt").write_text("Board color: blue\n", encoding="utf-8")

    output = tmp_path / "output"
    import os
    env = os.environ.copy()
    env["MC3_INDEX_PATH"] = str(tmp_path / "index.json")
    env["MC3_OUTPUT_DIR"] = str(output)

    subprocess.run([sys.executable, str(APP), "--index", str(corpus)], check=True, env=env)
    subprocess.run([
        sys.executable, str(APP),
        "--query-id", "query_02",
        "--query", "Which firmware release fixed ORR-1847?",
    ], check=True, env=env)

    payload = json.loads((output / "query_02_output.json").read_text(encoding="utf-8"))
    assert payload["answer"] == ""
    assert payload["citations"] == []
