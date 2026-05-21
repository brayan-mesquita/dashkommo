# Kommo CRM API - Guia de Referência Completo

Este documento serve como base de conhecimento técnica sobre a API do Kommo (v4) para integração, consulta e implementação de dados. Ele foi consolidado para fornecer contexto a sistemas de IA e desenvolvedores.

---

## 1. Configuração e Autenticação

### Base URL
A URL base para todas as chamadas é dinâmica baseada no subdomínio da conta:
`https://{subdomain}.kommo.com/api/v4`

### Cabeçalhos (Headers) Obrigatórios
Todas as requisições devem incluir:
- `Authorization: Bearer {ACCESS_TOKEN}`
- `Content-Type: application/json`
- `Accept: application/json`

### Formatos de Dados
- **Protocolo:** JSON para requisições e respostas.
- **Timestamps:** Todas as datas e horas utilizam **Unix Timestamps** (segundos desde a época).
- **Paginação:** Padrão de até 250 entidades por página (via `limit` e `page`).

---

## 2. Estrutura de Entidades Principais

### Leads (Oportunidades)
- **Endpoint:** `/api/v4/leads`
- **Campos Chave:** `id`, `name`, `price`, `status_id`, `pipeline_id`, `responsible_user_id`, `created_at`, `updated_at`, `closed_at`.
- **Relacionamentos:** Contidos em `_embedded`: `tags`, `companies`, `contacts`, `loss_reason`.

### Contatos e Empresas
- **Endpoints:** `/api/v4/contacts`, `/api/v4/companies`
- **Campos Chave:** `id`, `name`, `first_name`, `last_name`, `responsible_user_id`.
- **Custom Fields:** Valores armazenados em `custom_fields_values` (array de objetos com `field_id` e `values`).

### 2.3 Pipelines e Estágios (Funis de Vendas)
Os termos "Pipelines" e "Funis" são usados como sinônimos na plataforma.

**Regras e Limites Técnicos:**
- **Limites:** Máximo de 50 pipelines por conta e 100 estágios por pipeline (incluindo os de sistema).
- **Estágios Obrigatórios de Sistema:** Todo pipeline possui:
    - `Leads de Entrada` (Opcional/Entrada).
    - `Closed – Won` (ID: 142).
    - `Closed – Lost` (ID: 143).
- **Permissões:** GET (Livre), POST/PATCH/DELETE (Apenas Administradores).

**Principais Endpoints de Pipelines:**
- `GET /api/v4/leads/pipelines`: Lista todos os funis.
- `GET /api/v4/leads/pipelines/{id}`: Detalhes de um funil específico.
- `POST /api/v4/leads/pipelines`: Cria novos funis (aceita array).
- `PATCH /api/v4/leads/pipelines/{id}`: Edita propriedades (`name`, `sort`, `is_main`).
- `DELETE /api/v4/leads/pipelines/{id}`: Remove funil (não pode conter leads ou ser o último).

**Principais Endpoints de Estágios (Statuses):**
- `GET /api/v4/leads/pipelines/{pipeline_id}/statuses`: Lista estágios de um funil.
- `POST /api/v4/leads/pipelines/{pipeline_id}/statuses`: Adiciona estágios (definir `name`, `color`, `sort`).
- `PATCH /api/v4/leads/pipelines/{p_id}/statuses/{id}`: Atualiza um estágio.
- `DELETE /api/v4/leads/pipelines/{p_id}/statuses/{id}`: Remove um estágio (leads órfãos vão para o 1º estágio do funil).

**Campos Relevantes:**
- `is_main`: Booleano indicando se é o funil principal.
- `is_unsorted_on`: Booleano para ativar/desativar a etapa "Leads de Entrada".
- `color`: Código hexadecimal da cor do estágio.

---

## 3. Endpoints de Atividade e Configuração

### Tarefas (Tasks)
- **Endpoint:** `/api/v4/tasks`
- **Tipos:** `follow_up`, `meeting`, `call`, etc.
- **Status:** `is_completed` (boolean).

### Notas e Histórico (Notes)
- **Endpoints:** 
  - `/api/v4/leads/notes`
  - `/api/v4/contacts/notes`
  - `/api/v4/companies/notes`
