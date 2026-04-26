from __future__ import annotations

import platform
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.response import AppException
from app.models.sync import SyncConflict, SyncQueue, SyncState
from app.schemas.sync import (
    SyncConfigUpdate,
    SyncConflictListData,
    SyncConflictRead,
    SyncConflictResolveRequest,
    SyncLoginRequest,
    SyncRegisterRequest,
    SyncRunResult,
    SyncStatusRead,
)
from app.services.sync_client import SyncClient, SyncClientError
from app.services.sync_mapper import (
    ENTITY_FIELDS,
    RELATION_FIELDS,
    SYNC_ENTITY_MODELS,
    delete_payload,
    model_to_payload,
    normalize_sync_payload,
    parse_json,
    to_json,
)
from app.utils.datetime_utils import now_datetime_str
from app.utils.uuid_utils import new_uuid


DEFAULT_SYNC_SERVER_URL = "https://schedule-sync.zenithy.art"
AUTO_SYNC_DEBOUNCE_SECONDS = 3.0


class _AutoSyncScheduler:
    def __init__(self) -> None:
        self._timer = None
        self._running = False

    def schedule(self) -> None:
        import threading

        if self._timer is not None:
            self._timer.cancel()
        self._timer = threading.Timer(AUTO_SYNC_DEBOUNCE_SECONDS, self._run)
        self._timer.daemon = True
        self._timer.start()

    def _run(self) -> None:
        if self._running:
            return
        self._running = True
        try:
            from app.core.database import SessionLocal

            with SessionLocal() as db:
                SyncService(db).run()
        except Exception:
            # Auto sync must never break local desktop work.
            pass
        finally:
            self._running = False


_auto_sync_scheduler = _AutoSyncScheduler()


