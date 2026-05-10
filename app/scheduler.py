import schedule
import time
import subprocess
import os
from datetime import datetime

def run_sync():
    print(f"[{datetime.now()}] Iniciando sincronização com Kommo CRM...")
    try:
        # 1. Puxar dados da API
        subprocess.run([
            "python3", "kommo/agents/especialista-vendas/scripts/kommo_fetch.py", "leads", 
            "--env-file", "kommo/.env.kommo", "--all-pages", "--output", "kommo/data/leads_current.json"
        ], check=True)
        
        subprocess.run([
            "python3", "kommo/agents/especialista-vendas/scripts/kommo_fetch.py", "pipelines", 
            "--env-file", "kommo/.env.kommo", "--output", "kommo/data/pipelines_current.json"
        ], check=True)
        
        subprocess.run([
            "python3", "kommo/agents/especialista-vendas/scripts/kommo_fetch.py", "users", 
            "--env-file", "kommo/.env.kommo", "--output", "kommo/data/users_current.json"
        ], check=True)
        
        subprocess.run([
            "python3", "kommo/agents/especialista-vendas/scripts/kommo_fetch.py", "/api/v4/leads/loss_reasons", 
            "--env-file", "kommo/.env.kommo", "--output", "kommo/data/loss_reasons_current.json"
        ], check=True)

        # 2. Atualizar o Banco de Dados
        subprocess.run(["python3", "app/create_poc_db.py"], check=True)
        
        print(f"[{datetime.now()}] Sincronização concluída com sucesso!")
    except Exception as e:
        print(f"[{datetime.now()}] Erro na sincronização: {e}")

# Agendamento
schedule.every().day.at("06:00").do(run_sync)
schedule.every().day.at("12:00").do(run_sync)
schedule.every().day.at("18:00").do(run_sync)
schedule.every().day.at("00:00").do(run_sync)

if __name__ == "__main__":
    print("Serviço de agendamento iniciado (6h/12h/18h/00h)...")
    # Executa uma vez ao iniciar
    run_sync()
    while True:
        schedule.run_pending()
        time.sleep(60)
