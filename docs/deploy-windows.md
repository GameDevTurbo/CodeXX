# Windows 部署指南

## 前置条件

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 已安装并运行
- [Tailscale](https://tailscale.com/download)（可选，组网共享时需要）

## 部署步骤

### 1. 创建项目目录

```powershell
mkdir C:\CLIProxyAPI
cd C:\CLIProxyAPI
mkdir auths, logs, plugins
```

### 2. 创建配置文件

将项目根目录的 `config.yaml` 和 `docker-compose.yml` 复制到此目录，修改以下字段：

**config.yaml** 中需要修改的：
- `access.api-keys` — 生成密钥：Git Bash 执行 `openssl rand -hex 16`，加 `sk-` 前缀
- `remote-management.secret-key` — 管理面板登录密码

**docker-compose.yml** 中按需修改的：
- 端口绑定 — 仅本机用 `127.0.0.1:8317:8317`，Tailscale 共享用 `0.0.0.0:8317:8317`

### 3. 启动

```powershell
docker compose pull
docker compose up -d
```

### 4. 验证

```powershell
docker compose ps                    # 容器状态
docker compose logs --tail 20        # 查看日志
curl http://127.0.0.1:8317/v1/models -H "Authorization: Bearer sk-你的密钥"
```

返回 `{"data":[...],"object":"list"}` 即成功。管理面板：http://localhost:8317/management.html

## 常用命令

```powershell
docker compose down                              # 停止
docker compose restart                           # 重启（改配置后）
docker compose logs -f                           # 实时日志
docker compose pull && docker compose up -d      # 更新版本
```

## 常见问题

| 问题 | 解决 |
|------|------|
| `failed to connect to docker API` | 重新打开 Docker Desktop，等状态变为 Running |
| `port is already allocated` | 改 `docker-compose.yml` 和 `config.yaml` 中的端口 |
| 拉取镜像慢 | Docker Desktop → Settings → Docker Engine 加 `"registry-mirrors": ["https://mirror.ccs.tencentyun.com"]` |
