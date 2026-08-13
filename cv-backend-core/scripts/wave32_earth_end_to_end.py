from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List

from fastapi.testclient import TestClient

from app.main import app


CHAIN_STEPS: List[str] = [
    "OBSERVACAO",
    "EVENTO",
    "DIGITAL TWIN UPDATE",
    "CAUSAL ANALYSIS",
    "SCENARIO",
    "DECISION",
    "POLICY",
    "INVESTMENT",
    "PROCUREMENT",
    "EXECUTION",
    "MONITORING",
    "ECONOMIC IMPACT",
    "KNOWLEDGE",
    "AUDIT",
]


@dataclass
class GateResult:
    name: str
    status: str
    evidence: Dict[str, Any]


class Wave32EarthE2E:
    def __init__(self) -> None:
        self.client = TestClient(app)
        self.trace: List[Dict[str, Any]] = []

    def run(self) -> Dict[str, Any]:
        self._initialize_earth_runtime()
        self._run_chain()

        snapshot = self._get_snapshot()
        health = self.client.get("/earth/health").json()
        replay = self.client.post("/civilization/earth/replay", json={}).json()
        stress = self.client.post("/civilization/event-store/stress", json={}).json()
        telemetry = self.client.get("/telemetry/global").json()
        history = self.client.get("/earth/history").json()

        gates = self._evaluate_gates(
            snapshot=snapshot,
            health=health,
            replay=replay,
            stress=stress,
            telemetry=telemetry,
            history=history,
        )

        return {
            "wave": "WAVE_32",
            "scope": "EARTH",
            "status": "PASS" if all(g.status == "PASS" for g in gates) else "FAIL",
            "chain": CHAIN_STEPS,
            "trace": self.trace,
            "snapshot": snapshot,
            "health": health,
            "gates": [g.__dict__ for g in gates],
            "summary": {
                "pass": sum(1 for g in gates if g.status == "PASS"),
                "fail": sum(1 for g in gates if g.status != "PASS"),
            },
        }

    def _record(self, step: str, endpoint: str, response: Dict[str, Any]) -> None:
        self.trace.append(
            {
                "step": step,
                "endpoint": endpoint,
                "status": "ok",
                "response_excerpt": {
                    "status": response.get("status"),
                    "event_type": response.get("event", {}).get("event_type") if isinstance(response.get("event"), dict) else None,
                },
            }
        )

    def _initialize_earth_runtime(self) -> None:
        payload = {
            "seed": {
                "energy": {"renewable_share": 0.68},
                "economy": {"gdp_growth": 0.037},
                "health": {"coverage_index": 0.91},
            }
        }
        res = self.client.post("/earth/runtime/initialize", json=payload)
        res.raise_for_status()
        self._record("INIT", "/earth/runtime/initialize", res.json())

    def _post_event(self, step: str, event_type: str, payload: Dict[str, Any]) -> None:
        res = self.client.post("/earth/event", json={"event_type": event_type, "payload": payload})
        res.raise_for_status()
        self._record(step, "/earth/event", res.json())

    def _run_chain(self) -> None:
        chain_payloads = [
            ("OBSERVACAO", "SATELLITE_OBSERVATION", {"climate": {"risk_level": "moderate"}, "cities": {"critical_cities": 104}}),
            ("EVENTO", "ARCHIMEDES_EVENT_CLASSIFIED", {"infrastructure": {"status": "STABLE"}}),
            ("DIGITAL TWIN UPDATE", "DIGITAL_TWIN_UPDATED", {"infrastructure": {"availability": 0.994}}),
            ("CAUSAL ANALYSIS", "JOHN_CAUSAL_ANALYSIS", {"economy": {"gdp_growth": 0.038}}),
            ("SCENARIO", "CEFEIDA_SCENARIO_BUILT", {"climate": {"risk_level": "watch"}}),
            ("DECISION", "JOHN_DECISION_ISSUED", {"governance": {"policy_execution": 0.91}}),
            ("POLICY", "POLICY_APPLIED", {"governance": {"integrity_score": 0.96}}),
            ("INVESTMENT", "ECONOTECH_INVESTMENT_ALLOCATED", {"economy": {"gdp_growth": 0.039}}),
            ("PROCUREMENT", "SUPPLY_CHAIN_PROCUREMENT_RELEASED", {"logistics": {"on_time_delivery": 0.95}}),
            ("EXECUTION", "OPERA_EXECUTION_STARTED", {"infrastructure": {"critical_cities": 0}}),
            ("MONITORING", "BIM_MONITORING_UPDATED", {"energy": {"grid_stability": 0.98}}),
            ("ECONOMIC IMPACT", "CEA_ECONOMIC_IMPACT_MEASURED", {"economy": {"gdp_growth": 0.04}}),
            ("KNOWLEDGE", "ACADEMIA_KNOWLEDGE_STORED", {"population": {"status": "TRACKED"}}),
            ("AUDIT", "JURIDICOTECH_AUDIT_SIGNED", {"health": {"alerts": 0}}),
        ]

        for step, event_type, payload in chain_payloads:
            self._post_event(step, event_type, payload)

    def _get_snapshot(self) -> Dict[str, Any]:
        res = self.client.get("/earth/state/snapshot")
        res.raise_for_status()
        return res.json()

    def _evaluate_gates(
        self,
        *,
        snapshot: Dict[str, Any],
        health: Dict[str, Any],
        replay: Dict[str, Any],
        stress: Dict[str, Any],
        telemetry: Dict[str, Any],
        history: Dict[str, Any],
    ) -> List[GateResult]:
        criteria = health.get("criteria", {}) if isinstance(health, dict) else {}
        replay_info = replay.get("replay", {}) if isinstance(replay, dict) else {}
        earth_status = snapshot.get("status")

        integrations = telemetry.get("detalhes", {}) if isinstance(telemetry, dict) else {}
        online_count = sum(1 for v in integrations.values() if "ONLINE" in str(v).upper())

        return [
            GateResult("Earth Digital Twin", "PASS" if snapshot.get("digital_twin") == "SYNCHRONIZED" else "FAIL", {"digital_twin": snapshot.get("digital_twin")}),
            GateResult("Earth Spatial/Event Federation", "PASS" if criteria.get("Event Store") == "ACTIVE" else "FAIL", {"event_store": criteria.get("Event Store")}),
            GateResult("Event Store + Replay", "PASS" if stress.get("integrity") == "PASS" and replay_info.get("matches_current_state") else "FAIL", {"stress_integrity": stress.get("integrity"), "replay_match": replay_info.get("matches_current_state")}),
            GateResult("Telemetry/Observability", "PASS" if online_count >= 8 else "FAIL", {"online_integrations": online_count, "total_integrations": len(integrations)}),
            GateResult("Scenario + Causal Engine", "PASS" if any("SCENARIO" in str(e.get("event_type", "")).upper() for e in history.get("events", [])) and any("CAUSAL" in str(e.get("event_type", "")).upper() for e in history.get("events", [])) else "FAIL", {"history_events": len(history.get("events", []))}),
            GateResult("Economic + Investment Model", "PASS" if any("ECONOMIC" in str(e.get("event_type", "")).upper() or "INVESTMENT" in str(e.get("event_type", "")).upper() for e in history.get("events", [])) else "FAIL", {"financial_exposure": snapshot.get("financial_exposure")}),
            GateResult("Supply Chain + BIM", "PASS" if any("PROCUREMENT" in str(e.get("event_type", "")).upper() for e in history.get("events", [])) and any("BIM" in str(e.get("event_type", "")).upper() for e in history.get("events", [])) else "FAIL", {"logistics": snapshot.get("logistics")}),
            GateResult("Policy + Legal + Trust", "PASS" if any("POLICY" in str(e.get("event_type", "")).upper() for e in history.get("events", [])) and any("AUDIT" in str(e.get("event_type", "")).upper() for e in history.get("events", [])) else "FAIL", {"audit_integrity": snapshot.get("audit_integrity")}),
            GateResult("Knowledge/Memory", "PASS" if any("KNOWLEDGE" in str(e.get("event_type", "")).upper() or "ACADEMIA" in str(e.get("event_type", "")).upper() for e in history.get("events", [])) else "FAIL", {"active_events": snapshot.get("active_events")}),
            GateResult("Earth End-to-End", "PASS" if earth_status == "OPERATIONAL" and len(self.trace) >= len(CHAIN_STEPS) else "FAIL", {"earth_status": earth_status, "trace_steps": len(self.trace)}),
        ]


def main() -> None:
    runner = Wave32EarthE2E()
    result = runner.run()
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
