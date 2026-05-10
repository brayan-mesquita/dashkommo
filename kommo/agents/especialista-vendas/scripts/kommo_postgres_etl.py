#!/usr/bin/env python3
import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert

# Carregar variáveis de ambiente (simulado, o usuário fornecerá via .env.kommo)
# KOMMO_SUBDOMAIN, KOMMO_ACCESS_TOKEN
# PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DB

class KommoPostgresETL:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)

    def format_timestamp(self, ts: int) -> datetime:
        if ts:
            return datetime.fromtimestamp(ts)
        return None

    def process_users(self, data: List[Dict]):
        df = pd.DataFrame(data)
        # Selecionar e renomear colunas
        users = df[['id', 'name', 'email']].copy()
        users['updated_at'] = datetime.now()
        
        with self.engine.connect() as conn:
            for idx, row in users.iterrows():
                stmt = insert(text("kommo_users")).values(row.to_dict())
                stmt = stmt.on_conflict_do_update(
                    index_elements=['id'],
                    set_={k: v for k, v in row.to_dict().items() if k != 'id'}
                )
                conn.execute(stmt)
            conn.commit()
        print(f"Processados {len(users)} usuários.")

    def process_pipelines(self, data: List[Dict]):
        pipelines_list = []
        statuses_list = []
        
        for p in data:
            pipelines_list.append({
                'id': p['id'],
                'name': p['name'],
                'sort': p.get('sort'),
                'is_main': p.get('is_main'),
                'is_archive': p.get('is_archive', False)
            })
            
            if '_embedded' in p and 'statuses' in p['_embedded']:
                for s in p['_embedded']['statuses']:
                    statuses_list.append({
                        'id': s['id'],
                        'name': s['name'],
                        'pipeline_id': p['id'],
                        'sort': s.get('sort'),
                        'color': s.get('color'),
                        'type': s.get('type')
                    })
        
        # Upsert Pipelines
        df_p = pd.DataFrame(pipelines_list)
        # ... lógica de upsert similar ...
        print(f"Processados {len(df_p)} funis e {len(statuses_list)} status.")

    def process_leads(self, data: List[Dict]):
        processed_leads = []
        for l in data:
            processed_leads.append({
                'id': l['id'],
                'name': l.get('name'),
                'price': l.get('price'),
                'responsible_user_id': l.get('responsible_user_id'),
                'status_id': l.get('status_id'),
                'pipeline_id': l.get('pipeline_id'),
                'loss_reason_id': l.get('loss_reason_id'),
                'created_at': self.format_timestamp(l.get('created_at')),
                'updated_at': self.format_timestamp(l.get('updated_at')),
                'closed_at': self.format_timestamp(l.get('closed_at')),
                'closest_task_at': self.format_timestamp(l.get('closest_task_at')),
                'custom_fields': json.dumps(l.get('custom_fields_values', [])),
                'tags': json.dumps(l.get('_embedded', {}).get('tags', []))
            })
        
        df_l = pd.DataFrame(processed_leads)
        # Carga no Postgres
        # df_l.to_sql('kommo_leads', self.engine, if_exists='append', index=False)
        print(f"Processados {len(df_l)} leads.")

def main():
    # Exemplo de uso com dados locais
    # etl = KommoPostgresETL("postgresql://user:pass@host:port/db")
    # ... ler JSONs e chamar process_xxx ...
    print("Script de ETL inicializado. Aguardando credenciais para execução real.")

if __name__ == "__main__":
    main()
