# Métricas simples por monolito
from prometheus_client import Counter, Histogram, start_http_server

received_events = Counter('monolito_events_received', 'Eventos recebidos')
failed_events = Counter('monolito_events_failed', 'Eventos falhos')
event_latency = Histogram('monolito_event_latency_seconds', 'Latência de eventos')

def start_metrics_server(port=9000):
    start_http_server(port)
