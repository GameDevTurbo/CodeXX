#!/usr/bin/env python3
"""CLIProxyAPI Client Tool — configure this machine to use a remote CLIProxyAPI."""

import os
import sys
import json
import re
import threading
import platform
import subprocess
import shutil
import webbrowser
from pathlib import Path

try:
    import customtkinter as ctk
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter", "-q"])
    import customtkinter as ctk

OS = platform.system()
ENC = {"encoding": "utf-8", "errors": "replace"}
_NO_WIN = {"creationflags": subprocess.CREATE_NO_WINDOW} if OS == "Windows" else {}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C_BG    = "#0f0f14"
C_PANEL = "#1a1a24"
C_CARD  = "#16161f"
C_INPUT = "#24243a"
C_BLUE  = "#388bfd"
C_GREEN = "#3fb950"
C_RED   = "#da3633"
C_ORANGE= "#d28a28"
C_DIM   = "#646478"
C_TEXT  = "#dcdce6"


def find_tailscale() -> str:
    found = shutil.which("tailscale")
    if found:
        return found
    for p in [r"C:\Program Files\Tailscale\tailscale.exe",
              r"C:\Program Files (x86)\Tailscale\tailscale.exe",
              "/usr/local/bin/tailscale", "/opt/homebrew/bin/tailscale"]:
        if Path(p).exists():
            return p
    return ""


def _run_streaming(cmd: list, log_fn) -> int:
    """Run command, stream output line-by-line to log_fn, return exit code."""
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            **ENC, **_NO_WIN)
        for line in proc.stdout:
            line = line.strip()
            if line:
                log_fn(line[:200], "dim")
        proc.wait(timeout=180)
        return proc.returncode
    except Exception as e:
        log_fn(f"Error: {e}", "error")
        return 1


def install_tailscale(log_fn) -> bool:
    """Install Tailscale for the current platform. Returns True on success."""
    log_fn("Installing Tailscale...", "warn")
    if OS == "Windows":
        if shutil.which("winget"):
            rc = _run_streaming(["winget", "install", "tailscale.tailscale", "-e",
                               "--accept-source-agreements",
                               "--accept-package-agreements"], log_fn)
            return rc == 0
        else:
            # Download installer silently
            import urllib.request, tempfile
            url = "https://pkgs.tailscale.com/stable/tailscale-setup-latest-amd64.exe"
            log_fn("Downloading Tailscale installer...", "dim")
            try:
                tmp = Path(tempfile.gettempdir()) / "tailscale-setup.exe"
                urllib.request.urlretrieve(url, tmp)
                rc = _run_streaming([str(tmp), "/quiet", "/norestart"], log_fn)
                return rc == 0
            except Exception as e:
                log_fn(f"Download failed: {e}", "error")
                return False
    elif OS == "Darwin":
        if shutil.which("brew"):
            rc = _run_streaming(["brew", "install", "--cask", "tailscale"], log_fn)
            return rc == 0
        else:
            # App Store fallback
            webbrowser.open("https://apps.apple.com/us/app/tailscale/id1475387142")
            log_fn("Opening App Store for Tailscale...", "warn")
            return False
    else:
        rc = _run_streaming(["bash", "-c",
                          "curl -fsSL https://tailscale.com/install.sh | sh"], log_fn)
        return rc == 0


def install_node(log_fn) -> bool:
    """Install Node.js for the current platform."""
    log_fn("Installing Node.js...", "dim")
    if OS == "Windows":
        if shutil.which("winget"):
            rc = _run_streaming(["winget", "install", "OpenJS.NodeJS.LTS", "-e",
                               "--accept-source-agreements",
                               "--accept-package-agreements"], log_fn)
            return rc == 0
        else:
            import urllib.request, tempfile
            url = "https://nodejs.org/dist/latest-v22.x/node-v22.11.0-x64.msi"
            log_fn("Downloading Node.js installer...", "dim")
            try:
                tmp = Path(tempfile.gettempdir()) / "node-setup.msi"
                urllib.request.urlretrieve(url, tmp)
                rc = _run_streaming(["msiexec", "/i", str(tmp), "/quiet", "/norestart"], log_fn)
                return rc == 0
            except Exception as e:
                log_fn(f"Download failed: {e}", "error")
                return False
    elif OS == "Darwin":
        if shutil.which("brew"):
            rc = _run_streaming(["brew", "install", "node"], log_fn)
            return rc == 0
        webbrowser.open("https://nodejs.org")
        return False
    else:
        # Linux: use nodesource
        script = ("curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - "
                  "&& sudo apt-get install -y nodejs")
        if shutil.which("apt-get"):
            rc = _run_streaming(["bash", "-c", script], log_fn)
        elif shutil.which("dnf"):
            rc = _run_streaming(["sudo", "dnf", "install", "-y", "nodejs", "npm"], log_fn)
        else:
            rc = _run_streaming(["bash", "-c",
                              "curl -fsSL https://nodejs.org/dist/latest/node-linux-x64.tar.gz"
                              " | sudo tar -xz -C /usr/local --strip-components=1"], log_fn)
        return rc == 0

