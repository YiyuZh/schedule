数据库表结构草案 V1
一、设计原则
1. 技术前提
数据库：SQLite
时间字段：优先使用 TEXT，保存为 ISO 8601 格式
例如：2026-04-23 19:30:00
布尔值：SQLite 中使用 INTEGER
0 = false
1 = true
2. 设计目标

当前版本先覆盖以下核心能力：

固定任务模板
每日任务实例
单次事件
周期课程
学习计时记录
当前计时状态
设置项
AI 解析/规划日志
用户习惯统计基础
二、表清单总览
MVP 必建表
app_settings —— 系统设置
task_templates —— 固定任务模板
daily_tasks —— 每日任务实例
events —— 单次事件
courses —— 周期课程
study_sessions —— 学习记录
timer_state —— 当前计时状态
ai_logs —— AI 解析/规划日志
import_batches —— 导入批次记录
建议扩展表
course_exceptions —— 课程例外
habit_profiles —— 习惯统计结果缓存
operation_logs —— 操作日志
三、核心表详细设计
1. app_settings（系统设置表）

用于保存软件设置、AI 配置、用户偏好等。

用途
默认任务时长
AI provider / model / base_url
是否自动继承未完成任务
是否启用 AI
数据路径
完成任务是否自动结束计时
字段设计
字段名	类型	说明
id	INTEGER PK AUTOINCREMENT	主键
setting_key	TEXT NOT NULL UNIQUE	设置键
setting_value	TEXT	设置值
value_type	TEXT NOT NULL DEFAULT 'string'	值类型：string/int/bool/json
description	TEXT	说明
created_at	TEXT NOT NULL	创建时间
updated_at	TEXT NOT NULL	更新时间
建表 SQL
CREATE TABLE IF NOT EXISTS app_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT NOT NULL UNIQUE,
    setting_value TEXT,
    value_type TEXT NOT NULL DEFAULT 'string',
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
2. task_templates（固定任务模板表）

每天自动刷新的任务模板。

用途

例如：

英语学习
健身
背单词
字段设计
字段名	类型	说明
id	INTEGER PK AUTOINCREMENT	主键
title	TEXT NOT NULL	模板标题
category	TEXT NOT NULL DEFAULT '其他'	分类
is_study	INTEGER NOT NULL DEFAULT 0	是否学习任务
default_duration_minutes	INTEGER NOT NULL DEFAULT 30	默认预计时长
default_start_time	TEXT	默认开始时间，可空，如 19:00
default_end_time	TEXT	默认结束时间，可空
time_preference	TEXT NOT NULL DEFAULT 'none'	时间偏好：none/morning/afternoon/evening/night
priority	INTEGER NOT NULL DEFAULT 3	优先级 1-5
is_enabled	INTEGER NOT NULL DEFAULT 1	是否启用
inherit_unfinished	INTEGER NOT NULL DEFAULT 0	昨日未完成是否继承
notes	TEXT	备注
created_at	TEXT NOT NULL	创建时间
updated_at	TEXT NOT NULL	更新时间
约束建议
priority 限制在 1~5
time_preference 做 CHECK
建表 SQL
CREATE TABLE IF NOT EXISTS task_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '其他',
    is_study INTEGER NOT NULL DEFAULT 0 CHECK (is_study IN (0,1)),
    default_duration_minutes INTEGER NOT NULL DEFAULT 30 CHECK (default_duration_minutes >= 0),
    default_start_time TEXT,
    default_end_time TEXT,
    time_preference TEXT NOT NULL DEFAULT 'none'
        CHECK (time_preference IN ('none','morning','afternoon','evening','night')),
    priority INTEGER NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    is_enabled INTEGER NOT NULL DEFAULT 1 CHECK (is_enabled IN (0,1)),
    inherit_unfinished INTEGER NOT NULL DEFAULT 0 CHECK (inherit_unfinished IN (0,1)),
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
3. daily_tasks（每日任务实例表）

这是最核心的一张表。
真正展示在“今日任务”页面里的，就是这里的数据。

