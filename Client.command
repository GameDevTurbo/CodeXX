#!/bin/bash
# Double-click this in Finder to open the Client (Connect) tool
DIR="$(cd "$(dirname "$0")" && pwd)"
bash "$DIR/start.sh" client.py
