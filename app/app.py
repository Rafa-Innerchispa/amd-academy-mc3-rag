from __future__ import annotations

import argparse
import json
import os
import socket
from pathlib import Path

SOCKET_PATH = os.getenv("MC3_SOCKET", "/tmp/mc3.sock")
OUTPUT_DIR = Path(os.getenv("MC3_OUTPUT_DIR", "/app/output"))


def request(payload: dict) -> dict:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(28.0)
        client.connect(SOCKET_PATH)
        client.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        raw = b""
        while not raw.endswith(b"\n"):
            chunk = client.recv(65536)
            if not chunk:
                break
            raw += chunk
    return json.loads(raw.decode("utf-8"))


def write_output(query_id: str, payload: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    normalized = {
        "answer": str(payload.get("answer") or ""),
        "citations": payload.get("citations") if isinstance(payload.get("citations"), list) else [],
        "confidence": float(payload.get("confidence") or 0.0),
    }
    (OUTPUT_DIR / f"{query_id}_output.json").write_text(
        json.dumps(normalized, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="AMD AI League MC3 grader entrypoint")
    parser.add_argument("--index", dest="index_dir")
    parser.add_argument("--corpus")
    parser.add_argument("--query")
    parser.add_argument("--query-id")
    args = parser.parse_args()

    if args.index_dir:
        result = request({"action": "index", "corpus": args.index_dir})
        return 0 if result.get("ok") else 1

    if args.query is not None and args.query_id:
        try:
            result = request({
                "action": "query",
                "corpus": args.corpus,
                "query": args.query,
            })
        except Exception:
            result = {"answer": "", "citations": [], "confidence": 0.0}
        write_output(args.query_id, result)
        return 0

    parser.error("use --index <corpus> or --query <text> --query-id <id> [--corpus <corpus>]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
