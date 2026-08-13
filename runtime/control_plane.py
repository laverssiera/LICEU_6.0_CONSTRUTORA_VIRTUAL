from fastapi import FastAPI, HTTPException
from typing import Optional
from runtime.adaptive_approval import classify_risk, required_approval_level
from runtime.simplification_engine import SimplificationEngine
from runtime.change_heatmap import ChangeHeatmap
from runtime.feature_flags import is_real_money_mode
from runtime.change_approval import ChangeApprovalSystem
from runtime.impact_simulation_engine import simulate_rule_impact

app = FastAPI(title="Control Plane API")
simplification_engine = SimplificationEngine()
change_heatmap = ChangeHeatmap()
change_approval = ChangeApprovalSystem()

# --- Endpoint do CEO Cockpit ---
@app.get("/control/executive_cockpit")
def executive_cockpit():
    # Exemplo: mock de trust_score e sensibilidade
    trust_scores = {
        "hubbackoffice": 0.92,
        "juridicotech": 0.98,
        "opera": 0.87
    }
    sensitivity = {
        "hubbackoffice": 0.7,
        "juridicotech": 0.3,
        "opera": 0.8
    }
    return {
        "trust_scores": trust_scores,
        "sensitivity": sensitivity,
        "heatmap": change_heatmap.get_heatmap()
    }

# --- Endpoints de aprovação de mudanças ---

# --- Endpoint do Change Heatmap ---
@app.get("/control/change_heatmap")
def get_change_heatmap():
    return {
        "heatmap": change_heatmap.get_heatmap(),
        "ranking": change_heatmap.top_changing_modules()
    }
# Control Plane API — Painel de comando operacional

# --- Endpoints de aprovação de mudanças ---

@app.post("/change/submit_proposal")
def submit_change_proposal(author: str, description: str, dsl_text: str, tenant_id: str, pipelines: list):
    """
    Submete uma proposta de mudança (ex: nova regra DSL).
    """
    payload = {"dsl_text": dsl_text, "tenant_id": tenant_id, "pipelines": pipelines}
    proposal = change_approval.submit_proposal(author, description, payload)
    return {"proposal_id": proposal.proposal_id, "status": proposal.status.value}


@app.post("/change/simulate_impact")
def simulate_change_impact(proposal_id: str):
    """
    Simula o impacto da proposta de mudança.
    """
    def sim_fn(payload):
        return simulate_rule_impact(payload["dsl_text"], payload["tenant_id"], payload["pipelines"]).as_dict()
    report = change_approval.simulate_impact(proposal_id, sim_fn)
    return {"proposal_id": proposal_id, "simulation_report": report}


@app.post("/change/approve")
def approve_change(proposal_id: str, approver: str, justification: str):
    change_approval.approve(proposal_id, approver, justification)
    return {"proposal_id": proposal_id, "status": "approved"}


@app.post("/change/apply")
def apply_change(proposal_id: str):
    def apply_fn(payload):
        # Aqui entraria a lógica real de aplicação da mudança (ex: atualizar regras DSL do sistema)
        pass
    change_approval.apply(proposal_id, apply_fn)
    return {"proposal_id": proposal_id, "status": "applied"}


@app.post("/change/rollback")
def rollback_change(proposal_id: str):
    def rollback_fn(payload):
        # Aqui entraria a lógica real de rollback da mudança
        pass
    change_approval.rollback(proposal_id, rollback_fn)
    return {"proposal_id": proposal_id, "status": "rolled_back"}


@app.get("/change/audit")
def audit_change(proposal_id: str):
    log = change_approval.audit(proposal_id)
    return {"proposal_id": proposal_id, "audit_log": log}


@app.get("/change/list")
def list_change_proposals():
    proposals = change_approval.list_proposals()
    return [
        {
            "proposal_id": p.proposal_id,
            "author": p.author,
            "description": p.description,
            "status": p.status.value,
            "created_at": p.created_at,
        }
        for p in proposals
    ]

# Estados em memória (exemplo, pode ser persistido)
PAUSED_PIPELINES = set()
DISABLED_MONOLITHS = set()
FEATURE_FLAGS = {"REAL_MONEY_MODE": is_real_money_mode()}

