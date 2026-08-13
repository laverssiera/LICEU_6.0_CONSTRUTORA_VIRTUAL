from runtime.control_plane import PAUSED_PIPELINES
# Policy Engine do Runtime
from runtime.stage_event_matrix import STAGE_EVENT_MATRIX
from kanban.pipeline_stages import PipelineStage
from kanban.pipeline_score import get_db
from runtime.dlq import publish_dlq
import asyncio
from runtime.idempotency import is_event_processed, mark_event_processed
from runtime.event_store import persist_event
from runtime.financial_ledger import append_ledger_entry
from runtime.saga_engine import saga_compensate
from runtime.rate_limiter import rate_limiter
from runtime.event_signing import verify_signature
from runtime.feature_flags import is_real_money_mode

# Versão da policy engine
POLICY_ENGINE_VERSION = "v3.2"

# Modos de operação do tenant
TENANT_MODE_SIMULATION = "SIMULATION"
TENANT_MODE_PRODUCTION = "PRODUCTION"

def get_pipeline(pipeline_id):
    conn = get_db()
    cur = conn.execute("SELECT current_stage FROM business_pipeline WHERE id=?", (pipeline_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise Exception(f"Pipeline {pipeline_id} não encontrado")
    return row[0]

def is_event_allowed(stage, event_type):
    return event_type in STAGE_EVENT_MATRIX.get(stage, [])

def reject_event(event, reason="INVALID_STAGE_TRANSITION", source="runtime"):
    print(f"[POLICY] Evento rejeitado: {event}")
    asyncio.run(publish_dlq(event, reason, source=source))
    # SAGA: Compensação automática para eventos financeiros
    if event.get("type") in ("finance.generated", "payment.generated"):
        saga_compensate(event, reason=reason)
    # Aqui: pode gerar audit.finding também

def handle_event(event):
    event_id = event.get("id")
    if not event_id:
        reject_event(event, reason="MISSING_EVENT_ID")
        return
    if is_event_processed(event_id):
        print(f"[IDEMPOTENCY] Evento já processado: {event_id}")
        return
    pipeline_id = event.get("pipeline_id")
    if not pipeline_id:
        reject_event(event, reason="MISSING_PIPELINE_ID")
        return
    tenant_id = event.get("tenant_id")
    if not tenant_id:
        reject_event(event, reason="MISSING_TENANT_ID")
        return

    tenant_mode = event.get("tenant_mode", TENANT_MODE_PRODUCTION)
    if tenant_mode == TENANT_MODE_SIMULATION:
        print(f"[SANDBOX] Evento em modo SIMULATION: {event}")
        # Eventos de simulação não afetam dados reais
        # Apenas loga, audita e retorna
        persist_event({
            "id": f"audit-{event_id}-simulation",
            "type": "simulation.audit",
            "version": event.get("version", "v1"),
            "policy_version": POLICY_ENGINE_VERSION,
            "source": "policy_engine",
            "timestamp": event.get("timestamp"),
            "payload": {
                "action": "simulation_event",
                "pipeline_id": pipeline_id,
                "event_id": event_id,
                "reason": "sandbox mode"
            },
            "tenant_id": tenant_id,
            "correlation_id": event.get("correlation_id")
        })
        return


    # Enforcement: pipeline pausado manualmente pelo Control Plane
    if pipeline_id in PAUSED_PIPELINES:
        reject_event(event, reason="PIPELINE_PAUSED_MANUAL_OVERRIDE")
        # Auditoria do override
        persist_event({
            "id": f"audit-{event_id}-override",
            "type": "override.audit",
            "version": event.get("version", "v1"),
            "policy_version": POLICY_ENGINE_VERSION,
            "source": "policy_engine",
            "timestamp": event.get("timestamp"),
            "payload": {
                "action": "pipeline_paused",
                "pipeline_id": pipeline_id,
                "event_id": event_id,
                "reason": "manual override via Control Plane"
            },
            "tenant_id": tenant_id,
            "correlation_id": event.get("correlation_id")
        })
        return


    # Enforcement: modo produção com dinheiro real
    if is_real_money_mode():
        # Validações extras
        if event.get("type", "").startswith("payment") or event.get("type", "").startswith("finance"):
            # Exemplo: exige campo auditoria_extra
            if not event.get("auditoria_extra"):
                reject_event(event, reason="MISSING_EXTRA_AUDIT_PROD_MODE")
                return
        # Logs duplicados
        print(f"[REAL_MONEY_MODE] LOG DUPLICADO: {event}")
        # Alertas críticos
        if event.get("type", "").startswith("payment"):
            print(f"[ALERT] Evento financeiro crítico em produção: {event}")

    # Enforcement: assinatura de eventos (event signing)
    if not verify_signature(event):
        reject_event(event, reason="INVALID_SIGNATURE")
        return

    # Enforcement: Rate limit por domínio
    monolith = event.get("source", "unknown")
    allowed, rate_reason = rate_limiter.check(tenant_id, monolith, event["type"])
    if not allowed:
        reject_event(event, reason=rate_reason)
        return

    stage = get_pipeline(pipeline_id)
    if not is_event_allowed(stage, event["type"]):
        reject_event(event)
        return

    # ENFORCEMENT: Consistência financeira para eventos críticos
    if event["type"] in ("finance.generated", "payment.generated"):
        # 1. Só permite se pipeline em TERMO_ABERTURA ou posterior
        allowed_stages = [
            "TERMO_ABERTURA", "PILOTO", "LICOES", "ESCALA", "PAYBACK", "RETORNO", "BUSINESS_CASE"
        ]
        if stage not in allowed_stages:
            reject_event(event, reason="PIPELINE_STAGE_INVALID_FOR_FINANCIAL_EVENT")
            return
        # 2. Só permite se existe contract.signed válido para o pipeline
        conn = get_db()
        cur = conn.execute(
            "SELECT COUNT(1) FROM event_store WHERE pipeline_id=? AND type='contract.signed'", (pipeline_id,)
        )
        found = cur.fetchone()
        conn.close()
        if not found or found[0] == 0:
            reject_event(event, reason="MISSING_VALID_CONTRACT_SIGNED")
            return

    print(f"[POLICY] Evento permitido: {event}")
    mark_event_processed(event_id)
    persist_event(event)

    # Registro automático no financial_ledger para eventos financeiros
    if event["type"] in ("finance.generated", "payment.generated"):
        payload = event.get("payload", {})
        amount = payload.get("amount")
        from_account = payload.get("from_account")
        to_account = payload.get("to_account")
        if amount is not None and from_account and to_account:
            append_ledger_entry(
                event_id=event["id"],
                type_=event["type"],
                amount=amount,
                from_account=from_account,
                to_account=to_account,
                timestamp=event.get("timestamp")
            )
        else:
            print(f"[LEDGER] Evento financeiro sem dados completos: {event}")
