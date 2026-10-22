# 安全部署与交付

## 数据目录选择

优先级：--data-dir → CODEXX_SERVER_HOME → 兼容的既有根目录 config.yaml → 新默认目录。

- 新源码运行：仓库 data/。
- Windows 发布版：%LOCALAPPDATA%\CodeXX\Server。
- Mac 发布版：~/Library/Application Support/CodeXX/Server。
- Linux 发布版：XDG_DATA_HOME/CodeXX/Server，默认 ~/.local/share/CodeXX/Server。

不要把数据放进 App 包或 PyInstaller 临时解包目录。旧 config.yaml/auths 不自动搬家；诊断报告会显示实际使用目录。GUI、CLI 和 Compose 必须指向同一个目录。

## CLI（可供 AI 自动化）

Windows 发布版举例；源码以 python launcher.py 替代程序名：

```powershell
.\CLIProxyAPI-Server.exe --doctor --data-dir C:\CodeXXData --report doctor.json
.\CLIProxyAPI-Server.exe --init --data-dir C:\CodeXXData
.\CLIProxyAPI-Server.exe --export-profile --data-dir C:\CodeXXData --host 100.x.x.x --output connection.cliproxy
```

初始化生成随机 API Key 和管理密码，私密保存，不打印。重复 --init 保留已有配置、密钥、绑定和代理；发现只存在部分文件时拒绝覆盖，要求先检查。自定义端口用 --port；绑定具体 Tailscale IP 用 --bind；仅确需代理时用 --proxy-port。

新配置使用本轮核对的上游 config-version 8 结构（server/access/management/oauth）。旧版配置只读兼容，不自动迁移；不要把新生成器当作任意历史镜像的转换器。

## 真正启动服务

完成检查并得到部署授权后，在数据目录执行：

```bash
docker compose pull
docker compose up -d
```

首次部署需要联网拉取镜像；已有镜像的离线部署可用 docker compose up -d --pull never。GUI 更新若拉取或启动失败不会再显示完成。默认 latest 便于初次使用，但生产升级应先记录现有镜像 ID/digest，再选择经过测试的固定版本或 digest；不要无备份自动更新。

管理入口默认 http://127.0.0.1:8317/management.html。新增上游账号时由用户登录。网络、认证、生成分别验证，服务端的生成还应记录上游请求/账号归属证据。

## 局域网、Tailscale 与管理权限

CLI --init 默认绑定 127.0.0.1，仅本机可用。新 GUI 初始化会优先使用已识别的 Tailscale IP，无 IP 时回退本机。远程设备需要明确的绑定、Tailnet ACL 和防火墙许可，并从客户端实测；不要默默绑定 0.0.0.0。

管理 API 与业务 API 可能共用端口：API Key 不应具有管理权限，管理密码不能导出给普通客户端。访问控制也要在 Tailnet/防火墙层限制。共享文件含明文 API Key，应使用可信渠道并为不同设备按需分配不同 Key。

## 备份与回滚

升级前完整备份数据目录到不入 Git 的本地私密位置，记录当前镜像标识。不把运行中的日志或账号文件当发布包；需要一致备份时在获准的维护窗口停止写入。回滚恢复对应的配置/认证与旧镜像，不重建密钥冒充修复。

没有自动账号额度查询能力；只有授权的上游管理/使用数据才能证明具体账号和余额。doctor 不读取或上传 auths 的内容。
