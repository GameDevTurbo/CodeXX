# CLIProxyAPI Server

将 ChatGPT Plus / Claude Pro 等 AI 订阅转为标准 OpenAI API，供多设备共享。

> ⚠️ 违反各平台服务条款，仅供个人学习研究。

1. **只想使用已有服务**：下载 [CodeXX-Client](https://github.com/GameDevTurbo/CodeXX-Client/releases)，不需要部署本项目。
2. **要运行服务**：从 [Releases](https://github.com/GameDevTurbo/CodeXX/releases) 下载匹配系统与 CPU 的 `-offline.zip` 完整包。Windows 打开 Server.bat；Mac 打开 CLIProxyAPI-Server.app。预编译包无需 Python；缺少 Docker 或 Tailscale 时，点击界面的安装按钮，优先打开包内安装程序。
3. 打开 Docker Desktop。首次 Setup 创建配置；已有配置不会被覆盖或重置密钥。新 GUI 部署优先绑定已识别的 Tailscale IP，否则仅本机；纯 CLI 初始化默认仅本机。
4. 在管理页登录你授权的上游账号。验证 API 列表和实际生成是两项不同验收。
5. 导出 .cliproxy 给其他设备的客户端。连接文件只含 API 凭据，不含管理密码；请通过可信渠道传递。

## 首次部署与人工操作

普通小包支持应用内自动下载官方安装程序；完整离线包包含 Mac/Windows 安装程序、对应架构服务镜像及管理页面。离线部署自动加载本地镜像，不重复拉取。Linux 需预装 Engine + Compose；调用上游 AI 和账号登录仍需网络。见[自动下载与离线准备](docs/offline.md)或[一页 HTML 指南](docs/deployment.html)。

先读[首次部署流程与常见故障](docs/first-run.md)：包括 Docker 管理员授权、钥匙串/目录访问提示、下载和代理问题，以及“容器运行但 API 不通”的检查。**v1.1.0 历史包与当前源码存在差异**，以下载包内文档为准；新版流程需重新构建发布后才会生效。

GUI 的“检查连接”会验证 API 鉴权并提示下一步；不会自动登录上游账号或消耗额度测试生成。初始化、容器启动、API 连通、实际生成是四个独立步骤。

## 快速开始

| 平台 | 操作 |
|------|------|
| Windows | 双击 Server.bat |
| macOS | 双击 Server.command（首次右键→打开） |
| Linux | bash start.sh |

> 无 Python 环境？从 [Releases](https://github.com/GameDevTurbo/CodeXX/releases) 下载可执行文件。

---

## 流程

1. Docker Desktop 就绪 → 自动检测，可一键启动
2. 首次部署 → 自动生成 API Key 和管理密码
3. 服务启动后 → 显示连接信息，点 [Export .cliproxy] 分享给使用方

使用方请前往：[CodeXX-Client](https://github.com/GameDevTurbo/CodeXX-Client)

---

## 平台指南

- [Windows](docs/windows.md)
- [macOS](docs/macos.md)
- [Linux 云服务器](docs/linux.md)
