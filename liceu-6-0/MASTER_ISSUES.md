# LICEU 6.0 - Master Issues

Backlog mestre em ordem de execucao. Cada issue tem objetivo, tasks, criterio de aceite, estado atual e principal ponto de ancoragem no repositorio.

## EPIC 1 - CORE-DNA

### ISSUE 1.1 - Definir eventos canonicos globais

- Objetivo: eliminar ambiguidade entre monolitos.
- Tasks: manter [core_dna/events.proto](core_dna/events.proto) como fonte unica para lead.created, match.generated, deal.closed, contract.created, contract.signed, commission.protected, payment.generated e versionamento v1/v2.
- Criterio de aceite: todos os eventos documentados e nenhum evento duplicado com nomes diferentes.
- Estado: em progresso.
- Ancora atual: [core_dna/events.proto](core_dna/events.proto).

### ISSUE 1.2 - Build automatico do CORE-DNA

- Objetivo: gerar bindings a partir da fonte unica.
- Tasks: manter [core-sdk/scripts/build_dna.sh](core-sdk/scripts/build_dna.sh) gerando Python bindings, TypeScript bindings e JSON schema.
- Criterio de aceite: o build roda sem erro e gera os SDKs automaticamente.
- Estado: em progresso.
- Ancora atual: [core-sdk/scripts/build_dna.sh](core-sdk/scripts/build_dna.sh).

### ISSUE 1.3 - Criar Event Registry central

- Objetivo: saber quem emite e quem consome cada evento.
- Tasks: manter [event-registry/events.json](event-registry/events.json) com source, consumers, versions e current_version.
- Criterio de aceite: cada evento possui source e consumers declarados.
- Estado: em progresso.
- Ancora atual: [event-registry/events.json](event-registry/events.json).

## EPIC 2 - EVENT BUS (NATS)

### ISSUE 2.1 - Subir NATS com JetStream

- Tasks: configurar Docker com -js e monitor ativo.
- Criterio de aceite: localhost:4222 e localhost:8222 respondem.
- Estado: concluido no ambiente local.
- Ancora atual: [infra/docker-compose.yml](infra/docker-compose.yml).

### ISSUE 2.2 - Criar SDK de eventos unificado

- Tasks: manter publish() e subscribe() em um unico SDK.
- Criterio de aceite: qualquer monolito conecta com poucas linhas.
- Estado: concluido para o fluxo base.
- Ancora atual: [core-sdk/sdk/event_bus.py](core-sdk/sdk/event_bus.py).

### ISSUE 2.3 - Padronizar topic unico

- Regra: tudo trafega em liceu.events.
- Criterio de aceite: nenhum monolito cria topic proprio como trilha principal.
- Estado: concluido para runtime, SDK e listeners ativos do bootstrap local.
- Ancora atual: [core-sdk/sdk/event_bus.py](core-sdk/sdk/event_bus.py).

## EPIC 3 - RUNTIME LICEU

### ISSUE 3.1 - Criar runtime central

- Tasks: listener global e orquestracao central.
- Criterio de aceite: runtime escuta o barramento canonico.
- Estado: concluido para logging base.
- Ancora atual: [runtime/main.py](runtime/main.py).

### ISSUE 3.2 - Implementar roteamento inteligente

- Tasks: explicitar fluxos criticos entre monolitos.
- Criterio de aceite: deal.closed gera reacao no juridico e no financeiro por evento.
- Estado: parcialmente concluido via handlers de monolitos.
- Ancora atual: [monolitos/juridicotech/main.py](monolitos/juridicotech/main.py), [monolitos/hubbackoffice/main.py](monolitos/hubbackoffice/main.py).

### ISSUE 3.3 - Logging centralizado

- Tasks: logar todos os eventos e persistir historico.
- Criterio de aceite: runtime mantem trilha auditavel dos eventos.
- Estado: parcial; runtime persiste historico local e em Redis Stream com retries e replay manual, faltando retencao operacional e replay seletivo.
- Ancora atual: [runtime/main.py](runtime/main.py).

## EPIC 4 - JURIDICOTECH

### ISSUE 4.1 - Listener de eventos juridicos

- Eventos: deal.closed, proposal.sent.
- Estado: concluido para bootstrap local.

### ISSUE 4.2 - Geracao automatica de contrato

- Output: contract.created.
- Estado: concluido para o fluxo base com proposal.sent antecedendo contract.created.

