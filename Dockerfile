# Dockerfile otimizado para Easypanel (Raiz do Projeto)
FROM python:3.12-slim

WORKDIR /app

# Instalar dependências de sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar apenas os requisitos primeiro
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o projeto
COPY . .

# Criar diretório para o banco se não existir
RUN mkdir -p app/data

# Expor a porta do Streamlit
EXPOSE 8501

# Comando para rodar o scheduler e o streamlit
# Usando formato JSON para melhor tratamento de sinais OS
CMD ["sh", "-c", "python3 app/scheduler.py & streamlit run app/streamlit_app.py --server.port=8501 --server.address=0.0.0.0"]
