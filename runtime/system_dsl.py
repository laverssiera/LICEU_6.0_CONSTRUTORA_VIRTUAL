# System DSL — Linguagem Operacional Única
"""
Exemplo de regra em DSL:

WHEN pipeline.stage = VIABILIDADE_FINANCEIRA
IF score > 70
THEN allow transition TO APROVADO
ELSE block + audit
"""
import re
from typing import Any, Dict

class SystemDSLRule:
    def __init__(self, dsl_text: str):
        self.dsl_text = dsl_text
        self.parsed = self.parse(dsl_text)

    def parse(self, text: str) -> Dict[str, Any]:
        # Parsing simples para MVP
        # Suporta: WHEN ... IF ... THEN ... ELSE ...
        pattern = r"WHEN (.+?)\\nIF (.+?)\\nTHEN (.+?)(?:\\nELSE (.+))?"
        match = re.search(pattern, text, re.DOTALL)
        if not match:
            raise ValueError("DSL inválida")
        return {
            "when": match.group(1).strip(),
            "if": match.group(2).strip(),
            "then": match.group(3).strip(),
            "else": match.group(4).strip() if match.group(4) else None
        }

    def evaluate(self, context: Dict[str, Any]) -> str:
        # Avaliação simplificada (exemplo)
        # context: {"pipeline.stage": "VIABILIDADE_FINANCEIRA", "score": 80}
        when_cond = self.parsed["when"]
        if_cond = self.parsed["if"]
        then_action = self.parsed["then"]
        else_action = self.parsed["else"]

        # WHEN
        when_key, when_val = [x.strip() for x in when_cond.split("=")]
        if context.get(when_key) != when_val:
            return "SKIP"
        # IF
        # Suporta apenas 'score > N' para MVP
        if ">" in if_cond:
            key, val = [x.strip() for x in if_cond.split(">")]
            if float(context.get(key, 0)) > float(val):
                return then_action
            else:
                return else_action or "BLOCK"
        # Outros operadores podem ser adicionados
        return "BLOCK"

# Exemplo de uso
if __name__ == "__main__":
    dsl = """WHEN pipeline.stage = VIABILIDADE_FINANCEIRA\nIF score > 70\nTHEN allow transition TO APROVADO\nELSE block + audit"""
    rule = SystemDSLRule(dsl)
    ctx = {"pipeline.stage": "VIABILIDADE_FINANCEIRA", "score": 80}
    print(rule.evaluate(ctx))  # allow transition TO APROVADO
    ctx2 = {"pipeline.stage": "VIABILIDADE_FINANCEIRA", "score": 60}
    print(rule.evaluate(ctx2))  # block + audit
