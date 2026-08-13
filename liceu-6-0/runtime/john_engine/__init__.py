"""
John Internal Engine

Responsavel por interpretar eventos do ecossistema e gerar acoes inteligentes.

Nao decide. Apenas interpreta e executa scripts baseado em regras.
"""

import asyncio
import json
from typing import Dict, Any, Optional


class JohnInternal:
    """
    Engine de interpretacao interna do John.
    Vive dentro do runtime e processa eventos do barramento.
    """

    def __init__(self, brain_sdk=None, logger=None):
        """
        Args:
            brain_sdk: acesso ao SDK para calculos (CEFEIDA)
            logger: logger centralizado
        """
        self.sdk = brain_sdk
        self.logger = logger or self._default_logger

    def _default_logger(self, msg):
        print(f"[JOHN] {msg}")

    async def interpret(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpreta evento e gera resposta/acao.

        Entrada: qualquer evento do barramento
        Saida: dicionario com {message, action, priority, data}
        """

        event_type = event.get("type", "unknown")

        # Mapeamento de handlers por tipo de evento
        handlers = {
            "project.risk_detected": self._handle_risk_detected,
            "lead.created": self._handle_lead_created,
            "payment.delayed": self._handle_payment_delayed,
            "task.overdue": self._handle_task_overdue,
            "supply_chain.alert": self._handle_supply_alert,
            "audit.finding": self._handle_audit_finding,
        }

        handler = handlers.get(event_type, self._handle_unknown)
        return await handler(event)

    async def _handle_risk_detected(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Risco detectado em projeto."""
        risk_score = event.get("risk_score", 0.5)
        project_id = event.get("project_id")

        # CEFEIDA calcula o risco
        severity = "critical" if risk_score > 0.8 else "high" if risk_score > 0.6 else "medium"

        return {
            "message": f"Risco elevado detectado no projeto {project_id} (score: {risk_score:.2f})",
            "action": "notify_manager",
            "priority": severity,
            "data": {
                "project_id": project_id,
                "risk_score": risk_score,
                "recommendation": self._risk_recommendation(risk_score),
            },
        }

    async def _handle_lead_created(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Lead criado pelo CRM."""
        lead_id = event.get("lead_id")
        name = event.get("name", "Cliente")
        interest = event.get("interest", "unknown")

        return {
            "message": f"Novo lead recebido: {name}",
            "action": "log_interaction",
            "priority": "normal",
            "data": {
                "lead_id": lead_id,
                "name": name,
                "interest": interest,
                "next_step": "assign_to_module",
            },
        }

    async def _handle_payment_delayed(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Pagamento atrasado."""
        deal_id = event.get("deal_id")
        days_late = event.get("days_late", 1)

        return {
            "message": f"Pagamento atrasado em {days_late} dias",
            "action": "escalate_financial",
            "priority": "high" if days_late > 7 else "medium",
            "data": {
                "deal_id": deal_id,
                "days_late": days_late,
                "notification": "contact_client",
            },
        }

    async def _handle_task_overdue(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Tarefa vencida."""
        task_id = event.get("task_id")
        project_id = event.get("project_id")

        return {
            "message": f"Tarefa vencida no projeto {project_id}",
            "action": "notify_manager",
            "priority": "high",
            "data": {
                "task_id": task_id,
                "project_id": project_id,
                "action": "reschedule_or_reassign",
            },
        }

    async def _handle_supply_alert(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Alerta na cadeia de suprimentos."""
        supplier = event.get("supplier", "unknown")
        issue = event.get("issue", "unknown")

        return {
            "message": f"Alerta de suprimento: {supplier} - {issue}",
            "action": "notify_procurement",
            "priority": "high",
            "data": {
                "supplier": supplier,
                "issue": issue,
                "escalation": "contact_alternative_supplier",
            },
        }

    async def _handle_audit_finding(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Achado de auditoria."""
        severity = event.get("severity", "medium")
        finding = event.get("finding", "unknown")

        return {
            "message": f"Achado de auditoria [{severity}]: {finding}",
            "action": "create_action_item",
            "priority": severity,
            "data": {
                "finding": finding,
                "severity": severity,
                "assigned_to": "compliance_team",
            },
        }

    async def _handle_unknown(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback para eventos desconhecidos."""
        return {
            "message": f"Evento não mapeado: {event.get('type')}",
            "action": "log_only",
            "priority": "low",
            "data": event,
        }

    def _risk_recommendation(self, risk_score: float) -> str:
        """Recomendacao baseada no score de risco."""
        if risk_score > 0.8:
            return "Reforcar equipe, revisar cronograma, considerar pausa de obra"
        elif risk_score > 0.6:
            return "Reforcar equipe, aumentar supervisao, revisar recursos"
        else:
            return "Manter vigilancia, monitoramento intensivo"
