from __future__ import annotations

import argparse
import json
import os
import socket
import time
from pathlib import Path

SOCKET_PATH = os.getenv("MC3_SOCKET", "/tmp/mc3.sock")
OUTPUT_DIR = Path(os.getenv("MC3_OUTPUT_DIR", "/app/output"))


def request(payload: dict, *, connect_wait_s: float = 3.0, io_timeout_s: float = 28.0) -> dict:
    deadline = time.monotonic() + max(0.0, connect_wait_s)
    last_error: Exception | None = None

    while True:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(io_timeout_s)
                client.connect(SOCKET_PATH)
                client.sendall((json.dumps(payload) + "\n").encode("utf-8"))
                raw = b""
                while not raw.endswith(b"\n"):
                    chunk = client.recv(65536)
                    if not chunk:
                        break
                    raw += chunk
            if not raw:
                raise RuntimeError("empty_server_response")
            return json.loads(raw.decode("utf-8"))
        except (FileNotFoundError, ConnectionRefusedError, socket.timeout, OSError) as exc:
            last_error = exc
            if time.monotonic() >= deadline:
                raise last_error
            time.sleep(0.1)


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
        # Model initialization happens in the resident server before the Unix
        # socket is bound. Give startup/index a bounded readiness window while
        # remaining well inside the challenge's startup+index budget.
        result = request(
            {"action": "index", "corpus": args.index_dir},
            connect_wait_s=120.0,
            io_timeout_s=480.0,
        )
        return 0 if result.get("ok") else 1

    if args.query is not None and args.query_id:
        try:
            # Queries have a strict 30-second budget. A missing server should
            # fail closed quickly instead of spending the whole budget waiting.
            result = request(
                {
                    "action": "query",
                    "corpus": args.corpus,
                    "query": args.query,
                },
                connect_wait_s=2.0,
                io_timeout_s=27.0,
            )
        except Exception:
            result = {"answer": "", "citations": [], "confidence": 0.0}
        write_output(args.query_id, result)
        return 0

    parser.error("use --index <corpus> or --query <text> --query-id <id> [--corpus <corpus>]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
