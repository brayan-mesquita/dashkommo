import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from collections import Counter
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from datetime import datetime, timedelta
st.set_page_config(page_title="Inteligência de Vendas - Febracis", layout="wide")

# --- AUTHENTICATION ---
# Carregar credenciais (em produção, você pode colocar isso no secrets do Streamlit ou Easypanel)
# Por enquanto, vou criar um usuário padrão 'admin' com senha 'febracis2026'
# Em um cenário real, as senhas devem ser hashes.
credentials = {
    "usernames": {
        "Febracis": {
            "name": "Gestor Febracis",
            "password": "tempoderquemage" 
        }
    }
}

# Aqui simulamos o hashing para o stauth funcionar (v0.4.x exige o dicionário inteiro)
stauth.Hasher.hash_passwords(credentials)
# A função acima modifica o dicionário 'credentials' in-place, adicionando os hashes.

authenticator = stauth.Authenticate(
    credentials,
    "kommo_dashboard_v2",
    "auth_cookie",
    cookie_expiry_days=30
)

# Realizar login (na v0.4.x o método não retorna mais a tupla diretamente)
authenticator.login(location='main')

if st.session_state["authentication_status"] == False:
    st.error('Usuário ou senha incorretos')
elif st.session_state["authentication_status"] == None:
    st.warning('Por favor, faça login para acessar os dados sensíveis')