def ts_status() -> dict:
    exe = find_tailscale()
    if not exe:
        return {"installed": False, "connected": False, "ip": "", "state": "not_installed"}
    try:
        r = subprocess.run([exe, "status", "--json"],
                           capture_output=True, timeout=8, **ENC, **_NO_WIN)
        if r.returncode != 0:
            # CLI ran but daemon may not be reachable — service likely stopped
            return {"installed": True, "connected": False, "ip": "", "state": "service_stopped"}
        data = json.loads(r.stdout)
        backend = data.get("BackendState", "")
        if backend == "Running":
            addrs = data.get("Self", {}).get("TailscaleIPs", [])
            ip = next((a for a in addrs if "." in a), "")
            return {"installed": True, "connected": True, "ip": ip, "state": "running"}
        elif backend == "NeedsLogin":
            return {"installed": True, "connected": False, "ip": "", "state": "needs_login"}
        elif backend == "NoState":
            # Daemon just started, not yet initialized — treat as service_stopped
            return {"installed": True, "connected": False, "ip": "", "state": "service_stopped"}
        elif backend == "Stopped":
            # Authenticated but disconnected — just need tailscale up
            return {"installed": True, "connected": False, "ip": "", "state": "disconnected"}
        return {"installed": True, "connected": False, "ip": "", "state": backend.lower() or "disconnected"}
    except Exception:
        return {"installed": True, "connected": False, "ip": "", "state": "service_stopped"}


