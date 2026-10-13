FROM python:3.11.16-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    PORT=8000 \
    LINKSIFTY_DEMO_MODE=false

WORKDIR /app
COPY pyproject.toml uv.lock .python-version README.md ./
COPY backend/pyproject.toml backend/pyproject.toml
COPY backend/src/ backend/src/

RUN uv sync --locked --package linksifty --no-dev --no-editable \
    && useradd --create-home --uid 10001 app

USER app
EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn linksifty.main:app --host 0.0.0.0 --port \"${PORT:-8000}\""]
