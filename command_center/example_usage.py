"""
Exemplo de uso do LICEU COMMAND CENTER
"""
from control_center import CommandCenter

def main():
    center = CommandCenter()
    # Registrar camada operacional
    center.register_layer("obras", {"ativas": 12, "finalizadas": 3})
    # Atualizar telemetria
    center.update_telemetry("cpu_usage", 42)
    center.update_telemetry("health_score", 87)
    # Consultar dashboard
    dashboard = center.get_dashboard()
    print("Dashboard do Command Center:", dashboard)

if __name__ == "__main__":
    main()
