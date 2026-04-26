《日程安排》API 接口清单 V1
一、接口设计原则
1. 技术前提
后端框架：FastAPI
接口风格：RESTful 为主
数据格式：JSON
本地运行：默认 http://127.0.0.1:8000
2. 返回格式统一规范

建议所有接口统一返回：

{
  "code": 0,
  "message": "success",
  "data": {}
}
字段说明
code: 0 表示成功，非 0 表示失败
message: 接口描述信息
data: 具体返回数据
失败示例
{
  "code": 4001,
  "message": "task not found",
  "data": null
}
3. 时间字段建议

统一约定：

日期：YYYY-MM-DD
时间：HH:MM
日期时间：YYYY-MM-DD HH:MM:SS
4. 接口模块划分

本项目建议分为以下 9 个模块：

系统与健康检查
设置管理
固定任务模板
每日任务实例
单次事件
课程与课表导入
学习计时
学习记录与统计
AI 解析与 AI 规划
二、系统与健康检查
1. 健康检查
接口

GET /api/health

用途

前端检查 FastAPI 服务是否正常运行。

返回示例
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "ok"
  }
}
2. 获取应用基础信息
接口

GET /api/system/info

用途

获取版本、数据库状态、当前时间、AI 启用状态等。

返回字段建议
app_name
app_version
database_status
ai_enabled
current_time
三、设置管理
1. 获取全部设置
接口

GET /api/settings

用途

读取全部系统设置。

返回示例
{
  "code": 0,
  "message": "success",
  "data": {
    "settings": [
      {
        "key": "default_task_duration",
        "value": 30,
        "value_type": "int"
      },
      {
        "key": "ai_enabled",
        "value": true,
        "value_type": "bool"
      }
    ]
  }
}
2. 获取单个设置
接口

GET /api/settings/{key}

用途

按 key 获取某个设置项。

3. 新增或更新设置
接口

PUT /api/settings/{key}

请求体
{
  "value": "http://127.0.0.1:11434/v1",
  "value_type": "string",
  "description": "AI base url"
}
用途

保存单个设置项。

4. 批量更新设置
接口

PUT /api/settings

请求体
{
  "items": [
    {
      "key": "ai_enabled",
      "value": true,
      "value_type": "bool"
    },
    {
      "key": "default_task_duration",
      "value": 45,
      "value_type": "int"
    }
  ]
}
5. 删除设置
接口

DELETE /api/settings/{key}

用途

删除某个设置项。

四、固定任务模板接口
1. 获取固定任务模板列表
接口

GET /api/task-templates

查询参数
enabled: 可选，0/1
category: 可选
is_study: 可选，0/1
用途

获取固定任务模板列表。

2. 获取单个固定任务模板详情
接口

GET /api/task-templates/{template_id}

3. 创建固定任务模板
接口

POST /api/task-templates

请求体
{
  "title": "英语学习",
  "category": "学习",
  "is_study": true,
  "default_duration_minutes": 60,
  "default_start_time": "20:00",
  "default_end_time": "21:00",
  "time_preference": "evening",
  "priority": 2,
  "is_enabled": true,
  "inherit_unfinished": true,
  "notes": "每日固定任务"
}
4. 更新固定任务模板
接口

PUT /api/task-templates/{template_id}

用途

全量更新模板。

5. 部分更新固定任务模板
接口

PATCH /api/task-templates/{template_id}

用途

只改部分字段，比如启用状态、标题、时长。

6. 删除固定任务模板
接口

DELETE /api/task-templates/{template_id}

说明

建议逻辑删除或物理删除都可以。
如果物理删除，daily_tasks.template_id 应设为 NULL。

7. 启用/停用固定任务模板
接口

POST /api/task-templates/{template_id}/toggle

请求体
{
  "is_enabled": false
}
8. 手动触发今日模板刷新
接口

POST /api/task-templates/refresh-today

用途

根据模板生成今日任务实例。

请求体
{
  "date": "2026-04-23"
}
返回字段建议
created_count
skipped_count
task_ids
五、每日任务实例接口
1. 获取某日任务列表
接口

GET /api/daily-tasks

查询参数
date: 必填，YYYY-MM-DD
status: 可选
category: 可选
is_study: 可选
source: 可选
示例

GET /api/daily-tasks?date=2026-04-23

2. 获取单个任务详情
接口

GET /api/daily-tasks/{task_id}

3. 创建任务
接口

POST /api/daily-tasks