CHAOS_FLAGS = {
    "monolith_down": set(),  # monolith names
    "event_delay": {},       # event_id: delay_seconds
    "finance_error": set(),  # pipeline_ids
    "network_failure": set() # monolith names
}

TENANTS = {}

@app.post("/control/pause_pipeline")
def pause_pipeline(pipeline_id: str):
    PAUSED_PIPELINES.add(pipeline_id)
    return {"status": "paused", "pipeline_id": pipeline_id}

@app.post("/control/resume_pipeline")
def resume_pipeline(pipeline_id: str):
    PAUSED_PIPELINES.discard(pipeline_id)
    return {"status": "resumed", "pipeline_id": pipeline_id}

@app.post("/control/reprocess_event")
def reprocess_event(event_id: str):
    # Aqui: lógica de replay/reprocessamento real
    return {"status": "reprocess_requested", "event_id": event_id}

@app.post("/control/force_transition")
def force_transition(pipeline_id: str, to_stage: str, reason: str, approved_by: str):
    # Aqui: lógica de transição forçada + auditoria
    return {
        "status": "forced_transition_requested",
        "pipeline_id": pipeline_id,
        "to_stage": to_stage,
        "reason": reason,
        "approved_by": approved_by
    }

@app.post("/control/disable_monolith")
def disable_monolith(monolith: str):
    DISABLED_MONOLITHS.add(monolith)
    return {"status": "disabled", "monolith": monolith}

@app.post("/control/enable_monolith")
def enable_monolith(monolith: str):
    DISABLED_MONOLITHS.discard(monolith)
    return {"status": "enabled", "monolith": monolith}

@app.post("/control/set_feature_flag")
def set_feature_flag(flag: str, value: bool):
    FEATURE_FLAGS[flag] = value
    return {"status": "flag_set", "flag": flag, "value": value}

@app.get("/control/flags")
def get_flags():
    return FEATURE_FLAGS

@app.get("/control/status")
def get_status():
    return {
        "paused_pipelines": list(PAUSED_PIPELINES),
        "disabled_monoliths": list(DISABLED_MONOLITHS),
        "feature_flags": FEATURE_FLAGS
    }

@app.post("/control/chaos/monolith_down")
def chaos_monolith_down(monolith: str):
    CHAOS_FLAGS["monolith_down"].add(monolith)
    return {"status": "chaos_monolith_down", "monolith": monolith}

@app.post("/control/chaos/event_delay")
def chaos_event_delay(event_id: str, delay_seconds: int):
    CHAOS_FLAGS["event_delay"][event_id] = delay_seconds
    return {"status": "chaos_event_delay", "event_id": event_id, "delay": delay_seconds}

@app.post("/control/chaos/finance_error")
def chaos_finance_error(pipeline_id: str):
    CHAOS_FLAGS["finance_error"].add(pipeline_id)
    return {"status": "chaos_finance_error", "pipeline_id": pipeline_id}

@app.post("/control/chaos/network_failure")
def chaos_network_failure(monolith: str):
    CHAOS_FLAGS["network_failure"].add(monolith)
    return {"status": "chaos_network_failure", "monolith": monolith}

@app.get("/control/chaos/status")
def chaos_status():
    return CHAOS_FLAGS

@app.post("/control/onboard_tenant")
def onboard_tenant(tenant_id: str, owner: str, dashboard_url: str = None, limits: dict = None, feature_flags: dict = None):
    # Provisionamento automático
    TENANTS[tenant_id] = {
        "owner": owner,
        "dashboard_url": dashboard_url or f"/dashboards/{tenant_id}",
        "limits": limits or {"events_per_minute": 1000},
        "feature_flags": feature_flags or {},
        "db": f"db_{tenant_id}.sqlite",
        "logs": f"logs/{tenant_id}.log"
    }
    # Auditoria
    from runtime.event_store import persist_event
    persist_event({
        "id": f"audit-onboard-{tenant_id}",
        "type": "tenant.onboarded",
        "version": "v1",
        "source": "control_plane",
        "timestamp": None,
        "payload": TENANTS[tenant_id],
        "tenant_id": tenant_id
    })
    return {"status": "onboarded", "tenant_id": tenant_id, "info": TENANTS[tenant_id]}

@app.get("/control/tenants")
def list_tenants():
    return TENANTS
