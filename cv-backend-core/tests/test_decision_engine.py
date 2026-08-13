"""Tests para Decision Engine + Action Engine — LICEU 6.0 Nível 2"""
import pytest
from fastapi.testclient import TestClient


# ─── Unit tests: decision_engine.py ──────────────────────────────────────────

from app.services.decision_engine import (
    DecisionType,
    PriorityLevel,
    batch_evaluate,
    evaluate_event,
)


def test_decision_deal_created_assigns_broker():
    dec = evaluate_event({"event_type": "deal_created", "source": "archimedes"})
    assert dec is not None
    assert dec.type == DecisionType.PRIORITY
    assert dec.action == "assign_broker"
    assert dec.priority == PriorityLevel.HIGH


def test_decision_client_silent_triggers_followup():
    dec = evaluate_event(
        {"event_type": "client_silent", "source": "crm"},
        {"id": "c1", "stage": "negotiation", "silent_days": 5, "title": "Loft 101"},
    )
    assert dec is not None
    assert dec.type == DecisionType.FOLLOWUP
    assert dec.action == "send_whatsapp"


def test_decision_nda_signed_unlocks_properties():
    dec = evaluate_event({"event_type": "nda_signed", "source": "juridicotech"})
    assert dec is not None
    assert dec.type == DecisionType.UNLOCK
    assert dec.action == "unlock_properties"


def test_decision_legal_issue_blocks_deal():
    dec = evaluate_event({"event_type": "legal_issue_raised", "source": "juridicotech"})
    assert dec is not None
    assert dec.type == DecisionType.BLOCK
    assert dec.priority == PriorityLevel.CRITICAL
    assert dec.action == "block_deal"


def test_decision_high_heat_negotiation_force_close():
    dec = evaluate_event(
        {"event_type": "deal_created", "source": "archimedes"},
        {"id": "c2", "stage": "negotiation", "heat_score": 0.9, "title": "Cobertura 200"},
    )
    assert dec is not None
    assert dec.action == "force_close"
    assert dec.priority == PriorityLevel.CRITICAL


def test_decision_commission_released_insight():
    dec = evaluate_event({"event_type": "commission_released", "source": "hubbackoffice"})
    assert dec is not None
    assert dec.type == DecisionType.INSIGHT
    assert dec.action == "notify_commission"


def test_decision_monolith_degraded_triggers_incident():
    dec = evaluate_event({"event_type": "heartbeat", "source": "cefeida", "status": "degraded"})
    assert dec is not None
    assert dec.type == DecisionType.BLOCK
    assert dec.action == "trigger_incident"


def test_no_decision_for_unknown_event():
    dec = evaluate_event({"event_type": "some_untracked_event", "source": "core"})
    assert dec is None


def test_batch_evaluate_returns_all_relevant():
    events = [
        {"event_type": "deal_created", "source": "archimedes"},
        {"event_type": "nda_signed", "source": "juridicotech"},
        {"event_type": "some_untracked_event", "source": "core"},
    ]
    decisions = batch_evaluate(events)
    assert len(decisions) == 2


# ─── Unit tests: action_engine.py ────────────────────────────────────────────

from app.services.action_engine import available_actions, execute_action
from app.services.autonomous_engine import build_state, decide
from app.services.innovation_engine import build_state as build_innovation_state, decide as decide_innovation


def test_execute_assign_broker_returns_ok():
    result = execute_action("assign_broker", {"card_id": "c99", "source": "crm"})
    assert result["status"] == "ok"
    assert "assigned_broker" in result["result"]


def test_execute_block_deal_returns_ok():
    result = execute_action("block_deal", {"card_id": "c10", "reason": "legal_pending"})
    assert result["status"] == "ok"
    assert result["result"]["status"] == "blocked"


def test_execute_send_whatsapp_returns_ok():
    result = execute_action("send_whatsapp", {"phone": "+5511999", "message": "Olá!"})
    assert result["status"] == "ok"
    assert result["result"]["channel"] == "whatsapp"


def test_execute_unknown_action_raises():
    with pytest.raises(ValueError, match="não registrada"):
        execute_action("does_not_exist", {})


def test_available_actions_returns_list():
    actions = available_actions()
    assert "assign_broker" in actions
    assert "block_deal" in actions
    assert "send_whatsapp" in actions
    assert "launch_experiment" in actions
    assert len(actions) >= 7


