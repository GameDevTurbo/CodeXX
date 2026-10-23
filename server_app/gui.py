#!/usr/bin/env python3
"""CLIProxyAPI cross-platform launcher (Windows / macOS / Linux)."""

import os
import sys
import json
import re
import platform
import subprocess
import threading
import queue
import secrets
import shutil
import socket
from pathlib import Path
from datetime import datetime

import customtkinter as ctk
from .storage import data_directory, initialize, read_config, connection_profile, write_private
from .runtime import docker_executable, docker_environment, docker_running, compose_operation
from .dependencies import (bundle_directory, current_target, ensure_installer,
                           ensure_image, open_installer, prepare_bundle)

SCRIPT_DIR = data_directory()
OS = platform.system()          # Windows / Darwin / Linux
CONTAINER = "cli-proxy-api"
try:
    PORT = read_config(SCRIPT_DIR)["port"] if (SCRIPT_DIR / "config.yaml").exists() else 8317
except (OSError, ValueError):
    PORT = 8317
MGMT_URL = f"http://localhost:{PORT}/management.html"
API_URL  = f"http://localhost:{PORT}/v1"
CFG_PATH   = SCRIPT_DIR / "config.yaml"
CMP_PATH   = SCRIPT_DIR / "docker-compose.yml"
CREDS_PATH = SCRIPT_DIR / ".credentials.json"

# ── Docker helpers ─────────────────────────────────────────────────────────────

ENC = {"encoding": "utf-8", "errors": "replace"}

# Suppress CMD window popup on Windows for all background subprocess calls
if OS == "Windows":
    import subprocess as _sp
    _NO_WIN = {"creationflags": _sp.CREATE_NO_WINDOW}
else:
    _NO_WIN = {}

# ── Docker helpers ─────────────────────────────────────────────────────────────

def service_status() -> str:
    try:
        executable = docker_executable()
        if not executable:
            return ""
        result = subprocess.run([executable, "inspect", "--format", "{{.State.Status}}", CONTAINER],
                                env=docker_environment(executable), capture_output=True, timeout=5, **ENC, **_NO_WIN)
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""

def run_compose(args: list, log_fn):
    return compose_operation(SCRIPT_DIR, args, log_fn)

def start_docker_desktop():
    if OS == "Windows":
        paths = [
            r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
            r"C:\Program Files (x86)\Docker\Docker\Docker Desktop.exe",
            str(Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) /
                "Programs/DockerDesktop/Docker Desktop.exe"),
        ]
        for p in paths:
            if Path(p).exists():
                subprocess.Popen([p])
                return True
        return False
    elif OS == "Darwin":
        subprocess.Popen(["open", "-a", "Docker"])
        return True
    else:
        for cmd in [["systemctl", "--user", "start", "docker-desktop"],
                    ["dockerd"]]:
            if shutil.which(cmd[0]):
                subprocess.Popen(cmd)
                return True
        return False

def ensure_dirs():
    SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    for d in ("auths", "logs", "plugins"):
        (SCRIPT_DIR / d).mkdir(exist_ok=True)

def rand_hex(n=16) -> str:
    return secrets.token_hex(n)

def rand_pwd(n=20) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789"
    return "".join(secrets.choice(alphabet) for _ in range(n))

def open_browser(url: str):
    import webbrowser
    webbrowser.open(url)

def get_tailscale_ip() -> str:
    try:
        r = subprocess.run([find_tailscale() or "tailscale", "ip", "-4"],
                           capture_output=True, text=True, timeout=5, **ENC, **_NO_WIN)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""

def find_tailscale() -> str:
    """Return path to tailscale CLI, or empty string if not found."""
    found = shutil.which("tailscale")
    if found:
        return found
    for p in [
        r"C:\Program Files\Tailscale\tailscale.exe",
        r"C:\Program Files (x86)\Tailscale\tailscale.exe",
        "/Applications/Tailscale.app/Contents/MacOS/Tailscale",
        "/usr/local/bin/tailscale",
        "/opt/homebrew/bin/tailscale",
    ]:
        if Path(p).exists():
            return p
    return ""

