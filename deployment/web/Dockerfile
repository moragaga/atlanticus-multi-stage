# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:0.11.29 AS uv
FROM python:3.14.2-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /usr/app

COPY --from=uv /uv /bin/uv

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev \
    && find . -name '*.pyc' -delete \
    && find . -name '__pycache__' -type d -prune -exec rm -rf {} +

FROM python:3.14.2-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/app/.venv/bin:$PATH"

WORKDIR /usr/app

COPY --from=builder /usr/app /usr/app

EXPOSE 8000

CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
