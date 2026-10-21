# CLIProxyAPI

将 ChatGPT Plus / Claude Pro 等 AI 订阅转化为标准 OpenAI API，供多设备共享。

> 上游项目: https://github.com/router-for-me/CLIProxyAPI

---

## Windows 部署（一项式）

**前缀**：安装并启动 [Docker Desktop](https://www.docker.com/products/docker-desktop/)

1. 克隆本仓库

```bash
git clone https://github.com/GameDevTurbo/CodeXX.git
cd CodeXX
```

2. 双击 **`start.bat`**
3. 点击 **Setup and Deploy** — 自动生成密鑰、写入配置、拉取镜像、启动服务

> **重要**：如果容器连不上 ChatGPT/Claude，按照 [Windows 部署指南](docs/deploy-windows.md) 配置 Docker Desktop 代理。

---

## Linux / macOS 部署

```bash
git clone https://github.com/GameDevTurbo/CodeXX.git && cd CodeXX
bash scripts/deploy.sh --expose   # 美国服务器无需代理
```

---

## 快速查询

| 项目 | 地址 |
|------|------|
| API | `http://你的IP:8317/v1` |
| 管理面板 | `http://你的IP:8317/management.html` |
| Tailscale IP | `tailscale ip -4` |

---

## 风险声明

本项目通过 OAuth 通道使用订阅产品，**违反各平台服务条款**，存在封号风险。仅供个人学习研究。

---

## 文档

| 文档 | 内容 |
|------|------|
| [Windows 部署](docs/deploy-windows.md) | Docker Desktop + 代理配置 |
| [Linux 部署](docs/deploy-linux-server.md) | 云服务器部署 |
| [macOS 部署](docs/deploy-mac.md) | Mac 本地部署 |
| [使用指南](docs/usage-guide.md) | cc-switch、Tailscale共享 |
| [客户端接入](docs/client-setup.md) | 其他设备如何连接 |
