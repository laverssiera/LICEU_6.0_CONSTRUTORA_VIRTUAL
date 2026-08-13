"""
John CRM — Sales Development Representative

Responsavel por conversar com clientes, qualificar leads e direcionar para o ecossistema.

Funciona como interface externa + SDR inteligente.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional


class JohnCRM:
    """
    CRM Assistant que qualifica leads e publica eventos para o core.
    """

    def __init__(self, nats_bus=None, sdk=None, logger=None):
        """
        Args:
            nats_bus: acesso ao barramento de eventos
            sdk: acesso ao SDK (CEFEIDA) para calculos
            logger: logger centralizado
        """
        self.bus = nats_bus
        self.sdk = sdk
        self.logger = logger or self._default_logger

    def _default_logger(self, msg):
        print(f"[JOHN-CRM] {msg}")

    async def chat(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Conversacao com cliente.
        Qualifica o lead a partir da mensagem.

        Args:
            message: mensagem do cliente
            context: contexto (sessionId, source, etc)

        Returns:
            {response: str, event: str, lead_intent: str}
        """

        context = context or {}
        lead_id = context.get("lead_id") or str(uuid.uuid4())

        # Analisar intenção
        intent = self._detect_intent(message)
        score = self._calculate_score(message, intent)

        # Gerar resposta apropriada
        response = self._generate_response(intent, message)

        # Preparar evento
        event_data = {
            "lead_id": lead_id,
            "name": context.get("name") or "Novo Cliente",
            "email": context.get("email") or "",
            "phone": context.get("phone") or "",
            "interest": intent,
            "source": context.get("source") or "site",
            "initial_score": score,
            "created_by": "john_crm",
            "estimated_value": self._estimate_value(intent),
            "created_at": datetime.utcnow().isoformat(),
        }

        # Publicar lead.created no barramento
        if self.bus:
            await self.bus.publish("crm.lead.created", event_data)

        # Log
        self.logger(f"Lead {lead_id} criado: {intent} (score:{score})")

        return {
            "response": response,
            "event": "lead.created",
            "lead_id": lead_id,
            "intent": intent,
            "score": score,
        }

    async def qualify_lead(self, lead_id: str, interactions: list) -> Dict[str, Any]:
        """
        Qualifica lead baseado em todas as interacoes.

        Args:
            lead_id: ID do lead
            interactions: lista de interacoes (mensagens)

        Returns:
            {lead_id, final_score, status, assigned_module, recommendation}
        """

        # Consolidar intenções
        intents = [self._detect_intent(int["content"]) for int in interactions]
        avg_score = sum(
            [self._calculate_score(int["content"], self._detect_intent(int["content"])) 
             for int in interactions]
        ) / len(interactions) if interactions else 0

        # Decidir status
        if avg_score > 75:
            status = "qualified"
            module = self._assign_module(intents[0] if intents else "unknown")
        elif avg_score > 50:
            status = "pending_more_info"
            module = "SALES"
        else:
            status = "rejected"
            module = None

        recommendation = self._qualify_recommendation(status, intents)

        event_data = {
            "lead_id": lead_id,
            "final_score": int(avg_score),
            "status": status,
            "assigned_module": module,
            "recommendation": recommendation,
            "qualified_at": datetime.utcnow().isoformat(),
        }

        # Publicar qualificacao
        if self.bus:
            await self.bus.publish("crm.lead.qualified", event_data)

        self.logger(f"Lead {lead_id} qualificado: {status} → {module}")

        return event_data

    def _detect_intent(self, message: str) -> str:
        """Detecta intenção do cliente a partir da mensagem."""
        message_lower = message.lower()

        # Mapeamento simples (em produção usar NLP/ML)
        intents = {
            "construction": ["construir", "obra", "casa", "prédio", "imóvel", "projeto"],
            "investment": ["investir", "rendimento", "retorno", "financeiro", "aplicação"],
            "partnership": ["parceria", "colaborar", "junto", "negócio", "joint"],
            "financing": ["financiar", "crédito", "empréstimo", "taxa"],
            "consulting": ["consultar", "orientação", "dúvida", "ajuda"],
        }

        for intent_label, keywords in intents.items():
            if any(keyword in message_lower for keyword in keywords):
                return intent_label

        return "inquiry"

    def _calculate_score(self, message: str, intent: str) -> int:
        """Calcula score de qualificacao (0-100)."""
        score = 50  # baseline

        # Mensagem detalhada = melhor score
        if len(message) > 50:
            score += 10
        if len(message) > 100:
            score += 10

        # Intenção clara = melhor score
        intent_weights = {
            "construction": 20,
            "investment": 25,
            "partnership": 15,
            "financing": 20,
            "consulting": 10,
            "inquiry": 5,
        }

        score += intent_weights.get(intent, 5)

        # Caps no máximo
        return min(score, 100)

    def _generate_response(self, intent: str, original_message: str) -> str:
        """Gera resposta inteligente baseada na intenção."""
        responses = {
            "construction": (
                "Vou estruturar seu projeto de construção. "
                "Estimativa inicial será gerada após análise de viabilidade. "
                "Quer avançar para estudo técnico?"
            ),
            "investment": (
                "Entendido. Tenho oportunidades de investimento com retorno "
                "de 15-25% ao ano. Qual seu capital inicial?"
            ),
            "partnership": (
                "Parceria interessante. Vou conectar você com nossos estrategistas. "
                "Qual área de negócio te interessa?"
            ),
            "financing": (
                "Podemos estruturar financiamento com taxas competitivas. "
                "Qual o valor e prazo que você precisa?"
            ),
            "consulting": (
                "Como posso ajudar? Posso conectar você a especialistas em construção, "
                "financeiro ou estratégia."
            ),
            "inquiry": "Obrigado por se interessar. Como posso ajudá-lo?",
        }

        return responses.get(intent, responses["inquiry"])

    def _estimate_value(self, intent: str) -> str:
        """Estimativa inicial de valor por tipo."""
        estimates = {
            "construction": "R$ 500.000 - R$ 5.000.000",
            "investment": "R$ 100.000 - R$ 2.000.000",
            "partnership": "A combinar",
            "financing": "A combinar",
            "consulting": "Sem custo",
            "inquiry": "A definir",
        }
        return estimates.get(intent, "A definir")

    def _assign_module(self, intent: str) -> Optional[str]:
        """Atribui o módulo responsável."""
        assignments = {
            "construction": "OPERA",
            "investment": "CEA",
            "partnership": "STRATEGY",
            "financing": "CEA",
            "consulting": "P&D",
        }
        return assignments.get(intent)

    def _qualify_recommendation(self, status: str, intents: list) -> str:
        """Recomendacao de próximo passo."""
        if status == "qualified":
            return "Lead pronto para pitch técnico e comercial"
        elif status == "pending_more_info":
            return "Solicitar mais informações sobre escopo e budget"
        else:
            return "Lead não qualificado no momento. Manter em nurture list"
