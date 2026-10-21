#!/usr/bin/env python3
"""CLIProxyAPI cross-platform launcher (Windows / macOS / Linux)."""

import os
import sys
import json
import re
import platform
import subprocess
import threading
import secrets
import shutil
import socket
from pathlib import Path
from datetime import datetime

try:
    import customtkinter as ctk
except ImportError:
    print("Installing customtkinter...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter", "-q"])
    import customtkinter as ctk

SCRIPT_DIR = Path(__file__).parent.resolve()
OS = platform.system()          # Windows / Darwin / Linux
CONTAINER = "cli-proxy-api"
PORT = 8317
MGMT_URL = f"http://localhost:{PORT}/management.html"
API_URL  = f"http://localhost:{PORT}/v1"
CFG_PATH   = SCRIPT_DIR / "config.yaml"
CMP_PATH   = SCRIPT_DIR / "docker-compose.yml"
CREDS_PATH = SCRIPT_DIR / ".credentials.json"

# ── Docker helpers ─────────────────────────────────────────────────────────────

ENC = {"encoding": "utf-8", "errors": "replace"}

# ── Docker helpers ─────────────────────────────────────────────────────────────

def docker_running() -> bool:
    try:
        r = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False

def service_status() -> str:
    r = subprocess.run(
        ["docker", "inspect", "--format", "{{.State.Status}}", CONTAINER],
        capture_output=True, text=True, timeout=5, **ENC)
    return r.stdout.strip() if r.returncode == 0 else ""

def run_compose(args: list, log_fn):
    log_fn(f"Running: docker compose {' '.join(args)}", "dim")
    proc = subprocess.Popen(
        ["docker", "compose"] + args,
        cwd=str(SCRIPT_DIR),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, **ENC)
    for line in proc.stdout:
        line = line.rstrip()
        if line:
            col = "error" if any(w in line.lower() for w in ("error","fail","fatal")) \
                else "warn" if "warn" in line.lower() else "normal"
            log_fn(line, col)
    proc.wait()
    return proc.returncode

