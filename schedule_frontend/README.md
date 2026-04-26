# 日程安排前端

`schedule_frontend` 是“日程安排”项目的桌面端前端工程，基于：

- Vue 3
- TypeScript
- Vite
- Pinia
- Vue Router
- Element Plus
- Tauri 2.x

## 当前状态

- 已完成 Stitch UI 对接改造
- 已新增独立 `AI 工作区`
- 已切换为 Element Plus 按需加载
- 已完成一轮构建包体优化
- 已新增 `长期任务` 页面，支持目标管理、子任务拆解和生成今日任务
- 今日任务支持无计时直接完成并补录实际时长
- 学习任务可在完成时同步写入手动学习记录
- 学习记录页已强化为按学习科目统计和科目时长排行
- 导入中心已新增 AI 转课表 Prompt 弹窗
- 学习记录页已切换为轻量 SVG / CSS 图表
- 已增加全局运行状态面板与自动健康轮询
- AI 工作区已支持 DeepSeek 双模型诊断、示例填充、JSON 复制、日志导出与重试草稿回填
- 设置页已新增 `云同步` 卡片，侧边栏显示同步状态，顶栏“同步数据”可触发本地 `/api/sync/run`
- 已验证 `npm test`、`npm run build`、`npm run tauri:build`

默认后端地址：

```text
http://127.0.0.1:8000
```

## 目录说明

```text
schedule_frontend/
├─ public/        # 静态资源与导入模板
├─ src/
│  ├─ api/        # 接口请求封装
│  ├─ components/ # 复用组件
│  ├─ config/     # 应用常量
│  ├─ layouts/    # 页面布局
│  ├─ pages/      # 页面级组件
│  ├─ router/     # 路由
│  ├─ stores/     # Pinia 状态管理
│  ├─ styles/     # 全局样式
│  ├─ types/      # 类型定义
│  └─ utils/      # 工具函数
├─ src-tauri/
├─ package.json
├─ vite.config.ts
└─ README.md
```

## 已实现页面

- `TodayPage`
  - 今日任务列表、AI 快速输入、计时面板、刷新今日模板任务、无计时完成补录时长、长期任务来源标识
- `LongTermTasksPage`
  - 长期目标列表、截止提醒、进度看板、子任务 CRUD、子任务生成今日任务
- `TaskTemplatesPage`
  - 模板搜索、分页、启停、CRUD
- `SchedulePage`
  - 时间线、事件管理、课程实例、冲突提醒、AI 规划
- `StudyRecordsPage`
  - 快捷时间范围、统计卡片、按学习科目统计、科目时长排行、轻量 SVG / CSS 图表、JSON/CSV 导出
- `ImportPage`
  - 课程 JSON 校验、模板下载、本地文件选择、AI 转课表 Prompt、导入批次管理
- `SettingsPage`
  - 基础设置、DeepSeek 默认 AI 配置、云同步配置、原始设置 JSON 视图
- `FocusModePage`
  - 沉浸式专注模式
- `AiWorkspacePage`
  - AI 连接诊断、自然语言解析、智能规划、AI 日志与重试

## AI 默认路线

前端当前默认以 DeepSeek 作为一等入口：

- Provider：`deepseek`
- Base URL：`https://api.deepseek.com/v1`
- 聊天 / 解析模型：`deepseek-chat`
- 规划 / 推理模型：`deepseek-reasoner`

设置页中的 AI 配置面板提供 3 组预设：

- `DeepSeek 官方`
- `OpenAI 兼容`
- `本地兼容服务`

AI 工作区会分别显示当前 `parse` 与 `plan` 实际使用的模型，避免误以为两处共用同一个模型。

# 一键启动

如果你只是想启动整个项目进行开发，不需要分别手动开后端和前端。

回到项目根目录后，直接双击：

- `start-dev.bat`

或者执行：

```powershell
cd d:\apps\schedule
.\start-dev.ps1
```

## 首次运行会发生什么

根目录启动器会自动：

1. 创建后端 `.venv`
2. 安装后端依赖
3. 启动 FastAPI
4. 检查后端健康接口
5. 安装前端依赖
6. 自动选择 Tauri 或 Web 模式启动前端

