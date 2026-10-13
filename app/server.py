from __future__ import annotations

import json
import os
import re
import socket
import traceback
from pathlib import Path

from model import ResidentVLM
from parsers import build_index, chunk_text
from retrieval import (
    canonicalize_answer,
    citations_for_answer,
    fallback_answer_from_results,
    rank,
)

SOCKET_PATH = os.getenv("MC3_SOCKET", "/tmp/mc3.sock")
INDEX_PATH = Path(os.getenv("MC3_INDEX_PATH", "/tmp/mc3_index.json"))
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}
OBSOLETE_MARKERS = ("withdrawn", "superseded", "obsolete", "deprecated")
STATUS_RE = re.compile(
    r"(?im)^\s*(?:document\s+)?status\s*[:=-]\s*"
    r"(?:withdrawn|superseded|obsolete|deprecated)\b|"
    r"^\s*(?:this\s+document\s+is\s+)?"
    r"(?:withdrawn|superseded|obsolete|deprecated)\b"
)

MODEL = ResidentVLM()
INDEX: dict = {"corpus": "", "documents": []}


def _is_obsolete(path: Path) -> bool:
    lower = path.name.lower()
    return any(marker in lower for marker in OBSOLETE_MARKERS)


def _text_marks_obsolete(text: str) -> bool:
    return bool(STATUS_RE.search((text or "")[:1200]))


def _index_images(corpus: Path, index: dict) -> None:
    docs = index.setdefault("documents", [])
    for path in sorted(corpus.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        if _is_obsolete(path):
            continue
        try:
            text = MODEL.transcribe_image(str(path))
        except Exception:
            continue
        if not text.strip() or _text_marks_obsolete(text):
            continue
        rel = path.relative_to(corpus).as_posix()
        for chunk_id, chunk in enumerate(chunk_text(text)):
            docs.append({
                "source": rel,
                "chunk_id": chunk_id,
                "text": chunk,
                "kind": "vision",
            })


def build_full_index(corpus_path: str) -> dict:
    corpus = Path(corpus_path).resolve()
    index = build_index(str(corpus))

    stale_sources = {
        item["source"]
        for item in index.get("documents", [])
        if _is_obsolete(Path(item["source"])) or _text_marks_obsolete(item["text"])
    }
    index["documents"] = [
        item
        for item in index.get("documents", [])
        if item["source"] not in stale_sources
    ]

    _index_images(corpus, index)
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    return index


def load_index() -> dict:
    if not INDEX_PATH.exists():
        return {"corpus": "", "documents": []}
    try:
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"corpus": "", "documents": []}


def answer_query(question: str) -> dict:
    results = rank(INDEX.get("documents", []), question, limit=10)
    if not results:
        return {"answer": "", "citations": [], "confidence": 0.0}

    raw = MODEL.answer(question, results)
    answer = canonicalize_answer(question, str(raw.get("answer") or ""))
    citations = citations_for_answer(results, answer)

    if not answer or not citations:
        answer = fallback_answer_from_results(question, results)
        citations = citations_for_answer(results, answer)

    if not answer or not citations:
        return {"answer": "", "citations": [], "confidence": 0.0}

    return {
        "answer": answer,
        "citations": citations,
        "confidence": min(0.98, 0.80 + 0.04 * len(citations)),
    }


def dispatch(request: dict) -> dict:
    global INDEX
    action = request.get("action")
    if action == "health":
        return {
            "ok": True,
            "documents": len(INDEX.get("documents", [])),
            "model": MODEL.model_id,
            "device": MODEL.device,
        }
    if action == "index":
        INDEX = build_full_index(str(request["corpus"]))
        return {"ok": True, "documents": len(INDEX.get("documents", []))}
    if action == "query":
        if not INDEX.get("documents"):
            INDEX = load_index()
        return answer_query(str(request.get("query") or ""))
    return {"ok": False, "error": "unknown_action"}


def serve() -> None:
    global INDEX
    INDEX = load_index()
    try:
        os.unlink(SOCKET_PATH)
    except FileNotFoundError:
        pass
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(SOCKET_PATH)
        os.chmod(SOCKET_PATH, 0o666)
        server.listen(8)
        print(json.dumps({
            "event": "MC3_READY",
            "socket": SOCKET_PATH,
            "model": MODEL.model_id,
            "device": MODEL.device,
        }), flush=True)
        while True:
            conn, _ = server.accept()
            with conn:
                try:
                    raw = b""
                    while not raw.endswith(b"\n"):
                        chunk = conn.recv(65536)
                        if not chunk:
                            break
                        raw += chunk
                    request = json.loads(raw.decode("utf-8"))
                    response = dispatch(request)
                except Exception as exc:
                    response = {
                        "ok": False,
                        "error": type(exc).__name__,
                        "message": str(exc),
                        "trace": traceback.format_exc(limit=2),
                    }
                conn.sendall(
                    (json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8")
                )


if __name__ == "__main__":
    serve()
