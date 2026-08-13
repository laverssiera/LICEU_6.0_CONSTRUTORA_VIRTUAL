from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4


class ContinentalDependencyRuntime:
    """Calcula e rastreia dependências entre regiões continentais."""

    def __init__(self) -> None:
        self._dependencies: Dict[str, Dict[str, Any]] = {}
        self._adjacency: Dict[str, Set[str]] = {}
        self._risk_map: Dict[str, float] = {}

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _dep_key(self, source: str, target: str) -> str:
        return f"{source}::{target}"

    # ── Dependency Registration ───────────────────────────────────────────────

    def register_dependency(
        self,
        source_region: str,
        target_region: str,
        dependency_type: str,
        strength: float = 1.0,
        continent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        dep_id = str(uuid4())
        key = self._dep_key(source_region, target_region)

        entry = {
            "dependency_id": dep_id,
            "key": key,
            "source_region": source_region,
            "target_region": target_region,
            "dependency_type": dependency_type,
            "strength": max(0.0, min(1.0, strength)),
            "continent": continent,
            "detected_at": self._utc_now(),
            "metadata": metadata or {},
        }
        self._dependencies[dep_id] = entry

        if source_region not in self._adjacency:
            self._adjacency[source_region] = set()
        self._adjacency[source_region].add(target_region)

        return deepcopy(entry)

    def calculate_dependencies(self, regions: List[str]) -> Dict[str, Any]:
        """Calcula dependências transitivas entre regiões."""
        if not regions:
            return {"regions": [], "dependencies": [], "transitive_count": 0}

        region_set = set(regions)
        relevant: List[Dict[str, Any]] = []
        for dep in self._dependencies.values():
            if dep["source_region"] in region_set or dep["target_region"] in region_set:
                relevant.append(deepcopy(dep))

        transitive = self._compute_transitive(region_set)

        return {
            "regions": regions,
            "direct_dependencies": relevant,
            "transitive_paths": transitive,
            "transitive_count": len(transitive),
            "calculated_at": self._utc_now(),
        }

    def _compute_transitive(self, region_set: Set[str]) -> List[Tuple[str, str]]:
        """BFS para dependências transitivas dentro do conjunto."""
        paths: List[Tuple[str, str]] = []
        visited: Set[str] = set()

        for origin in region_set:
            queue = list(self._adjacency.get(origin, set()))
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                if current in region_set and current != origin:
                    paths.append((origin, current))
                queue.extend(self._adjacency.get(current, set()))

        return paths

    # ── Risk ──────────────────────────────────────────────────────────────────

    def update_risk(self, region: str, risk_index: float) -> Dict[str, Any]:
        self._risk_map[region] = max(0.0, min(1.0, risk_index))
        return {"region": region, "risk_index": self._risk_map[region], "updated_at": self._utc_now()}

    def get_continental_risk(self, continent_regions: Optional[List[str]] = None) -> Dict[str, Any]:
        regions = continent_regions or list(self._risk_map.keys())
        values = [self._risk_map.get(r, 0.0) for r in regions]
        avg_risk = sum(values) / len(values) if values else 0.0
        return {
            "regions": regions,
            "risk_map": {r: self._risk_map.get(r, 0.0) for r in regions},
            "continental_risk_index": round(avg_risk, 4),
            "risk_level": self._risk_level(avg_risk),
        }

    def _risk_level(self, index: float) -> str:
        if index < 0.3:
            return "LOW"
        if index < 0.6:
            return "MODERATE"
        if index < 0.85:
            return "HIGH"
        return "CRITICAL"

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_dependency(self, dependency_id: str) -> Optional[Dict[str, Any]]:
        entry = self._dependencies.get(dependency_id)
        return deepcopy(entry) if entry else None

    def list_dependencies(self, continent: Optional[str] = None) -> List[Dict[str, Any]]:
        deps = self._dependencies.values()
        if continent:
            deps = (d for d in deps if d.get("continent") == continent)
        return [deepcopy(d) for d in deps]

    def get_dependents(self, region: str) -> List[str]:
        return [dep["source_region"] for dep in self._dependencies.values() if dep["target_region"] == region]

    def get_dependencies_of(self, region: str) -> List[str]:
        return list(self._adjacency.get(region, set()))

    def status(self) -> Dict[str, Any]:
        return {
            "total_dependencies": len(self._dependencies),
            "total_regions_tracked": len(self._adjacency),
            "risk_regions_tracked": len(self._risk_map),
        }


continental_dependency_runtime = ContinentalDependencyRuntime()
