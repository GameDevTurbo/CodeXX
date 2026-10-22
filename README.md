# CodeXX Server

部署并管理 CLIProxyAPI 服务，向客户端提供标准 API。仅使用你有权使用的账号和服务，遵守上游条款；服务入口不等于上游账号身份或额度证明。

## 最短路径

1. **只想使用已有服务**：下载 [CodeXX-Client](https://github.com/GameDevTurbo/CodeXX-Client/releases)，不需要部署本项目。
2. **要运行服务**：从 [Releases](https://github.com/GameDevTurbo/CodeXX/releases) 下载匹配系统与 CPU 的 Server 包。Windows 打开 CLIProxyAPI-Server.exe；Mac 打开 CLIProxyAPI-Server.app。预编译包无需 Python，Docker Desktop 和 Tailscale 需按需要安装。
3. 打开 Docker Desktop。首次 Setup 创建配置；已有配置不会被覆盖或重置密钥。新 GUI 部署优先绑定已识别的 Tailscale IP，否则仅本机；纯 CLI 初始化默认仅本机。
4. 在管理页登录你授权的上游账号。验证 API 列表和实际生成是两项不同验收。
5. 导出 .cliproxy 给其他设备的客户端。连接文件只含 API 凭据，不含管理密码；请通过可信渠道传递。

有本机 AI 支持时，先让 AI 读 [AI_START.md](AI_START.md)。不要把管理密码或 API Key 粘贴进聊天。

## 目录

| 位置 | 作用 |
|---|---|
| Server.bat / Server.command | 源码兼容入口；优先使用预编译程序 |
| launcher.py | 稳定的 Python/CLI 入口 |
| server_app/ | GUI、配置生成、持久路径、诊断与导出 |
| scripts/ | 项目 .venv 启动器和白名单发布打包器 |
| scripts/legacy/ | 历史实现，只保留参考，不应运行、不发布 |
| docs/ | 平台、部署、维护与验证指南 |
| data/ | 新源码部署数据（忽略 Git） |
| release/ | 分平台 ZIP、SHA256（忽略 Git） |

原仓库根目录若已有 config.yaml，继续使用原目录，不自动迁移 auths、日志或凭据。新发布版使用系统用户数据目录，不再把配置写入 PyInstaller 临时目录。可用 CODEXX_SERVER_HOME 或 --data-dir 指定目录，详见 [部署指南](docs/deployment.md)。

关闭 Server 管理窗口不会停止 Docker 容器。新初始化的 Compose 默认启用 `unless-stopped`、30 秒优雅停止、2 CPU、1 GiB 内存、512 进程数上限和 Docker JSON 日志轮转（10 MiB × 5），用于长期挂机时限制资源失控；已有 Compose 不会被静默覆盖。

本仓库停止构建旧客户端；Client.bat / Client.command 只转到独立客户端或下载页，避免两份代码产生不同修复结果。

## 只读诊断

```powershell
.\CLIProxyAPI-Server.exe --doctor --report doctor.json
.\CLIProxyAPI-Server.exe --doctor --probe --report api.json
```

第一条只检查本地文件和 Docker 状态，不启动/停止容器；第二条按 Compose 的本机发布地址（包括指定的 Tailscale IP）请求 /v1/models，不生成文本。doctor 的退出码 0=满足所查条件、2=尚未就绪；操作错误为 1。报告不含密钥或上游正文，账号与额度未知时保持 unknown/null。

## 更多

- [本轮工程分析与验证边界](docs/engineering-review.md)
- [Windows](docs/windows.md) / [macOS](docs/macos.md) / [Linux](docs/linux.md)
- [初始化、导出、升级与回滚](docs/deployment.md)
- [工程决策与发布验收](docs/development.md)

代理不是必选项：只有上游网络确实需要代理时才配置。容器里的 127.0.0.1 不是宿主机；配置容器代理与 Docker 拉取镜像代理是两件事。不要为了排障关闭防火墙或重置账号。
