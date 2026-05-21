# Documentação Oficial e Exploração da API Kommo

## Link Oficial
- **Developer Center:** [https://www.kommo.com/developers/api/v4/](https://www.kommo.com/developers/api/v4/)

## Instruções para o Agente
1. **Sempre Consultar:** Antes de realizar extrações complexas (filtros aninhados, busca por campos personalizados específicos ou eventos), verifique a sintaxe correta na documentação oficial.
2. **Foco em GET:** Foque exclusivamente nos métodos `GET` para todos os recursos (Leads, Contacts, Companies, Tasks, Events, Pipelines, Users).
3. **Exploração de "Voltas" da API:**
   - Use a documentação para entender como os `custom_fields` são estruturados e como filtrá-los.
   - Verifique como as `notes` e `tasks` se relacionam com os leads para reconstruir a jornada do cliente sem alterar o CRM.
   - Explore os endpoints de `events` para entender o histórico de mudanças de status e quem realizou cada ação.

## Restrição Absoluta
**PROIBIDO:** O uso de métodos `POST`, `PATCH`, `PUT` ou `DELETE`. O agente deve atuar como uma camada de inteligência e auditoria, sem capacidade de escrita para preservar a integridade dos dados operacionais da consultoria.
