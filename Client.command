#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ -f "$DIR/../CodeXX-Client/Client.command" ]]; then
  exec bash "$DIR/../CodeXX-Client/Client.command" "$@"
fi
exec open "https://github.com/GameDevTurbo/CodeXX-Client/releases"
