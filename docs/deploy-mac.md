# macOS 部署指南

## 一键部署（推荐）

```bash
bash scripts/deploy.sh
```

脚本会自动检查 Docker、生成密钥、创建配置、启动服务。如需手动部署，继续阅读下方步骤。

---

## 手动部署

### 前置条件

- [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)（方案一）
- 或 Go >= 1.22：`brew install go`（方案二）

## 方案一：Docker 部署（推荐）

```bash
mkdir -p ~/CLIProxyAPI && cd ~/CLIProxyAPI
mkdir -p auths logs plugins
# 创建 config.yaml 和 docker-compose.yml（参考项目根目录文件，修改密钥和密码）
docker compose pull && docker compose up -d
```

验证：

```bash
curl -s http://127.0.0.1:8317/v1/models -H "Authorization: Bearer sk-你的密钥"
```

## 方案二：原生编译

```bash
git clone https://github.com/router-for-me/CLIProxyAPI.git
cd CLIProxyAPI
go build -o cli-proxy-api .
cp config.example.yaml config.yaml
# 编辑 config.yaml
./cli-proxy-api
```

### launchd 开机自启（可选）

创建 `~/Library/LaunchAgents/com.cliproxyapi.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cliproxyapi</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/你的用户名/CLIProxyAPI/cli-proxy-api</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/你的用户名/CLIProxyAPI</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/你的用户名/CLIProxyAPI/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/你的用户名/CLIProxyAPI/logs/stderr.log</string>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.cliproxyapi.plist     # 启动
launchctl unload ~/Library/LaunchAgents/com.cliproxyapi.plist   # 停止
```
