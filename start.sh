#!/bin/bash
# CLIProxyAPI Launcher — macOS / Linux
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

find_python() {
    for cmd in python3 python python3.12 python3.11 python3.10; do
        if command -v "$cmd" &>/dev/null; then
            echo "$cmd"; return 0
        fi
    done
    # Common non-PATH locations
    for p in \
        /usr/local/bin/python3 \
        /opt/homebrew/bin/python3 \
        /usr/bin/python3 \
        "$HOME/.pyenv/shims/python3" \
        "$HOME/Library/Python/3.12/bin/python3" \
        "/Library/Developer/CommandLineTools/usr/bin/python3"
    do
        [ -x "$p" ] && { echo "$p"; return 0; }
    done
    return 1
}

install_python() {
    OS="$(uname -s)"
    if [ "$OS" = "Darwin" ]; then
        if command -v brew &>/dev/null; then
            echo "Installing Python via Homebrew..."
            brew install python3
        else
            echo "Homebrew not found."
            echo "Install Python from: https://www.python.org/downloads/"
            if command -v open &>/dev/null; then
                open "https://www.python.org/downloads/"
            fi
            exit 1
        fi
    else
        # Linux — try common package managers
        if command -v apt-get &>/dev/null; then
            sudo apt-get install -y python3 python3-pip python3-tk
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y python3 python3-pip python3-tkinter
        elif command -v pacman &>/dev/null; then
            sudo pacman -S --noconfirm python python-pip tk
        elif command -v zypper &>/dev/null; then
            sudo zypper install -y python3 python3-pip python3-tk
        else
            echo "Cannot auto-install Python. Please install Python 3 from https://python.org"
            exit 1
        fi
    fi
}

PY=$(find_python 2>/dev/null || true)

if [ -z "$PY" ]; then
    echo "Python not found. Attempting install..."
    install_python
    PY=$(find_python 2>/dev/null || true)
fi

if [ -z "$PY" ]; then
    echo "Error: Python 3 could not be found or installed."
    echo "Please install Python 3 from https://python.org and try again."
    exit 1
fi

echo "Using: $($PY --version 2>&1)"

# Install customtkinter
"$PY" -m pip install customtkinter -q 2>/dev/null || true

# Launch (detached from terminal)
"$PY" "$DIR/launcher.py" &
disown
