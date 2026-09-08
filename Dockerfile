# Multi-stage Dockerfile for EV Backend using Astral uv
FROM ghcr.io/astral-sh/uv:latest AS uv_bin
FROM python:3.12-slim AS builder

WORKDIR /app

# Copy uv binary from official image
COPY --from=uv_bin /uv /uvx /bin/

# Environment settings for uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install dependencies first for optimal Docker layer caching
COPY pyproject.toml README.md ./
RUN uv venv /app/.venv && uv pip install -e .

# Copy application source code
COPY app /app/app
COPY .env.example /app/.env.example

# Final production stage
FROM python:3.12-slim AS runner

WORKDIR /app

# Copy virtualenv and app code from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app /app/app
COPY --from=builder /app/pyproject.toml /app/README.md ./

# Place virtual environment binaries in PATH
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
