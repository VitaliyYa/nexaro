# Multi-stage Dockerfile for SmartRent Backend
# Stage 1: Build dependencies with uv
# Stage 2: Slim production runtime

# ---------------------------------------------------------------------------
# Stage 1 — Builder: install dependencies into a virtual environment
# ---------------------------------------------------------------------------
FROM python:3.14-slim AS builder

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first for Docker layer caching
# README.md is required by hatchling build backend during metadata resolution
COPY pyproject.toml uv.lock* README.md ./

# Install production dependencies only (no dev group) into .venv
RUN uv sync --no-dev --frozen --no-editable

# Copy application source code
COPY src/ src/

# ---------------------------------------------------------------------------
# Stage 2 — Runtime: minimal image with only what's needed
# ---------------------------------------------------------------------------
FROM python:3.14-slim AS runtime

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid app --shell /bin/bash --create-home app

WORKDIR /app

# Copy virtual environment and source from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Ensure virtualenv binaries are on PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Single worker — VPS has 1 CPU / 1 GB RAM
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
