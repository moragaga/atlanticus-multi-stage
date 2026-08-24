#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INTEGRATION_ROOT="$ROOT/integration/web-build"
RUNTIME_ROOT="$INTEGRATION_ROOT/.runtime"
CONTEXT="$RUNTIME_ROOT/context"
BUILD_SOURCES="$RUNTIME_ROOT/build-sources"
IMAGE="atlanticus-web-build-smoke:local"
CONTAINER="atlanticus-web-build-smoke"
PORT="${ATLANTICUS_WEB_BUILD_SMOKE_PORT:-18050}"

cleanup() {
    docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
}
trap cleanup EXIT

rm -rf "$RUNTIME_ROOT"
mkdir -p "$CONTEXT/wheels" "$BUILD_SOURCES"
cp -R "$INTEGRATION_ROOT/fixture/." "$CONTEXT/"
cp "$ROOT/deployment/web/Dockerfile.dockerignore" "$CONTEXT/.dockerignore"
cp "$ROOT/web/applications/reference/gunicorn.conf.py" "$CONTEXT/gunicorn.conf.py"
cp -R "$ROOT/web/framework/observability" "$BUILD_SOURCES/observability"
cp -R "$ROOT/web/framework/core" "$BUILD_SOURCES/core"

if grep -Eq '^[[:space:]]*(preload_app|debug)[[:space:]]*=' "$CONTEXT/gunicorn.conf.py"; then
    echo 'Production Gunicorn configuration must not define preload_app or debug.' >&2
    exit 1
fi

uv build \
    --wheel \
    --no-sources \
    "$BUILD_SOURCES/observability" \
    --out-dir "$CONTEXT/wheels"

uv build \
    --wheel \
    --no-sources \
    "$BUILD_SOURCES/core" \
    --out-dir "$CONTEXT/wheels"

(
    cd "$CONTEXT"
    uv lock --python 3.14.2
)

docker build \
    --file "$ROOT/deployment/web/Dockerfile" \
    --tag "$IMAGE" \
    "$CONTEXT"

cleanup

docker run \
    --detach \
    --name "$CONTAINER" \
    --memory 768m \
    --cpus 0.75 \
    --publish "127.0.0.1:${PORT}:8000" \
    --env ATLANTICUS_ENVIRONMENT=production \
    "$IMAGE" >/dev/null

for _ in $(seq 1 60); do
    if curl --fail --silent --show-error "http://127.0.0.1:${PORT}/health/live" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

curl --fail --silent --show-error "http://127.0.0.1:${PORT}/health/live" >/dev/null
curl --fail --silent --show-error "http://127.0.0.1:${PORT}/assets/app.min.css" >/dev/null
curl --fail --silent --show-error \
    "http://127.0.0.1:${PORT}/assets/0010_atlanticus_web/js/0000__00_runtime.js" >/dev/null
curl --fail --silent --show-error \
    "http://127.0.0.1:${PORT}/assets/0900_smoke_application/js/0000__900_application.js" >/dev/null

for source_path in \
    '/assets/0010_atlanticus_web/css/0000__00_tokens.css' \
    '/assets/css/900_override.css'; do
    source_status="$(curl --silent --output /dev/null --write-out '%{http_code}' \
        "http://127.0.0.1:${PORT}${source_path}")"
    if [[ "$source_status" != "404" ]]; then
        echo "Expected unminified CSS to be unavailable at ${source_path}, got $source_status" >&2
        exit 1
    fi
done

gunicorn_logs="$(docker logs "$CONTAINER" 2>&1)"
if ! grep -Fq 'Atlanticus Gunicorn capacity workers=' <<<"$gunicorn_logs"; then
    echo 'Gunicorn did not report Atlanticus automatic capacity.' >&2
    printf '%s\n' "$gunicorn_logs" >&2
    exit 1
fi

docker exec "$CONTAINER" python /usr/app/verify_snapshot.py

echo 'R18A Docker Web build smoke passed.'
