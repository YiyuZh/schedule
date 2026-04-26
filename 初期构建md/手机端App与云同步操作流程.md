# 手机端 App 与云同步操作流程

## 1. 先说结论

你的想法可行，但需要调整成“本地优先 + 云端同步仓库”的架构：

- 电脑端继续保留本地数据库和本地 FastAPI 后端。
- 手机端不能直接运行当前 Python FastAPI 后端，应做一个移动端客户端，内部保存本地数据。
- 云服务器不负责 AI、规划、计时等业务逻辑，只负责账号、设备、同步记录、冲突版本和备份。
- 云服务器必须做账号系统；不同账号的数据必须通过 `user_id` 严格隔离。
- AI API 由用户在客户端自己配置，客户端直接调用 DeepSeek / OpenAI 兼容接口，不通过你的云服务器中转。
- 电脑端或手机端改了数据后，先写本地，再把变更推到云服务器；另一端定时或手动拉取云端变化。

最推荐路线：

1. 先做云同步服务。
2. 先让 Windows 桌面端能和云服务器同步。
3. 再做手机端 Web/PWA 版验证同步体验。
4. 最后用 Capacitor 或 Tauri iOS 打包成真正 iPhone App。

## 2. 必须理解的现实限制

### 2.1 iPhone App 不能只在 Windows 上完整完成

iOS 真机调试、签名、TestFlight 和 App Store 分发都依赖 Apple 开发生态。实际需要：

- 一台 Mac，或 macOS 云构建环境。
- Xcode。
- Apple ID。
- 如果要 TestFlight / App Store 分发，需要加入 Apple Developer Program。

Apple 官方分发入口：<https://developer.apple.com/distribute/>

### 2.2 当前桌面端架构不能原样搬到手机

当前桌面端是：

```text
Vue/Tauri 前端 -> 本地 FastAPI -> 本地 SQLite
```

手机端不能简单变成：

```text
iPhone 前端 -> iPhone 本地 FastAPI
```

原因是普通 iOS App 里不适合跑当前 Python 后端。移动端应该改为：

```text
iPhone App -> 移动端本地存储 -> 云同步服务
```

电脑端继续：

```text
Windows Tauri App -> 本地 FastAPI -> 本地 SQLite -> 云同步服务
```

### 2.3 AI 调用必须放在用户端

本项目的 AI 调用建议固定为“用户端自带 API Key”：

```text
Windows 桌面端
  用户在本地设置 DeepSeek/OpenAI Key
  本地 FastAPI 直接调用 AI Provider

iPhone App
  用户在 App 设置页配置 DeepSeek/OpenAI Key
  App 通过本机安全存储保存 Key
  App 直接调用 AI Provider

云同步服务器
  不保存 AI Key
  不代理 AI 请求
  不承担 AI 成本
```

这样做的好处：

- 你的 2 核 2G 云服务器不会被 AI 请求拖垮。
- 用户自己的 AI 额度由用户自己承担。
- 云端泄露风险更低，因为云端没有用户的 AI Key。
- 电脑端和手机端可以各自选择模型，例如 DeepSeek、OpenAI、OpenRouter 或本地兼容服务。

注意：

- 桌面端可以继续沿用现有本地 FastAPI AI 配置。
- iPhone App 应把 Key 存在 Keychain 或 Capacitor 安全存储插件中。
- Web/PWA 调试阶段可能遇到 AI Provider 的 CORS 限制；真实 iOS App 可以通过原生 HTTP 插件调用，避免浏览器跨域限制。

## 3. 手机端技术路线选择

### 推荐路线 A：Vue 3 + Capacitor

适合你现在这种情况。

优点：

- 可以继续使用 Vue 3 / TypeScript。
- 能把移动端打包成 iOS App。
- iOS 原生能力通过插件接入。
- 比重新写 SwiftUI 更省时间。

官方说明：Capacitor 提供 native iOS runtime，并允许 JavaScript 与 Swift/Objective-C 原生代码通信。  
参考：<https://capacitorjs.com/docs/ios>

适合第一版手机端功能：

- 今日任务
- 长期任务
- 学习记录
- 日程列表
- 设置云同步账号
- 后台或手动同步

