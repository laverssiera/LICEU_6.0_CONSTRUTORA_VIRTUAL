from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings

PHONE_DIGITS = re.compile(r"\D+")


@dataclass
class WhatsAppDeliveryResult:
    channel: str
    status: str
    to: str
    provider: str
    message_id: str | None = None
    detail: str | None = None


class WhatsAppBusinessService:
    def __init__(self) -> None:
        self.enabled = settings.WHATSAPP_ENABLED
        self.version = settings.WHATSAPP_GRAPH_VERSION
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.token = settings.WHATSAPP_ACCESS_TOKEN

    def send_text(self, *, to: str, body: str) -> WhatsAppDeliveryResult:
        target = self._normalize_phone(to)
        if not target:
            return WhatsAppDeliveryResult(
                channel="whatsapp",
                status="invalid_phone",
                to=to,
                provider="meta",
                detail="Telefone inválido para envio WhatsApp.",
            )

        if not self.enabled or not self.token or not self.phone_number_id:
            return WhatsAppDeliveryResult(
                channel="whatsapp",
                status="queued",
                to=target,
                provider="meta",
                detail="Modo simulado: configure WHATSAPP_ENABLED/token/phone_number_id para envio real.",
            )

        url = f"https://graph.facebook.com/{self.version}/{self.phone_number_id}/messages"
        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": target,
            "type": "text",
            "text": {"preview_url": False, "body": body[:1024]},
        }
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=7.0)
            response.raise_for_status()
            data = response.json()
            message_id = None
            messages = data.get("messages") if isinstance(data, dict) else None
            if isinstance(messages, list) and messages:
                message_id = messages[0].get("id")
            return WhatsAppDeliveryResult(
                channel="whatsapp",
                status="sent",
                to=target,
                provider="meta",
                message_id=message_id,
            )
        except Exception as exc:
            return WhatsAppDeliveryResult(
                channel="whatsapp",
                status="error",
                to=target,
                provider="meta",
                detail=str(exc),
            )

    def default_contact(self) -> str:
        return self._normalize_phone(settings.WHATSAPP_BUSINESS_NUMBER)

    def readiness(self) -> dict[str, Any]:
        token_configured = bool(self.token)
        phone_id_configured = bool(self.phone_number_id)
        ready = bool(self.enabled and token_configured and phone_id_configured)
        return {
            "enabled": bool(self.enabled),
            "ready": ready,
            "graph_version": self.version,
            "phone_number_id_configured": phone_id_configured,
            "access_token_configured": token_configured,
            "default_contact": self.default_contact(),
        }

    @staticmethod
    def _normalize_phone(raw: str | None) -> str:
        digits = PHONE_DIGITS.sub("", raw or "")
        if not digits:
            return ""

        if digits.startswith("0"):
            digits = digits.lstrip("0")

        if not digits.startswith(settings.WHATSAPP_DEFAULT_COUNTRY_CODE):
            digits = f"{settings.WHATSAPP_DEFAULT_COUNTRY_CODE}{digits}"

        if len(digits) < 12:
            return ""
        return digits
