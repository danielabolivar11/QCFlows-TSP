#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

git pull --recurse-submodules

uv sync
uv sync --project src/qcflows_interface
