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

Work / Closure branch:

`antigravity/mc3-final-close-20261013`

## Docker image

**FINAL PUBLIC IMAGE URI:**

`us-central1-docker.pkg.dev/innerops-agentic-platform/amd-academy-public/amd-academy-mc3-rag:mc3-final`

Digest: `sha256:652a0ff48600c93116a6afb9859ce05d2ce8c8acb85d0b96835f3657e32ea910`

Public anonymous pull command:
```bash
docker pull us-central1-docker.pkg.dev/innerops-agentic-platform/amd-academy-public/amd-academy-mc3-rag:mc3-final
```

## Grader interface

Index:

```bash
python3 /app/app.py --index /app/corpus
```

Query:

```bash
python3 /app/app.py --corpus /app/corpus --query-id <id> --query "<question>"
```

Output:

```bash
/app/output/<query-id>_output.json
```

## Verification & Hardware Metrics

- **GPU Runtime Status:** PASS (AMD Radeon AI PRO R9700 / gfx1201)
- **PyTorch ROCm Version:** `2.13.0+rocm10.0.0`
- **Sample Score:** 10/10 PASS
- **Visual Questions Score:** 2/2 PASS (PIN14 and REV-C2)
- **Startup + Indexing Latency:** 50.49 s (Budget: 600 s)
- **Max Query Latency:** 23.80 s (Budget: 30 s)
- **Full 10-Query Run Time:** 24.19 s (Budget: 600 s)
- **Peak VRAM Usage:** 31.74 GiB (GPU Capacity: 31.86 GiB)
- **Image Size:** 24.68 GiB (26,499,065,421 bytes / 26.5 GB content size, budget: <= 60 GiB)
- **No Network Verification:** PASS (`--network none`)
- **Container Resident Server:** PASS (Unix socket `/tmp/mc3.sock` alive)
- **Anonymous Public Pull:** PASS (Verified with empty Docker config)

## Pre-submit checklist

- [x] Docker builds on AMD host
- [x] contract tests pass
- [x] exact-citation multi-hop tests pass
- [x] image model weights baked into image
- [x] no runtime model download required
- [x] final AMD GPU runtime PASS
- [x] official public sample score recorded (10/10)
- [x] visual questions verified on GPU (2/2)
- [x] latency/VRAM/image-size recorded
- [x] `--network none` PASS
- [x] public Docker image pushed
- [x] replace `[PENDING_PUBLIC_IMAGE_URI]`
- [x] submit in LabLab
