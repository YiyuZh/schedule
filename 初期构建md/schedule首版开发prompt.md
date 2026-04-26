你现在是这个项目的后端主开发工程师。请直接开始为项目生成第一版可运行后端，不要只给方案说明。目标是：在本地 Windows 10 环境下，为一个“日程安排”桌面应用提供 FastAPI 后端服务，供 Vue3 + Tauri 前端调用。

====================
一、项目背景
====================

项目名称：日程安排

这是一个本地优先的个人日程与学习管理工具。前端技术栈已经确定为：
- Vue 3
- Tauri

你现在只负责后端：
- FastAPI
- SQLite
- SQLAlchemy 2.x
- Pydantic v2

该后端运行在本地，默认监听：
- http://127.0.0.1:8000

后端职责：
1. 提供 REST API
2. 管理 SQLite 数据库
3. 实现每日固定任务刷新
4. 实现任务、事件、课程、学习记录 CRUD
5. 实现学习计时逻辑
6. 实现学习统计逻辑
7. 预留 AI 解析与 AI 规划接口
8. 提供课表 JSON 导入能力

注意：
- 这是本地桌面应用后端，不是公网 SaaS
- 代码必须可运行
- 结构必须清晰，可继续扩展
- 不要偷懒只生成单文件 demo
- 直接产出正式项目骨架和核心实现

====================
二、开发目标
====================

请你完成一个可运行的第一版后端 MVP，要求做到：

1. 能正常启动 FastAPI 服务
2. 能自动初始化 SQLite 数据库
3. 能提供基础健康检查接口
4. 能完成固定任务模板 CRUD
5. 能完成每日任务 CRUD
6. 能完成学习计时
7. 能完成学习记录查询与统计
8. 能完成单次事件 CRUD
9. 能完成课程 JSON 导入
10. 能为 AI 模块预留接口和服务层
11. 项目结构清晰，后续方便继续开发

====================
三、技术强约束
====================

必须遵守以下技术要求：

1. 使用 Python 3.11+
2. 使用 FastAPI
3. 使用 Pydantic v2
4. 使用 SQLAlchemy 2.x ORM 风格
5. 使用 SQLite
6. 使用 uvicorn 作为启动服务
7. 使用 requirements.txt 管理依赖
8. 使用模块化目录，不允许把全部逻辑堆在一个文件
9. 使用 SQLAlchemy session 依赖注入
10. 使用 FastAPI APIRouter 分模块组织接口
11. 使用 response_model 约束接口响应
12. 使用统一响应格式
13. 使用 lifespan 处理应用启动初始化，例如建表、基础设置初始化
14. 对输入做明确校验，避免脏数据直接入库
15. 尽量使用类型注解
16. 代码可读性优先，不要炫技
17. 不要引入过重依赖
18. 先不要做鉴权登录系统
19. 先不要做异步任务队列
20. 先不要做云同步

====================
四、项目目录要求
====================

请按下面这个结构生成项目，允许合理补充文件，但不要偏离：

schedule_backend/
├─ app/
│  ├─ main.py
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ database.py
│  │  └─ response.py
│  ├─ models/
│  │  ├─ base.py
│  │  ├─ app_setting.py
│  │  ├─ task_template.py
│  │  ├─ daily_task.py
│  │  ├─ event.py
│  │  ├─ course.py
│  │  ├─ study_session.py
│  │  ├─ timer_state.py
│  │  ├─ ai_log.py
│  │  └─ import_batch.py
│  ├─ schemas/
│  │  ├─ common.py
│  │  ├─ settings.py
│  │  ├─ task_template.py
│  │  ├─ daily_task.py
│  │  ├─ event.py
│  │  ├─ course.py
│  │  ├─ study_session.py
│  │  ├─ timer.py
│  │  ├─ ai.py
│  │  └─ import_schema.py
│  ├─ api/
│  │  ├─ deps.py
│  │  ├─ health.py
│  │  ├─ settings.py
│  │  ├─ task_templates.py
│  │  ├─ daily_tasks.py
│  │  ├─ events.py
│  │  ├─ courses.py
│  │  ├─ timer.py
│  │  ├─ study_sessions.py
│  │  ├─ study_stats.py
│  │  ├─ ai.py
│  │  └─ imports.py
│  ├─ services/
│  │  ├─ settings_service.py
│  │  ├─ task_template_service.py
│  │  ├─ daily_task_service.py
│  │  ├─ event_service.py
│  │  ├─ course_service.py
│  │  ├─ timer_service.py
│  │  ├─ study_service.py
│  │  ├─ stats_service.py
│  │  ├─ ai_service.py
│  │  └─ import_service.py
│  ├─ utils/
│  │  ├─ datetime_utils.py
│  │  ├─ validators.py
│  │  └─ json_utils.py
│  └─ seed/
│     └─ init_settings.py
├─ data/
│  └─ app.db
├─ requirements.txt
├─ README.md
└─ run.py

====================
五、数据库表要求
====================

请基于以下表结构生成 SQLAlchemy 模型。字段名尽量与下方一致。

