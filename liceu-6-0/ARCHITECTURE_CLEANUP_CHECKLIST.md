# Checklist de Limpeza de Arquitetura (EPIC J)

## J.1 — Remover lógica duplicada
- [ ] Identificar funções/fluxos repetidos em Archimedes, Hub, Jurídico
- [ ] Consolidar lógica em módulos centrais ou SDK
- [ ] Remover código morto/duplicado

## J.2 — Garantir “Thin Monolith”
- [ ] Monólito não toma decisão de negócio
- [ ] Apenas reage a eventos e publica comandos/eventos
- [ ] Toda lógica de decisão fica em engines/serviços

## J.3 — Proibir acesso direto ao banco entre módulos
- [ ] Buscar por imports de drivers SQL/ORM fora do módulo de persistência
- [ ] Refatorar para uso de eventos para comunicação entre domínios
- [ ] Validar via revisão de código e scripts de lint
