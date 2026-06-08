#!/usr/bin/env bash
# refresh.sh — entrypoint Gate A. Rigenera la tabella anelli in STATE.md dai check
# eseguibili definiti in state/rings.json. Uso: bash state/refresh.sh [SESSION_ID]
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$DIR/refresh.py" "$@"
