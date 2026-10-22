import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile


def main():
    parser = argparse.ArgumentParser(description="Build a minimal, credential-free native release.")
    parser.add_argument("--role", choices=["client", "server"], required=True)
    parser.add_argument("--skip-build", action="store_true")
    options = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    title = options.role.title()
    name = "CLIProxyAPI-" + title
    system = platform.system()
    architecture = {"amd64": "x64", "x86_64": "x64", "arm64": "arm64", "aarch64": "arm64"}.get(platform.machine().lower())
    if not architecture or system not in {"Windows", "Darwin", "Linux"}:
        raise SystemExit("Unsupported build platform or architecture")
    label = "macOS" if system == "Darwin" else system
    if not options.skip_build:
        command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed",
                   "--onedir" if system == "Darwin" else "--onefile", "--name", name,
                   "client.py" if options.role == "client" else "launcher.py"]
        subprocess.run(command, cwd=root, check=True)
    binary = root / "dist" / (name + (".app" if system == "Darwin" else ".exe" if system == "Windows" else ""))
    if not binary.exists():
        raise SystemExit("Native build artifact is missing: " + str(binary))
    executable = binary / "Contents" / "MacOS" / name if system == "Darwin" else binary
    with executable.open("rb") as stream:
        header = stream.read(64)
    if header.startswith(b"version https://git-lfs") or (system == "Windows" and not header.startswith(b"MZ")):
        raise SystemExit("Artifact is not a native executable")
    output = root / "release"
    output.mkdir(exist_ok=True)
    package_name = name + "-" + label + "-" + architecture
    archive = output / (package_name + ".zip")
    with tempfile.TemporaryDirectory(prefix="codexx-package-") as temporary:
        stage = Path(temporary) / package_name
        stage.mkdir()
        if binary.is_dir():
            shutil.copytree(binary, stage / binary.name, symlinks=True)
        else:
            shutil.copy2(binary, stage / binary.name)
        if system == "Windows":
            shutil.copy2(root / (title + ".bat"), stage / (title + ".bat"))
        shutil.copy2(root / "README.md", stage / "README.md")
        shutil.copy2(root / "AI_START.md", stage / "AI_START.md")
        if options.role == "client":
            shutil.copy2(root / "TAILSCALE_FIX.md", stage / "TAILSCALE_FIX.md")
        for document in sorted((root / "docs").rglob("*.md")):
            destination = stage / "docs" / document.relative_to(root / "docs")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(document, destination)
        manifest = {"role": options.role, "platform": label, "architecture": architecture,
                    "python_bundled": True, "contains_credentials": False,
                    "entrypoint": binary.name, "source": "https://github.com/GameDevTurbo/CodeXX" + ("-Client" if options.role == "client" else "")}
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        if system == "Darwin":
            subprocess.run(["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(stage), str(archive)], check=True)
        else:
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
                for path in sorted(stage.rglob("*")):
                    if path.is_file():
                        bundle.write(path, path.relative_to(stage.parent))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".zip.sha256").write_text(digest + "  " + archive.name + "\n", encoding="utf-8")
    print(json.dumps({"archive": str(archive), "sha256": digest, "platform": label, "architecture": architecture}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
