#!/usr/bin/env bash
set -euo pipefail

echo "Atlanticus compress started"

./clean_root.sh

zip -r "atlanticus-multi-stage-version-0.1.0-$(date +%Y%m%d-%H%M%S).zip" . -x "*venv*" "*.idea*" "*.git*" "*.env*" "*.DS_Store*" "*.local-assets*" "*.local-data*"
echo "Atlanticus compress completed successfully."