def find_tailscale_gui() -> str:
    """Return the platform's Tailscale graphical client, when available."""
    if OS == "Windows":
        for path in (
            r"C:\Program Files\Tailscale\tailscale-ipn.exe",
            r"C:\Program Files (x86)\Tailscale\tailscale-ipn.exe",
        ):
            if Path(path).exists():
                return path
    if OS == "Darwin":
        if Path("/Applications/Tailscale.app").exists():
            return "/Applications/Tailscale.app"
    return ""

def tailscale_status() -> dict:
    """Returns dict: installed, connected, ip, state."""
    exe = find_tailscale()
    if not exe:
        return {"installed": False, "connected": False, "ip": "", "state": "not_installed"}
    try:
        r = subprocess.run([exe, "status", "--json"],
                           capture_output=True, text=True, timeout=8, **ENC, **_NO_WIN)
        if r.returncode != 0:
            return {"installed": True, "connected": False, "ip": "", "state": "stopped"}
        data = json.loads(r.stdout)
        backend = data.get("BackendState", "")
        if backend == "Running":
            addrs = data.get("Self", {}).get("TailscaleIPs", [])
            ip = next((a for a in addrs if "." in a), "")
            return {"installed": True, "connected": True, "ip": ip, "state": "running"}
        elif backend in ("NeedsLogin", "NoState"):
            return {"installed": True, "connected": False, "ip": "", "state": "needs_login"}
        else:
            return {"installed": True, "connected": False, "ip": "", "state": backend.lower() or "stopped"}
    except Exception:
        ip = get_tailscale_ip()
        return {"installed": True, "connected": bool(ip), "ip": ip,
                "state": "running" if ip else "stopped"}

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return ""

def get_api_keys() -> list:
    if not CFG_PATH.exists():
        return []
    try:
        return read_config(SCRIPT_DIR).get("api-keys", [])
    except (OSError, ValueError):
        return []

