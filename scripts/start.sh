#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ROLE="${1:-client}"
shift || true
case "$ROLE" in
  client) NAME="CLIProxyAPI-Client" ;;
  server) NAME="CLIProxyAPI-Server" ;;
  *) echo "Unknown role: $ROLE" >&2; exit 2 ;;
esac
if [[ "$(uname -s)" == Darwin && -d "$ROOT/$NAME.app" ]]; then
  if [[ $# -eq 0 ]]; then exec open "$ROOT/$NAME.app"; fi
  exec "$ROOT/$NAME.app/Contents/MacOS/$NAME" "$@"
fi
if [[ -x "$ROOT/$NAME" ]]; then exec "$ROOT/$NAME" "$@"; fi
for PYTHON in python3 python /opt/homebrew/bin/python3 /usr/local/bin/python3; do
  if command -v "$PYTHON" >/dev/null 2>&1 && "$PYTHON" -c 'import sys; assert sys.version_info >= (3,10)' 2>/dev/null; then
    exec "$PYTHON" "$ROOT/scripts/launch.py" --role "$ROLE" -- "$@"
  fi
done
echo "Python 3.10+ with tkinter is required for source mode. Prefer the prebuilt release." >&2
exit 1
