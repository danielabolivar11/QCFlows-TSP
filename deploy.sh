#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

git pull --recurse-submoodules

UV="$HOME/.local/bin/uv"

"$UV" sync
"$UV" sync --project src/qcflows_interface
