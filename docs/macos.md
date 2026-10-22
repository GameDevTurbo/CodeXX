# macOS Server（Apple Silicon）

本次测试目标是 Apple Silicon（M1/M2/M3/M4 等 arm64）。请下载并使用 `macOS-arm64` 包，不要使用 `macOS-x64` 包。可以在“关于本机”中确认芯片，也可以在终端运行 `uname -m`：Apple Silicon 应显示 `arm64`。

发布包的推荐流程：

1. 下载 `CLIProxyAPI-Server-macOS-arm64.zip`，解压到用户有权限的目录。
2. 确认 Docker Desktop 也是 Apple Silicon 版本，并启动 Docker Desktop。
3. 首次打开 `CLIProxyAPI-Server.app`。如果 macOS 提示开发者无法验证，先确认压缩包来源和校验值，再按组织允许的方式在“系统设置 → 隐私与安全性”中批准；不要为了绕过提示而关闭系统安全策略。
4. 在 Server 界面完成初始化和部署；初始化不会覆盖已有配置，也不会重置 API Key 或上游认证。
5. 如果使用 Tailscale，先安装 macOS 版并完成账号登录、网络扩展和防火墙相关授权，再在 Server 中确认检测到 Tailscale 地址。

预编译包不需要 Python，但仍需要 Docker Desktop；Server 本身不替代 Docker。Apple Silicon 上若 Docker 使用了 x86/amd64 模拟镜像，可能出现启动慢、资源占用高或兼容性问题，应优先使用上游提供的多架构镜像。

App 尚无 Apple 开发者签名、公证。遇到系统或组织的安装限制，使用获准的软件安装流程；不会自动关闭安全策略。Tailscale 网络扩展许可及账号登录由用户确认。

源码可运行 bash Server.command，需含 Python 3.10+；打开 GUI 还需要 tkinter/customtkinter。依赖在项目 .venv 中，不向 Homebrew 的全局 Python 强行安装。

无桌面或只做只读检查时，可直接运行 `python3 launcher.py --doctor --report doctor.json`，不需要 Tk 显示会话；`--init` 和 `--harden-runtime` 同样只操作指定数据目录，不会自动启动或重启容器。路径包含空格时请给 `--data-dir` 和报告路径加引号。

新发布版数据默认 ~/Library/Application Support/CodeXX/Server，不写 App 内部；旧根目录 config.yaml 保持兼容。使用路径带空格的数据目录时务必加引号。

长期运行注意事项：

- 关闭 Server 管理窗口不会停止 Docker 容器；这是预期行为，容器由 Docker Desktop 按 `restart: unless-stopped` 管理。
- 新初始化的 Compose 默认包含 CPU、内存、进程数上限、优雅停止和 Docker 日志轮转；这些限制用于防止长期挂机时失控，但仍应结合并发量观察 Docker Desktop 的资源使用。
- 不要用 GUI 的“停止服务”测试关闭 Server 窗口的效果；前者会停止容器，后者只关闭管理界面。
- macOS 睡眠、网络切换、Tailscale 重连和 Docker Desktop 更新都可能暂时中断服务；恢复后应依次检查 Docker、容器状态、Tailscale 和 `/v1/models`。
- 不要把 `~/Library/Application Support/CodeXX/Server` 下的 `config.yaml`、`.credentials.json`、`auths/` 或导出的 `.cliproxy` 上传到工单、聊天或 Git。

首次验收建议按层进行：

1. Server 界面显示 Docker 正常。
2. 配置和 Compose 已生成，且数据目录位于上面的 Application Support 路径。
3. 容器状态为 running。
4. 管理页可以打开并完成你授权的上游账号登录。
5. `/v1/models` 能通过 API Key 返回模型列表。
6. 再用客户端验证一次实际请求。模型列表成功不等于具体模型生成、账号路由或额度已经验证。

Apple Silicon 专项检查：

```bash
uname -m
docker version
docker compose version
docker inspect cli-proxy-api --format '{{.Architecture}} {{.State.Status}}'
```

第一条应为 `arm64`；后两条应能正常返回版本；最后一条用于确认容器状态和架构。若 Docker Desktop 已启用 Rosetta 或 amd64 模拟，不要把模拟运行结果当作原生 arm64 性能结论。

诊断 CLI：./CLIProxyAPI-Server.app/Contents/MacOS/CLIProxyAPI-Server --doctor --report doctor.json

本轮在 Windows 做实现与回归；Mac 已提供原生 App 构建、arm64/x64 双架构 CI 和静态入口检查。Apple Silicon 的 Finder、Tk、Docker Desktop、Tailscale 网络扩展、睡眠恢复和长期运行仍需在真实 Mac 上验收；本地 Windows 检查不能替代签名、公证和实机网络测试。
