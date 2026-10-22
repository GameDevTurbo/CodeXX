# CodeXX Server 工程规范

- 中文回复；文本 UTF-8 无 BOM。使用 apply_patch 编辑文件。
- 根目录 launcher.py / Server.bat / Server.command 是兼容入口；实现位于 server_app/。
- 修改前读 README.md、AI_START.md 和 docs/development.md。不在 scripts/legacy 中继续实现新功能。
- 依赖统一来自 requirements.txt，源码使用 .venv；构建用 python scripts/build_release.py --role server。
- 运行配置、.cliproxy、auths、密钥、诊断日志、备份不入 Git，不入发布包，不输出到聊天。
- 保留既有配置和用户修改，不覆盖密钥。初始化不等于部署，API 连通不等于生成或具体聊天路由成功，unknown/null 不等于零。
- 不修改 Codex Desktop 托管字段 notify、marketplaces、plugins、mcp_servers.node_repl，不改写历史聊天来冒充迁移。
- Windows 自测优先临时 HOME/CODEX_HOME/LOCALAPPDATA/数据目录与模拟 API；不反复关闭在用客户端，不启停线上容器。
- 实质修改后构建并核验成品；发布版数据必须存于持久目录，不使用 PyInstaller 临时路径。
- 不在无现成测试框架时引入无关框架；隔离行为检查不能冒充 Mac 真机验证。说明 Mac 签名/公证/实机测试的缺口。
- 用户未明确要求时不创建分支、提交、推送、发布 Release 或重启线上服务。
