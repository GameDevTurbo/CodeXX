# CLIProxyAPI Server

将 ChatGPT Plus / Claude Pro 等 AI 订阅转为标准 OpenAI API，供多设备共享。

> ⚠️ 违反各平台服务条款，仅供个人学习研究。

---

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
