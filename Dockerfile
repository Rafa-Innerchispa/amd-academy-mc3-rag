FROM rocm/pytorch:rocm10.0_ubuntu26.04_py3.14_pytorch_release_2.13.0

ENV PYTHONUNBUFFERED=1 \
    MC3_INDEX_PATH=/tmp/mc3_index.json \
    MC3_OUTPUT_DIR=/app/output

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python3 -c 'import torch; assert "rocm" in torch.__version__.lower(), torch.__version__' && \
    python3 -c 'import importlib.metadata as m; print("torch==" + m.version("torch"))' > /tmp/torch-pin.txt && \
    pip install --no-cache-dir -c /tmp/torch-pin.txt -r /app/requirements.txt && \
    python3 -c 'import torch; assert "rocm" in torch.__version__.lower(), torch.__version__'

COPY app/ /app/
RUN mkdir -p /app/output

CMD ["python3", "/app/app.py", "--help"]
