from __future__ import annotations

import os
from pathlib import Path

from huggingface_hub import snapshot_download

MODEL_ID = os.getenv("MODEL_ID", "Qwen/Qwen2.5-VL-3B-Instruct")
MODEL_REVISION = os.getenv("MODEL_REVISION", "66285546d2b821cf421d4f5eb2576359d3770cd3")
MODEL_DIR = Path(os.getenv("MODEL_DIR", "/models/Qwen2.5-VL-3B-Instruct"))
MODEL_DIR.mkdir(parents=True, exist_ok=True)

snapshot_download(
    repo_id=MODEL_ID,
    revision=MODEL_REVISION,
    local_dir=str(MODEL_DIR),
    ignore_patterns=["*.md", "*.gitattributes"],
)
print(f"MODEL_READY {MODEL_ID}@{MODEL_REVISION} -> {MODEL_DIR}")