## 如果没有 Rust

如果机器没有 Rust / Cargo，启动器会自动降级为：

```bash
npm run dev
```

如果 Rust 环境可用，则会优先走：

```bash
npm run tauri:dev
```

## 如何停止

回到项目根目录后，执行：

```powershell
cd d:\apps\schedule
.\stop-dev.ps1
```

或者双击：

- `stop-dev.bat`

## 单独启动前端

Web 模式：

```bash
cd d:\apps\schedule\schedule_frontend
npm install
npm run dev
```

Tauri 模式：

```bash
cd d:\apps\schedule\schedule_frontend
npm install
npm run tauri:dev
```

## Tauri 桌面验证

当前本机已完成：

- `cargo -V`
- `rustc -V`
- `npm run tauri:build`
- 根启动器自动进入 `Tauri` 模式

当前有效的安装包输出：

```text
src-tauri/target/release/bundle/nsis/日程安排_0.3.0_x64-setup.exe
```

## 构建

Web 构建：

```bash
cd d:\apps\schedule\schedule_frontend
npm run build
```

Tauri 构建：

```bash
cd d:\apps\schedule\schedule_frontend
npm run tauri:build
```

## 近期升级说明

- `vite.config.ts`
  - 已启用 `unplugin-vue-components` 和 `ElementPlusResolver`
  - Element Plus 组件与指令改为按需引入
  - `vue-vendor` 与 `element-plus-icons` 已拆分为独立 chunk
- `src/components/study/StudyChartsPanel.vue`
  - 学习记录页图表改为原生轻量实现，已移除 ECharts 依赖
- `src/components/tasks/TaskCompletionDialog.vue`
  - 支持无计时完成任务时补录实际时长
- `src/pages/LongTermTasksPage.vue`
  - 支持长期任务看板、子任务拆解、截止提醒、页面级错误提示和生成今日任务
- `src/api/longTermTasks.ts`
  - 封装长期任务与子任务 API
- `src/components/imports/CourseImportPromptDialog.vue`
  - 支持复制给外部 AI 的课表转 JSON Prompt
- `src/router/index.ts`
  - 路由改为懒加载
  - 页面标题会自动同步为 `页面名 - 日程安排`
- `src/layouts/AppLayout.vue`
  - 侧边栏增加运行模式、AI 状态、云同步状态、最近同步、健康检查信息
  - 后端健康检查与系统信息会自动轮询刷新
  - “新建日程”菜单已支持跳转创建长期任务
- `src/components/settings/SyncConfigPanel.vue`
  - 云同步配置入口，支持服务器地址、设备名、启用开关、登录/退出、手动同步、待上传和冲突摘要
- `src/stores/sync.ts`
  - 封装 `/api/sync/*`，管理同步状态、登录状态、同步结果和冲突列表
- `src/pages/AiWorkspacePage.vue`
  - 增加 DeepSeek 双模型诊断、parse / plan 示例填充
  - 增加结果 JSON 复制
  - 增加 AI 日志导出、输入复制、Context / Output 复制
  - 增加日志重试后自动滚动回对应工作区
- `src/styles/element-plus-services.css`
  - 单独承接消息提示相关样式，避免影响测试环境
- 当前构建结果
  - `npm run build` 已通过
  - `npm run tauri:build` 已通过
  - 安装包输出：`src-tauri/target/release/bundle/nsis/日程安排_0.3.0_x64-setup.exe`

## 修改后端地址

如需修改前端请求地址，在 `schedule_frontend` 根目录创建 `.env.local`：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 关键入口

- 统一请求层：`src/api/client.ts`
- AI 工作区：`src/pages/AiWorkspacePage.vue`
- 全局应用状态：`src/stores/app.ts`
- 运行时检测：`src/utils/runtime.ts`
- 复制 / 导出工具：`src/utils/share.ts`
- 页面刷新 / 导出事件：`src/utils/pageEvents.ts`
- Tauri 文件选择桥接：`src/utils/desktop.ts`
- Tauri 原生入口：`src-tauri/src/main.rs`
