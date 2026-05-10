import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURAÇÃO E CONEXÃO
# ==========================================
st.set_page_config(page_title="Gestão de Projetos - Histórico", layout="wide")

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
    
    # Limpeza: Remove linhas onde colunas essenciais são 'X' ou nulas
    # Se 'PROJETO' ou 'RECEBIDO' for 'X', a linha é descartada
    data = data[~data.stack().str.contains('^X$', na=False).any(level=0)]
    
    return data

# ==========================================
# 2. PROCESSAMENTO PARA O GRÁFICO DE LINHAS
# ==========================================
def preparar_historico(df):
    # Criamos cópias para não estragar o dataframe original
    df_hist = df.copy()
    
    # 1. Separar Cancelados de Enviados na coluna ENVIADO
    # Se for texto como "cancelado", vira 1 na coluna Cancelados
    df_hist['IS_CANCELADO'] = df_hist['ENVIADO'].astype(str).str.lower().str.contains('cancelad', na=False)
    
    # 2. Converter colunas para data real (ignora erros de texto)
    df_hist['RECEBIDO_DT'] = pd.to_datetime(df_hist['RECEBIDO'], errors='coerce').dt.date
    df_hist['DESPACHADO_DT'] = pd.to_datetime(df_hist['DESPACHADO'], errors='coerce').dt.date
    df_hist['ENVIADO_DT'] = pd.to_datetime(df_hist['ENVIADO'], errors='coerce').dt.date
    
    # 3. Contabilizar eventos por dia
    rec = df_hist.groupby('RECEBIDO_DT').size().rename('Recebidos')
    desp = df_hist.groupby('DESPACHADO_DT').size().rename('Despachados')
    env = df_hist[df_hist['IS_CANCELADO'] == False].groupby('ENVIADO_DT').size().rename('Enviados')
    
    # Para cancelados, usamos a data de recebimento como referência de quando o projeto "morreu" no sistema
    # ou a data de enviado se houver. Aqui usaremos a data de recebimento para o histórico.
    canc = df_hist[df_hist['IS_CANCELADO'] == True].groupby('RECEBIDO_DT').size().rename('Cancelados')
    
    # Cruzar todas as datas em uma única tabela
    historico = pd.concat([rec, desp, env, canc], axis=1).fillna(0).astype(int)
    historico.index.name = 'Data'
    return historico

# ==========================================
# 3. INTERFACE
# ==========================================
try:
    df_raw = load_data()
    
    st.title("📈 Histórico Geral de Fluxo de Projetos")
    
    # Preparar dados do gráfico (Independente do filtro de data para ser Histórico)
    df_linha = preparar_historico(df_raw)
    
    # Filtro de Data na Lateral (Apenas para a Tabela e KPIs)
    st.sidebar.header("🗓️ Filtro de Visualização")
    hoje = datetime.now().date()
    periodo = st.sidebar.date_input("Filtrar Tabela por Período", 
                                   value=(hoje - timedelta(days=30), hoje))

    # --- GRÁFICO DE LINHAS QUE SE CRUZAM ---
    st.subheader("Visualização Histórica (Recebidos vs Despachados vs Enviados vs Cancelados)")
    st.line_chart(df_linha)

    # --- KPIs NO PERÍODO SELECIONADO ---
    if isinstance(periodo, tuple) and len(periodo) == 2:
        inicio, fim = periodo
        df_filtrado = df_raw.copy()
        df_filtrado['RECEBIDO_TMP'] = pd.to_datetime(df_filtrado['RECEBIDO'], errors='coerce').dt.date
        mask = (df_filtrado['RECEBIDO_TMP'] >= inicio) & (df_filtrado['RECEBIDO_TMP'] <= fim)
        df_final = df_filtrado[mask]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Recebidos", len(df_final))
        # Cálculo de cancelados no período
        canc_count = df_final['ENVIADO'].astype(str).str.lower().str.contains('cancelad', na=False).sum()
        c2.metric("Cancelados", canc_count)
        
        st.subheader(f"📋 Detalhes do Período: {inicio.strftime('%d/%m/%y')} a {fim.strftime('%d/%m/%y')}")
        st.dataframe(df_final.drop(columns=['RECEBIDO_TMP']), use_container_width=True)

except Exception as e:
    st.error(f"Erro ao processar gráfico histórico: {e}")