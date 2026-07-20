FROM python:3.13-slim AS builder

WORKDIR /build

# Build-time deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ git libgdal-dev gdal-bin libgeos-dev libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first (keeps image ~1.5GB smaller than default)
RUN pip install --no-cache-dir \
    torch==2.4.0+cpu torchvision==0.19.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
# Skip the torch lines already installed above; install everything else
RUN grep -v -E '^(torch|torchvision|pytorch-lightning|torchmetrics)' requirements.txt \
    | pip install --no-cache-dir -r /dev/stdin

# ── Runtime image ──────────────────────────────────────────────────────────────
FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal-dev gdal-bin libgeos-dev libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY . .

# DeepForest downloads weights on first run; pre-warm the cache at build time
# so production containers start instantly. Skip if bandwidth is a concern.
RUN python -c "from deepforest import main; m = main.deepforest(); m.use_release()" || true

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
