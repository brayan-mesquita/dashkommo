# Dockerfile otimizado para Easypanel
FROM python:3.12-slim

WORKDIR /app

# Instalar dependências de sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar apenas os requisitos primeiro (aproveita cache do Docker)
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o projeto para dentro do container
COPY . .

# Garantir que as pastas de dados existam
RUN mkdir -p kommo/data

# Expor a porta do Streamlit
EXPOSE 8501

# Comando para rodar o scheduler e o streamlit
# O scheduler precisa de acesso ao diretório raiz para rodar os scripts da pasta kommo/
CMD python3 app/scheduler.py & streamlit run app/streamlit_app.py --server.port=8501 --server.address=0.0.0.0
