# Métricas de fluxo por pipeline e monólito
from prometheus_client import Counter, Histogram, start_http_server

pipeline_events = Counter('pipeline_events_total', 'Eventos por pipeline', ['tenant_id', 'pipeline_id', 'event_type'])
pipeline_invalid_events = Counter('pipeline_invalid_events_total', 'Eventos inválidos por pipeline', ['tenant_id', 'pipeline_id', 'event_type'])
pipeline_stage_time = Histogram('pipeline_stage_time_seconds', 'Tempo por stage', ['tenant_id', 'pipeline_id', 'stage'])
monolith_error_rate = Counter('monolith_error_total', 'Taxa de erro por monólito', ['tenant_id', 'monolith'])

# Exemplo de uso:
def start_metrics_server(port=9100):
    start_http_server(port)
