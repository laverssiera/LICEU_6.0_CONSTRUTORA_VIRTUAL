# Checklist de Onboarding de Monólito

## 1. Uso do SDK
- [ ] Monólito utiliza o SDK oficial para emissão e consumo de eventos.
- [ ] Não há uso direto de NATS/event bus sem o SDK.

## 2. Respeito ao Pipeline
- [ ] Todas as operações seguem o fluxo de pipeline definido (Kanban).
- [ ] Não há bypass de estágios ou transições não auditadas.

## 3. Métricas
- [ ] Monólito expõe métricas Prometheus (pipeline_events_total, error_rate, etc).
- [ ] Métricas incluem tenant_id, pipeline_id e event_type.

## 4. Auditoria
- [ ] Todas as ações críticas são auditadas (event_store, pipeline_history).
- [ ] Auditoria inclui policy_version e correlation_id.

## 5. Testes de Integração
- [ ] Monólito passou por testes de integração em sandbox/simulação.
- [ ] Falhas e exceções são tratadas e auditadas.

## 6. Aprovação
- [ ] Checklist revisado e aprovado por responsável técnico.
- [ ] Registro de aprovação no Control Plane.

---

**Atenção:** Monólitos que não cumprirem todos os itens não devem ser promovidos para produção.
