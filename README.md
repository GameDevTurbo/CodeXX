# CLIProxyAPI 私有部署

将 ChatGPT Plus/Pro、Claude Pro、Gemini Advanced 等 AI 订阅转化为标准 OpenAI 兼容 API，供本地工具和客户端统一调用。

> 上游项目：https://github.com/router-for-me/CLIProxyAPI

## 风险声明

**使用前务必了解以下风险，本项目仅供学习研究。**

### 封号风险（最核心）

此工具通过各平台 CLI 的 OAuth 通道将订阅产品"伪装"为 API 调用，**违反 OpenAI、Anthropic、Google 等平台的服务条款**。

| 行为 | 风险等级 | 后果 |
|------|---------|------|
| 个人低频使用 | 中 | 账号可能被限制或封禁，订阅费不退 |
| 多人共享使用 | 高 | 高频多 IP 调用极易触发风控，封号概率大幅上升 |
| 对外转售/运营 | 极高 | 封号 + 可能面临法律追责 |

### 凭证安全风险

- OAuth 令牌以文件形式存储在 `auths/` 目录，**泄露等于账号被盗**
- 端口绑定 `0.0.0.0` 且无防火墙时，局域网/公网均可访问
- Docker 镜像为预编译产物，无法保证与开源代码完全一致

### 数据隐私风险

- 所有 AI 对话内容经过此代理中转，理论上可被记录或篡改
- 共享使用时，服务部署方可看到所有用户的请求日志

### 稳定性风险

- 依赖各平台 CLI OAuth 机制，平台随时可更改导致失效
- 无 SLA 保障，不适合生产环境
- 账号配额用尽后无法自动续费

### 合规风险

- 对外提供 AI API 服务涉及未授权转售
- 国内运营需考虑 AI 服务备案等监管要求

## 信息速查

| 项目 | 值 |
|------|-----|
| API 地址 | `http://127.0.0.1:8317/v1` |
| 管理面板 | `http://localhost:8317/management.html` |
| 默认端口 | 8317 |
| 配置文件 | `config.yaml` |
| 凭证目录 | `auths/`（勿手动修改，勿泄露） |

## 必备工具

| 工具 | 用途 | 获取方式 |
|------|------|----------|
| Docker Desktop | 容器运行环境（Windows/macOS） | https://www.docker.com/products/docker-desktop/ |
| Docker + Compose | 容器运行环境（Linux） | `curl -fsSL https://get.docker.com \| sh` |
| Git Bash / OpenSSL | 生成随机密钥 | Windows 随 Git 安装；macOS/Linux 自带 |
| Tailscale | 安全组网共享（可选） | https://tailscale.com/download |
| cc-switch | Claude Code / Codex 配置切换（可选） | https://github.com/farion1231/cc-switch/releases |
| Go >= 1.22 | 原生编译（可选，不用 Docker 时） | https://go.dev/dl/ |

## 快速开始

```bash
mkdir -p auths logs plugins          # 1. 创建目录
# 2. 编辑 config.yaml 和 docker-compose.yml（见项目根目录文件）
docker compose pull && docker compose up -d   # 3. 启动
# 4. 浏览器打开 http://localhost:8317/management.html 添加账号
```

## 文档索引

| 文档 | 内容 |
|------|------|
| [Windows 部署](docs/deploy-windows.md) | Docker Desktop 环境部署 |
| [macOS 部署](docs/deploy-mac.md) | Docker 或原生编译部署 |
| [Linux 云服务器部署](docs/deploy-linux-server.md) | Docker / systemd / 反向代理 / 防火墙 |
| [使用指南](docs/usage-guide.md) | 添加账号、客户端对接、cc-switch、Tailscale 共享 |

## 项目文件

```
├── config.yaml          # 主配置（API Key、路由策略、管理面板密码）
├── docker-compose.yml   # Docker 编排（端口、卷挂载）
├── .env.example         # 环境变量模板（高级存储选项）
├── auths/               # OAuth 凭证（自动生成）
├── logs/                # 运行日志
├── plugins/             # 插件
└── docs/                # 部署与使用文档
```