请求体
{
  "template_id": null,
  "title": "写作业",
  "category": "学习",
  "is_study": true,
  "task_date": "2026-04-23",
  "start_time": null,
  "end_time": null,
  "planned_duration_minutes": 90,
  "priority": 2,
  "status": "pending",
  "source": "manual",
  "sort_order": 10,
  "notes": ""
}
4. 更新任务
接口

PUT /api/daily-tasks/{task_id}

用途

全量更新任务。

5. 部分更新任务
接口

PATCH /api/daily-tasks/{task_id}

用途

修改标题、时间、优先级、备注等部分字段。

6. 删除任务
接口

DELETE /api/daily-tasks/{task_id}

7. 修改任务状态
接口

POST /api/daily-tasks/{task_id}/status

请求体
{
  "status": "completed"
}
状态值
pending
running
completed
skipped
8. 勾选完成任务
接口

POST /api/daily-tasks/{task_id}/complete

用途

快速标记完成。

9. 取消完成任务
接口

POST /api/daily-tasks/{task_id}/uncomplete

10. 任务排序调整
接口

POST /api/daily-tasks/reorder

请求体
{
  "date": "2026-04-23",
  "items": [
    { "id": 3, "sort_order": 1 },
    { "id": 5, "sort_order": 2 },
    { "id": 8, "sort_order": 3 }
  ]
}
11. 继承昨日未完成任务
接口

POST /api/daily-tasks/inherit-unfinished

请求体
{
  "from_date": "2026-04-22",
  "to_date": "2026-04-23"
}
12. 获取今日任务汇总信息
接口

GET /api/daily-tasks/summary

查询参数
date: 必填
返回字段建议
total_count
completed_count
skipped_count
pending_count
completion_rate
study_task_count
六、单次事件接口
1. 获取事件列表
接口

GET /api/events

查询参数
date: 可选
start_date: 可选
end_date: 可选
category: 可选
status: 可选
2. 获取单个事件详情
接口

GET /api/events/{event_id}

3. 创建事件
接口

POST /api/events

请求体
{
  "title": "开会",
  "category": "会议",
  "event_date": "2026-04-24",
  "start_time": "10:00",
  "end_time": "11:00",
  "location": "会议室A",
  "priority": 1,
  "status": "scheduled",
  "source": "manual",
  "linked_task_id": null,
  "notes": ""
}
4. 更新事件
接口

PUT /api/events/{event_id}

5. 部分更新事件
接口

PATCH /api/events/{event_id}

6. 删除事件
接口

DELETE /api/events/{event_id}

7. 修改事件状态
接口

POST /api/events/{event_id}/status

请求体
{
  "status": "completed"
}
状态值
scheduled
completed
cancelled
8. 检查时间冲突
接口

POST /api/events/check-conflict

请求体
{
  "event_date": "2026-04-24",
  "start_time": "10:00",
  "end_time": "11:00",
  "exclude_event_id": null
}
返回字段建议
has_conflict
conflict_events
conflict_tasks
conflict_courses
9. 获取某日时间线数据
接口

GET /api/events/timeline

查询参数
date: 必填
用途

给日程页或首页时间线组件统一返回：

事件
课程实例
已安排时间的任务
七、课程与课表导入接口
1. 获取课程规则列表
接口

GET /api/courses

查询参数
term_name: 可选
weekday: 可选
batch_id: 可选
2. 获取单个课程规则详情
接口

GET /api/courses/{course_id}

3. 创建课程规则
接口

POST /api/courses

说明

一般不建议前端手敲，但保留接口。

4. 更新课程规则
接口

PUT /api/courses/{course_id}

5. 删除课程规则
接口

DELETE /api/courses/{course_id}

6. 获取某日课程实例
接口

GET /api/courses/day-view

查询参数
date: 必填
用途

根据 courses 规则动态计算某天课程安排。

7. 获取某周课程实例
接口

GET /api/courses/week-view

查询参数
start_date: 必填
end_date: 必填
8. 获取导入批次列表
接口

GET /api/import-batches

9. 获取单个导入批次详情
接口

GET /api/import-batches/{batch_id}

10. 导入课表 JSON
接口

POST /api/import/courses/json

请求体
{
  "semester_name": "2026春季学期",
  "term_start_date": "2026-02-24",
  "term_end_date": "2026-07-05",
  "courses": [
    {
      "course_name": "大学英语",
      "weekday": 1,
      "start_time": "08:00",
      "end_time": "09:35",
      "location": "A201",
      "teacher": "张老师",
      "weeks": [1,2,3,4,5,6,7,8,9,10]
    }
  ]
}
返回字段建议
batch_id
parsed_count
preview_items
11. 预校验课表 JSON
接口