用途
某天的英语学习
某天的健身
手动新增的今日任务
AI 解析后加入的任务
字段设计
字段名	类型	说明
id	INTEGER PK AUTOINCREMENT	主键
template_id	INTEGER	来源模板 id，可空
title	TEXT NOT NULL	任务标题
category	TEXT NOT NULL DEFAULT '其他'	分类
is_study	INTEGER NOT NULL DEFAULT 0	是否学习任务
task_date	TEXT NOT NULL	所属日期，格式建议 YYYY-MM-DD
start_time	TEXT	开始时间，可空
end_time	TEXT	结束时间，可空
planned_duration_minutes	INTEGER NOT NULL DEFAULT 0	预计时长
actual_duration_minutes	INTEGER NOT NULL DEFAULT 0	实际时长，通常由学习记录汇总
priority	INTEGER NOT NULL DEFAULT 3	优先级
status	TEXT NOT NULL DEFAULT 'pending'	pending/running/completed/skipped
source	TEXT NOT NULL DEFAULT 'manual'	manual/template/ai/import
sort_order	INTEGER NOT NULL DEFAULT 0	列表排序
notes	TEXT	备注
completed_at	TEXT	完成时间
created_at	TEXT NOT NULL	创建时间
updated_at	TEXT NOT NULL	更新时间
关键说明
template_id 可追溯来源模板
task_date 非常重要，查询今天任务靠它
actual_duration_minutes 建议不要手动乱写，优先通过 study_sessions 汇总
唯一性建议

为了防止模板重复刷新，可以加：

同一个 template_id 在同一天只能生成一条
建表 SQL
CREATE TABLE IF NOT EXISTS daily_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER,
    title TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '其他',
    is_study INTEGER NOT NULL DEFAULT 0 CHECK (is_study IN (0,1)),
    task_date TEXT NOT NULL,
    start_time TEXT,
    end_time TEXT,
    planned_duration_minutes INTEGER NOT NULL DEFAULT 0 CHECK (planned_duration_minutes >= 0),
    actual_duration_minutes INTEGER NOT NULL DEFAULT 0 CHECK (actual_duration_minutes >= 0),
    priority INTEGER NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','running','completed','skipped')),
    source TEXT NOT NULL DEFAULT 'manual'
        CHECK (source IN ('manual','template','ai','import')),
    sort_order INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (template_id) REFERENCES task_templates(id) ON DELETE SET NULL,
    UNIQUE (template_id, task_date)
);
4. events（单次事件表）

用于存储带明确时间段的单次行程。

用途

例如：

明天 10 点开会
后天下午去医院
今天去网吧
字段设计
字段名	类型	说明
id	INTEGER PK AUTOINCREMENT	主键
title	TEXT NOT NULL	事件标题
category	TEXT NOT NULL DEFAULT '其他'	分类
event_date	TEXT NOT NULL	日期 YYYY-MM-DD
start_time	TEXT	开始时间
end_time	TEXT	结束时间
location	TEXT	地点
priority	INTEGER NOT NULL DEFAULT 3	优先级
status	TEXT NOT NULL DEFAULT 'scheduled'	scheduled/completed/cancelled
source	TEXT NOT NULL DEFAULT 'manual'	manual/ai/import
linked_task_id	INTEGER	若由任务转事件，可关联任务
notes	TEXT	备注
created_at	TEXT NOT NULL	创建时间
updated_at	TEXT NOT NULL	更新时间
建表 SQL
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '其他',
    event_date TEXT NOT NULL,
    start_time TEXT,
    end_time TEXT,
    location TEXT,
    priority INTEGER NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    status TEXT NOT NULL DEFAULT 'scheduled'
        CHECK (status IN ('scheduled','completed','cancelled')),
    source TEXT NOT NULL DEFAULT 'manual'
        CHECK (source IN ('manual','ai','import')),
    linked_task_id INTEGER,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (linked_task_id) REFERENCES daily_tasks(id) ON DELETE SET NULL
);
5. courses（周期课程表）

