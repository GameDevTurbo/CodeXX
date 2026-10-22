#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ "${1:-}" == "launcher.py" ]]; then shift; fi
exec bash "$DIR/scripts/start.sh" server "$@"
