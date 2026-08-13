from __future__ import annotations

from typing import Any, Dict

import httpx

from app.config import settings
from app.models.task import Task


class OperaGateway:
    def __init__(self, base_url: str | None = None, timeout_seconds: float | None = None) -> None:
        self.base_url = (base_url or settings.URL_OPERA).rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.OPERA_TIMEOUT_SECONDS

    def build_task_payload(self, task: Task) -> Dict[str, Any]:
        return {
            "task_id": task.id,
            "plan_id": task.plan_id,
            "title": task.title,
            "description": task.description,
            "assigned_to": task.assigned_to,
            "status": task.status,
            "priority": task.priority,
            "origin": "liceu-core-os",
        }

    def publish_task(self, task: Task) -> Dict[str, Any]:
        payload = self.build_task_payload(task)

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(f"{self.base_url}/tasks/sync", json=payload)

            if response.status_code >= 400:
                return {
                    "synced": False,
                    "status_code": response.status_code,
                    "detail": "OPERA returned non-success status",
                }

            return {
                "synced": True,
                "status_code": response.status_code,
                "detail": "Task sent to OPERA",
            }
        except Exception as exc:
            return {
                "synced": False,
                "status_code": None,
                "detail": f"OPERA unavailable: {exc}",
            }
