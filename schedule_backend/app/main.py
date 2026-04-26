from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    ai,
    courses,
    daily_tasks,
    events,
    health,
    imports,
    long_term_tasks,
    settings as settings_api,
    study_sessions,
    study_stats,
    sync,
    task_templates,
    timer,
)
from app.core.config import settings
from app.core.database import SessionLocal, initialize_database
from app.core.response import register_exception_handlers
from app.schemas.daily_task import DailyTaskInheritRequest
from app.seed.init_settings import seed_default_settings
from app.services.daily_task_service import DailyTaskService
from app.services.settings_service import SettingsService
from app.services.task_template_service import TaskTemplateService
from app.utils.datetime_utils import shift_date, today_str


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    with SessionLocal() as db:
        seed_default_settings(db)
        TaskTemplateService(db).refresh_today(today_str())
        auto_inherit = bool(SettingsService(db).get_setting_value("auto_inherit_unfinished", False))
        if auto_inherit:
            DailyTaskService(db).inherit_unfinished(
                DailyTaskInheritRequest(from_date=shift_date(today_str(), -1), to_date=today_str())
            )
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
register_exception_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(settings_api.router, prefix=settings.api_prefix)
app.include_router(task_templates.router, prefix=settings.api_prefix)
app.include_router(daily_tasks.router, prefix=settings.api_prefix)
app.include_router(long_term_tasks.router, prefix=settings.api_prefix)
app.include_router(events.router, prefix=settings.api_prefix)
app.include_router(courses.router, prefix=settings.api_prefix)
app.include_router(imports.router, prefix=settings.api_prefix)
app.include_router(timer.router, prefix=settings.api_prefix)
app.include_router(study_sessions.router, prefix=settings.api_prefix)
app.include_router(study_stats.router, prefix=settings.api_prefix)
app.include_router(ai.router, prefix=settings.api_prefix)
app.include_router(sync.router, prefix=settings.api_prefix)
