# 工程决策与发布

## 本次收敛

从“多个重复脚本 + 两份客户端 + 平台名相同的产物”收敛为稳定入口、单一实现包、统一构建、私密数据目录四层。server_app 只管 Server，客户端仅由 CodeXX-Client 构建。旧实现移入 scripts/legacy 保留已有修改，不作为可执行指南。

启动器优先成品，源码才创建 .venv。Python/Tk 不可用时返回明确错误，不静默装全系统 Python。依赖文件变化时重新安装，支持匹配平台的 offline_deps/wheels。

## 构建

发布版本记录于根目录 VERSION。将版本号改为新的三段数字并与代码一起提交到 main，仓库自动测试、构建四个平台产物，全部成功后创建对应 v 标签和 Release。也支持推送与 VERSION 一致的 v 标签；workflow_dispatch 仅构建验收，不发布。发布附件由 CI 生成，不上传本机预览包。

```bash
python -m pip install -r requirements.txt pyinstaller
python scripts/build_release.py --role server
```

Windows 使用 onefile EXE；macOS 使用 onedir App 和 ditto 归档，分别构建 Intel 与 Apple Silicon；Linux 原生构建。不能在 Windows 构建 Mac 成品。发布包通过白名单只带程序、文档、manifest，不包含 config.yaml、auths、.credentials.json、.venv 或历史脚本。

CI 按系统和架构分别执行；工作流写好不代表已经在远程运行。Mac App 签名、公证和真实机器验收尚待补齐，不能承诺任意 Mac 一键信任。

Mac 本地构建若提示 Xcode 许可未接受（lipo 返回 69），应由用户在终端运行 `sudo xcodebuild -license` 阅读并自行决定是否接受，然后重新构建。不能跳过该错误后交付残缺 App。2026-10-23 在用户接受许可后完成 arm64 构建，并从归档解压的独立 Server.command 验证 CLI 初始化与只读诊断。根目录 launcher.py 必须转发到 server_app.cli，不再保留旧 GUI 实现；入口回归测试覆盖该路径。该结果不代替 Finder GUI、签名/公证及其他系统验收。

本机预览包验证：8 项隔离回归通过；解压后 CLI 的带空格数据目录、重复初始化、诊断与导出完成验收；App 在临时目录通过 codesign 严格完整性检查（仅 ad-hoc 签名，无开发者签名/公证）。打包阶段仅在临时副本清理 FinderInfo/ResourceFork，不清除 quarantine 或安全属性。图形模式在受控命令行环境退出 134，原因尚未确定；桌面工具未获准访问此 App，无法进一步确认 Finder GUI。因此当前产物为预览验证包，正式发布前必须补做 GUI 实机验收，不应把 CLI 验收描述为完整 GUI 可用。

2026-10-23 补验：通过 macOS Launch Services 打开本机 arm64 App 后窗口可显示，未复现直接从受控终端启动时的 SIGABRT。窗口显示不代表部署通过；用户仍需按首次部署指南验收 Docker、API 和生成。签名仍为 ad-hoc，未做开发者签名或公证。

补验同时发现本机 Tk 环境中后台线程调用 after 会使状态一直停在 Checking；改为线程安全队列，由主线程读取并调度所有 GUI 回调。重建后桌面已显示 Docker Running、Not configured、Not deployed 和 Setup 按钮，并补充不依赖真实窗口的线程调度回归。

## 回归标准

运行 `python -m unittest discover -s tests -v`：使用模拟 Docker 进程及本地模拟 API，不启停实际容器。CI 必须调用 `scripts/build_release.py`，不能另行复制源码启动脚本进发布包。Mac 包的 Server.command 直接调用同目录 App；上传和发布均使用 release/ 下的 ZIP 及 SHA-256。矩阵分别使用 macos-15（arm64）与 macos-15-intel（x64），标签来自 [GitHub 官方 runner 文档](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)。

在临时数据目录验证：重复初始化不改密钥、部分配置不覆盖、导出无管理密码、带空格路径、非法端口、只读诊断、Docker 不可用、构建包无凭据。用本地模拟 API 验证认证，不触碰线上服务。

至少额外验证一份真实 Windows 打包后的 --doctor/--init/--export-profile。正常 GUI 只做必要的一次验收；不要循环开关用户在用客户端。Mac 需独立验证 Finder 启动、GUI、网络扩展、带空格路径和 Docker 绑定。

## 尚需后续建设

签名与公证、镜像版本策略、可复用的正式回归体系、受授权的上游账号/额度查询，以及正式发布前的 Mac 实机验收。它们不能用本次 Windows 编译和模拟测试代替。