1. app_settings
- id
- setting_key (unique)
- setting_value
- value_type
- description
- created_at
- updated_at

2. task_templates
- id
- title
- category
- is_study
- default_duration_minutes
- default_start_time
- default_end_time
- time_preference
- priority
- is_enabled
- inherit_unfinished
- notes
- created_at
- updated_at

3. daily_tasks
- id
- template_id (nullable, FK)
- title
- category
- is_study
- task_date
- start_time
- end_time
- planned_duration_minutes
- actual_duration_minutes
- priority
- status
- source
- sort_order
- notes
- completed_at
- created_at
- updated_at
- unique(template_id, task_date)

4. events
- id
- title
- category
- event_date
- start_time
- end_time
- location
- priority
- status
- source
- linked_task_id (nullable, FK)
- notes
- created_at
- updated_at

5. courses
- id
- batch_id (nullable, FK)
- course_name
- weekday
- start_time
- end_time
- location
- teacher
- term_name
- term_start_date
- term_end_date
- week_list_json
- color
- notes
- created_at
- updated_at

6. study_sessions
- id
- task_id (nullable, FK)
- task_title_snapshot
- category_snapshot
- session_date
- start_at
- end_at
- duration_minutes
- source
- note
- created_at

7. timer_state
- id
- task_id (FK)
- started_at
- paused_at
- accumulated_seconds
- status
- created_at
- updated_at

8. ai_logs
- id
- log_type
- provider
- model_name
- user_input
- context_json
- ai_output_json
- parsed_success
- applied_success
- error_message
- created_at

9. import_batches
- id
- import_type
- file_name
- raw_content
- parsed_count
- status
- error_message
- created_at

要求：
- created_at / updated_at 统一处理
- 合理添加索引
- 合理添加约束
- 布尔字段用 SQLite 兼容方式处理
- 时间日期字段先使用字符串存储，保持和前端约定一致
- week_list_json 使用 JSON 字符串存储

====================
六、统一响应格式
====================

所有接口统一返回：

{
  "code": 0,
  "message": "success",
  "data": ...
}

失败时：
{
  "code": 非0,
  "message": "错误信息",
  "data": null
}

请封装统一响应工具方法，不要在每个接口里手写重复结构。

====================
七、第一版必须实现的 API
====================

请优先实现以下接口，确保可以跑通。

【系统】
1. GET /api/health
2. GET /api/system/info

【设置】
3. GET /api/settings
4. GET /api/settings/{key}
5. PUT /api/settings/{key}
6. PUT /api/settings

【固定任务模板】
7. GET /api/task-templates
8. GET /api/task-templates/{template_id}
9. POST /api/task-templates
10. PUT /api/task-templates/{template_id}
11. PATCH /api/task-templates/{template_id}
12. DELETE /api/task-templates/{template_id}
13. POST /api/task-templates/{template_id}/toggle
14. POST /api/task-templates/refresh-today

【每日任务】
15. GET /api/daily-tasks
16. GET /api/daily-tasks/{task_id}
17. POST /api/daily-tasks
18. PUT /api/daily-tasks/{task_id}
19. PATCH /api/daily-tasks/{task_id}
20. DELETE /api/daily-tasks/{task_id}
21. POST /api/daily-tasks/{task_id}/status
22. POST /api/daily-tasks/{task_id}/complete
23. POST /api/daily-tasks/{task_id}/uncomplete
24. POST /api/daily-tasks/reorder
25. POST /api/daily-tasks/inherit-unfinished
26. GET /api/daily-tasks/summary

【单次事件】
27. GET /api/events
28. GET /api/events/{event_id}
29. POST /api/events
30. PUT /api/events/{event_id}
31. PATCH /api/events/{event_id}
32. DELETE /api/events/{event_id}
33. POST /api/events/{event_id}/status
34. POST /api/events/check-conflict
35. GET /api/events/timeline

【课程与导入】
36. GET /api/courses
37. GET /api/courses/{course_id}
38. POST /api/courses
39. PUT /api/courses/{course_id}
40. DELETE /api/courses/{course_id}
41. GET /api/courses/day-view
42. GET /api/courses/week-view
43. GET /api/import-batches
44. GET /api/import-batches/{batch_id}
45. POST /api/import/courses/validate
46. POST /api/import/courses/json
47. DELETE /api/import-batches/{batch_id}/courses

【学习计时】
48. GET /api/timer/current
49. POST /api/timer/start
50. POST /api/timer/pause
51. POST /api/timer/resume
52. POST /api/timer/stop
53. POST /api/timer/discard
54. POST /api/timer/switch

【学习记录与统计】
55. GET /api/study-sessions
56. GET /api/study-sessions/{session_id}
57. POST /api/study-sessions
58. PUT /api/study-sessions/{session_id}
59. DELETE /api/study-sessions/{session_id}
60. GET /api/study-stats/overview
61. GET /api/study-stats/by-category
62. GET /api/study-stats/by-task
63. GET /api/study-stats/by-day
64. GET /api/study-sessions/export

