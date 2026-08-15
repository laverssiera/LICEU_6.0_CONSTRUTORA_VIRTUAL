from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional


class GlobalCausalLineageRuntime:
    """Valida a cadeia causal global entre evento, decisão, execução, impacto e twin."""

    @staticmethod
    def _normalize_path(continent_path: Optional[Iterable[str]]) -> List[str]:
        if not continent_path:
            return []
        normalized: List[str] = []
        for item in continent_path:
            value = str(item).strip()
            if value and value not in normalized:
                normalized.append(value)
        return normalized

    def validate_global_lineage(
        self,
        continente_origem: Optional[str] = None,
        event_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        decision_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        impact_id: Optional[str] = None,
        continente_destino: Optional[str] = None,
        continent_path: Optional[List[str]] = None,
        twin_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        reasons: List[str] = []

        event_id = (event_id or kwargs.get("event") or "").strip()
        trace_id = (trace_id or kwargs.get("trace") or "").strip()
        decision_id = (decision_id or kwargs.get("decision") or "").strip()
        execution_id = (execution_id or kwargs.get("execution") or "").strip()
        impact_id = (impact_id or kwargs.get("impact") or "").strip()
        twin_id = (twin_id or kwargs.get("twin") or "").strip()
        continente_origem = (continente_origem or kwargs.get("origin_continent") or "").strip()
        continente_destino = (continente_destino or kwargs.get("destination_continent") or "").strip()

        if not trace_id:
            reasons.append("missing_trace_id")
        if not event_id:
            reasons.append("missing_event_id")
        if not decision_id:
            reasons.append("missing_decision_id")
        if not execution_id:
            reasons.append("missing_execution_id")
        if not impact_id:
            reasons.append("missing_impact_id")
        if not twin_id:
            reasons.append("missing_twin_id")

        path = self._normalize_path(continent_path)
        if continente_origem and not path:
            path = [continente_origem]
        if continente_destino and continente_destino not in path:
            path.append(continente_destino) if continente_destino else None
        if continente_origem and path and continente_origem not in path:
            path.insert(0, continente_origem)
        if continente_destino and path and continente_destino not in path:
            path.append(continente_destino)

        if not path and (continente_origem or continente_destino):
            path = []
            if continente_origem:
                path.append(continente_origem)
            if continente_destino:
                path.append(continente_destino)

        if not continent_path and continente_origem and continente_destino and continente_origem != continente_destino:
            path = [continente_origem, continente_destino]

        if continente_origem and continente_destino and path:
            try:
                origin_index = path.index(continente_origem)
                destination_index = path.index(continente_destino)
            except ValueError:
                origin_index = -1
                destination_index = -1
            if origin_index >= 0 and destination_index >= 0 and origin_index > destination_index:
                reasons.append("continent_path_out_of_order")

        if continente_origem and path and path[0] != continente_origem:
            reasons.append("continent_origin_mismatch")
        if continente_destino and path and path[-1] != continente_destino:
            reasons.append("continent_destination_mismatch")

        chain = [item for item in (event_id, decision_id, execution_id, impact_id, twin_id) if item]
        if chain and chain[0] != event_id:
            reasons.append("chain_order_invalid")

        global_lineage_valid = not reasons and bool(event_id and decision_id and execution_id and impact_id and twin_id)

        payload = {
            "global_lineage_valid": global_lineage_valid,
            "status": "PASS" if global_lineage_valid else "FAIL",
            "trace_id": trace_id,
            "continente_origem": continente_origem,
            "continente_destino": continente_destino,
            "event_id": event_id,
            "decision_id": decision_id,
            "execution_id": execution_id,
            "impact_id": impact_id,
            "twin_id": twin_id,
            "caused_by": event_id,
            "derived_from": decision_id,
            "propagated_to": deepcopy(path),
            "impacted": impact_id,
            "reconciled_by": twin_id,
            "chain": chain,
            "continent_path": deepcopy(path),
            "reasons": reasons,
        }

        if not payload["propagated_to"] and continente_origem and continente_destino:
            payload["propagated_to"] = [continente_origem, continente_destino]
            payload["continent_path"] = payload["propagated_to"]

        return payload


global_causal_lineage_runtime = GlobalCausalLineageRuntime()