class SyncService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create_state(self) -> SyncState:
        state = self.db.scalar(select(SyncState).order_by(SyncState.id.asc()))
        if state is not None:
            if not state.server_url:
                state.server_url = DEFAULT_SYNC_SERVER_URL
                state.enabled = True
                self.db.commit()
                self.db.refresh(state)
            return state

        state = SyncState(
            device_id=new_uuid(),
            device_name=(platform.node() or "Windows Desktop")[:100],
            server_url=DEFAULT_SYNC_SERVER_URL,
            enabled=True,
        )
        self.db.add(state)
        self.db.commit()
        self.db.refresh(state)
        return state

    def _pending_count(self) -> int:
        return int(self.db.scalar(select(func.count(SyncQueue.id))) or 0)

    def _conflict_count(self) -> int:
        return int(self.db.scalar(select(func.count(SyncConflict.id)).where(SyncConflict.status == "open")) or 0)

    def get_status(self) -> SyncStatusRead:
        state = self.get_or_create_state()
        return SyncStatusRead(
            enabled=bool(state.enabled),
            configured=bool(state.server_url),
            logged_in=bool(state.access_token),
            server_url=state.server_url,
            user_email=state.user_email,
            device_id=state.device_id,
            device_name=state.device_name,
            pending_count=self._pending_count(),
            conflict_count=self._conflict_count(),
            last_push_at=state.last_push_at,
            last_pull_at=state.last_pull_at,
            last_error=state.last_error,
        )

    def save_config(self, payload: SyncConfigUpdate) -> SyncStatusRead:
        state = self.get_or_create_state()
        state.enabled = payload.enabled
        state.server_url = payload.server_url or DEFAULT_SYNC_SERVER_URL
        if payload.device_name:
            state.device_name = payload.device_name.strip()
        state.last_error = None
        self.db.commit()
        return self.get_status()

    def login(self, payload: SyncLoginRequest) -> SyncStatusRead:
        state = self.get_or_create_state()
        state.server_url = payload.server_url or state.server_url or DEFAULT_SYNC_SERVER_URL
        if payload.device_name:
            state.device_name = payload.device_name.strip()
        state.user_email = payload.email.strip()
        state.enabled = True
        self.db.commit()

        try:
            result = SyncClient(state.server_url).login(
                email=payload.email.strip(),
                password=payload.password,
                device_id=state.device_id,
                device_name=state.device_name,
            )
            self._apply_token_result(state, result)
            state.latest_change_id = 0
            self.db.commit()
            self.bootstrap()
            return self.get_status()
        except SyncClientError as exc:
            self._set_last_error(str(exc))
            raise AppException(str(exc), code=4091, status_code=400) from exc

    def register_account(self, payload: SyncRegisterRequest) -> SyncStatusRead:
        state = self.get_or_create_state()
        state.server_url = payload.server_url or state.server_url or DEFAULT_SYNC_SERVER_URL
        if payload.device_name:
            state.device_name = payload.device_name.strip()
        state.user_email = payload.email.strip()
        state.enabled = True
        self.db.commit()

        try:
            client = SyncClient(state.server_url)
            client.register(email=payload.email.strip(), password=payload.password, display_name=payload.display_name)
            result = client.login(
                email=payload.email.strip(),
                password=payload.password,
                device_id=state.device_id,
                device_name=state.device_name,
            )
            self._apply_token_result(state, result)
            state.latest_change_id = 0
            self.db.commit()
            self.bootstrap()
            return self.get_status()
        except SyncClientError as exc:
            self._set_last_error(str(exc))
            raise AppException(str(exc), code=4091, status_code=400) from exc

    def logout(self) -> SyncStatusRead:
        state = self.get_or_create_state()
        state.access_token = None
        state.refresh_token = None
        state.user_email = None
        state.last_error = None
        self.db.commit()
        return self.get_status()

    def _apply_token_result(self, state: SyncState, result: dict[str, Any]) -> None:
        access_token = result.get("access_token") or result.get("token")
        if not access_token:
            raise SyncClientError("cloud login response missing access_token")
        state.access_token = str(access_token)
        refresh_token = result.get("refresh_token")
        state.refresh_token = str(refresh_token) if refresh_token else None
        state.last_error = None
        self.db.commit()

    def _set_last_error(self, message: str) -> None:
        state = self.get_or_create_state()
        state.last_error = message
        self.db.commit()

    def _not_ready_result(self, action: str) -> SyncRunResult:
        state = self.get_or_create_state()
        if not state.server_url:
            message = "cloud sync is not configured"
        elif not state.access_token:
            message = "cloud sync account is not logged in"
        else:
            message = "cloud sync is not available"
        state.last_error = message
        self.db.commit()
        return SyncRunResult(error_count=1, message=f"{action} failed: {message}")

    def enqueue_change(
        self,
        entity_type: str,
        entity_id: int | str,
        operation: str,
        *,
        model: object | None = None,
        payload: dict[str, Any] | None = None,
        base_version: int | None = None,
        sync_scope: str | None = None,
        changed_fields: list[str] | None = None,
    ) -> None:
        state = self.get_or_create_state()
        if model is not None and operation != "delete":
            if not getattr(model, "sync_id", None):
                setattr(model, "sync_id", new_uuid())
            previous_version = int(getattr(model, "sync_version", 1) or 1)
            setattr(model, "sync_version", previous_version + 1)
            setattr(model, "sync_dirty", True)
            setattr(model, "sync_deleted", False)
            setattr(model, "updated_by_device_id", state.device_id)
            base_version = previous_version
            payload = model_to_payload(entity_type, model)
            if sync_scope:
                payload["sync_scope"] = sync_scope
            if changed_fields:
                payload["changed_fields"] = changed_fields

        if payload is None:
            payload = {"entity_type": entity_type, "local_id": entity_id}

        self.db.add(
            SyncQueue(
                entity_type=entity_type,
                entity_id=str(entity_id),
                operation=operation,
                payload_json=to_json(payload),
                base_version=int(base_version or 0),
            )
        )
        self.db.commit()
        self._schedule_auto_sync_if_ready()

    def enqueue_delete(self, entity_type: str, *, entity_id: int | str, sync_id: str | None, sync_version: int | None) -> None:
        self.enqueue_change(
            entity_type,
            entity_id,
            "delete",
            payload=delete_payload(entity_type, entity_id=entity_id, sync_id=sync_id, sync_version=int(sync_version or 1)),
            base_version=int(sync_version or 1),
        )

    def safe_enqueue_change(self, *args: Any, **kwargs: Any) -> None:
        try:
            self.enqueue_change(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - sync queue must not break local writes.
            self.db.rollback()
            self._set_last_error(f"local write succeeded, but sync enqueue failed: {exc}")

    def safe_enqueue_delete(self, *args: Any, **kwargs: Any) -> None:
        try:
            self.enqueue_delete(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - sync queue must not break local deletes.
            self.db.rollback()
            self._set_last_error(f"local delete succeeded, but sync enqueue failed: {exc}")

    def _schedule_auto_sync_if_ready(self) -> None:
        state = self.get_or_create_state()
        if state.enabled and state.server_url and state.access_token:
            _auto_sync_scheduler.schedule()

    def _request_with_refresh(self, method: str, state: SyncState, **kwargs: Any) -> dict[str, Any]:
        client = SyncClient(state.server_url or "")
        try:
            return getattr(client, method)(token=state.access_token or "", **kwargs)
        except SyncClientError as exc:
            if "401" not in str(exc) or not state.refresh_token:
                raise
            result = client.refresh(refresh_token=state.refresh_token, device_id=state.device_id)
            self._apply_token_result(state, result)
            return getattr(client, method)(token=state.access_token or "", **kwargs)

    def push(self) -> SyncRunResult:
        state = self.get_or_create_state()
        if not state.server_url or not state.access_token:
            return self._not_ready_result("push")

        queue_items = self.db.scalars(select(SyncQueue).order_by(SyncQueue.created_at.asc(), SyncQueue.id.asc())).all()
        if not queue_items:
            state.last_push_at = now_datetime_str()
            state.last_error = None
            self.db.commit()
            return SyncRunResult(message="no pending changes")

        changes = [
            {
                "queue_id": item.id,
                "entity_type": item.entity_type,
                "entity_id": item.entity_id,
                "operation": item.operation,
                "payload": parse_json(item.payload_json),
                "base_version": item.base_version,
                "created_at": item.created_at,
            }
            for item in queue_items
        ]

        try:
            result = self._request_with_refresh("push", state, device_id=state.device_id, changes=changes)
            rejected_items = result.get("rejected_items") if isinstance(result.get("rejected_items"), list) else []
            accepted_items = result.get("accepted_items") if isinstance(result.get("accepted_items"), list) else []
            raw_accepted_ids = result.get("accepted_queue_ids")
            accepted_ids = {
                int(item)
                for item in raw_accepted_ids
                if isinstance(item, int) or (isinstance(item, str) and item.isdigit())
            } if isinstance(raw_accepted_ids, list) else set()
            accepted_by_id = {
                int(item.get("queue_id")): item
                for item in accepted_items
                if isinstance(item, dict)
                and item.get("queue_id") is not None
                and (isinstance(item.get("queue_id"), int) or str(item.get("queue_id")).isdigit())
            }
            accepted_ids.update(accepted_by_id.keys())
            rejected_by_id = {
                int(item.get("queue_id")): str(item.get("message") or "cloud rejected this change")
                for item in rejected_items
                if isinstance(item, dict) and item.get("queue_id") is not None
            }
            rejected_count = int(result.get("rejected_count") or len(rejected_by_id) or 0)
            accepted_count = int(result.get("accepted_count") or result.get("pushed_count") or len(accepted_ids) or 0)
            if not accepted_ids and rejected_count == 0:
                accepted_ids = {int(item.id) for item in queue_items}
                accepted_count = len(accepted_ids)

            for item in queue_items:
                if int(item.id) in accepted_ids:
                    self._mark_queue_entity_synced(item, accepted_by_id.get(int(item.id)))
                    self.db.delete(item)
                elif int(item.id) in rejected_by_id:
                    item.retry_count += 1
                    item.last_error = rejected_by_id[int(item.id)]

            state.last_push_at = now_datetime_str()
            state.last_error = f"cloud rejected {rejected_count} changes" if rejected_count else None
            self.db.commit()
            return SyncRunResult(
                push_count=accepted_count,
                error_count=1 if rejected_count else 0,
                message=state.last_error or f"pushed {accepted_count} changes",
            )
        except SyncClientError as exc:
            for item in queue_items:
                item.retry_count += 1
                item.last_error = str(exc)
            state.last_error = str(exc)
            self.db.commit()
            return SyncRunResult(error_count=1, message=str(exc))

    def _mark_queue_entity_synced(self, item: SyncQueue, accepted_item: dict[str, Any] | None = None) -> None:
        model = SYNC_ENTITY_MODELS.get(item.entity_type)
        if model is None:
            return

        payload = parse_json(item.payload_json) or {}
        envelope = normalize_sync_payload(item.entity_type, item.entity_id, payload)
        sync_id = str((accepted_item or {}).get("entity_id") or envelope.get("sync_id") or item.entity_id)
        local = self._find_by_sync_id(item.entity_type, sync_id)
        if local is None:
            return

        accepted_version = (accepted_item or {}).get("sync_version")
        if accepted_version is None:
            accepted_version = envelope.get("sync_version") or getattr(local, "sync_version", 1)

        if hasattr(local, "sync_version"):
            setattr(local, "sync_version", int(accepted_version or 1))
        if hasattr(local, "sync_dirty"):
            setattr(local, "sync_dirty", False)
        if hasattr(local, "sync_deleted"):
            setattr(local, "sync_deleted", item.operation == "delete")
        if hasattr(local, "last_synced_at"):
            setattr(local, "last_synced_at", now_datetime_str())
        if hasattr(local, "updated_by_device_id"):
            setattr(local, "updated_by_device_id", self.get_or_create_state().device_id)

    def bootstrap(self) -> SyncRunResult:
        state = self.get_or_create_state()
        if not state.server_url or not state.access_token:
            return self._not_ready_result("bootstrap")

        page = 1
        page_size = 500
        applied_count = 0
        conflict_count = 0
        latest_change_id = state.latest_change_id

        try:
            while True:
                result = self._request_with_refresh("bootstrap", state, page=page, page_size=page_size)
                items = result.get("items") if isinstance(result.get("items"), list) else []
                for item in sorted(items, key=self._change_order):
                    change = {
                        "entity_type": item.get("entity_type"),
                        "entity_id": item.get("entity_id"),
                        "operation": "upsert",
                        "remote_version": item.get("sync_version"),
                        "payload": item.get("payload"),
                    }
                    try:
                        if self._apply_remote_change(change):
                            self.db.flush()
                            applied_count += 1
                        else:
                            conflict_count += 1
                    except Exception as exc:  # noqa: BLE001
                        self.db.rollback()
                        entity_type = str(change.get("entity_type") or "unknown")
                        entity_id = str(change.get("entity_id") or "")
                        self._record_remote_conflict(entity_type, entity_id, None, {**change, "apply_error": str(exc)})
                        conflict_count += 1

                latest_change_id = int(result.get("latest_change_id") or latest_change_id or 0)
                if len(items) < page_size:
                    break
                page += 1

            state.latest_change_id = latest_change_id
            state.last_pull_at = now_datetime_str()
            state.last_error = None if conflict_count == 0 else f"{conflict_count} bootstrap changes need review"
            self.db.commit()
            return SyncRunResult(
                pull_count=applied_count,
                conflict_count=conflict_count,
                message=f"bootstrap applied {applied_count} cloud records",
            )
        except SyncClientError as exc:
            state.last_error = str(exc)
            self.db.commit()
            return SyncRunResult(error_count=1, message=str(exc))

    def pull(self) -> SyncRunResult:
        state = self.get_or_create_state()
        if not state.server_url or not state.access_token:
            return self._not_ready_result("pull")

        try:
            result = self._request_with_refresh(
                "pull",
                state,
                device_id=state.device_id,
                since_change_id=state.latest_change_id,
            )
            changes = result.get("changes") if isinstance(result.get("changes"), list) else []
            applied_count = 0
            conflict_count = 0
            for change in sorted(changes, key=self._change_order):
                try:
                    if self._apply_remote_change(change):
                        self.db.flush()
                        applied_count += 1
                    else:
                        conflict_count += 1
                except Exception as exc:  # noqa: BLE001 - one bad cloud record must not stop the whole pull.
                    self.db.rollback()
                    entity_type = str(change.get("entity_type") or "unknown")
                    entity_id = str(change.get("entity_id") or "")
                    self._record_remote_conflict(entity_type, entity_id, None, {**change, "apply_error": str(exc)})
                    conflict_count += 1

            latest_change_id = result.get("latest_change_id")
            if latest_change_id is not None:
                state.latest_change_id = int(latest_change_id)
            state.last_pull_at = now_datetime_str()
            state.last_error = None if conflict_count == 0 else f"{conflict_count} remote changes need review"
            self.db.commit()
            return SyncRunResult(
                pull_count=len(changes),
                conflict_count=conflict_count,
                message=(
                    f"applied {applied_count} cloud changes, {conflict_count} conflicts"
                    if changes
                    else "no remote changes"
                ),
            )
        except SyncClientError as exc:
            state.last_error = str(exc)
            self.db.commit()
            return SyncRunResult(error_count=1, message=str(exc))

    def run(self) -> SyncRunResult:
        push_result = self.push()
        if push_result.error_count:
            return push_result
        pull_result = self.pull()
        return SyncRunResult(
            push_count=push_result.push_count,
            pull_count=pull_result.pull_count,
            conflict_count=pull_result.conflict_count,
            error_count=pull_result.error_count,
            message=pull_result.message if pull_result.error_count or pull_result.conflict_count else "sync completed",
        )

    def _change_order(self, change: dict[str, Any]) -> int:
        order = {
            "task_template": 10,
            "long_term_task": 20,
            "daily_task": 30,
            "event": 40,
            "course": 50,
            "long_term_subtask": 60,
            "study_session": 70,
        }
        return order.get(str(change.get("entity_type") or ""), 999)

    def _find_by_sync_id(self, entity_type: str, sync_id: str) -> object | None:
        model = SYNC_ENTITY_MODELS.get(entity_type)
        if model is None:
            return None
        return self.db.scalar(select(model).where(model.sync_id == sync_id))

    def _find_local_id_by_sync_id(self, entity_type: str, sync_id: str | None) -> int | None:
        if not sync_id:
            return None
        item = self._find_by_sync_id(entity_type, str(sync_id))
        return int(getattr(item, "id")) if item is not None else None

    def _record_remote_conflict(self, entity_type: str, entity_id: str, local: object | None, change: dict[str, Any]) -> None:
        local_payload = model_to_payload(entity_type, local) if local is not None and entity_type in SYNC_ENTITY_MODELS else None
        self.db.add(
            SyncConflict(
                entity_type=entity_type,
                entity_id=entity_id,
                local_payload_json=to_json(local_payload) if local_payload else None,
                remote_payload_json=to_json(change),
                base_version=int(getattr(local, "sync_version", 0) if local is not None else 0),
                remote_version=int(change.get("sync_version") or change.get("remote_version") or 0),
            )
        )

    def _apply_remote_change(self, change: dict[str, Any]) -> bool:
        entity_type = str(change.get("entity_type") or "")
        model = SYNC_ENTITY_MODELS.get(entity_type)
        if model is None:
            self._record_remote_conflict(entity_type or "unknown", str(change.get("entity_id") or ""), None, change)
            return False

        envelope = normalize_sync_payload(entity_type, str(change.get("entity_id") or ""), change.get("payload"))
        sync_id = str(envelope["sync_id"])
        local = self._find_by_sync_id(entity_type, sync_id)
        if local is not None and bool(getattr(local, "sync_dirty", False)):
            self._record_remote_conflict(entity_type, sync_id, local, change)
            return False

        if str(change.get("operation") or "") == "delete" or bool(envelope["sync_deleted"]):
            if local is not None:
                self.db.delete(local)
            return True

        if local is None:
            local = model()
            setattr(local, "sync_id", sync_id)
            self.db.add(local)

        data = self._normalize_remote_data(entity_type, dict(envelope["data"]))
        relation_sync_ids = dict(envelope["relation_sync_ids"])
        if not self._apply_relations(entity_type, local, data, relation_sync_ids, change):
            return False

        for key in ENTITY_FIELDS.get(entity_type, ()):
            if key in {"id", "created_at", "updated_at"} or key in RELATION_FIELDS.get(entity_type, {}):
                continue
            if key in data and hasattr(local, key):
                setattr(local, key, data[key])

        if hasattr(local, "sync_version"):
            setattr(local, "sync_version", int(envelope.get("sync_version") or change.get("remote_version") or 1))
        if hasattr(local, "sync_deleted"):
            setattr(local, "sync_deleted", bool(envelope.get("sync_deleted")))
        if hasattr(local, "updated_by_device_id"):
            setattr(local, "updated_by_device_id", envelope.get("updated_by_device_id"))
        if hasattr(local, "sync_dirty"):
            setattr(local, "sync_dirty", False)
        if hasattr(local, "last_synced_at"):
            setattr(local, "last_synced_at", now_datetime_str())
        return True

    def _normalize_priority(self, value: Any) -> int:
        if isinstance(value, int):
            return min(5, max(1, value))
        if isinstance(value, str):
            text = value.strip().lower()
            if text in {"high", "urgent", "高", "高优先级"}:
                return 5
            if text in {"low", "低", "低优先级"}:
                return 1
            if text.isdigit():
                return min(5, max(1, int(text)))
        return 3

    def _normalize_remote_data(self, entity_type: str, data: dict[str, Any]) -> dict[str, Any]:
        """Make mobile/web payloads satisfy the desktop SQLite constraints."""
        if "priority" in data:
            data["priority"] = self._normalize_priority(data.get("priority"))

        if entity_type == "task_template":
            data.setdefault("category", "other")
            data.setdefault("is_study", False)
            data.setdefault("default_duration_minutes", 30)
            data.setdefault("time_preference", "none")
            data.setdefault("is_enabled", True)
            data.setdefault("inherit_unfinished", False)

        if entity_type == "daily_task":
            data.setdefault("category", "other")
            data.setdefault("is_study", False)
            data.setdefault("actual_duration_minutes", 0)
            data.setdefault("planned_duration_minutes", 0)
            data.setdefault("status", "pending")
            data.setdefault("source", "manual")
            data.setdefault("sort_order", 0)
            if data.get("source") not in {"manual", "template", "ai", "import"}:
                data["source"] = "manual"

        if entity_type == "event":
            data.setdefault("category", "other")
            data.setdefault("status", "scheduled")
            data.setdefault("source", "manual")
            if data.get("status") == "pending":
                data["status"] = "scheduled"
            if data.get("source") not in {"manual", "ai", "import"}:
                data["source"] = "manual"

        if entity_type == "course":
            today = now_datetime_str()[:10]
            data["batch_id"] = None
            data.setdefault("course_name", "未命名课程")
            data.setdefault("weekday", 1)
            data.setdefault("start_time", "08:00")
            data.setdefault("end_time", "09:00")
            data.setdefault("term_name", "默认学期")
            data.setdefault("term_start_date", today)
            data.setdefault("term_end_date", today)
            data.setdefault("week_list_json", "[1]")

        if entity_type == "study_session":
            data.setdefault("task_title_snapshot", "Study Session")
            data.setdefault("category_snapshot", "study")
            data.setdefault("duration_minutes", 0)
            data.setdefault("source", "manual")
            if data.get("source") not in {"timer", "manual", "import"}:
                data["source"] = "manual"

        if entity_type == "long_term_task":
            data.setdefault("category", "项目")
            data.setdefault("status", "active")
            data.setdefault("progress_percent", 0)
            data.setdefault("sort_order", 0)

        if entity_type == "long_term_subtask":
            data.setdefault("category", "项目")
            data.setdefault("is_study", False)
            data.setdefault("planned_duration_minutes", 30)
            data.setdefault("status", "pending")
            data.setdefault("sort_order", 0)

        return data

    def _apply_relations(
        self,
        entity_type: str,
        local: object,
        data: dict[str, Any],
        relation_sync_ids: dict[str, Any],
        change: dict[str, Any],
    ) -> bool:
        for local_field, (target_entity_type, relation_key) in RELATION_FIELDS.get(entity_type, {}).items():
            relation_sync_id = relation_sync_ids.get(relation_key)
            raw_value = data.get(local_field)
            if relation_sync_id is None and isinstance(raw_value, str) and not raw_value.isdigit():
                relation_sync_id = raw_value

            if relation_sync_id:
                local_id = self._find_local_id_by_sync_id(target_entity_type, str(relation_sync_id))
                if local_id is None and local_field == "long_task_id":
                    self._record_remote_conflict(entity_type, str(change.get("entity_id") or ""), local, change)
                    return False
                setattr(local, local_field, local_id)
            elif raw_value is None:
                setattr(local, local_field, None)
            elif isinstance(raw_value, int):
                target_model = SYNC_ENTITY_MODELS.get(target_entity_type)
                target_exists = self.db.get(target_model, raw_value) is not None if target_model is not None else False
                if target_exists:
                    setattr(local, local_field, raw_value)
                elif local_field == "long_task_id":
                    self._record_remote_conflict(entity_type, str(change.get("entity_id") or ""), local, change)
                    return False
                else:
                    setattr(local, local_field, None)
        return True

    def list_conflicts(self) -> SyncConflictListData:
        conflicts = self.db.scalars(select(SyncConflict).order_by(SyncConflict.created_at.desc(), SyncConflict.id.desc())).all()
        return SyncConflictListData(items=[SyncConflictRead.model_validate(item) for item in conflicts])

    def resolve_conflict(self, conflict_id: int, payload: SyncConflictResolveRequest) -> SyncConflictRead:
        conflict = self.db.get(SyncConflict, conflict_id)
        if conflict is None:
            raise AppException("sync conflict not found", code=4092, status_code=404)
        conflict.mark_resolved(payload.resolution)
        self.db.commit()
        self.db.refresh(conflict)
        return SyncConflictRead.model_validate(conflict)
