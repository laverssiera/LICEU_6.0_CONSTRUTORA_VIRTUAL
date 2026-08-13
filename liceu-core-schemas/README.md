# liceu-core-schemas

Schema Registry global do ecossistema Liceu 6.0.

## Objetos principais
- BuildingBlock: insumos, kits e módulos compartilhados entre Engenharia, Orçamento e Supply.
- BudgetEnvelope: envelope orçamentário consolidado com subtotal, contingência e impostos.
- LiceuToken: representação da moeda interna com saldo disponível e lastro em BRL.
- CognitivePulse: mensagem cognitiva do Joh Brasileiro para eventos de cultura, qualidade e compliance.

## Uso rápido
Os modelos ficam disponíveis no pacote Python `liceu_core_schemas` e podem ser exportados para JSON Schema via `export_schema_registry()`.
