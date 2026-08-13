from fastapi.testclient import TestClient
from sqlalchemy import text

from app.internal import event_bus
from app.database import SessionLocal
from app.main import app
from app.models.orchestration import AuditAction, AuditEvent, AuditLog, HealthScore, ImmutableAuditLog, InvestmentEligibilityDecision, RecoveryPlan
from app.services.opera_gateway import OperaGateway

client = TestClient(app)


def _auth_headers(username: str, password: str = "demo123") -> dict[str, str]:
    token_response = client.post(
        "/auth/sso/login",
        json={"username": username, "password": password, "portal": "workspace"},
    )
    assert token_response.status_code == 200
    access_token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


DEFAULT_HEADERS = _auth_headers("irmandade_demo")
client.headers.update(DEFAULT_HEADERS)


def _reset_event_bus_messages() -> None:
    event_bus._fallback_bus.messages = []


def _reset_audit_state() -> None:
    db = SessionLocal()
    try:
        db.query(ImmutableAuditLog).delete()
        db.query(AuditAction).delete()
        db.query(AuditLog).filter(AuditLog.entity_type.in_(["audit_event", "audit_action", "investment_eligibility"])).delete(synchronize_session=False)
        db.query(AuditEvent).delete()
        db.commit()
    finally:
        db.close()


def _reset_hospital_state() -> None:
    db = SessionLocal()
    try:
        db.query(InvestmentEligibilityDecision).delete()
        db.query(RecoveryPlan).delete()
        db.query(HealthScore).delete()
        db.commit()
    finally:
        db.close()


def _reset_business_flow_state() -> None:
    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM business_cases"))
        db.execute(text("DELETE FROM training_assignments"))
        db.execute(text("DELETE FROM trainings"))
        db.execute(text("DELETE FROM process_updates"))
        db.execute(text("DELETE FROM processes"))
        db.execute(text("DELETE FROM project_tasks"))
        db.execute(text("DELETE FROM projects"))
        db.execute(text("DELETE FROM business_stage_history"))
        db.execute(text("DELETE FROM business_pipeline"))
        db.execute(text("DELETE FROM dre_entries"))
        db.commit()
    finally:
        db.close()


def test_rbac_denies_strategy_creation_for_client_profile():
    denied = client.post(
        "/strategies",
        json={
            "name": "Sem permissao",
            "description": "Cliente nao pode criar estrategia",
            "priority": "normal",
            "status": "backlog",
        },
        headers=_auth_headers("cliente_demo"),
    )

    assert denied.status_code == 403


def test_business_pipeline_first_flow_e2e_with_audit_and_training():
    _reset_event_bus_messages()
    _reset_audit_state()
    _reset_hospital_state()
    _reset_business_flow_state()

    # 1) criar negocio
    created = client.post(
        "/business-pipeline",
        json={
            "title": "Empreendimento 20 casas",
            "portfolio": "Obras Comuns",
            "program": "Residencial",
            "stage": "Ideia",
            "estimated_cost": 2000000,
            "expected_return": 3200000,
        },
    )
    assert created.status_code == 200
    pipeline_id = created.json()["business"]["id"]

    # 2) aprovar
    approved = client.patch(
        f"/business-pipeline/{pipeline_id}",
        json={"stage": "Aprovado"},
    )
    assert approved.status_code == 200
    assert approved.json()["business"]["stage"] == "Aprovado"

    runtime = client.get(f"/business-pipeline/{pipeline_id}/runtime")
    assert runtime.status_code == 200
    runtime_payload = runtime.json()

    # 3) ver projeto nascer
    project = runtime_payload["project"]
    assert project is not None
    project_id = project["id"]
    assert project["status"] in {"planned", "in_progress"}

    # 4) ver task aparecer
    task_names = [item["task_name"].lower() for item in runtime_payload["tasks"]]
    assert "terraplanagem" in task_names
    assert "fundação" in task_names
    assert "estrutura" in task_names

    # 5) simular erro de execução
    completion = client.post(
        f"/projects/{project_id}/tasks/complete",
        json={
            "task": "fundação",
            "has_error": True,
            "error_description": "Falha de execução da fundação em campo",
            "assigned_to": "obra.team.alpha",
        },
    )
    assert completion.status_code == 200
    completion_payload = completion.json()
    assert completion_payload["task"]["status"] == "completed"

    # 6) ver auditoria agir
    assert completion_payload["audit_event"] is not None
    assert completion_payload["audit_event"]["entity_id"] == project_id
    assert completion_payload["audit_event"]["severity"] in {"HIGH", "CRITICAL"}

    # 7) ver treinamento surgir
    assert completion_payload["training"] is not None
    assert completion_payload["training"]["status"] == "assigned"

    runtime_after_error = client.get(f"/business-pipeline/{pipeline_id}/runtime")
    assert runtime_after_error.status_code == 200
    after_payload = runtime_after_error.json()
    assert after_payload["trainings"]
    assert after_payload["audit_events"]

    channels = [entry.get("channel") for entry in event_bus.get_event_bus().recent_messages(limit=200)]
    for expected_channel in [
        "business.created",
        "business.approved",
        "project.created",
        "execution.started",
        "task.completed",
        "audit.detected",
        "training.required",
        "process.updated",
        "financial.updated",
    ]:
        assert expected_channel in channels

    timeline = client.get(f"/business-pipeline/{pipeline_id}/timeline")
    assert timeline.status_code == 200
    timeline_payload = timeline.json()
    assert timeline_payload["pipeline_id"] == pipeline_id
    assert timeline_payload["project_id"] == project_id
    assert any(item["channel"] == "business.approved" for item in timeline_payload["events"])
    assert any(item["channel"] == "execution.started" for item in timeline_payload["events"])

    steps = {item["name"]: item["done"] for item in timeline_payload["steps"]}
    assert steps["business.created"] is True
    assert steps["business.approved"] is True
    assert steps["project.created"] is True
    assert steps["execution.started"] is True
    assert steps["task.completed"] is True
    assert steps["audit.detected"] is True
    assert steps["training.required"] is True
    assert steps["process.updated"] is True
    assert steps["financial.updated"] is True

    timeline_filtered = client.get(f"/business-pipeline/{pipeline_id}/timeline?hours=24&limit=2&offset=1")
    assert timeline_filtered.status_code == 200
    filtered_payload = timeline_filtered.json()
    assert filtered_payload["filters"]["hours"] == 24
    assert filtered_payload["filters"]["limit"] == 2
    assert filtered_payload["filters"]["offset"] == 1
    assert filtered_payload["pagination"]["total"] >= len(filtered_payload["events"])
    assert filtered_payload["pagination"]["returned"] == len(filtered_payload["events"])
    assert len(filtered_payload["events"]) <= 2

    finance = client.post(f"/projects/{project_id}/finance/realize")
    assert finance.status_code == 200
    finance_payload = finance.json()
    assert finance_payload["project_id"] == project_id
    assert "margem" in finance_payload
    assert "payback" in finance_payload

    closed = client.post(
        f"/business-pipeline/{pipeline_id}/close",
        json={
            "lessons_learned": "Execucao com correcao de fundacao e ganho de maturidade operacional.",
            "duration": 18,
            "success": True,
        },
    )
    assert closed.status_code == 200
    closed_payload = closed.json()
    assert closed_payload["status"] == "closed"
    assert closed_payload["business_case"]["project_id"] == project_id
    assert closed_payload["business_case"]["duration"] == 18
    assert closed_payload["business_case"]["success"] is True

    timeline_after_close = client.get(f"/business-pipeline/{pipeline_id}/timeline")
    assert timeline_after_close.status_code == 200
    timeline_after_close_payload = timeline_after_close.json()
    assert any(item["channel"] == "business.closed" for item in timeline_after_close_payload["events"])
    final_steps = {item["name"]: item["done"] for item in timeline_after_close_payload["steps"]}
    assert final_steps["business.closed"] is True


