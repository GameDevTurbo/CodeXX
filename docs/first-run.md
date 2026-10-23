# 首次部署：每一步看到什么、需要手动做什么

## 选择正确的下载包

Apple Silicon 下载 macOS-arm64，Intel Mac 下载 macOS-x64；Windows 和 Linux 同样按 CPU 选择。使用 Release 随附的文档及 manifest.json，不要把 main 分支说明直接当成旧发布包说明。核对同名 .sha256，再解压到可写目录。

预编译包无需 Python。macOS/Windows 仍需 Docker Desktop；Linux 需 Docker Engine 与 Compose 插件。Tailscale 仅在其他设备远程访问时需要。本机先完成部署和验证，再配置远程连接。

## 正常操作流程

| 步骤 | 用户操作 | 通过标准 / 下一步 |
|---|---|---|
| 1. 安装 Docker | 从官方站点安装匹配 CPU 的 Docker Desktop，打开应用 | 引擎为 Running；安装成功不等于引擎已经启动 |
| 2. 完成系统提示 | 按需接受 Docker 协议，在系统弹窗输入本机管理员密码；钥匙串、目录访问提示由用户检查确认 | 密码只在系统弹窗输入，不发到聊天；Mac 必须解锁 |
| 3. 打开 Server | Mac 打开 .app 或 Server.command；Windows 打开 Server.bat | 程序发现 Docker，即使 Finder 的 PATH 没有 docker |
| 4. 首次 Setup | 填写确实在用的代理端口；无需代理填 0，然后 Generate and Deploy | 随机密钥保存到数据目录，不在聊天显示；旧配置保留 |
| 5. 拉取与启动 | 等待镜像下载；有系统或钥匙串弹窗时在本机处理 | 命令成功才进入后续步骤；超时不等于后台任务已取消 |
| 6. 检查连接 | 点击“检查连接” | 有密钥模型列表成功且无密钥被拒绝；模型数可为 0 |
| 7. 接入上游 | 在 Management Panel 中登录自己授权的上游账号，或配置自己的上游 API Key | 账号和模型可用性需要单独确认；GitHub 登录不会授权 AI 账号 |
| 8. 验证生成 | 用自己的客户端选择一个模型发送一次明确的测试请求 | 可能消耗上游额度，由用户主动执行；模型列表成功不代替此步 |
| 9. 客户端连接 | 需要时导出 .cliproxy 并导入客户端 | 仅含客户端 API 凭据，无管理密码；localhost 仅用于当前电脑 |

发布版 Mac 数据默认位于 `~/Library/Application Support/CodeXX/Server`；源码默认 `data/`。指定 `--data-dir` 时 GUI/CLI 必须使用同一目录。路径带空格时加引号。旧根目录配置优先兼容，不自动迁移或重新生成密钥。

## 卡住时怎么处理

| 现象 | 检查和恢复 |
|---|---|
| Docker 安装包下载慢或中断 | 从官方渠道重试或断点续传，核对下载完整性；不要因下载慢关闭系统安全机制 |
| 找不到 Docker | 确认 Docker.app 在 Applications 或用户 Applications；新版会自动定位。源码终端可用完整 Docker 路径检查版本 |
| 一直等 Docker | 打开 Docker Desktop，检查管理员授权、协议、钥匙串等窗口；解锁 Mac 后再试。程序不会代填密码或接受协议 |
| Pull 没进度、TLS/网络错误 | 查看 Docker Desktop 的代理设置和当前代理是否运行；Docker 镜像拉取代理与容器内上游代理是两件事。检查凭据助手/钥匙串提示，不要清空用户凭据 |
| 启动停在 Starting / created | 检查 Docker 的目录共享和 macOS 文件访问提示、Compose 源路径是否存在。先看状态，不要连续重建容器 |
| 端口已占用 | 确认是否已有本项目或其他服务占用；不要自动停止无关服务。新部署可选其他 API 端口，同时检查 OAuth 回调端口 8085 |
| running 但本机 API 不通 | 用 docker compose ps 检查发布端口；检查容器 NetworkSettings.Networks 是否为空、日志是否 network is unreachable。备份后在维护窗口通过 Compose 重建网络/容器，不把 running 当验收成功 |
| 401 | 使用当前数据目录的 API Key；管理面板使用管理密码，两者不可互换 |
| 模型列表 200 但为空 | 检查上游账号登录、模型配置和路由；未知额度不能当成 0 |
| 只有管理页打不开 | 查看容器访问 GitHub 管理页资源的网络和代理；检查 management 配置。业务 API 与管理页分别验证 |

GUI 拉取最多等待 10 分钟，其他 Compose 操作最多等待 2 分钟，并定期提示检查弹窗。超时只终止本次客户端等待，Docker 后台可能仍在处理。先运行“检查连接”或 `docker compose ps`，再决定是否重试。程序不会自动切换凭据、删除密钥或清理 Docker 卷。

只读 CLI 检查（Mac 发布版）：

```bash
./CLIProxyAPI-Server.app/Contents/MacOS/CLIProxyAPI-Server --doctor --probe --report doctor.json
```

报告包含 next_steps，generation 始终为 not_checked；不读取上游认证文件、不请求生成。源码可用 `.venv/bin/python launcher.py` 替换可执行文件路径；诊断无需打开 Tk 窗口。分享诊断前仍应检查路径、地址等个人环境信息。

## v1.1.0 历史包与本次实机记录

2026-10-23 在 Apple Silicon Mac 部署的旧 v1.1.0 包只有 arm64 可执行文件，但 Server.command 调用 start.sh，后者寻找缺失的 launcher.py，因此不可依赖该脚本。修订后的发布流程生成独立的 .app 启动入口，不带这套源码脚本；此修订尚未发布，不能期待重新下载旧 tag 就获得修复。

本次还遇到 Docker 缺失、下载中断、锁屏、管理员授权等待、公开镜像拉取停顿、目录挂载等待，以及一次启动失败后容器没有网络端点。本机最终使用 Docker 命名卷、固定镜像 digest 并重新建立容器网络，验证了无密钥/错误密钥 401、有效密钥模型列表 200、管理接口/页面 200。上游账号未接入，未验证实际生成。

命名卷是本次部署的人工恢复方案，新版 Setup 仍默认使用数据目录绑定挂载；未实现自动迁移。旧部署必须保留运行时数据位置，尤其不要把初始化副本覆盖到卷里的最新配置。采用命名卷的用户需单独备份卷，不能只备份源码目录。

关闭 Server 窗口不会停止容器。容器随 Docker 按 unless-stopped 恢复；退出 Docker、Mac 休眠或网络变化会影响可用性。需要长期开机运行时，也要单独检查 Docker 登录启动设置。签名、公证、Windows/Intel Mac 实机及远程联网仍需正式发布前验收。