用于存放课表导入后的周期课程规则。

用途

例如：

每周一 08:00 - 09:35 大学英语
第 1~16 周生效
设计说明

这里存的是“规则”，不是每天一条条展开后的事件。
真正展示某一天/某一周时，由后端根据规则计算。

字段设计
字段名	类型	说明
id	INTEGER PK AUTOINCREMENT	主键
batch_id	INTEGER	导入批次 id
course_name	TEXT NOT NULL	课程名
weekday	INTEGER NOT NULL	星期几，1-7
start_time	TEXT NOT NULL	开始时间
end_time	TEXT NOT NULL	结束时间
location	TEXT	地点
teacher	TEXT	教师
term_name	TEXT	学期名
term_start_date	TEXT NOT NULL	学期开始日期
term_end_date	TEXT NOT NULL	学期结束日期
week_list_json	TEXT NOT NULL	生效周次，JSON 数组
color	TEXT	前端显示颜色，可选
notes	TEXT	备注
created_at	TEXT NOT NULL	创建时间
updated_at	TEXT NOT NULL	更新时间
为什么 week_list 用 JSON

因为有些课不是连续周，比如只在 [1,3,5,7,9] 上。
用 JSON 最省事。

建表 SQL
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER,
    course_name TEXT NOT NULL,
    weekday INTEGER NOT NULL CHECK (weekday BETWEEN 1 AND 7),
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    location TEXT,
    teacher TEXT,
    term_name TEXT,
    term_start_date TEXT NOT NULL,
    term_end_date TEXT NOT NULL,
    week_list_json TEXT NOT NULL,
    color TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (batch_id) REFERENCES import_batches(id) ON DELETE SET NULL
);
6. study_sessions（学习记录表）

这是学习统计最核心的数据来源。

用途

记录每一次学习会话：

英语学习 55 分钟
Python 学习 80 分钟
字段设计
字段名	类型	说明
id	INTEGER PK AUTOINCREMENT	主键
task_id	INTEGER	关联 daily_tasks.id，可空
task_title_snapshot	TEXT NOT NULL	任务标题快照
category_snapshot	TEXT NOT NULL DEFAULT '学习'	分类快照
session_date	TEXT NOT NULL	学习日期 YYYY-MM-DD
start_at	TEXT NOT NULL	开始时间
end_at	TEXT NOT NULL	结束时间
duration_minutes	INTEGER NOT NULL	本次学习时长
source	TEXT NOT NULL DEFAULT 'timer'	timer/manual/import
note	TEXT	备注
created_at	TEXT NOT NULL	创建时间
为什么要加 snapshot

因为以后任务标题可能会改。
为了保证历史记录稳定，学习记录里要存当时的标题和分类快照。

建表 SQL
CREATE TABLE IF NOT EXISTS study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    task_title_snapshot TEXT NOT NULL,
    category_snapshot TEXT NOT NULL DEFAULT '学习',
    session_date TEXT NOT NULL,
    start_at TEXT NOT NULL,
    end_at TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes >= 0),
    source TEXT NOT NULL DEFAULT 'timer'
        CHECK (source IN ('timer','manual','import')),
    note TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES daily_tasks(id) ON DELETE SET NULL
);
7. timer_state（当前计时状态表）

用于存当前正在进行的学习计时。
这个表通常只会有 0 或 1 条有效记录。

用途
当前是否正在计时
正在计时的是哪个任务
开始时间
暂停累计时长
字段设计
字段名	类型	说明
id	INTEGER PK AUTOINCREMENT	主键
task_id	INTEGER NOT NULL	正在计时的任务 id
started_at	TEXT NOT NULL	开始时间
paused_at	TEXT	暂停时间
accumulated_seconds	INTEGER NOT NULL DEFAULT 0	已累计秒数
status	TEXT NOT NULL DEFAULT 'running'	running/paused
created_at	TEXT NOT NULL	创建时间
updated_at	TEXT NOT NULL	更新时间
关键约束建议

业务层保证同一时刻只存在一条有效计时记录。

