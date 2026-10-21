# Linux 部署指南（云服务器）

适用于 Ubuntu / Debian / CentOS。云服务器在境外，无需配置代理。

## 部署服务

```bash
git clone https://github.com/GameDevTurbo/CodeXX.git && cd CodeXX
bash scripts/deploy.sh --expose
```

`--expose` 让服务监听 `0.0.0.0`，需同时开放防火墙/安全组 8317 端口。

管理面板：http://你的服务器IP:8317/management.html

## 日常管理

```bash
docker compose up -d --pull never   # 启动
docker compose down                  # 停止
docker compose logs -f               # 实时日志
docker compose pull && docker compose up -d  # 更新镜像
```

## 防火墙

```bash
# Ubuntu/Debian
sudo ufw allow 8317/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8317/tcp && sudo firewall-cmd --reload
```

> 同时在云服务商控制台开放 8317 入站规则。

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
| 无法拉取镜像 | 网络问题，改用 `--pull never` 使用已有镜像 |
| API 不通 | 检查防火墙 + 云安全组 8317 入站 |
| cc-switch 返回 404 | 协议改为 **OpenAI Responses** |