POST /api/import/courses/validate

用途

只校验，不落库。

12. 删除某次导入的课程
接口

DELETE /api/import-batches/{batch_id}/courses

用途

一键删除这次导入生成的全部课程。

八、学习计时接口
1. 获取当前计时状态
接口

GET /api/timer/current

返回字段建议
has_active_timer
task_id
task_title
started_at
paused_at
accumulated_seconds
status
2. 开始计时
接口

POST /api/timer/start

请求体
{
  "task_id": 12
}
业务规则
同时只能有一个计时任务
若已有计时任务，返回冲突提示
3. 暂停计时
接口

POST /api/timer/pause

4. 恢复计时
接口

POST /api/timer/resume

5. 结束计时
接口

POST /api/timer/stop

请求体
{
  "note": "今天状态不错"
}
用途

结束当前计时，并自动生成 study_sessions 记录。

6. 放弃当前计时
接口

POST /api/timer/discard

用途

终止当前计时但不生成学习记录。

7. 切换计时任务
接口

POST /api/timer/switch

请求体
{
  "new_task_id": 15,
  "save_current_session": true
}
九、学习记录接口
1. 获取学习记录列表
接口

GET /api/study-sessions

查询参数
start_date: 可选
end_date: 可选
category: 可选
task_id: 可选
page: 可选
page_size: 可选
2. 获取单条学习记录详情
接口

GET /api/study-sessions/{session_id}

3. 手动新增学习记录
接口

POST /api/study-sessions

请求体
{
  "task_id": 12,
  "task_title_snapshot": "英语学习",
  "category_snapshot": "学习",
  "session_date": "2026-04-23",
  "start_at": "2026-04-23 19:00:00",
  "end_at": "2026-04-23 20:10:00",
  "duration_minutes": 70,
  "source": "manual",
  "note": ""
}
4. 更新学习记录
接口

PUT /api/study-sessions/{session_id}

5. 删除学习记录
接口

DELETE /api/study-sessions/{session_id}

6. 获取学习统计总览
接口

GET /api/study-stats/overview

查询参数
start_date: 可选
end_date: 可选
返回字段建议
today_minutes
week_minutes
month_minutes
total_minutes
7. 获取按分类统计
接口

GET /api/study-stats/by-category

查询参数
start_date
end_date
返回示例
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "category": "英语",
        "duration_minutes": 300
      },
      {
        "category": "Python",
        "duration_minutes": 240
      }
    ]
  }
}
8. 获取按任务统计
接口

GET /api/study-stats/by-task

查询参数
start_date
end_date
9. 获取按日统计
接口

GET /api/study-stats/by-day

查询参数
start_date
end_date
10. 导出学习记录
接口

GET /api/study-sessions/export

查询参数
format=csv|json
start_date
end_date
十、AI 解析与 AI 规划接口

这是你项目里很关键的一块。

1. 获取 AI 配置状态
接口

GET /api/ai/config

返回字段建议
enabled
provider
model_name
base_url
has_api_key
2. 保存 AI 配置
接口

PUT /api/ai/config

请求体
{
  "enabled": true,
  "provider": "openai_compatible",
  "base_url": "http://127.0.0.1:11434/v1",
  "api_key": "xxx",
  "model_name": "deepseek-chat",
  "timeout": 60,
  "temperature": 0.2
}
3. 测试 AI 连通性
接口

POST /api/ai/test-connection

用途

测试当前模型配置是否可调用。

4. 自然语言解析
接口

POST /api/ai/parse

用途

将用户输入的一句话解析成结构化任务/事件/课程命令。

请求体
{
  "text": "明天上午10点去开会，下午学英语1小时",
  "date_context": "2026-04-23"
}
返回示例
{
  "code": 0,
  "message": "success",
  "data": {
    "actions": [
      {
        "action_type": "add_event",
        "title": "开会",
        "date": "2026-04-24",
        "start_time": "10:00",
        "end_time": "11:00",
        "category": "会议"
      },
      {
        "action_type": "add_task",
        "title": "英语学习",
        "date": "2026-04-24",
        "planned_duration_minutes": 60,
        "category": "学习",
        "is_study": true,
        "time_preference": "afternoon"
      }
    ],
    "raw_log_id": 21
  }
}
5. 应用 AI 解析结果
接口

POST /api/ai/parse/apply

用途

将 /api/ai/parse 的结果真正写入数据库。

