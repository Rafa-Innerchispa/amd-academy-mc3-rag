# LabLab Submission — AMD AI League Mini Challenge 3

## Project name

**Grounded Multimodal RAG on AMD ROCm**

## One-line pitch

A local-first multimodal RAG engine on AMD ROCm that answers from mixed enterprise documents with value-only responses, exact minimal citations, and clean refusal when evidence is insufficient.

## Description

Grounded Multimodal RAG on AMD ROCm is our Mini Challenge 3 implementation for the AMD AI League.

The system indexes a mixed corpus containing PDF, DOCX, XLSX, CSV, TXT, production logs, source code and images. It then answers each question with only the requested value and the exact set of source files required to prove that answer.

The architecture is designed around the challenge's real traps rather than generic RAG demos:

- superseded and withdrawn documents are filtered;
- spreadsheets and CSV files preserve row-level provenance;
- technical identifiers are retained as retrieval anchors;
- multi-hop questions can bridge from a log to a ticket and then to a fix database;
- image-only values are transcribed with a resident vision-language model;
- encrypted, unreadable and unsupported files are skipped without aborting indexing;
- unsupported answers fail closed instead of being guessed.

The container uses the mandated AMD ROCm PyTorch base image and ships all model weights inside the image. Qwen2.5-VL-3B stays resident behind a Unix socket so the grader's fresh query process does not reload the model for every question.

The result is a fully local, network-independent retrieval system built for exact evidence rather than plausible prose.

## Why AMD

The entire runtime is designed around AMD ROCm. The submission uses the mandated ROCm 10 PyTorch base image and targets AMD GPU inference directly. The resident-model architecture is specifically intended to make repeated grader calls efficient on AMD hardware while preserving the challenge's strict startup and per-query budgets.

## Key technologies

- AMD ROCm
- AMD Radeon AI PRO R9700 / compatible AMD GPU
- PyTorch ROCm
- Qwen2.5-VL-3B-Instruct
- Hugging Face Transformers
- Python
- Docker
- multimodal RAG
- exact citation provenance

## GitHub

https://github.com/Rafa-Innerchispa/amd-academy-mc3-rag

Submission branch:

`chatgpt/mc3-contract-baseline-20261013`

## Docker image

**FINAL PUBLIC IMAGE URI: [PENDING_PUBLIC_IMAGE_URI]**

Replace this placeholder immediately after the final AMD runtime check/push.

## Grader interface

Index:

```
python3 /app/app.py --index /app/corpus
```

Query:

```
python3 /app/app.py --corpus /app/corpus --query-id <id> --query "<question>"
```

Output:

```
/app/output/<query-id>_output.json
```

## Pre-submit checklist

- [x] Docker builds on AMD host
- [x] contract tests pass
- [x] exact-citation multi-hop tests pass
- [x] image model weights baked into image
- [x] no runtime model download required
- [ ] final AMD GPU runtime PASS
- [ ] official public sample score recorded
- [ ] visual questions verified on GPU
- [ ] latency/VRAM/image-size recorded
- [ ] `--network none` PASS
- [ ] public Docker image pushed
- [ ] replace `[PENDING_PUBLIC_IMAGE_URI]`
- [ ] submit in LabLab

## Truth boundary

Do not claim final GPU benchmark numbers until the current AMD validation gate records them. Do not hardcode any public sample answer; the graded corpus is different.