### 可选路线 B：Tauri 2 iOS

Tauri 2 官方已经支持 Windows、macOS、Linux、Android、iOS 单代码库构建。  
参考：<https://tauri.app/>、<https://v2.tauri.app/blog/tauri-2-0-0-beta/>

优点：

- 和现在桌面端技术栈更接近。
- 理论上能复用更多 Tauri 结构。

风险：

- iOS 调试、插件和权限会比 Capacitor 更折腾。
- 当前项目已经有桌面 UI，直接一套界面适配手机会比较别扭。

建议：

- 第一版手机端不要优先走 Tauri iOS。
- 等云同步和移动端核心页面稳定后，再评估是否把手机端迁回 Tauri 多端。

### 不推荐第一版直接 SwiftUI 重写

SwiftUI 是最原生的 iOS 方案，但会导致：

- 重新写一套 UI。
- 重新写本地数据层。
- 重新写同步层。
- 和现有 Vue 前端复用度低。

除非以后明确要做长期商业化 App，否则第一版不推荐。

## 4. 推荐总体操作流程

### 阶段 0：准备条件

你需要准备：

- 一台 2 核 2G 云服务器。
- 一个域名，例如 `schedule.example.com`。
- HTTPS 证书，推荐用 Caddy 自动签发。
- 一个 Git 仓库。
- 后续 iOS 打包需要 Mac / Xcode / Apple Developer Program。

2 核 2G 服务器够用，前提是：

- 用户量先按个人或少量用户设计。
- 云端只做同步和存储。
- 不在服务器上跑 AI 大模型。
- 数据库先用 PostgreSQL 或 SQLite WAL，推荐 PostgreSQL。

### 阶段 1：先做云同步服务

新建服务目录：

```text
D:/apps/
├─ schedule/
└─ schedule_sync_server/
```

云端服务只做这些事：

- 用户注册 / 登录。
- Access Token / Refresh Token。
- 设备注册。
- 接收客户端变更。
- 返回其他设备的变更。
- 保存删除标记。
- 保存版本号。
- 提供备份导出。

不要把 AI 规划、计时逻辑、日程冲突检测全部搬到云端。

账号隔离必须从第一版就做：

- 每个用户有独立 `user_id`。
- 每条同步记录都必须带 `user_id`。
- 服务端不能信任客户端传入的 `user_id`，必须从登录 token 解析。
- 查询、推送、拉取、删除都必须附带 `where user_id = 当前登录用户`。
- 数据库唯一约束建议使用 `(user_id, entity_type, entity_id)`，不要只用 `(entity_type, entity_id)`。

### 阶段 2：先让 Windows 桌面端同步

先在现有本地 FastAPI 后端增加同步层：

```text
本地 SQLite
  -> 记录本地变更
  -> 推送到云服务器
  -> 拉取其他设备变化
  -> 合并回本地 SQLite
```

桌面端设置页新增：

- 云同步开关。
- 云服务器地址。
- 登录账号 / 退出登录。
- 当前设备名。
- 最近同步时间。
- 手动同步按钮。
- AI 配置仍留在本地设置中，不上传 `ai_api_key`。

第一版同步策略：

- 默认每 30 秒自动同步一次。
- 用户点击“同步数据”时立即同步。
- 离线时写本地同步队列。
- 恢复网络后自动补传。

### 阶段 3：做手机端最小可用版

建议先建：

```text
schedule/
└─ schedule_mobile/
```

手机端第一版页面只做核心：

- 登录 / 配置同步服务器
- AI API 配置
- 今日任务
- 长期任务
- 学习记录
- 日程列表
- 设置

不要第一版就做完整桌面端所有复杂页面。

手机端本地存储建议：

- PWA 验证阶段：IndexedDB。
- 真 App 阶段：Capacitor SQLite 插件或同等本地 SQLite 方案。

### 阶段 4：手机端接入同步

手机端也遵守同一套同步协议：

```text
手机本地数据 -> 手机同步队列 -> 云服务器 -> 电脑端拉取
电脑本地数据 -> 电脑同步队列 -> 云服务器 -> 手机端拉取
```

关键要求：

