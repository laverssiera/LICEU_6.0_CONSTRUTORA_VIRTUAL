# runtime

Listener central do ecossistema. O runtime consome apenas o topico canonico `liceu.events`, consulta o registry central para mostrar a rota prevista dos eventos e persiste historico local em `runtime/data/events.jsonl`.

Responsabilidades atuais:
- logging central de todos os eventos recebidos
- persistencia append-only do historico
- leitura do registry central para explicar consumidores esperados
- persistencia externa do historico em Redis Stream
- trilha de dead-letter em Redis Stream e arquivo local
- retries de persistencia para streams operacionais
- replay manual da dead-letter via replay_dead_letters.py
- bootstrap previsivel com dependencias instaladas na imagem

Responsabilidades ainda pendentes:
- enforcement de politicas de roteamento no barramento
