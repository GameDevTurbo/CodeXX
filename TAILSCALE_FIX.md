# Tailscale 启动与登录修复

## 已定位的问题

Windows 版 Tailscale 的命令行工具是 `tailscale.exe`，而通知区/登录界面由
`tailscale-ipn.exe` 提供。此前客户端错误地将 `Tailscale.exe` 当作图形程序启动；
由于 Windows 文件名不区分大小写，这实际上启动了命令行工具，因而不会显示登录界面。

## 已修复

- `launcher.py` 和 `client.py` 现在在 Windows 上优先启动
  `C:\Program Files\Tailscale\tailscale-ipn.exe`。
- 若未安装图形程序，仍会回退到 `tailscale up`，以便在终端完成网页登录。

## 本机恢复步骤

截至 2026 年 10 月 22 日，Tailscale 服务正在运行，网络诊断正常，但当前状态为
`Logged out`。重新登录即可恢复：

1. 从 CodeXX 的 Tailscale 区域点击 **Login**。
2. 在弹出的 Tailscale 窗口中点击 **Log in** 并在浏览器完成认证。
3. 返回 CodeXX，等待状态显示为 `Connected` 和 Tailscale IP。

如果图形窗口没有出现，可在 PowerShell 执行：

```powershell
& 'C:\Program Files\Tailscale\tailscale.exe' up
```

复制终端输出的登录链接到浏览器完成认证，然后用以下命令确认：

```powershell
tailscale status
tailscale ip -4
```