- 每条记录都有全局唯一 `sync_id`。
- 每台设备都有 `device_id`。
- 每条记录都有 `version`。
- 删除不是直接物理删除，而是上传 `deleted_at` 删除标记。

### 阶段 5：打包 iPhone App

如果使用 Capacitor：

```bash
npm install @capacitor/core @capacitor/cli @capacitor/ios
npx cap init
npx cap add ios
npm run build
npx cap sync ios
npx cap open ios
```

然后在 Xcode 中：

1. 选择开发者 Team。
2. 连接 iPhone 真机。
3. 调试运行。
4. Archive。
5. 通过 TestFlight 分发测试。
6. 稳定后提交 App Store。

如果使用 Tauri iOS：

```bash
npm run tauri ios init
npm run tauri ios dev
npm run tauri ios build
```

但第一版仍建议优先 Capacitor。

## 5. 真实使用时的数据流

### 场景 A：电脑完成一个任务

1. 电脑端本地 FastAPI 把任务状态改为 completed。
2. 本地 SQLite 记录一条同步变更。
3. 同步引擎把变更推到云服务器。
4. 手机端下次同步时拉取该变更。
5. 手机端本地任务状态变为 completed。

### 场景 B：手机新增一个长期任务子任务

1. 手机端写入手机本地数据库。
2. 手机端把新增记录推送到云服务器。
3. 电脑端拉取后写入本地 SQLite。
4. 电脑端长期任务页出现该子任务。

### 场景 C：电脑和手机同时编辑同一个任务

第一版建议采用简单策略：

- 若两个设备改的是不同字段，尽量合并。
- 若两个设备改的是同一字段，用 `updated_at` 晚的一方覆盖。
- 若涉及完成状态，优先保留 completed，不轻易回退到 pending。
- 冲突记录写入本地 `sync_conflicts`，以后可做冲突详情页面。

## 6. 哪些数据应该同步

应该同步：

- 固定任务模板
- 每日任务
- 长期任务
- 长期子任务
- 单次事件
- 课程
- 学习记录
- 课程导入结果
- 非敏感设置

暂时不要同步：

- 当前正在运行的 `timer_state`
- AI API Key 明文
- AI API Key 密文
- 本地日志文件
- Tauri 窗口状态
- 本地数据库文件整体

AI 非敏感配置可以同步：

- `ai_provider`
- `ai_base_url`
- `ai_model_name`
- `ai_plan_model_name`

可以同步。

但 `ai_api_key` 不要同步，哪怕加密后也不建议第一版同步。每台设备由用户单独配置自己的 Key。

## 7. 账号设计与用户数据隔离

第一版至少需要账号系统，否则手机和电脑同步会变成“所有人共用一个数据池”，这是不可接受的。

### 7.1 用户账号

建议最小字段：

```text
users
- id
- email
- password_hash
- display_name
- is_active
- created_at
- updated_at
```

登录方式第一版建议只做：

- 邮箱 + 密码。
- 暂不做微信 / Apple 登录。
- 暂不做手机号验证码。

### 7.2 设备

一个账号可以绑定多台设备：

```text
devices
- id
- user_id
- device_id
- device_name
- device_type: desktop / ios / web
- last_seen_at
- created_at
- updated_at
```

典型关系：

```text
张三账号
  - Windows 电脑
  - iPhone
  - 备用浏览器 PWA

李四账号
  - Windows 电脑
  - iPhone
```

张三和李四的数据完全隔离。

### 7.3 登录态

建议：

- Access Token 有效期：30 分钟到 2 小时。
- Refresh Token 有效期：30 天。
- 每个 Refresh Token 绑定设备。
- 用户退出登录时，只清除当前设备 token，不影响其他设备。

### 7.4 数据隔离规则

所有云端数据表都必须遵守：

```text
读数据：where user_id = 当前登录用户
写数据：user_id 从 token 中取，不允许客户端传
删数据：只能删除当前 user_id 下的数据
同步：pull / push 都只能处理当前 user_id 的记录
```

如果以后做管理员后台，也只能看统计，不默认开放查看用户明细数据。

## 8. 服务器容量预估

你的 2 核 2G 云服务器如果只做账号和同步，不跑 AI，不做复杂报表，个人项目和小规模用户是够的。

