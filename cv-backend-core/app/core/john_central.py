from __future__ import annotations

import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class JohnContact(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None


class JohnContext(BaseModel):
    current_page: str = "Liceu-Home"
    user_type: str = "Guest"
    contact: JohnContact = Field(default_factory=JohnContact)
    session_id: str | None = None


class JohnWelcomeRequest(BaseModel):
    request: str = Field(min_length=3, max_length=400)
    context: JohnContext = Field(default_factory=JohnContext)


class JohnDiscussRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=80)
    message: str = Field(min_length=3, max_length=400)
    target_john: str = Field(min_length=3, max_length=80)
    conversation_id: str = Field(default_factory=lambda: str(uuid4()))


INTENT_RULES: list[dict[str, Any]] = [
    {
        "intent": "INVESTMENT_QUERY",
        "profile": "investidor",
        "redirect_to": "CEA_INVESTIMENTOS_PORTAL",
        "consult_local_john": "JOHN_BIM_IA",
        "priority": 40,
        "keywords": ["investir", "investimento", "retorno", "cotas", "rentabilidade", "aporte"],
    },
    {
        "intent": "ASSET_DISCOVERY",
        "profile": "cliente",
        "redirect_to": "ARCHIMEDES_PORTAL",
        "consult_local_john": "JOHN_ARCHIMEDES",
        "priority": 20,
        "keywords": ["terreno", "terrenos", "casa", "casas", "imovel", "imóvel", "lote"],
    },
    {
        "intent": "LEARNING_PATH",
        "profile": "aluno",
        "redirect_to": "ACADEMIA_SABER_PORTAL",
        "consult_local_john": "JOHN_ACADEMIA",
        "priority": 30,
        "keywords": ["curso", "cursos", "treinamento", "academia", "aprender", "escola"],
    },
    {
        "intent": "SUPPLIER_SYNC",
        "profile": "fornecedor",
        "redirect_to": "ERP_FORNECEDORES_PORTAL",
        "consult_local_john": "JOHN_FORNECEDORES",
        "priority": 25,
        "keywords": ["fornecedor", "estoque", "kits", "kit", "entrega", "suprimentos"],
    },
]

LOCAL_JOHNS: dict[str, dict[str, Any]] = {
    "JOHN_FORNECEDORES": {
        "monolith": "erp_fornecedores",
        "answer": "Estoque estratégico disponível para consulta e reserva assistida.",
        "status": "online",
    },
    "JOHN_BIM_IA": {
        "monolith": "bim_arqu_eng",
        "answer": "Modelos sustentáveis homologados com performance energética ativa.",
        "status": "online",
    },
    "JOHN_ARCHIMEDES": {
        "monolith": "archimedes",
        "answer": "Portfólio de terrenos e ativos com leitura de viabilidade atualizada.",
        "status": "online",
    },
    "JOHN_ACADEMIA": {
        "monolith": "academia_saber",
        "answer": "Trilhas de formação e capacitação prontas para matrícula guiada.",
        "status": "online",
    },
}


def _score_keyword(text: str, keyword: str) -> float:
    if keyword in text:
        return 1.0
    return SequenceMatcher(None, text, keyword).ratio()


def route_intent(message: str) -> dict[str, Any]:
    text = message.lower()
    tokens = set(re.findall(r"\w+", text, flags=re.UNICODE))
    best_rule = INTENT_RULES[0]
    best_score = -1.0

    for rule in INTENT_RULES:
        exact_matches = sum(
            1
            for keyword in rule["keywords"]
            if (" " in keyword and keyword in text) or keyword in tokens
        )
        fuzzy_score = max((_score_keyword(text, keyword) for keyword in rule["keywords"]), default=0.0)
        score = (exact_matches * 100) + (fuzzy_score * 10) + rule.get("priority", 0)
        if score > best_score:
            best_rule = rule
            best_score = score

    return {**best_rule, "match_score": round(best_score / 10, 2)}


def compute_thermometer(message: str, context: JohnContext, match_score: float) -> dict[str, Any]:
    score = 40 + min(int(match_score * 4), 35)
    if context.contact.email:
        score += 15
    if context.contact.name:
        score += 10
    if context.user_type.lower() != "guest":
        score += 5
    score = max(0, min(score, 99))

    band = "alto" if score >= 80 else "médio" if score >= 60 else "baixo"
    return {"score": score, "band": band}


def resolve_session_id(context: JohnContext) -> str:
    return context.session_id or str(uuid4())


def build_lead_payload(payload: JohnWelcomeRequest, action: dict[str, Any], thermometer: dict[str, Any], session_id: str) -> dict[str, Any]:
    return {
        "name": payload.context.contact.name or "Visitante",
        "email": payload.context.contact.email or f"anon-{session_id[:8]}@lead.local",
        "source_page": payload.context.current_page,
        "user_type": payload.context.user_type,
        "inferred_profile": action["profile"],
        "intent": action["intent"],
        "redirect_to": action["redirect_to"],
        "request_text": payload.request,
        "thermometer_score": float(thermometer["score"]),
        "session_id": session_id,
        "status": "qualified" if thermometer["score"] >= 70 else "captured",
    }


def build_welcome_response(payload: JohnWelcomeRequest) -> dict[str, Any]:
    action = route_intent(payload.request)
    session_id = resolve_session_id(payload.context)
    thermometer = compute_thermometer(payload.request, payload.context, action["match_score"])
    return {
        "request": payload.request,
        "profile": action["profile"],
        "session_id": session_id,
        "thermometer": thermometer,
        "john_action": {
            "intent": action["intent"],
            "redirect_to": action["redirect_to"],
            "consult_local_john": action["consult_local_john"],
        },
        "context": {
            "current_page": payload.context.current_page,
            "user_type": payload.context.user_type,
        },
    }


def discuss_with_local_john(payload: JohnDiscussRequest) -> dict[str, Any]:
    target = LOCAL_JOHNS.get(
        payload.target_john,
        {
            "monolith": "core_os",
            "answer": "John local indisponível; consulta encaminhada ao núcleo central.",
            "status": "fallback",
        },
    )

    telemetry = {
        "conversation_id": payload.conversation_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "topic": payload.topic,
        "target_john": payload.target_john,
        "target_monolith": target["monolith"],
        "message": payload.message,
        "status": target["status"],
    }

    return {
        "status": "discussed",
        "target_john": payload.target_john,
        "response": {
            "monolith": target["monolith"],
            "answer": target["answer"],
        },
        "telemetry": telemetry,
    }
