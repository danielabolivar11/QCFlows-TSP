#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

git pull --recurse-submodules

UV="$HOME/.local/bin/uv"

"$UV" sync
"$UV" sync --project src/qcflows_interface

# server-specific restart, if this box provides one
if [ -x ./deploy.service-restart.sh ]; then
  ./deploy.service-restart.sh
fi