建表 SQL
CREATE TABLE IF NOT EXISTS timer_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    paused_at TEXT,
    accumulated_seconds INTEGER NOT NULL DEFAULT 0 CHECK (accumulated_seconds >= 0),
    status TEXT NOT NULL DEFAULT 'running'
        CHECK (status IN ('running','paused')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES daily_tasks(id) ON DELETE CASCADE
);
8. ai_logs（AI 日志表）

记录 AI 解析和 AI 规划过程，便于调试与追溯。

用途
记录用户输入原文
记录 AI 返回 JSON
记录是否成功
记录写入前后的结果
字段设计
字段名	类型	说明
id	INTEGER PK AUTOINCREMENT	主键
log_type	TEXT NOT NULL	parse/plan
provider	TEXT	模型提供方
model_name	TEXT	模型名
user_input	TEXT NOT NULL	用户原始输入
context_json	TEXT	上下文 JSON
ai_output_json	TEXT	AI 输出 JSON
parsed_success	INTEGER NOT NULL DEFAULT 0	是否成功解析
applied_success	INTEGER NOT NULL DEFAULT 0	是否已应用到数据库
error_message	TEXT	错误信息
created_at	TEXT NOT NULL	创建时间
建表 SQL
CREATE TABLE IF NOT EXISTS ai_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_type TEXT NOT NULL CHECK (log_type IN ('parse','plan')),
    provider TEXT,
    model_name TEXT,
    user_input TEXT NOT NULL,
    context_json TEXT,
    ai_output_json TEXT,
    parsed_success INTEGER NOT NULL DEFAULT 0 CHECK (parsed_success IN (0,1)),
    applied_success INTEGER NOT NULL DEFAULT 0 CHECK (applied_success IN (0,1)),
    error_message TEXT,
    created_at TEXT NOT NULL
);
9. import_batches（导入批次表）

用于记录课表或其他批量数据导入。

用途
记录某次课表导入
方便回滚、排错、覆盖旧数据
字段设计
字段名	类型	说明
id	INTEGER PK AUTOINCREMENT	主键
import_type	TEXT NOT NULL	course/csv/json
file_name	TEXT	文件名
raw_content	TEXT	原始导入内容，可选
parsed_count	INTEGER NOT NULL DEFAULT 0	解析成功条数
status	TEXT NOT NULL DEFAULT 'success'	success/failed/partial
error_message	TEXT	错误信息
created_at	TEXT NOT NULL	创建时间
建表 SQL
CREATE TABLE IF NOT EXISTS import_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_type TEXT NOT NULL CHECK (import_type IN ('course','csv','json')),
    file_name TEXT,
    raw_content TEXT,
    parsed_count INTEGER NOT NULL DEFAULT 0 CHECK (parsed_count >= 0),
    status TEXT NOT NULL DEFAULT 'success'
        CHECK (status IN ('success','failed','partial')),
    error_message TEXT,
    created_at TEXT NOT NULL
);
四、建议扩展表
10. course_exceptions（课程例外表，可选）

用于处理课程临时停课、改时间、补课等。

字段设计
字段名	类型	说明
id	INTEGER PK AUTOINCREMENT	主键
course_id	INTEGER NOT NULL	对应课程
exception_date	TEXT NOT NULL	例外日期
action_type	TEXT NOT NULL	cancel/replace
new_start_time	TEXT	新开始时间
new_end_time	TEXT	新结束时间
new_location	TEXT	新地点
notes	TEXT	备注
created_at	TEXT NOT NULL	创建时间
建表 SQL
CREATE TABLE IF NOT EXISTS course_exceptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    exception_date TEXT NOT NULL,
    action_type TEXT NOT NULL CHECK (action_type IN ('cancel','replace')),
    new_start_time TEXT,
    new_end_time TEXT,
    new_location TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);
11. habit_profiles（习惯统计缓存表，可选）

如果后面 AI 规划要更聪明，可以把统计结果缓存下来，不用每次现算。

