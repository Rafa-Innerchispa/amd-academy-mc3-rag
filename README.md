# Grounded Multimodal RAG on AMD ROCm — Mini Challenge 3

AMD AI League / LabLab **Mini Challenge 3** submission candidate.

## What it does

A local-first multimodal RAG system that indexes a mixed enterprise corpus and answers questions with:

- the **value only**;
- the **exact minimal citation set**;
- clean refusal when the corpus cannot support the answer.

Supported corpus types include PDF, DOCX, XLSX, CSV, TXT, LOG, source code and images.

## AMD / ROCm design

- mandated ROCm 10 PyTorch base image;
- Qwen2.5-VL-3B weights baked into the Docker image;
- resident model/index server over a Unix socket;
- thin `/app/app.py` grader client;
- no network required during evaluation;
- local AMD GPU execution.

## Challenge-specific robustness

- withdrawn/superseded document filtering;
- row-level CSV/XLSX provenance;
- exact-value normalization;
- identifier-aware retrieval;
- true multi-hop retrieval across files;
- exact citation-by-necessity;
- image-only answers through the resident VLM;
- encrypted/unreadable/unknown files fail per-file instead of aborting indexing;
- unanswerable questions return an empty answer and empty citations.

## Grader contract

Index once:

```bash
python3 /app/app.py --index /app/corpus
```

Query:

```bash
python3 /app/app.py \
  --corpus /app/corpus \
  --query-id query_01 \
  --query "What is the maximum junction temperature?"
```

Output:

```json
{"answer":"94","citations":["specs/tq40_datasheet_r2.pdf"],"confidence":0.9}
```

## Current readiness

- Docker build on AMD: **PASS**
- logical/contract tests: **PASS**
- challenge-archetype tests: **PASS**
- Project Runtime Registry / allowlist: **PASS**
- final AMD GPU runtime benchmark: **in progress**

See `docs/SUBMISSION_READINESS.md`.

## Lineage

This repository reuses proven design patterns from MC2 ChispaVision OCR and InnerOS/HyperLoom evidence work, while keeping MC3 implementation and submission scope separate.


## Project Family & AMD AI League Context

This repository is part of the **InnerOS on AMD** challenge family for the AMD AI League 2026:
- **Canonical Umbrella Repository:** [https://github.com/Rafa-Innerchispa/inneros-amd-ai-league-2026](https://github.com/Rafa-Innerchispa/inneros-amd-ai-league-2026)
- **Match 2 (Vision OCR):** [https://github.com/Rafa-Innerchispa/infralens-ocr-amd](https://github.com/Rafa-Innerchispa/infralens-ocr-amd) (`chispavision-mc2:final-512`)
- **Match 4 (Web Retrieval):** [https://github.com/Rafa-Innerchispa/amd-academy-mc4-web-retrieval](https://github.com/Rafa-Innerchispa/amd-academy-mc4-web-retrieval)
- **Verified MC3 Docker Artifact:** `us-central1-docker.pkg.dev/innerops-agentic-platform/amd-academy-public/amd-academy-mc3-rag:mc3-final` (`sha256:652a0ff48600c93116a6afb9859ce05d2ce8c8acb85d0b96835f3657e32ea910`)
