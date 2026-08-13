# Dependency Graph Global
"""
Gera o grafo de dependências Kanban → Runtime → Monólitos → Eventos → Ledger
Exporta em formato Mermaid para visualização.
"""
def build_dependency_graph():
    # Exemplo estático para MVP
    nodes = [
        "Kanban", "Runtime", "Monolitos", "Eventos", "Ledger"
    ]
    edges = [
        ("Kanban", "Runtime"),
        ("Runtime", "Monolitos"),
        ("Monolitos", "Eventos"),
        ("Eventos", "Ledger")
    ]
    return nodes, edges

def export_mermaid():
    nodes, edges = build_dependency_graph()
    lines = ["graph TD"]
    for src, dst in edges:
        lines.append(f"    {src} --> {dst}")
    return "\n".join(lines)

if __name__ == "__main__":
    print(export_mermaid())
