# macOS 使用指南

## 部署服务（服务端）

**前置**
- [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)

**步骤**

1. 克隆或下载本项目
2. 在项目目录运行：

```bash
bash start.sh
```

3. 弹出图形界面后步骤与 Windows 相同：
   点 **[Start Docker]** → **[Setup]** → **[Generate and Deploy]**

或纯命令行方式：

```bash
bash scripts/deploy.sh
```

管理面板：http://localhost:8317/management.html

---

## 使用服务（客户端）

```bash
python3 client.py
```

操作同 Windows 客户端部分。

---

## 常见问题

| 问题 | 解决 |
|------|------|
| Python 未找到 | `brew install python3` 或从 python.org 安装 |
| Docker 未运行 | 打开 Docker Desktop 等待就绪 |
| cc-switch 返回 404 | 协议改为 **OpenAI Responses** |
| 容器无法访问上游 | 本地代理配置同 Windows Docker Proxies 步骤 |
