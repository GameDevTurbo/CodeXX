"""Official installer cache and portable, architecture-specific offline bundles."""
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import ssl
import subprocess
import sys
import time
import urllib.request

import certifi

from .runtime import docker_executable, docker_environment, process_options

TARGETS = ("macOS-arm64", "macOS-x64", "Windows-x64", "Linux-x64")
IMAGE = "eceasy/cli-proxy-api:latest"
TAILSCALE_VERSION = "1.104.2"


def current_target():
    system = {"Darwin": "macOS"}.get(platform.system(), platform.system())
    arch = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "x64", "amd64": "x64"}.get(platform.machine().lower())
    target = f"{system}-{arch}"
    if target not in TARGETS:
        raise ValueError("当前系统/架构尚无预编译依赖包。")
    return target


def package_directory():
    if os.environ.get("CODEXX_PACKAGE_DIR"):
        return Path(os.environ["CODEXX_PACKAGE_DIR"]).expanduser().resolve()
    root = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
    if root.name == "MacOS" and root.parent.name == "Contents" and root.parent.parent.suffix == ".app":
        from .macos_paths import original_app_path
        app = root.parent.parent
        original = original_app_path(app)
        root = (original or app).parent
    return root


def bundle_directory(target=None):
    target = target or current_target()
    if os.environ.get("CODEXX_OFFLINE_DIR"):
        return Path(os.environ["CODEXX_OFFLINE_DIR"]).expanduser().resolve()
    local = package_directory() / "offline_deps" / target
    if local.exists() or os.access(package_directory(), os.W_OK):
        return local
    from .storage import data_directory
    return data_directory() / "offline_deps" / target


def catalog(target):
    if target not in TARGETS:
        raise ValueError("不支持的目标系统/架构。")
    if target.startswith("macOS"):
        arch = "arm64" if target.endswith("arm64") else "amd64"
        return {"docker": ("Docker.dmg", f"https://desktop.docker.com/mac/main/{arch}/Docker.dmg"),
                "tailscale": ("Tailscale.pkg", f"https://pkgs.tailscale.com/stable/Tailscale-{TAILSCALE_VERSION}-macos.pkg")}
    if target == "Windows-x64":
        return {"docker": ("Docker-Desktop-Installer.exe", "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"),
                # MSI embeds the x64 payload; do not cache the network bootstrap EXE.
                "tailscale": ("Tailscale.msi", f"https://pkgs.tailscale.com/stable/tailscale-setup-{TAILSCALE_VERSION}-amd64.msi")}
    # Linux prerequisites are distribution-specific and must be installed first.
    return {}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tls_context():
    # Native releases run without a Python installation or its certificate paths.
    context = ssl.create_default_context(cafile=certifi.where())
    context.load_default_certs()
    return context


def read_manifest(root, target):
    path = Path(root) / "manifest.json"
    if not path.exists():
        return {"schema_version": 1, "target": target, "files": {}}
    if path.stat().st_size > 1024 * 1024:
        raise ValueError("离线清单过大。")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1 or data.get("target") != target or not isinstance(data.get("files"), dict):
        raise ValueError("离线包清单无效或系统/架构不匹配。")
    if set(data["files"]) - {*catalog(target), "image", "management"}:
        raise ValueError("离线包清单包含未知组件。")
    return data


def save_manifest(root, data):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    temporary = root / "manifest.json.tmp"
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(root / "manifest.json")


def verified_file(root, target, component):
    root = Path(root).resolve()
    record = read_manifest(root, target)["files"].get(component)
    if record is None:
        return None
    expected = {"image": "cli-proxy-api-image.tar", "management": "management.html"}.get(component) or catalog(target).get(component, (None,))[0]
    if not isinstance(record, dict) or expected is None or record.get("name") != expected:
        raise ValueError("离线文件名称无效。")
    path = root / expected
    if not path.is_file() or path.resolve().parent != root:
        raise ValueError("离线文件缺失或路径无效，请重新准备离线包。")
    if type(record.get("size")) is not int or record["size"] <= 0 or path.stat().st_size != record["size"]:
        raise ValueError("离线文件大小不匹配，请重新准备离线包。")
    if not re.fullmatch(r"[0-9a-f]{64}", str(record.get("sha256", ""))) or sha256(path) != record["sha256"]:
        raise ValueError("离线文件 SHA-256 校验失败，已停止操作。")
    return path


