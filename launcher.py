if __package__:
    # Keep package execution working for PyInstaller and ``python -m``.
    from .server_app.cli import main
else:
    # Server.command executes this compatibility entry point as a file, so
    # Python does not provide a package context in source mode.
    from server_app.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
