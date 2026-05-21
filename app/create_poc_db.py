import sqlite3
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

# Configuração
DB_PATH = 'app/kommo_poc.db'
DATA_DIR = Path('app/data')

def create_schema(conn):
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pipelines (
        id INTEGER PRIMARY KEY,
        name TEXT
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS statuses (
        id INTEGER PRIMARY KEY,
        name TEXT,
        pipeline_id INTEGER
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY,
        name TEXT,
        price REAL,
        responsible_user_id INTEGER,
        status_id INTEGER,
        pipeline_id INTEGER,
        created_at TIMESTAMP,
        loss_reason_id INTEGER,
        tags TEXT
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS loss_reasons (
        id INTEGER PRIMARY KEY,
        name TEXT
    )''')
    conn.commit()

def load_data():
    conn = sqlite3.connect(DB_PATH)
    create_schema(conn)
    
    # Carregar Usuários
    with open(DATA_DIR / 'users_current.json', 'r') as f:
        users_data = json.load(f)['data']
        for u in users_data:
            conn.execute('INSERT OR REPLACE INTO users (id, name) VALUES (?, ?)', (u['id'], u['name']))
            
    # Carregar Pipelines e Statuses
    with open(DATA_DIR / 'pipelines_current.json', 'r') as f:
        pipelines_data = json.load(f)['data']
        for p in pipelines_data:
            conn.execute('INSERT OR REPLACE INTO pipelines (id, name) VALUES (?, ?)', (p['id'], p['name']))
            if '_embedded' in p and 'statuses' in p['_embedded']:
                for s in p['_embedded']['statuses']:
                    conn.execute('INSERT OR REPLACE INTO statuses (id, name, pipeline_id) VALUES (?, ?, ?)', 
                                 (s['id'], s['name'], p['id']))

    # Carregar Motivos de Perda
    with open(DATA_DIR / 'loss_reasons_current.json', 'r') as f:
        loss_data = json.load(f)
        reasons = loss_data.get('_embedded', {}).get('loss_reasons', [])
        for lr in reasons:
            conn.execute('INSERT OR REPLACE INTO loss_reasons (id, name) VALUES (?, ?)', (lr['id'], lr['name']))

    # Carregar Leads
    with open(DATA_DIR / 'leads_current.json', 'r') as f:
        leads_data = json.load(f)['data']
        active_ids = []
        for l in leads_data:
            active_ids.append(l['id'])
            created_at = datetime.fromtimestamp(l['created_at']).strftime('%Y-%m-%d %H:%M:%S')
            tags_list = [tag['name'] for tag in l.get('_embedded', {}).get('tags', [])]
            tags_str = json.dumps(tags_list)
            conn.execute('''
                INSERT OR REPLACE INTO leads (id, name, price, responsible_user_id, status_id, pipeline_id, created_at, loss_reason_id, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (l['id'], l['name'], l['price'], l['responsible_user_id'], l['status_id'], l['pipeline_id'], created_at, l.get('loss_reason_id'), tags_str))
            
        # Limpar registros obsoletos (leads excluídos no Kommo)
        if active_ids:
            placeholders = ','.join(['?'] * len(active_ids))
            conn.execute(f'DELETE FROM leads WHERE id NOT IN ({placeholders})', active_ids)

    conn.commit()
    conn.close()
    print("Banco de dados POC criado e populado com sucesso!")

if __name__ == "__main__":
    load_data()
