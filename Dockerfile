FROM rocm/pytorch:rocm10.0_ubuntu26.04_py3.14_pytorch_release_2.13.0

ARG MODEL_ID=Qwen/Qwen2.5-VL-3B-Instruct
ARG MODEL_REVISION=66285546d2b821cf421d4f5eb2576359d3770cd3

ENV PYTHONUNBUFFERED=1 \
    HF_HUB_DISABLE_TELEMETRY=1 \
    MODEL_ID=${MODEL_ID} \
    MODEL_REVISION=${MODEL_REVISION} \
    MODEL_DIR=/models/Qwen2.5-VL-3B-Instruct \
    MC3_SOCKET=/tmp/mc3.sock \
    MC3_INDEX_PATH=/tmp/mc3_index.json \
    MC3_OUTPUT_DIR=/app/output

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python3 -c 'import importlib.metadata as m; names={"torch","torchvision","torchaudio","triton","pytorch-triton-rocm"}; print("\n".join(sorted({d.metadata["Name"]+"=="+d.version for d in m.distributions() if (d.metadata["Name"] or "").lower() in names})))' > /tmp/rocm-pins.txt && \
    pip install --no-cache-dir -c /tmp/rocm-pins.txt -r /app/requirements.txt && \
    python3 -c 'import torch; assert "rocm" in torch.__version__.lower(), torch.__version__'

COPY app/download_model.py /app/download_model.py
RUN python3 /app/download_model.py

ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

COPY app/ /app/
RUN mkdir -p /app/output

CMD ["python3", "/app/server.py"]
