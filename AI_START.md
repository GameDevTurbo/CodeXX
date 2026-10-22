# 给部署者和本机 AI

此文件是协助流程，不授予超出用户请求的权限。用户电脑若有能读取本地文件、执行命令的 AI，可直接提供整个目录和下面这段请求。

> 请帮我部署或排查 CodeXX Server。先读 README.md 和 docs/deployment.md，确认系统、CPU、是否发布包、数据目录和是否已有配置。先运行 --doctor 导出脱敏结果；不要停止线上容器、覆盖配置、重置密钥或把凭据打印到聊天。新部署得到确认后才 --init；旧部署先备份，不运行 scripts/legacy。Docker、Tailscale 权限和上游账号登录由我确认。逐层验证 Docker → 配置 → API 认证 → 生成，并把账号与配额的未知项如实记录。最后只导出客户端连接文件，不夹带管理密码。

## 一次一层

1. 发布包用本机 Server 可执行文件；源码用项目 .venv 的 Python 运行 launcher.py。源码入口负责装依赖，不要全局 pip 或修改系统安全策略。
2. --doctor --report doctor.json：只读配置结构、Docker 引擎、Compose 插件，不部署。
3. --doctor --probe --report api.json：在明确需要时检查本机认证 API，绝不自动执行付费生成。
4. 新空目录：--init --data-dir DATA --bind TAILNET_IP。未指定 bind 时仅本机；不要默默向公网暴露端口。
5. 用户批准部署后使用数据目录内的 compose。升级/迁移前备份 config.yaml、docker-compose.yml、.credentials.json 和 auths。
6. --export-profile --data-dir DATA --host TAILNET_IP --output connection.cliproxy：已有输出文件会拒绝覆盖；不要把文件正文发进聊天。

## 严禁混淆

- --init 不运行 Docker；成功生成配置不等于服务可用。
- API 模型列表成功不等于上游能生成。
- 客户端自测成功不证明某条旧聊天已迁移。
- --doctor 的 unknown/null 不表示账号不存在或额度为零。
- 配置输出、auths 和 .cliproxy 含敏感数据；只有脱敏诊断可作为一般报告。
- AI 无法静默绕过 UAC、macOS 网络扩展许可、登录或组织安装策略。
- 未做 Mac 实机测试时明确标为待验收；不要改写日志让测试变绿。