### 8.1 保守估算

推荐按这个规模设计第一版：

```text
注册用户：100 - 300 人
日活用户：30 - 100 人
同时在线使用：10 - 30 人
瞬时同步请求：10 - 30 RPS
数据量：几十万条 sync_records 以内
```

这个规模下，FastAPI + PostgreSQL + Caddy 在 2 核 2G 上通常可以稳定工作。

### 8.2 乐观估算

如果代码写得比较轻、索引完整、同步 payload 不大，可以尝试：

```text
注册用户：500 - 1000 人
日活用户：100 - 300 人
同时在线使用：30 - 80 人
瞬时同步请求：30 - 80 RPS
数据量：100 万条 sync_records 左右
```

但这个阶段已经需要观察：

- CPU 使用率。
- PostgreSQL 内存。
- 慢查询。
- 磁盘 IO。
- 同步 payload 大小。
- 备份耗时。

### 8.3 按 30 秒自动同步粗算

假设：

- 100 个日活用户。
- 每人 2 台设备。
- 每台设备 30 秒同步一次。

请求量大约是：

```text
100 用户 * 2 设备 * 2 请求(push + pull) / 30 秒
= 约 13.3 RPS
```

这对 2 核 2G 来说一般没问题。

如果变成：

```text
300 用户 * 2 设备 * 2 请求 / 30 秒
= 约 40 RPS
```

也可能能跑，但要依赖数据库索引、连接池、payload 控制和服务器质量。

### 8.4 AI 不影响服务器容量

因为 AI 由客户端直接调用 Provider：

- 用户自己的 DeepSeek Key 由用户设备保存。
- 电脑端本地 FastAPI 调 AI。
- iPhone App 直接调 AI。
- 云服务器不代理 AI 请求。

所以 AI 使用量不会明显增加云服务器 CPU 和内存压力。

如果以后改成服务器代理 AI，那 2 核 2G 会很快变成瓶颈，而且还会带来用户 Key 托管、费用滥用、风控和隐私问题。

### 8.5 什么时候需要升级服务器

出现这些情况再升级：

- CPU 长期超过 70%。
- 内存长期超过 80%。
- PostgreSQL 频繁 OOM 或连接耗尽。
- 同步接口 P95 延迟超过 500ms。
- 用户数量超过 300 日活。
- `sync_records` 超过 100 万且查询变慢。

推荐下一档：

```text
2 核 4G：更稳，适合 300 - 800 日活以内的小应用
4 核 8G：适合开始公开推广后的早期阶段
```

## 9. 你实际应该怎么开始

按这个顺序做，别一口气同时做 iOS 和同步，不然容易乱：

1. 先确认云服务器可以跑 Docker。
2. 给服务器绑定域名和 HTTPS。
3. 使用同级独立项目 `D:/apps/schedule_sync_server` 维护云同步服务端。
4. 先做账号注册 / 登录 / 设备注册。
5. 做最小同步 API。
6. 桌面端接入同步。
7. 用两个账号测试数据隔离。
8. 用两份本地数据库模拟“电脑 A / 电脑 B”同步。
9. 同步稳定后，再做 `schedule_mobile`。
10. 先用浏览器打开手机 Web/PWA 测试。
11. 最后上 Capacitor / Xcode / TestFlight。

## 10. 建议的第一版验收标准

第一版不要追求完美，只要做到：

- 用户 A 看不到用户 B 的任何任务、学习记录、长期任务。
- 同一账号下电脑和手机能同步。
- 电脑端新增任务，手机端 30 秒内能看到。
- 手机端完成任务，电脑端 30 秒内能看到。
- 离线新增任务，联网后能自动同步。
- 删除任务后另一端也能删除或隐藏。
- 学习记录能同步。
- 长期任务和子任务能同步。
- 同一个账号下多设备不会互相覆盖数据库。
- 用户可以在每台设备单独配置 AI API Key。
- 云服务器数据库里没有保存 `ai_api_key`。

## 11. 一句话路线图

先做“云同步协议 + 桌面端同步”，再做“手机 Web/PWA”，最后打包“iPhone App”。这样风险最小，也最符合你“云服务器只存数据，功能在客户端实现”的目标。
