# 日程安排

“日程安排”是一个本地优先的个人日程、学习记录、长期任务与云同步工具。

当前项目由三部分组成：

- Windows 电脑端：Vue 3 + Tauri 2 + 本地 FastAPI + SQLite。
- 手机端：Vue 3 + Capacitor + IndexedDB，当前已冻结为最终功能性基线。
- 云同步服务端：FastAPI + PostgreSQL，独立项目位于 `D:\apps\schedule_sync_server`。

云服务器只负责账号、设备、同步数据和变更日志；AI Key 只保存在用户设备本地，不上传、不代理。

## 目录

```text
schedule/
├─ README.md
├─ schedule.prd.md
├─ 三端联通上线操作手册.md
├─ 任务记忆文档.md
├─ 项目文件索引.md
├─ 项目文件索引.json
├─ 电脑端任务记忆文档.md
├─ 电脑端项目文件索引.md
├─ 电脑端项目文件索引.json
├─ schedule_backend/
├─ schedule_frontend/
├─ schedule_mobile/
├─ start-dev.ps1
├─ stop-dev.ps1
├─ build-release.ps1
└─ release/
```

## 一键开发启动

```powershell
cd D:\apps\schedule
.\start-dev.ps1
```

双击入口：

```text
start-dev.bat
```

停止开发环境：

```powershell
cd D:\apps\schedule
.\stop-dev.ps1
```

## Windows 安装包发布

最终用户不需要安装 Python、Node.js、Rust、npm 或 pip。发布给普通用户的文件是：

```text
release\Schedule_0.4.0_x64_setup.exe
```

在开发机生成安装包：

```powershell
cd D:\apps\schedule
.\build-release.ps1
```

如果只想跳过自动测试加快本机构建：

```powershell
.\build-release.ps1 -SkipTests
```

构建机需要安装 Python 3.11+、Node.js、Rust/MSVC 工具链和 Tauri CLI；这些只用于打包，不要求用户安装。

安装包内部结构：

- FastAPI 后端用 PyInstaller 打成 `schedule-backend.exe`。
- Tauri 将后端作为 sidecar 打入 NSIS 安装包。
- 应用启动后自动拉起本地后端，默认监听 `127.0.0.1:18765`。
- 本地 SQLite 数据库创建在 `%APPDATA%\日程安排\data\app.db`。
- 开发模式仍使用 `127.0.0.1:8000`，不会和安装版冲突。

## 云同步

正式同步域名：

```text
https://schedule-sync.zenithy.art
```

服务器部署目录：

```text
/opt/apps/schedule-sync
```

公网网关复用：

```text
/opt/apps/hiremate/Caddyfile
```

三端联通、部署、Caddy、iOS 测试和常见错误处理请看：

```text
三端联通上线操作手册.md
```

## 手机端冻结约束

`schedule_mobile` 已进入最终功能性基线。后续维护电脑端、云服务器、Caddy、部署脚本或管理员后台时，默认不得修改手机端代码。只有 iOS 打包发布、严重故障紧急修复、或云端无法兼容旧手机端时，才允许做最小化手机端改动。

## 验证命令

电脑端后端：

```powershell
cd D:\apps\schedule\schedule_backend
pytest -q
python -c "from app.main import app; print(app.title)"
```

电脑端前端：

```powershell
cd D:\apps\schedule\schedule_frontend
npm test -- --run
npm run build:desktop
npm run tauri:build
```

发布包：

```powershell
cd D:\apps\schedule
.\build-release.ps1
```