def test_autonomous_build_state_extracts_bottlenecks_and_top_monolith():
    state = build_state(
        {
            "kpis": {
                "estimated_revenue": 100000,
                "pipeline_value": 300000,
                "active_deals": 12,
                "active_leads": 40,
                "conversion_rate": 8,
                "juridico_cards": 3,
                "high_risk_cards": 2,
            },
            "financeiro": {"accounts_receivable": 200000, "estimated_revenue": 100000},
            "monolith_status": [{"name": "juridicotech", "status": "degraded"}],
            "performance": [{"source": "archimedes", "revenue": 90000}],
            "risk_signals": [{"card_id": "c1"}, {"card_id": "c2"}, {"card_id": "c3"}],
        }
    )
    assert state["risk_level"] == "high"
    assert "legal" in state["bottlenecks"]
    assert "finance" in state["bottlenecks"]
    assert state["top_monolith"] == "archimedes"


def test_autonomous_decide_generates_macro_actions():
    decisions = decide(
        {
            "risk_level": "high",
            "conversion_rate": 0.05,
            "bottlenecks": ["legal", "finance"],
            "active_deals": 8,
        }
    )
    actions = {item["action"] for item in decisions}
    assert "reduce_exposure" in actions
    assert "boost_marketing" in actions
    assert "prioritize_legal" in actions
    assert "tighten_finance" in actions


def test_innovation_build_state_defines_budget_guardrails():
    state = build_innovation_state(
        {
            "kpis": {
                "pipeline_value": 500000,
                "estimated_revenue": 150000,
            },
            "performance": [{"source": "archimedes", "revenue": 100000}],
            "risk_signals": [{"card_id": "c1"}],
        },
        {"risk_level": "medium", "bottlenecks": ["legal"]},
    )
    assert state["available_budget"] > 0
    assert state["budget_guard_limit"] > 0
    assert state["top_monolith"] == "archimedes"


def test_innovation_decide_blocks_misaligned_or_overbudget_experiments():
    ideas = decide_innovation(
        {
            "available_budget": 50000,
            "budget_guard_limit": 10000,
            "risk_level": "high",
            "bottlenecks": ["legal"],
        },
        {
            "kpis": {"active_leads": 10, "conversion_rate": 8},
            "performance": [{"source": "archimedes", "revenue": 90000}],
            "risk_signals": [{"card_id": "c1"}],
        },
    )
    assert any(item["status"] == "testing" for item in ideas)
    assert any(item["status"] == "blocked" for item in ideas)
    blocked = [item for item in ideas if item["status"] == "blocked"]
    assert any(item["governance"]["blocked_reasons"] for item in blocked)


# ─── Integration tests: /decisions endpoints ─────────────────────────────────

from app.main import app as _app

@pytest.fixture(scope="module")
def client():
    """TestClient com SQLite de testes."""
    with TestClient(_app) as c:
        yield c


def test_decisions_list_empty_initially(client):
    r = client.get("/decisions")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert isinstance(data["decisions"], list)


