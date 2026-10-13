# Grounded Multimodal RAG on AMD ROCm — Mini Challenge 3

AMD AI League / LabLab **Mini Challenge 3** final submission candidate.

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
- local AMD GPU execution on Radeon AI PRO R9700 / gfx1201.

## Final verified result

- Docker build on AMD: **PASS**
- PyTorch ROCm: **2.13.0+rocm10.0.0**
- official public sample score: **10/10**
- visual questions: **2/2**
- startup + indexing: **50.49 s**
- max query latency: **23.80 s**
- full 10-query run: **24.19 s**
- peak VRAM: **31.74 GiB**
- image size: **24.68 GiB**
- `--network none`: **PASS**
- resident Unix-socket server: **PASS**
- anonymous public pull: **PASS**

## Public image

`us-central1-docker.pkg.dev/innerops-agentic-platform/amd-academy-public/amd-academy-mc3-rag:mc3-final`

Digest:

`sha256:652a0ff48600c93116a6afb9859ce05d2ce8c8acb85d0b96835f3657e32ea910`

Anonymous pull:

```bash
docker pull us-central1-docker.pkg.dev/innerops-agentic-platform/amd-academy-public/amd-academy-mc3-rag:mc3-final
```

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

## Submission copy

See:

- `docs/LABLAB_SUBMISSION.md`
- `docs/SUBMISSION_READINESS.md`

## Lineage

This repository reuses proven design patterns from MC2 ChispaVision OCR and InnerOS/HyperLoom evidence work, while keeping MC3 implementation and submission scope separate.