请求体
{
  "log_id": 21,
  "actions": [
    {
      "action_type": "add_event",
      "title": "开会",
      "date": "2026-04-24",
      "start_time": "10:00",
      "end_time": "11:00",
      "category": "会议"
    }
  ]
}
返回字段建议
created_task_ids
created_event_ids
created_course_ids
6. AI 智能规划
接口

POST /api/ai/plan

用途

根据当天已有安排、固定任务和个人习惯，生成候选行程方案。

请求体
{
  "date": "2026-04-23",
  "user_input": "今天想去网吧",
  "include_habits": true,
  "option_count": 3
}
返回示例
{
  "code": 0,
  "message": "success",
  "data": {
    "plan_options": [
      {
        "name": "推荐方案",
        "items": [
          {
            "item_type": "event",
            "title": "网吧",
            "date": "2026-04-23",
            "start_time": "16:00",
            "end_time": "17:30",
            "category": "娱乐"
          },
          {
            "item_type": "task_schedule",
            "task_id": 12,
            "title": "英语学习",
            "date": "2026-04-23",
            "start_time": "20:00",
            "end_time": "21:00"
          }
        ],
        "reason": "已避开你的健身安排，并优先使用你常见的晚间学习时间。"
      }
    ],
    "raw_log_id": 25
  }
}
7. 应用 AI 规划结果
接口

POST /api/ai/plan/apply

请求体
{
  "log_id": 25,
  "selected_option_index": 0
}
用途

将某个规划方案正式写入任务/事件。

8. 获取 AI 日志列表
接口

GET /api/ai/logs

查询参数
log_type: parse/plan
page
page_size
9. 获取单条 AI 日志详情
接口

GET /api/ai/logs/{log_id}

10. 删除 AI 日志
接口

DELETE /api/ai/logs/{log_id}

十一、习惯分析接口（建议预留）

虽然第一版可以先简单做，但接口最好先留。

1. 获取习惯画像摘要
接口

GET /api/habits/summary

返回字段建议
preferred_study_time_slots
preferred_fitness_time_slots
average_study_duration
most_common_categories
2. 手动触发习惯分析
接口

POST /api/habits/rebuild

用途

根据历史记录重新计算习惯统计。

十二、推荐开发优先级

如果你要让 Codex 按顺序开发，我建议接口分 4 批做。

第一批：基础可运行
/api/health
/api/settings
/api/task-templates
/api/daily-tasks
/api/daily-tasks/summary
第二批：学习系统
/api/timer/current
/api/timer/start
/api/timer/pause
/api/timer/resume
/api/timer/stop
/api/study-sessions
/api/study-stats/*
第三批：日程系统
/api/events
/api/events/check-conflict
/api/events/timeline
/api/courses
/api/import/courses/json
第四批：AI 系统
/api/ai/config
/api/ai/test-connection
/api/ai/parse
/api/ai/parse/apply
/api/ai/plan
/api/ai/plan/apply
十三、最小 MVP 必须有的接口

如果你只想尽快先把第一版跑起来，最少要这些：

任务相关
GET /api/daily-tasks
POST /api/daily-tasks
PATCH /api/daily-tasks/{task_id}
DELETE /api/daily-tasks/{task_id}
POST /api/daily-tasks/{task_id}/complete
模板相关
GET /api/task-templates
POST /api/task-templates
POST /api/task-templates/refresh-today
学习计时
GET /api/timer/current
POST /api/timer/start
POST /api/timer/pause
POST /api/timer/resume
POST /api/timer/stop
学习记录
GET /api/study-sessions
GET /api/study-stats/overview
事件相关
GET /api/events
POST /api/events
POST /api/events/check-conflict
导入相关
POST /api/import/courses/validate
POST /api/import/courses/json
AI 相关
POST /api/ai/parse
POST /api/ai/parse/apply
POST /api/ai/plan
POST /api/ai/plan/apply
十四、接口命名统一建议

为了后面不乱，建议统一如下：

名词复数
/api/daily-tasks
/api/events
/api/courses
/api/study-sessions
动作型接口单独挂后缀
/complete
/status
/refresh-today
/check-conflict
/apply
/test-connection
避免命名混乱

不要同时出现：

/task
/tasks
/dailyTask
/daily_tasks

统一用：

kebab-case
复数资源名
十五、一句话总结这份接口清单

这套 API 已经完整覆盖了你项目要做的核心能力：

固定任务模板
每日任务管理
单次事件管理
课表导入
学习计时与学习统计
AI 自然语言解析
AI 智能规划
设置与本地模型配置