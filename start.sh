#!/bin/bash
# CLIProxyAPI Launcher - macOS / Linux
cd "$(dirname "$0")"
python3 -m pip install customtkinter -q 2>/dev/null || pip3 install customtkinter -q 2>/dev/null
python3 launcher.py
