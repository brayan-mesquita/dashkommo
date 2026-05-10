#!/usr/bin/env python3
import datetime
import json
import os
import sys
from pathlib import Path

# Adiciona o diretório atual ao path para importações
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

try:
    from kommo_analytics.client import KommoClient
except ImportError:
    print("Erro: Não foi possível importar KommoClient. Verifique a estrutura de pastas.")
    sys.exit(1)

# Lista de recursos para backup (alias ou path bruto)
RESOURCES = [
    ("account", "account.json"),
    ("users", "users.json"),
    ("pipelines", "pipelines.json"),
    ("lead-custom-fields", "lead_custom_fields.json"),
    ("contact-custom-fields", "contact_custom_fields.json"),
    ("company-custom-fields", "company_custom_fields.json"),
    ("/api/v4/leads/loss_reasons", "loss_reasons.json"),
    ("/api/v4/bots", "salesbots.json"),
    ("/api/v4/webhooks", "webhooks.json"),
    ("catalogs", "catalogs.json"),
    ("leads", "leads.json"),
    ("contacts", "contacts.json"),
    ("companies", "companies.json"),
    ("tasks", "tasks.json"),
    ("lead-notes", "lead_notes.json"),
    ("contact-notes", "contact_notes.json"),
    ("company-notes", "company_notes.json"),
]

def main():
    # Carrega cliente do ambiente (.env.kommo deve estar acessível)
    try:
        client = KommoClient.from_env(search_from=str(CURRENT_DIR))
    except Exception as e:
        print(f"Erro ao inicializar cliente: {e}")
        sys.exit(1)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Salva na pasta data/backups/ no root do projeto
    project_root = CURRENT_DIR.parent.parent.parent
    backup_dir = project_root / "data" / "backups" / f"backup_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"====================================================")
    print(f"INICIANDO BACKUP COMPLETO KOMMO")
    print(f"Data/Hora: {datetime.datetime.now().isoformat()}")
    print(f"Diretório: {backup_dir}")
    print(f"====================================================\n")
    
    summary = {
        "timestamp": timestamp,
        "backup_directory": str(backup_dir),
        "results": {}
    }
    
    for resource, filename in RESOURCES:
        print(f"[*] Extraindo: {resource}...", end=" ", flush=True)
        try:
            # Alguns recursos não são paginados ou o client já trata
            # Mas para garantir backup total de leads/contatos, usamos all_pages
            
            # Nota: para notes, o volume pode ser alto. 
            # O fetch_resource com all_pages=True buscará tudo respeitando o limite do client.
            
            data = client.fetch_resource(
                resource, 
                all_pages=True, 
                max_pages=2000, # Limite alto para garantir extração completa
                limit=250
            )
            
            output_path = backup_dir / filename
            client.dump_json(data, output=str(output_path))
            
            # Conta registros se for estrutura paginada (data['records']) ou dict simples
            if isinstance(data, dict):
                count = data.get("records", "1 (single)")
            else:
                count = "1"
                
            summary["results"][resource] = {
                "status": "success",
                "count": count,
                "file": filename
            }
            print(f"OK ({count} registros)")
            
        except (Exception, SystemExit) as e:
            msg = str(e) if str(e) else "Erro desconhecido (provavelmente resposta vazia ou 404)"
            print(f"ERRO: {msg}")
            summary["results"][resource] = {
                "status": "error",
                "message": msg
            }

    # Salva o resumo final
    with open(backup_dir / "backup_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        
    print(f"\n====================================================")
    print(f"BACKUP CONCLUÍDO COM SUCESSO!")
    print(f"Localização: {backup_dir}")
    print(f"====================================================")

if __name__ == "__main__":
    main()