def test_connection(api_url: str, api_key: str) -> tuple[bool, str]:
    try:
        import urllib.request
        req = urllib.request.Request(
            f"{api_url.rstrip('/')}/models",
            headers={"Authorization": f"Bearer {api_key}"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
            models = [m["id"] for m in data.get("data", [])]
            return True, f"{len(models)} models available: {', '.join(models[:3])}"
    except Exception as e:
        return False, str(e)


def get_claude_settings_path() -> Path:
    return Path.home() / ".claude" / "settings.json"


def get_ccswitch_config_path() -> Path:
    return Path.home() / ".codex" / "config.toml"


def configure_claude_code(api_url: str, api_key: str) -> str:
    path = get_claude_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception:
        data = {}
    data.setdefault("env", {})
    data["env"]["ANTHROPIC_BASE_URL"] = api_url
    data["env"]["ANTHROPIC_API_KEY"]  = api_key
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(path)


def configure_ccswitch(api_url: str, api_key: str, name: str = "cliproxy") -> str:
    path = get_ccswitch_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    block = (
        f'\n[model_providers.{name}]\n'
        f'name = "{name}"\n'
        f'wire_api = "responses"\n'
        f'requires_openai_auth = false\n'
        f'base_url = "{api_url}"\n'
        f'api_key = "{api_key}"\n'
    )
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    # Remove existing block for same name
    text = re.sub(
        rf'\n\[model_providers\.{re.escape(name)}\][^\[]*', "", text)
    text = text.rstrip() + "\n" + block
    path.write_text(text, encoding="utf-8")
    return str(path)


def set_env_vars(api_url: str, api_key: str) -> str:
    if OS == "Windows":
        subprocess.run(["setx", "OPENAI_BASE_URL", api_url], capture_output=True)
        subprocess.run(["setx", "OPENAI_API_KEY", api_key], capture_output=True)
        subprocess.run(["setx", "ANTHROPIC_BASE_URL", api_url], capture_output=True)
        subprocess.run(["setx", "ANTHROPIC_API_KEY", api_key], capture_output=True)
        return "System env vars set (restart terminal to take effect)"
    else:
        profile = Path.home() / (".zshrc" if Path.home().joinpath(".zshrc").exists() else ".bashrc")
        lines = profile.read_text(encoding="utf-8") if profile.exists() else ""
        for key, val in [("OPENAI_BASE_URL", api_url), ("OPENAI_API_KEY", api_key),
                          ("ANTHROPIC_BASE_URL", api_url), ("ANTHROPIC_API_KEY", api_key)]:
            lines = re.sub(rf'^export {key}=.*$', "", lines, flags=re.MULTILINE)
            lines += f'\nexport {key}="{val}"'
        profile.write_text(lines.strip() + "\n", encoding="utf-8")
        return f"Written to {profile} (run: source {profile})"


class ClientApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CLIProxyAPI Client")
        self.geometry("580x980")
        self.resizable(False, False)
        self.configure(fg_color=C_BG)
        self._ts_connected = False
        self._saved_url = ""
        self._saved_key = ""
        self._build_ui()
        self.after(200, self._check_tools)
        self.after(300, self._ts_refresh)
        self.after(500, self._auto_check_server)
        self._auto     = self.after(10000, self._tick)
        self._srv_auto = self.after(30000, self._server_tick)

    def _tick(self):
        self._ts_refresh()
        self._auto = self.after(10000, self._tick)

    def _server_tick(self):
        self._auto_check_server()
        self._srv_auto = self.after(30000, self._server_tick)

    def _auto_check_server(self):
        """Auto-check server connectivity in background."""
        url = getattr(self, "url_entry", None)
        key = getattr(self, "key_entry", None)
        if not url or not key:
            return
        u = url.get().strip()
        k = key.get().strip()
        if not u or not k:
            # Try to load from saved .credentials
            creds_path = Path(__file__).parent / ".last_connection.json"
            if creds_path.exists():
                try:
                    d = json.loads(creds_path.read_text(encoding="utf-8"))
                    u = d.get("api_url", "")
                    k = d.get("api_key", "")
                    if u and k:
                        self.after(0, lambda: (
                            url.delete(0, "end"), url.insert(0, u),
                            key.delete(0, "end"), key.insert(0, k)))
                except Exception:
                    pass
        if not u or not k:
            self.after(0, lambda: self._update_srv_status("no_config"))
            return

        def check():
            try:
                import urllib.request
                req = urllib.request.Request(
                    f"{u.rstrip('/')}/models",
                    headers={"Authorization": f"Bearer {k}"})
                with urllib.request.urlopen(req, timeout=6) as r:
                    data = json.loads(r.read())
                    count = len(data.get("data", []))
                    self.after(0, lambda: self._update_srv_status("online", count))
            except Exception:
                self.after(0, lambda: self._update_srv_status("offline"))
        threading.Thread(target=check, daemon=True).start()

    def _update_srv_status(self, state: str, model_count: int = 0):
        if not hasattr(self, "srv_dot"):
            return
        if state == "online":
            self.srv_dot.configure(text_color=C_GREEN)
            self.srv_stat.configure(
                text=f"Online · {model_count} models available", text_color=C_GREEN)
        elif state == "offline":
            self.srv_dot.configure(text_color=C_RED)
            self.srv_stat.configure(text="Unreachable — check Tailscale & server", text_color=C_RED)
        else:
            self.srv_dot.configure(text_color=C_DIM)
            self.srv_stat.configure(text="Enter API address and key below", text_color=C_DIM)
        self._refresh_readiness()

    def _build_ui(self):
        # ── Header ───────────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="CLIProxyAPI Client",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=C_BLUE).pack(anchor="w", padx=20, pady=(16, 0))
        ctk.CTkLabel(self, text="Follow the steps below to connect and configure.",
                     font=ctk.CTkFont(size=11), text_color=C_DIM
                     ).pack(anchor="w", padx=20, pady=(0, 8))

        # ── Status Dashboard ──────────────────────────────────────────────────
        dash = ctk.CTkFrame(self, fg_color="#0d1a0d", corner_radius=8)
        dash.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(dash, text="Live Status",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=C_GREEN).pack(anchor="w", padx=14, pady=(10,4))

        def status_row(parent, label):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=2)
            dot  = ctk.CTkLabel(row, text="●", font=ctk.CTkFont(size=12),
                                 text_color=C_DIM, width=18)
            dot.pack(side="left")
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=9),
                         text_color=C_DIM, width=80, anchor="w").pack(side="left", padx=(4,0))
            stat = ctk.CTkLabel(row, text="Checking...",
                                 font=ctk.CTkFont(size=9), text_color=C_DIM, anchor="w")
            stat.pack(side="left", padx=(4,0))
            return dot, stat

        self.ts_dash_dot, self.ts_dash_stat = status_row(dash, "Tailscale")
        self.srv_dot, self.srv_stat          = status_row(dash, "Server API")

        # Readiness indicator + quick refresh
        dash_btm = ctk.CTkFrame(dash, fg_color="transparent")
        dash_btm.pack(fill="x", padx=14, pady=(6,10))
        self.ready_lbl = ctk.CTkLabel(dash_btm, text="",
                                       font=ctk.CTkFont(size=10, weight="bold"),
                                       text_color=C_DIM)
        self.ready_lbl.pack(side="left")
        ctk.CTkButton(dash_btm, text="↺ Refresh Now", width=110, height=24,
                      font=ctk.CTkFont(size=9),
                      fg_color=C_PANEL, hover_color=C_CARD, text_color=C_DIM,
                      border_width=1, border_color=C_DIM,
                      command=lambda: (self._ts_refresh(), self._auto_check_server())
                      ).pack(side="right")

        # ── STEP 1: Tailscale ─────────────────────────────────────────────
        s1 = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=8)
        s1.pack(fill="x", padx=20, pady=(0, 8))

        s1h = ctk.CTkFrame(s1, fg_color="transparent")
        s1h.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(s1h, text="Step 1 — Tailscale Network",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C_TEXT).pack(side="left")
        ctk.CTkLabel(s1h, text="Required for remote access",
                     font=ctk.CTkFont(size=9), text_color=C_DIM).pack(side="right")

        ts_row = ctk.CTkFrame(s1, fg_color="transparent")
        ts_row.pack(fill="x", padx=14, pady=(0, 4))
        self.ts_dot  = ctk.CTkLabel(ts_row, text="●", font=ctk.CTkFont(size=14),
                                     text_color=C_DIM, width=18)
        self.ts_dot.pack(side="left")
        self.ts_stat = ctk.CTkLabel(ts_row, text="Checking...",
                                     font=ctk.CTkFont(size=10), text_color=C_DIM)
        self.ts_stat.pack(side="left", padx=(4, 0))

        ts_btns = ctk.CTkFrame(s1, fg_color="transparent")
        ts_btns.pack(fill="x", padx=14, pady=(2, 10))
        self.btn_ts_connect = ctk.CTkButton(
            ts_btns, text="Connect", width=110, height=28,
            font=ctk.CTkFont(size=9, weight="bold"),
            fg_color=C_GREEN, hover_color="#2d8a3e",
            command=self._ts_connect)
        self.btn_ts_connect.pack(side="left", padx=(0, 6))
        self.btn_ts_disconnect = ctk.CTkButton(
            ts_btns, text="Disconnect (keep LAN)", width=175, height=28,
            font=ctk.CTkFont(size=9, weight="bold"),
            fg_color="#7a2020", hover_color="#601818",
            command=self._ts_disconnect)
        self.btn_ts_disconnect.pack(side="left", padx=(0, 6))
        ctk.CTkButton(ts_btns, text="↺", width=32, height=28,
                      font=ctk.CTkFont(size=11),
                      fg_color=C_PANEL, hover_color=C_CARD, text_color=C_DIM,
                      border_width=1, border_color=C_DIM,
                      command=self._ts_refresh).pack(side="left")

        # ── STEP 2: Server Connection ─────────────────────────────────────
        self.s2_frame = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=8)
        self.s2_frame.pack(fill="x", padx=20, pady=(0, 8))

        s2h = ctk.CTkFrame(self.s2_frame, fg_color="transparent")
        s2h.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(s2h, text="Step 2 — Server Connection",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C_TEXT).pack(side="left")
        self.s2_hint = ctk.CTkLabel(s2h, text="⚠ Complete Step 1 first",
                                     font=ctk.CTkFont(size=9), text_color=C_ORANGE)
        self.s2_hint.pack(side="right")

        top = ctk.CTkFrame(self.s2_frame, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(0, 6))
        ctk.CTkButton(top, text="Import .cliproxy file", width=165,
                      fg_color=C_PANEL, border_width=1, border_color=C_DIM,
                      text_color=C_DIM, font=ctk.CTkFont(size=10),
                      hover_color=C_CARD,
                      command=self._import_file).pack(side="left")
        ctk.CTkLabel(top, text="or enter manually:",
                     text_color=C_DIM, font=ctk.CTkFont(size=10)
                     ).pack(side="left", padx=(10, 0))

        def entry_row(label, placeholder):
            f = ctk.CTkFrame(self.s2_frame, fg_color="transparent")
            f.pack(fill="x", padx=14, pady=3)
            ctk.CTkLabel(f, text=label, width=80, anchor="w",
                         text_color=C_DIM, font=ctk.CTkFont(size=10)).pack(side="left")
            e = ctk.CTkEntry(f, placeholder_text=placeholder,
                             fg_color=C_INPUT, border_color=C_DIM,
                             font=ctk.CTkFont(size=10))
            e.pack(side="left", fill="x", expand=True)
            return e

        self.url_entry = entry_row("API URL", "http://100.x.x.x:8317/v1")
        self.key_entry = entry_row("API Key", "sk-...")

        test_row = ctk.CTkFrame(self.s2_frame, fg_color="transparent")
        test_row.pack(fill="x", padx=14, pady=(6, 12))
        self.btn_test = ctk.CTkButton(test_row, text="Test Connection", width=145,
                                       fg_color=C_BLUE, hover_color="#2a6fd4",
                                       font=ctk.CTkFont(size=10, weight="bold"),
                                       command=self._test, state="disabled")
        self.btn_test.pack(side="left")
        self.test_lbl = ctk.CTkLabel(test_row, text="Connect Tailscale to enable",
                                      font=ctk.CTkFont(size=10), text_color=C_DIM)
        self.test_lbl.pack(side="left", padx=(10, 0))

        # Configure local tools (inside step 2)
        cfg = ctk.CTkFrame(self.s2_frame, fg_color=C_PANEL, corner_radius=6)
        cfg.pack(fill="x", padx=14, pady=(0, 12))
        ctk.CTkLabel(cfg, text="Configure",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=C_DIM).pack(anchor="w", padx=12, pady=(8, 4))
        tools_cfg = [
            ("Claude Code", self._cfg_claude),
            ("cc-switch",   self._cfg_ccswitch),
            ("Env Vars",    self._cfg_env),
            ("All at once", self._cfg_all),
        ]
        self.tool_labels = {}
        cfg_row = ctk.CTkFrame(cfg, fg_color="transparent")
        cfg_row.pack(fill="x", padx=12, pady=(0, 8))
        for name, cmd in tools_cfg:
            ctk.CTkButton(cfg_row, text=name, width=105, height=26,
                          fg_color=C_CARD, border_width=1, border_color=C_DIM,
                          text_color=C_TEXT, font=ctk.CTkFont(size=9),
                          hover_color="#22222e", command=cmd).pack(side="left", padx=(0, 4))
            self.tool_labels[name] = None   # not used for status here

        # ── STEP 3: Required Tools ───────────────────────────────────────
        chk = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=8)
        chk.pack(fill="x", padx=20, pady=(0, 8))

        chk_hdr = ctk.CTkFrame(chk, fg_color="transparent")
        chk_hdr.pack(fill="x", padx=14, pady=(10, 6))
        ctk.CTkLabel(chk_hdr, text="Step 3 — Install Required Tools",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C_TEXT).pack(side="left")
        self.btn_setup_all = ctk.CTkButton(
            chk_hdr, text="⚡ Setup All", width=110, height=26,
            font=ctk.CTkFont(size=9, weight="bold"),
            fg_color=C_BLUE, hover_color="#2a6fd4",
            command=self._setup_all)
        self.btn_setup_all.pack(side="right")

        self.tool_rows: dict = {}
        TOOLS = [
            ("Tailscale",   "tailscale", "https://tailscale.com/download",
             None,   "tailscale"),
            ("Node / npm",  "node",      "https://nodejs.org/en/download/",
             None,   "OpenJS.NodeJS.LTS"),
            ("Claude Code", "claude",    "https://docs.anthropic.com/en/docs/claude-code",
             "npm install -g @anthropic-ai/claude-code", None),
            ("Codex CLI",   "codex",     "https://github.com/openai/codex",
             "npm install -g @openai/codex", None),
            ("cc-switch",   "cc-switch", "https://github.com/farion1231/cc-switch/releases",
             None,   None),
        ]
        for name, cmd, url, npm_cmd, winget_id in TOOLS:
            row = ctk.CTkFrame(chk, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=3)
            dot  = ctk.CTkLabel(row, text="●", font=ctk.CTkFont(size=12),
                                 text_color=C_DIM, width=16)
            dot.pack(side="left")
            lbl  = ctk.CTkLabel(row, text=name, font=ctk.CTkFont(size=10),
                                 text_color=C_TEXT, width=100, anchor="w")
            lbl.pack(side="left", padx=(4, 0))
            stat = ctk.CTkLabel(row, text="Checking...", font=ctk.CTkFont(size=9),
                                 text_color=C_DIM, width=160, anchor="w")
            stat.pack(side="left", padx=(6, 0))
            btn  = ctk.CTkButton(row, text="Install", width=80, height=24,
                                  font=ctk.CTkFont(size=8),
                                  fg_color=C_ORANGE, hover_color="#a06020",
                                  command=lambda u=url, n=npm_cmd, w=winget_id:
                                      self._install_tool(u, n, w))
            btn.pack(side="right")
            btn.pack_forget()
            self.tool_rows[name] = {"dot": dot, "stat": stat, "btn": btn,
                                     "cmd": cmd, "url": url,
                                     "npm": npm_cmd, "winget": winget_id}

        chk_bot = ctk.CTkFrame(chk, fg_color="transparent")
        chk_bot.pack(fill="x", padx=14, pady=(4, 12))
        self.btn_recheck = ctk.CTkButton(
            chk_bot, text="↺  Recheck", width=90, height=26,
            font=ctk.CTkFont(size=9),
            fg_color=C_PANEL, hover_color=C_CARD, text_color=C_DIM,
            border_width=1, border_color=C_DIM,
            command=self._recheck_tools)
        self.btn_recheck.pack(side="left")
        self.chk_status_lbl = ctk.CTkLabel(
            chk_bot, text="", font=ctk.CTkFont(size=9), text_color=C_DIM)
        self.chk_status_lbl.pack(side="left", padx=(10, 0))

        # ── Log ──────────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Log", font=ctk.CTkFont(size=10),
                     text_color=C_DIM).pack(anchor="w", padx=20)
        self.log_box = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Courier", size=9),
            fg_color="#0a0a0e", text_color=C_TEXT, corner_radius=6, wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=20, pady=(4, 16))
        self.log_box.configure(state="disabled")

    # ── Tailscale ──────────────────────────────────────────────────────────────

    def _ts_refresh(self):
        threading.Thread(target=self._ts_refresh_worker, daemon=True).start()

    def _ts_refresh_worker(self):
        ts = ts_status()
        self.after(0, lambda: self._ts_apply(ts))

    def _refresh_readiness(self):
        """Update the dashboard readiness indicator."""
        if not hasattr(self, "ready_lbl"):
            return
        ts_ok  = self._ts_connected
        srv_ok = hasattr(self, "srv_stat") and "Online" in self.srv_stat.cget("text")
        if ts_ok and srv_ok:
            self.ready_lbl.configure(text="✓ Ready — all systems go", text_color=C_GREEN)
        elif ts_ok:
            self.ready_lbl.configure(text="Tailscale ✓  Server ✗ — enter config below", text_color=C_ORANGE)
        else:
            self.ready_lbl.configure(text="Connect Tailscale first (Step 1)", text_color=C_RED)

    def _ts_apply(self, ts: dict):
        """Update Tailscale UI, gate Step 2, and sync dashboard."""
        self.btn_ts_connect.pack_forget()
        self.btn_ts_disconnect.pack_forget()

        connected = ts.get("connected", False)
        self._ts_connected = connected

        # Sync dashboard dot
        if hasattr(self, "ts_dash_dot"):
            if connected:
                self.ts_dash_dot.configure(text_color=C_GREEN)
                self.ts_dash_stat.configure(
                    text=f"Connected · {ts.get('ip', '')}", text_color=C_GREEN)
            elif not ts.get("installed", True):
                self.ts_dash_dot.configure(text_color=C_DIM)
                self.ts_dash_stat.configure(text="Not installed", text_color=C_DIM)
            else:
                self.ts_dash_dot.configure(text_color=C_RED)
                self.ts_dash_stat.configure(text="Not connected", text_color=C_RED)

        # Gate Step 2
        if connected:
            self.btn_test.configure(state="normal", fg_color=C_BLUE)
            self.test_lbl.configure(text="", text_color=C_DIM)
            self.s2_hint.configure(text="✓ Tailscale connected", text_color=C_GREEN)
            self._auto_check_server()
        else:
            self.btn_test.configure(state="disabled", fg_color=C_DIM)
            self.test_lbl.configure(text="Connect Tailscale to enable", text_color=C_DIM)
            self.s2_hint.configure(text="⚠ Complete Step 1 first", text_color=C_ORANGE)

        if not ts["installed"]:
            self.ts_dot.configure(text_color=C_DIM)
            self.ts_stat.configure(text="Not installed", text_color=C_DIM)
            self.btn_ts_connect.configure(text="Install", fg_color=C_ORANGE,
                                           command=lambda: self._install_tool(
                                               "https://tailscale.com/download", None, "tailscale"))
            self.btn_ts_connect.pack(side="left", padx=(0, 6))

        elif connected:
            self.ts_dot.configure(text_color=C_GREEN)
            self.ts_stat.configure(text=f"● Connected · {ts['ip']}", text_color=C_GREEN)
            self.btn_ts_disconnect.pack(side="left", padx=(0, 6))

        elif ts["state"] == "service_stopped":
            self.ts_dot.configure(text_color=C_RED)
            self.ts_stat.configure(text="Service not running — start it first", text_color=C_RED)
            self.btn_ts_connect.configure(text="① Start Service", fg_color="#8b3a00",
                                           command=self._ts_start_service)
            self.btn_ts_connect.pack(side="left", padx=(0, 6))

        elif ts["state"] == "needs_login":
            self.ts_dot.configure(text_color=C_ORANGE)
            self.ts_stat.configure(text="Service running — need to log in", text_color=C_ORANGE)
            self.btn_ts_connect.configure(text="② Login", fg_color=C_ORANGE,
                                           command=self._ts_login)
            self.btn_ts_connect.pack(side="left", padx=(0, 6))

        elif ts["state"] == "disconnected":
            self.ts_dot.configure(text_color=C_RED)
            self.ts_stat.configure(text="Logged in but disconnected", text_color=C_RED)
            self.btn_ts_connect.configure(text="③ Connect", fg_color=C_GREEN,
                                           command=self._ts_connect)
            self.btn_ts_connect.pack(side="left", padx=(0, 6))

        else:
            self.ts_dot.configure(text_color=C_DIM)
            self.ts_stat.configure(text=f"Unknown state: {ts.get('state')}", text_color=C_DIM)
            self.btn_ts_connect.configure(text="Retry", fg_color=C_DIM,
                                           command=self._ts_connect)
            self.btn_ts_connect.pack(side="left", padx=(0, 6))

    def _recheck_tools(self):
        """Recheck with visual busy indicator."""
        self.btn_recheck.configure(text="↺ Checking...", state="disabled")
        self.chk_status_lbl.configure(text="Scanning...", text_color=C_DIM)
        def run():
            self._check_tools_bg()
            self.after(0, lambda: (
                self.btn_recheck.configure(text="↺  Recheck", state="normal"),
                self.chk_status_lbl.configure(text="Done", text_color=C_GREEN)
            ))
            self.after(3000, lambda: self.chk_status_lbl.configure(text=""))
        threading.Thread(target=run, daemon=True).start()

    def _ts_start_service(self):
        """Start the Tailscale service/daemon. All output goes to the log panel."""
        self.log("─── Starting Tailscale Service ───", "warn")
        exe = find_tailscale()
        if not exe:
            self.log("ERROR: tailscale.exe not found. Is Tailscale installed?", "error")
            return

        self.log(f"Found: {exe}", "dim")

        def run():
            # Step 1: try net start (service might allow it without full admin)
            self.after(0, lambda: self.log("Attempting: net start tailscale ...", "dim"))
            r1 = subprocess.run(["net", "start", "tailscale"],
                                capture_output=True, **ENC, **_NO_WIN)
            out1 = (r1.stdout + r1.stderr).strip()
            if out1:
                for line in out1.splitlines():
                    self.after(0, lambda l=line: self.log(f"  {l}", "ok" if r1.returncode == 0 else "dim"))

            if r1.returncode == 0:
                self.after(0, lambda: self.log("Service started!", "ok"))
            else:
                # Step 2: try tailscale up — it may start the daemon implicitly
                self.after(0, lambda: self.log("Trying: tailscale up ...", "dim"))
                r2 = subprocess.run([exe, "up"], capture_output=True, timeout=15, **ENC, **_NO_WIN)
                out2 = (r2.stdout + r2.stderr).strip()
                if out2:
                    for line in out2.splitlines():
                        self.after(0, lambda l=line: self.log(f"  {l}", "dim"))

                if r2.returncode != 0:
                    # Step 3: need admin — show clear instructions in log
                    self.after(0, lambda: (
                        self.log("─── Admin Required ───────────────", "warn"),
                        self.log("The Tailscale service needs to be started with admin rights.", "warn"),
                        self.log("Please do ONE of the following:", "warn"),
                        self.log("  A) Open Start Menu → search 'Tailscale' → Run as administrator", "dim"),
                        self.log("  B) Open CMD as Administrator → type: net start tailscale", "dim"),
                        self.log("  C) Open Services (services.msc) → find Tailscale → Start", "dim"),
                        self.log("After starting, click ↺ Refresh in this tool.", "dim"),
                        self.log("──────────────────────────────────", "warn"),
                    ))

            import time; time.sleep(2)
            self.after(0, lambda: (
                self.log("Rechecking Tailscale status...", "dim"),
                self._ts_refresh()
            ))
        threading.Thread(target=run, daemon=True).start()

    def _ts_connect(self):
        exe = find_tailscale()
        if not exe:
            self.log("Tailscale not found.", "error"); return
        self.log("─── Connecting Tailscale ──────────", "warn")
        self.log(f"Running: {exe} up", "dim")
        def run():
            try:
                r = subprocess.run([exe, "up"], capture_output=True,
                                   timeout=30, **ENC, **_NO_WIN)
                out = (r.stdout + r.stderr).strip()
                if out:
                    for line in out.splitlines():
                        self.after(0, lambda l=line: self.log(f"  {l}", "dim"))
                self.after(0, lambda: (
                    self.log("Connected!" if r.returncode == 0
                             else f"Exit code: {r.returncode}", "ok" if r.returncode == 0 else "warn"),
                    self._ts_refresh()
                ))
            except subprocess.TimeoutExpired:
                self.after(0, lambda: self.log("Timeout — check Tailscale status manually", "warn"))
            except Exception as e:
                self.after(0, lambda: self.log(f"Error: {e}", "error"))
        threading.Thread(target=run, daemon=True).start()

    def _ts_disconnect(self):
        exe = find_tailscale()
        if not exe:
            self.log("Tailscale not found.", "error"); return
        self.log("─── Disconnecting Tailscale ───────", "warn")
        def run():
            try:
                r = subprocess.run([exe, "down"], capture_output=True,
                                   timeout=15, **ENC, **_NO_WIN)
                out = (r.stdout + r.stderr).strip()
                if out:
                    for line in out.splitlines():
                        self.after(0, lambda l=line: self.log(f"  {l}", "dim"))
                self.after(0, lambda: (
                    self.log("Disconnected. LAN access restored." if r.returncode == 0
                             else "Disconnect may have failed.", "ok" if r.returncode == 0 else "warn"),
                    self._ts_refresh()
                ))
            except Exception as e:
                self.after(0, lambda: self.log(f"Error: {e}", "error"))
        threading.Thread(target=run, daemon=True).start()

    def _ts_login(self):
        exe = find_tailscale()
        if not exe:
            self.log("Tailscale not installed — click [Install] to auto-install.", "error")
            return
        self.log("─── Tailscale Login ───────────────", "warn")
        self.log(f"Running: {exe} up", "dim")
        self.log("A browser should open automatically — complete login there.", "dim")

        def run():
            try:
                # No stdout redirect — let Tailscale open browser via Windows API
                proc = subprocess.Popen([exe, "up"])
                proc.wait(timeout=90)
                self.after(0, lambda: self.log("tailscale up finished.", "dim"))
            except subprocess.TimeoutExpired:
                proc.kill()
                self.after(0, lambda: self.log("Timed out — check your browser.", "warn"))
            except Exception as e:
                self.after(0, lambda: self.log(f"Error: {e}", "warn"))
        threading.Thread(target=run, daemon=True).start()

        # Poll every 3s for up to 60s after login attempt
        self.after(3000, lambda: self._ts_poll_until_connected(0))

    def _ts_poll_until_connected(self, attempt: int):
        """Poll Tailscale status after login, update UI when connected."""
        def check():
            ts = ts_status()
            if ts["connected"]:
                self.after(0, lambda: (
                    self._ts_apply(ts),
                    self.log(f"Tailscale connected: {ts['ip']}", "ok")
                ))
            elif attempt < 20:
                self.after(0, lambda a=attempt: self.log(
                    f"Waiting for Tailscale auth... ({a*3}s)", "dim"))
                self.after(3000, lambda: self._ts_poll_until_connected(attempt + 1))
            else:
                self.after(0, lambda: (
                    self._ts_refresh(),
                    self.log("Login timed out. Check your browser and try again.", "error")
                ))
        threading.Thread(target=check, daemon=True).start()

    # ── Tool checker ───────────────────────────────────────────────────────────

    def _check_tools(self):
        threading.Thread(target=self._check_tools_bg, daemon=True).start()

    def _check_tools_bg(self):
        for name, info in self.tool_rows.items():
            found = shutil.which(info["cmd"])
            if found:
                try:
                    r = subprocess.run([info["cmd"], "--version"], capture_output=True,
                                       timeout=5, **ENC, **_NO_WIN)
                    ver = (r.stdout or r.stderr).strip().splitlines()[0][:30]
                except Exception:
                    ver = "installed"
                self.after(0, lambda n=name, v=ver: (
                    self.tool_rows[n]["dot"].configure(text_color=C_GREEN),
                    self.tool_rows[n]["stat"].configure(text=v, text_color=C_GREEN),
                    self.tool_rows[n]["btn"].pack_forget()
                ))
            else:
                self.after(0, lambda n=name: (
                    self.tool_rows[n]["dot"].configure(text_color=C_RED),
                    self.tool_rows[n]["stat"].configure(text="Not found", text_color=C_RED),
                    self.tool_rows[n]["btn"].pack(side="right")
                ))

    def _install_tool(self, url: str, npm_cmd: str | None, winget_id: str | None = None):
        name = next((k for k, v in self.tool_rows.items()
                     if v.get("url") == url), "")
        info = self.tool_rows.get(name, {})
        btn  = info.get("btn")
        stat = info.get("stat")

        # Show installing state in UI
        def set_busy(msg="Installing..."):
            if btn:  btn.configure(text=msg, state="disabled", fg_color=C_DIM)
            if stat: stat.configure(text=msg, text_color=C_ORANGE)

        def set_done(ok: bool, msg: str):
            if btn:  btn.configure(state="normal",
                                    fg_color=C_GREEN if ok else C_ORANGE,
                                    text="Installed ✓" if ok else "Retry")
            if stat: stat.configure(text=msg, text_color=C_GREEN if ok else C_RED)

        self.after(0, set_busy)
        self.log(f"Installing {name or 'tool'}...", "warn")

        def log_live(m, k="dim"):
            self.after(0, lambda: self.log(m, k))

        def run():
            ok = False
            if name == "Tailscale":
                ok = install_tailscale(log_live)
                self.after(0, lambda o=ok: set_done(o, "Installed ✓" if o else "Install failed"))
                if ok:
                    self.after(0, lambda: (
                        self.log("Tailscale installed! Connecting...", "ok"),
                        self._check_tools(),
                        self._ts_login()
                    ))
                    return
            elif name == "Node / npm":
                ok = install_node(log_live)
                self.after(0, lambda o=ok: set_done(o, "Installed ✓ (restart to use npm)" if o else "Install failed"))
                if ok:
                    self.after(0, lambda: (
                        self.log("Node.js installed! Restart this tool to use npm.", "ok"),
                        self._check_tools()
                    ))
                    return
            elif npm_cmd and shutil.which("npm"):
                proc = subprocess.Popen(npm_cmd.split(),
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        **ENC, **_NO_WIN)
                for line in proc.stdout:
                    line = line.strip()
                    if line: self.after(0, lambda l=line: self.log(l, "dim"))
                proc.wait()
                ok = proc.returncode == 0
                self.after(0, lambda o=ok: set_done(o, "Installed ✓" if o else "npm failed"))
                if ok:
                    self.after(500, self._check_tools)
                    return
            # Fallback: nothing available to auto-install
            self.after(0, lambda: (
                set_done(False, "Manual install needed"),
                self.log(f"Cannot auto-install {name}. Visit: {url}", "warn")
            ))
        threading.Thread(target=run, daemon=True).start()

    def _setup_all(self):
        """Install all missing tools in sequence, non-blocking."""
        self.btn_setup_all.configure(text="Installing... please wait", state="disabled")
        self.chk_status_lbl.configure(text="", text_color=C_DIM)
        self.log("=== Setting up all missing tools ===", "warn")
        def run():
            installed_any = False
            for name, info in self.tool_rows.items():
                if shutil.which(info["cmd"]):
                    continue
                installed_any = True
                self.after(0, lambda n=name: (
                    self.log(f"Installing {n}...", "dim"),
                    self.chk_status_lbl.configure(text=f"Installing {n}...", text_color=C_ORANGE)
                ))
                ok = False
                if name == "Tailscale":
                    ok = install_tailscale(
                        lambda m, k="dim": self.after(0, lambda: self.log(m, k)))
                elif name == "Node / npm":
                    ok = install_node(
                        lambda m, k="dim": self.after(0, lambda: self.log(m, k)))
                elif info.get("npm") and shutil.which("npm"):
                    r = subprocess.run(info["npm"].split(),
                                       capture_output=True, **ENC, **_NO_WIN)
                    ok = r.returncode == 0
                self.after(0, lambda n=name, o=ok: self.log(
                    f"{n}: {'✓ installed' if o else '✗ failed — check log'}", "ok" if o else "warn"))
            self.after(0, lambda: (
                self.log("=== Setup complete. Rechecking... ===", "ok"),
                self._check_tools(),
                self.btn_setup_all.configure(text="⚡ Setup All", state="normal"),
                self.chk_status_lbl.configure(
                    text="All done!" if installed_any else "All tools already installed",
                    text_color=C_GREEN)
            ))
            self.after(4000, lambda: self.chk_status_lbl.configure(text=""))
        threading.Thread(target=run, daemon=True).start()

    def log(self, msg: str, color: str = C_TEXT):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"{msg}\n")
        self.log_box.configure(state="disabled")
        self.log_box.see("end")

    def _get_inputs(self) -> tuple[str, str]:
        return self.url_entry.get().strip(), self.key_entry.get().strip()

    def _import_file(self):
        import tkinter.filedialog as fd
        path = fd.askopenfilename(
            parent=self,
            title="Import connection file",
            filetypes=[("CLIProxy config", "*.cliproxy"), ("JSON", "*.json"), ("All", "*.*")])
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, data.get("api_url", ""))
            self.key_entry.delete(0, "end")
            self.key_entry.insert(0, data.get("api_key", ""))
            self.log(f"Imported from {Path(path).name}", C_GREEN)
        except Exception as e:
            self.log(f"Import failed: {e}", C_RED)

    def _test(self):
        url, key = self._get_inputs()
        if not url or not key:
            self.test_lbl.configure(text="Enter URL and Key first", text_color=C_RED)
            return
        self.test_lbl.configure(text="Testing...", text_color=C_DIM)
        def run():
            ok, msg = test_connection(url, key)
            if ok:
                # Save last successful connection for auto-check
                try:
                    creds = {"api_url": url, "api_key": key}
                    (Path(__file__).parent / ".last_connection.json").write_text(
                        json.dumps(creds), encoding="utf-8")
                except Exception:
                    pass
                self.after(0, lambda: (
                    self.test_lbl.configure(text=f"✓ {msg[:60]}", text_color=C_GREEN),
                    self.log(f"Connection OK — {msg}", C_GREEN),
                    self._update_srv_status("online",
                        int(msg.split()[0]) if msg and msg[0].isdigit() else 0)
                ))
            else:
                self.after(0, lambda: (
                    self.test_lbl.configure(text="✗ Failed", text_color=C_RED),
                    self.log(f"Connection failed: {msg}", C_RED),
                    self._update_srv_status("offline")
                ))
        threading.Thread(target=run, daemon=True).start()

    def _cfg_claude(self):
        url, key = self._get_inputs()
        if not url or not key:
            self.log("Enter URL and Key first.", C_RED); return
        try:
            path = configure_claude_code(url, key)
            self.log(f"Claude Code configured → {path}", C_GREEN)
            self.tool_labels["Claude Code"].configure(text="✓ Configured", text_color=C_GREEN)
        except Exception as e:
            self.log(f"Error: {e}", C_RED)

    def _cfg_ccswitch(self):
        url, key = self._get_inputs()
        if not url or not key:
            self.log("Enter URL and Key first.", C_RED); return
        try:
            path = configure_ccswitch(url, key)
            self.log(f"cc-switch provider 'cliproxy' added → {path}", C_GREEN)
            self.log("In cc-switch: select 'cliproxy', set Protocol = OpenAI Responses", C_DIM)
            self.tool_labels["cc-switch"].configure(text="✓ Configured", text_color=C_GREEN)
        except Exception as e:
            self.log(f"Error: {e}", C_RED)

    def _cfg_env(self):
        url, key = self._get_inputs()
        if not url or not key:
            self.log("Enter URL and Key first.", C_RED); return
        try:
            msg = set_env_vars(url, key)
            self.log(f"Env vars set — {msg}", C_GREEN)
            self.tool_labels["Env Vars"].configure(text="✓ Configured", text_color=C_GREEN)
        except Exception as e:
            self.log(f"Error: {e}", C_RED)

    def _cfg_all(self):
        self._cfg_claude()
        self._cfg_ccswitch()
        self._cfg_env()
        self.tool_labels["All at once"].configure(text="✓ All configured!", text_color=C_GREEN)


if __name__ == "__main__":
    app = ClientApp()
    def on_close():
        if hasattr(app, "_auto"):
            app.after_cancel(app._auto)
        app.destroy()
    app.protocol("WM_DELETE_WINDOW", on_close)
    app.mainloop()
