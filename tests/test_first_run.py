import contextlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import queue
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from server_app import cli, runtime, storage


class FirstRunTests(unittest.TestCase):
    def test_gui_worker_schedules_without_calling_tk(self):
        from server_app.gui import App
        callbacks = queue.Queue()
        callback = lambda: None
        owner = SimpleNamespace(_ui_tasks=callbacks)
        worker = threading.Thread(target=lambda: App._schedule(owner, 0, callback))
        worker.start()
        worker.join(timeout=2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(callbacks.get_nowait(), (0, callback))
        self.assertTrue(callbacks.empty())

    def test_public_launcher_routes_headless_cli(self):
        with tempfile.TemporaryDirectory(prefix="codexx entry ") as directory:
            root = Path(directory)
            report = root / "init.json"
            result = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / "launcher.py"),
                                     "--init", "--data-dir", str(root / "data with spaces"),
                                     "--report", str(report)], capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0)
            self.assertTrue(json.loads(report.read_text())["created"])

    def test_finder_path_finds_docker_and_helpers(self):
        path = str(Path("/Applications/Docker.app/Contents/Resources/bin/docker"))
        with patch.object(runtime.sys, "platform", "darwin"), \
                patch.object(runtime.shutil, "which", return_value=None), \
                patch.object(Path, "is_file", lambda p: str(p) == path), \
                patch.object(runtime.os, "access", return_value=True):
            self.assertEqual(runtime.docker_executable(), path)
            self.assertEqual(runtime.docker_environment(path)["PATH"].split(os.pathsep)[0],
                             str(Path(path).parent))

    def test_silent_compose_is_bounded_and_does_not_claim_rollback(self):
        real_popen = subprocess.Popen
        messages = []

        def silent(*args, **kwargs):
            return real_popen([sys.executable, "-c", "import time; time.sleep(30)"], **kwargs)

        with tempfile.TemporaryDirectory(prefix="codexx test ") as root, \
                patch.object(runtime, "docker_executable", return_value=sys.executable), \
                patch.object(runtime.subprocess, "Popen", side_effect=silent):
            started = time.monotonic()
            code = runtime.compose_operation(root, ["up", "-d"],
                                             lambda text, kind: messages.append(text),
                                             timeout=0.2, heartbeat=0.05)
        self.assertEqual(code, 124)
        self.assertLess(time.monotonic() - started, 5)
        self.assertTrue(any("后台任务可能仍在继续" in text for text in messages))
        self.assertTrue(any("仍在等待 Docker" in text for text in messages))

    def test_compose_failure_propagates(self):
        real_popen = subprocess.Popen
        messages = []

        def failed(*args, **kwargs):
            return real_popen([sys.executable, "-c", "print('failed'); raise SystemExit(7)"], **kwargs)

        with tempfile.TemporaryDirectory() as root, \
                patch.object(runtime, "docker_executable", return_value=sys.executable), \
                patch.object(runtime.subprocess, "Popen", side_effect=failed):
            code = runtime.compose_operation(root, ["pull"], lambda text, kind: messages.append(text))
        self.assertEqual(code, 7)
        self.assertTrue(any("未标记部署完成" in text for text in messages))

    def test_missing_docker_has_manual_next_step(self):
        with tempfile.TemporaryDirectory() as root, patch.object(cli, "docker_executable", return_value=None):
            report = cli.doctor(Path(root))
        self.assertFalse(report["ready"])
        self.assertTrue(any("安装 Docker" in step for step in report["next_steps"]))
        self.assertIsNone(report["remaining_quota"])

    def test_repeat_setup_preserves_keys_and_partial_setup_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="codexx data ") as directory:
            root = Path(directory)
            storage.initialize(root)
            original = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
            result = storage.initialize(root, port=9001)
            self.assertTrue(result["preserved_existing"])
            self.assertEqual(original, {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()})
            (root / "docker-compose.yml").unlink()
            with self.assertRaises(ValueError):
                storage.initialize(root)
            self.assertEqual((root / "config.yaml").read_bytes(), original["config.yaml"])

    @contextlib.contextmanager
    def models_server(self, enforce_auth):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(401 if enforce_auth and not self.headers.get("Authorization") else 200)
                self.end_headers()
                self.wfile.write(b'{"data": [], "object": "list"}')

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            yield server.server_port
        finally:
            server.shutdown()
            server.server_close()
            worker.join()

    def probe(self, enforce_auth):
        with self.models_server(enforce_auth) as port, tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            storage.initialize(root, port=port)
            key = storage.read_config(root)["api-keys"][0]
            with patch.object(cli, "docker_executable", return_value="fake-docker"), \
                    patch.object(cli.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)):
                result = cli.doctor(root, probe=True)
            self.assertNotIn(key, json.dumps(result))
            return result

    def test_empty_models_are_not_generation_or_zero_quota(self):
        result = self.probe(True)
        self.assertTrue(result["ready"])
        self.assertEqual(result["model_count"], 0)
        self.assertEqual(result["generation"], "not_checked")
        self.assertIsNone(result["remaining_quota"])
        self.assertTrue(any("模型列表为空" in step for step in result["next_steps"]))

    def test_open_api_is_not_reported_as_authenticated(self):
        result = self.probe(False)
        self.assertFalse(result["ready"])
        self.assertEqual(result["api"], "authentication_not_enforced")


if __name__ == "__main__":
    unittest.main()
