# 使用指南

## 管理面板

浏览器打开 http://localhost:8317/management.html，用 `config.yaml` 中 `secret-key` 的**原始明文**登录（首次启动后会自动哈希化）。

## 添加账号

### ChatGPT / Codex

前提：ChatGPT Plus 或 Pro 订阅。

1. ChatGPT 网页 → **Settings → Security** → 开启 **"Enable device code authorization for Codex"**
2. 管理面板 → **OAuth 登录** → **Codex OAuth** → 点击登录
3. 将返回的链接复制到浏览器，完成 ChatGPT 授权
4. 凭证自动保存到 `auths/`，可重复添加多个账号

### Claude

需 Claude Pro/Max 订阅。管理面板 → **Claude OAuth** 授权。

### Gemini

- **OAuth**：管理面板 → Gemini OAuth
- **API Key**：在 `config.yaml` 中直接配置

## API 测试

```bash
# 列出模型
curl -s http://127.0.0.1:8317/v1/models -H "Authorization: Bearer sk-你的密钥"

# 对话
curl -s http://127.0.0.1:8317/v1/chat/completions \
  -H "Authorization: Bearer sk-你的密钥" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-6-sol","messages":[{"role":"user","content":"Hello"}]}'
```

## 客户端对接

兼容所有支持 OpenAI API 的客户端，填入：

- **API 地址**：`http://127.0.0.1:8317/v1`
- **API Key**：`config.yaml` 中 `access.api-keys` 的值

已验证客户端：Cherry Studio、ChatBox、NextChat、Open WebUI。

## cc-switch 配置

[cc-switch](https://github.com/farion1231/cc-switch) 用于 Codex 配置切换。新建 Provider，TOML 配置：

```toml
model_provider = "custom"
model = "gpt-6-sol"
model_reasoning_effort = "high"

[model_providers.custom]
name = "custom"
wire_api = "responses"
requires_openai_auth = false
base_url = "http://127.0.0.1:8317/v1"
```

Auth Mode 选 API Key，填入对应密钥。切换到该 Provider 即可。

## Tailscale 共享

### 配置步骤

1. **开放端口** — `docker-compose.yml` 端口改为 `"0.0.0.0:8317:8317"`，重启容器
2. **分配独立 Key** — `config.yaml` 的 `access.api-keys` 下添加新密钥
3. **告知对方** — Tailscale IP + 端口 + 独立 Key

```bash
tailscale ip -4   # 查看你的 Tailscale IP
```

### 撤销访问

删除 `config.yaml` 中对应的 api-key，配置热重载即时生效。

## 负载均衡

添加多个同类型账号后自动生效，策略在 `config.yaml` 的 `routing.strategy` 中配置：

| 策略 | 说明 |
|------|------|
| `round-robin` | 轮询（默认） |
| `weighted-round-robin` | 加权轮询 |
| `fill-first` | 填满一个再用下一个 |

账号触发限流时自动切换到其他可用账号。
