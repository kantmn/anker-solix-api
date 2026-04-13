# ---------- Stage 1: Build dependencies ----------
FROM python:3.14-slim AS builder

# Set the working directory
WORKDIR /app
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Copy only dependency files first (for caching)
COPY anker-solix-api/pyproject.toml ./

# Install dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

RUN poetry install --only main
RUN poetry add requests fastapi uvicorn

# ---------- Stage 2: Runtime ----------
FROM python:3.14-slim

# Set the working directory
WORKDIR /app
ENV PYTHONPATH=/app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.14 /usr/local/lib/python3.14
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app code
COPY anker-solix-api /app/anker_api
COPY script.py /app/

# Set the entrypoint (adjust to your application)
CMD ["python", "script.py"]