elif st.session_state["authentication_status"]:
    # --- DASHBOARD CONTENT ---
    name = st.session_state["name"]
    st.sidebar.title(f"Bem-vindo, {name}")
    authenticator.logout('Logout', 'sidebar')

    # Função para formatação de moeda brasileira
    def format_currency(value):
        if pd.isna(value) or value == 0: return "R$ 0,00"
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def get_data(query):
        conn = sqlite3.connect('app/kommo_poc.db')
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    st.title("📊 Inteligência de Vendas Kommo")
    st.markdown("Visão consolidada de alta performance e análise de conversão.")

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Controle de Dados")
    if st.sidebar.button("🔄 Sincronizar Dados Agora"):
        with st.sidebar.status("Buscando dados no Kommo..."):
            try:
                import subprocess
                # Chama o scheduler no modo 'uma única vez'
                result = subprocess.run(["python3", "app/scheduler.py", "--once"], capture_output=True, text=True)
                if result.returncode == 0:
                    st.sidebar.success("Sincronização concluída!")
                    st.rerun()
                else:
                    st.sidebar.error(f"Erro na sincronização: {result.stderr}")
            except Exception as e:
                st.sidebar.error(f"Falha ao disparar script: {e}")

    st.sidebar.divider()
    st.sidebar.header("Filtros de Visão")

    # Filtro de Funil (com opção de TODOS)
    pipelines_df = get_data("SELECT * FROM pipelines")
    pipeline_options = ["Todos os Funis"] + list(pipelines_df['name'])
    selected_pipeline = st.sidebar.selectbox("Selecione o Funil", pipeline_options)

    # Filtro de Vendedor
    users_df = get_data("SELECT * FROM users")
    user_options = ["Todos os Vendedores"] + list(users_df['name'])
    selected_user = st.sidebar.selectbox("Selecione o Vendedor", user_options)

    # Filtro de Data Rápido
    st.sidebar.subheader("Período de Criação")
    date_preset = st.sidebar.selectbox(
        "Atalho de Data",
        ["Todo o Período", "Este Mês", "Mês Anterior", "Últimos 7 Dias", "Personalizado"]
    )

    hoje = datetime.now().date()
    db_min_date = pd.to_datetime(get_data("SELECT MIN(created_at) FROM leads").iloc[0,0]).date()
    db_max_date = pd.to_datetime(get_data("SELECT MAX(created_at) FROM leads").iloc[0,0]).date()

    if date_preset == "Todo o Período":
        start_date, end_date = db_min_date, db_max_date
    elif date_preset == "Este Mês":
        start_date = hoje.replace(day=1)
        end_date = hoje
    elif date_preset == "Mês Anterior":
        end_date = hoje.replace(day=1) - timedelta(days=1)
        start_date = end_date.replace(day=1)
    elif date_preset == "Últimos 7 Dias":
        start_date = hoje - timedelta(days=7)
        end_date = hoje
    else:
        start_date = st.sidebar.date_input("Data Inicial", db_min_date, format="DD/MM/YYYY")
        end_date = st.sidebar.date_input("Data Final", db_max_date, format="DD/MM/YYYY")

    # --- DATA LOADING ---
    where_conditions = [f"DATE(l.created_at) BETWEEN '{start_date}' AND '{end_date}'"]
    
    if selected_pipeline != "Todos os Funis":
        pipeline_id = pipelines_df[pipelines_df['name'] == selected_pipeline]['id'].values[0]
        where_conditions.append(f"l.pipeline_id = {pipeline_id}")
        
    if selected_user != "Todos os Vendedores":
        user_id = users_df[users_df['name'] == selected_user]['id'].values[0]
        where_conditions.append(f"l.responsible_user_id = {user_id}")
        
    where_clause = "WHERE " + " AND ".join(where_conditions)

    leads_query = f"""
        SELECT l.*, u.name as user_name, s.name as status_name, lr.name as loss_reason_name, p.name as pipeline_name
        FROM leads l
        JOIN users u ON l.responsible_user_id = u.id
        JOIN statuses s ON l.status_id = s.id
        JOIN pipelines p ON l.pipeline_id = p.id
        LEFT JOIN loss_reasons lr ON l.loss_reason_id = lr.id
        {where_clause}
    """
    df = get_data(leads_query)

    # --- KEY METRICS ---
    df_ganhos = df[df['status_name'].str.contains('Ganho|Won', case=False)].copy()

    st.subheader("📌 Indicadores de Performance")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total de Leads", f"{len(df):,}".replace(",", "."))
    m2.metric("VGV Potencial", format_currency(df['price'].sum()))
    m3.metric("Faturamento Real", format_currency(df_ganhos['price'].sum()))
    m4.metric("Taxa de Conversão", f"{(len(df_ganhos)/len(df)*100 if len(df)>0 else 0):.1f}%")
    
    ticket_medio = df_ganhos['price'].sum() / len(df_ganhos) if len(df_ganhos) > 0 else 0
    m5.metric("Ticket Médio", format_currency(ticket_medio))

    # --- ROW 1: FUNNEL & VENDOR ---
    st.divider()
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Funil de Vendas (Volume por Etapa)")
        status_counts = df['status_name'].value_counts().reset_index()
        status_counts.columns = ['Etapa', 'Quantidade']
        fig_funnel = px.funnel(status_counts.head(15), x='Quantidade', y='Etapa', color='Etapa')
        fig_funnel.update_layout(showlegend=False)
        st.plotly_chart(fig_funnel, use_container_width=True)

    with c2:
        st.subheader("Faturamento Real por Vendedor")
        user_won_vgv = df_ganhos.groupby('user_name')['price'].sum().sort_values(ascending=False).reset_index()
        user_won_vgv['Valor_Formatado'] = user_won_vgv['price'].apply(format_currency)
        fig_user = px.bar(user_won_vgv, x='user_name', y='price', 
                          labels={'price': 'Faturamento (R$)', 'user_name': 'Vendedor'}, 
                          color='user_name',
                          hover_data={'Valor_Formatado': True, 'price': False})
        fig_user.update_layout(showlegend=False)
        st.plotly_chart(fig_user, use_container_width=True)

    # --- ROW 2: PIPELINES COMPARISON ---
    if selected_pipeline == "Todos os Funis":
        st.divider()
        st.subheader("Comparativo entre Funis")
        pipe_comp = df.groupby('pipeline_name').agg({
            'id': 'count',
            'price': 'sum'
        }).reset_index()
        pipe_comp.columns = ['Funil', 'Qtd Leads', 'VGV Potencial']
        
        col_a, col_b = st.columns(2)
        with col_a:
            fig_pipe_leads = px.pie(pipe_comp, values='Qtd Leads', names='Funil', title="Distribuição de Leads")
            st.plotly_chart(fig_pipe_leads, use_container_width=True)
        with col_b:
            fig_pipe_vgv = px.pie(pipe_comp, values='VGV Potencial', names='Funil', title="Distribuição de VGV Potencial")
            st.plotly_chart(fig_pipe_vgv, use_container_width=True)

    # --- ROW 3: LOSS & TIMELINE ---
    st.divider()
    c3, c4 = st.columns(2)

    with c3:
        st.subheader("Motivos de Perda")
        loss_df = df[df['loss_reason_name'].notna()]
        if not loss_df.empty:
            loss_counts = loss_df['loss_reason_name'].value_counts().reset_index()
            fig_loss = px.pie(loss_counts, values='count', names='loss_reason_name', hole=0.4)
            st.plotly_chart(fig_loss, use_container_width=True)
        else: st.write("Sem dados de perda.")

    with c4:
        st.subheader("Entrada de Leads por Dia")
        df_temp = df.copy()
        df_temp['created_at'] = pd.to_datetime(df_temp['created_at'])
        daily_leads = df_temp.groupby(df_temp['created_at'].dt.date).size().reset_index(name='leads')
        daily_leads['Data'] = daily_leads['created_at'].apply(lambda x: x.strftime('%d/%m/%Y'))
        fig_line = px.line(daily_leads, x='created_at', y='leads', markers=True, 
                           hover_data={'Data': True, 'created_at': False})
        st.plotly_chart(fig_line, use_container_width=True)

    # --- ROW 4: TAGS ---
    st.divider()
    st.subheader("🏷️ Inteligência de Tags (O que converte)")
    t1, t2 = st.columns(2)

    def get_top_tags(dataframe):
        all_tags = []
        for t_str in dataframe['tags'].dropna():
            try:
                tags = json.loads(t_str)
                all_tags.extend(tags)
            except: continue
        return Counter(all_tags).most_common(10)

    with t1:
        st.markdown("**Principais Tags em Vendas Fechadas**")
        top_ganhos = get_top_tags(df_ganhos)
        if top_ganhos:
            tag_df = pd.DataFrame(top_ganhos, columns=['Tag', 'Qtd'])
            st.plotly_chart(px.bar(tag_df, x='Qtd', y='Tag', orientation='h', color='Tag').update_layout(showlegend=False), use_container_width=True)
        else: st.info("Sem tags.")

    with t2:
        st.markdown("**Glossário Rápido**")
        st.info("""
        - **VGV Potencial:** Tudo que está aberto ou fechado.
        - **Faturamento Real:** Somente o que foi 'Ganho'.
        - **Todos os Funis:** Consolida B2B, Unidade e outros funis ativos.
        """)

    st.caption("Protótipo preparado para Deploy via Docker/Easypanel.")
