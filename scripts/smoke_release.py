"""Exercise native CLI branches using private temporary data, without Docker mutations."""
import json
from pathlib import Path
import platform
import subprocess
import tempfile


def main():
    root = Path(__file__).resolve().parent.parent
    executable = root / "dist/CLIProxyAPI-Server"
    if platform.system() == "Windows":
        executable = executable.with_suffix(".exe")
    elif platform.system() == "Darwin":
        executable = root / "dist/CLIProxyAPI-Server.app/Contents/MacOS/CLIProxyAPI-Server"
    with tempfile.TemporaryDirectory(prefix="codexx native smoke ") as directory:
        temporary = Path(directory)
        data = temporary / "data with spaces"
        def run(arguments, expected=0):
            report = temporary / "report.json"
            report.unlink(missing_ok=True)
            result = subprocess.run([str(executable), *arguments, "--data-dir", str(data), "--report", str(report)],
                                    capture_output=True, timeout=45)
            if result.returncode != expected or not report.is_file():
                raise RuntimeError("Native CLI smoke failed: " + arguments[0])
            return json.loads(report.read_text(encoding="utf-8"))
        assert run(["--init"])["created"]
        credentials = (data / ".credentials.json").read_bytes()
        assert run(["--init"])["preserved_existing"]
        assert credentials == (data / ".credentials.json").read_bytes()
        profile = temporary / "connection.cliproxy"
        assert not run(["--export-profile", "--host", "localhost", "--output", str(profile)])["contains_management_password"]
        assert "mgmt_password" not in profile.read_text(encoding="utf-8")
        report = run(["--check-offline", "--bundle-dir", str(temporary / "missing")], expected=2)
        assert not report["ready"]
    print("Native initialization, preservation, export and offline diagnostics passed.")


if __name__ == "__main__":
    main()