- **Uso:** Armazena logs de chamadas, chats, mudanças de sistema e anotações manuais.

### Eventos (Events)
- **Endpoint:** `/api/v4/events`
- **Uso:** Auditoria completa. Registra QUEM mudou O QUÊ e QUANDO. Essencial para calcular tempo em etapa (aging).

### Salesbots (Bots)
- **Endpoint:** `/api/v4/bots`
- **Uso:** Listagem de automações e fluxos de chatbot configurados.

---

## 4. Técnicas de Consulta (GET)

### Paginação
A API utiliza paginação baseada em `limit` e `page`:
- `limit`: Máximo de 250 itens por página.
- `page`: Número da página (começa em 1).
- **Exemplo:** `/api/v4/leads?limit=250&page=1`

### Filtragem
Filtros são passados via query params no formato `filter[campo]=valor`.
- **Por Data:** `filter[created_at][from]=1711324800` (Timestamp Unix).
- **Por Status:** `filter[status][]=142&filter[status][]=143`.
- **Por Usuário:** `filter[responsible_user_id][]=12345`.

### Inclusão de Dados Relacionados (`with`)
Para evitar múltiplas chamadas, use o parâmetro `with`:
- **Exemplo:** `/api/v4/leads?with=contacts,loss_reason`

---

## 5. Implementação de Dados (POST / PATCH)

### Criar Lead (POST)
**Endpoint:** `/api/v4/leads`
**Corpo (JSON):**
```json
[
  {
    "name": "Novo Lead Exemplo",
    "price": 1000,
    "pipeline_id": 123456,
    "status_id": 654321,
    "responsible_user_id": 999,
    "custom_fields_values": [
      {
        "field_id": 111,
        "values": [{ "value": "Valor Personalizado" }]
      }
    ]
  }
]
```

### Atualizar Lead (PATCH)
**Endpoint:** `/api/v4/leads`
**Corpo (JSON):** Deve conter o `id` do registro.
```json
[
  {
    "id": 44854417,
    "price": 2500,
    "status_id": 100100340
  }
]
```

---

## 6. Limites e Boas Práticas (Rate Limits)

- **Limite de Requisições:** Máximo de **7 requisições por segundo por IP**.
- **Batching:** 
    - Limite técnico: Até 250 itens por chamada.
    - **Recomendação Oficial:** Enviar em blocos de **50 entidades** para evitar timeouts (504 Gateway Timeout).
- **Tratamento de Erros e Bloqueios:**
  - `200 OK`: Sucesso.
  - `204 No Content`: Busca sem resultados.
  - `401 Unauthorized`: Token expirado ou inválido.
  - `429 Too Many Requests`: Limite de taxa excedido.
  - `403 Forbidden`: Bloqueio de IP por violação contínua de limites ou excesso de requisições inválidas.

---

## 7. Webhooks e Integrações

- **Limite:** Máximo de **100 webhooks** por conta.
- **Endpoint:** `/api/v4/webhooks`
- **Eventos Comuns:** `add_lead`, `update_lead`, `delete_lead`, `add_contact`, `add_company`, `update_contact`, etc.
- **Flexibilidade:** Um único webhook pode ser configurado para múltiplos eventos simultaneamente.

---

## 8. Leads de Entrada (Incoming Leads)

Esta é uma etapa especial e isolada para leads não verificados.
- **Comportamento:** Leads nesta etapa não aparecem nas listas gerais do CRM até serem "aceitos" por um usuário.
- **Criação via API:** Apenas tipos `"forms"` (formulários) e `"sip"` (chamadas) podem ser criados programaticamente.
- **Duplicidade:** O Kommo verifica automaticamente duplicatas e adiciona a tag `duplicate` se houver match.

---

## 9. Dicas para IA de Contexto

- **Mapeamento de IDs:** Sempre que ler um Lead, use o `pipelines.json` para traduzir `status_id` em um nome legível (ex: "Aguardando Atendimento").
- **Custom Fields:** Os IDs de campos personalizados variam por conta. Consulte `/api/v4/leads/custom_fields` para mapear os nomes (ex: "Ticket Médio", "Origem") aos IDs numéricos.
- **Relacionamento N para N:** Um Lead pode ter múltiplos contatos vinculados.
