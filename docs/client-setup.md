# 客户端接入指南

收到管理员提供的配置文件或 API 地址后，在这台电脑运行 `client.py` 即可完成全部配置。

## 快速开始

```bash
# Windows
双击 start.bat，然后点左侧菜单或直接运行：
python client.py

# macOS / Linux
bash start.sh
```

## 界面功能

### 连接配置

| 操作 | 说明 |
|------|------|
| [Import .cliproxy file] | 导入管理员导出的配置文件，自动填入 URL 和 Key |
| 手动填写 | 直接填入 API 地址和 Key |
| [Test Connection] | 验证连接，显示可用模型数量 |

### Tailscale 管理

| 状态 | 按钮 | 说明 |
|------|------|------|
| 已连接 | [Disconnect (keep LAN)] | 断开 Tailscale，局域网立即恢复 |
| 已断开 | [Connect] | 重新连接 Tailscale |
| 未登录 | [Login] | 打开 Tailscale 应用程序完成授权 |
| 未安装 | [Download] | 打开下载页 |

### 工具检测

自动检测常用 AI 工具是否已安装：

| 工具 | 安装命令 |
|------|------|
| Claude Code | `npm install -g @anthropic-ai/claude-code` |
| Codex CLI | `npm install -g @openai/codex` |
| cc-switch | 下载页 github.com/farion1231/cc-switch/releases |
| Node.js | 下载页 nodejs.org |

点击 [Install] 按鈕可直接安装（需要 npm）或跳转到下载页。

### 配置本地工具

| 按鈕 | 配置内容 |
|------|------|
| [Configure Claude Code] | 写入 `~/.claude/settings.json` 设置 ANTHROPIC_BASE_URL |
| [Configure cc-switch] | 添加 `cliproxy` Provider 到 `~/.codex/config.toml` |
| [Set Env Vars] | 设置 OPENAI_BASE_URL / ANTHROPIC_BASE_URL 等环境变量 |
| [All at once] | 一键配置以上所有 |

> cc-switch 协议必须选 **OpenAI Responses**，不是 Chat Completions。

## 常见问题

| 现象 | 解决 |
|------|------|
| 连接超时 | 确认 Tailscale 已连接，并与服务器处于同一网络 |
| 401 错误 | API Key 不匹配，联系管理员 |
| cc-switch 对话失败 404 | 协议选错，必须用 **OpenAI Responses** |
| Tailscale 导致局域网断连 | 在面板点 [Disconnect (keep LAN)] |
