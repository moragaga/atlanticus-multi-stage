#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOCAL_DIR="$ROOT_DIR/integration/ada-application-base-local"
NETWORK='atlanticus-ada-application-base-local'
COSMOS_CONTAINER='atlanticus-ada-application-base-cosmos'
APP_CONTAINER='atlanticus-ada-application-base-app'
ENV_FILE="$LOCAL_DIR/.runtime/environment.env"

docker rm -f "$APP_CONTAINER" >/dev/null 2>&1 || true
docker rm -f "$COSMOS_CONTAINER" >/dev/null 2>&1 || true
docker network rm "$NETWORK" >/dev/null 2>&1 || true
rm -f "$ENV_FILE"
rmdir "$LOCAL_DIR/.runtime" >/dev/null 2>&1 || true

printf 'ADA Application Base local baseline stopped.\n'
