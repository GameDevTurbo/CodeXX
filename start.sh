#!/bin/bash
# CLIProxyAPI Launcher — macOS / Linux
cd "$(dirname "$0")"

get_python() {
    for cmd in python3 python; do
        command -v "$cmd" &>/dev/null && { echo "$cmd"; return; }
    done
}

install_python_macos() {
    echo "Python not found."
    if command -v brew &>/dev/null; then
        echo "Installing via Homebrew..."
        brew install python3
    else
        echo "Opening python.org download page..."
        open "https://www.python.org/downloads/"
        echo "After installing Python, run this script again."
        exit 1
    fi
}

install_python_linux() {
    echo "Python not found. Trying package manager..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y python3 python3-pip python3-tk
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3 python3-pip python3-tkinter
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm python python-pip tk
    else
        echo "Cannot auto-install. Please install Python 3 manually."
        exit 1
    fi
}

PYTHON=$(get_python)

if [ -z "$PYTHON" ]; then
    OS=$(uname -s)
    if [ "$OS" = "Darwin" ]; then
        install_python_macos
    else
        install_python_linux
    fi
    PYTHON=$(get_python)
fi

if [ -z "$PYTHON" ]; then
    echo "Python still not found. Please install Python 3 from https://python.org"
    exit 1
fi

echo "Using: $($PYTHON --version)"
$PYTHON -m pip install customtkinter -q 2>/dev/null
$PYTHON launcher.py
