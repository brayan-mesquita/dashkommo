import os
import json
from datetime import datetime, timezone, timedelta
from collections import defaultdict, Counter
from pathlib import Path
import sys

# Adiciona o diretório do script ao path para importar kommo_analytics
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from kommo_analytics.client import KommoClient

def get_month_range():
    # Data atual baseada no contexto do sistema: 18 de maio de 2026
    now = datetime(2026, 5, 18, hour=23, minute=59, second=59, tzinfo=timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start_of_month, now

def format_currency(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def generate_reports():
    client = KommoClient.from_env(search_from=str(CURRENT_DIR))
    start_of_month, end_of_month = get_month_range()
    from_ts = int(start_of_month.timestamp())
    to_ts = int(end_of_month.timestamp())

    print(f"Extraindo dados de {start_of_month.strftime('%d/%m/%Y')} até {end_of_month.strftime('%d/%m/%Y')}...")

    # Busca usuários
    print("Buscando usuários...")
    users_data = client.fetch_resource("users", all_pages=True)
    users = users_data.get("data", [])
    users_by_id = {u["id"]: u["name"] for u in users}

    # Busca pipelines para nomes de status e tipos
    print("Buscando pipelines e status...")
    pipelines_data = client.fetch_resource("pipelines", all_pages=True)
    pipelines = pipelines_data.get("data", [])
    status_names = {}
    won_ids = set()
    lost_ids = set()
    for pipe in pipelines:
        for status in pipe.get("_embedded", {}).get("statuses", []):
            status_names[status["id"]] = status["name"]
            if status.get("type") == 3: won_ids.add(status["id"])
            elif status.get("type") == 2: lost_ids.add(status["id"])

    # Busca leads criados no mês
    print("Buscando leads criados no mês...")
    created_leads = client.fetch_resource("leads", params={
        "filter[created_at][from]": from_ts,
        "filter[created_at][to]": to_ts,
        "with": "tags"
    }, all_pages=True).get("data", [])

    # Busca leads ganhos no mês
    print("Buscando leads ganhos no mês...")
    # Filtramos por closed_at para garantir que foram fechados no mês
    won_leads = client.fetch_resource("leads", params={
        "filter[closed_at][from]": from_ts,
        "filter[closed_at][to]": to_ts,
        "with": "tags"
    }, all_pages=True).get("data", [])
    
    # Filtro manual para garantir status de ganho
    won_leads = [l for l in won_leads if l.get("status_id") in won_ids]

    # Busca leads perdidos no mês
    print("Buscando leads perdidos no mês...")
    lost_leads = client.fetch_resource("leads", params={
        "filter[closed_at][from]": from_ts,
        "filter[closed_at][to]": to_ts,
        "with": "loss_reason,tags"
    }, all_pages=True).get("data", [])
    
    # Filtro manual para garantir status de perda
    lost_leads = [l for l in lost_leads if l.get("status_id") in lost_ids]

    # Leads sob responsabilidade (Ativos)
    print("Buscando leads ativos...")
    active_leads = client.fetch_resource("leads", params={
        "with": "tags"
    }, all_pages=True).get("data", [])
    active_leads = [l for l in active_leads if l.get("status_id") not in (won_ids | lost_ids)]

    # Tarefas
    print("Buscando tarefas abertas...")
    open_tasks = client.fetch_resource("tasks", params={"filter[is_completed]": 0}, all_pages=True).get("data", [])
    
    # Eventos para tarefas concluídas no mês
    print("Buscando tarefas concluídas no mês via eventos...")
    events = client.fetch_resource("events", params={
        "filter[created_at][from]": from_ts,
        "filter[type]": "task_completed"
    }, all_pages=True).get("data", [])
    
    # Processamento por vendedor
    seller_data = defaultdict(lambda: {
        "name": "",
        "won_value": 0,
        "won_count": 0,
        "lost_count": 0,
        "active_count": 0,
        "loss_reasons": Counter(),
        "tasks_pending": 0,
        "tasks_overdue": 0,
        "tasks_completed": 0,
        "won_tags": Counter(),
        "daily_volume": Counter()
    })

    for u in users:
        seller_data[u["id"]]["name"] = u["name"]

    for l in won_leads:
        uid = l.get("responsible_user_id")
        seller_data[uid]["won_value"] += (l.get("price") or 0)
        seller_data[uid]["won_count"] += 1
        for tag in l.get("_embedded", {}).get("tags", []):
            seller_data[uid]["won_tags"][tag["name"]] += 1

    for l in lost_leads:
        uid = l.get("responsible_user_id")
        seller_data[uid]["lost_count"] += 1
        reasons = l.get("_embedded", {}).get("loss_reason", [])
        if reasons:
            for r in reasons:
                seller_data[uid]["loss_reasons"][r.get("name") or "Desconhecido"] += 1
        else:
            seller_data[uid]["loss_reasons"]["Não informado"] += 1

    for l in active_leads:
        uid = l.get("responsible_user_id")
        seller_data[uid]["active_count"] += 1

    # Volume diário baseado na criação de leads no mês
    for l in created_leads:
        uid = l.get("responsible_user_id")
        dt_str = datetime.fromtimestamp(l["created_at"], tz=timezone.utc).strftime("%Y-%m-%d")
        seller_data[uid]["daily_volume"][dt_str] += 1

    now_ts = int(end_of_month.timestamp())
    for t in open_tasks:
        uid = t.get("responsible_user_id")
        seller_data[uid]["tasks_pending"] += 1
        if t.get("complete_till") and t["complete_till"] < now_ts:
            seller_data[uid]["tasks_overdue"] += 1

    for e in events:
        uid = e.get("created_by")
        if uid in seller_data:
            seller_data[uid]["tasks_completed"] += 1

    # Geração dos arquivos Markdown
    output_dir = Path("Base_de_Conhecimento/Relatorios_de_Vendas/")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Relatório Geral também
    total_won_value = 0
    total_won_count = 0
    total_lost_count = 0
    total_active_count = 0
    
    vendedores_ativos = []

    for uid, data in seller_data.items():
        if data["won_count"] == 0 and data["lost_count"] == 0 and data["active_count"] == 0 and sum(data["daily_volume"].values()) == 0:
            continue
        
        name = data["name"]
        vendedores_ativos.append(name)
        filename = f"Desempenho_{name.replace(' ', '_')}.md"
        filepath = output_dir / filename

        total_won_value += data["won_value"]
        total_won_count += data["won_count"]
        total_lost_count += data["lost_count"]
        total_active_count += data["active_count"]

        # Gráfico diário usando Mermaid
        days_keys = sorted(data["daily_volume"].keys())
        chart_section = ""
        if days_keys:
            x_labels = ", ".join([f'"{d[-2:]}"' for d in days_keys])
            y_values = ", ".join([str(data["daily_volume"][d]) for d in days_keys])
            chart_section = f"""```mermaid
xychart-beta
    title "Volume de Leads Criados por Dia (Maio)"
    x-axis [{x_labels}]
    y-axis "Qtd Leads"
    bar [{y_values}]
```"""

        content = f"""# Relatório de Desempenho - {name}
**Data de Geração:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
**Período:** {start_of_month.strftime('%d/%m/%Y')} a {end_of_month.strftime('%d/%m/%Y')}

## 💰 Resultados de Vendas
- **Total Vendido:** {format_currency(data['won_value'])}
- **Leads Ganhos:** {data['won_count']}
- **Leads Perdidos:** {data['lost_count']}
- **Taxa de Conversão (Win Rate):** {(data['won_count'] / max(1, data['won_count'] + data['lost_count']) * 100):.1f}%

## 📋 Gestão de Leads
- **Leads sob Responsabilidade (Atuais):** {data['active_count']}
- **Total de Leads Criados no Mês:** {sum(data['daily_volume'].values())}

## ❌ Análise de Perdas
**Motivos das oportunidades perdidas:**
"""
        if data["loss_reasons"]:
            for reason, count in data["loss_reasons"].most_common():
                content += f"- {reason}: {count}\n"
        else:
            content += "- Nenhum motivo registrado no período.\n"

        content += f"""
## 🛠️ Atividades e Tarefas
- ✅ **Concluídas (no mês):** {data['tasks_completed']}
- ⏳ **Pendentes:** {data['tasks_pending']}
- 🚨 **Atrasadas:** {data['tasks_overdue']}

## 🏷️ Tags nos Ganhos
**Principais tags nos leads convertidos:**
"""
        if data["won_tags"]:
            for tag, count in data["won_tags"].most_common(5):
                content += f"- {tag}: {count}\n"
        else:
            content += "- Nenhuma tag identificada nos ganhos.\n"

        content += f"""
## 📈 Volume de Leads Criados por Dia
{chart_section}

---
[[Dashboard_Inicial|⬅️ Voltar ao Dashboard]]
"""
        filepath.write_text(content, encoding="utf-8")
        print(f"Relatório gerado: {filepath}")

    # Relatório Geral Unidade
    geral_path = output_dir / "Desempenho_Geral_Unidade.md"
    geral_content = f"""# Desempenho Geral da Unidade
**Data de Geração:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
**Período:** {start_of_month.strftime('%d/%m/%Y')} a {end_of_month.strftime('%d/%m/%Y')}

## 📊 Consolidado
- **Total Vendido:** {format_currency(total_won_value)}
- **Total de Leads Ganhos:** {total_won_count}
- **Total de Leads Perdidos:** {total_lost_count}
- **Total de Leads Ativos:** {total_active_count}
- **Win Rate Geral:** {(total_won_count / max(1, total_won_count + total_lost_count()) * 100 if total_won_count+total_lost_count > 0 else 0):.1f}%

## 👥 Vendedores Analisados
{chr(10).join([f'- [[Desempenho_{n.replace(" ", "_")}|{n}]]' for n in sorted(vendedores_ativos)])}

---
[[Dashboard_Inicial|⬅️ Voltar ao Dashboard]]
"""
    # Fix potential error in general report win rate calculation
    win_rate_val = (total_won_count / (total_won_count + total_lost_count) * 100) if (total_won_count + total_lost_count) > 0 else 0
    geral_content = geral_content.replace("{(total_won_count / max(1, total_won_count + total_lost_count()) * 100 if total_won_count+total_lost_count > 0 else 0):.1f}%", f"{win_rate_val:.1f}%")
    
    geral_path.write_text(geral_content, encoding="utf-8")
    print(f"Relatório geral gerado: {geral_path}")

if __name__ == "__main__":
    try:
        generate_reports()
    except Exception as e:
        print(f"Erro ao gerar relatórios: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
