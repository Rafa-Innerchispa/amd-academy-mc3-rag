from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

DEFAULT_MODEL_ID = "Qwen/Qwen2.5-VL-3B-Instruct"


def _extract_json(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    if not text:
        return {}
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {}
    except Exception:
        pass
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S | re.I)
    if fenced:
        try:
            value = json.loads(fenced.group(1))
            return value if isinstance(value, dict) else {}
        except Exception:
            return {}
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        try:
            value = json.loads(text[start:end + 1])
            return value if isinstance(value, dict) else {}
        except Exception:
            return {}
    return {}


class ResidentVLM:
    def __init__(self) -> None:
        import torch
        from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

        self.torch = torch
        self.torch.set_num_threads(8)
        self.model_id = os.getenv("MODEL_ID", DEFAULT_MODEL_ID)
        self.model_dir = Path(os.getenv("MODEL_DIR", "/models/Qwen2.5-VL-3B-Instruct"))
        source = str(self.model_dir if self.model_dir.is_dir() else self.model_id)
        local = self.model_dir.is_dir()

        self.processor = AutoProcessor.from_pretrained(source, local_files_only=local)
        if torch.cuda.is_available():
            self.device = "cuda"
            dtype = torch.bfloat16
            try:
                free_mem, _ = torch.cuda.mem_get_info(0)
                gpu_budget = max(256, int(free_mem * 0.70 / (1024 * 1024)))
                max_memory = {0: f"{gpu_budget}MiB", "cpu": "24GiB"}
            except Exception:
                free_mem = 0
                max_memory = None

            if max_memory is not None and free_mem < (7 * 1024**3):
                self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                    source,
                    torch_dtype=dtype,
                    device_map="auto",
                    max_memory=max_memory,
                    local_files_only=local,
                    attn_implementation="sdpa",
                ).eval()
            else:
                self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                    source,
                    torch_dtype=dtype,
                    local_files_only=local,
                    attn_implementation="sdpa",
                ).to("cuda").eval()
        else:
            self.device = "cpu"
            dtype = torch.float32
            self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                source,
                torch_dtype=dtype,
                local_files_only=local,
                attn_implementation="sdpa",
            ).to("cpu").eval()

    def _generate(self, messages: list[dict], max_new_tokens: int = 128) -> str:
        from qwen_vl_utils import process_vision_info

        prompt = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(messages)
        device = getattr(self.model, "device", self.device)
        inputs = self.processor(
            text=[prompt],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        ).to(device)
        with self.torch.inference_mode():
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                num_beams=1,
            )
        generated = output[:, inputs["input_ids"].shape[1]:]
        return self.processor.batch_decode(
            generated,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0].strip()

    def transcribe_image(self, path: str) -> str:
        image = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        messages = [
            {
                "role": "system",
                "content": [{
                    "type": "text",
                    "text": (
                        "Read only text visibly printed in the image. Preserve technical "
                        "identifiers, revision labels, pin names, punctuation and line order. "
                        "Do not describe the image and do not invent missing text."
                    ),
                }],
            },
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": "Transcribe the visible text exactly."},
                ],
            },
        ]
        return self._generate(messages, max_new_tokens=128)

    def answer(self, question: str, contexts: list[dict]) -> dict[str, Any]:
        packed = []
        for item in contexts[:4]:
            packed.append(
                f"SOURCE: {item['source']}\n"
                f"CHUNK: {item['chunk_id']}\n"
                f"TEXT:\n{item['text']}"
            )
        context_text = "\n\n---\n\n".join(packed)
        system = (
            "You answer only from the supplied corpus excerpts. Return strict JSON with "
            "exactly answer and citations. answer must be the complete value only, never a "
            "sentence. citations must be the exact minimal set of source file paths needed "
            "to derive the answer. If the corpus excerpts do not support the answer, return "
            '{"answer":"","citations":[]}. Never use outside knowledge.'
        )
        user = (
            f"QUESTION:\n{question}\n\n"
            f"CORPUS EXCERPTS:\n{context_text}\n\n"
            "Return JSON only."
        )
        messages = [
            {"role": "system", "content": [{"type": "text", "text": system}]},
            {"role": "user", "content": [{"type": "text", "text": user}]},
        ]
        payload = _extract_json(self._generate(messages, max_new_tokens=64))
        answer = str(payload.get("answer") or "").strip()
        citations = payload.get("citations")
        if not isinstance(citations, list):
            citations = []
        citations = [str(value).strip() for value in citations if str(value).strip()]
        return {"answer": answer, "citations": citations}