### ISSUE 4.3 - Assinatura digital

- Output: contract.signed.
- Estado: concluido para o bootstrap local.

### ISSUE 4.4 - Protecao de comissao

- Output: commission.protected.
- Estado: concluido para o fluxo base.

### ISSUE 4.5 - Integracao com todos monolitos

- Regra: nenhum deal fecha sem juridico.
- Estado: pendente como regra sistemica.

## EPIC 5 - HUB BACKOFFICE

### ISSUE 5.1 - Listener financeiro global

- Eventos: contract.signed, deal.closed.
- Estado: parcial.

### ISSUE 5.2 - Contas a pagar/receber automatico

- Output: payment.generated.
- Estado: concluido para o fluxo base.

### ISSUE 5.3 - Integracao contabil

- Estado: pendente.

### ISSUE 5.4 - RH e estrutura organizacional

- Estado: pendente.

## EPIC 6 - JOHN

### ISSUE 6.1 - Listener universal de eventos

- Estado: parcial; lead.created implementado.

### ISSUE 6.2 - Engine de sugestao

- Exemplo: lead.created -> abordagem.
- Estado: parcial.

### ISSUE 6.3 - Memory layer

- Aprende com deal.won e deal.lost.
- Estado: pendente.

## EPIC 7 - ARCHIMEDES

### ISSUE 7.1 - Emitir eventos corretos

- Eventos: lead.created e deal.closed.
- Estado: concluido para bootstrap local.

### ISSUE 7.2 - Remover logica interna duplicada

- Regra: nao calcular juridico nem financeiro localmente.
- Estado: diretriz definida, revisao ampla ainda pendente.

### ISSUE 7.3 - Consumir respostas do ecossistema

- Contract status e payment status.
- Estado: pendente.

## EPIC 8 - CEFEIDA

### ISSUE 8.1 - Engine de analise via evento

- Input: lead.created.
- Output: match.generated.
- Estado: pendente.

### ISSUE 8.2 - Score de mercado

- Estado: pendente.

## EPIC 9 - CEA

### ISSUE 9.1 - Simulacao via evento

- Input: simulation.requested.
- Output: finance.generated.
- Estado: pendente.

## EPIC 10 - GAMEMKT

### ISSUE 10.1 - Listener de comportamento

- Eventos: lead.created, client.silent.
- Estado: parcial; lead.created implementado.

### ISSUE 10.2 - Disparo de campanhas

- Output: campaign.triggered.
- Estado: concluido para o fluxo base.

## EPIC 11 - GOVERNANCE

### ISSUE 11.1 - Criar sistema de usuarios unico

- Perfis: ADMIN, BROKER, CLIENT, SYSTEM.
- Estado: pendente.

### ISSUE 11.2 - Permissoes por monolito

- Estado: pendente.

### ISSUE 11.3 - Auditoria global

- Estado: pendente.

## EPIC 12 - OBSERVABILIDADE

### ISSUE 12.1 - Prometheus

- Estado: scaffold concluido; instrumentacao por aplicacao pendente.

### ISSUE 12.2 - Grafana

- Estado: scaffold concluido; dashboards de negocio pendentes.

### ISSUE 12.3 - Logs centralizados

- Estado: scaffold concluido com Loki; pipeline de logs ainda basico.

## EPIC 13 - API GATEWAY (KONG)

### ISSUE 13.1 - Centralizar entrada

- Estado: parcial; gateway local ativo para Archimedes e NATS monitor.

### ISSUE 13.2 - Rate limiting

- Estado: pendente.

## EPIC 14 - KANBAN GLOBAL

### ISSUE 14.1 - Criar modelo de tarefas

- Estado: pendente.

### ISSUE 14.2 - Timeline por projeto

- Estado: pendente.

### ISSUE 14.3 - Notificacoes cross-monolito

- Estado: pendente.

## EPIC FINAL - BOOTSTRAP TOTAL

### ISSUE FINAL - Subir sistema completo local

- Ordem: docker compose up, build core-dna, subir runtime, subir monolitos, testar evento.
- Estado: concluido para o bootstrap local validado, com imagens Python preparadas sem pip install no startup.
- Ancora atual: [README.md](README.md).

## Regra operacional

- Cada monolito implementa SDK, subscribe() e publish().
- CORE-DNA, Event Bus e Governance permanecem unicos.