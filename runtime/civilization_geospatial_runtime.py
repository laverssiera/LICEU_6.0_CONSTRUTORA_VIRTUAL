from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Dict, Optional

try:
    import psycopg2
except Exception:  # pragma: no cover
    psycopg2 = None

logger = logging.getLogger(__name__)


class CivilizationGeospatialRuntime:
    """Gestao geoespacial com persistencia opcional em PostGIS e saida Cesium."""

    def __init__(self, postgis_dsn: Optional[str] = None) -> None:
        self._lock = RLock()
        self._positions: Dict[str, Dict[str, Any]] = {}
        self._dsn = self._normalize_dsn(postgis_dsn or os.getenv("POSTGIS_DSN") or os.getenv("DATABASE_URL"))
        self._postgis_enabled = False
        self._bootstrap_postgis()

    def _normalize_dsn(self, dsn: Optional[str]) -> Optional[str]:
        if not dsn:
            return None
        normalized = dsn.replace("postgresql+psycopg2://", "postgresql://")
        normalized = normalized.replace("postgresql+psycopg://", "postgresql://")
        return normalized

    def _bootstrap_postgis(self) -> None:
        if not self._dsn or psycopg2 is None:
            return

        try:
            with psycopg2.connect(self._dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS postgis")
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS civilization_twin_positions (
                            twin_id TEXT PRIMARY KEY,
                            latitude DOUBLE PRECISION NOT NULL,
                            longitude DOUBLE PRECISION NOT NULL,
                            altitude DOUBLE PRECISION NOT NULL DEFAULT 0,
                            captured_at TIMESTAMPTZ NOT NULL,
                            geom geometry(Point, 4326)
                        )
                        """
                    )
                conn.commit()
            self._postgis_enabled = True
        except Exception as exc:  # pragma: no cover
            logger.warning("PostGIS bootstrap unavailable: %s", exc)
            self._postgis_enabled = False

    def upsert_position(
        self,
        twin_id: str,
        latitude: float,
        longitude: float,
        altitude: float = 0.0,
        captured_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "twin_id": twin_id,
            "latitude": float(latitude),
            "longitude": float(longitude),
            "altitude": float(altitude),
            "captured_at": captured_at or datetime.now(timezone.utc).isoformat(),
        }

        with self._lock:
            self._positions[twin_id] = payload

        source = "memory"
        if self._postgis_enabled and self._dsn:
            try:
                with psycopg2.connect(self._dsn) as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO civilization_twin_positions (twin_id, latitude, longitude, altitude, captured_at, geom)
                            VALUES (%s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                            ON CONFLICT (twin_id)
                            DO UPDATE SET
                                latitude = EXCLUDED.latitude,
                                longitude = EXCLUDED.longitude,
                                altitude = EXCLUDED.altitude,
                                captured_at = EXCLUDED.captured_at,
                                geom = EXCLUDED.geom
                            """,
                            (
                                twin_id,
                                payload["latitude"],
                                payload["longitude"],
                                payload["altitude"],
                                payload["captured_at"],
                                payload["longitude"],
                                payload["latitude"],
                            ),
                        )
                    conn.commit()
                source = "postgis"
            except Exception as exc:  # pragma: no cover
                logger.warning("PostGIS upsert failed: %s", exc)

        return {"position": payload, "source": source}

    def get_latest_position(self, twin_id: str) -> Optional[Dict[str, Any]]:
        if self._postgis_enabled and self._dsn:
            try:
                with psycopg2.connect(self._dsn) as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            SELECT twin_id, latitude, longitude, altitude, captured_at
                            FROM civilization_twin_positions
                            WHERE twin_id = %s
                            """,
                            (twin_id,),
                        )
                        row = cur.fetchone()
                        if row:
                            return {
                                "twin_id": row[0],
                                "latitude": float(row[1]),
                                "longitude": float(row[2]),
                                "altitude": float(row[3]),
                                "captured_at": row[4].isoformat() if row[4] else None,
                            }
            except Exception as exc:  # pragma: no cover
                logger.warning("PostGIS lookup failed: %s", exc)

        with self._lock:
            return self._positions.get(twin_id)

    def to_cesium_entity(self, twin_id: str) -> Optional[Dict[str, Any]]:
        position = self.get_latest_position(twin_id)
        if not position:
            return None

        return {
            "id": twin_id,
            "name": f"Twin {twin_id}",
            "position": {
                "cartographicDegrees": [
                    position["longitude"],
                    position["latitude"],
                    position["altitude"],
                ]
            },
            "point": {
                "pixelSize": 12,
                "color": {"rgba": [0, 200, 255, 255]},
                "outlineColor": {"rgba": [255, 255, 255, 255]},
                "outlineWidth": 2,
            },
            "properties": {
                "captured_at": position.get("captured_at"),
            },
        }


geospatial_runtime = CivilizationGeospatialRuntime()
