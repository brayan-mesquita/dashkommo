# Projeto CRM Kommo - Consultoria Febracis

Este projeto contém a estrutura para um **Agente Especialista em Vendas CRM**, focado na metodologia Febracis e integração com o CRM Kommo.

## Estrutura de Pastas
- `agents/especialista-vendas/`: Definição do agente, habilidades e instruções.
  - `SKILL.md`: Guia de comportamento e metas do agente.
  - `scripts/`: Ferramentas Python para interagir com a API do Kommo.
  - `references/`: Documentação da API e metodologia Febracis.
  - `prompts/`: Modelos de análise de dados e performance.

## Configuração Inicial

### 1. Variáveis de Ambiente
Crie ou edite o arquivo `.env.kommo` na raiz do projeto:
```env
KOMMO_SUBDOMAIN=seu_subdominio
KOMMO_ACCESS_TOKEN=seu_token_de_acesso
```

### 2. Dependências
Certifique-se de ter o Python 3 instalado. As dependências básicas são `requests` e `python-dotenv`.
```bash
pip install requests python-dotenv
```

## Como Usar o Agente

O agente pode realizar as seguintes tarefas:

### Gerar Relatório de Performance
Para extrair um snapshot dos últimos 30 dias e gerar um relatório de decisão:
```bash
python3 agents/especialista-vendas/scripts/kommo_report.py report --env-file .env.kommo --days 30
```

### Verificar Saúde do Funil
Listar leads parados ou sem tarefas (Seguindo a disciplina Febracis):
```bash
python3 agents/especialista-vendas/scripts/kommo_fetch.py tasks --env-file .env.kommo --param filter[is_completed]=0
```

### Consultar Métodos de Venda
Leia os arquivos em `agents/especialista-vendas/references/` para entender como aplicar o Método CIS e os KPIs de Alta Performance no Kommo.

## 💾 Backup de Dados
Para realizar um backup completo de todas as informações do Kommo (Funis, Leads, Contatos, Bots, etc.), utilize o script:
```bash
python3 agents/especialista-vendas/scripts/kommo_backup.py
```
Os dados serão salvos em `data/backups/backup_YYYYMMDD_HHMMSS/` no formato JSON. Isso garante a segurança da organização dos funis e informações de vendas em caso de perda de acesso à conta.

## Perfil e Segurança do Agente
O agente é um especialista de **apenas leitura (Read-Only)**. Ele foi configurado para **jamais realizar alterações** no CRM Kommo. Seu papel é buscar dados, analisar padrões e gerar relatórios de alta performance.

Para garantir que o agente entenda todas as possibilidades da API, ele deve consultar frequentemente o guia em `agents/especialista-vendas/references/api-exploration.md` e a documentação oficial do Kommo.