def start_docker_desktop():
    if OS == "Windows":
        paths = [
            r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
            r"C:\Program Files (x86)\Docker\Docker\Docker Desktop.exe",
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
        r = subprocess.run(["tailscale", "ip", "-4"],
                           capture_output=True, text=True, timeout=5, **ENC)
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
    """On Windows/macOS, return GUI app path. Returns empty on Windows
    since Tailscale.exe == tailscale.exe (same binary, case-insensitive)."""
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
                           capture_output=True, text=True, timeout=8, **ENC)
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
    text = CFG_PATH.read_text(encoding="utf-8")
    return re.findall(r'^\s*-\s*"?(sk-[a-f0-9]+)"?', text, re.MULTILINE)

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

        self._docker_poll = None
        self._refreshing  = False   # prevent concurrent refresh threads
        self._build_ui()
        self._refresh()
        self._auto = self.after(8000, self._tick)

    # ── UI build ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        pad = {"padx": 20}

        # Header
        ctk.CTkLabel(self, text="CLIProxyAPI Manager",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=C_BLUE).pack(anchor="w", pady=(16,0), **pad)
        ctk.CTkLabel(self, text="AI Subscription API Gateway",
                     font=ctk.CTkFont(size=11), text_color=C_DIM).pack(anchor="w", pady=(0,10), **pad)

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
            self.after(0, lambda: self._apply_status(docker_ok, cfg_ok, svc, ts))
        finally:
            self._refreshing = False

    def _apply_status(self, docker_ok: bool, cfg_ok: bool, svc: str, ts: dict):
        """Apply collected status to UI — runs on main thread."""
        # Step 1: Docker
        if docker_ok:
            self._set_step(self.s1, C_GREEN, "Running", None, None)
        else:
            self._set_step(self.s1, C_ORANGE, "Not running",
                           "Start Docker", C_ORANGE, self._start_docker)

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
                           "Download", C_DIM, self._tailscale_download)
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
        self.after(0, lambda: self._render_connect_info(rows, server_ip, key))

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
            display = value[:50] + ("…" if len(value) > 50 else "")
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

        client_py = SCRIPT_DIR / "client.py"
        if client_py.exists():
            ctk.CTkButton(self.conn_frame, text="Open Client Tool →",
                          font=ctk.CTkFont(size=9), width=150, height=26,
                          fg_color=C_BLUE, hover_color="#2a6fd4",
                          command=lambda: subprocess.Popen(
                              [sys.executable, str(client_py)],
                              cwd=str(SCRIPT_DIR))
                          ).grid(row=btn_row, column=2, padx=14, pady=(8,12))

        self.conn_frame.pack(fill="x", padx=20, pady=(0,8),
                             before=self.log_box)

    def _copy(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)

    def _export(self, server_ip: str, api_key: str):
        data = {
            "api_url":  f"http://{server_ip}:{PORT}/v1" if server_ip else API_URL,
            "api_key":  api_key,
            "mgmt_url": f"http://{server_ip}:{PORT}/management.html" if server_ip else MGMT_URL,
            "server":   server_ip or "localhost",
            "port":     PORT,
        }
        import tkinter.filedialog as fd
        path = fd.asksaveasfilename(
            parent=self,
            defaultextension=".cliproxy",
            filetypes=[("CLIProxy config", "*.cliproxy"), ("JSON", "*.json")],
            initialfile="cliproxy-connection",
            title="Export connection file")
        if path:
            Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
            self.log(f"Saved: {path}", "ok")

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
        self._auto = self.after(8000, self._tick)

    # ── Step actions ───────────────────────────────────────────────────────────

    def _tailscale_download(self):
        open_browser("https://tailscale.com/download")
        self.log("Opening tailscale.com/download in browser...", "warn")

    def _tailscale_login(self):
        exe = find_tailscale()
        if not exe:
            self.log("Tailscale not found. Please install it.", "error")
            open_browser("https://tailscale.com/download")
            return

        # macOS: open the .app bundle
        gui = find_tailscale_gui()
        if gui:
            self.log("Opening Tailscale app...", "warn")
            subprocess.Popen(["open", gui])
            self.after(4000, self._refresh)
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
        self.after(6000, self._refresh)

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
                    self.after(0, lambda l=line: self.log(l, "dim"))
                match = re.search(r'https://\S+', line)
                if match and not url:
                    url = match.group(0)
                    self.after(0, lambda u=url: (
                        self.log(f"Opening: {u}", "ok"),
                        open_browser(u)
                    ))
            proc.wait()
        except Exception as e:
            msg = str(e)
            self.after(0, lambda m=msg: self.log(f"Error: {m}", "error"))
        self.after(5000, self._refresh)

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
            self.after(4000, self._refresh)

    def _start_docker(self):
        self.log("Starting Docker Desktop...", "warn")
        if not start_docker_desktop():
            self.log("Could not find Docker Desktop executable.", "error")
            return
        self.log("Waiting for Docker to be ready (up to 90s)...", "warn")
        self._poll_docker(0)

    def _poll_docker(self, attempt: int):
        if docker_running():
            self.log("Docker is ready!", "ok")
            self._refresh()
            if not CFG_PATH.exists():
                self._show_wizard()
        elif attempt < 30:
            self.log(f"Still waiting... ({attempt*3}s)", "dim")
            self.after(3000, lambda: self._poll_docker(attempt + 1))
        else:
            self.log("Docker did not start in time. Try opening it manually.", "error")

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
        self._run_bg(lambda: run_compose(["up", "-d", "--pull", "never"], self._safe_log),
                     done=lambda: (self._refresh(), open_browser(MGMT_URL)))

    def _start_service(self):
        if not docker_running():
            self.log("Docker not running.", "error"); return
        ensure_dirs()
        self._run_bg(lambda: run_compose(["up", "-d", "--pull", "never"], self._safe_log),
                     done=self._refresh)

    def _stop_service(self):
        if not docker_running():
            self.log("Docker not running.", "error"); return
        self._run_bg(lambda: run_compose(["down"], self._safe_log), done=self._refresh)

    def _restart_service(self):
        if not docker_running():
            self.log("Docker not running.", "error"); return
        self._run_bg(lambda: run_compose(["restart"], self._safe_log), done=self._refresh)

    def _update_image(self):
        if not docker_running():
            self.log("Docker not running.", "error"); return
        def do():
            rc = run_compose(["pull"], self._safe_log)
            if rc != 0:
                self._safe_log("Pull failed — starting with existing image.", "warn")
            run_compose(["up", "-d", "--pull", "never"], self._safe_log)
        self._run_bg(do, done=lambda: (self._refresh(), self.log("Update complete!", "ok")))

    def _live_logs(self):
        if service_status() != "running":
            self.log("Service not running.", "error"); return
        if OS == "Windows":
            subprocess.Popen(["powershell", "-NoExit", "-Command",
                               f"cd '{SCRIPT_DIR}'; docker compose logs -f"])
        elif OS == "Darwin":
            script = f'tell app "Terminal" to do script "cd {SCRIPT_DIR} && docker compose logs -f"'
            subprocess.Popen(["osascript", "-e", script])
        else:
            for term in ("gnome-terminal", "xterm", "konsole"):
                if shutil.which(term):
                    subprocess.Popen([term, "--", "bash", "-c",
                                       f"cd {SCRIPT_DIR} && docker compose logs -f; bash"])
                    break

    def _copy_url(self):
        self.clipboard_clear()
        self.clipboard_append(API_URL)
        self.copy_btn.configure(text="Copied!")
        self.after(1500, lambda: self.copy_btn.configure(text="Copy URL"))

    # ── Generate config and deploy ─────────────────────────────────────────────

    def _generate_and_deploy(self):
        if not docker_running():
            self.log("Start Docker Desktop first.", "error"); return

        px = self.proxy_entry.get().strip()
        k1 = f"sk-{rand_hex()}"
        k2 = f"sk-{rand_hex()}"
        pw = rand_pwd()

        cfg = "\n".join([
            "config-version: 8",
            'host: "0.0.0.0"',
            f"port: {PORT}",
            "access:",
            "  api-keys:",
            f'    - "{k1}"',
            f'    - "{k2}"',
            "oauth:",
            '  auth-dir: "/root/.cli-proxy-api"',
            "routing:",
            '  strategy: "round-robin"',
            "remote-management:",
            "  allow-remote: true",
            f'  secret-key: "{pw}"',
            "  disable-control-panel: false",
        ]) + "\n"

        CFG_PATH.write_text(cfg, encoding="utf-8")
        self.log("config.yaml generated.", "ok")

        # Save credentials for UI display
        creds = {"api_keys": [k1, k2], "mgmt_password": pw,
                 "mgmt_url": MGMT_URL, "api_url": API_URL}
        CREDS_PATH.write_text(json.dumps(creds, indent=2), encoding="utf-8")

        if px and px != "0":
            cmp = CMP_PATH.read_text(encoding="utf-8")
            if "HTTP_PROXY" not in cmp:
                env_block = (
                    f"    environment:\n"
                    f"      - HTTP_PROXY=http://host.docker.internal:{px}\n"
                    f"      - HTTPS_PROXY=http://host.docker.internal:{px}\n"
                    f"      - NO_PROXY=localhost,127.0.0.1\n"
                )
                cmp = cmp.replace("    restart:", env_block + "    restart:")
                CMP_PATH.write_text(cmp, encoding="utf-8")
                self.log(f"Proxy configured: port {px}", "ok")

        self.log("")
        self.log("═══ Save these credentials! ═══", "warn")
        self.log(f"API Key 1:     {k1}", "ok")
        self.log(f"API Key 2:     {k2}", "ok")
        self.log(f"Mgmt password: {pw}", "ok")
        self.log(f"Mgmt URL:      {MGMT_URL}", "ok")
        self.log("")

        ensure_dirs()
        self.wiz_frame.pack_forget()
        self._refresh()

        def do():
            rc = run_compose(["pull"], self._safe_log)
            if rc != 0:
                self._safe_log("Pull failed — using existing image.", "warn")
            run_compose(["up", "-d", "--pull", "never"], self._safe_log)
        self._run_bg(do, done=lambda: (
            self._refresh(),
            self.log("All done! Opening management panel...", "ok"),
            open_browser(MGMT_URL)
        ))

    # ── Background task helper ─────────────────────────────────────────────────

    def _safe_log(self, msg: str, kind: str = "normal"):
        """Thread-safe log: schedule on main thread via after()."""
        self.after(0, lambda m=msg, k=kind: self.log(m, k))

    def _run_bg(self, fn, done=None):
        """Run fn in background thread; schedule done() on main thread only on success."""
        def worker():
            try:
                fn()
                if done:
                    self.after(0, done)
            except Exception as e:
                msg = str(e)
                self.after(0, lambda m=msg: self.log(f"Error: {m}", "error"))
        threading.Thread(target=worker, daemon=True).start()

    def on_close(self):
        if self._auto:
            self.after_cancel(self._auto)
        self.destroy()


if __name__ == "__main__":
    try:
        app = App()
        app.protocol("WM_DELETE_WINDOW", app.on_close)
        app.mainloop()
    except Exception as e:
        import traceback
        msg = traceback.format_exc()
        try:
            import tkinter.messagebox as mb
            import tkinter as tk
            root = tk.Tk(); root.withdraw()
            mb.showerror("CLIProxyAPI Launcher Error", msg)
        except Exception:
            print(msg, file=sys.stderr)
