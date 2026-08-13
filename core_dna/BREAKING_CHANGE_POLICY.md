# Breaking Change Policy para eventos LICEU

- Toda alteração que remova, renomeie ou altere o significado de campos em eventos existentes deve ser considerada breaking change.
- Para breaking changes, crie uma nova versão do evento (ex: v2) e mantenha suporte à versão anterior pelo menos até todos os consumidores migrarem.
- Campos opcionais podem ser adicionados em versões existentes, mas nunca removidos.
- Mudanças em schemas devem ser refletidas em core_dna/event_names.json e versionadas (ex: lead.created v1 → lead.created v2).
- Toda alteração de schema deve ser acompanhada de atualização dos testes de contrato e documentação automática.

## Exemplo de versionamento de schema

- lead.created v1: `{ lead_id, name, email }`
- lead.created v2: `{ lead_id, name, email, phone }`

Ambas as versões coexistem até o fim da migração.
