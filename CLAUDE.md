# CLIProxyAPI 项目说明

将 ChatGPT Plus/Pro、Claude Pro 等 AI 订阅封装为标准 OpenAI API，供多设备共享。

## 架构

- 服务端口: 8317 （API + 管理面板）
- 容器: `cli-proxy-api`，镜像 eceasy/cli-proxy-api:latest
- 路由: round-robin，限流自动切换
- 远程共享: Tailscale 组网

## 工具

| 文件 | 用途 | 使用对象 |
|------|------|------|
| `launcher.py` | 部署端 GUI: 4步向导 + 连接信息 | 运行服务的机器 |
| `client.py` | 使用端 GUI: 导入配置 + Tailscale管理 + 工具检测 | 其他设备 |
| `start.bat` | Windows 双击入口 | 所有 Windows |
| `_bootstrap.ps1` | 自动找 Python，支持离线包 | 由 start.bat 调用 |
| `start.sh` | macOS/Linux 入口 | Mac/Linux |
| `prepare_offline.bat` | 预下载依赖包 | 有网时提前准备 |
| `config.yaml` | 主配置: API Key、路由、管理密码 | 服务端 |
| `docker-compose.yml` | Docker 编排 | 服务端 |

## 常用命令

```bash
# 启动
docker compose up -d --pull never
# 停止
docker compose down
# 容器状态
docker ps --filter name=cli-proxy-api
# API 健康
curl -s http://127.0.0.1:8317/v1/models -H 'Authorization: Bearer YOUR_KEY'
# Tailscale IP
tailscale ip -4
```

## 首次部署检查清单

1. Docker Desktop 已运行: `docker info` 无报错
2. `config.yaml` 已创建（启动器自动生成）
3. Docker Desktop 代理已配置: Settings → Proxies → Manual
4. 目录已创建: `auths/ logs/ plugins/` （启动器自动创建）

## 常见故障

| 现象 | 原因 | 解决 |
|------|------|------|
| docker API 报错 | Docker Desktop 未运行 | 启动器点 [Start Docker] |
| 模型调用 500，耗时20s | 容器无法访问上游 | Docker Desktop 配置代理 |
| cc-switch 返回 404 | 协议选错 | cc-switch 必须选 **OpenAI Responses** |
| Tailscale 导致局域网断 | DNS/路由冲突 | client.py 点 [Disconnect (keep LAN)] |

## 相关文档

- [Windows](docs/windows.md)
- [Linux 云服务器](docs/linux.md)
- [macOS](docs/macos.md)
