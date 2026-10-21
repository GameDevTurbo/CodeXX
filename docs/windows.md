# Windows 使用指南

## 部署服务（服务端）

**前置**
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- 本机代理软件（7890 或其他端口）

**步骤**

1. 克隆或下载本项目
2. 双击 `start.bat`
3. 点 **[Start Docker]** 等待 Docker 就绪
4. 点 **[Setup]** → 填代理端口（如 `7890`）→ **[Generate and Deploy]**
5. 界面显示 Connection Info，保存 API Key 和管理密码

> **Docker Desktop 代理配置（必须）**
> Settings → Proxies → Manual → HTTP/HTTPS 填 `http://127.0.0.1:代理端口` → Apply & Restart
>
> 跳过此步服务能启动，但调用模型时会报 500 错误。

管理面板：http://localhost:8317/management.html，登录后添加 ChatGPT / Claude 账号。

---

## 使用服务（客户端）

1. 双击 `start.bat` → 在启动器点 **[Open Client Tool]**
   或直接运行：`python client.py`
2. 点 **[Import .cliproxy file]** 导入服务端导出的配置文件
   或手动填写 API 地址和 Key
3. 点 **[Test Connection]** 验证
4. 点 **[All at once]** 一键配置 Claude Code + cc-switch + 环境变量

> cc-switch 协议必须选 **OpenAI Responses**（不是 Chat）

---

## 常见问题

| 问题 | 解决 |
|------|------|
| 模型调用返回 500 | Docker Desktop → Settings → Proxies 配置代理 |
| cc-switch 返回 404 | 协议改为 **OpenAI Responses** |
| Tailscale 导致局域网断 | client.py → **[Disconnect (keep LAN)]** |
| Docker 启动失败 | 在开始菜单打开 Docker Desktop，等图标稳定 |
