# 日程安排

“日程安排”是一个本地优先的个人日程、学习记录与长期目标管理工具。当前项目已经拆成三端：

- Windows 电脑端：Vue 3 + Tauri + 本地 FastAPI + SQLite。
- 手机端：Vue 3 + Capacitor + IndexedDB。
- 云同步服务端：FastAPI + PostgreSQL，独立仓库目录为 `D:\apps\schedule_sync_server`。

云端只负责账号、设备、同步快照和变更日志；AI Key 只保存在用户设备本地，不上传、不代理。

## 目录

```text
schedule/
├─ README.md
├─ schedule.prd.md
├─ 三端联通上线操作手册.md
├─ 任务记忆文档.md
├─ 项目文件索引.md
├─ 项目文件索引.json
├─ 初期构建md/
├─ schedule_backend/
├─ schedule_frontend/
├─ schedule_mobile/
├─ start-dev.ps1
├─ start-dev.bat
├─ stop-dev.ps1
└─ stop-dev.bat
```

云同步服务端独立在：

```text
D:\apps\schedule_sync_server
```

服务器部署目录固定为：

```text
/opt/apps/schedule-sync
```

正式同步域名固定为：

```text
https://schedule-sync.zenithy.art
```

## 当前能力

- 今日任务、固定任务模板、事件、课程、学习记录、学习统计、长期任务均已可用。
- 长期任务支持子任务拆解，子任务可生成今日任务。
- 学习记录按“学习科目”统计，例如数学、Python、英语。
- DeepSeek 是默认 AI 路线，解析使用 `deepseek-chat`，规划使用 `deepseek-reasoner`。
- 导入中心支持课表 JSON 导入，并提供“AI 转课表 Prompt”辅助图片课表转换。
- Windows 端支持一键启动、Tauri 开发模式和 NSIS 安装包构建。
- 云同步已升级为三端统一 envelope v1，支持 desktop/mobile payload 兼容。
- 电脑端 pull 已能把远端数据写入本地业务表；本地 dirty 时进入冲突记录。
- 手机端支持登录后 bootstrap、启动同步、网络恢复同步、前台恢复同步和 Token refresh。
- 手机端已完成最终功能性基线：模板自动刷新每日任务、AI 解析保留单独开始时间、日程事件可编辑删除、云端确认后本地实体标记为已同步。

## 手机端冻结约束

- `schedule_mobile` 已封板为最终功能基线。
- 后续升级电脑端、云服务器端、部署脚本、Caddy 或管理后台时，默认不得修改手机端目录。
- 新业务功能优先在电脑端和云服务器端实现；云端新增字段必须兼容旧手机端可忽略、可读取、不崩溃。
- 只有 iOS 打包发布、严重故障紧急修复、云端无法兼容旧手机端时，才允许最小化修改手机端。
- 任何手机端改动后必须重新执行 `npm test -- --run`、`npm run build`、`npm run cap:sync`。

## 一键启动 Windows 电脑端

双击：

```text
start-dev.bat
```

或执行：

```powershell
cd D:\apps\schedule
.\start-dev.ps1
```

启动器会自动：

1. 创建后端 `.venv`。
2. 安装后端依赖。
3. 启动 FastAPI 并检查 `/api/health`。
4. 安装前端依赖。
5. Rust/Tauri 可用时进入 `npm run tauri:dev`。
6. Rust 不可用时降级为 `npm run dev`。

停止：

```powershell
cd D:\apps\schedule
.\stop-dev.ps1
```

## 手动启动

后端：

```powershell
cd D:\apps\schedule\schedule_backend
python run.py
```

桌面前端 Web：

```powershell
cd D:\apps\schedule\schedule_frontend
npm run dev
```

Tauri：

```powershell
cd D:\apps\schedule\schedule_frontend
npm run tauri:dev
```

手机端：

```powershell
cd D:\apps\schedule\schedule_mobile
npm install
npm run dev
```

## 云同步上线

请按 [三端联通上线操作手册.md](./三端联通上线操作手册.md) 执行，顺序是：

1. 部署 `schedule_sync_server` 到 `/opt/apps/schedule-sync`。
2. 接入 `/opt/apps/hiremate/Caddyfile`。
3. 运行云端冒烟测试。
4. Windows 电脑端填写 `https://schedule-sync.zenithy.art` 并登录。
5. 手机端填写 `https://schedule-sync.zenithy.art` 并登录。
6. 验证电脑到手机、手机到电脑双向同步。

## 验证命令

电脑端后端：

```powershell
cd D:\apps\schedule\schedule_backend
pytest -q
python -c "from app.main import app; print(app.title)"
```

桌面前端：

```powershell
cd D:\apps\schedule\schedule_frontend
npm test -- --run
npm run build
```

手机端：

```powershell
cd D:\apps\schedule\schedule_mobile
npm run build
```

云同步服务端：

```powershell
cd D:\apps\schedule_sync_server
python -m pytest -q
python -c "from app.main import app; print(app.title)"
```

服务器上：

```bash
cd /opt/apps/schedule-sync
bash deploy/smoke-test.sh http://127.0.0.1:18130
```

## 文档说明

- `任务记忆文档.md`：当前阶段、关键决策、验证结果。
- `项目文件索引.md`：人类可读文件索引。
- `项目文件索引.json`：机器可读文件索引。
- `三端联通上线操作手册.md`：正式联通和上线流程。
- `电脑端任务记忆文档.md` / `电脑端项目文件索引.md`：Windows 电脑端专用维护入口。
- `手机端操作手册.md`：根目录手机端手册入口。
- `schedule_mobile/手机端操作手册.md`：手机端长期维护、调试、发布和 iOS 上架说明。
- `schedule_mobile/任务记忆文档.md` / `schedule_mobile/项目文件索引.md`：手机端专用维护入口。
- `D:\apps\schedule_sync_server\任务记忆文档.md` / `D:\apps\schedule_sync_server\项目文件索引.md`：云同步服务端专用维护入口。
- `初期构建md/`：阶段性方案、旧 Prompt、旧操作流程归档。
