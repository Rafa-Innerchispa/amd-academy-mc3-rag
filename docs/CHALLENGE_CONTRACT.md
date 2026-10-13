# AMD AI League Match 3 — Grader Contract

Status: implementation baseline, not submission-ready.

Publicly verified interface and limits:

- Index pass: `python3 /app/app.py --index /app/corpus`
- Query pass: `python3 /app/app.py --corpus /app/corpus --query-id <id> --query "<question>"`
- Output: `/app/output/<query_id>_output.json`
- JSON shape: `{"answer": "...", "citations": ["relative/path"], "confidence": 0.0-1.0}`
- Startup/indexing budget: 10 minutes
- Per-query budget: 30 seconds
- GPU memory: 1–48 GiB
- Uncompressed image: <= 60 GiB
- Network unavailable during grading
- Unsupported, unreadable and encrypted files must not abort the corpus walk
- Unanswerable questions must return an empty answer and empty citations
- Citations are judged exactly; unnecessary files can invalidate an otherwise correct answer

## Current baseline

Implemented:
- grader-compatible CLI
- persistent JSON index
- TXT/LOG/code/CSV/PDF/DOCX/XLSX parsing
- deterministic chunking
- identifier-aware lexical retrieval
- conservative fail-closed answer behavior
- ROCm 10 mandated base image
- basic contract tests

Still required before submission:
- resident GPU model server
- image/scanned-PDF transcription
- stronger revision/superseded-document filtering
- dense retrieval or equivalent recall layer
- exact-value generation and citation-by-necessity pruning
- official starter-kit sample scoring on AMD GPU
- VRAM, image-size and no-network validation
