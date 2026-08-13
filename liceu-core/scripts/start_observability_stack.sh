#!/bin/bash
# start_observability_stack.sh
# Sobe Grafana, Prometheus, Loki, Tempo, Jaeger

docker compose -f ../docker-compose.runtime.yml up -d grafana prometheus loki tempo jaeger
