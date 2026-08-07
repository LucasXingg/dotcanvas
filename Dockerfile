# syntax=docker/dockerfile:1
FROM node:20-alpine AS frontend-build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend .
RUN npm run build

FROM python:3.12-slim AS base

# Runtime libs for cairosvg; build tools so install_package() can compile
# C-extension sdists when no compatible wheel exists for the current Python.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
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
COPY --from=frontend-build /app/dist ./frontend/dist
COPY server.py ./
COPY src ./src

# Install project dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# Provide a default config file inside the image (can be overridden via volume)
RUN if [ ! -f configs/config.yaml ]; then cp configs/config-example.yaml configs/config.yaml; fi

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
