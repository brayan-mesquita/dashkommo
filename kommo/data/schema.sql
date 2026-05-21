-- Schema SQL para PostgreSQL (Metabase)
-- Projeto: Integração Kommo CRM -> Metabase

-- Tabela de Usuários (Vendedores)
CREATE TABLE IF NOT EXISTS kommo_users (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Funis (Pipelines)
CREATE TABLE IF NOT EXISTS kommo_pipelines (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    sort INT,
    is_main BOOLEAN,
    is_archive BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Status de Funil
CREATE TABLE IF NOT EXISTS kommo_statuses (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    pipeline_id BIGINT REFERENCES kommo_pipelines(id),
    sort INT,
    color TEXT,
    type INT, -- 0: standard, 1: initial, 142: won, 143: lost
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Motivos de Perda
CREATE TABLE IF NOT EXISTS kommo_loss_reasons (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    sort INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Negócios (Leads)
CREATE TABLE IF NOT EXISTS kommo_leads (
    id BIGINT PRIMARY KEY,
    name TEXT,
    price NUMERIC(15, 2),
    responsible_user_id BIGINT REFERENCES kommo_users(id),
    status_id BIGINT REFERENCES kommo_statuses(id),
    pipeline_id BIGINT REFERENCES kommo_pipelines(id),
    loss_reason_id BIGINT REFERENCES kommo_loss_reasons(id),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    closed_at TIMESTAMP,
    closest_task_at TIMESTAMP,
    custom_fields JSONB, -- Armazena campos customizados como JSON para flexibilidade no Metabase
    tags JSONB,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Tabela de Tarefas
CREATE TABLE IF NOT EXISTS kommo_tasks (
    id BIGINT PRIMARY KEY,
    responsible_user_id BIGINT REFERENCES kommo_users(id),
    entity_id BIGINT, -- ID do Lead/Contato/Empresa
    entity_type TEXT, -- 'leads', 'contacts', 'companies'
    task_type_id INT,
    text TEXT,
    is_completed BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    complete_till TIMESTAMP,
    completed_at TIMESTAMP
);
