from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class CivilizationSnapshot:
    snapshot_id: str
    captured_at: str
    state: Dict[str, Any]
    score: Dict[str, Any]
    decision: Dict[str, Any]
    metadata: Dict[str, Any]


class CivilizationSnapshotRuntime:
    """Armazenamento em memoria de snapshots para auditoria rapida."""

    def __init__(self) -> None:
        self._snapshots: List[CivilizationSnapshot] = []

    def capture(
        self,
        state: Dict[str, Any],
        score: Dict[str, Any],
        decision: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        snapshot = CivilizationSnapshot(
            snapshot_id=str(uuid4()),
            captured_at=datetime.now(timezone.utc).isoformat(),
            state=state,
            score=score,
            decision=decision,
            metadata=metadata or {},
        )
        self._snapshots.append(snapshot)
        return asdict(snapshot)

    def latest(self) -> Optional[Dict[str, Any]]:
        if not self._snapshots:
            return None
        return asdict(self._snapshots[-1])

    def list_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        return [asdict(item) for item in self._snapshots[-limit:]]


snapshot_runtime = CivilizationSnapshotRuntime()
