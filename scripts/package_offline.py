"""Add verified offline payloads without extracting/rebuilding native App ZIPs."""
import argparse
from pathlib import Path
import shutil
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from server_app.dependencies import TARGETS, check_bundle, read_manifest, sha256


def package(base, bundle, target, output):
    base, bundle, output = Path(base), Path(bundle), Path(output)
    if not check_bundle(bundle, target)["ready"]:
        raise ValueError("Offline bundle is incomplete")
    manifest = read_manifest(bundle, target)
    expected_root = f"CLIProxyAPI-Server-{target}"
    with zipfile.ZipFile(base) as original:
        if not all(info.filename.split("/", 1)[0] in {expected_root, "__MACOSX"} for info in original.infolist()):
            raise ValueError("Unexpected package root")
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as result:
            for info in original.infolist():
                # Preserve permissions, symlinks and Apple resource metadata.
                with original.open(info) as source, result.open(info, "w", force_zip64=True) as destination:
                    shutil.copyfileobj(source, destination, 1024 * 1024)
            for name in ["manifest.json", *[entry["name"] for entry in manifest["files"].values()]]:
                result.write(bundle / name, f"{expected_root}/offline_deps/{target}/{name}")
    output.with_suffix(".zip.sha256").write_text(sha256(output) + "  " + output.name + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=TARGETS, required=True)
    parser.add_argument("--bundle-dir", type=Path, required=True)
    parser.add_argument("--base-archive", type=Path, required=True)
    options = parser.parse_args()
    output = options.base_archive.with_name(options.base_archive.stem + "-offline.zip")
    package(options.base_archive, options.bundle_dir, options.target, output)
    print(output)


if __name__ == "__main__":
    main()
