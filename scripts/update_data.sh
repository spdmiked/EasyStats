#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../pipeline"
python -m specmeta_pipeline update --provider "${DATA_PROVIDER:-hybrid}" "$@"

