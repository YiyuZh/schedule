from __future__ import annotations

from sqlalchemy import Engine, text

from app.utils.uuid_utils import new_uuid


SYNC_TABLES = (
    "task_templates",
    "daily_tasks",
    "events",
    "courses",
    "study_sessions",
    "long_term_tasks",
    "long_term_subtasks",
)

SYNC_COLUMNS: tuple[tuple[str, str], ...] = (
    ("sync_id", "VARCHAR(36)"),
    ("sync_version", "INTEGER NOT NULL DEFAULT 1"),
    ("sync_dirty", "BOOLEAN NOT NULL DEFAULT 0"),
    ("sync_deleted", "BOOLEAN NOT NULL DEFAULT 0"),
    ("last_synced_at", "VARCHAR(19)"),
    ("updated_by_device_id", "VARCHAR(64)"),
)


def _table_columns(engine: Engine, table_name: str) -> set[str]:
    with engine.connect() as connection:
        rows = connection.execute(text(f"PRAGMA table_info({table_name})")).mappings().all()
    return {str(row["name"]) for row in rows}


def ensure_sync_schema(engine: Engine) -> None:
    """Add sync columns to existing SQLite tables without requiring Alembic."""
    for table_name in SYNC_TABLES:
        existing_columns = _table_columns(engine, table_name)
        if not existing_columns:
            continue

        with engine.begin() as connection:
            for column_name, column_sql in SYNC_COLUMNS:
                if column_name not in existing_columns:
                    connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"))

            connection.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_sync_id ON {table_name} (sync_id)"))
            missing_sync_id_rows = connection.execute(
                text(f"SELECT id FROM {table_name} WHERE sync_id IS NULL OR sync_id = ''")
            ).mappings()
            for row in missing_sync_id_rows:
                connection.execute(
                    text(f"UPDATE {table_name} SET sync_id = :sync_id WHERE id = :id"),
                    {"sync_id": new_uuid(), "id": row["id"]},
                )
