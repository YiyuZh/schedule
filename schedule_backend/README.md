# Schedule Backend

FastAPI + SQLite backend for the local-first `Schedule / 日程安排` desktop application.

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- SQLite
- Pydantic v2
- Uvicorn
- `jsonschema` for strict AI JSON validation

## Run Locally

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the backend:

```bash
python run.py
```

Default service address:

```text
http://127.0.0.1:8000
```

## Database

- Default SQLite database path: `data/app.db`
- Tables are initialized automatically on startup
- Default settings are seeded automatically on startup
- Enabled task templates are refreshed into today's daily tasks on startup

## Implemented Modules

- System health and runtime info
- App settings read/update
- Task template CRUD and daily refresh
- Daily task CRUD, status updates, reorder, inherit unfinished, summary
- Long-term task CRUD, subtask management, progress calculation, and create-daily-task bridge
- Event CRUD, conflict detection, timeline view
- Course CRUD, day view, week view
- Course JSON validation/import and import batch management
- Study timer start/pause/resume/stop/discard/switch
- Study session CRUD and export
- Study statistics overview, by category/subject, by task, by day
- AI config, real provider test connection, parse/plan/apply flow, AI logs
- Local cloud sync foundation: sync status/config/login/logout/run/push/pull/conflicts

## AI Provider Support

The backend now uses a real OpenAI-compatible HTTP client instead of the old mock-only flow.

Supported target types:

- OpenAI official compatible endpoint
- DeepSeek / OpenRouter style OpenAI-compatible endpoint
- Local OpenAI-compatible servers such as LM Studio or similar local model gateways

The backend currently talks to:

```text
{ai_base_url}/chat/completions
```

So `ai_base_url` should usually include the provider version prefix.

Examples:

- OpenAI: `https://api.openai.com/v1`
- DeepSeek: `https://api.deepseek.com/v1`
- OpenRouter: `https://openrouter.ai/api/v1`
- Local model server: `http://127.0.0.1:1234/v1`

## AI Settings

默认 AI 路线现已切换为 DeepSeek 双模型：

- `ai_provider = deepseek`
- `ai_base_url = https://api.deepseek.com/v1`
- `ai_model_name = deepseek-chat`
- `ai_plan_model_name = deepseek-reasoner`

The following keys are read from `app_settings`:

| Key | Meaning |
| --- | --- |
| `ai_enabled` | Enable or disable AI endpoints |
| `ai_provider` | Provider label for UI/logging, for example `deepseek`, `openai_compatible`, `openrouter`, `local` |
| `ai_base_url` | OpenAI-compatible base URL |
| `ai_api_key` | API key for remote providers |
| `ai_model_name` | Chat / parse model name, for example `deepseek-chat` |
| `ai_plan_model_name` | Planning / reasoning model name, for example `deepseek-reasoner` |
| `ai_timeout` | Request timeout in seconds |
| `ai_temperature` | Generation temperature |

Important behavior:

- If `ai_enabled = false`, AI parse/plan/test endpoints return clear configuration errors.
- Remote providers require `ai_api_key`.
- Localhost / local model gateways can leave `ai_api_key` empty.
- `parse` always uses `ai_model_name`.
- `plan` prefers `ai_plan_model_name`, and falls back to `ai_model_name` if the planning model is missing in an older database.
- DeepSeek `deepseek-reasoner` requests do not send `temperature`, and `reasoning_content` is stored in `ai_logs` metadata for debugging.
- `ai_model_name` and `ai_base_url` must be configured before real AI calls can run.

## Local Cloud Sync Foundation

The first desktop sync foundation is implemented locally. It does not require the cloud server to be deployed yet.

- Local tables: `sync_state`, `sync_queue`, `sync_conflicts`
- Sync metadata fields are added to `daily_tasks`, `long_term_tasks`, and `long_term_subtasks`
- Startup migration `ensure_sync_schema()` safely adds missing sync columns to older SQLite databases and backfills `sync_id`
- Local APIs:
  - `GET /api/sync/status`
  - `POST /api/sync/config`
  - `POST /api/sync/login`
  - `POST /api/sync/logout`
  - `POST /api/sync/run`
  - `POST /api/sync/push`
  - `POST /api/sync/pull`
  - `GET /api/sync/conflicts`
  - `POST /api/sync/conflicts/{id}/resolve`
- If the cloud server is missing or unreachable, the backend keeps local changes in `sync_queue` and returns readable errors.
- `ai_api_key` is never included in sync payloads.

## AI Endpoint Notes

### `/api/ai/test-connection`

- Sends a real model request
- Confirms the provider can return JSON-only output
- When `ai_provider = deepseek`, it checks both `deepseek-chat` and `deepseek-reasoner`
- Response shape stays `{ ok, message }`, and `message` includes both chat / reasoner results

### `/api/ai/parse`

- Uses strong prompt constraints
- Requests JSON-only output
- Validates output with JSON schema + Pydantic models
- Attempts one repair pass if the first model output is invalid
- Writes `ai_logs`

### `/api/ai/plan`

- Collects context from:
  - daily tasks for the target date
  - events for the target date
  - expanded course occurrences for the target date
  - recent study stats
  - simple habit snapshot when `include_habits = true`
- Requests JSON-only plan options
- Validates schema and basic scheduling semantics
- Writes `ai_logs`

### `/api/ai/parse/apply` and `/api/ai/plan/apply`

- Keep the existing frontend API unchanged
- Set `applied_success = true` only after writes finish successfully

## Project Structure

```text
schedule_backend/
├─ app/
│  ├─ api/                # FastAPI routers
│  ├─ core/               # config, database, unified responses
│  ├─ models/             # SQLAlchemy models
│  ├─ schemas/            # Pydantic request/response schemas
│  ├─ services/
│  │  ├─ ai_service.py
│  │  ├─ ai_provider_client.py
│  │  ├─ ai_prompt_builder.py
│  │  └─ ai_response_parser.py
│  ├─ utils/              # datetime/json/validation helpers
│  └─ seed/               # default settings seed
├─ data/                  # SQLite database directory
├─ requirements.txt
├─ README.md
└─ run.py
```

## Notes

- This backend is designed for a local Windows desktop app, not a public SaaS deployment.
- All API responses follow the unified format:

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```
