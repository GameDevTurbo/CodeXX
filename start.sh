#!/bin/bash
# CLIProxyAPI Client Launcher 鈥?macOS / Linux
# Usage: bash start.sh [client.py]
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="${1:-client.py}"
OS_TYPE="$(uname -s)"

find_python() {
    for cmd in python3 python python3.12 python3.11 python3.10; do
        command -v "$cmd" &>/dev/null && { echo "$cmd"; return 0; }
    done
    for p in /usr/local/bin/python3 /opt/homebrew/bin/python3 \
              /usr/bin/python3 "$HOME/.pyenv/shims/python3" \
              "$HOME/Library/Python/3.12/bin/python3" \
              "/Library/Developer/CommandLineTools/usr/bin/python3"; do
        [ -x "$p" ] && { echo "$p"; return 0; }
    done
    return 1
}

check_tkinter() {
    "$1" -c "import tkinter" 2>/dev/null
}

install_python_and_tk() {
    if [ "$OS_TYPE" = "Darwin" ]; then
        if command -v brew &>/dev/null; then
            echo "Installing Python + tkinter via Homebrew..."
            brew install python-tk 2>/dev/null || brew install python3
        else
            echo "Please install Python from: https://www.python.org/downloads/macos/"
            open "https://www.python.org/downloads/macos/" 2>/dev/null || true
            exit 1
        fi
    else
        echo "Installing Python + tkinter..."
        if command -v apt-get &>/dev/null; then
            sudo apt-get install -y python3 python3-pip python3-tk
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y python3 python3-pip python3-tkinter
        elif command -v pacman &>/dev/null; then
            sudo pacman -S --noconfirm python python-pip tk
        elif command -v zypper &>/dev/null; then
            sudo zypper install -y python3 python3-pip python3-tk
        else
            echo "Cannot auto-install. Install Python 3 + tkinter manually."
            exit 1
        fi
    fi
}

PY=$(find_python 2>/dev/null || true)

if [ -z "$PY" ]; then
    echo "Python not found. Installing..."
    install_python_and_tk
    PY=$(find_python 2>/dev/null || true)
fi

if [ -z "$PY" ]; then
    echo "Error: Python 3 not found. Install from https://python.org"
    exit 1
fi

# Check tkinter (required for GUI)
if ! check_tkinter "$PY"; then
    echo "tkinter not found. Installing..."
    if [ "$OS_TYPE" = "Darwin" ]; then
        brew install python-tk 2>/dev/null || true
    elif command -v apt-get &>/dev/null; then
        sudo apt-get install -y python3-tk
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3-tkinter
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm tk
    fi
fi

echo "Python: $($PY --version 2>&1)"

# Install customtkinter
"$PY" -m pip install customtkinter -q 2>/dev/null || true

# Launch detached from terminal
"$PY" "$DIR/$SCRIPT" &
disown
