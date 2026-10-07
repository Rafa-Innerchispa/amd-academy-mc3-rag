# MC3 Architecture

## Goal

Provide a grounded, fail-closed RAG core for the AMD AI Academy Mini Challenge 3.

Current baseline intentionally starts with deterministic retrieval and extractive answers so correctness, provenance and no-answer behavior can be tested before adding GPU generation.

## Pipeline

```text
corpus
  -> safe file walk
  -> deterministic text chunking
  -> persistent lexical index
  -> ranked retrieval
  -> extractive grounded answer
  -> exact file/line citations
```

## Current supported inputs

Text-like sources: TXT, Markdown, logs, source code, JSON, YAML, CSV, TOML, INI and CFG.

Unsupported/binary formats are skipped with structured evidence instead of aborting ingestion.

PDF, DOCX, XLSX and image adapters are intentionally the next layer. Image ingestion should reuse the proven MC2 ChispaVision OCR capability rather than duplicate OCR logic.

## Safety / grading contracts

- unreadable files do not abort corpus ingestion;
- unsupported files do not enter context;
- withdrawn files never enter the index;
- a query with no lexical evidence returns an empty answer and empty citations;
- every grounded answer carries exact source filename and line range;
- index artifacts use an explicit versioned schema;
- no external API is required for the baseline.

## ROCm lane

The generator layer is deliberately replaceable. A ROCm 10.1 serving candidate can consume retrieved chunks later while preserving the same QueryResult and Citation contracts.

No AMD performance claim is made until measured on physical AMD hardware.
