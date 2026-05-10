# 📝 Mandatos do Gemini (Projeto Kommo CRM)

Este arquivo define as regras de operação para o agente Gemini neste workspace.

## 📂 Estrutura de Arquivos e Organização
- **Base de Conhecimento:** Todos os relatórios de performance, análises de vendedores e insights em Markdown (.md) DEVEM ser salvos no diretório `Base_de_Conhecimento/Relatorios_de_Vendas/`.
- **Nomenclatura:** Continue seguindo o padrão `Desempenho_[Nome_Vendedor].md` para relatórios individuais e `Desempenho_Geral_Unidade.md` para o consolidado.
- **Indexação:** Sempre que um novo relatório for criado, o arquivo `Base_de_Conhecimento/Dashboard_Inicial.md` deve ser atualizado com o novo link, se necessário.

## 🛠️ Uso de Ferramentas
- Use os scripts em `agents/especialista-vendas/scripts/` para coleta de dados.
- O output final para o usuário deve ser focado na visualização via **Obsidian**.

## 🛡️ Segurança
- Jamais realize operações de escrita (POST/PATCH/DELETE) no CRM Kommo.
- Não exponha tokens do arquivo `.env.kommo`.
