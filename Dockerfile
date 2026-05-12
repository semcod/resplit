# rebuild — official Docker image
# ghcr.io/semcod/rebuild:latest
#
# Stages:
#   builder  – install Python deps + Playwright browsers
#   runtime  – slim final image

ARG PYTHON_VERSION=3.11
ARG PLAYWRIGHT_VERSION=1.44

# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: builder
# ─────────────────────────────────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim AS builder

WORKDIR /build

# System deps needed to build Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY rebuild/ rebuild/

RUN pip install --upgrade pip \
    && pip install --no-cache-dir ".[screenshots]"

# Install Playwright browsers (Chromium only for lightweight image)
RUN playwright install chromium \
    && playwright install-deps chromium

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: runtime
# ─────────────────────────────────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim AS runtime

LABEL org.opencontainers.image.title="rebuild" \
      org.opencontainers.image.description="Historical deployment analysis — walk git history, deploy, test endpoints" \
      org.opencontainers.image.url="https://github.com/semcod/resplit" \
      org.opencontainers.image.source="https://github.com/semcod/resplit" \
      org.opencontainers.image.licenses="Apache-2.0"

# Runtime system deps: git (required), docker CLI (optional for docker-compose deploys)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/rebuild /usr/local/bin/rebuild

# Copy Playwright browser binaries and deps
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

WORKDIR /workspace

# Default: show help
ENTRYPOINT ["rebuild"]
CMD ["--help"]
