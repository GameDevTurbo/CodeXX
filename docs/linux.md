# Linux Server

有桌面时可使用原生发布程序或 bash start.sh。无桌面的服务器使用 launcher.py 的 --doctor、--init 和 --export-profile；这些 CLI 分支不导入 GUI，也不要求 Tk 显示会话。

源码创建 .venv 后安装 requirements.txt，按 deployment.md 初始化数据并显式运行 Docker Compose。系统 Docker、Compose 和网络权限由管理员准备，不自动运行远程脚本安装。

默认仅绑定本机。需要共享时指定 Tailscale IP；不要为解决权限问题关闭防火墙。日志、密钥和 auths 不进入 Git 或发布包。
