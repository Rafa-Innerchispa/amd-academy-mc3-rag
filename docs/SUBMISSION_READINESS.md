# MC3 Submission Readiness

Date: 2026-10-13

## Candidate

- Repository: Rafa-Innerchispa/amd-academy-mc3-rag
- Branch: `chatgpt/mc3-contract-baseline-20261013`
- Logical CI head: `01b8bec6b2044cbf8da2d9d03aaec4e731cf8ce1`
- Logical contract CI: PASS

## Official contract verified

The public Match 3 starter kit confirms:

- Docker image submission
- mandated ROCm 10 PyTorch base image
- `python3 /app/app.py --index /app/corpus`
- one fresh `--query` process per question
- output at `/app/output/<query-id>_output.json`
- exact-set citations
- empty answer + empty citations for unanswerable questions
- 60 GiB uncompressed image maximum
- 1–48 GiB GPU VRAM
- 10 minute startup + indexing budget
- 30 second per-query budget
- 10 minute whole-question run budget
- no outbound network during evaluation
- unreadable, encrypted and unknown files must not abort indexing

## Sample-archetype coverage in code

1. PDF current-vs-withdrawn revision
   - withdrawn filename/content filtering
   - exact numeric value normalization

2. DOCX roadmap quarter
   - DOCX paragraphs and table parsing
   - `Qx FYyy` canonicalization

3. XLSX part number
   - per-sheet, per-row chunks with header context
   - part-number canonicalization

4. CSV ticket -> firmware
   - row-level chunks with header context
   - ticket identifier boosting

5. LOG error code
   - text/log parsing
   - error-code canonicalization

6. Python current default vs old comment
   - source parsing
   - semantic numeric fallback prefers assignment/current line over comments

7. PNG-only pin
   - resident Qwen2.5-VL image transcription during index

8. JPG-only revision
   - resident Qwen2.5-VL image transcription during index

9. True multi-hop LOG -> ticket -> CSV
   - whole-corpus second-hop identifier scan
   - provenance records `via_identifier` and `via_source`
   - exact two-file citation derivation
   - CSV row-level chunking prevents unrelated-row false direct matches

10. Unanswerable encrypted source
    - encrypted PDF skip
    - fail-closed empty answer/citations

## CI evidence already PASS

The branch tests cover:

- parser/retrieval basic contract
- zero-lexical-overlap multi-hop
- exact two-file citations
- direct minimal citation
- model-prose exact-value canonicalization
- evidence-only fallback
- delayed resident-server readiness
- technical identifier numeric-fragment rejection
- old commented value `60` vs current constant `180`
- CSV row granularity preserving true multi-hop

## Pending AMD-only gates

Do not mark submission-ready until all are recorded:

- [ ] Docker build on AMD host
- [ ] ROCm torch preserved after dependency install
- [ ] container remains alive with resident server
- [ ] official sample corpus indexes successfully
- [ ] official sample score recorded
- [ ] PNG/JPG OCR answers verified on GPU
- [ ] query latency < 30 s
- [ ] startup + index < 10 min
- [ ] full 10-query run < 10 min
- [ ] peak VRAM between 1 and 48 GiB
- [ ] uncompressed image <= 60 GiB
- [ ] `--network none` execution passes
- [ ] unreadable file / encrypted PDF / unknown binary / empty directory do not abort

## Active validation owner

InnerOS task: `ops_697abbbc088c`

Expected evidence:

- source SHA
- final SHA
- Docker build result
- ROCm torch version
- container-alive result
- official sample score
- image size
- GPU VRAM
- query latency
- no-network result
- any safe fixes committed on validation branch

## Submission rule

No hardcoded sample values. The graded corpus and questions are different and harder.
