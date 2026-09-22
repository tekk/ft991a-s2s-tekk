# ==============================================================================
# YAESU FT-991A OPENAI REALTIME S2S APPLIANCE - DOCKERFILE
# Multi-stage build targeting Linux SBCs (ARM64) & PCs (x86_64)
# ==============================================================================

# Stage 1: Build Web UI
FROM node:20-bookworm-slim AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Python Runtime Environment
FROM python:3.11-slim-bookworm

LABEL maintainer="tekk"
LABEL description="Yaesu FT-991A Transceiver Bridge to OpenAI Realtime Speech-to-Speech"

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies:
# - libportaudio2 & portaudio19-dev: low-latency audio streaming via sounddevice
# - alsa-utils: ALSA soundcard diagnostics & access
# - ffmpeg: OPUS, MP3, OGG, M4A compression
# - curl: healthcheck / diagnostics
RUN apt-get update && apt-get install -y --no-install-recommends \
    libportaudio2 \
    portaudio19-dev \
    alsa-utils \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application backend
COPY backend ./backend

# Copy compiled Web UI from build stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create mount points for persistent storage
RUN mkdir -p /app/data /app/recordings

# Expose default Web UI port
EXPOSE 80

# Healthcheck checking the REST API
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:80/api/config || exit 1

ENTRYPOINT ["python3", "-m", "backend.app"]
CMD ["--no-console"]
