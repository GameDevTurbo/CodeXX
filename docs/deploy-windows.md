# Windows 部署指南

## 一键部署（推荐）

双击项目目录中的 **`start.bat`**，打开图形管理界面，点击 **"Deploy (first time)"** 完成首次部署。

---

## 手动部署

### 前置条件

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 已安装并运行
- [Tailscale](https://tailscale.com/download)（可选，组网共享时需要）
- 本机有代理软件（访问 ChatGPT/Claude 上游必须）

### 1. 创建目录

```powershell
mkdir auths, logs, plugins
```

### 2. 配置文件

**config.yaml** 需修改：
- `access.api-keys` — 生成密钥：`openssl rand -hex 16` 加 `sk-` 前缀
- `remote-management.secret-key` — 管理面板密码

**docker-compose.yml** 端口按需调整：
- 仅本机用 `127.0.0.1:8317:8317`
- Tailscale 远程共享用 `0.0.0.0:8317:8317`

### 3. 配置 Docker Desktop 代理（必须）

容器访问 ChatGPT/Claude 上游必须走本机代理，但容器内无法直接访问 `127.0.0.1`，需要通过 Docker Desktop 统一转发。

**Docker Desktop → Settings → Resources → Proxies：**

- 勾选 **Manual proxy configuration**
- HTTP Proxy：`http://127.0.0.1:7890`（替换为你的代理端口）
- HTTPS Proxy：`http://127.0.0.1:7890`
- Bypass：`localhost,127.0.0.1`
- 点击 **Apply & Restart**

> 跳过此步服务会启动成功，但调用模型时报 `connection refused`，耗时约 20 秒后失败。

### 4. 启动

```powershell
# 首次（需联网拉取镜像）
docker compose pull && docker compose up -d

# 离线/已有镜像
docker compose up -d --pull never
```

### 5. 验证

```powershell
docker compose ps
curl http://127.0.0.1:8317/v1/models -H "Authorization: Bearer sk-你的密钥"
```

返回模型列表即成功。管理面板：http://localhost:8317/management.html

## 常用命令

```powershell
docker compose down                              # 停止
docker compose restart                           # 重启（改配置后）
docker compose logs -f                           # 实时日志
docker compose pull && docker compose up -d      # 更新镜像
```

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `failed to connect to docker API` | Docker Desktop 未运行 | 打开 Docker Desktop，等图标稳定 |
| 调用模型返回 500，耗时 20s | 容器无法访问上游 | 配置 Docker Desktop 代理（见步骤 3） |
| `port is already allocated` | 端口冲突 | 修改 `docker-compose.yml` 端口 |
| 拉取镜像失败 | 网络问题 | 改用 `--pull never` 用本地镜像，或配置镜像加速 |
