# MC3 Submission Readiness

Date: 2026-10-13

## Final status

**READY FOR LABLAB SUBMISSION FOR POINTS**

The Match 3 prize window has passed, but the AMD AI League still accepts closed matches for leaderboard points.

## Candidate

- Repository: Rafa-Innerchispa/amd-academy-mc3-rag
- Final closure branch: `antigravity/mc3-final-close-20261013`
- Public image: `us-central1-docker.pkg.dev/innerops-agentic-platform/amd-academy-public/amd-academy-mc3-rag:mc3-final`
- Digest: `sha256:652a0ff48600c93116a6afb9859ce05d2ce8c8acb85d0b96835f3657e32ea910`

## Verified acceptance

- [x] Docker build on AMD host
- [x] ROCm torch preserved after dependency install
- [x] container remains alive with resident server
- [x] official sample corpus indexes successfully
- [x] official sample score **10/10**
- [x] PNG/JPG visual questions **2/2**
- [x] max query latency **23.80 s < 30 s**
- [x] startup + index **50.49 s < 600 s**
- [x] full 10-query run **24.19 s < 600 s**
- [x] peak VRAM **31.74 GiB** within 1–48 GiB
- [x] uncompressed image **24.68 GiB < 60 GiB**
- [x] `--network none` PASS
- [x] unreadable / encrypted / unsupported-file behavior is fail-per-file, not abort
- [x] anonymous public pull PASS

## Runtime evidence

- GPU: AMD Radeon AI PRO R9700 / gfx1201
- PyTorch: `2.13.0+rocm10.0.0`
- model: Qwen2.5-VL-3B-Instruct
- resident transport: Unix socket `/tmp/mc3.sock`

## Public image

```bash
docker pull us-central1-docker.pkg.dev/innerops-agentic-platform/amd-academy-public/amd-academy-mc3-rag:mc3-final
```

## Submission action remaining

The technical artifact is complete.

Remaining human/platform action:
1. open AMD AI League Match 3 on LabLab;
2. paste the copy from `docs/LABLAB_SUBMISSION.md`;
3. provide the public image URI above;
4. submit for leaderboard points.

## Storage note

The local Docker copy is **not required as the sole source of truth** because the public immutable artifact exists and anonymous pull has been verified. Any later local cleanup decision should still follow the storage decision brief and preserve reproducibility.
