#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ARTIFACT_DIR="$ROOT_DIR/artifacts/web/ada-application-base"
LOCAL_DIR="$ROOT_DIR/integration/ada-application-base-local"
IMAGE='atlanticus-ada-application-base:local'
NETWORK='atlanticus-ada-application-base-local'
COSMOS_CONTAINER='atlanticus-ada-application-base-cosmos'
APP_CONTAINER='atlanticus-ada-application-base-app'
RUNTIME_DIR="$LOCAL_DIR/.runtime"
ENV_FILE="$RUNTIME_DIR/environment.env"
COSMOS_KEY='C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=='
DATABASE='ada-application-base-local'
HOST_PORT="${ATLANTICUS_ADA_BASE_PORT:-8000}"
READY_TIMEOUT_SECONDS=60

cleanup_failed_start() {
    docker rm -f "$APP_CONTAINER" >/dev/null 2>&1 || true
    docker rm -f "$COSMOS_CONTAINER" >/dev/null 2>&1 || true
    docker network rm "$NETWORK" >/dev/null 2>&1 || true
    rm -f "$ENV_FILE"
}

fail() {
    echo "$1" >&2
    exit 1
}

if ! command -v docker >/dev/null 2>&1; then
    fail 'Docker is required to run the ADA Application Base locally.'
fi
if [[ ! -f "$ARTIFACT_DIR/uv.lock" ]]; then
    fail 'ADA Application Base artifact lock is required.'
fi
if [[ ! "$HOST_PORT" =~ ^[0-9]+$ ]] || (( HOST_PORT < 1 || HOST_PORT > 65535 )); then
    fail 'ATLANTICUS_ADA_BASE_PORT must be a valid TCP port.'
fi

for container in "$APP_CONTAINER" "$COSMOS_CONTAINER"; do
    if docker ps -a --format '{{.Names}}' | grep -Fxq "$container"; then
        fail "Local ADA baseline already exists. Run integration/ada-application-base-local/stop-local.sh first."
    fi
done

docker network rm "$NETWORK" >/dev/null 2>&1 || true
mkdir -p "$RUNTIME_DIR"
rm -f "$ENV_FILE"
umask 077
{
    printf 'ATLANTICUS_ENVIRONMENT=local\n'
    printf 'ATLANTICUS_COSMOS_READY_URL=http://cosmos-emulator:8080/ready\n'
    printf 'ATLANTICUS_COSMOS_ENDPOINT=http://cosmos-emulator:8081\n'
    printf 'ATLANTICUS_COSMOS_KEY=%s\n' "$COSMOS_KEY"
    printf 'ATLANTICUS_COSMOS_DATABASE=%s\n' "$DATABASE"
    printf 'ATLANTICUS_COSMOS_ALLOW_INSECURE_HTTP=true\n'
    printf 'ATLANTICUS_FLASK_SECRET_KEY=%s\n' "$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
    printf 'ATLANTICUS_AZURE_OBSERVABILITY_MODE=off\n'
} > "$ENV_FILE"

trap cleanup_failed_start ERR

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
    -v "$LOCAL_DIR:/local:ro" \
    "$IMAGE" \
    python /local/provision.py

docker run -d \
    --name "$APP_CONTAINER" \
    --network "$NETWORK" \
    --env-file "$ENV_FILE" \
    --memory 768m \
    --cpus 0.75 \
    -p "127.0.0.1:${HOST_PORT}:8000" \
    "$IMAGE" >/dev/null

ready=false
for ((attempt = 0; attempt < READY_TIMEOUT_SECONDS; attempt++)); do
    if docker exec "$APP_CONTAINER" python -c \
        "from urllib.request import urlopen; response=urlopen('http://127.0.0.1:8000/health/ready', timeout=2); raise SystemExit(0 if 200 <= response.status < 300 else 1)" \
        >/dev/null 2>&1; then
        ready=true
        break
    fi
    if ! docker ps --filter "name=^/${APP_CONTAINER}$" --filter status=running --format '{{.Names}}' | grep -Fxq "$APP_CONTAINER"; then
        break
    fi
    sleep 1
done

if [[ "$ready" != true ]]; then
    echo 'ADA Application Base did not become ready; application logs follow.' >&2
    docker logs "$APP_CONTAINER" >&2 || true
    false
fi

trap - ERR
printf 'ADA Application Base local baseline is ready.\n'
printf 'URL: http://127.0.0.1:%s/\n' "$HOST_PORT"
printf 'Environment: local\n'
printf 'Stop: bash integration/ada-application-base-local/stop-local.sh\n'
