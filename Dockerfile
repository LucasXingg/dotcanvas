# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

# Install system dependencies required for cairosvg and friends
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libcairo2 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf-2.0-0 \
        libffi8 \
        shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY pyproject.toml README.md ./
COPY assets ./assets
COPY canvas ./canvas
COPY configs ./configs
COPY docs ./docs
COPY pages ./pages
COPY server.py ./
COPY src ./src

# Install project dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# Provide a default config file inside the image (can be overridden via volume)
RUN if [ ! -f configs/config.yaml ]; then cp configs/config-example.yaml configs/config.yaml; fi

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
