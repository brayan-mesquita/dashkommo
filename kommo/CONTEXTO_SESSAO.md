# 🧠 Contexto do Projeto: CRM Febracis Porto Velho

Este arquivo serve como ponte de contexto para futuras sessoes.

## 🎯 Objetivo do Agente
Transformar dados brutos do Kommo CRM em inteligencia de vendas seguindo a metodologia de Alta Performance da Febracis.

## 🛠️ O que ja foi construido:
1. **Estrutura de Habilidades:** Pasta `agents/especialista-vendas/` com scripts de fetch e report.
2. **Seguranca:** O agente esta configurado para NUNCA realizar alteracoes no CRM (Apenas GET).
3. **Base de Conhecimento (Obsidian):** Pasta `Base_de_Conhecimento/` organizada para visualização.
   - **Relatorios Individuais:** Movidos para `Base_de_Conhecimento/Relatorios_de_Vendas/`.
   - **Relatorio Geral:** `Base_de_Conhecimento/Relatorios_de_Vendas/Desempenho_Geral_Unidade.md`.
   - **Dashboard Central:** `Base_de_Conhecimento/Dashboard_Inicial.md` para navegação no Obsidian.
5. **Apresentacao Visual:** Arquivo `Desempenho_Geral.excalidraw` com graficos e indicadores.

## 🔑 Credenciais e Acesso
- Armazenadas no arquivo `.env.kommo` (Subdominio e Access Token).
- Dominio: `crmfbcpvh.kommo.com`.

## 📉 Metricas de Ouro Definidas:
- **Win Rate:** Focada em decisoes (Ganhos vs Perdidos).
- **Saude do Funil:** Zero tarefas atrasadas.
- **Ticket Medio:** Identificacao de vendedores de volume vs vendedores de valor (ex: Camila).

## 🚀 Proximos Passos Sugeridos:
- Realizar auditoria nos leads perdidos (351 leads da Camila).
- Criar automacoes de busca para identificar leads parados ha mais de 48h.
- Analisar a conversao por Tag de Origem para medir ROI de marketing.

---
*Ultima atualizacao: 27 de Abril de 2026.*
