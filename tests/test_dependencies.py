import io
import json
import os
from pathlib import Path
import queue
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import zipfile

from server_app import dependencies as deps, storage
from scripts.package_offline import package


class DependencyTests(unittest.TestCase):
    def test_translocated_app_finds_original_offline_directory(self):
        with tempfile.TemporaryDirectory(prefix="codexx downloaded ") as directory:
            root = Path(directory)
            bundle = root / "offline_deps/macOS-arm64"
            bundle.mkdir(parents=True)
            self.bundle(bundle)
            app = root / "CLIProxyAPI-Server.app"
            moved = "/private/tmp/AppTranslocation/uuid/d/CLIProxyAPI-Server.app/Contents/MacOS/CLIProxyAPI-Server"
            with patch.dict(os.environ, {}, clear=True), \
                    patch.object(deps.sys, "frozen", True, create=True), \
                    patch.object(deps.sys, "executable", moved), \
                    patch("server_app.macos_paths.original_app_path", return_value=app), \
                    patch.object(deps, "download", side_effect=AssertionError("Unexpected download")):
                self.assertEqual(deps.bundle_directory("macOS-arm64"), bundle)
                self.assertEqual(deps.ensure_installer(bundle, "macOS-arm64", "docker", lambda *args: None), (bundle / "Docker.dmg").resolve())

    def test_unresolved_translocation_never_downloads_or_pulls(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.dict(os.environ, {}, clear=True), \
                patch.object(deps, "package_directory", return_value=Path("/private/tmp/AppTranslocation/uuid/d")), \
                patch.object(deps, "download", side_effect=AssertionError("Unexpected download")), \
                patch.object(deps, "docker_command", side_effect=AssertionError("Unexpected Docker command")):
            with self.assertRaisesRegex(ValueError, "临时运行路径"):
                deps.ensure_installer(directory, "macOS-arm64", "docker", lambda *args: None)
            with self.assertRaisesRegex(ValueError, "临时运行路径"):
                deps.ensure_image(directory, "macOS-arm64", lambda *args: None)

    def bundle(self, root, target="macOS-arm64"):
        files = {}
        names = {key: value[0] for key, value in deps.catalog(target).items()}
        names.update(image="cli-proxy-api-image.tar", management="management.html")
        for component, name in names.items():
            path = root / name
            path.write_bytes((component + " payload").encode())
            files[component] = {"name": name, "size": path.stat().st_size, "sha256": deps.sha256(path)}
        data = {"schema_version": 1, "target": target, "files": files,
                "image": {"tag": deps.IMAGE, "platform": deps.image_platform(target), "id": "sha256:" + "a" * 64}}
        deps.save_manifest(root, data)
        return data

    def test_cached_installers_work_with_network_disabled(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.bundle(root)
            with patch.object(deps.urllib.request, "urlopen", side_effect=AssertionError("Unexpected network")):
                path = deps.ensure_installer(root, "macOS-arm64", "docker", lambda *args: None, offline=True)
                self.assertEqual(path.name, "Docker.dmg")
                self.assertTrue(deps.check_bundle(root, "macOS-arm64")["ready"])

    def test_offline_missing_installer_never_downloads(self):
        with tempfile.TemporaryDirectory() as root, patch.object(deps, "download", side_effect=AssertionError("Unexpected network")):
            with self.assertRaises(ValueError):
                deps.ensure_installer(root, "macOS-arm64", "docker", lambda *args: None, offline=True)

    def test_corruption_and_wrong_architecture_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.bundle(root)
            (root / "Docker.dmg").write_bytes(b"corrupt payload")
            with self.assertRaises(ValueError):
                deps.verified_file(root, "macOS-arm64", "docker")
            with self.assertRaises(ValueError):
                deps.check_bundle(root, "macOS-x64")

    def test_manifest_cannot_reference_outside_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = self.bundle(root)
            data["files"]["docker"]["name"] = "../secret"
            deps.save_manifest(root, data)
            with self.assertRaises(ValueError):
                deps.verified_file(root, "macOS-arm64", "docker")

    def test_offline_load_checks_image_identity_and_installs_panel(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "bundle"
            bundle.mkdir()
            self.bundle(bundle)
            data_root = root / "runtime"
            storage.initialize(data_root)
            credentials = (data_root / ".credentials.json").read_bytes()
            config = (data_root / "config.yaml").read_bytes()
            image = [{"Id": "sha256:" + "a" * 64, "Os": "linux", "Architecture": "arm64"}]
            with patch.object(deps, "docker_command", side_effect=["Loaded", json.dumps(image)]) as command, \
                    patch.object(deps.urllib.request, "urlopen", side_effect=AssertionError("Unexpected network")):
                self.assertTrue(deps.ensure_image(bundle, "macOS-arm64", lambda *args: None, True, data_root))
                self.assertEqual(command.call_args_list[0].args[0][:2], ["image", "load"])
            self.assertEqual((data_root / ".credentials.json").read_bytes(), credentials)
            self.assertEqual((data_root / "config.yaml").read_bytes(), config)
            self.assertTrue((data_root / "static/management.html").is_file())
            compose = (data_root / "docker-compose.yml").read_text()
            self.assertIn("MANAGEMENT_STATIC_PATH", compose)
            self.assertIn("./static:/CLIProxyAPI/static", compose)

    def test_wrong_image_identity_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.bundle(root)
            image = [{"Id": "sha256:" + "b" * 64, "Os": "linux", "Architecture": "arm64"}]
            with patch.object(deps, "docker_command", side_effect=["Loaded", json.dumps(image)]):
                with self.assertRaises(ValueError):
                    deps.ensure_image(root, "macOS-arm64", lambda *args: None, True)

    def test_offline_gui_missing_image_never_pulls(self):
        from server_app.gui import App
        with tempfile.TemporaryDirectory() as directory, \
                patch("server_app.gui.bundle_directory", return_value=Path(directory)), \
                patch("server_app.gui.run_compose", side_effect=AssertionError("Unexpected pull")):
            owner = SimpleNamespace(_safe_log=lambda *args: None)
            with self.assertRaises(ValueError):
                App._prepare_service_image(owner, offline=True)

    def test_offline_packaging_preserves_symlinks_and_excludes_private_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "bundle"
            bundle.mkdir()
            self.bundle(bundle)
            (bundle / ".credentials.json").write_text("must not be packaged")
            base = root / "base.zip"
            with zipfile.ZipFile(base, "w") as archive:
                symlink = zipfile.ZipInfo("CLIProxyAPI-Server-macOS-arm64/App.app/Contents/link")
                symlink.create_system = 3
                symlink.external_attr = 0o120777 << 16
                archive.writestr(symlink, "../Frameworks/library")
            output = root / "offline.zip"
            package(base, bundle, "macOS-arm64", output)
            with zipfile.ZipFile(output) as archive:
                info = archive.getinfo(symlink.filename)
                self.assertEqual(info.external_attr, symlink.external_attr)
                self.assertEqual(archive.read(info), b"../Frameworks/library")
                self.assertFalse(any(".credentials" in name for name in archive.namelist()))
                self.assertIn("CLIProxyAPI-Server-macOS-arm64/offline_deps/macOS-arm64/manifest.json", archive.namelist())

    def test_download_rejects_html_and_keeps_incomplete_download_unpublished(self):
        class Response(io.BytesIO):
            status = 200
            headers = {"Content-Length": "100", "ETag": '"one"'}
            def geturl(self):
                return "https://desktop.docker.com/test"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Docker.dmg"
            with patch.object(deps.urllib.request, "urlopen", side_effect=[Response(b"short") for _ in range(3)]):
                with self.assertRaises(ValueError):
                    deps.download("https://desktop.docker.com/test", path, lambda *args: None)
            self.assertFalse(path.exists())
            self.assertTrue(path.with_name("Docker.dmg.part").exists())
            response = Response(b"<html>error</html>")
            response.headers = {"Content-Type": "text/html"}
            with patch.object(deps.urllib.request, "urlopen", return_value=response):
                with self.assertRaises(ValueError):
                    deps.download("https://desktop.docker.com/test", path, lambda *args: None)


if __name__ == "__main__":
    unittest.main()
