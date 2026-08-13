from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from neo4j import GraphDatabase
except Exception:  # pragma: no cover
    GraphDatabase = None

logger = logging.getLogger(__name__)


class CivilizationGraphRuntime:
    """Grafo da civilizacao com persistencia opcional em Neo4j."""

    def __init__(
        self,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
    ) -> None:
        self._lock = RLock()
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._edges: Set[Tuple[str, str, str]] = set()
        self._driver = None

        uri = neo4j_uri or os.getenv("NEO4J_URI")
        user = neo4j_user or os.getenv("NEO4J_USER")
        password = neo4j_password or os.getenv("NEO4J_PASSWORD")

        if uri and user and password and GraphDatabase is not None:
            try:
                self._driver = GraphDatabase.driver(uri, auth=(user, password))
            except Exception as exc:  # pragma: no cover
                logger.warning("Neo4j unavailable: %s", exc)
                self._driver = None

    def upsert_twin_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        twin_id = str(state.get("twin_id") or "civilization-global")
        node = {
            "id": twin_id,
            "label": "CivilizationTwin",
            "status": state.get("status") or state.get("civilization_status") or "UNKNOWN",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "attributes": state.get("attributes") or {},
            "metrics": state.get("metrics") or {},
        }

        with self._lock:
            self._nodes[twin_id] = node

        self._upsert_neo4j_node(node)
        return node

    def register_sensor_event(self, twin_id: str, event: Dict[str, Any]) -> None:
        sensor_id = str(event.get("sensor_id") or "unknown-sensor")
        metric = str(event.get("metric") or "unknown")

        with self._lock:
            self._nodes.setdefault(
                sensor_id,
                {
                    "id": sensor_id,
                    "label": "Sensor",
                    "metric": metric,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            self._edges.add((sensor_id, "STREAMS_TO", twin_id))

        self._upsert_neo4j_edge(sensor_id=sensor_id, twin_id=twin_id, metric=metric)

    def get_graph(self, limit: int = 200) -> Dict[str, Any]:
        safe_limit = max(1, min(limit, 5000))

        with self._lock:
            nodes = list(self._nodes.values())[:safe_limit]
            edges = [
                {"from": item[0], "type": item[1], "to": item[2]}
                for item in list(self._edges)[:safe_limit]
            ]

        return {
            "nodes": nodes,
            "edges": edges,
            "counts": {
                "nodes": len(nodes),
                "edges": len(edges),
            },
        }

    def _upsert_neo4j_node(self, node: Dict[str, Any]) -> None:
        if self._driver is None:
            return
        try:
            with self._driver.session() as session:
                session.run(
                    """
                    MERGE (t:CivilizationTwin {id: $id})
                    SET t.status = $status,
                        t.updated_at = $updated_at,
                        t.attributes_json = $attributes_json,
                        t.metrics_json = $metrics_json
                    """,
                    id=node["id"],
                    status=node["status"],
                    updated_at=node["updated_at"],
                    attributes_json=json.dumps(node.get("attributes") or {}, ensure_ascii=True),
                    metrics_json=json.dumps(node.get("metrics") or {}, ensure_ascii=True),
                )
        except Exception as exc:  # pragma: no cover
            logger.warning("Neo4j node upsert failed: %s", exc)

    def _upsert_neo4j_edge(self, sensor_id: str, twin_id: str, metric: str) -> None:
        if self._driver is None:
            return
        try:
            with self._driver.session() as session:
                session.run(
                    """
                    MERGE (s:Sensor {id: $sensor_id})
                    SET s.metric = $metric
                    MERGE (t:CivilizationTwin {id: $twin_id})
                    MERGE (s)-[:STREAMS_TO]->(t)
                    """,
                    sensor_id=sensor_id,
                    twin_id=twin_id,
                    metric=metric,
                )
        except Exception as exc:  # pragma: no cover
            logger.warning("Neo4j edge upsert failed: %s", exc)


graph_runtime = CivilizationGraphRuntime()
