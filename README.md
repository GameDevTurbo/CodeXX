# CLIProxyAPI Server

将 ChatGPT Plus / Claude Pro 等 AI 订阅转为标准 OpenAI API，供多设备共享。

> ⚠️ 违反各平台服务条款，仅供个人学习研究。

1. **只想使用已有服务**：下载 [CodeXX-Client](https://github.com/GameDevTurbo/CodeXX-Client/releases)，不需要部署本项目。
2. **要运行服务**：从 [Releases](https://github.com/GameDevTurbo/CodeXX/releases) 下载匹配系统与 CPU 的 Server 包。Windows 打开 CLIProxyAPI-Server.exe；Mac 打开 CLIProxyAPI-Server.app。预编译包无需 Python，Docker Desktop 和 Tailscale 需按需要安装。
3. 打开 Docker Desktop。首次 Setup 创建配置；已有配置不会被覆盖或重置密钥。新 GUI 部署优先绑定已识别的 Tailscale IP，否则仅本机；纯 CLI 初始化默认仅本机。
4. 在管理页登录你授权的上游账号。验证 API 列表和实际生成是两项不同验收。
5. 导出 .cliproxy 给其他设备的客户端。连接文件只含 API 凭据，不含管理密码；请通过可信渠道传递。

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
