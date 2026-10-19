# CLIProxyAPI 私有部署

将 ChatGPT Plus/Pro、Claude Pro、Gemini Advanced 等 AI 订阅转化为标准 OpenAI 兼容 API，供本地工具和客户端统一调用。

> 上游项目：https://github.com/router-for-me/CLIProxyAPI

## 风险声明

**使用前务必了解以下风险，本项目仅供学习研究。**

此工具通过各平台 CLI 的 OAuth 通道将订阅产品“伪装”为 API 调用，**违反 OpenAI、Anthropic、Google 等平台的服务条款**。

| 行为 | 风险等级 | 后果 |
|------|---------|------|
| 个人低频使用 | 中 | 账号可能被限制或封禁 |
| 多人共享使用 | 高 | 高频多 IP 调用极易触发风控 |
| 对外转售/运营 | 极高 | 封号 + 可能面临法律追责 |

- OAuth 令牌以文件形式存储在 `auths/` 目录，**泄露等于账号被盗**
- 端口绑定 `0.0.0.0` 且无防火墙时，局域网/公网均可访问

## 信息速查

| 项目 | 値 |
|------|-----|
| API 地址 | `http://127.0.0.1:8317/v1` |
| 管理面板 | `http://localhost:8317/management.html` |
| 默认端口 | 8317 |
| 配置文件 | `config.yaml` |
| 凭证目录 | `auths/`（勿手动修改，勿泄露） |

## 快速开始（Windows）

### 方式一：图形界面（推荐）

双击 `start.bat` 打开图形管理界面，点击 **Deploy (first time)** 完成首次部署。

### 方式二：命令行

```bash
mkdir auths logs plugins
docker compose pull && docker compose up -d
```

管理面板：http://localhost:8317/management.html

> **重要**：容器需要通过本机代理访问 ChatGPT/Claude 上游。必须在 Docker Desktop → Settings → Proxies 中配置代理，否则模型调用将返回 500 错误。详见 [Windows 部署指南](docs/deploy-windows.md)。

## 必备工具

| 工具 | 用途 | 获取方式 |
|------|------|----------|
| Docker Desktop | 容器运行环境 | https://www.docker.com/products/docker-desktop/ |
| Tailscale | 安全组网共享（可选） | https://tailscale.com/download |
| cc-switch | Codex CLI 配置切换（可选） | https://github.com/farion1231/cc-switch/releases |

## 文档索引

| 文档 | 内容 |
|------|------|
| [Windows 部署](docs/deploy-windows.md) | Docker Desktop 环境部署 + 代理配置 |
| [macOS 部署](docs/deploy-mac.md) | Docker 或原生编译部署 |
| [Linux 云服务器部署](docs/deploy-linux-server.md) | Docker / systemd / 反向代理 / 防火墙 |
| [使用指南](docs/usage-guide.md) | 添加账号、cc-switch、Tailscale 共享 |

## 项目文件

```
├── config.yaml          # 主配置（API Key、路由策略、管理面板密码）
├── docker-compose.yml   # Docker 编排（端口、卷挂载、代理环境变量）
├── .env.example         # 环境变量模板（高级存储选项）
├── start.bat            # Windows 双击启动器
├── launcher.ps1         # Windows GUI 管理工具
├── auths/               # OAuth 凭证（自动生成）
├── logs/                # 运行日志
├── plugins/             # 插件
└── docs/                # 部署与使用文档
```
