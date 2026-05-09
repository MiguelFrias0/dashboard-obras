import streamlit as st
import pandas as pd
from supabase import create_client, Client

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Dashboard de Obras", layout="wide")

# Credenciais (As mesmas que usamos no ETL)
URL = "https://mzoxfeamysrxyxhydroa.supabase.co"
KEY = "sb_secret_98JyR9lv9TyHiYPBHC9iJQ_q7cY1Hrq"

# Inicializa o cliente do Supabase
@st.cache_resource
def init_connection():
    return create_client(URL, KEY)

supabase = init_connection()

# ==========================================
# 2. FUNÇÃO PARA BUSCAR DADOS
# ==========================================
@st.cache_data(ttl=600) # Atualiza o cache a cada 10 minutos
def load_data():
    # Puxa tudo da tabela que você criou
    response = supabase.table("Data_Base_Secundaria").select("*").execute()
    return pd.DataFrame(response.data)

# ==========================================
# 3. INTERFACE DO DASHBOARD
# ==========================================
st.title("🏗️ Monitoramento de Projetos e Obras")

try:
    df = load_data()

    # --- KPIs RÁPIDOS ---
    total_projetos = len(df)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Projetos", total_projetos)
    
    if 'CLIENTE' in df.columns:
        col2.metric("Qtd de Clientes", df['CLIENTE'].nunique())
    
    # --- FILTROS ---
    st.sidebar.header("Filtros")
    if 'CLIENTE' in df.columns:
        cliente_sel = st.sidebar.multiselect("Selecione o Cliente", options=df['CLIENTE'].unique())
        if cliente_sel:
            df = df[df['CLIENTE'].isin(cliente_sel)]

    # --- VISUALIZAÇÃO ---
    st.subheader("Visualização dos Dados")
    st.dataframe(df, use_container_width=True)

    # --- GRÁFICO SIMPLES ---
    if 'CLIENTE' in df.columns:
        st.subheader("Projetos por Cliente")
        contagem_cliente = df['CLIENTE'].value_counts()
        st.bar_chart(contagem_cliente)

except Exception as e:
    st.error(f"Erro ao carregar dados do Supabase: {e}")