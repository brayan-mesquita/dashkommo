# Fontes e campos esperados

Use este arquivo para mapear a estrutura mínima que o CRM precisa expor.

## Entidades principais

### leads
- id_lead
- data_criacao
- origem
- campanha
- responsavel
- status
- segmento

### oportunidades
- id_oportunidade
- id_conta
- data_abertura
- etapa_atual
- valor
- probabilidade
- owner
- origem
- produto
- data_fechamento_prevista
- data_fechamento_real
- motivo_perda
- status_ganho_perdido

### atividades
- id_atividade
- tipo_atividade
- data_atividade
- owner
- id_lead ou id_oportunidade
- concluida
- canal

### contas / clientes
- id_conta
- nome
- segmento
- faixa_receita
- regiao
- carteira

## Perguntas para adaptar ao CRM real

- O pipeline é baseado em leads ou oportunidades?
- O valor da venda fica em oportunidade, proposta ou pedido?
- Existe histórico de mudança de etapa?
- Existe tabela de metas por vendedor/equipe/período?
- Existe dado de atividade para medir cadência e follow-up?

## Regras de consistência

- Não somar oportunidades perdidas e ganhas no mesmo indicador de pipeline ativo.
- Não calcular taxa de conversão sem fixar numerador e denominador.
- Se houver múltiplas moedas, normalizar antes de comparar valores.
