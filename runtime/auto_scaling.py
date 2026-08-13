# Autoescalonamento simples baseado em backlog de eventos
import random

def get_event_backlog():
    # Simulação: substitua por consulta real ao Event Bus/Queue
    return random.randint(0, 1000)

def auto_scale(min_instances=1, max_instances=10, backlog_threshold=200):
    backlog = get_event_backlog()
    if backlog > backlog_threshold:
        scale = min(max_instances, min_instances + backlog // backlog_threshold)
        print(f"[AUTO-SCALING] Aumentando para {scale} instâncias (backlog={backlog})")
        # Aqui: integração real com orquestrador (K8s, Docker, etc)
    else:
        print(f"[AUTO-SCALING] Mantendo {min_instances} instância(s) (backlog={backlog})")

if __name__ == "__main__":
    auto_scale()
