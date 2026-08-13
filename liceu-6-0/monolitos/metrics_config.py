"""
metrics_config.py
Configuração de métricas Prometheus para monolitos LICEU 6.0
"""
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total de requisições HTTP",
    ["method", "endpoint", "http_status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Duração das requisições HTTP em segundos",
    ["method", "endpoint"]
)

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response: Response = await call_next(request)
        process_time = time.time() - start_time
        REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
        REQUEST_LATENCY.labels(request.method, request.url.path).observe(process_time)
        return response

def metrics_endpoint():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
