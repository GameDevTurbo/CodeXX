# 使用指南

## 管理面板

浏览器打开 http://localhost:8317/management.html，用 `config.yaml` 中 `secret-key` 的**原始明文**登录。

## 添加账号

### ChatGPT / Codex

前提：ChatGPT Plus 或 Pro 订阅。

1. ChatGPT 网页 → **Settings → Security** → 开启 **Enable device code authorization for Codex**
2. 管理面板 → **Codex OAuth** → 点击登录
3. 将返回链接复制到浏览器，完成授权
4. 凭证自动保存到 `auths/`，可添加多个账号

### Claude

需 Claude Pro/Max 订阅。管理面板 → **Claude OAuth** 授权。

### Gemini

- **OAuth**：管理面板 → Gemini OAuth
- **API Key**：在 `config.yaml` 中直接配置

## API 测试

```bash
# 列出可用模型
curl -s http://127.0.0.1:8317/v1/models -H Authorization: Bearer sk-u5bc6u9470/n/n# /u5bf9/u8bdd/u6d4b/u8bd5/ncurl -s -X POST http://127.0.0.1:8317/v1/chat/completions /n  -H Authorization: Bearer sk-u5bc6u9470 
  -H Content-Type: application/json 
  -d '{model:gpt-6-sol,messages:[{role:user,content:hi}],max_tokens:5}'
```

返回 JSON 且 `choices[0].message.content` 有内容即全链路正常。

## 客户端对接

- **API 地址**：`http://127.0.0.1:8317/v1`（远程访问替换为 Tailscale IP）
- **API Key**：`config.yaml` 中 `access.api-keys` 的値

已验证：Cherry Studio、ChatBox、NextChat、Open WebUI。

## cc-switch 配置

[cc-switch](https://github.com/farion1231/cc-switch) 用于 Codex CLI 配置切换。

| 字段 | 値 |
|------|-----|
| API 地址 | `http://127.0.0.1:8317/v1`（远程替换为 Tailscale IP） |
| API Key | `config.yaml` 中的密鑰 |
| 协议 | **OpenAI Responses**（必须选这个，不是 Chat） |

```toml
model_provider = custom
model = gpt-6-sol
model_reasoning_effort = high

[model_providers.custom]
name = custom
wire_api = responses
requires_openai_auth = false
base_url = http://127.0.0.1:8317/v1
```

保存后手动切换到该 Provider，再做一次实际对话验证模型调用是否正常。

## Tailscale 远程共享

### 部署端配置

1. **开放端口** — `docker-compose.yml` 端口改为 `0.0.0.0:8317:8317`，重启容器
2. **分配独立 Key** — `config.yaml` 的 `access.api-keys` 下添加新密鑰
3. **查看 Tailscale IP**：`tailscale ip -4`
4. **告知对方** — Tailscale IP + 端口 8317 + 独立 Key

### 客户端配置

双方加入同一 Tailscale 网络后：

- **API 地址**：`http://<Tailscale IP>:8317/v1`
- **API Key**：管理员分配的密鑰
- **协议**：OpenAI Responses（cc-switch）

### 撤销访问

删除 `config.yaml` 中对应的 api-key，配置热重载即时生效，无需重启容器。

## 负载均衡

添加多个同类型账号后自动生效，策略在 `config.yaml` 的 `routing.strategy` 中配置：

| 策略 | 说明 |
|------|------|
| `round-robin` | 轮询（默认） |
| `weighted-round-robin` | 加权轮询 |
| `fill-first` | 填满一个再用下一个 |

账号触发限流时自动切换到其他可用账号。
