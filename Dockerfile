# Multi-stage build keeps the final image small (only runtime deps, no build tools).
# Small images = faster deploys, smaller attack surface.

# --- Stage 1: build dependencies into a virtualenv -------------------------
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN python -m venv /venv \
    && /venv/bin/pip install --no-cache-dir --upgrade pip \
    && /venv/bin/pip install --no-cache-dir -r requirements.txt \
    && /venv/bin/pip uninstall -y pip

# --- Stage 2: minimal runtime image ----------------------------------------
FROM python:3.12-slim AS runtime

# Patch OS packages, and remove pip/setuptools from the runtime image: the app
# runs from the prebuilt /venv, so they are not needed, and removing them also
# removes the copies of urllib3, msgpack and setuptools they bundle.
# Found by scanning the first build with Trivy.
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && pip uninstall -y pip setuptools wheel

# Security hardening: run as a non-root user, never as root.
RUN groupadd --system appgroup \
    && useradd --system --gid appgroup --no-create-home appuser

WORKDIR /app
COPY --from=builder /venv /venv
COPY app ./app

ENV PATH="/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser

EXPOSE 8000

# Container-level healthcheck so the orchestrator knows if the app is healthy.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
