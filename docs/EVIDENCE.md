# MC3 Evidence

## Baseline status

Branch: `chatgpt/mc3-rag-baseline-clean-20261007`

Implemented:

- deterministic mixed text-file ingestion;
- structured skip evidence for unsupported/unreadable inputs;
- withdrawn-document exclusion;
- deterministic line-preserving chunk IDs;
- persistent versioned lexical index;
- fail-closed no-answer behavior;
- exact filename + line-range citations;
- extractive grounded answer stage;
- tests for citation, no-answer, withdrawn docs, unknown files and index round trip.

## Claims intentionally NOT made yet

- no claim of official MC3 grader compliance until the exact brief is captured;
- no claim of PDF/DOCX/XLSX/image support yet;
- no claim of GPU acceleration yet;
- no claim of ROCm 10.1 performance;
- no claim that the extractive baseline is the final generator.

## Next measurable gates

1. Run the test suite locally.
2. Add safe PDF/DOCX/XLSX parsers.
3. Integrate MC2 OCR as an image adapter.
4. Capture the official grader CLI/container contract.
5. Add a ROCm model-serving generator without weakening provenance/no-answer guarantees.
6. Benchmark query latency and VRAM on the R9700.