class IncompleteDownload(ValueError):
    pass


def download(url, destination, log, allow_html=False):
    for attempt in range(3):
        try:
            return _download_once(url, destination, log, allow_html)
        except (OSError, IncompleteDownload):
            if attempt == 2:
                raise
            log(f"下载中断，保留进度并重试（{attempt + 2}/3）…", "warn")


def _download_once(url, destination, log, allow_html=False):
    """Resume partial downloads only with a matching server validator."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    validator_file = partial.with_name(partial.name + ".etag")
    headers = {"User-Agent": "CodeXX-Server/1.3"}
    offset = partial.stat().st_size if partial.exists() and validator_file.exists() else 0
    if offset:
        headers.update({"Range": f"bytes={offset}-", "If-Range": validator_file.read_text()})
    request = urllib.request.Request(url, headers=headers)
    started = last_notice = time.monotonic()
    with urllib.request.urlopen(request, timeout=30, context=tls_context()) as response:
        if response.geturl().split(":", 1)[0] != "https":
            raise ValueError("下载被重定向到非 HTTPS 地址。")
        resumed = response.status == 206
        if resumed and (not offset or not response.headers.get("Content-Range", "").startswith(f"bytes {offset}-")):
            raise ValueError("下载续传响应无效。")
        if not resumed:
            offset = 0
        if not allow_html and "text/html" in response.headers.get("Content-Type", "").lower():
            raise ValueError("下载返回网页，而非安装包。")
        validator = response.headers.get("ETag") or response.headers.get("Last-Modified")
        if validator:
            validator_file.write_text(validator)
        else:
            validator_file.unlink(missing_ok=True)
        expected = int(response.headers["Content-Length"]) + offset if response.headers.get("Content-Length") else None
        count = offset
        with partial.open("ab" if resumed else "wb") as stream:
            while True:
                if time.monotonic() - started > 3600:
                    raise TimeoutError("下载超时，进度已保留，可再次重试。")
                block = response.read(1024 * 1024)
                if not block:
                    break
                stream.write(block)
                count += len(block)
                if time.monotonic() - last_notice >= 10:
                    total = f" / {expected // 1048576} MB" if expected else " MB"
                    log(f"{destination.name}: {count // 1048576}{total}", "dim")
                    last_notice = time.monotonic()
        if count == 0 or (expected is not None and count != expected):
            raise IncompleteDownload("下载不完整，进度已保留，可再次重试。")
    partial.replace(destination)
    validator_file.unlink(missing_ok=True)


def ensure_installer(root, target, component, log, offline=False):
    cached = verified_file(root, target, component)
    if cached:
        log(f"使用本地安装包：{cached.name}（SHA-256 已核对）", "ok")
        return cached
    if offline:
        raise ValueError("离线包缺少安装程序；请在联网机器准备完整离线包。")
    if "AppTranslocation" in package_directory().parts and not os.environ.get("CODEXX_OFFLINE_DIR"):
        raise ValueError("macOS 临时运行路径无法定位安装包。请点击“选择离线包”，或关闭窗口后使用解压目录内的 Server.command；未开始下载。")
    if component not in catalog(target):
        raise ValueError("Linux 请先按发行版安装 Docker Engine、Compose；Tailscale 按官方安装说明准备。")
    name, url = catalog(target)[component]
    log(f"正在从官方站点下载 {name}…", "normal")
    path = Path(root) / name
    download(url, path, log)
    digest = sha256(path)
    if component == "tailscale":
        with urllib.request.urlopen(url + ".sha256", timeout=30, context=tls_context()) as response:
            vendor_digest = response.read(4096).decode().strip().split()[0].lower()
        if not re.fullmatch(r"[0-9a-f]{64}", vendor_digest) or vendor_digest != digest:
            raise ValueError("Tailscale 官方校验值不匹配，已停止使用下载文件。")
    data = read_manifest(root, target)
    data["files"][component] = {"name": name, "size": path.stat().st_size, "sha256": digest, "source": url}
    save_manifest(root, data)
    log(f"{name} 已下载并记录 SHA-256。", "ok")
    return path


def open_installer(path):
    # Leave the vendor installer, EULA and administrator prompts visible.
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    elif os.name == "nt":
        os.startfile(str(path))
    else:
        raise ValueError("Linux 请使用发行版安装流程。")


def docker_command(arguments, timeout=1200):
    executable = docker_executable()
    if not executable:
        raise ValueError("准备镜像需要 Docker 引擎；也可直接下载 Release 的完整离线包。")
    result = subprocess.run([executable, *arguments], env=docker_environment(executable),
                            capture_output=True, text=True, timeout=timeout, **process_options())
    if result.returncode:
        raise ValueError("Docker 镜像操作失败，请检查引擎、网络、权限及磁盘空间。")
    return result.stdout.strip()


def image_platform(target):
    return "linux/arm64" if target.endswith("arm64") else "linux/amd64"


def prepare_bundle(root, target, log, installers_only=False):
    root = Path(root)
    for component in catalog(target):
        ensure_installer(root, target, component, log)
    data = read_manifest(root, target)
    if not installers_only:
        log("正在缓存管理面板…", "normal")
        panel = root / "management.html"
        panel_url = "https://github.com/router-for-me/Cli-Proxy-API-Management-Center/releases/latest/download/management.html"
        download(panel_url, panel, log, allow_html=True)
        data["files"]["management"] = {"name": panel.name, "size": panel.stat().st_size,
                                         "sha256": sha256(panel), "source": panel_url}
        log(f"正在准备 {image_platform(target)} 服务镜像…", "normal")
        docker_command(["pull", "--platform", image_platform(target), IMAGE])
        details = json.loads(docker_command(["image", "inspect", IMAGE]))[0]
        if details["Os"] + "/" + details["Architecture"] != image_platform(target):
            raise ValueError("Docker 镜像架构不匹配。")
        partial = root / "cli-proxy-api-image.tar.part"
        root.mkdir(parents=True, exist_ok=True)
        docker_command(["image", "save", "--output", str(partial), IMAGE])
        path = partial.with_suffix("")
        partial.replace(path)
        data["files"]["image"] = {"name": path.name, "size": path.stat().st_size, "sha256": sha256(path)}
        data["image"] = {"tag": IMAGE, "id": details["Id"], "platform": image_platform(target),
                         "repo_digests": details.get("RepoDigests", [])}
    save_manifest(root, data)
    result = check_bundle(root, target)
    log("离线包准备完成。" if result["ready"] else "安装包已准备；服务镜像尚未准备。", "ok" if result["ready"] else "warn")
    return result


def check_bundle(root, target):
    components = [*catalog(target), "image", "management"]
    files = {component: verified_file(root, target, component) is not None for component in components}
    return {"target": target, "directory": str(root), "ready": all(files.values()), "files": files,
            "requires_preinstalled_linux_dependencies": target.startswith("Linux"),
            "upstream_network_required": True}


def ensure_image(root, target, log, offline=False, data_root=None):
    image = verified_file(root, target, "image")
    if not image:
        if offline:
            raise ValueError("离线包缺少服务镜像，已停止部署；不会尝试联网拉取。")
        if "AppTranslocation" in package_directory().parts and not os.environ.get("CODEXX_OFFLINE_DIR"):
            raise ValueError("macOS 临时运行路径无法定位离线包，请选择离线目录或使用 Server.command；未开始拉取镜像。")
        return False
    data = read_manifest(root, target).get("image", {})
    if not isinstance(data, dict):
        raise ValueError("离线镜像描述格式无效。")
    if data.get("tag") != IMAGE or data.get("platform") != image_platform(target) or not re.fullmatch(r"sha256:[0-9a-f]{64}", str(data.get("id", ""))):
        raise ValueError("离线镜像描述无效或架构不匹配。")
    panel = verified_file(root, target, "management")
    if offline and panel is None:
        raise ValueError("离线包缺少管理面板，已停止部署。")
    log("正在加载并核验本地服务镜像…", "normal")
    docker_command(["image", "load", "--input", str(image)])
    details = json.loads(docker_command(["image", "inspect", IMAGE]))[0]
    if details["Id"] != data["id"] or details["Os"] + "/" + details["Architecture"] != image_platform(target):
        raise ValueError("已加载镜像的标识或架构不匹配，已停止部署。")
    if panel is not None and data_root is not None:
        from .storage import install_management_asset
        install_management_asset(data_root, panel)
    log("本地镜像校验通过，部署将跳过联网拉取。", "ok")
    return True
