# Gera documentação automática dos eventos registrados
import json
from pathlib import Path

EVENTS_PATH = Path(__file__).parent.parent / "core_dna" / "event_names.json"
DOC_PATH = Path(__file__).parent.parent / "core_dna" / "EVENTS_DOC.md"

def main():
    with open(EVENTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    lines = ["# Documentação dos Eventos\n"]
    lines.append("| Evento | Versão | Domínio | Descrição |")
    lines.append("|--------|--------|---------|-----------|")
    for e in data["events"]:
        desc = e.get("description", "-")
        lines.append(f"| {e['name']} | {e['version']} | {e['domain']} | {desc} |")
    with open(DOC_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Documentação gerada em {DOC_PATH}")

if __name__ == "__main__":
    main()
