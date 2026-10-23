import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request

from .storage import (connection_profile, data_directory, harden_runtime,
                      initialize, read_config, write_private, probe_url)
from .runtime import docker_executable, docker_environment


def doctor(root, probe=False):
    executable = docker_executable()
    report = {"schema_version": 1, "data_directory": str(root), "platform": sys.platform,
              "configuration": "missing", "compose_exists": (root / "docker-compose.yml").is_file(),
              "docker_cli": bool(executable), "docker_engine": False,
              "compose_plugin": False, "api": "not_checked", "upstream_account": "unknown",
              "remaining_quota": None, "read_only": True}
    config = None
    try:
        config = read_config(root)
        report.update(configuration="valid", api_key_count=len(config["api-keys"]),
                      port=config["port"], config_schema=config["schema"])
    except FileNotFoundError:
        pass
    except (OSError, ValueError):
        report["configuration"] = "invalid"
    if report["docker_cli"]:
        for field, command in [("docker_engine", [executable, "info", "--format", "{{.ServerVersion}}"]),
                               ("compose_plugin", [executable, "compose", "version", "--short"])]:
            try:
                settings = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
                report[field] = subprocess.run(command, env=docker_environment(executable),
                                               capture_output=True, timeout=6, **settings).returncode == 0
            except (OSError, subprocess.TimeoutExpired):
                report[field] = False
    if probe and config:
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, request, stream, code, message, headers, url):
                return None
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect)
        try:
            report["probe_url"] = probe_url(root, config["port"])
            request = urllib.request.Request(report["probe_url"],
                                             headers={"Authorization": "Bearer " + config["api-keys"][0]})
            with opener.open(request, timeout=5) as response:
                payload = json.loads(response.read(1024 * 1024))
            if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
                raise ValueError("Invalid models response")
            report.update(api="authenticated", model_count=len(payload["data"]))
            # A successful request alone does not prove that authentication is enforced.
            try:
                with opener.open(report["probe_url"], timeout=5):
                    report["api"] = "authentication_not_enforced"
            except urllib.error.HTTPError as error:
                if error.code != 401:
                    report.update(api="unexpected_unauthenticated_status", http_status=error.code)
        except urllib.error.HTTPError as error:
            report.update(api="http_error", http_status=error.code)
        except (OSError, ValueError, TypeError, AttributeError):
            report["api"] = "unavailable_or_invalid_response"
    report["ready"] = all([report["configuration"] == "valid", report["compose_exists"],
                            report["docker_engine"], report["compose_plugin"]])
    if probe:
        report["ready"] = report["ready"] and report["api"] == "authenticated"
    report["next_steps"] = []
    if not report["docker_cli"]:
        report["next_steps"].append("安装 Docker Desktop（预编译 Server 仍需要 Docker），打开后完成系统授权。")
    elif not report["docker_engine"]:
        report["next_steps"].append("打开 Docker Desktop，检查管理员密码/协议/钥匙串提示，等待引擎就绪后重试。")
    if report["docker_cli"] and not report["compose_plugin"]:
        report["next_steps"].append("Docker Compose 不可用；检查或更新 Docker Desktop。")
    if report["configuration"] != "valid" or not report["compose_exists"]:
        report["next_steps"].append("新部署使用 Setup 初始化；已有配置先备份并修复，不要重置密钥。")
    if probe and report["api"] != "authenticated":
        report["next_steps"].append("检查容器状态、目录共享弹窗、端口映射和密钥；running 不等于 API 可访问。")
    if report.get("model_count") == 0:
        report["next_steps"].append("模型列表为空；在管理页检查上游账号授权及模型配置，实际生成尚未验证。")
    report["generation"] = "not_checked"
    return report


def main():
    parser = argparse.ArgumentParser(description="CodeXX Server: safe initialization, diagnostics and profile export")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--doctor", action="store_true", help="Read-only environment diagnosis; does not deploy")
    actions.add_argument("--init", action="store_true", help="Initialize missing data; never overwrite existing configuration")
    actions.add_argument("--harden-runtime", action="store_true",
                         help="Add missing long-running Compose resource/log defaults; preserve existing values")
    actions.add_argument("--export-profile", action="store_true", help="Export client credentials, never the management password")
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--report", type=Path, help="Sanitized JSON report destination")
    parser.add_argument("--probe", action="store_true", help="With --doctor, check local /v1/models; no generation")
    parser.add_argument("--port", type=int, default=8317)
    parser.add_argument("--bind", default="127.0.0.1", help="New deployments default to loopback; choose a tailnet IP explicitly")
    parser.add_argument("--proxy-port", type=int)
    parser.add_argument("--host", help="Client-visible server IP or hostname for export")
    parser.add_argument("--key-index", type=int, default=0)
    parser.add_argument("--output", type=Path, help="New .cliproxy file; refuses to overwrite")
    options = parser.parse_args()
    if options.data_dir:
        os.environ["CODEXX_SERVER_HOME"] = str(options.data_dir.expanduser().resolve())
    root = data_directory()
    try:
        if options.doctor:
            result = doctor(root, options.probe)
            code = 0 if result["ready"] else 2
        elif options.init:
            result = initialize(root, options.port, options.bind, options.proxy_port)
            code = 0
        elif options.harden_runtime:
            result = harden_runtime(root)
            code = 0
        elif options.export_profile:
            if not options.host or not options.output:
                parser.error("--export-profile requires --host and --output")
            if options.report and options.report.resolve() == options.output.resolve():
                parser.error("--report and --output must be different files")
            profile = connection_profile(root, options.host, options.key_index)
            write_private(options.output, json.dumps(profile, ensure_ascii=False, indent=2))
            result = {"exported": True, "path": str(options.output), "contains_management_password": False}
            code = 0
        else:
            from .gui import main as gui_main
            return gui_main()
    except (OSError, ValueError) as error:
        result = {"success": False, "error_type": type(error).__name__,
                  "message": "操作失败；请检查路径、配置格式或参数。已有配置未被自动覆盖。"}
        code = 1
    if options.report:
        if options.report.resolve() in {root.resolve() / name for name in ("config.yaml", "docker-compose.yml", ".credentials.json")}:
            parser.error("Report cannot overwrite configuration or credentials")
        write_private(options.report, json.dumps(result, ensure_ascii=False, indent=2), replace=True)
    elif sys.stdout:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return code
