#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ARTIFACT_DIR="$ROOT_DIR/artifacts/web/ada-application-base"
SMOKE_DIR="$ROOT_DIR/integration/ada-application-base-runtime"
IMAGE="atlanticus-ada-application-base:local"
SUFFIX="${$}"
NETWORK="atlanticus-r18b-${SUFFIX}"
COSMOS_CONTAINER="atlanticus-r18b-cosmos-${SUFFIX}"
APP_CONTAINER="atlanticus-r18b-app-${SUFFIX}"
RUNTIME_DIR="$SMOKE_DIR/.runtime"
ENV_FILE="$RUNTIME_DIR/environment-${SUFFIX}.env"
COSMOS_KEY='C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=='
DATABASE="ada-r18b-${SUFFIX}"
SAFE_ROOT="conciencia_situacional/__atlanticus_r18b_smoke"

INPUT_ENV_FILE="${1:-${ATLANTICUS_SMOKE_ENV_FILE:-}}"

read_env_value() {
    local file="$1"
    local key="$2"
    python - "$file" "$key" <<'PYENV'
from __future__ import annotations

import sys
from pathlib import Path

path = Path(sys.argv[1])
key = sys.argv[2]
for raw_line in path.read_text(encoding='utf-8').splitlines():
    line = raw_line.strip()
    if not line or line.startswith('#') or '=' not in line:
        continue
    name, value = line.split('=', 1)
    if name.strip() != key:
        continue
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    print(value, end='')
    raise SystemExit(0)
raise SystemExit(1)
PYENV
}

if [[ -n "$INPUT_ENV_FILE" ]]; then
    if [[ ! -f "$INPUT_ENV_FILE" ]]; then
        echo 'Smoke environment file does not exist.' >&2
        exit 1
    fi
    if [[ -z "${ATLANTICUS_SHAREPOINT_READ_ENDPOINT:-}" ]]; then
        ATLANTICUS_SHAREPOINT_READ_ENDPOINT="$(read_env_value "$INPUT_ENV_FILE" ATLANTICUS_SHAREPOINT_READ_ENDPOINT || true)"
    fi
    if [[ -z "${ATLANTICUS_SHAREPOINT_WRITE_ENDPOINT:-}" ]]; then
        ATLANTICUS_SHAREPOINT_WRITE_ENDPOINT="$(read_env_value "$INPUT_ENV_FILE" ATLANTICUS_SHAREPOINT_WRITE_ENDPOINT || true)"
    fi
fi

if [[ -z "${ATLANTICUS_SHAREPOINT_READ_ENDPOINT:-}" ]]; then
    echo 'ATLANTICUS_SHAREPOINT_READ_ENDPOINT is required (export it or pass an env file as the first argument).' >&2
    exit 1
fi
if [[ -z "${ATLANTICUS_SHAREPOINT_WRITE_ENDPOINT:-}" ]]; then
    echo 'ATLANTICUS_SHAREPOINT_WRITE_ENDPOINT is required (export it or pass an env file as the first argument).' >&2
    exit 1
fi

cleanup() {
    docker rm -f "$APP_CONTAINER" >/dev/null 2>&1 || true
    docker rm -f "$COSMOS_CONTAINER" >/dev/null 2>&1 || true
    docker network rm "$NETWORK" >/dev/null 2>&1 || true
    rm -f "$ENV_FILE"
}
trap cleanup EXIT

mkdir -p "$RUNTIME_DIR"
rm -f "$ENV_FILE"
umask 077
{
    printf 'ATLANTICUS_ENVIRONMENT=production\n'
    printf 'ATLANTICUS_IDENTITY_PROVIDER=app_service\n'
    printf 'ATLANTICUS_COSMOS_READY_URL=http://cosmos-emulator:8080/ready\n'
    printf 'ATLANTICUS_COSMOS_ENDPOINT=http://cosmos-emulator:8081\n'
    printf 'ATLANTICUS_COSMOS_KEY=%s\n' "$COSMOS_KEY"
    printf 'ATLANTICUS_COSMOS_DATABASE=%s\n' "$DATABASE"
    printf 'ATLANTICUS_COSMOS_ALLOW_INSECURE_HTTP=true\n'
    printf 'ATLANTICUS_FLASK_SECRET_KEY=%s\n' "$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
    printf 'ATLANTICUS_SHAREPOINT_READ_ENDPOINT=%s\n' "$ATLANTICUS_SHAREPOINT_READ_ENDPOINT"
    printf 'ATLANTICUS_SHAREPOINT_WRITE_ENDPOINT=%s\n' "$ATLANTICUS_SHAREPOINT_WRITE_ENDPOINT"
    printf 'ATLANTICUS_SHAREPOINT_ROOT_PATH=%s\n' "$SAFE_ROOT"
    printf 'ATLANTICUS_SHAREPOINT_TOOL_PATH=operaciones_integradas\n'
    printf 'ATLANTICUS_AZURE_OBSERVABILITY_MODE=off\n'
    printf 'ATLANTICUS_SMOKE_APPLICATION_URL=http://ada-application-base:8000\n'
} > "$ENV_FILE"

if [[ ! -f "$ARTIFACT_DIR/uv.lock" ]]; then
    (
        cd "$ARTIFACT_DIR"
        uv lock
    )
fi

docker build \
    -f "$ROOT_DIR/deployment/web/Dockerfile" \
    -t "$IMAGE" \
    "$ARTIFACT_DIR"

docker network create "$NETWORK" >/dev/null

docker run -d \
    --name "$COSMOS_CONTAINER" \
    --network "$NETWORK" \
    --hostname cosmos-emulator \
    --memory 2g \
    --cpus 1.0 \
    -e PROTOCOL=http \
    -e GATEWAY_PUBLIC_ENDPOINT=cosmos-emulator \
    -e ENABLE_EXPLORER=false \
    -e ENABLE_TELEMETRY=false \
    -e LOG_LEVEL=warn \
    mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-latest >/dev/null

docker run --rm \
    --network "$NETWORK" \
    --env-file "$ENV_FILE" \
    -v "$SMOKE_DIR:/smoke:ro" \
    "$IMAGE" \
    python /smoke/seed_prepare.py

docker run -d \
    --name "$APP_CONTAINER" \
    --network "$NETWORK" \
    --hostname ada-application-base \
    --env-file "$ENV_FILE" \
    --memory 768m \
    --cpus 0.75 \
    "$IMAGE" >/dev/null

sleep 1
if ! docker ps --filter "name=^/${APP_CONTAINER}$" --filter status=running --format '{{.Names}}' | grep -Fxq "$APP_CONTAINER"; then
    echo 'ADA Application Base container did not remain running.' >&2
    docker logs "$APP_CONTAINER" >&2 || true
    exit 1
fi

LOGS="$(docker logs "$APP_CONTAINER" 2>&1)"
if [[ "$LOGS" != *'Atlanticus Gunicorn capacity'* ]]; then
    echo 'Gunicorn did not report Atlanticus automatic capacity.' >&2
    printf '%s\n' "$LOGS" >&2
    exit 1
fi

if ! docker run --rm \
    --network "$NETWORK" \
    --env-file "$ENV_FILE" \
    -v "$SMOKE_DIR:/smoke:ro" \
    "$IMAGE" \
    python /smoke/exercise_runtime.py; then
    echo 'R18B runtime exercise failed; application logs follow.' >&2
    docker logs "$APP_CONTAINER" >&2 || true
    exit 1
fi

printf 'Gunicorn automatic capacity: OK\n'
printf 'R18B prepare -> runtime -> HTTP smoke passed.\n'
