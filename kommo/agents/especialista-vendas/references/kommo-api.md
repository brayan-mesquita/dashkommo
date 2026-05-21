# Kommo API para relatórios

## Credenciais mínimas

O script usa estas variáveis de ambiente:

- `KOMMO_SUBDOMAIN`
- `KOMMO_ACCESS_TOKEN`

Formato base da URL:

- `https://{KOMMO_SUBDOMAIN}.kommo.com`

## Endpoints principais usados pelo agente

- `/api/v4/account`
- `/api/v4/users`
- `/api/v4/leads/pipelines`
- `/api/v4/leads`
- `/api/v4/contacts`
- `/api/v4/companies`
- `/api/v4/tasks`
- `/api/v4/events`
- `/api/v4/events/types`
- `/api/v4/leads/notes`
- `/api/v4/contacts/notes`
- `/api/v4/companies/notes`
- `/api/v4/leads/custom_fields`
- `/api/v4/contacts/custom_fields`
- `/api/v4/companies/custom_fields`
- `/api/v4/catalogs`

O script `kommo_fetch.py` aceita tanto aliases conhecidos quanto um path bruto `/api/v4/...`, então o agente não fica preso a uma lista fixa de recursos.

## Fluxo recomendado

1. Testar conexão com `account`.
2. Buscar pipelines, usuários e campos personalizados.
3. Coletar snapshot da janela desejada com leads criados, ganhos, perdidos, tarefas abertas e eventos.
4. Gerar métricas de decisão: séries, gargalos por etapa, aging, donos, perdas e transições.
5. Salvar snapshot bruto quando precisar auditoria ou reprodução do relatório.

## Exemplos

```bash
python3 skills/crm-consultas-relatorios/scripts/kommo_fetch.py --list-resources
python3 skills/crm-consultas-relatorios/scripts/kommo_fetch.py account --env-file ../../.env.kommo
python3 skills/crm-consultas-relatorios/scripts/kommo_fetch.py events --env-file ../../.env.kommo --all-pages --param filter[created_at][from]=1711324800
python3 skills/crm-consultas-relatorios/scripts/kommo_fetch.py /api/v4/leads/pipelines --env-file ../../.env.kommo
python3 skills/crm-consultas-relatorios/scripts/kommo_report.py snapshot --env-file ../../.env.kommo --days 30 --output ../../data/kommo-snapshot.json
python3 skills/crm-consultas-relatorios/scripts/kommo_report.py report --env-file ../../.env.kommo --days 30 --interval week --output ../../data/kommo-report.json
```

## Observações

- Use paginação para entidades grandes.
- Normalize datas, owners, status e pipelines antes de montar relatórios.
- Se houver múltiplos pipelines, segmentar os indicadores por pipeline antes de consolidar.
- O relatório genérico já entrega: visão geral, série temporal, resumo por pipeline, etapas, owners, perdas, tarefas abertas, leads parados, eventos e catálogo de campos.