def test_business_first_flow_demo_endpoint_executes_complete_playbook():
    _reset_event_bus_messages()
    _reset_audit_state()
    _reset_hospital_state()
    _reset_business_flow_state()

    response = client.post(
        "/business-pipeline/demo/first-flow",
        json={
            "title": "Empreendimento 20 casas",
            "portfolio": "Obras Comuns",
            "program": "Residencial",
            "estimated_cost": 2000000,
            "expected_return": 3200000,
            "error_task": "fundação",
            "simulate_error": True,
            "assigned_to": "obra.team.alpha",
            "close_duration": 18,
            "timeline_hours": 24,
            "timeline_limit": 120,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["pipeline_id"]
    assert payload["project_id"]
    assert payload["steps"]["created"]["status"] == "created"
    assert payload["steps"]["approved"]["status"] == "updated"
    assert payload["steps"]["task_completion"]["status"] == "processed"
    assert payload["steps"]["financial"]["status"] == "ok"
    assert payload["steps"]["closed"]["status"] == "closed"

    timeline = payload["timeline"]
    assert timeline["pipeline_id"] == payload["pipeline_id"]
    assert timeline["project_id"] == payload["project_id"]
    channels = [item["channel"] for item in timeline["events"]]
    for expected in [
        "business.created",
        "business.approved",
        "project.created",
        "execution.started",
        "task.completed",
        "audit.detected",
        "training.required",
        "process.updated",
        "financial.updated",
        "business.closed",
    ]:
        assert expected in channels


def test_audit_engine_ingests_and_classifies_event():
    _reset_audit_state()
    created = client.post(
        "/audit/events/ingest",
        json={
            "event_type": "payment.overdue",
            "source": "hubbackoffice",
            "payload": {
                "project_id": "audit-hub-001",
                "title": "Pagamento atrasado de fornecedor",
                "risk": "high",
            },
        },
    )

    assert created.status_code == 200
    payload = created.json()
    assert payload["status"] == "ingested"
    assert payload["audit_event"]["audit_domain"] == "financial"
    assert payload["audit_event"]["severity"] == "HIGH"
    assert payload["audit_event"]["entity_id"] == "audit-hub-001"

    listed = client.get("/audit/events?source=hubbackoffice&severity=HIGH&limit=20")
    assert listed.status_code == 200
    assert any(item["id"] == payload["audit_event"]["id"] for item in listed.json()["items"])


def test_audit_listener_captures_monolith_events_from_bus():
    _reset_audit_state()
    _reset_event_bus_messages()
    warmup = client.get("/audit/events?limit=1")
    assert warmup.status_code == 200

    bus = event_bus.get_event_bus()
    bus.publish(
        "work.delay",
        {
            "source": "opera",
            "project_id": "audit-opera-001",
            "title": "Obra com atraso de execucao",
        },
    )
    bus.publish(
        "payment.overdue",
        {
            "source": "hubbackoffice",
            "project_id": "audit-hub-002",
            "title": "Pagamento vencido no hub",
        },
    )
    bus.publish(
        "bypass.detected",
        {
            "source": "juridicotech",
            "project_id": "audit-jur-001",
            "title": "Bypass contratual detectado",
        },
    )

    listed = client.get("/audit/events?limit=50")
    assert listed.status_code == 200
    items = listed.json()["items"]

    assert any(item["entity_id"] == "audit-opera-001" and item["audit_domain"] == "operations" for item in items)
    assert any(item["entity_id"] == "audit-hub-002" and item["audit_domain"] == "financial" for item in items)
    assert any(item["entity_id"] == "audit-jur-001" and item["severity"] == "CRITICAL" for item in items)


def test_audit_engine_escalates_recurrence_and_generates_actions():
    _reset_audit_state()
    payload = {
        "project_id": "audit-proc-001",
        "title": "Falha recorrente no fluxo operacional",
        "owner": "ops_director",
    }

    first = client.post(
        "/audit/events/ingest",
        json={
            "event_type": "process.deviation",
            "source": "opera",
            "payload": payload,
        },
    )
    assert first.status_code == 200
    assert first.json()["audit_event"]["severity"] == "MEDIUM"
    first_action_types = {item["action_type"] for item in first.json()["generated_actions"]}
    assert first_action_types == {"task"}

    second = client.post(
        "/audit/events/ingest",
        json={
            "event_type": "process.deviation",
            "source": "opera",
            "payload": payload,
        },
    )
    assert second.status_code == 200
    assert second.json()["audit_event"]["severity"] == "HIGH"
    second_action_types = {item["action_type"] for item in second.json()["generated_actions"]}
    assert second_action_types == {"task", "training", "process_update"}

    third = client.post(
        "/audit/events/ingest",
        json={
            "event_type": "process.deviation",
            "source": "opera",
            "payload": payload,
        },
    )
    assert third.status_code == 200
    assert third.json()["audit_event"]["payload"]["audit_context"]["recurrence_count"] >= 2

    actions = client.get("/audit/actions?action_type=training&limit=50")
    assert actions.status_code == 200
    assert any(item["audit_id"] == second.json()["audit_event"]["id"] for item in actions.json()["items"])


def test_immutable_audit_logs_preserve_chain_and_block_mutations():
    _reset_audit_state()

    created = client.post(
        "/audit/events/ingest",
        json={
            "event_type": "payment.overdue",
            "source": "hubbackoffice",
            "payload": {
                "project_id": "audit-immutable-001",
                "title": "Pagamento vencido para trilha imutavel",
                "risk": "high",
            },
        },
    )
    assert created.status_code == 200

    logs_response = client.get("/audit/immutable-logs?limit=100")
    assert logs_response.status_code == 200
    logs = logs_response.json()["items"]
    assert len(logs) >= 1
    assert all(item["hash_value"] for item in logs)

    verify_response = client.get("/audit/immutable-logs/verify")
    assert verify_response.status_code == 200
    assert verify_response.json()["valid"] is True
    assert verify_response.json()["total"] >= 1

    db = SessionLocal()
    try:
        first = db.query(ImmutableAuditLog).order_by(ImmutableAuditLog.created_at.asc()).first()
        assert first is not None
        first.action = "tampered.action"
        try:
            db.commit()
            assert False, "era esperado erro de imutabilidade"
        except Exception:
            db.rollback()
    finally:
        db.close()


def test_hospital_health_score_model_calculates_and_lists_history():
    _reset_audit_state()
    _reset_hospital_state()
    company_id = "supplier-hospital-001"

    events = [
        {
            "event_type": "payment.overdue",
            "source": "hubbackoffice",
            "payload": {"company_id": company_id, "title": "Fornecedor com fatura vencida", "risk": "high"},
        },
        {
            "event_type": "bypass.detected",
            "source": "juridicotech",
            "payload": {"company_id": company_id, "title": "Falha contratual critica"},
        },
        {
            "event_type": "runtime.outage",
            "source": "runtime",
            "payload": {"company_id": company_id, "title": "Instabilidade de sistema"},
        },
        {
            "event_type": "bypass.detected",
            "source": "juridicotech",
            "payload": {"company_id": company_id, "title": "Reincidencia contratual"},
        },
    ]

    for item in events:
        ingested = client.post("/audit/events/ingest", json=item)
        assert ingested.status_code == 200

    calculated = client.post(
        "/hospital/health-scores/recalculate",
        json={"company_id": company_id, "lookback_days": 90},
    )
    assert calculated.status_code == 200

    snapshot = calculated.json()["health_score"]
    assert snapshot["company_id"] == company_id
    assert set(snapshot["dimensions"].keys()) == {"financial", "operational", "compliance", "technology"}
    assert isinstance(snapshot["score"], int)
    assert snapshot["risk"] in {"low", "medium", "high", "critical"}

    second_snapshot = client.post(
        "/hospital/health-scores/recalculate",
        json={"company_id": company_id, "lookback_days": 90},
    )
    assert second_snapshot.status_code == 200

    listed = client.get("/hospital/health-scores?limit=50")
    assert listed.status_code == 200
    assert any(item["company_id"] == company_id for item in listed.json()["items"])

    filtered = client.get(f"/hospital/health-scores?risk={snapshot['risk']}&limit=50")
    assert filtered.status_code == 200
    assert any(item["company_id"] == company_id for item in filtered.json()["items"])

    history = client.get(f"/hospital/health-scores/{company_id}/history?limit=20")
    assert history.status_code == 200
    assert history.json()["company_id"] == company_id
    assert history.json()["total"] >= 2


def test_hospital_dashboard_highlights_deterioration_and_supports_filters():
    _reset_audit_state()
    _reset_hospital_state()

    stable_company = "supplier-hospital-stable"
    deteriorating_company = "supplier-hospital-deteriorating"

    # baseline snapshots with no recent incidents
    assert client.post("/hospital/health-scores/recalculate", json={"company_id": stable_company, "lookback_days": 90}).status_code == 200
    assert client.post("/hospital/health-scores/recalculate", json={"company_id": deteriorating_company, "lookback_days": 90}).status_code == 200

    # only deteriorating company receives critical incidents before a new recalculation
    critical_events = [
        {
            "event_type": "bypass.detected",
            "source": "juridicotech",
            "payload": {"company_id": deteriorating_company, "title": "Risco contratual 1"},
        },
        {
            "event_type": "bypass.detected",
            "source": "juridicotech",
            "payload": {"company_id": deteriorating_company, "title": "Risco contratual 2"},
        },
        {
            "event_type": "runtime.outage",
            "source": "runtime",
            "payload": {"company_id": deteriorating_company, "title": "Interrupcao de sistema"},
        },
    ]
    for event in critical_events:
        assert client.post("/audit/events/ingest", json=event).status_code == 200

    assert client.post("/hospital/health-scores/recalculate", json={"company_id": stable_company, "lookback_days": 90}).status_code == 200
    degraded = client.post(
        "/hospital/health-scores/recalculate",
        json={"company_id": deteriorating_company, "lookback_days": 90},
    )
    assert degraded.status_code == 200
    degraded_risk = degraded.json()["health_score"]["risk"]

    dashboard = client.get("/hospital/health-dashboard?period_days=90&limit=50")
    assert dashboard.status_code == 200
    rows = dashboard.json()["items"]
    assert any(item["company_id"] == stable_company for item in rows)
    deteriorating_row = next(item for item in rows if item["company_id"] == deteriorating_company)
    assert deteriorating_row["is_deteriorating"] is True
    assert deteriorating_row["trend"] == "down"

    only_deteriorating = client.get("/hospital/health-dashboard?period_days=90&deteriorating_only=true&limit=50")
    assert only_deteriorating.status_code == 200
    only_rows = only_deteriorating.json()["items"]
    assert any(item["company_id"] == deteriorating_company for item in only_rows)
    assert all(item["is_deteriorating"] is True for item in only_rows)

    risk_filtered = client.get(f"/hospital/health-dashboard?period_days=90&risk={degraded_risk}&limit=50")
    assert risk_filtered.status_code == 200
    assert any(item["company_id"] == deteriorating_company for item in risk_filtered.json()["items"])


def test_hospital_recovery_plan_is_created_and_tracks_score_evolution():
    _reset_audit_state()
    _reset_hospital_state()

    company_id = "supplier-recovery-001"

    baseline = client.post(
        "/hospital/health-scores/recalculate",
        json={"company_id": company_id, "lookback_days": 90},
    )
    assert baseline.status_code == 200
    assert baseline.json()["recovery_plan"] is None

    critical_events = [
        {
            "event_type": "bypass.detected",
            "source": "juridicotech",
            "payload": {"company_id": company_id, "title": "Falha contratual grave 1"},
        },
        {
            "event_type": "bypass.detected",
            "source": "juridicotech",
            "payload": {"company_id": company_id, "title": "Falha contratual grave 2"},
        },
        {
            "event_type": "payment.overdue",
            "source": "hubbackoffice",
            "payload": {"company_id": company_id, "title": "Inadimplencia fornecedor", "risk": "high"},
        },
        {
            "event_type": "runtime.outage",
            "source": "runtime",
            "payload": {"company_id": company_id, "title": "Queda de sistema 1"},
        },
        {
            "event_type": "runtime.outage",
            "source": "runtime",
            "payload": {"company_id": company_id, "title": "Queda de sistema 2"},
        },
        {
            "event_type": "process.deviation",
            "source": "opera",
            "payload": {"company_id": company_id, "title": "Desvio de processo 1", "risk": "high"},
        },
        {
            "event_type": "process.deviation",
            "source": "opera",
            "payload": {"company_id": company_id, "title": "Desvio de processo 2", "risk": "high"},
        },
        {
            "event_type": "payment.overdue",
            "source": "hubbackoffice",
            "payload": {"company_id": company_id, "title": "Inadimplencia adicional", "risk": "high"},
        },
    ]
    for item in critical_events:
        assert client.post("/audit/events/ingest", json=item).status_code == 200

    opened = client.post(
        "/hospital/health-scores/recalculate",
        json={"company_id": company_id, "lookback_days": 90},
    )
    assert opened.status_code == 200
    plan = opened.json()["recovery_plan"]
    assert plan is not None
    assert plan["status"] in {"in_progress", "aggravated"}
    assert plan["owner"] == "governance_ops"
    assert plan["due_at"] is not None
    assert len(plan["actions"]) >= 3

    assert client.post(
        "/audit/events/ingest",
        json={
            "event_type": "runtime.outage",
            "source": "runtime",
            "payload": {"company_id": company_id, "title": "Instabilidade adicional"},
        },
    ).status_code == 200

    aggravated = client.post(
        "/hospital/health-scores/recalculate",
        json={"company_id": company_id, "lookback_days": 90},
    )
    assert aggravated.status_code == 200
    aggravated_plan = aggravated.json()["recovery_plan"]
    assert aggravated_plan is not None
    assert aggravated_plan["id"] == plan["id"]
    assert aggravated_plan["status"] == "aggravated"
    history = aggravated_plan["context"].get("score_history") or []
    assert len(history) >= 2

    listed = client.get(f"/hospital/recovery-plans?company_id={company_id}&limit=20")
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1
    listed_plan = listed.json()["items"][0]
    assert listed_plan["id"] == plan["id"]

    updated = client.patch(
        f"/hospital/recovery-plans/{plan['id']}/status",
        json={"status": "completed", "note": "Intervencao aplicada e validada"},
    )
    assert updated.status_code == 200
    assert updated.json()["item"]["status"] == "completed"
    assert updated.json()["item"]["closed_at"] is not None

    completed_list = client.get("/hospital/recovery-plans?status=completed&limit=20")
    assert completed_list.status_code == 200
    assert any(item["id"] == plan["id"] for item in completed_list.json()["items"])


def test_hospital_investment_eligibility_supports_eligible_monitoring_and_restricted():
    _reset_audit_state()
    _reset_hospital_state()

    eligible_company = "supplier-invest-eligible"
    monitoring_company = "supplier-invest-monitoring"
    restricted_company = "supplier-invest-restricted"

    # eligible: score alto sem plano de recuperacao aberto
    assert client.post(
        "/hospital/health-scores/recalculate",
        json={"company_id": eligible_company, "lookback_days": 90},
    ).status_code == 200
    eligible_eval = client.post(
        "/hospital/investment-eligibility/evaluate",
        json={"company_id": eligible_company},
    )
    assert eligible_eval.status_code == 200
    assert eligible_eval.json()["item"]["decision"] == "eligible"

    # monitoring: score intermediario (60-79) via degradacao balanceada entre dimensoes
    monitoring_events = [
        {
            "event_type": "payment.overdue",
            "source": "hubbackoffice",
            "payload": {"company_id": monitoring_company, "title": "atraso financeiro", "risk": "high"},
        },
        {
            "event_type": "runtime.outage",
            "source": "runtime",
            "payload": {"company_id": monitoring_company, "title": "instabilidade tecnica"},
        },
        {
            "event_type": "bypass.detected",
            "source": "juridicotech",
            "payload": {"company_id": monitoring_company, "title": "alerta compliance"},
        },
        {
            "event_type": "process.deviation",
            "source": "opera",
            "payload": {"company_id": monitoring_company, "title": "desvio operacional", "blocking": True},
        },
    ]
    for event in monitoring_events:
        assert client.post("/audit/events/ingest", json=event).status_code == 200

    monitoring_health = client.post(
        "/hospital/health-scores/recalculate",
        json={"company_id": monitoring_company, "lookback_days": 90},
    )
    assert monitoring_health.status_code == 200
    monitoring_score = monitoring_health.json()["health_score"]["score"]
    assert 60 <= monitoring_score < 80

    monitoring_eval = client.post(
        "/hospital/investment-eligibility/evaluate",
        json={"company_id": monitoring_company},
    )
    assert monitoring_eval.status_code == 200
    assert monitoring_eval.json()["item"]["decision"] == "monitoring"

    # restricted: score baixo e plano agravado
    restricted_events = [
        {
            "event_type": "bypass.detected",
            "source": "juridicotech",
            "payload": {"company_id": restricted_company, "title": "falha critica 1"},
        },
        {
            "event_type": "bypass.detected",
            "source": "juridicotech",
            "payload": {"company_id": restricted_company, "title": "falha critica 2"},
        },
        {
            "event_type": "runtime.outage",
            "source": "runtime",
            "payload": {"company_id": restricted_company, "title": "queda 1"},
        },
        {
            "event_type": "runtime.outage",
            "source": "runtime",
            "payload": {"company_id": restricted_company, "title": "queda 2"},
        },
        {
            "event_type": "payment.overdue",
            "source": "hubbackoffice",
            "payload": {"company_id": restricted_company, "title": "inadimplencia 1", "risk": "high"},
        },
        {
            "event_type": "payment.overdue",
            "source": "hubbackoffice",
            "payload": {"company_id": restricted_company, "title": "inadimplencia 2", "risk": "high"},
        },
        {
            "event_type": "process.deviation",
            "source": "opera",
            "payload": {"company_id": restricted_company, "title": "desvio grave", "blocking": True},
        },
    ]
    for event in restricted_events:
        assert client.post("/audit/events/ingest", json=event).status_code == 200

    restricted_health = client.post(
        "/hospital/health-scores/recalculate",
        json={"company_id": restricted_company, "lookback_days": 90},
    )
    assert restricted_health.status_code == 200
    assert restricted_health.json()["health_score"]["score"] <= 60

    restricted_eval = client.post(
        "/hospital/investment-eligibility/evaluate",
        json={"company_id": restricted_company},
    )
    assert restricted_eval.status_code == 200
    restricted_item = restricted_eval.json()["item"]
    assert restricted_item["decision"] == "restricted"

    listed = client.get("/hospital/investment-eligibility?decision=restricted&limit=50")
    assert listed.status_code == 200
    assert any(item["company_id"] == restricted_company for item in listed.json()["items"])

    # rastreabilidade de auditoria da decisao
    db = SessionLocal()
    try:
        log = (
            db.query(AuditLog)
            .filter(AuditLog.entity_type == "investment_eligibility")
            .filter(AuditLog.entity_id == restricted_item["id"])
            .first()
        )
        assert log is not None
        assert log.action == "investment.eligibility.restricted"
    finally:
        db.close()


def test_multi_tenant_isolation_for_strategic_entities():
    liceu_created = client.post(
        "/strategies",
        json={
            "name": "Estrategia tenant Liceu",
            "description": "Dados isolados por tenant",
            "priority": "high",
            "status": "backlog",
        },
    )
    assert liceu_created.status_code == 200
    liceu_strategy_id = liceu_created.json()["strategy"]["id"]

    acme_headers = _auth_headers("executivo_acme")
    acme_created = client.post(
        "/strategies",
        json={
            "name": "Estrategia tenant ACME",
            "description": "Tenant secundario",
            "priority": "high",
            "status": "backlog",
        },
        headers=acme_headers,
    )
    assert acme_created.status_code == 200
    acme_strategy_id = acme_created.json()["strategy"]["id"]

    acme_list = client.get("/strategies", headers=acme_headers)
    assert acme_list.status_code == 200
    acme_ids = {item["id"] for item in acme_list.json()["items"]}
    assert acme_strategy_id in acme_ids
    assert liceu_strategy_id not in acme_ids

    acme_get_liceu = client.get(f"/strategies/{liceu_strategy_id}", headers=acme_headers)
    assert acme_get_liceu.status_code == 404

    liceu_list = client.get("/strategies")
    assert liceu_list.status_code == 200
    liceu_ids = {item["id"] for item in liceu_list.json()["items"]}
    assert liceu_strategy_id in liceu_ids
    assert acme_strategy_id not in liceu_ids

    liceu_get_acme = client.get(f"/strategies/{acme_strategy_id}")
    assert liceu_get_acme.status_code == 404


def test_strategy_crud_endpoints():
    created = client.post(
        "/strategies",
        json={
            "name": "Expansao regional 2026",
            "description": "Aumentar capilaridade em polos estrategicos",
            "priority": "high",
            "status": "backlog",
        },
    )
    assert created.status_code == 200
    created_payload = created.json()
    assert created_payload["status"] == "created"
    assert created_payload["strategic_card"]["stage"] == "backlog"
    strategy_id = created_payload["strategy"]["id"]

    listed = client.get("/strategies")
    assert listed.status_code == 200
    assert any(item["id"] == strategy_id for item in listed.json()["items"])

    fetched = client.get(f"/strategies/{strategy_id}")
    assert fetched.status_code == 200
    assert fetched.json()["strategy"]["name"] == "Expansao regional 2026"

    updated = client.patch(
        f"/strategies/{strategy_id}",
        json={"status": "planning", "priority": "critical"},
    )
    assert updated.status_code == 200
    assert updated.json()["strategy"]["status"] == "planning"
    assert updated.json()["strategy"]["priority"] == "critical"

    deleted = client.delete(f"/strategies/{strategy_id}")
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"

    missing = client.get(f"/strategies/{strategy_id}")
    assert missing.status_code == 404


def test_strategic_kanban_allows_adjacent_transition_and_blocks_jump():
    created = client.post(
        "/strategies",
        json={
            "name": "Estrategia kanban",
            "description": "Validar transicao estrategica",
            "priority": "high",
            "status": "backlog",
        },
    )
    assert created.status_code == 200
    card_id = created.json()["strategic_card"]["id"]

    moved = client.patch(
        f"/strategic-kanban/cards/{card_id}/stage",
        json={"stage": "planning"},
    )
    assert moved.status_code == 200
    assert moved.json()["card"]["stage"] == "planning"

    invalid = client.patch(
        f"/strategic-kanban/cards/{card_id}/stage",
        json={"stage": "done"},
    )
    assert invalid.status_code == 409
    assert invalid.json()["detail"] == "Transição estratégica inválida"


def test_strategic_audit_tracks_lifecycle_and_kanban_stage_changes():
    created = client.post(
        "/strategies",
        json={
            "name": "Estrategia auditavel",
            "description": "Validar trilha de auditoria completa",
            "priority": "high",
            "status": "backlog",
        },
    )
    assert created.status_code == 200
    payload = created.json()
    strategy_id = payload["strategy"]["id"]
    card_id = payload["strategic_card"]["id"]

    updated = client.patch(
        f"/strategies/{strategy_id}",
        json={"status": "planning", "priority": "critical"},
    )
    assert updated.status_code == 200

    moved = client.patch(
        f"/strategic-kanban/cards/{card_id}/stage",
        json={"stage": "executing"},
    )
    assert moved.status_code == 200
    assert moved.json()["card"]["stage"] == "executing"

    deleted = client.delete(f"/strategies/{strategy_id}")
    assert deleted.status_code == 200

    entity_audit = client.get(
        f"/strategic-audit?entity_type=strategic_strategy&entity_id={strategy_id}&limit=20"
    )
    assert entity_audit.status_code == 200
    entity_items = entity_audit.json()["items"]
    actions = {item["action"] for item in entity_items}
    assert "strategic.strategy.created" in actions
    assert "strategic.strategy.updated" in actions
    assert "strategic.strategy.deleted" in actions

    updated_entry = next(item for item in entity_items if item["action"] == "strategic.strategy.updated")
    assert updated_entry["delta"]["status"]["from"] == "backlog"
    assert updated_entry["delta"]["status"]["to"] == "planning"

    kanban_audit = client.get(
        f"/strategic-audit?entity_type=strategic_kanban_card&entity_id={card_id}&limit=20"
    )
    assert kanban_audit.status_code == 200
    kanban_items = kanban_audit.json()["items"]
    assert any(item["action"] == "strategic.kanban.stage_changed" for item in kanban_items)
    stage_entry = next(item for item in kanban_items if item["action"] == "strategic.kanban.stage_changed")
    assert stage_entry["delta"]["stage"]["from"] == "planning"
    assert stage_entry["delta"]["stage"]["to"] == "executing"


def test_strategic_john_suggestions_follow_context_and_tenant_isolation():
    strategy = client.post(
        "/strategies",
        json={
            "name": "Estrategia Academia John",
            "description": "Capacitar operacao com apoio da academia",
            "priority": "high",
            "status": "planning",
        },
    )
    assert strategy.status_code == 200
    strategy_id = strategy.json()["strategy"]["id"]

    objective = client.post(
        "/objectives",
        json={
            "strategy_id": strategy_id,
            "metric": "Times capacitados",
            "target": 40,
            "deadline": "2026-12-31T00:00:00Z",
            "status": "planning",
        },
    )
    assert objective.status_code == 200
    objective_id = objective.json()["objective"]["id"]

    initiative = client.post(
        "/initiatives",
        json={
            "objective_id": objective_id,
            "name": "Treinamento de squad de obra",
            "description": "Trilha de treinamento para equipe operacional em campo",
            "initiative_type": "training",
            "owner": "academy_ops_lead",
            "status": "planning",
        },
    )
    assert initiative.status_code == 200
    initiative_payload = initiative.json()
    initiative_id = initiative_payload["initiative"]["id"]
    card_id = initiative_payload["strategic_card"]["id"]

    suggested = client.get(
        f"/strategic-suggestions/initiative/{initiative_id}?focus=plano%20de%20capacitacao"
    )
    assert suggested.status_code == 200
    suggestion_payload = suggested.json()
    assert suggestion_payload["status"] == "ok"
    assert suggestion_payload["suggestion"]["target_john"] == "JOHN_ACADEMIA"
    assert suggestion_payload["suggestion"]["target_monolith"] == "academia_saber"
    assert suggestion_payload["suggestion"]["recommended_action"] == "detalhar plano"
    assert "Trilhas de formação" in suggestion_payload["suggestion"]["summary"]
    assert suggestion_payload["telemetry"]["tenant"] == "liceu"
    assert suggestion_payload["card_id"] == card_id

    board = client.get("/strategic-kanban/board?actor=academy_ops_lead&stage=planning")
    assert board.status_code == 200
    planning_column = next(column for column in board.json()["columns"] if column["id"] == "planning")
    initiative_card = next(item for item in planning_column["items"] if item["id"] == card_id)
    assert initiative_card["john"]["target_john"] == "JOHN_ACADEMIA"
    assert initiative_card["john"]["target_monolith"] == "academia_saber"

    audit = client.get(
        f"/strategic-audit?entity_type=strategic_initiative&entity_id={initiative_id}&limit=20"
    )
    assert audit.status_code == 200
    assert any(item["action"] == "strategic.john.suggestion.generated" for item in audit.json()["items"])

    denied = client.get(
        f"/strategic-suggestions/initiative/{initiative_id}",
        headers=_auth_headers("executivo_acme"),
    )
    assert denied.status_code == 404


def test_strategic_kanban_board_filters_by_portfolio_monolith_and_actor():
    created = client.post(
        "/strategies",
        json={
            "name": "Estrategia board",
            "description": "Filtro do board estrategico",
            "priority": "high",
            "status": "planning",
        },
    )
    strategy_id = created.json()["strategy"]["id"]

    objective = client.post(
        "/objectives",
        json={
            "strategy_id": strategy_id,
            "metric": "Entrega filtrada",
            "target": 10,
            "deadline": "2026-12-31T00:00:00Z",
            "status": "planning",
        },
    )
    objective_id = objective.json()["objective"]["id"]

    initiative = client.post(
        "/initiatives",
        json={
            "objective_id": objective_id,
            "name": "Fluxo operacional",
            "description": "Roteamento para opera",
            "initiative_type": "process",
            "owner": "ops_manager",
            "status": "planning",
        },
    )
    assert initiative.status_code == 200

    board = client.get(
        "/strategic-kanban/board?portfolio=strategic_planning&monolith=opera&actor=ops_manager&stage=planning"
    )
    assert board.status_code == 200
    payload = board.json()
    assert payload["status"] == "ok"
    assert payload["filters"]["portfolio"] == "strategic_planning"
    assert payload["filters"]["monolith"] == "opera"
    assert payload["filters"]["actor"] == "ops_manager"

    planning_column = next(column for column in payload["columns"] if column["id"] == "planning")
    assert any(item["entity_type"] == "strategic_initiative" for item in planning_column["items"])
    assert payload["kpis"]["total_cards"] >= 1


def test_objective_crud_endpoints_with_strategy_relationship():
    strategy = client.post(
        "/strategies",
        json={
            "name": "OKR Growth 2026",
            "description": "Estrutura mestra de crescimento",
            "priority": "high",
            "status": "planning",
        },
    )
    assert strategy.status_code == 200
    strategy_id = strategy.json()["strategy"]["id"]

    created = client.post(
        "/objectives",
        json={
            "strategy_id": strategy_id,
            "metric": "MRR",
            "target": 1500000,
            "deadline": "2026-12-31T00:00:00Z",
            "status": "backlog",
        },
    )
    assert created.status_code == 200
    payload = created.json()
    assert payload["status"] == "created"
    assert payload["objective"]["strategy_id"] == strategy_id
    objective_id = payload["objective"]["id"]

    listed = client.get(f"/objectives?strategy_id={strategy_id}")
    assert listed.status_code == 200
    assert any(item["id"] == objective_id for item in listed.json()["items"])

    fetched = client.get(f"/objectives/{objective_id}")
    assert fetched.status_code == 200
    assert fetched.json()["objective"]["metric"] == "MRR"

    updated = client.patch(
        f"/objectives/{objective_id}",
        json={"status": "planning", "target": 1800000},
    )
    assert updated.status_code == 200
    assert updated.json()["objective"]["status"] == "planning"
    assert updated.json()["objective"]["target"] == 1800000

    deleted = client.delete(f"/objectives/{objective_id}")
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"

    missing = client.get(f"/objectives/{objective_id}")
    assert missing.status_code == 404


def test_objective_creation_fails_when_strategy_does_not_exist():
    created = client.post(
        "/objectives",
        json={
            "strategy_id": 999999,
            "metric": "NPS",
            "target": 80,
            "deadline": "2026-12-31T00:00:00Z",
            "status": "backlog",
        },
    )

    assert created.status_code == 404
    assert created.json()["detail"] == "Strategy não encontrada"


def test_initiative_crud_endpoints_with_objective_relationship():
    _reset_event_bus_messages()
    strategy = client.post(
        "/strategies",
        json={
            "name": "Estrategia de produtividade",
            "description": "Acelerar entrega com melhor alocacao",
            "priority": "high",
            "status": "planning",
        },
    )
    assert strategy.status_code == 200
    strategy_id = strategy.json()["strategy"]["id"]

    objective = client.post(
        "/objectives",
        json={
            "strategy_id": strategy_id,
            "metric": "Lead Time",
            "target": 20,
            "deadline": "2026-11-30T00:00:00Z",
            "status": "planning",
        },
    )
    assert objective.status_code == 200
    objective_id = objective.json()["objective"]["id"]

    created = client.post(
        "/initiatives",
        json={
            "objective_id": objective_id,
            "name": "Padronizar fluxo de obra",
            "description": "Ajustes de processo ponta a ponta",
            "initiative_type": "process",
            "owner": "ops_manager",
            "status": "backlog",
        },
    )
    assert created.status_code == 200
    payload = created.json()
    assert payload["status"] == "created"
    assert payload["initiative"]["objective_id"] == objective_id
    assert payload["initiative"]["initiative_type"] == "process"
    assert payload["dispatch"]["total_targets"] == 1
    assert payload["dispatch"]["targets"][0]["target"] == "opera"
    initiative_id = payload["initiative"]["id"]

    listed = client.get(f"/initiatives?objective_id={objective_id}")
    assert listed.status_code == 200
    assert any(item["id"] == initiative_id for item in listed.json()["items"])

    fetched = client.get(f"/initiatives/{initiative_id}")
    assert fetched.status_code == 200
    assert fetched.json()["initiative"]["owner"] == "ops_manager"

    updated = client.patch(
        f"/initiatives/{initiative_id}",
        json={"initiative_type": "training", "status": "planning", "owner": "academy_lead"},
    )
    assert updated.status_code == 200
    assert updated.json()["initiative"]["initiative_type"] == "training"
    assert updated.json()["initiative"]["status"] == "planning"
    assert updated.json()["initiative"]["owner"] == "academy_lead"

    deleted = client.delete(f"/initiatives/{initiative_id}")
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"

    missing = client.get(f"/initiatives/{initiative_id}")
    assert missing.status_code == 404


def test_initiative_creation_fails_with_invalid_type():
    strategy = client.post(
        "/strategies",
        json={
            "name": "Estrategia comercial",
            "description": "Expandir carteira com qualidade",
            "priority": "normal",
            "status": "backlog",
        },
    )
    strategy_id = strategy.json()["strategy"]["id"]

    objective = client.post(
        "/objectives",
        json={
            "strategy_id": strategy_id,
            "metric": "Conversao",
            "target": 35,
            "deadline": "2026-10-31T00:00:00Z",
            "status": "backlog",
        },
    )
    objective_id = objective.json()["objective"]["id"]

    created = client.post(
        "/initiatives",
        json={
            "objective_id": objective_id,
            "name": "Iniciativa invalida",
            "description": "Teste de validacao",
            "initiative_type": "unknown",
            "owner": "owner_x",
            "status": "backlog",
        },
    )

    assert created.status_code == 422
    assert created.json()["detail"] == "initiative_type inválido"


def test_initiative_creation_fails_when_objective_does_not_exist():
    created = client.post(
        "/initiatives",
        json={
            "objective_id": 999999,
            "name": "Sem objetivo",
            "description": "Falha esperada",
            "initiative_type": "execution",
            "owner": "ops",
            "status": "backlog",
        },
    )

    assert created.status_code == 404
    assert created.json()["detail"] == "Objective não encontrado"


def test_plan_crud_endpoints_with_initiative_relationship():
    strategy = client.post(
        "/strategies",
        json={
            "name": "Estrategia operacional",
            "description": "Consolidar execucao em escala",
            "priority": "high",
            "status": "planning",
        },
    )
    assert strategy.status_code == 200
    strategy_id = strategy.json()["strategy"]["id"]

    objective = client.post(
        "/objectives",
        json={
            "strategy_id": strategy_id,
            "metric": "OTIF",
            "target": 96,
            "deadline": "2026-12-15T00:00:00Z",
            "status": "planning",
        },
    )
    assert objective.status_code == 200
    objective_id = objective.json()["objective"]["id"]

    initiative = client.post(
        "/initiatives",
        json={
            "objective_id": objective_id,
            "name": "Padrao de execucao nacional",
            "description": "Modelo unificado de operacao",
            "initiative_type": "execution",
            "owner": "ops_director",
            "status": "planning",
        },
    )
    assert initiative.status_code == 200
    initiative_id = initiative.json()["initiative"]["id"]

    created = client.post(
        "/plans",
        json={
            "initiative_id": initiative_id,
            "title": "Plano de rollout por regiao",
            "description": "Implantacao em ondas trimestrais",
            "status": "backlog",
            "priority": "high",
        },
    )
    assert created.status_code == 200
    payload = created.json()
    assert payload["status"] == "created"
    assert payload["plan"]["initiative_id"] == initiative_id
    assert payload["generation"]["initiative_type"] == "execution"
    assert payload["generation"]["created_count"] == 3
    assert len(payload["generated_tasks"]) == 3
    plan_id = payload["plan"]["id"]

    listed = client.get(f"/plans?initiative_id={initiative_id}")
    assert listed.status_code == 200
    assert any(item["id"] == plan_id for item in listed.json()["items"])

    fetched = client.get(f"/plans/{plan_id}")
    assert fetched.status_code == 200
    assert fetched.json()["plan"]["title"] == "Plano de rollout por regiao"

    updated = client.patch(
        f"/plans/{plan_id}",
        json={"status": "planning", "priority": "critical"},
    )
    assert updated.status_code == 200
    assert updated.json()["plan"]["status"] == "planning"
    assert updated.json()["plan"]["priority"] == "critical"

    deleted = client.delete(f"/plans/{plan_id}")
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"

    missing = client.get(f"/plans/{plan_id}")
    assert missing.status_code == 404


def test_plan_creation_fails_when_initiative_does_not_exist():
    created = client.post(
        "/plans",
        json={
            "initiative_id": 999999,
            "title": "Plano sem iniciativa",
            "description": "Falha esperada",
            "status": "backlog",
            "priority": "normal",
        },
    )

    assert created.status_code == 404
    assert created.json()["detail"] == "Initiative não encontrada"


def test_plan_generate_tasks_endpoint_is_idempotent():
    strategy = client.post(
        "/strategies",
        json={
            "name": "Estrategia de processos",
            "description": "Automatizar desdobramento de tarefas",
            "priority": "high",
            "status": "planning",
        },
    )
    strategy_id = strategy.json()["strategy"]["id"]

    objective = client.post(
        "/objectives",
        json={
            "strategy_id": strategy_id,
            "metric": "Tasks template",
            "target": 9,
            "deadline": "2026-12-31T00:00:00Z",
            "status": "planning",
        },
    )
    objective_id = objective.json()["objective"]["id"]

    initiative = client.post(
        "/initiatives",
        json={
            "objective_id": objective_id,
            "name": "Padronizacao operacional",
            "description": "Processo com etapas claras",
            "initiative_type": "process",
            "owner": "process_owner",
            "status": "planning",
        },
    )
    initiative_id = initiative.json()["initiative"]["id"]

    plan = client.post(
        "/plans",
        json={
            "initiative_id": initiative_id,
            "title": "Plano base de processo",
            "description": "Primeira versao do rollout",
            "status": "planning",
            "priority": "high",
        },
    )
    assert plan.status_code == 200
    plan_payload = plan.json()
    plan_id = plan_payload["plan"]["id"]
    assert plan_payload["generation"]["created_count"] == 3

    regenerated = client.post(f"/plans/{plan_id}/generate-tasks")
    assert regenerated.status_code == 200
    regenerated_payload = regenerated.json()
    assert regenerated_payload["status"] == "processed"
    assert regenerated_payload["generation"]["template_count"] == 3
    assert regenerated_payload["generation"]["created_count"] == 0
    assert regenerated_payload["generated_tasks"] == []

    listed = client.get(f"/tasks?plan_id={plan_id}")
    assert listed.status_code == 200
    assert listed.json()["total"] == 3


def test_training_initiative_emits_training_required_with_linked_tracks():
    _reset_event_bus_messages()

    strategy = client.post(
        "/strategies",
        json={
            "name": "Estrategia Academia",
            "description": "Capacitacao operacional assistida",
            "priority": "high",
            "status": "planning",
        },
    )
    strategy_id = strategy.json()["strategy"]["id"]

    objective = client.post(
        "/objectives",
        json={
            "strategy_id": strategy_id,
            "metric": "Pessoas treinadas",
            "target": 50,
            "deadline": "2026-12-31T00:00:00Z",
            "status": "planning",
        },
    )
    objective_id = objective.json()["objective"]["id"]

    initiative = client.post(
        "/initiatives",
        json={
            "objective_id": objective_id,
            "name": "Treinamento de execucao em campo",
            "description": "Capacitacao de obra para equipe operacional",
            "initiative_type": "training",
            "owner": "academy_ops_lead",
            "status": "planning",
        },
    )
    initiative_id = initiative.json()["initiative"]["id"]

    plan = client.post(
        "/plans",
        json={
            "initiative_id": initiative_id,
            "title": "Plano de capacitação inicial",
            "description": "Sequência de onboarding da equipe",
            "status": "planning",
            "priority": "high",
        },
    )
    assert plan.status_code == 200
    payload = plan.json()

    assert payload["academy_sync"]["listener"] == "academia_saber"
    assert payload["academy_sync"]["channel"] == "academia.saber.treinamentos"
    assert payload["academy_sync"]["academy_training"]["academy"] == "academia_saber"
    assert payload["academy_sync"]["academy_training"]["module_count"] == 3
    assert len(payload["academy_sync"]["academy_training"]["linked_task_titles"]) == 3

    recent = event_bus.get_event_bus().recent_messages(limit=100)
    training_events = [entry for entry in recent if entry.get("channel") == "academia.saber.treinamentos"]
    assert training_events
    latest = training_events[-1]["message"]
    assert latest["event_type"] == "training.required"
    assert latest["initiative_id"] == initiative_id
    assert latest["academy_training"]["academy"] == "academia_saber"


def test_task_crud_endpoints_with_plan_relationship():
    strategy = client.post(
        "/strategies",
        json={
            "name": "Estrategia de producao",
            "description": "Ganhos operacionais sustentaveis",
            "priority": "high",
            "status": "planning",
        },
    )
    assert strategy.status_code == 200
    strategy_id = strategy.json()["strategy"]["id"]

    objective = client.post(
        "/objectives",
        json={
            "strategy_id": strategy_id,
            "metric": "Produtividade",
            "target": 30,
            "deadline": "2026-12-20T00:00:00Z",
            "status": "planning",
        },
    )
    assert objective.status_code == 200
    objective_id = objective.json()["objective"]["id"]

    initiative = client.post(
        "/initiatives",
        json={
            "objective_id": objective_id,
            "name": "Padrao de time operacional",
            "description": "Definir rotina de execucao semanal",
            "initiative_type": "execution",
            "owner": "opera_lead",
            "status": "planning",
        },
    )
    assert initiative.status_code == 200
    initiative_id = initiative.json()["initiative"]["id"]

    plan = client.post(
        "/plans",
        json={
            "initiative_id": initiative_id,
            "title": "Plano de treino do time",
            "description": "Ritmo de implantacao",
            "status": "planning",
            "priority": "high",
        },
    )
    assert plan.status_code == 200
    plan_id = plan.json()["plan"]["id"]

    created = client.post(
        "/tasks",
        json={
            "plan_id": plan_id,
            "title": "Alinhar squad inicial",
            "description": "Kickoff de operacao",
            "assigned_to": "user-op-001",
            "status": "backlog",
            "priority": "high",
        },
    )
    assert created.status_code == 200
    payload = created.json()
    assert payload["status"] == "created"
    assert payload["task"]["assigned_to"] == "user-op-001"
    task_id = payload["task"]["id"]

    listed = client.get(f"/tasks?plan_id={plan_id}")
    assert listed.status_code == 200
    assert any(item["id"] == task_id for item in listed.json()["items"])

    fetched = client.get(f"/tasks/{task_id}")
    assert fetched.status_code == 200
    assert fetched.json()["task"]["title"] == "Alinhar squad inicial"

    updated = client.patch(
        f"/tasks/{task_id}",
        json={"status": "planning", "priority": "critical", "assigned_to": "user-op-002"},
    )
    assert updated.status_code == 200
    assert updated.json()["task"]["status"] == "planning"
    assert updated.json()["task"]["priority"] == "critical"
    assert updated.json()["task"]["assigned_to"] == "user-op-002"

    deleted = client.delete(f"/tasks/{task_id}")
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"

    missing = client.get(f"/tasks/{task_id}")
    assert missing.status_code == 404


def test_task_creation_fails_when_plan_does_not_exist():
    created = client.post(
        "/tasks",
        json={
            "plan_id": 999999,
            "title": "Task invalida",
            "description": "Falha esperada",
            "assigned_to": "ops",
            "status": "backlog",
            "priority": "normal",
        },
    )

    assert created.status_code == 404
    assert created.json()["detail"] == "Plan não encontrado"


def test_task_dispatch_to_opera_endpoint(monkeypatch):
    strategy = client.post(
        "/strategies",
        json={
            "name": "Estrategia OPERA",
            "description": "Fluxo de despacho operacional",
            "priority": "high",
            "status": "planning",
        },
    )
    strategy_id = strategy.json()["strategy"]["id"]

    objective = client.post(
        "/objectives",
        json={
            "strategy_id": strategy_id,
            "metric": "Tasks sincronizadas",
            "target": 100,
            "deadline": "2026-12-31T00:00:00Z",
            "status": "planning",
        },
    )
    objective_id = objective.json()["objective"]["id"]

    initiative = client.post(
        "/initiatives",
        json={
            "objective_id": objective_id,
            "name": "Hub OPERA",
            "description": "Rotina de sincronizacao",
            "initiative_type": "process",
            "owner": "opera_manager",
            "status": "planning",
        },
    )
    initiative_id = initiative.json()["initiative"]["id"]

    plan = client.post(
        "/plans",
        json={
            "initiative_id": initiative_id,
            "title": "Plano de despacho",
            "description": "Sequencia de envio",
            "status": "planning",
            "priority": "high",
        },
    )
    plan_id = plan.json()["plan"]["id"]

    task = client.post(
        "/tasks",
        json={
            "plan_id": plan_id,
            "title": "Enviar para OPERA",
            "description": "Task pronta para sincronizacao",
            "assigned_to": "ops_sync",
            "status": "backlog",
            "priority": "normal",
        },
    )
    task_id = task.json()["task"]["id"]

    def _mock_publish_task(self, _: object):
        return {"synced": True, "status_code": 200, "detail": "mocked"}

    monkeypatch.setattr(OperaGateway, "publish_task", _mock_publish_task)

    dispatched = client.post(f"/tasks/{task_id}/dispatch-opera")
    assert dispatched.status_code == 200
    assert dispatched.json()["status"] == "processed"
    assert dispatched.json()["opera_sync"]["synced"] is True


def test_strategic_events_are_emitted_on_create_endpoints():
    _reset_event_bus_messages()

    strategy = client.post(
        "/strategies",
        json={
            "name": "Estrategia de eventos",
            "description": "Validar emissao automatica",
            "priority": "high",
            "status": "planning",
        },
    )
    assert strategy.status_code == 200
    strategy_id = strategy.json()["strategy"]["id"]

    objective = client.post(
        "/objectives",
        json={
            "strategy_id": strategy_id,
            "metric": "Eventos publicados",
            "target": 4,
            "deadline": "2026-12-31T00:00:00Z",
            "status": "planning",
        },
    )
    assert objective.status_code == 200
    objective_id = objective.json()["objective"]["id"]

    initiative = client.post(
        "/initiatives",
        json={
            "objective_id": objective_id,
            "name": "Iniciativa de observabilidade",
            "description": "Fluxo fim a fim",
            "initiative_type": "process",
            "owner": "events_owner",
            "status": "planning",
        },
    )
    assert initiative.status_code == 200
    initiative_id = initiative.json()["initiative"]["id"]

    plan = client.post(
        "/plans",
        json={
            "initiative_id": initiative_id,
            "title": "Plano de monitoramento",
            "description": "Acompanhar publicacoes",
            "status": "planning",
            "priority": "high",
        },
    )
    assert plan.status_code == 200
    plan_id = plan.json()["plan"]["id"]

    task = client.post(
        "/tasks",
        json={
            "plan_id": plan_id,
            "title": "Task de verificacao",
            "description": "Conferir eventos",
            "assigned_to": "observer",
            "status": "backlog",
            "priority": "normal",
        },
    )
    assert task.status_code == 200

    bus = event_bus.get_event_bus()
    recent = bus.recent_messages(limit=100)
    channels = [entry.get("channel") for entry in recent]

    assert "strategy.created" in channels
    assert "initiative.created" in channels
    assert "plan.created" in channels
    assert "task.generated" in channels


def test_initiative_dispatch_endpoint_routes_to_pd_and_academia_when_applicable():
    _reset_event_bus_messages()

    strategy = client.post(
        "/strategies",
        json={
            "name": "Estrategia de inovacao",
            "description": "Programa de evolucao tecnica",
            "priority": "high",
            "status": "planning",
        },
    )
    strategy_id = strategy.json()["strategy"]["id"]

    objective = client.post(
        "/objectives",
        json={
            "strategy_id": strategy_id,
            "metric": "Novas trilhas",
            "target": 12,
            "deadline": "2026-12-31T00:00:00Z",
            "status": "planning",
        },
    )
    objective_id = objective.json()["objective"]["id"]

    initiative = client.post(
        "/initiatives",
        json={
            "objective_id": objective_id,
            "name": "Treinamento de IA e P&D",
            "description": "Pesquisa aplicada para nova trilha",
            "initiative_type": "training",
            "owner": "academy_research_lead",
            "status": "planning",
        },
    )
    assert initiative.status_code == 200
    initiative_id = initiative.json()["initiative"]["id"]

    redelivered = client.post(f"/initiatives/{initiative_id}/dispatch")
    assert redelivered.status_code == 200
    payload = redelivered.json()["dispatch"]
    assert payload["total_targets"] == 2

    targets = {item["target"] for item in payload["targets"]}
    assert "academia_saber" in targets
    assert "pdi_ia" in targets

    channels = [entry.get("channel") for entry in event_bus.get_event_bus().recent_messages(limit=100)]
    assert "initiative.dispatch.academia_saber" in channels
    assert "initiative.dispatch.pdi_ia" in channels


def test_pd_process_is_created_and_versioned_for_research_initiative():
    _reset_event_bus_messages()

    strategy = client.post(
        "/strategies",
        json={
            "name": "Estrategia P&D",
            "description": "Programa de pesquisa aplicada",
            "priority": "high",
            "status": "planning",
        },
    )
    strategy_id = strategy.json()["strategy"]["id"]

    objective = client.post(
        "/objectives",
        json={
            "strategy_id": strategy_id,
            "metric": "Protótipos validados",
            "target": 3,
            "deadline": "2026-12-31T00:00:00Z",
            "status": "planning",
        },
    )
    objective_id = objective.json()["objective"]["id"]

    created = client.post(
        "/initiatives",
        json={
            "objective_id": objective_id,
            "name": "Pesquisa de IA para prototipo",
            "description": "P&D para novo fluxo cognitivo",
            "initiative_type": "process",
            "owner": "pd_owner",
            "status": "planning",
        },
    )
    assert created.status_code == 200
    payload = created.json()
    assert payload["pd_sync"]["action"] == "created"
    assert payload["pd_sync"]["process"]["version"] == 1
    assert payload["pd_sync"]["process"]["target_monolith"] == "pdi_ia"
    initiative_id = payload["initiative"]["id"]

    updated = client.patch(
        f"/initiatives/{initiative_id}",
        json={"description": "P&D para novo fluxo cognitivo versionado"},
    )
    assert updated.status_code == 200
    updated_payload = updated.json()
    assert updated_payload["pd_sync"]["action"] == "versioned"
    assert updated_payload["pd_sync"]["process"]["version"] == 2

    channels = [entry.get("channel") for entry in event_bus.get_event_bus().recent_messages(limit=100)]
    assert "pd.process.created" in channels
    assert "pd.process.versioned" in channels


def test_work_crud_endpoints_persist_kanban_items():
    created = client.post(
        "/work",
        json={
            "title": "Estudo inicial de terreno",
            "description": "Pipeline de validação",
            "monolith_origin": "archimedes",
            "status": "backlog",
            "priority": "high",
            "created_by": "00000000-0000-0000-0000-000000000001",
            "context": {"demand": 90, "supply": 40, "risk": 10, "expected_revenue": 150000, "cost": 100000},
            "watchers": ["00000000-0000-0000-0000-000000000101"],
            "dependencies": [],
        },
    )

    assert created.status_code == 200
    created_payload = created.json()
    assert created_payload["status"] == "created"
    work_id = created_payload["work"]["id"]

    listed = client.get("/work")
    assert listed.status_code == 200
    assert any(item["id"] == work_id for item in listed.json()["items"])

    updated = client.patch(
        f"/work/{work_id}",
        json={"status": "in_progress", "priority": "critical"},
    )
    assert updated.status_code == 200
    assert updated.json()["work"]["status"] == "in_progress"
    assert updated.json()["work"]["priority"] == "critical"


def test_event_endpoints_store_and_list_event_sourcing_base():
    created = client.post(
        "/events",
        json={
            "event_type": "deal.created.v1",
            "payload": {"deal_id": "D-001", "producer": "archimedes"},
            "source": "archimedes",
        },
    )

    assert created.status_code == 200
    assert created.json()["event"]["event_type"] == "deal.created.v1"

    listed = client.get("/events")
    assert listed.status_code == 200
    assert any(item["event_type"] == "deal.created.v1" for item in listed.json()["items"])


def test_orchestrator_legal_gate_blocks_non_approved_contracts():
    created = client.post(
        "/work",
        json={
            "title": "Contrato SPE",
            "description": "Requer validação jurídica",
            "monolith_origin": "juridicotech",
            "context": {"type": "contract", "juridico_approved": False},
        },
    )
    work_id = created.json()["work"]["id"]

    processed = client.post(f"/work/{work_id}/orchestrate")
    assert processed.status_code == 200
    assert processed.json()["result"]["status"] == "blocked"
    assert processed.json()["result"]["reason"] == "legal_gate"


def test_orchestrator_priority_engine_dispatches_positive_work():
    created = client.post(
        "/work",
        json={
            "title": "Projeto com sinal positivo",
            "description": "Fluxo completo",
            "monolith_origin": "archimedes",
            "context": {
                "demand": 100,
                "supply": 20,
                "risk": 5,
                "expected_revenue": 250000,
                "cost": 100000,
            },
        },
    )
    work_id = created.json()["work"]["id"]

    processed = client.post(f"/work/{work_id}/orchestrate")
    assert processed.status_code == 200
    payload = processed.json()["result"]
    assert payload["decision"] == "approve"
    assert payload["dispatch"]["target"] == "archimedes"
    assert payload["priority_score"] > 0


def test_plugin_monolith_registry_endpoint_registers_runtime_handler():
    response = client.post(
        "/plugins/monolith/register",
        json={"name": "archimedes"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "registered"
    assert payload["monolith"]["name"] == "archimedes"