def test_decisions_process_deal_created(client):
    r = client.post("/decisions/process", json={"event_type": "deal_created", "source": "test_suite"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "decision_generated"
    assert data["decision"]["action"] == "assign_broker"


def test_decisions_process_unknown_no_decision(client):
    r = client.post("/decisions/process", json={"event_type": "completely_unknown", "source": "test"})
    assert r.status_code == 200
    assert r.json()["status"] == "no_decision"


def test_decisions_execute_action(client):
    # Gerar decisão
    r1 = client.post("/decisions/process", json={"event_type": "nda_signed", "source": "test"})
    assert r1.status_code == 200
    dec_id = r1.json()["decision"]["id"]

    # Executar
    r2 = client.post(f"/decisions/{dec_id}/execute")
    assert r2.status_code == 200
    data = r2.json()
    assert data["status"] == "executed"
    assert data["result"]["status"] == "ok"


def test_decisions_execute_idempotent(client):
    r1 = client.post("/decisions/process", json={"event_type": "commission_released", "source": "test"})
    dec_id = r1.json()["decision"]["id"]

    client.post(f"/decisions/{dec_id}/execute")
    r2 = client.post(f"/decisions/{dec_id}/execute")
    assert r2.json()["status"] == "already_executed"


def test_decisions_execute_404_unknown(client):
    r = client.post("/decisions/00000000-0000-0000-0000-000000000000/execute")
    assert r.status_code == 404


def test_decisions_actions_list(client):
    r = client.get("/decisions/actions")
    assert r.status_code == 200
    assert "assign_broker" in r.json()["actions"]


def test_decisions_batch_process(client):
    r = client.post("/decisions/batch", json={
        "events": [
            {"event_type": "deal_created", "source": "archimedes"},
            {"event_type": "nda_signed", "source": "juridicotech"},
        ]
    })
    assert r.status_code == 200
    data = r.json()
    assert data["processed"] == 2
    assert len(data["decisions"]) == 2


def test_autonomous_state_returns_snapshot(client):
    r = client.get("/autonomous/state")
    assert r.status_code == 200
    payload = r.json()
    assert payload["status"] == "ok"
    assert "state" in payload
    assert payload["state"]["mode"] in {"AUTO", "SEMI", "MANUAL"}


def test_autonomous_mode_patch_and_evaluate(client):
    r1 = client.patch("/autonomous/mode", json={"mode": "AUTO"})
    assert r1.status_code == 200
    assert r1.json()["mode"] == "AUTO"

    r2 = client.post("/autonomous/evaluate")
    assert r2.status_code == 200
    payload = r2.json()
    assert payload["status"] == "ok"
    assert payload["mode"] == "AUTO"
    assert isinstance(payload["decisions"], list)


def test_autonomous_override_and_rollback(client):
    override = client.post(
        "/autonomous/override",
        json={
            "action": "prioritize_legal",
            "target": "juridicotech",
            "reason": "Override manual de teste",
            "payload": {"target": "juridicotech"},
        },
    )
    assert override.status_code == 200
    action_id = override.json()["action"]["id"]

    rollback = client.post(f"/autonomous/actions/{action_id}/rollback")
    assert rollback.status_code == 200
    assert rollback.json()["status"] == "rolled_back"


def test_autonomous_override_blocks_illegal_close(client):
    blocked = client.post(
        "/autonomous/override",
        json={
            "action": "close_deal",
            "target": "juridicotech",
            "reason": "Tentativa sem contrato",
            "payload": {"deal_id": "d1"},
            "contract_signed": False,
        },
    )
    assert blocked.status_code == 403


def test_innovation_state_returns_snapshot(client):
    r = client.get("/innovation/state")
    assert r.status_code == 200
    payload = r.json()
    assert payload["status"] == "ok"
    assert payload["state"]["mode"] in {"AUTO", "SUPERVISED", "RESTRICTED"}
    assert isinstance(payload["ideas"], list)


def test_innovation_mode_patch_and_evaluate(client):
    r1 = client.patch("/innovation/mode", json={"mode": "AUTO"})
    assert r1.status_code == 200
    assert r1.json()["mode"] == "AUTO"

    r2 = client.post("/innovation/evaluate")
    assert r2.status_code == 200
    payload = r2.json()
    assert payload["status"] == "ok"
    assert payload["mode"] == "AUTO"
    assert isinstance(payload["ideas"], list)
    assert all("governance" in item for item in payload["ideas"])


def test_innovation_actions_list(client):
    r = client.get("/innovation/actions")
    assert r.status_code == 200
    payload = r.json()
    assert payload["status"] == "ok"
    assert isinstance(payload["actions"], list)


def test_executive_state_returns_snapshot(client):
    r = client.get("/executive/state")
    assert r.status_code == 200
    payload = r.json()
    assert payload["status"] == "ok"
    assert payload["state"]["mode"] in {"AUTO", "SUPERVISED", "MANUAL"}
    assert "monoliths" in payload["state"]


def test_executive_mode_patch_and_evaluate(client):
    r1 = client.patch("/executive/mode", json={"mode": "SUPERVISED"})
    assert r1.status_code == 200
    assert r1.json()["mode"] == "SUPERVISED"

    r2 = client.post("/executive/evaluate")
    assert r2.status_code == 200
    payload = r2.json()
    assert payload["status"] == "ok"
    assert payload["mode"] == "SUPERVISED"
    assert isinstance(payload["decisions"], list)


def test_executive_override_feedback_and_rollback(client):
    override = client.post(
        "/executive/override",
        json={
            "action": "freeze_investments",
            "target": "all_monoliths",
            "reason": "Override de teste",
            "payload": {"target": "all_monoliths"},
            "legal_approved": True,
            "treasury_limit": 1000000,
            "requested_budget": 50000,
            "core_aligned": True,
        },
    )
    assert override.status_code == 200
    action_id = override.json()["action"]["id"]

    feedback = client.post(
        "/executive/feedback",
        json={
            "decision": "freeze_investments",
            "success": True,
            "impact_score": 0.2,
            "notes": "resultado de teste",
        },
    )
    assert feedback.status_code == 200
    assert feedback.json()["status"] == "ok"

    rollback = client.post(f"/executive/actions/{action_id}/rollback")
    assert rollback.status_code == 200
    assert rollback.json()["status"] == "rolled_back"
