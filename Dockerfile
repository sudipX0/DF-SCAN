# Python base
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install OS deps (build tools + runtime libs for OpenCV/Torch)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    python3-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    libgomp1 \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Create and use a virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Workdir
WORKDIR /app

# Install Python deps with cache mount (speeds up rebuilds)
COPY requirements.txt ./requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy source
COPY backend ./backend
COPY frontend ./frontend

# Ensure temp dir exists
RUN mkdir -p /app/backend/temp

# Expose FastAPI port
EXPOSE 8000

# Run from backend so relative imports work (from model import ...)
WORKDIR /app/backend
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]