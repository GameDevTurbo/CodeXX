# 客户端接入指南

收到管理员提供的 API 地址和 Key 后，按以下步骤配置。

## 接入信息

| 项目 | 内容 |
|------|------|
| API 地址 | `http://管理员提供的IP:8317/v1` |
| API Key | 管理员分配的 `sk-xxx` |
| 内网方式 | 全员加入同一 Tailscale 网络 |

## cc-switch 配置（推荐）

[cc-switch](https://github.com/farion1231/cc-switch/releases) 是 Codex CLI 的配置切换工具。

### 新建 Provider

1. 打开 cc-switch → 点击 **Add Provider**
2. 填写以下信息：

| 字段 | 値 |
|------|-----|
| Name | 自定义名称，如 `home-proxy` |
| API Base URL | `http://管理员IP:8317/v1` |
| API Key | 管理员分配的 Key |
| Protocol / Wire API | **OpenAI Responses**（必须选这个，不是 Chat Completions） |
| Model | `gpt-6-sol` （或任意可用模型） |

3. 点击 **Save** → 手动切换到该 Provider
4. 发一条测试消息验证模型调用正常

### 可用模型

```bash
# 查看所有可用模型
curl -s http://管理员IP:8317/v1/models -H 'Authorization: Bearer YOUR_KEY'
```

主要模型：

| 模型 ID | 说明 |
|------|------|
| `gpt-6-sol` | ChatGPT 最新旗舰模型 |
| `gpt-6-luna` | 较快的高性能模型 |
| `gpt-5.6-sol` | 稳定版本 |

## 其他客户端

充API地址和 Key 即可接入。

### Claude Code

```bash
# 在终端执行，會连接到家裡服务
export ANTHROPIC_BASE_URL=http://管理员IP:8317/v1
export ANTHROPIC_API_KEY=YOUR_KEY
claude
```

### ChatBox / Cherry Studio / NextChat

1. 设置 → 自定义 OpenAI 兼容接口
2. 填写 API 地址 + Key
3. 模型手动填写 `gpt-6-sol` 或从列表选择

### 环境变量（通用）

```bash
export OPENAI_API_KEY=YOUR_KEY
export OPENAI_BASE_URL=http://管理员IP:8317/v1
```

## 快速测试

```bash
# 模型列表（返回 JSON 即连接成功）
curl -s http://管理员IP:8317/v1/models -H 'Authorization: Bearer YOUR_KEY'

# 对话测试（返回有内容即全链路正常）
curl -s -X POST http://管理员IP:8317/v1/chat/completions \n  -H 'Authorization: Bearer YOUR_KEY' \n  -H 'Content-Type: application/json' \n  -d '{"model":"gpt-6-sol","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
```

## 常见问题

| 现象 | 解决 |
|------|------|
| 连接超时 | 确认已加入 Tailscale 并与服务器处于同一网络 |
| 401 错误 | API Key 不匹配，联系管理员获取正确 Key |
| cc-switch 对话失败 | 协议必须选 **OpenAI Responses**，不是 Chat |
| 模型返回 500 | 服务器端网络问题，联系管理员排查 |
