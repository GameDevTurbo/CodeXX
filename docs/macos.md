# macOS Server

下载与你的芯片匹配的 macOS-arm64（Apple Silicon）或 macOS-x64（Intel）包，打开 CLIProxyAPI-Server.app；预编译包不需要 Python。Docker Desktop 同样要与芯片兼容。

App 尚无 Apple 开发者签名、公证。遇到系统或组织的安装限制，使用获准的软件安装流程；不会自动关闭安全策略。Tailscale 网络扩展许可及账号登录由用户确认。

源码可运行 bash Server.command，需含 Python 3.10+；打开 GUI 还需要 tkinter/customtkinter。依赖在项目 .venv 中，不向 Homebrew 的全局 Python 强行安装。

无桌面或只做只读检查时，可直接运行 `python3 launcher.py --doctor --report doctor.json`，不需要 Tk 显示会话；`--init` 和 `--harden-runtime` 同样只操作指定数据目录，不会自动启动或重启容器。路径包含空格时请给 `--data-dir` 和报告路径加引号。

新发布版数据默认 ~/Library/Application Support/CodeXX/Server，不写 App 内部；旧根目录 config.yaml 保持兼容。使用路径带空格的数据目录时务必加引号。

诊断 CLI：./CLIProxyAPI-Server.app/Contents/MacOS/CLIProxyAPI-Server --doctor --report doctor.json

本轮在 Windows 做实现与回归；Mac 已提供原生 App 构建、双架构 CI 和静态入口检查，但 Finder、Tk、Docker/Tailscale 网络及托盘需 Mac 真机继续验收。
