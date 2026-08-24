#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ARTIFACT_DIR="$ROOT_DIR/artifacts/web/ada-application-base"
SMOKE_DIR="$ROOT_DIR/integration/ada-access-runtime"
IMAGE="atlanticus-ada-access-r18d4:local"
SUFFIX="${$}"
NETWORK="atlanticus-r18d4-${SUFFIX}"
COSMOS_CONTAINER="atlanticus-r18d4-cosmos-${SUFFIX}"
APP_CONTAINER="atlanticus-r18d4-app-${SUFFIX}"
RUNTIME_DIR="$SMOKE_DIR/.runtime"
ENV_FILE="$RUNTIME_DIR/environment-${SUFFIX}.env"
COSMOS_KEY='C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=='
BOOTSTRAP_EMAIL='atlanticus.r18d4@example.com'

cleanup() {
    docker rm -f "$APP_CONTAINER" >/dev/null 2>&1 || true
    docker rm -f "$COSMOS_CONTAINER" >/dev/null 2>&1 || true
    docker network rm "$NETWORK" >/dev/null 2>&1 || true
    rm -f "$ENV_FILE"
}
trap cleanup EXIT

write_environment() {
    local scenario="$1"
    local environment="$2"
    local database="$3"
    local bootstrap_admin="$4"

    rm -f "$ENV_FILE"
    umask 077
    {
        printf 'ATLANTICUS_ENVIRONMENT=%s\n' "$environment"
        printf 'ATLANTICUS_COSMOS_READY_URL=http://cosmos-emulator:8080/ready\n'
        printf 'ATLANTICUS_COSMOS_ENDPOINT=http://cosmos-emulator:8081\n'
        printf 'ATLANTICUS_COSMOS_KEY=%s\n' "$COSMOS_KEY"
        printf 'ATLANTICUS_COSMOS_DATABASE=%s\n' "$database"
        printf 'ATLANTICUS_COSMOS_ALLOW_INSECURE_HTTP=true\n'
        printf 'ATLANTICUS_FLASK_SECRET_KEY=%s\n' "$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
        printf 'ATLANTICUS_AZURE_OBSERVABILITY_MODE=off\n'
        printf 'ATLANTICUS_SMOKE_APPLICATION_URL=http://%s:8000\n' "$APP_CONTAINER"
        printf 'ATLANTICUS_SMOKE_SCENARIO=%s\n' "$scenario"
        if [[ -n "$bootstrap_admin" ]]; then
            printf 'ATLANTICUS_BOOTSTRAP_ADMIN=%s\n' "$bootstrap_admin"
        fi
    } > "$ENV_FILE"
}

run_scenario() {
    local scenario="$1"
    local environment="$2"
    local bootstrap_admin="$3"
    local database="ada-r18d4-${scenario}-${SUFFIX}"

    write_environment "$scenario" "$environment" "$database" "$bootstrap_admin"

    docker run --rm \
        --network "$NETWORK" \
        --env-file "$ENV_FILE" \
        -v "$SMOKE_DIR:/smoke:ro" \
        "$IMAGE" \
        python /smoke/provision.py

    docker rm -f "$APP_CONTAINER" >/dev/null 2>&1 || true
    docker run -d \
        --name "$APP_CONTAINER" \
        --network "$NETWORK" \
        --env-file "$ENV_FILE" \
        --memory 768m \
        --cpus 0.75 \
        "$IMAGE" >/dev/null

    sleep 1
    if ! docker ps --filter "name=^/${APP_CONTAINER}$" --filter status=running --format '{{.Names}}' | grep -Fxq "$APP_CONTAINER"; then
        echo "Access smoke application did not remain running: $scenario" >&2
        docker logs "$APP_CONTAINER" >&2 || true
        exit 1
    fi

    if ! docker run --rm \
        --network "$NETWORK" \
        --env-file "$ENV_FILE" \
        -v "$SMOKE_DIR:/smoke:ro" \
        "$IMAGE" \
        python /smoke/exercise_access.py; then
        echo "Access smoke failed: $scenario" >&2
        docker logs "$APP_CONTAINER" >&2 || true
        exit 1
    fi

    docker rm -f "$APP_CONTAINER" >/dev/null
}

mkdir -p "$RUNTIME_DIR"

if [[ ! -f "$ARTIFACT_DIR/uv.lock" ]]; then
    echo 'ADA Application Base artifact lock is required.' >&2
    exit 1
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

run_scenario 'local-empty' 'local' 'local-ignored@example.com'
run_scenario 'production-guest' 'production' ''
run_scenario 'production-bootstrap-admin' 'production' "$BOOTSTRAP_EMAIL"

printf 'R18D.4 local empty -> production Guest -> production bootstrap admin smokes passed.\n'
