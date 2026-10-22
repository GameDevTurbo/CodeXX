# 工程决策与发布

## 本次收敛

从“多个重复脚本 + 两份客户端 + 平台名相同的产物”收敛为稳定入口、单一实现包、统一构建、私密数据目录四层。server_app 只管 Server，客户端仅由 CodeXX-Client 构建。旧实现移入 scripts/legacy 保留已有修改，不作为可执行指南。

启动器优先成品，源码才创建 .venv。Python/Tk 不可用时返回明确错误，不静默装全系统 Python。依赖文件变化时重新安装，支持匹配平台的 offline_deps/wheels。

## 构建

```bash
python -m pip install -r requirements.txt pyinstaller
python scripts/build_release.py --role server
```

Windows 使用 onefile EXE；macOS 使用 onedir App 和 ditto 归档，分别构建 Intel 与 Apple Silicon；Linux 原生构建。不能在 Windows 构建 Mac 成品。发布包通过白名单只带程序、文档、manifest，不包含 config.yaml、auths、.credentials.json、.venv 或历史脚本。

CI 按系统和架构分别执行；工作流写好不代表已经在远程运行。Mac App 签名、公证和真实机器验收尚待补齐，不能承诺任意 Mac 一键信任。

## 回归标准

在临时数据目录验证：重复初始化不改密钥、部分配置不覆盖、导出无管理密码、带空格路径、非法端口、只读诊断、Docker 不可用、构建包无凭据。用本地模拟 API 验证认证，不触碰线上服务。

至少额外验证一份真实 Windows 打包后的 --doctor/--init/--export-profile。正常 GUI 只做必要的一次验收；不要循环开关用户在用客户端。Mac 需独立验证 Finder 启动、GUI、网络扩展、带空格路径和 Docker 绑定。

## 尚需后续建设

签名与公证、镜像版本策略、可复用的正式回归体系、受授权的上游账号/额度查询，以及正式发布前的 Mac 实机验收。它们不能用本次 Windows 编译和模拟测试代替。
