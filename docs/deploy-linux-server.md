# Linux 云服务器部署指南

适用于 Ubuntu 20.04+、Debian 11+、CentOS Stream 9+。

## 方案一：一键部署脚本（推荐）

```bash
# 本地脚本（完整版，自动生成密钥和配置）
bash scripts/deploy.sh
# 可选参数: --dir ~/myproxy --port 8317 --expose

# 或使用社区远程脚本
curl -fsSL https://raw.githubusercontent.com/brokechubb/cliproxyapi-installer/refs/heads/master/cliproxyapi-installer | bash
```

## 方案二：Docker 部署（推荐）

```bash
# 安装 Docker（如未安装）
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker

# 部署
mkdir -p ~/cliproxyapi && cd ~/cliproxyapi
mkdir -p auths logs plugins
# 创建 config.yaml 和 docker-compose.yml（参考项目根目录文件，修改密钥和密码）
# 云服务器 docker-compose.yml 端口建议用 "8317:8317"（不限制 127.0.0.1，通过防火墙控制）
docker compose pull && docker compose up -d
```

## 方案三：原生编译 + systemd

```bash
# 编译
sudo apt update && sudo apt install -y golang-go   # 或手动安装 Go >= 1.22
git clone https://github.com/router-for-me/CLIProxyAPI.git
cd CLIProxyAPI && go build -o cli-proxy-api .
sudo mv cli-proxy-api /usr/local/bin/

# 配置
sudo mkdir -p /opt/cliproxyapi
# 将 config.yaml 放入 /opt/cliproxyapi/
```

创建 `/etc/systemd/system/cliproxyapi.service`：

```ini
[Unit]
Description=CLIProxyAPI
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/cliproxyapi
ExecStart=/usr/local/bin/cli-proxy-api
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now cliproxyapi
sudo journalctl -u cliproxyapi -f   # 查看日志
```

## 防火墙

```bash
# UFW (Ubuntu)
sudo ufw allow 8317/tcp && sudo ufw reload

# firewalld (CentOS)
sudo firewall-cmd --permanent --add-port=8317/tcp && sudo firewall-cmd --reload
```

> 同时检查云服务商的安全组是否放行了 8317 入站规则。

## HTTPS 反向代理（可选）

使用 Caddy 自动签发证书：

```bash
sudo apt install -y caddy
```

`/etc/caddy/Caddyfile`：

```
api.yourdomain.com {
    reverse_proxy 127.0.0.1:8317
}
```

```bash
sudo systemctl restart caddy
```

## 常见问题

| 问题 | 解决 |
|------|------|
| 拉取镜像慢 | `/etc/docker/daemon.json` 加 `"registry-mirrors": ["https://mirror.ccs.tencentyun.com"]`，重启 Docker |
| 容器运行但 API 不通 | 检查防火墙 + 云安全组入站规则 |