【AI 预留接口】
65. GET /api/ai/config
66. PUT /api/ai/config
67. POST /api/ai/test-connection
68. POST /api/ai/parse
69. POST /api/ai/parse/apply
70. POST /api/ai/plan
71. POST /api/ai/plan/apply
72. GET /api/ai/logs
73. GET /api/ai/logs/{log_id}
74. DELETE /api/ai/logs/{log_id}

注意：
- AI 接口第一版可以先做“伪实现”或 mock 实现
- 但接口、schema、service 层要先搭好
- 以后方便接 DeepSeek / OpenAI 兼容接口

====================
八、关键业务规则
====================

必须实现以下业务规则：

1. 每日固定任务刷新
- 根据 task_templates 生成今日 daily_tasks
- 同一个 template_id 在同一天只能生成一条
- 已生成则跳过

2. 未完成任务继承
- 支持把昨天未完成任务复制到今天
- 不要修改原任务，而是新建今日任务

3. 学习计时
- 同一时间只能有一个 timer_state 处于有效状态
- start 时如果已有活动计时，应返回明确错误
- stop 时自动生成一条 study_sessions
- discard 时终止计时但不生成学习记录

4. 学习统计
- 支持按日期区间汇总学习时长
- 支持按分类统计
- 支持按任务统计
- 支持按日统计

5. 事件冲突检测
- 检查 events
- 检查带时间的 daily_tasks
- 检查 courses 动态展开后的实例
- 返回冲突对象列表

6. 课程导入
- 支持课程 JSON 校验
- 支持导入批次记录
- 支持按 batch 删除课程

7. AI 模块
- 第一版先做好 service 抽象层
- parse / plan / apply 先做基础占位实现
- 保证以后接真实模型时改动最小

====================
九、Pydantic Schema 要求
====================

请为每个模块分别设计：
- Create schema
- Update schema
- Patch schema
- Read schema
- List item schema
- Query 参数 schema（适合的就做）

要求：
1. 字段校验清晰
2. 尽量避免过度宽松的自动转换
3. 枚举字段做限制，例如：
   - task status
   - source
   - log_type
   - timer status
4. 合理使用默认值
5. 导出给前端的 schema 尽量稳定

====================
十、服务层要求
====================

不要把业务逻辑直接堆在路由函数里。

每个模块都应有对应 service，至少做到：
- 路由层：只做请求解析、调用 service、返回结果
- service 层：负责业务逻辑
- model 层：数据库模型
- schema 层：输入输出校验

重点把以下逻辑放到 service：
- 刷新今日模板任务
- 继承未完成任务
- 计时开始/暂停/恢复/停止
- 统计聚合
- 事件冲突检测
- 课表导入校验与写入
- AI mock 解析与规划

====================
十一、实现细节要求
====================

1. 在 README.md 写清楚：
- 如何安装依赖
- 如何运行
- 默认数据库位置
- 目录说明
- 已实现接口模块

2. 提供 requirements.txt
3. 提供 run.py，支持直接启动
4. main.py 中注册所有 router
5. 使用 /api 作为统一前缀
6. 适度补充基础异常处理
7. 尽量让接口错误信息可读
8. 不要为了省事省略核心字段
9. 不要用伪代码代替正式代码
10. 不要只返回 pass 或 TODO
11. mock 的 AI 接口也要返回合法结构
12. 导出接口至少支持 JSON；CSV 可先实现基础版
13. 对日期、时间字符串做基础格式校验
14. 所有代码要能被正常 import，不要循环依赖
15. 保证 Windows 本地运行友好

====================
十二、输出方式要求
====================

请不要只给一堆解释。请按下面顺序直接输出结果：

1. 先给出完整项目目录树
2. 再逐个文件输出代码
3. 每个文件都用清晰标题标识，例如：
   === file: app/main.py ===
4. 所有关键文件都要给出完整内容
5. 不要省略 imports
6. 不要只展示部分片段
7. 生成的代码应能直接复制到本地形成项目
8. 如果内容过长，可以分批输出，但必须保持连续、可拼接

====================
十三、开发优先级
====================

请按下面顺序优先完成：

第一优先级：
- 数据库基础设施
- models
- schemas
- health/settings
- task_templates
- daily_tasks

第二优先级：
- timer
- study_sessions
- study_stats

第三优先级：
- events
- conflict detection
- courses
- imports

第四优先级：
- ai mock module
- ai logs
- system info

====================
十四、代码风格
====================

1. 简洁、稳健、可维护
2. 命名统一
3. 不要无意义抽象
4. 不要过度工程化
5. 先保证可用，再考虑复杂优化
6. 适度注释关键逻辑
7. 对复杂业务逻辑写清楚注释

====================
十五、最终目标
====================

你最终交付的不是“示例代码”，而是：
- 一个结构完整的 FastAPI 项目骨架
- 一套基本可运行的后端代码
- 一份本地 SQLite 数据驱动的 MVP 后端
- 后续可继续接前端、接 AI、继续扩展

现在直接开始输出项目代码。