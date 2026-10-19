# CLIProxyAPI 项目说明

本项目将 ChatGPT Plus/Pro、Claude Pro 等 AI 订阅封装为标准 OpenAI 兴容 API，供多设备共享。

## 架构总览

- 服务端口: 8317（API + 管理面板）
- 容器: `cli-proxy-api`，镜像 eceasy/cli-proxy-api:latest
- 路由: round-robin，限流时自动切换备用账号
- 远程: Tailscale 组网共享

## 关键文件

| 文件 | 用途 |
|------|------|
| `config.yaml` | 主配置: API Key列表、路由策略、管理面板密码 |
| `docker-compose.yml` | Docker编排: 端口、卷挂载、代理环境变量 |
| `start.bat` | Windows双击启动器 |
| `launcher.ps1` | Windows GUI管理工具(启动/停止/重启/日志) |
| `auths/` | OAuth凭证(自动生成，不提交、不共享) |

## 常用命令

```bash
# 启动（已有本地镜像）
docker compose up -d --pull never
# 启动（拉取最新）
docker compose pull && docker compose up -d
# 停止/重启
docker compose down
docker compose restart
# 容器状态
docker ps --filter name=cli-proxy-api
# API健康检查
curl -s http://127.0.0.1:8317/v1/models -H 'Authorization: Bearer YOUR_KEY'
# 对话测试
curl -s -X POST http://127.0.0.1:8317/v1/chat/completions \n  -H 'Authorization: Bearer YOUR_KEY' \n  -H 'Content-Type: application/json' \n  -d '{"model":"gpt-6-sol","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
# Tailscale IP
tailscale ip -4
```

## 首次部署检查清单

1. **Docker Desktop已运行**: `docker info` 无报错
2. **`config.yaml`已创建**: 参考 `.env.example` 和 `docs/deploy-windows.md`
3. **Docker Desktop代理已配置**: Settings → Proxies → Manual → `http://127.0.0.1:代理端口`
4. **目录已创建**: `auths/ logs/ plugins/`

## 常见故障

| 现象 | 原因 | 解决 |
|------|------|------|
| `failed to connect to docker API` | Docker Desktop未运行 | 打开 Docker Desktop |
| 模型调用500返回，耗时20s | 容器无法访问上游 | Docker Desktop Proxies配置代理 |
| 拉取镜像失败 | 网络问题 | 改用 `--pull never` 用已有本地镜像 |
| 401 Unauthorized | API Key错误 | 检查 `config.yaml` `access.api-keys` |
| cc-switch对话失败 | 协议选错 | 协议必须选 **OpenAI Responses**，不是 Chat |

## config.yaml 关键字段

```yaml
access:
  api-keys:
    - 'sk-xxx'  # 建议每个设备分配独立 Key

routing:
  strategy: 'round-robin'

remote-management:
  secret-key: '管理面板密码'
```

新增 Key: `openssl rand -hex 16` 加 sk- 前缀，写入 config.yaml。配置热重载，无需重启容器。

## 相关文档

- [Windows 部署指南](docs/deploy-windows.md)
- [macOS 部署指南](docs/deploy-mac.md)
- [Linux 部署指南](docs/deploy-linux-server.md)
- [使用指南](docs/usage-guide.md)
