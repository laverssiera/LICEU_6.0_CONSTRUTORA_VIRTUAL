from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from app.config import settings
from app.models.backoffice import BackofficeLead

TOKEN_PATTERN = re.compile(r"[a-z0-9_]+", re.IGNORECASE)


@dataclass
class ScoringModel:
    bias: float
    weights: dict[str, float]


class CRMScoringService:
    """Lightweight scorer for lead intent quality without external ML dependencies."""

    def __init__(self, model_path: str | None = None) -> None:
        raw_path = model_path or settings.CRM_SCORING_MODEL_PATH
        self.model_path = Path(raw_path)
        self.model = self._load_or_default()

    def score(self, *, message: str, profile: str, source: str) -> float:
        tokens = self._tokenize(message)
        score = self.model.bias

        for token in tokens:
            score += self.model.weights.get(token, 0.0)

        score += self._profile_bias(profile)
        score += self._source_bias(source)
        probability = 1.0 / (1.0 + math.exp(-score))
        return round(max(0.0, min(100.0, probability * 100.0)), 2)

    def retrain_from_leads(self, leads: Iterable[BackofficeLead]) -> dict[str, float | int]:
        positive = []
        negative = []

        for lead in leads:
            text = (lead.request_text or "").strip()
            if not text:
                continue
            tokens = set(self._tokenize(text))
            if not tokens:
                continue

            status = (lead.status or "").lower()
            is_positive = status in {"qualified", "converted", "won"} or float(lead.thermometer_score or 0) >= 70
            if is_positive:
                positive.append(tokens)
            else:
                negative.append(tokens)

        total = len(positive) + len(negative)
        if total < 8:
            return {
                "trained_examples": total,
                "status": "insufficient_data",
            }

        token_stats: dict[str, list[int]] = {}
        for bucket, rows in ((0, negative), (1, positive)):
            for row in rows:
                for token in row:
                    token_stats.setdefault(token, [0, 0])[bucket] += 1

        new_weights: dict[str, float] = {}
        for token, (neg_count, pos_count) in token_stats.items():
            # Laplace smoothing avoids zero-division and controls overfitting.
            p_pos = (pos_count + 1.0) / (len(positive) + 2.0)
            p_neg = (neg_count + 1.0) / (len(negative) + 2.0)
            weight = math.log(p_pos / p_neg)
            if abs(weight) >= 0.06:
                new_weights[token] = round(weight, 5)

        base_pos = (len(positive) + 1.0) / (total + 2.0)
        base_neg = (len(negative) + 1.0) / (total + 2.0)
        new_bias = round(math.log(base_pos / base_neg), 5)

        self.model = ScoringModel(bias=new_bias, weights=new_weights)
        self._persist()

        return {
            "trained_examples": total,
            "positive_examples": len(positive),
            "negative_examples": len(negative),
            "weights": len(new_weights),
            "status": "trained",
        }

    def _load_or_default(self) -> ScoringModel:
        if self.model_path.exists():
            try:
                payload = json.loads(self.model_path.read_text(encoding="utf-8"))
                bias = float(payload.get("bias", 0.0))
                weights = {str(k): float(v) for k, v in (payload.get("weights") or {}).items()}
                return ScoringModel(bias=bias, weights=weights)
            except Exception:
                pass

        return ScoringModel(
            bias=0.0,
            weights={
                "investir": 0.95,
                "investimento": 0.88,
                "retorno": 0.62,
                "obra": 0.61,
                "construcao": 0.69,
                "parceria": 0.54,
                "orcamento": 0.47,
                "curso": 0.35,
                "duvida": -0.18,
                "talvez": -0.24,
                "depois": -0.35,
            },
        )

    def _persist(self) -> None:
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "bias": self.model.bias,
            "weights": self.model.weights,
        }
        self.model_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    @staticmethod
    def _profile_bias(profile: str) -> float:
        normalized = (profile or "").lower()
        return {
            "investidor": 0.45,
            "cliente": 0.38,
            "fornecedor": 0.2,
            "aluno": 0.15,
        }.get(normalized, 0.0)

    @staticmethod
    def _source_bias(source: str) -> float:
        normalized = (source or "").lower()
        return {
            "whatsapp": 0.28,
            "site": 0.1,
            "crm": 0.16,
            "referral": 0.2,
        }.get(normalized, 0.0)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [token.lower() for token in TOKEN_PATTERN.findall(text or "") if len(token) > 2]
