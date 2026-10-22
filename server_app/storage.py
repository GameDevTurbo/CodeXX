import ipaddress
import json
import os
from pathlib import Path
import secrets
import sys

import yaml


def data_directory():
    configured = os.environ.get("CODEXX_SERVER_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    root = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
    if getattr(sys, "frozen", False) and sys.platform == "darwin" and root.name == "MacOS" and root.parent.name == "Contents" and root.parent.parent.suffix == ".app":
        root = root.parent.parent.parent
    if (root / "config.yaml").is_file():
        return root
    if not getattr(sys, "frozen", False):
        return root / "data"
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "CodeXX" / "Server"


def write_private(path, content, replace=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | (os.O_TRUNC if replace else os.O_EXCL)
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
        stream.write(content)


def read_config(root):
    path = Path(root) / "config.yaml"
    if path.stat().st_size > 1024 * 1024:
        raise ValueError("配置文件过大。")
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        raise ValueError("config.yaml 不是有效 YAML；未修改原文件。") from None
    if not isinstance(document, dict):
        raise ValueError("配置必须是 YAML 对象。")
    access = document.get("access", {})
    server = document.get("server", {})
    if not isinstance(access, dict) or not isinstance(server, dict):
        raise ValueError("配置中的 access/server 类型无效。")
    keys = access.get("api-keys", document.get("api-keys", []))
    if not isinstance(keys, list) or not keys or not all(isinstance(key, str) and key.strip() and "\n" not in key and "\r" not in key for key in keys):
        raise ValueError("配置缺少有效 API Key。")
    port = server.get("port", document.get("port", 8317))
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("服务端口必须为 1–65535。")
    return {"api-keys": keys, "port": port, "schema": "v8" if "server" in document else "legacy"}


def initialize(root, port=8317, bind="127.0.0.1", proxy_port=None):
    root = Path(root)
    if not 1 <= port <= 65535 or (proxy_port is not None and not 1 <= proxy_port <= 65535):
        raise ValueError("端口必须为 1–65535。")
    ipaddress.ip_address(bind)
    targets = [root / name for name in ("config.yaml", "docker-compose.yml", ".credentials.json")]
    if targets[0].exists() and targets[1].exists():
        read_config(root)
        return {"created": False, "data_directory": str(root), "preserved_existing": True}
    if any(path.exists() for path in targets):
        raise ValueError("发现不完整的既有配置；请先备份并修复，初始化不会覆盖它。")
    root.mkdir(parents=True, exist_ok=True)
    keys = ["sk-" + secrets.token_hex(24) for index in range(2)]
    password = secrets.token_urlsafe(24)
    configuration = {"config-version": 8, "server": {"host": "0.0.0.0", "port": port},
                     "access": {"api-keys": keys}, "oauth": {"auth-dir": "/root/.cli-proxy-api"},
                     "routing": {"strategy": "round-robin"},
                     "management": {"allow-remote": True, "secret-key": password, "disable-control-panel": False}}
    address = "[" + bind + "]" if ":" in bind else bind
    service = {"image": "eceasy/cli-proxy-api:latest", "pull_policy": "missing", "container_name": "cli-proxy-api",
               "ports": [f"{address}:{port}:{port}", "127.0.0.1:8085:8085"],
               "volumes": ["./config.yaml:/CLIProxyAPI/config.yaml", "./auths:/root/.cli-proxy-api",
                           "./logs:/CLIProxyAPI/logs", "./plugins:/CLIProxyAPI/plugins"],
               "restart": "unless-stopped"}
    if proxy_port:
        service["environment"] = {"HTTP_PROXY": f"http://host.docker.internal:{proxy_port}",
                                  "HTTPS_PROXY": f"http://host.docker.internal:{proxy_port}",
                                  "NO_PROXY": "localhost,127.0.0.1,::1"}
        service["extra_hosts"] = ["host.docker.internal:host-gateway"]
    documents = [yaml.safe_dump(configuration, allow_unicode=True, sort_keys=False),
                 yaml.safe_dump({"services": {"cli-proxy-api": service}}, sort_keys=False),
                 json.dumps({"api_keys": keys, "mgmt_password": password}, indent=2)]
    created = []
    try:
        for path, content in zip(targets, documents):
            write_private(path, content)
            created.append(path)
        for name in ("auths", "logs", "plugins"):
            (root / name).mkdir(mode=0o700, exist_ok=True)
    except Exception:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return {"created": True, "data_directory": str(root), "bind": bind, "port": port,
            "credentials": "Stored locally; never included in this report."}


def connection_profile(root, host, key_index=0):
    from urllib.parse import urlsplit
    if not isinstance(host, str) or not host or any(character in host for character in "/?#@\r\n \t"):
        raise ValueError("host 必须是 IP 或主机名，不得包含协议、路径或凭据。")
    try:
        address = ipaddress.ip_address(host.strip("[]"))
        authority = f"[{address}]" if address.version == 6 else str(address)
    except ValueError:
        authority = host
        if ":" in host or urlsplit("http://" + host).hostname != host.lower():
            raise ValueError("主机名无效。")
    config = read_config(root)
    if not 0 <= key_index < len(config["api-keys"]):
        raise ValueError("API Key 索引超出范围。")
    return {"name": f"CodeXX · {host}", "api_url": f"http://{authority}:{config['port']}/v1",
            "api_key": config["api-keys"][key_index]}


def probe_url(root, port):
    path = Path(root) / "docker-compose.yml"
    host = "127.0.0.1"
    published = port
    if path.exists():
        if path.stat().st_size > 1024 * 1024:
            raise ValueError("Compose 文件过大。")
        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            ports = document["services"]["cli-proxy-api"].get("ports", [])
            for binding in ports:
                if isinstance(binding, dict):
                    target = int(binding["target"])
                    candidate_port = int(binding.get("published", target))
                    candidate_host = binding.get("host_ip", "127.0.0.1")
                elif isinstance(binding, str):
                    parts = binding.removesuffix("/tcp").rsplit(":", 2)
                    target = int(parts[-1])
                    candidate_port = int(parts[-2]) if len(parts) > 1 else target
                    candidate_host = parts[0].strip("[]") if len(parts) > 2 else "127.0.0.1"
                else:
                    continue
                if target == port:
                    host, published = candidate_host, candidate_port
                    break
            address = ipaddress.ip_address(host)
            if address.is_unspecified:
                host = "::1" if address.version == 6 else "127.0.0.1"
            if not 1 <= published <= 65535:
                raise ValueError("Invalid published port")
        except (yaml.YAMLError, KeyError, AttributeError, TypeError, ValueError):
            raise ValueError("无法安全识别 Compose API 绑定。") from None
    authority = f"[{host}]" if ":" in host else host
    return f"http://{authority}:{published}/v1/models"
