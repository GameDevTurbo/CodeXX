import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import traceback


def main():
    parser = argparse.ArgumentParser(description="Prepare an isolated source runtime and launch CodeXX.")
    parser.add_argument("--role", choices=["client", "server"], required=True)
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    options = parser.parse_args()
    arguments = options.arguments
    if arguments[:1] == ["--"]:
        arguments = arguments[1:]
    diagnostic = any(argument in {"--help", "-h", "--status", "--check-route", "--check-connection",
                                  "--check-generation", "--doctor", "--init", "--harden-runtime",
                                  "--export-profile"} for argument in arguments)
    root = Path(__file__).resolve().parent.parent
    entry = root / ("client.py" if options.role == "client" else "launcher.py")
    directory = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".config")))
    log_path = directory / ("CLIProxyAPI-Client" if options.role == "client" else "CodeXX-Server") / "startup.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log:
        try:
            if sys.version_info < (3, 10):
                raise RuntimeError("Python 3.10 or later is required.")
            environment = root / ".venv"
            python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            if not python.exists():
                subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True, stdout=log, stderr=log)
            requirements = root / "requirements.txt"
            fingerprint = hashlib.sha256(requirements.read_bytes()).hexdigest()
            marker = environment / ".codexx-requirements"
            modules = (["yaml"] if options.role == "server" and diagnostic else
                       ["tkinter", "customtkinter"] + (["tomlkit", "pystray", "PIL"] if options.role == "client" else ["yaml"]))
            probe = "import importlib.util; assert all(importlib.util.find_spec(name) for name in " + repr(modules) + ")"
            ready = subprocess.run([str(python), "-c", probe], stdout=log, stderr=log).returncode == 0
            if not ready or not marker.exists() or marker.read_text() != fingerprint:
                command = [str(python), "-m", "pip", "install", "-r", str(requirements)]
                wheels = root / "offline_deps" / "wheels"
                if wheels.exists():
                    result = subprocess.run(command + ["--no-index", "--find-links", str(wheels)], stdout=log, stderr=log)
                    if result.returncode:
                        subprocess.run(command, check=True, stdout=log, stderr=log)
                else:
                    subprocess.run(command, check=True, stdout=log, stderr=log)
                if subprocess.run([str(python), "-c", probe], stdout=log, stderr=log).returncode != 0:
                    raise RuntimeError("Python is missing Tk or another required module; install a Python distribution with Tk.")
                marker.write_text(fingerprint, encoding="utf-8")
            if diagnostic:
                return subprocess.run([str(python), str(entry), *arguments], cwd=root).returncode
            executable = python.with_name("pythonw.exe") if os.name == "nt" else python
            settings = {"creationflags": subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
            subprocess.Popen([str(executable), str(entry), *arguments], cwd=root, stdin=subprocess.DEVNULL,
                             stdout=log, stderr=log, close_fds=True, **settings)
            return 0
        except Exception:
            traceback.print_exc(file=log)
            print("Startup failed. See " + str(log_path), file=sys.stderr)
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
