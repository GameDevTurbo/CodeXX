# Windows Server

普通用户下载 Windows-x64 Server 发布包，解压后打开 EXE；源码用户打开 Server.bat。源码需要含 Tk 的 Python 3.10+，依赖安装到项目 .venv。源码初始化失败会返回错误，日志在 %LOCALAPPDATA%\CodeXX-Server\startup.log。

先运行 Docker Desktop；Tailscale 用于远程访问时才需要。安装、系统权限、账号登录仍需用户授权，不以“全自动”为由绕过 UAC。

新发布版数据在 %LOCALAPPDATA%\CodeXX\Server；已有根目录配置保持兼容。可用 --data-dir 明确指定同一数据目录。关闭 Server 管理窗口不停止 Docker 容器。

按 [部署指南](deployment.md) 诊断、初始化、部署、认证、导出。只使用服务的电脑安装独立 CodeXX-Client，不要运行本仓库的历史 client.py 实现。

本轮自测以隔离临时目录和模拟服务为主；真实服务器只读检查，不反复启停线上容器。Windows 构建成功不代表 Mac 实机验证完成。
