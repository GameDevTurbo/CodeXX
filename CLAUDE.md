# CLIProxyAPI Server — Agent 开发指南

> 本文件供 AI 编程助手（Claude Code / Codex）读取，用于快速理解项目状态和继续迭代。

---

## 项目概述

CLIProxyAPI Server：将 ChatGPT Plus / Claude Pro 等 AI 订阅转为标准 OpenAI 兼容 API。
部署在本地或云服务器，通过 Tailscale 安全共享给多台设备。

**配套仓库：** [CodeXX-Client](https://github.com/GameDevTurbo/CodeXX-Client) — 使用端工具

---

## 文件结构

```
CLIProxyAPI-Server.exe  # Windows 预编译（Git LFS，18MB）
Server.bat              # Windows：双击启动（优先用.exe，否则bootstrap）
Server.command          # macOS：双击启动（首次右键→打开）
start.sh               # Linux/macOS CLI 启动
_bootstrap.ps1          # Windows Python 探测（PATH→安装目录→winget）
launcher.py             # 主程序 GUI（Python + customtkinter）
docker-compose.yml      # Docker 编排（端口8317/8085，卷挂载）
prepare_offline.bat/sh  # 预下载离线依赖（Docker镜像+Python+wheels）
.github/workflows/build.yml  # CI：push tag v* 触发三平台构建
docs/windows.md         # Windows 部署+使用指南
docs/macos.md           # macOS 指南
docs/linux.md           # Linux 云服务器指南
```

---

## launcher.py 架构

### 4步向导 UI

```
Step 1: Docker Desktop  → [Start Docker] 按钮，自动轮询就绪
Step 2: Configuration   → [Setup] 打开向导，自动生成 config.yaml
Step 3: Service         → [Deploy/Start/Stop/Restart]
Step ★: Tailscale       → [Install/Login/Connect/Disconnect]
Connection Info Card    → 服务就绪后显示 IP、API Key、管理密码、[Export .cliproxy]
```

### 关键方法

| 方法 | 功能 |
|------|------|
| `docker_running()` | 检测 Docker Desktop，捕获 TimeoutExpired |
| `service_status()` | 检测容器状态（running/exited/etc） |
| `run_compose(args, log_fn)` | 流式运行 docker compose，输出到 log |
| `tailscale_status()` | 检测 Tailscale 状态 |
| `_refresh()` | 非阻塞后台刷新，`self.after(0, ...)` 更新 UI |
| `_generate_and_deploy()` | 生成 config.yaml + API Key + 管理密码，写 .credentials.json |
| `_show_connect_info()` | 后台获取IP/Key/密码，渲染连接信息卡片 |

### config.yaml 生成

首次 [Setup] → 生成 `config.yaml`（含随机 API Key + 密码）→ 保存到 `.credentials.json`（本地，gitignored）→ 启动服务 → 打开管理面板

---

## 已知问题 & 待完成

### 🔴 高优先级

1. **launcher.py 字体未调整**
   - client.py 已做字体放大，launcher.py 还未做
   - 修复：`re.sub(r'size=(\d+)', scale_fn, text)` 同 client.py 方式

2. **Server exe 未重建**
   - 上次字体/功能改动后没有重建 `CLIProxyAPI-Server.exe`
   - 重建命令：
     ```
     python -m PyInstaller --onefile --windowed --name CLIProxyAPI-Server launcher.py
     copy dist\CLIProxyAPI-Server.exe CLIProxyAPI-Server.exe
     git add CLIProxyAPI-Server.exe && git commit && git push
     ```

3. **Mac 兼容性未测试**
   - `Server.command` 需 `chmod +x` 才能双击
   - Docker Desktop for Mac 路径与 Windows 不同
   - `start_docker_desktop()` 里 macOS 分支用 `open -a Docker`（已实现）

### 🟡 中优先级

4. **`.gitignore` 需更新**
   - 需加入 PyInstaller artifacts：`dist/ build/ *.spec`
   - 当前已有 `build/`, `dist/`, `*.spec`（由清理 agent 添加，已生效）

5. **`prepare_offline.bat` Docker 镜像步骤**
   - 如果 Docker 未运行会跳过，需要提示用户先启动 Docker

6. **Tailscale NoState / starting 问题**
   - 服务端 Tailscale 有时卡在 NoState
   - 原因：Docker Desktop 重启后破坏网络路由
   - 临时解法：重启 Tailscale 服务后运行 `tailscale up`

### 🟢 已解决

- ✅ Docker 检测非阻塞（TimeoutExpired 捕获）
- ✅ 所有 subprocess 后台线程，UI 不冻结
- ✅ Connection Info 卡片展示所有凭证
- ✅ Export .cliproxy 文件给使用端
- ✅ Docker Desktop 代理配置（Settings → Proxies → Manual）
- ✅ `_NO_WIN` 跨平台处理
- ✅ 日志颜色和时间戳

---

## 开发工作流

```bash
cd E:\TestCodeX\CodeXX

# 语法检查
python -m py_compile launcher.py

# 启动 GUI 测试
python launcher.py

# 重建 exe
python -m PyInstaller --onefile --windowed --name CLIProxyAPI-Server launcher.py
copy dist\CLIProxyAPI-Server.exe CLIProxyAPI-Server.exe

# 启动/停止服务
docker compose up -d --pull never
docker compose down

# 验证 API
curl -s http://localhost:8317/v1/models -H "Authorization: Bearer sk-e181d637cc511d0ae93355fed01febbc"

# 触发 CI 三平台构建
git tag v1.x.x && git push origin v1.x.x
```

---

## 配置文件说明

### config.yaml（gitignored）
```yaml
config-version: 8
host: "0.0.0.0"
port: 8317
access:
  api-keys: ["sk-xxx", "sk-yyy"]  # 自动生成
oauth:
  auth-dir: "/root/.cli-proxy-api"
routing:
  strategy: "round-robin"
remote-management:
  allow-remote: true
  secret-key: "原始密码"  # 首次登录后自动 bcrypt 哈希化
```

### docker-compose.yml
- 端口：`0.0.0.0:8317:8317`（API），`127.0.0.1:8085:8085`（管理）
- 卷：`./config.yaml`, `./auths/`, `./logs/`, `./plugins/`
- 代理：通过 Docker Desktop Settings → Proxies 全局配置（不在 compose 里设置）

---

## 环境信息

- **OS**: Windows 11 Pro 10.0.22631
- **Python**: `C:\Users\GameDevTurbo\AppData\Local\Programs\Python\Python312\python.exe`
- **Tailscale IP**: 100.95.33.74 (MingWin)
- **API Key（测试用）**: sk-e181d637cc511d0ae93355fed01febbc
- **管理面板**: http://localhost:8317/management.html
- **GitHub**: GameDevTurbo/CodeXX

---

## 下一步建议

1. **launcher.py 字体放大**（对标 client.py 的改动）
2. **重建 CLIProxyAPI-Server.exe**
3. **Mac 实机测试**：`bash start.sh`，验证 Docker 检测和 Tailscale 流程
4. **推 tag v1.2.0** 触发 CI 构建三平台正式包
5. **文档更新**：Server 端 docs/ 确认与实际流程一致