字段设计
字段名	类型	说明
id	INTEGER PK AUTOINCREMENT	主键
category	TEXT NOT NULL	类别，如 英语/健身
metric_key	TEXT NOT NULL	指标名，如 preferred_time_slot
metric_value	TEXT NOT NULL	指标值
calculated_at	TEXT NOT NULL	统计时间
建表 SQL
CREATE TABLE IF NOT EXISTS habit_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    metric_key TEXT NOT NULL,
    metric_value TEXT NOT NULL,
    calculated_at TEXT NOT NULL
);
12. operation_logs（操作日志表，可选）

用于记录关键用户操作，方便排错。

建表 SQL
CREATE TABLE IF NOT EXISTS operation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_name TEXT NOT NULL,
    action_name TEXT NOT NULL,
    target_type TEXT,
    target_id INTEGER,
    detail_json TEXT,
    created_at TEXT NOT NULL
);
五、索引建议

SQLite 虽然轻，但该加的索引还是要加，不然后期查日程会慢。

建议索引 SQL
CREATE INDEX IF NOT EXISTS idx_daily_tasks_task_date
ON daily_tasks(task_date);

CREATE INDEX IF NOT EXISTS idx_daily_tasks_status
ON daily_tasks(status);

CREATE INDEX IF NOT EXISTS idx_daily_tasks_template_id
ON daily_tasks(template_id);

CREATE INDEX IF NOT EXISTS idx_events_event_date
ON events(event_date);

CREATE INDEX IF NOT EXISTS idx_events_date_time
ON events(event_date, start_time, end_time);

CREATE INDEX IF NOT EXISTS idx_courses_weekday
ON courses(weekday);

CREATE INDEX IF NOT EXISTS idx_study_sessions_session_date
ON study_sessions(session_date);

CREATE INDEX IF NOT EXISTS idx_study_sessions_task_id
ON study_sessions(task_id);

CREATE INDEX IF NOT EXISTS idx_ai_logs_type
ON ai_logs(log_type);

CREATE INDEX IF NOT EXISTS idx_import_batches_type
ON import_batches(import_type);
六、表关系说明
核心关系
1. task_templates → daily_tasks
一个固定模板
对应多天的任务实例

关系：

task_templates.id = daily_tasks.template_id
2. daily_tasks → study_sessions
一个学习任务
可以对应多次学习记录

关系：

daily_tasks.id = study_sessions.task_id
3. daily_tasks → timer_state
某一时刻只允许一个任务正在计时
timer_state.task_id 指向当前计时任务
4. import_batches → courses
一次导入
可生成多条课程规则

关系：

import_batches.id = courses.batch_id
5. daily_tasks → events
某些任务可能被安排成固定时间事件
可用 events.linked_task_id 建立关联
七、最小够用版建议

如果你要尽快开发，第一版我建议先只落这 9 张表：

app_settings
task_templates
daily_tasks
events
courses
study_sessions
timer_state
ai_logs
import_batches

这已经足够支撑：

今日任务
固定刷新
学习计时
学习统计
行程新增
AI 解析
课表导入
八、开发阶段的几个关键建议
1. daily_tasks.actual_duration_minutes 不要手动乱维护

最稳妥做法：

页面展示时动态汇总 study_sessions
或者在每次新增/修改 study_sessions 后同步更新

否则很容易出现数据不一致。

2. courses 不要一开始就展开成整学期所有事件

因为这样数据会膨胀，而且修改麻烦。
更稳妥是：

存规则
查询某天/某周时动态算出课程实例
3. timer_state 建议业务上强制只保留 1 条活动记录

不要同时存在多条“running”。

4. AI 返回原始 JSON 一定要保留

这对后面排查“为什么识别错了”非常重要。

5. 导入课表一定要有 batch_id

后面用户想“删除这次导入的全部课程”时会非常好用。

九、推荐初始化顺序

如果你后面让 Codex 开发，数据库部分建议按这个顺序做：

建 app_settings
建 task_templates
建 daily_tasks
建 study_sessions
建 timer_state
建 events
建 import_batches
建 courses
建 ai_logs
建索引

这样最稳。