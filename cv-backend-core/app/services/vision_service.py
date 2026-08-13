from __future__ import annotations

import importlib.util
from collections import Counter
from pathlib import Path
from typing import Any


class ConcreteVisionAI:
    provider = "concrete-vision-ai"

    PATHOLOGY_MAP = {
        "fissura": {
            "code": "fissura_estrutural",
            "label": "Fissura Estrutural",
            "severity": "critical",
            "recommendation": "Revisar detalhamento estrutural e sequência de cura do concreto.",
        },
        "infiltr": {
            "code": "infiltracao_junta",
            "label": "Infiltração em Junta",
            "severity": "warning",
            "recommendation": "Refazer vedação e validar pontos de impermeabilização.",
        },
        "corros": {
            "code": "corrosao_armadura",
            "label": "Corrosão de Armadura",
            "severity": "critical",
            "recommendation": "Inspecionar armaduras expostas e revisar cobrimento mínimo.",
        },
        "desalinh": {
            "code": "desalinhamento_modular",
            "label": "Desalinhamento Modular",
            "severity": "warning",
            "recommendation": "Recalibrar gabarito e revisar encaixe DFMA.",
        },
    }

    def inspect_pathologies(
        self,
        observations: list[str],
        discipline: str,
        artifact_uri: str | None = None,
    ) -> dict[str, Any]:
        findings = []

        for raw in observations or []:
            text = raw.lower()
            matched = False
            for keyword, meta in self.PATHOLOGY_MAP.items():
                if keyword in text:
                    findings.append({**meta, "evidence": raw})
                    matched = True
                    break
            if not matched:
                findings.append(
                    {
                        "code": "anomalia_em_analise",
                        "label": "Anomalia em análise",
                        "severity": "info",
                        "recommendation": "Coletar nova evidência visual e revisar checklist de campo.",
                        "evidence": raw,
                    }
                )

        if not findings:
            findings.append(
                {
                    "code": "monitoramento_preventivo",
                    "label": "Monitoramento Preventivo",
                    "severity": "info",
                    "recommendation": "Seguir rotina normal de inspeção preventiva.",
                    "evidence": "Sem observações informadas",
                }
            )

        counts = Counter(item["code"] for item in findings)
        top_pathology = counts.most_common(1)[0][0]
        highest_severity = "critical" if any(item["severity"] == "critical" for item in findings) else "warning" if any(item["severity"] == "warning" for item in findings) else "info"
        lessons = self._load_lessons_learned(discipline)

        return {
            "provider": self.provider,
            "artifact_uri": artifact_uri,
            "discipline": discipline,
            "total_findings": len(findings),
            "top_pathology": top_pathology,
            "severity": highest_severity,
            "summary": f"{len(findings)} evidências analisadas para {discipline}; patologia dominante: {top_pathology}.",
            "primary_action": findings[0]["recommendation"],
            "findings": findings,
            "lessons_learned": lessons,
        }

    def _load_lessons_learned(self, discipline: str) -> dict[str, Any]:
        feedback_path = Path(__file__).resolve().parent / "engenharia_bim.py" / "workflow" / "feedback_patologias.py"
        if feedback_path.exists():
            spec = importlib.util.spec_from_file_location("feedback_patologias", feedback_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "injetar_licoes_aprendidas"):
                    return module.injetar_licoes_aprendidas(discipline)

        return {
            "disciplina": discipline,
            "trava_seguranca": "ATIVADA",
            "instrucao_tecnica": "Revisar padrões executivos e memorial descritivo.",
            "msg_qualidade": "Aprendizado padrão carregado pelo John Brasileiro.",
        }
