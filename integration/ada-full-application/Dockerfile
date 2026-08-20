FROM python:3.14.2-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_HTTP_TIMEOUT=120 \
    UV_PROJECT_ENVIRONMENT=/workspace/.venv

WORKDIR /workspace

COPY backend /workspace/backend
COPY connectivity /workspace/connectivity
COPY web /workspace/web
COPY scopes/ada /workspace/scopes/ada
COPY integration/ada-full-application/tests /workspace/integration/ada-full-application/tests
COPY integration/ada-full-application/e2e_pages /workspace/e2e_pages

WORKDIR /workspace/connectivity

RUN uv sync \
        --only-group dev \
        --frozen \
    && uv sync \
        --package atlanticus-cosmos \
        --no-default-groups \
        --inexact \
        --frozen \
        --no-editable \
    && uv sync \
        --package atlanticus-http \
        --no-default-groups \
        --inexact \
        --frozen \
        --no-editable

WORKDIR /workspace/web

RUN uv sync \
        --package atlanticus-web-composition-runtime-infrastructure \
        --no-default-groups \
        --inexact \
        --frozen \
        --no-editable \
    && uv sync \
        --package atlanticus-web-identity-app-service \
        --no-default-groups \
        --inexact \
        --frozen \
        --no-editable

WORKDIR /workspace/scopes/ada

RUN uv sync \
        --package ada-composition-web-deployment \
        --no-default-groups \
        --inexact \
        --frozen \
        --no-editable

WORKDIR /workspace

ENTRYPOINT [".venv/bin/python", "-m", "pytest", "-q", "-s", "integration/ada-full-application/tests"]
