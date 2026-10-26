#!/usr/bin/env bash
set -euo pipefail

exec start-notebook.sh \
    --ip=0.0.0.0 \
    --port=8888 \
    --no-browser \
    --NotebookApp.token="${JUPYTER_TOKEN:-}" \
    --NotebookApp.password=""
