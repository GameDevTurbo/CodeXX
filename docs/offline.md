# 自动下载与离线部署

## 普通用户

推荐下载对应平台的 `CLIProxyAPI-Server-系统-架构-offline.zip`，解压整个文件夹后打开 Server：

1. 缺少 Docker 时，点击“安装 Docker”；安装程序优先从包内打开。完成安装后打开 Docker，等待就绪。
2. 跨设备访问时再点击“安装 Tailscale”，完成安装、登录和系统授权。本机使用可跳过。
3. 完整离线包会自动勾选“离线部署”。点击 Setup → Generate and Deploy，自动核验和加载本地镜像、挂载本地管理面板、启动服务，不执行镜像拉取。
4. 打开管理面板，接入上游账号，检查连接，再验证一次实际生成。

普通 ZIP 体积更小，缺失依赖时应用内自动从官方地址下载并打开安装程序，文件保存在 `offline_deps/目标平台/`。下载进度可见，可重试；完整文件通过大小和 SHA-256 核验后才使用。Tailscale 同时核对官方 SHA-256。

保持解压文件夹完整；不要只移动 App 而丢下 offline_deps。安装、协议、管理员/网络扩展权限和账号登录仍在系统或厂商界面完成，不静默代替用户接受协议。

macOS 下载的 App 可能从系统的 AppTranslocation 临时目录运行。v1.3.1 会尝试读取其原始目录；若系统无法返回位置，会停止下载并提示选择离线包。可以点击“选择离线包”指定完整解压目录，或关闭管理窗口后使用同目录 Server.command；该入口会显式传入依赖目录。无需移除 quarantine 或关闭系统安全保护。

离线指安装文件与服务镜像可在无下载网络的环境中使用；调用上游 AI、账号首次授权及 Tailscale 登录仍需要相应网络。Windows 的 WSL/虚拟化等系统前置项需提前准备；Linux 离线包包含服务镜像和管理页面，Docker Engine、Compose 及可选 Tailscale 需按发行版预装，不通用捆绑系统包。

## 在联网电脑准备工程内离线文件

源码使用项目 `.venv`；发布程序同样支持这些参数，无需 Python。准备文件不会安装软件或启动服务容器：

```bash
# 只准备当前平台安装程序，不需要 Docker 引擎
.venv/bin/python launcher.py --prepare-offline --installers-only

# 准备完整离线依赖（需要联网与已运行的 Docker）
.venv/bin/python launcher.py --prepare-offline --target macOS-arm64

# 只读核验，断网可运行；缺文件或校验失败会返回非零状态
.venv/bin/python launcher.py --check-offline --target macOS-arm64
```

可选目标：`macOS-arm64`、`macOS-x64`、`Windows-x64`、`Linux-x64`。可用 `--bundle-dir PATH` 指定存储目录；GUI 可用 `CODEXX_OFFLINE_DIR` 指向该目录。默认工程目录：

```text
offline_deps/
  macOS-arm64/
    Docker.dmg
    Tailscale.pkg
    cli-proxy-api-image.tar
    management.html
    manifest.json
```

清单记录目标平台、文件大小与 SHA-256、镜像 ID、架构及仓库 digest。准备镜像使用对应 `linux/arm64` 或 `linux/amd64`，只拉取和保存，不运行镜像。准备镜像可能更新本机同名镜像标签，请在专用准备机器上使用。

界面“准备完整离线包”将文件准备到上述目录：Docker 未就绪时只下载安装程序，Docker 就绪后再次点击可补齐镜像和管理面板。Release 的完整离线包由 CI 在专用 runner 上完成这些步骤。

`offline_deps/` 已被 Git 忽略，大安装程序和镜像不放进 Git 历史。CI 会将其与对应原生程序打成独立 `-offline.zip` Release 附件。普通包和离线包均包含 HTML 指南；构建过程只收录校验通过的依赖白名单，不带运行配置、上游账号或 API Key。

## 无桌面的 Linux

先准备 Docker Engine + Compose，在解压目录执行：

```bash
chmod +x CLIProxyAPI-Server
./CLIProxyAPI-Server --init --data-dir "$HOME/.local/share/CodeXX/Server"
./CLIProxyAPI-Server --load-offline --data-dir "$HOME/.local/share/CodeXX/Server"
cd "$HOME/.local/share/CodeXX/Server"
docker compose up -d --pull never
```

`--load-offline` 核验并加载镜像、挂载本地管理面板，不启动容器。`--offline` 用于图形界面；勾选后缺失离线文件会明确报错，不回退到联网下载或拉取。已有配置和密钥保留，自定义面板挂载冲突时停止并提示人工处理。

## 下载来源

- [Docker macOS 官方下载与安装说明](https://docs.docker.com/desktop/setup/install/mac-install/)
- [Docker Windows 官方下载与安装说明](https://docs.docker.com/desktop/setup/install/windows-install/)
- [Tailscale 官方稳定包与 SHA-256](https://pkgs.tailscale.com/stable/)
- [CLIProxyAPI 官方管理面板说明](https://help.router-for.me/management/webui)

当前 Tailscale 安装程序固定为 1.104.2，Windows 采用内含 x64 安装载荷的 MSI；Docker 下载地址由官方维护，准备时记录实际文件校验值；服务镜像准备时记录镜像标识。校验值验证文件完整性，使用时还应保留来源可信的整包及其发布校验文件。
