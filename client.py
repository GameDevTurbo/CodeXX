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

def ts_status() -> dict:
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
        return {"installed": True, "connected": False, "ip": "", "state": backend.lower() or "stopped"}
    except Exception:
        return {"installed": True, "connected": False, "ip": "", "state": "unknown"}


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
    if OS == "Windows":
        return Path.home() / ".claude" / "settings.json"
    return Path.home() / ".claude" / "settings.json"


def get_ccswitch_config_path() -> Path:
    if OS == "Windows":
        return Path.home() / ".codex" / "config.toml"
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
    import re
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
            import re
            lines = re.sub(rf'^export {key}=.*$', "", lines, flags=re.MULTILINE)
            lines += f'\nexport {key}="{val}"'
        profile.write_text(lines.strip() + "\n", encoding="utf-8")
        return f"Written to {profile} (run: source {profile})"


class ClientApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CLIProxyAPI Client Setup")
        self.geometry("560x920")
        self.resizable(False, False)
        self.configure(fg_color=C_BG)
        self._build_ui()
        self.after(200, self._check_tools)
        self.after(300, self._ts_refresh)

    def _build_ui(self):
        # Header
        ctk.CTkLabel(self, text="Client Setup",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=C_BLUE).pack(anchor="w", padx=20, pady=(16, 0))
        ctk.CTkLabel(self, text="Connect this machine to a CLIProxyAPI server",
                     font=ctk.CTkFont(size=11), text_color=C_DIM
                     ).pack(anchor="w", padx=20, pady=(0, 12))

        # Import section
        imp = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=8)
        imp.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(imp, text="Server Connection",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C_TEXT).pack(anchor="w", padx=14, pady=(12, 4))

        # Import file button
        top = ctk.CTkFrame(imp, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(0, 8))
        ctk.CTkButton(top, text="Import .cliproxy file", width=170,
                      fg_color=C_PANEL, border_width=1, border_color=C_DIM,
                      text_color=C_DIM, font=ctk.CTkFont(size=10),
                      hover_color=C_CARD,
                      command=self._import_file).pack(side="left")
        ctk.CTkLabel(top, text="or enter manually:",
                     text_color=C_DIM, font=ctk.CTkFont(size=10)
                     ).pack(side="left", padx=(12, 0))

        # Manual entry
        def row(parent, label, placeholder, show=""):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(fill="x", padx=14, pady=3)
            ctk.CTkLabel(f, text=label, width=90, anchor="w",
                         text_color=C_DIM, font=ctk.CTkFont(size=10)).pack(side="left")
            e = ctk.CTkEntry(f, placeholder_text=placeholder, show=show,
                             fg_color=C_INPUT, border_color=C_DIM, font=ctk.CTkFont(size=10))
            e.pack(side="left", fill="x", expand=True)
            return e

        self.url_entry = row(imp, "API URL", "http://100.x.x.x:8317/v1")
        self.key_entry = row(imp, "API Key", "sk-...")

        # Test button
        test_row = ctk.CTkFrame(imp, fg_color="transparent")
        test_row.pack(fill="x", padx=14, pady=(6, 12))
        ctk.CTkButton(test_row, text="Test Connection", width=140,
                      fg_color=C_BLUE, hover_color="#2a6fd4",
                      font=ctk.CTkFont(size=10, weight="bold"),
                      command=self._test).pack(side="left")
        self.test_lbl = ctk.CTkLabel(test_row, text="",
                                      font=ctk.CTkFont(size=10), text_color=C_DIM)
        self.test_lbl.pack(side="left", padx=(10, 0))

        # Configure section
        cfg = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=8)
        cfg.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(cfg, text="Configure Local Tools",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C_TEXT).pack(anchor="w", padx=14, pady=(12, 6))

        tools = [
            ("Claude Code", "Auto-set ANTHROPIC_BASE_URL in ~/.claude/settings.json",
             self._cfg_claude),
            ("cc-switch",   "Add 'cliproxy' provider to ~/.codex/config.toml",
             self._cfg_ccswitch),
            ("Env Vars",    "Set OPENAI_BASE_URL / ANTHROPIC_BASE_URL system-wide",
             self._cfg_env),
            ("All at once", "Configure all tools above in one click",
             self._cfg_all),
        ]

        self.tool_labels = {}
        for name, desc, cmd in tools:
            row_f = ctk.CTkFrame(cfg, fg_color="transparent")
            row_f.pack(fill="x", padx=14, pady=4)
            ctk.CTkButton(row_f, text=name, width=130,
                          fg_color=C_PANEL, border_width=1, border_color=C_DIM,
                          text_color=C_TEXT, font=ctk.CTkFont(size=10),
                          hover_color=C_CARD, command=cmd).pack(side="left")
            lbl = ctk.CTkLabel(row_f, text=desc, text_color=C_DIM,
                               font=ctk.CTkFont(size=9), anchor="w")
            lbl.pack(side="left", padx=(10, 0))
            self.tool_labels[name] = lbl

        ctk.CTkFrame(cfg, fg_color="transparent", height=8).pack()

        # Tailscale section
        tsf = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=8)
        tsf.pack(fill="x", padx=20, pady=(0, 8))

        hdr = ctk.CTkFrame(tsf, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(hdr, text="Tailscale (Remote Network)",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C_TEXT).pack(side="left")

        self.ts_dot  = ctk.CTkLabel(tsf, text="●", font=ctk.CTkFont(size=14),
                                     text_color=C_DIM)
        self.ts_dot.pack(side="left", padx=(14,4), pady=(0,8))
        self.ts_stat = ctk.CTkLabel(tsf, text="Checking...",
                                     font=ctk.CTkFont(size=10), text_color=C_DIM)
        self.ts_stat.pack(side="left", pady=(0,8))

        btn_row = ctk.CTkFrame(tsf, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(0, 10))

        self.btn_ts_connect = ctk.CTkButton(
            btn_row, text="Connect", width=100, height=28,
            font=ctk.CTkFont(size=9, weight="bold"),
            fg_color=C_GREEN, hover_color="#2d8a3e",
            command=self._ts_connect)
        self.btn_ts_connect.pack(side="left", padx=(0, 6))

        self.btn_ts_disconnect = ctk.CTkButton(
            btn_row, text="Disconnect (keep LAN)", width=170, height=28,
            font=ctk.CTkFont(size=9, weight="bold"),
            fg_color="#7a2020", hover_color="#601818",
            command=self._ts_disconnect)
        self.btn_ts_disconnect.pack(side="left", padx=(0, 6))

        ctk.CTkButton(btn_row, text="↺", width=32, height=28,
                      font=ctk.CTkFont(size=11),
                      fg_color=C_PANEL, hover_color=C_CARD, text_color=C_DIM,
                      border_width=1, border_color=C_DIM,
                      command=self._ts_refresh).pack(side="left")

        # Tool checker section
        chk = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=8)
        chk.pack(fill="x", padx=20, pady=(0, 8))
        ctk.CTkLabel(chk, text="Required Tools",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C_TEXT).pack(anchor="w", padx=14, pady=(12,6))

        self.tool_rows: dict = {}
        TOOLS = [
            ("Claude Code", "claude",     "https://docs.anthropic.com/en/docs/claude-code",
             "npm install -g @anthropic-ai/claude-code"),
            ("Codex CLI",   "codex",      "https://github.com/openai/codex",
             "npm install -g @openai/codex"),
            ("cc-switch",   "cc-switch",  "https://github.com/farion1231/cc-switch/releases",
             None),
            ("Node / npm",  "node",       "https://nodejs.org/en/download/",
             None),
        ]
        for name, cmd, url, npm_cmd in TOOLS:
            row = ctk.CTkFrame(chk, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=3)
            dot  = ctk.CTkLabel(row, text="●", font=ctk.CTkFont(size=12),
                                 text_color=C_DIM, width=16)
            dot.pack(side="left")
            lbl  = ctk.CTkLabel(row, text=name, font=ctk.CTkFont(size=10),
                                 text_color=C_TEXT, width=100, anchor="w")
            lbl.pack(side="left", padx=(4,0))
            stat = ctk.CTkLabel(row, text="—", font=ctk.CTkFont(size=9),
                                 text_color=C_DIM, width=120, anchor="w")
            stat.pack(side="left", padx=(6,0))
            btn  = ctk.CTkButton(row, text="Install", width=80, height=24,
                                  font=ctk.CTkFont(size=8),
                                  fg_color=C_ORANGE, hover_color="#a06020",
                                  command=lambda u=url, n=npm_cmd: self._install_tool(u, n))
            btn.pack(side="right")
            btn.pack_forget()
            self.tool_rows[name] = {"dot": dot, "stat": stat, "btn": btn,
                                     "cmd": cmd, "url": url, "npm": npm_cmd}

        ctk.CTkButton(chk, text="↺  Recheck", width=90, height=26,
                      font=ctk.CTkFont(size=9),
                      fg_color=C_PANEL, hover_color=C_CARD, text_color=C_DIM,
                      border_width=1, border_color=C_DIM,
                      command=self._check_tools).pack(anchor="w", padx=14, pady=(4,12))

        # Log
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

    def _ts_apply(self, ts: dict):
        if not ts["installed"]:
            self.ts_dot.configure(text_color=C_DIM)
            self.ts_stat.configure(text="Not installed — download from tailscale.com", text_color=C_DIM)
            self.btn_ts_connect.configure(text="Download", fg_color=C_DIM,
                                           command=lambda: webbrowser.open("https://tailscale.com/download"))
            self.btn_ts_disconnect.pack_forget()
        elif ts["connected"]:
            self.ts_dot.configure(text_color=C_GREEN)
            self.ts_stat.configure(text=f"Connected · {ts['ip']}", text_color=C_GREEN)
            self.btn_ts_connect.pack_forget()
            self.btn_ts_disconnect.pack(side="left", padx=(0,6))
        elif ts["state"] == "needs_login":
            self.ts_dot.configure(text_color=C_ORANGE)
            self.ts_stat.configure(text="Not logged in", text_color=C_ORANGE)
            self.btn_ts_connect.configure(text="Login", fg_color=C_ORANGE,
                                           command=self._ts_login)
            self.btn_ts_connect.pack(side="left", padx=(0,6))
            self.btn_ts_disconnect.pack_forget()
        else:
            self.ts_dot.configure(text_color=C_RED)
            self.ts_stat.configure(text=f"Disconnected ({ts['state']})", text_color=C_RED)
            self.btn_ts_connect.configure(text="Connect", fg_color=C_GREEN,
                                           command=self._ts_connect)
            self.btn_ts_connect.pack(side="left", padx=(0,6))
            self.btn_ts_disconnect.pack_forget()

    def _ts_connect(self):
        exe = find_tailscale()
        if not exe:
            self.log("Tailscale not found.", "error"); return
        self.log("Connecting Tailscale...", "dim")
        def run():
            r = subprocess.run([exe, "up"], capture_output=True, **ENC, **_NO_WIN)
            self.after(0, lambda: (
                self.log("Tailscale connected." if r.returncode == 0
                         else f"Error: {r.stderr.strip()}", "ok" if r.returncode == 0 else "error"),
                self._ts_refresh()
            ))
        threading.Thread(target=run, daemon=True).start()

    def _ts_disconnect(self):
        exe = find_tailscale()
        if not exe:
            self.log("Tailscale not found.", "error"); return
        self.log("Disconnecting Tailscale (LAN will be restored)...", "dim")
        def run():
            r = subprocess.run([exe, "down"], capture_output=True, **ENC, **_NO_WIN)
            self.after(0, lambda: (
                self.log("Tailscale disconnected. LAN access restored." if r.returncode == 0
                         else f"Error: {r.stderr.strip()}", "ok" if r.returncode == 0 else "error"),
                self._ts_refresh()
            ))
        threading.Thread(target=run, daemon=True).start()

    def _ts_login(self):
        exe = find_tailscale()
        if not exe: return
        if OS == "Windows":
            gui = Path(r"C:\Program Files\Tailscale\Tailscale.exe")
        else:
            gui = Path("/Applications/Tailscale.app")
        if gui.exists():
            subprocess.Popen([str(gui)], **_NO_WIN) if OS == "Windows" \
                else subprocess.Popen(["open", str(gui)])
            self.log("Tailscale app opened — click Log In.", "warn")
        else:
            subprocess.Popen([exe, "up"], **_NO_WIN)
        self.after(5000, self._ts_refresh)

    # ── Tool checker ───────────────────────────────────────────────────────────

    def _check_tools(self):
        for name, info in self.tool_rows.items():
            cmd = info["cmd"]
            found = shutil.which(cmd)
            if found:
                try:
                    r = subprocess.run([cmd, "--version"], capture_output=True,
                                       text=True, timeout=5)
                    ver = (r.stdout or r.stderr).strip().splitlines()[0][:30]
                except Exception:
                    ver = "installed"
                info["dot"].configure(text_color=C_GREEN)
                info["stat"].configure(text=ver, text_color=C_GREEN)
                info["btn"].pack_forget()
            else:
                info["dot"].configure(text_color=C_RED)
                info["stat"].configure(text="Not found", text_color=C_RED)
                info["btn"].pack(side="right")

    def _install_tool(self, url: str, npm_cmd: str | None):
        if npm_cmd and shutil.which("npm"):
            self.log(f"Running: {npm_cmd}", "dim")
            import threading
            def run():
                r = subprocess.run(npm_cmd.split(), capture_output=True,
                                   text=True, encoding="utf-8", errors="replace")
                self.after(0, lambda: (
                    self.log(r.stdout.strip() or r.stderr.strip(), "ok" if r.returncode == 0 else "error"),
                    self._check_tools()
                ))
            threading.Thread(target=run, daemon=True).start()
        else:
            webbrowser.open(url)
            self.log(f"Opened: {url}", "dim")

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
        self.update()
        ok, msg = test_connection(url, key)
        if ok:
            self.test_lbl.configure(text=f"✓ {msg[:60]}", text_color=C_GREEN)
            self.log(f"Connection OK — {msg}", C_GREEN)
        else:
            self.test_lbl.configure(text=f"✗ Failed", text_color=C_RED)
            self.log(f"Connection failed: {msg}", C_RED)

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
    app.geometry("560x640")
    app.mainloop()