# ── Main window ────────────────────────────────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C_BG      = "#0f0f14"
C_PANEL   = "#1a1a24"
C_CARD    = "#16161f"
C_INPUT   = "#24243a"
C_BLUE    = "#388bfd"
C_GREEN   = "#3fb950"
C_RED     = "#da3633"
C_ORANGE  = "#d28a28"
C_DIM     = "#646478"
C_TEXT    = "#dcdce6"
C_WIZARD  = "#121e12"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CLIProxyAPI Manager")
        self.geometry("580x780")
        self.resizable(False, False)
        self.configure(fg_color=C_BG)

        self._ui_tasks = queue.Queue()
        self.after(50, self._drain_ui)
        self._docker_poll = None
        self._refreshing  = False   # prevent concurrent refresh threads
        self._operation_running = False
        self._build_ui()
        self._refresh()
        self._auto = self._schedule(8000, self._tick)

    def _schedule(self, delay, callback):
        # Tk must only be called from its owning thread, including after().
        if threading.current_thread() is threading.main_thread():
            return self.after(delay, callback)
        self._ui_tasks.put((delay, callback))

    def _drain_ui(self):
        try:
            while True:
                delay, callback = self._ui_tasks.get_nowait()
                self.after(delay, callback)
        except queue.Empty:
            pass
        self.after(50, self._drain_ui)

    # ── UI build ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        pad = {"padx": 20}

        # Header
        ctk.CTkLabel(self, text="CLIProxyAPI Manager",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=C_BLUE).pack(anchor="w", pady=(16,0), **pad)
        ctk.CTkLabel(self, text="AI Subscription API Gateway",
                     font=ctk.CTkFont(size=11), text_color=C_DIM).pack(anchor="w", pady=(0,10), **pad)

        tools = ctk.CTkFrame(self, fg_color="transparent")
        tools.pack(fill="x", padx=20, pady=(0,8))
        self.offline = ctk.BooleanVar(value=os.environ.get("CODEXX_OFFLINE") == "1" or
                                     (bundle_directory() / "cli-proxy-api-image.tar").is_file())
        ctk.CTkCheckBox(tools, text="离线部署", variable=self.offline, width=120).pack(side="left")
        ctk.CTkButton(tools, text="准备完整离线包", width=150,
                      command=self._prepare_offline).pack(side="left", padx=(8,0))

        # Steps
        self.steps_frame = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=8)
        self.steps_frame.pack(fill="x", padx=20, pady=(0,8))
        self.s1 = self._step_row(self.steps_frame, "1", "Docker Desktop")
        self.s2 = self._step_row(self.steps_frame, "2", "Configuration")
        self.s3 = self._step_row(self.steps_frame, "3", "Service")
        self.s4 = self._step_row(self.steps_frame, "★", "Tailscale (Remote)")

        # Wizard panel
        self.wiz_frame = ctk.CTkFrame(self, fg_color=C_WIZARD, corner_radius=8)
        self.wiz_frame.pack(fill="x", padx=20, pady=(0,8))
        self.wiz_frame.pack_forget()

        ctk.CTkLabel(self.wiz_frame, text="Generate Configuration",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=C_GREEN).pack(anchor="w", padx=14, pady=(12,2))
        ctk.CTkLabel(self.wiz_frame,
                     text="API keys and management password will be auto-generated.",
                     font=ctk.CTkFont(size=10), text_color=C_DIM).pack(anchor="w", padx=14)

        row = ctk.CTkFrame(self.wiz_frame, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(10,0))
        ctk.CTkLabel(row, text="Local proxy port:", text_color=C_DIM,
                     font=ctk.CTkFont(size=10)).pack(side="left")
        self.proxy_entry = ctk.CTkEntry(row, width=70, placeholder_text="7890",
                                        fg_color=C_INPUT, border_color=C_DIM)
        self.proxy_entry.insert(0, "7890")
        self.proxy_entry.pack(side="left", padx=(8,8))
        ctk.CTkLabel(row, text="(0 = no proxy, e.g. overseas server)",
                     font=ctk.CTkFont(size=9), text_color=C_DIM).pack(side="left")

        ctk.CTkButton(self.wiz_frame, text="Generate and Deploy",
                      fg_color=C_GREEN, hover_color="#2d8a3e",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=self._generate_and_deploy).pack(anchor="w", padx=14, pady=(10,14))

        # Action buttons row 1
        r1 = ctk.CTkFrame(self, fg_color="transparent")
        r1.pack(fill="x", padx=20, pady=(0,6))
        ctk.CTkButton(r1, text="Management Panel", width=170,
                      fg_color="#2c5282", hover_color="#2a4a72",
                      command=lambda: open_browser(MGMT_URL)).pack(side="left", padx=(0,6))
        ctk.CTkButton(r1, text="Start Service", width=120,
                      fg_color="#236b3c", hover_color="#1a5230",
                      command=self._start_service).pack(side="left", padx=(0,6))
        ctk.CTkButton(r1, text="Stop", width=80,
                      fg_color="#7a2020", hover_color="#601818",
                      command=self._stop_service).pack(side="left", padx=(0,6))
        ctk.CTkButton(r1, text="Live Logs", width=110,
                      fg_color="#382850", hover_color="#2a1e3c",
                      command=self._live_logs).pack(side="left")

        # Action buttons row 2
        r2 = ctk.CTkFrame(self, fg_color="transparent")
        r2.pack(fill="x", padx=20, pady=(0,10))
        ctk.CTkButton(r2, text="Restart Service", width=150,
                      fg_color="#463c14", hover_color="#342c0e",
                      command=self._restart_service).pack(side="left", padx=(0,6))
        ctk.CTkButton(r2, text="Update Image", width=150,
                      fg_color="#2a2a50", hover_color="#1e1e3c",
                      command=self._update_image).pack(side="left")
        ctk.CTkButton(r2, text="检查连接", width=120,
                      command=self._check_connection).pack(side="left", padx=(6,0))

        # Connection info card (shown when service is running)
        self.conn_frame = ctk.CTkFrame(self, fg_color="#0f1f0f", corner_radius=8)
        # built lazily in _show_connect_info

        # API bar
        api_bar = ctk.CTkFrame(self, fg_color=C_PANEL, corner_radius=6)
        api_bar.pack(fill="x", padx=20, pady=(0,6))
        self.api_lbl = ctk.CTkLabel(api_bar, text=f"API: {API_URL}",
                                     font=ctk.CTkFont(size=10), text_color=C_DIM)
        self.api_lbl.pack(side="left", padx=12, pady=8)
        self.copy_btn = ctk.CTkButton(api_bar, text="Copy URL", width=90,
                                       fg_color="transparent", border_width=1,
                                       border_color=C_DIM, text_color=C_DIM,
                                       font=ctk.CTkFont(size=9),
                                       hover_color=C_PANEL,
                                       command=self._copy_url)
        self.copy_btn.pack(side="right", padx=8, pady=5)

        # Log
        log_hdr = ctk.CTkFrame(self, fg_color="transparent")
        log_hdr.pack(fill="x", padx=20)
        ctk.CTkLabel(log_hdr, text="Log", font=ctk.CTkFont(size=10),
                     text_color=C_DIM).pack(side="left")
        ctk.CTkButton(log_hdr, text="Clear", width=56,
                      fg_color="transparent", border_width=1, border_color=C_DIM,
                      text_color=C_DIM, font=ctk.CTkFont(size=9),
                      hover_color=C_PANEL,
                      command=self._clear_log).pack(side="right")

        self.log_box = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Courier", size=10),
                                       fg_color="#0a0a0e", text_color=C_TEXT,
                                       corner_radius=6, wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=20, pady=(4,16))
        self.log_box.configure(state="disabled")

    def _step_row(self, parent, num, name):
        f = ctk.CTkFrame(parent, fg_color="transparent", height=46)
        f.pack(fill="x", padx=0, pady=0)
        f.pack_propagate(False)

        dot = ctk.CTkLabel(f, text="●", font=ctk.CTkFont(size=18), text_color=C_DIM, width=30)
        dot.pack(side="left", padx=(14,0))

        info = ctk.CTkFrame(f, fg_color="transparent")
        info.pack(side="left", padx=(6,0))
        ctk.CTkLabel(info, text=f"Step {num}", font=ctk.CTkFont(size=8),
                     text_color=C_DIM).pack(anchor="w")
        ctk.CTkLabel(info, text=name, font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=C_TEXT).pack(anchor="w")

        stat = ctk.CTkLabel(f, text="Checking...", font=ctk.CTkFont(size=10),
                             text_color=C_DIM, width=160, anchor="w")
        stat.pack(side="left", padx=(10,0))

        btn = ctk.CTkButton(f, text="", width=120, height=28,
                             font=ctk.CTkFont(size=9, weight="bold"))
        btn.pack(side="right", padx=14)
        btn.pack_forget()

        sep = ctk.CTkFrame(parent, fg_color=C_PANEL, height=1)
        sep.pack(fill="x", padx=0)

        return {"dot": dot, "stat": stat, "btn": btn}

    # ── Logging ────────────────────────────────────────────────────────────────

    def log(self, msg: str, kind: str = "normal"):
        colors = {"normal": C_TEXT, "dim": C_DIM, "ok": C_GREEN,
                  "warn": C_ORANGE, "error": C_RED}
        color = colors.get(kind, C_TEXT)
        ts  = datetime.now().strftime("%H:%M:%S")
        text = f"[{ts}] {msg}\n"
        self.log_box.configure(state="normal")
        try:                                       # apply per-line color via underlying tk Text
            tb = self.log_box._textbox
            tag = f"c_{kind}"
            tb.tag_configure(tag, foreground=color)
            tb.insert("end", text, tag)
        except Exception:
            self.log_box.insert("end", text)
        self.log_box.configure(state="disabled")
        self.log_box.see("end")

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    # ── Status refresh (non-blocking) ─────────────────────────────────────────

    def _refresh(self):
        """Start a background thread to collect status, then update UI."""
        if self._refreshing:
            return
        self._refreshing = True
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self):
        """Collect all status info in background (no UI calls here)."""
        try:
            docker_ok = docker_running()
            cfg_ok    = CFG_PATH.exists()
            svc       = service_status() if docker_ok else ""
            ts        = tailscale_status()
            self._schedule(0, lambda: self._apply_status(docker_ok, cfg_ok, svc, ts))
        finally:
            self._refreshing = False

    def _apply_status(self, docker_ok: bool, cfg_ok: bool, svc: str, ts: dict):
        """Apply collected status to UI — runs on main thread."""
        # Step 1: Docker
        if docker_ok:
            self._set_step(self.s1, C_GREEN, "Running", None, None)
        else:
            self._set_step(self.s1, C_ORANGE, "Not running",
                           "Start Docker" if docker_executable() else "安装 Docker", C_ORANGE, self._start_docker)

        # Step 2: Config
        if cfg_ok:
            self._set_step(self.s2, C_GREEN, "Ready", None, None)
            self.wiz_frame.pack_forget()
        else:
            self._set_step(self.s2, C_ORANGE, "Not configured",
                           "Setup", C_BLUE, self._show_wizard)

        # Step 3: Service
        if svc == "running":
            self._set_step(self.s3, C_GREEN, "Running", None, None)
            self._show_connect_info()
        elif svc in ("exited", "created"):
            self._set_step(self.s3, C_RED, "Stopped",
                           "Start", C_GREEN, self._start_service)
            self.conn_frame.pack_forget()
        else:
            self._set_step(self.s3, C_DIM, "Not deployed",
                           "Deploy", C_BLUE, self._deploy)
            self.conn_frame.pack_forget()

        # Step 4: Tailscale
        if ts["state"] == "not_installed":
            self._set_step(self.s4, C_DIM, "Not installed",
                           "安装 Tailscale", C_DIM, self._tailscale_download)
        elif ts["state"] == "needs_login":
            self._set_step(self.s4, C_ORANGE, "Not logged in",
                           "Login", C_ORANGE, self._tailscale_login)
        elif ts["connected"]:
            self._set_step(self.s4, C_GREEN,
                           f"Connected · {ts['ip']}", None, None)
        else:
            self._set_step(self.s4, C_ORANGE, f"Stopped ({ts['state']})",
                           "Start", C_ORANGE, self._tailscale_start)

    def _show_connect_info(self):
        """Fetch network info in background, then build the card."""
        threading.Thread(target=self._build_connect_info, daemon=True).start()

    def _build_connect_info(self):
        """Runs in background thread — collects data, then updates UI on main thread."""
        ts_ip    = get_tailscale_ip()
        local_ip = get_local_ip()
        keys     = get_api_keys()
        key      = keys[0] if keys else "—"
        mgmt_pwd = "—"
        if CREDS_PATH.exists():
            try:
                creds = json.loads(CREDS_PATH.read_text(encoding="utf-8"))
                mgmt_pwd = creds.get("mgmt_password", "—")
            except Exception:
                pass
        server_ip     = ts_ip or local_ip or "localhost"
        mgmt_url_real = f"http://{server_ip}:{PORT}/management.html"
        rows = []
        if ts_ip:
            rows.append(("Tailscale API", f"http://{ts_ip}:{PORT}/v1"))
        if local_ip:
            rows.append(("LAN API",       f"http://{local_ip}:{PORT}/v1"))
        rows.append(("API Key",      key))
        rows.append(("Mgmt Panel",   mgmt_url_real))
        rows.append(("Mgmt Password", mgmt_pwd))
        self._schedule(0, lambda: self._render_connect_info(rows, server_ip, key))

    def _render_connect_info(self, rows, server_ip, key):
        """Runs on main thread — builds the connection info card."""
        # Clear and rebuild widgets
        for w in self.conn_frame.winfo_children():
            w.destroy()

        ctk.CTkLabel(self.conn_frame, text="Connection Info",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C_GREEN).grid(row=0, column=0, columnspan=3,
                                               sticky="w", padx=14, pady=(10,4))

        for i, (label, value) in enumerate(rows, start=1):
            ctk.CTkLabel(self.conn_frame, text=label, text_color=C_DIM,
                         font=ctk.CTkFont(size=9), width=100, anchor="w"
                         ).grid(row=i, column=0, padx=(14,4), pady=2, sticky="w")
            display = "•••••••• (Copy to use)" if label in ("API Key", "Mgmt Password") else value[:50] + ("…" if len(value) > 50 else "")
            ctk.CTkLabel(self.conn_frame, text=display,
                         text_color=C_TEXT, font=ctk.CTkFont(family="Courier", size=9),
                         anchor="w"
                         ).grid(row=i, column=1, padx=4, pady=2, sticky="w")
            v = value
            ctk.CTkButton(self.conn_frame, text="Copy", width=56, height=22,
                          font=ctk.CTkFont(size=8),
                          fg_color=C_PANEL, hover_color=C_CARD, text_color=C_DIM,
                          border_width=1, border_color=C_DIM,
                          command=lambda x=v: self._copy(x)
                          ).grid(row=i, column=2, padx=(4,14), pady=2)

        btn_row = len(rows) + 1
        ctk.CTkButton(self.conn_frame, text="Export .cliproxy file",
                      font=ctk.CTkFont(size=9), width=160, height=26,
                      fg_color=C_PANEL, hover_color=C_CARD, text_color=C_DIM,
                      border_width=1, border_color=C_DIM,
                      command=lambda: self._export(server_ip, key)
                      ).grid(row=btn_row, column=0, columnspan=2,
                             padx=14, pady=(8,12), sticky="w")

        ctk.CTkButton(self.conn_frame, text="Download Client →",
                      font=ctk.CTkFont(size=9), width=150, height=26,
                      fg_color=C_BLUE, hover_color="#2a6fd4",
                      command=lambda: open_browser("https://github.com/GameDevTurbo/CodeXX-Client/releases")
                      ).grid(row=btn_row, column=2, padx=14, pady=(8,12))

        self.conn_frame.pack(fill="x", padx=20, pady=(0,8),
                             before=self.log_box)

    def _copy(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)

    def _export(self, server_ip: str, api_key: str):
        import tkinter.filedialog as filedialog
        try:
            data = connection_profile(SCRIPT_DIR, server_ip or "localhost")
            path = filedialog.asksaveasfilename(parent=self, defaultextension=".cliproxy",
                                               filetypes=[("CLIProxy config", "*.cliproxy")],
                                               initialfile="cliproxy-connection", title="Export connection file")
            if path:
                write_private(path, json.dumps(data, ensure_ascii=False, indent=2), replace=True)
                self.log("Connection profile exported; management password excluded.", "ok")
        except (OSError, ValueError):
            self.log("Export failed. Check configuration and output path; no credentials logged.", "error")

    def _set_step(self, s, dot_color, stat_text, btn_text, btn_color, btn_cmd=None):
        s["dot"].configure(text_color=dot_color)
        s["stat"].configure(text=stat_text,
                             text_color=dot_color if dot_color != C_DIM else C_DIM)
        if btn_text:
            s["btn"].configure(text=btn_text, fg_color=btn_color,
                                hover_color=btn_color, command=btn_cmd)
            s["btn"].pack(side="right", padx=14)
        else:
            s["btn"].pack_forget()

    def _tick(self):
        self._refresh()
        self._auto = self._schedule(8000, self._tick)

    # ── Step actions ───────────────────────────────────────────────────────────

    def _tailscale_download(self):
        self._install_dependency("tailscale")

    def _install_dependency(self, component):
        if OS == "Linux":
            if self.offline.get():
                self.log("Linux 离线部署需预装 Docker Engine、Compose；Tailscale 按发行版准备。", "warn")
                return
            open_browser("https://docs.docker.com/engine/install/" if component == "docker" else "https://tailscale.com/download/linux")
            return
        offline = self.offline.get()
        def install():
            path = ensure_installer(bundle_directory(), current_target(), component, self._safe_log, offline)
            open_installer(path)
            self._safe_log("已打开安装程序；请完成安装、协议及系统授权，安装后打开应用。", "warn")
        self._run_bg(install, done=self._refresh)

    def _prepare_offline(self):
        if self.offline.get():
            self.log("准备离线包需要联网；请在联网机器取消离线部署后再准备。", "warn")
            return
        def prepare():
            target = current_target()
            root = bundle_directory(target)
            result = prepare_bundle(root, target, self._safe_log, installers_only=not docker_running())
            self._safe_log(f"离线文件位置：{root}", "normal")
            if not result["ready"]:
                self._safe_log("安装程序已缓存；Docker 就绪后再次准备可补齐镜像，或下载 Release 的完整离线包。", "warn")
        self._run_bg(prepare)

    def _prepare_service_image(self, offline):
        if ensure_image(bundle_directory(), current_target(), self._safe_log, offline, SCRIPT_DIR):
            return 0
        return run_compose(["pull"], self._safe_log)

    def _tailscale_login(self):
        exe = find_tailscale()
        if not exe:
            self.log("Tailscale not found. Please install it.", "error")
            open_browser("https://tailscale.com/download")
            return

        # Open the graphical client when it is installed.
        gui = find_tailscale_gui()
        if gui:
            self.log("Opening Tailscale app...", "warn")
            if OS == "Darwin":
                subprocess.Popen(["open", gui])
            else:
                subprocess.Popen([gui])
            self._schedule(4000, self._refresh)
            return

        # Windows / Linux: run 'tailscale up' in a visible terminal
        self.log("Running 'tailscale up' — check the terminal/browser for login URL...", "warn")
        if OS == "Windows":
            subprocess.Popen(
                ["powershell", "-NoExit", "-Command",
                 f"Write-Host 'Connecting Tailscale...' -ForegroundColor Cyan; "
                 f"& '{exe}' up; "
                 f"Write-Host 'Done. You can close this window.' -ForegroundColor Green"],
                creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            for term in ("gnome-terminal", "xterm", "konsole"):
                if shutil.which(term):
                    subprocess.Popen([term, "--", "bash", "-c",
                                      f"{exe} up; read -p 'Press Enter to close'"])
                    break
            else:
                subprocess.Popen([exe, "up"])
        self._schedule(6000, self._refresh)

    def _do_tailscale_login(self, exe):
        import re
        try:
            proc = subprocess.Popen(
                [exe, "login"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, **ENC)
            url = ""
            for line in proc.stdout:
                line = line.strip()
                if line:
                    self._schedule(0, lambda l=line: self.log(l, "dim"))
                match = re.search(r'https://\S+', line)
                if match and not url:
                    url = match.group(0)
                    self._schedule(0, lambda u=url: (
                        self.log(f"Opening: {u}", "ok"),
                        open_browser(u)
                    ))
            proc.wait()
        except Exception as e:
            msg = str(e)
            self._schedule(0, lambda m=msg: self.log(f"Error: {m}", "error"))
        self._schedule(5000, self._refresh)

    def _tailscale_start(self):
        ts = tailscale_status()
        if ts["state"] in ("needs_login", "stopped"):
            self._tailscale_login()
            return
        exe = find_tailscale()
        if exe:
            self.log("Reconnecting Tailscale...", "warn")
            self._run_bg(lambda: subprocess.run([exe, "up"],
                                                capture_output=True, **ENC))
            self._schedule(4000, self._refresh)

    def _start_docker(self):
        if not docker_executable():
            self._install_dependency("docker")
            return
        self.log("Starting Docker Desktop...", "warn")
        if not start_docker_desktop():
            self.log("Could not find Docker Desktop executable.", "error")
            return
        self.log("等待 Docker 就绪；请在本机完成管理员密码、协议或钥匙串提示（不会自动代填）。", "warn")
        self._poll_docker(0)

    def _poll_docker(self, attempt: int):
        if docker_running():
            self.log("Docker is ready!", "ok")
            self._refresh()
            if not CFG_PATH.exists():
                self._show_wizard()
        elif attempt < 30:
            self.log(f"Still waiting... ({attempt*3}s)", "dim")
            self._schedule(3000, lambda: self._poll_docker(attempt + 1))
        else:
            self.log("Docker 尚未就绪。请打开 Docker Desktop 完成授权，然后再次点击 Start Docker。", "error")

    def _check_connection(self):
        def check():
            from .cli import doctor
            result = doctor(SCRIPT_DIR, probe=True)
            self._safe_log(f"Docker: {result['docker_engine']} | API: {result['api']}", "normal")
            if result["api"] == "authenticated":
                self._safe_log(f"API 鉴权通过；模型数 {result['model_count']}。实际生成未验证。", "ok")
            for step in result["next_steps"]:
                self._safe_log(step, "warn")
        self._run_bg(check)

    def _show_wizard(self):
        self.wiz_frame.pack(fill="x", padx=20, pady=(0,8),
                             before=self.log_box)

    def _deploy(self):
        if not docker_running():
            self.log("Docker not running.", "error"); return
        if not CFG_PATH.exists():
            self.log("No config.yaml found.", "error")
            self._show_wizard(); return
        ensure_dirs()
        offline = self.offline.get()
        def deploy():
            code = self._prepare_service_image(offline)
            return code if code else run_compose(["up", "-d", "--pull", "never"], self._safe_log)
        self._run_bg(deploy,
                     done=lambda: (self._refresh(), open_browser(MGMT_URL)))

    def _start_service(self):
        if not docker_running():
            self.log("Docker not running.", "error"); return
        ensure_dirs()
        self._deploy()

    def _stop_service(self):
        if not docker_running():
            self.log("Docker not running.", "error"); return
        self._run_bg(lambda: run_compose(["down"], self._safe_log), done=self._refresh)

    def _restart_service(self):
        if not docker_running():
            self.log("Docker not running.", "error"); return
        self._run_bg(lambda: run_compose(["restart"], self._safe_log), done=self._refresh)

    def _update_image(self):
        if self.offline.get():
            self.log("离线部署不会更新镜像；请在联网机器重新准备离线包。", "warn")
            return
        if not docker_running():
            self.log("Docker not running.", "error"); return
        def do():
            rc = run_compose(["pull"], self._safe_log)
            if rc != 0:
                return rc
            return run_compose(["up", "-d", "--pull", "never"], self._safe_log)
        self._run_bg(do, done=lambda: (self._refresh(), self.log("Update complete!", "ok")))

    def _live_logs(self):
        if service_status() != "running":
            self.log("Service not running.", "error"); return
        self._run_bg(lambda: run_compose(["logs", "--tail", "100"], self._safe_log))

    def _copy_url(self):
        self.clipboard_clear()
        self.clipboard_append(API_URL)
        self.copy_btn.configure(text="Copied!")
        self._schedule(1500, lambda: self.copy_btn.configure(text="Copy URL"))

    # ── Generate config and deploy ─────────────────────────────────────────────

    def _generate_and_deploy(self):
        if not docker_running():
            self.log("Start Docker Desktop first.", "error")
            return
        try:
            proxy = self.proxy_entry.get().strip()
            result = initialize(SCRIPT_DIR, PORT, get_tailscale_ip() or "127.0.0.1",
                                int(proxy) if proxy and proxy != "0" else None)
        except (OSError, ValueError):
            self.log("Initialization failed; check proxy port and existing configuration. Nothing overwritten.", "error")
            return
        self.log("Configuration created; credentials stay in the data directory." if result["created"] else
                 "Existing configuration preserved; keys and proxy settings were not regenerated.", "ok")
        self.wiz_frame.pack_forget()
        self._refresh()
        offline = self.offline.get()
        def deploy():
            result = self._prepare_service_image(offline)
            if result != 0:
                return result
            return run_compose(["up", "-d", "--pull", "never"], self._safe_log)

        self._run_bg(deploy, done=lambda: (self._refresh(), self.log("Container started; authenticate upstream in the management panel.", "ok"),
                                          open_browser(MGMT_URL)))

    # ── Background task helper ─────────────────────────────────────────────────

    def _safe_log(self, msg: str, kind: str = "normal"):
        """Thread-safe log: schedule on main thread via after()."""
        self._schedule(0, lambda m=msg, k=kind: self.log(m, k))

    def _run_bg(self, fn, done=None):
        """Run fn in background thread; schedule done() on main thread only on success."""
        if self._operation_running:
            self.log("已有操作正在进行，请等待结果，勿重复部署。", "warn")
            return
        self._operation_running = True
        def worker():
            try:
                result = fn()
                if type(result) is int and result != 0:
                    raise RuntimeError(f"Command failed (exit {result})")
                if done:
                    self._schedule(0, done)
            except Exception as e:
                msg = str(e)
                self._schedule(0, lambda m=msg: self.log(f"Error: {m}", "error"))
            finally:
                self._schedule(0, lambda: setattr(self, "_operation_running", False))
        threading.Thread(target=worker, daemon=True).start()

    def on_close(self):
        if self._auto:
            self.after_cancel(self._auto)
        self.destroy()


def main():
    try:
        app = App()
        app.protocol("WM_DELETE_WINDOW", app.on_close)
        app.mainloop()
        return 0
    except Exception:
        import tkinter.messagebox as messagebox
        messagebox.showerror("CodeXX Server", "Startup failed. Run --doctor --report to inspect the environment.")
        return 1
