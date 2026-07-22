FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# uv / uvx — required by mcp_client.py to launch the AviationStack MCP server
# (mcp_client.py runs `uvx aviationstack-mcp` as a subprocess).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Shell form so ${PORT} (injected by Render) expands; 8000 is the local fallback.
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}