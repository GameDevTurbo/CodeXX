#!/usr/bin/env python3
"""Compatibility entry point for the Server GUI and headless CLI."""
from server_app.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
