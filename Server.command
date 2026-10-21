#!/bin/bash
# Double-click this in Finder to open the Server (Deploy) tool
DIR="$(cd "$(dirname "$0")" && pwd)"
bash "$DIR/start.sh" launcher.py
