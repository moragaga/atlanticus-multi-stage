# syntax=docker/dockerfile:1.7

# El stage de UV evita usar pip y mantiene una versión fija del gestor de dependencias.
FROM ghcr.io/astral-sh/uv:0.11.29 AS uv
FROM python:3.14.2-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /usr/app

COPY --from=uv /uv /bin/uv

# Las dependencias productivas deben resolver wheels para Linux; no agregamos toolchain al builder.
# Cada aplicación Web es el contexto de build y aporta pyproject.toml, uv.lock, código y wheels locales.
COPY . .

# La sincronización es reproducible y la caché de UV no forma parte de la imagen final.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev \
    && find . -name '*.pyc' -delete \
    && find . -name '__pycache__' -type d -prune -exec rm -rf {} +

FROM python:3.14.2-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/app/.venv/bin:$PATH"

WORKDIR /usr/app

# Solo copiamos el resultado sincronizado; la caché de UV y archivos ignorados quedan fuera.
COPY --from=builder /usr/app /usr/app

EXPOSE 8000

# Gunicorn usa el contrato transversal de Atlanticus desde gunicorn.conf.py de la aplicación.
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
