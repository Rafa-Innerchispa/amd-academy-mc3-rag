from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

from parsers import build_index
from retrieval import minimal_citations, rank

INDEX_PATH = Path(os.getenv("MC3_INDEX_PATH", "/tmp/mc3_index.json"))
OUTPUT_DIR = Path(os.getenv("MC3_OUTPUT_DIR", "/app/output"))

NUMBER_RE = re.compile(r"(?<![A-Za-z0-9])[-+]?\d+(?:\.\d+)?(?:\s?%|\s?[A-Za-z]{1,6})?")
VERSION_RE = re.compile(r"\b(?:v(?:ersion)?\s*)?\d+(?:\.\d+){1,3}(?:[-_A-Za-z0-9.]*)\b", re.I)
IDENT_RE = re.compile(r"\b[A-Z]{2,}[A-Z0-9_-]*[-#]?[0-9]{2,}\b")


def save_index(index: dict) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")


def load_index() -> dict:
    if not INDEX_PATH.exists():
        return {"corpus": "", "documents": []}
    try:
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"corpus": "", "documents": []}


def extract_answer(question: str, results: list[dict]) -> str:
    if not results:
        return ""
    q = question.lower()
    joined = "\n".join(item["text"] for item in results[:4])

    patterns = []
    if any(word in q for word in ("version", "release", "firmware")):
        patterns.append(VERSION_RE)
    if any(word in q for word in ("temperature", "voltage", "current", "maximum", "minimum", "limit", "speed")):
        patterns.append(NUMBER_RE)
    if any(word in q for word in ("ticket", "error", "code", "part", "identifier", "id")):
        patterns.append(IDENT_RE)

    for pattern in patterns:
        match = pattern.search(joined)
        if match:
            return match.group(0).strip()

    # Conservative baseline: do not fabricate prose. Exact-value generation
    # will be replaced by the resident ROCm model lane.
    return ""


def answer_query(index: dict, query: str) -> dict:
    results = rank(index.get("documents", []), query)
    answer = extract_answer(query, results)
    citations = minimal_citations(results, answer)
    if answer and not citations:
        answer = ""
    confidence = 0.0 if not answer else min(0.95, 0.55 + 0.05 * len(citations))
    return {"answer": answer, "citations": citations, "confidence": confidence}


def write_output(query_id: str, payload: dict) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{query_id}_output.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="AMD AI League MC3 grader entrypoint")
    parser.add_argument("--index", dest="index_dir")
    parser.add_argument("--corpus")
    parser.add_argument("--query")
    parser.add_argument("--query-id")
    args = parser.parse_args()

    if args.index_dir:
        save_index(build_index(args.index_dir))
        return 0

    if args.query and args.query_id:
        index = load_index()
        if args.corpus and (not index.get("documents") or index.get("corpus") != str(Path(args.corpus).resolve())):
            index = build_index(args.corpus)
            save_index(index)
        write_output(args.query_id, answer_query(index, args.query))
        return 0

    parser.error("use --index <corpus> or --query <text> --query-id <id> [--corpus <corpus>]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
