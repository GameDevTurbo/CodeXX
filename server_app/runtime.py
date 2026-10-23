"""Docker discovery and bounded operations shared by GUI and diagnostics."""
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import time


def docker_executable():
    found = shutil.which("docker")
    if found:
        return found
    candidates = []
    if sys.platform == "darwin":
        candidates = [Path("/Applications/Docker.app/Contents/Resources/bin/docker"),
                      Path.home() / "Applications/Docker.app/Contents/Resources/bin/docker"]
    elif os.name == "nt":
        candidates = [Path(os.environ.get("ProgramFiles", r"C:\Program Files")) /
                      "Docker/Docker/resources/bin/docker.exe",
                      Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) /
                      "Programs/DockerDesktop/resources/bin/docker.exe"]
    return next((str(path) for path in candidates if path.is_file() and os.access(path, os.X_OK)), None)


def docker_environment(executable):
    environment = os.environ.copy()
    # Finder does not inherit a shell's PATH; credential helpers live beside Docker.
    environment["PATH"] = str(Path(executable).parent) + os.pathsep + environment.get("PATH", "")
    return environment


def process_options():
    return {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}


def docker_running():
    executable = docker_executable()
    if not executable:
        return False
    try:
        return subprocess.run([executable, "info"], env=docker_environment(executable),
                              capture_output=True, timeout=6, **process_options()).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def compose_operation(root, arguments, log, timeout=None, heartbeat=15):
    executable = docker_executable()
    if not executable:
        log("未找到 Docker。请安装 Docker Desktop，首次启动后完成系统授权。", "error")
        return 127
    limit = timeout if timeout is not None else (600 if arguments[:1] == ["pull"] else 120)
    log("正在执行 docker compose " + " ".join(arguments), "dim")
    try:
        process = subprocess.Popen([executable, "compose", *arguments], cwd=root,
                                   env=docker_environment(executable), stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                                   **process_options())
    except OSError:
        log("无法启动 Docker 命令，请运行环境检查。", "error")
        return 127
    lines = queue.Queue()

    def collect():
        try:
            for line in process.stdout:
                lines.put(line.rstrip())
        finally:
            process.stdout.close()
            lines.put(None)

    threading.Thread(target=collect, daemon=True).start()
    started = last_notice = time.monotonic()
    while True:
        elapsed = time.monotonic() - started
        if elapsed >= limit:
            process.kill()
            process.wait()
            log("操作超时；已停止等待，Docker 后台任务可能仍在继续。请先检查容器状态，勿反复部署。", "error")
            log("拉取：检查网络、Docker 代理及钥匙串提示；启动：检查目录共享授权、端口占用和容器网络。", "warn")
            return 124
        try:
            line = lines.get(timeout=min(0.5, max(0.01, limit - elapsed)))
        except queue.Empty:
            line = ""
        if line is None:
            try:
                code = process.wait(timeout=max(0.01, limit - elapsed))
            except subprocess.TimeoutExpired:
                continue
            if code:
                log("命令失败，未标记部署完成。请检查 Docker 授权、代理、目录共享及端口占用。", "error")
            return code
        if line:
            log(line, "error" if any(word in line.lower() for word in ("error", "failed", "fatal")) else "normal")
        if time.monotonic() - last_notice >= heartbeat:
            log("仍在等待 Docker；如有系统密码、钥匙串或文件访问弹窗，请在本机确认。", "warn")
            last_notice = time.monotonic()
