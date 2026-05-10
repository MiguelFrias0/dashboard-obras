import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Dashboard de Obras", layout="wide")

# Credenciais
URL = "https://mzoxfeamysrxyxhydroa.supabase.co"
KEY = "sb_secret_98JyR9lv9TyHiYPBHC9iJQ_q7cY1Hrq"

@st.cache_resource
def init_connection():
    return create_client(URL, KEY)

supabase = init_connection()

@st.cache_data(ttl=600)
def load_data():
    response = supabase.table("Data_Base_Secundaria").select("*").execute()
    data = pd.DataFrame(response.data)
    
    # Converte as colunas de data para o formato datetime do Python
    colunas_data = ['RECEBIDO', 'DESPACHADO', 'PREVISÃO ENVIO', 'ENVIADO']
    for col in colunas_data:
        if col in data.columns:
            data[col] = pd.to_datetime(data[col]).dt.date
            
    return data

# ==========================================
# 2. CARGA DE DADOS E FILTROS NA SIDEBAR
# ==========================================
try:
    df_original = load_data()
    df = df_original.copy()

    st.sidebar.header("🗓️ Filtros de Período")

    # Sugestão de data inicial (Segunda-feira desta semana)
    hoje = datetime.now().date()
    segunda_padrao = hoje - timedelta(days=hoje.weekday())
    domingo_padrao = segunda_padrao + timedelta(days=6)

    # Seletor de Intervalo de Datas
    periodo = st.sidebar.date_input(
        "Selecione o intervalo (Início - Fim)",
        value=(segunda_padrao, domingo_padrao),
        format="DD/MM/YYYY"
    )

    # Aplica o filtro se o usuário selecionar as duas datas (Início e Fim)
    if isinstance(periodo, tuple) and len(periodo) == 2:
        data_inicio, data_fim = periodo
        # Filtramos com base na coluna RECEBIDO
        df = df[(df['RECEBIDO'] >= data_inicio) & (df['RECEBIDO'] <= data_fim)]

    # ==========================================
    # 3. INTERFACE DO DASHBOARD
    # ==========================================
    st.title("🏗️ Monitoramento de Projetos e Obras")
    st.write(f"Mostrando dados de **{data_inicio.strftime('%d/%m/%Y')}** até **{data_fim.strftime('%d/%m/%Y')}**")

    # --- KPIs RÁPIDOS ---
    total_projetos = len(df)
    col1, col2, col3 = st.columns(3)
    col1.metric("Projetos no Período", total_projetos)
    
    if 'CLIENTE' in df.columns:
        col2.metric("Qtd de Clientes", df['CLIENTE'].nunique())

    # --- TABELA INTERATIVA ---
    st.subheader("📋 Lista de Projetos Filtrados")
    st.dataframe(df, use_container_width=True)

    # --- GRÁFICO POR ANALISTA ---
    if 'ANALISTA CLIENTE' in df.columns:
        st.subheader("📊 Carga por Analista (no período)")
        contagem_analista = df['ANALISTA CLIENTE'].value_counts()
        st.bar_chart(contagem_analista)

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")