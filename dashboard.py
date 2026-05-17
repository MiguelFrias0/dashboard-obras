import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURAÇÃO E IDENTIDADE PREMIUM
# ==========================================
st.set_page_config(page_title="Costa Company - Gestão de Projetos", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 38px; color: #ffffff; }
    div[data-testid="stMetricLabel"] { font-size: 15px; color: #a1a1a1; }
    .stMetric { 
        background-color: #1e1e1e; 
        padding: 20px; 
        border-radius: 12px; 
        border-left: 5px solid #ffffff;
    }
    .subtext-chamativo {
        font-size: 13px;
        color: #00ffcc; /* Ciano Neon */
        font-weight: bold;
        margin-top: -10px;
        margin-bottom: 15px;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .subtext-alerta {
        font-size: 13px;
        color: #ff4b4b; /* Vermelho */
        font-weight: bold;
        margin-top: -10px;
        margin-bottom: 15px;
        font-family: 'Helvetica Neue', sans-serif;
    }
    h1, h2, h3 { color: #ffffff; font-family: 'Helvetica Neue', sans-serif; }
    .stDataFrame { border: 1px solid #333; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

URL = "https://mzoxfeamysrxyxhydroa.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_connection():
    return create_client(URL, KEY)

supabase = init_connection()

@st.cache_data(ttl=600)
def load_data():
    response = supabase.table("Data_Base_Secundaria").select("*").limit(10000).execute()
    data = pd.DataFrame(response.data)
    
    data = data[~data.isin(['X', 'x']).any(axis=1)]
    colunas_data = ['RECEBIDO', 'DESPACHADO', 'PREVISÃO ENVIO', 'ENVIADO']
    for col in colunas_data:
        if col in data.columns:
            data[col] = pd.to_datetime(data[col], errors='coerce').dt.date
            
    return data

# ==========================================
# 2. PROCESSAMENTO E LÓGICA (COM FUSO HORÁRIO BR)
# ==========================================
try:
    df_raw = load_data()
    status_f = df_raw['FIM / AÇÃO'].astype(str).str.lower()

    # --- AJUSTE DE FUSO HORÁRIO (UTC-3 BRASÍLIA) ---
    agora_brasil = datetime.utcnow() - timedelta(hours=3)
    hoje = agora_brasil.date()
    
    # 1. Calendário Dinâmico
    segunda = hoje - timedelta(days=agora_brasil.weekday())
    domingo = segunda + timedelta(days=6)
    periodo = st.sidebar.date_input("Filtrar Período de Análise", value=(segunda, domingo), format="DD/MM/YYYY")

    # 2. Zona Autônoma (Meses Fechados)
    hoje_pd = pd.to_datetime(hoje)
    primeiro_dia_mes_atual = hoje_pd.replace(day=1)
    
    fim_tri = (primeiro_dia_mes_atual - pd.Timedelta(days=1)).date()
    inicio_tri = (primeiro_dia_mes_atual - pd.DateOffset(months=3)).date()
    
    dias_tri = (fim_tri - inicio_tri).days + 1
    semanas_tri = dias_tri / 7 

    if isinstance(periodo, tuple) and len(periodo) == 2:
        inicio, fim = periodo
        
        # --- CÁLCULOS DO PERÍODO SELECIONADO ---
        mask_desp = (df_raw['DESPACHADO'] >= inicio) & (df_raw['DESPACHADO'] <= fim)
        total_despachados = df_raw[mask_desp].shape[0]

        mask_env = (df_raw['ENVIADO'] >= inicio) & (df_raw['ENVIADO'] <= fim) & (status_f.str.contains('ok', na=False))
        total_enviados = df_raw[mask_env].shape[0]

        mask_canc = (df_raw['RECEBIDO'] >= inicio) & (df_raw['RECEBIDO'] <= fim) & (status_f.str.contains('cancelad', na=False))
        total_cancelados = df_raw[mask_canc].shape[0]

        taxa_conversao = (total_enviados / total_despachados) * 100 if total_despachados > 0 else 0.0
        taxa_str = f"{taxa_conversao:.1f}%"

        # --- CÁLCULOS DO TRIMESTRE FECHADO ---
        mask_desp_tri = (df_raw['DESPACHADO'] >= inicio_tri) & (df_raw['DESPACHADO'] <= fim_tri)
        total_desp_tri = df_raw[mask_desp_tri].shape[0]

        mask_env_tri = (df_raw['ENVIADO'] >= inicio_tri) & (df_raw['ENVIADO'] <= fim_tri) & (status_f.str.contains('ok', na=False))
        total_env_tri = df_raw[mask_env_tri].shape[0]

        media_desp_semana = total_desp_tri / semanas_tri if semanas_tri > 0 else 0
        media_env_semana = total_env_tri / semanas_tri if semanas_tri > 0 else 0

        # --- CÁLCULO DE CRESCIMENTO ---
        perc_desp = ((total_despachados - media_desp_semana) / media_desp_semana) * 100 if media_desp_semana > 0 else 0
        perc_env = ((total_enviados - media_env_semana) / media_env_semana) * 100 if media_env_semana > 0 else 0

        classe_desp = "subtext-chamativo" if perc_desp >= 0 else "subtext-alerta"
        sinal_desp = "+" if perc_desp >= 0 else ""
        
        classe_env = "subtext-chamativo" if perc_env >= 0 else "subtext-alerta"
        sinal_env = "+" if perc_env >= 0 else ""

        meta_equipe_semana = media_desp_semana * 1.30
        meta_individual_semana = meta_equipe_semana / 4

        # ==========================================
        # 3. INTERFACE GRÁFICA
        # ==========================================
        st.title("🏗️ Dashboard de Gestão | Costa Company")
        st.write(f"Filtro Dinâmico: **{inicio.strftime('%d/%m/%Y')}** até **{fim.strftime('%d/%m/%Y')}**")
        st.markdown("---")

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("🚛 Despachados", total_despachados)
        with c2: st.metric("✅ Enviados (OK)", total_enviados)
        with c3: st.metric("📊 Enviados Vs. Despachados", taxa_str)
        with c4: st.metric("🚫 Cancelados", total_cancelados)

        st.markdown("<br>", unsafe_allow_html=True)
        
        meses = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 
                 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
        texto_trimestre = f"{meses[inicio_tri.month]} a {meses[fim_tri.month]}/{fim_tri.year}"
        
        st.subheader(f"🎯 Desempenho e Metas (Base Meses Fechados: {texto_trimestre})")
        
        ca1, ca2, ca3, ca4 = st.columns(4)
        with ca1:
            st.metric("🏭 Média Despachos / Sem", f"{media_desp_semana:.1f}")
            st.markdown(f"<p class='{classe_desp}'>⚡ Período: {sinal_desp}{perc_desp:.1f}% vs média</p>", unsafe_allow_html=True)
        with ca2:
            st.metric("📈 Média Envios / Sem", f"{media_env_semana:.1f}")
            st.markdown(f"<p class='{classe_env}'>⚡ Período: {sinal_env}{perc_env:.1f}% vs média</p>", unsafe_allow_html=True)
        with ca3:
            st.metric("👥 Meta Equipe (Semanal)", f"{meta_equipe_semana:.1f}")
            st.markdown("<p class='subtext-chamativo' style='color: #ffaa00;'>🏆 Média Despachos + 30%</p>", unsafe_allow_html=True)
        with ca4:
            st.metric("👤 Meta Individual (Semanal)", f"{meta_individual_semana:.1f}")
            st.markdown("<p class='subtext-chamativo' style='color: #ffaa00;'>🏃‍♂️ Divisão por 4 Orçamentistas</p>", unsafe_allow_html=True)

        st.markdown("---")

        st.subheader("📈 Tendência de Fluxo Histórico")
        rec_g = df_raw.groupby('RECEBIDO').size().rename('Recebidos')
        desp_g = df_raw.groupby('DESPACHADO').size().rename('Despachados')
        env_g = df_raw[status_f.str.contains('ok', na=False)].groupby('ENVIADO').size().rename('Enviados')
        
        df_chart = pd.concat([rec_g, desp_g, env_g], axis=1).fillna(0).astype(int).sort_index()
        st.line_chart(df_chart.loc[inicio:fim])

        st.markdown("---")
        st.subheader("📋 Detalhamento dos Projetos Ativos")
        df_table = df_raw[(df_raw['RECEBIDO'] >= inicio) | (df_raw['DESPACHADO'] >= inicio)]
        st.dataframe(df_table, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar o dashboard: {e}")
