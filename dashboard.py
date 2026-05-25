import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. CONFIGURAÇÃO E IDENTIDADE VISUAL DARK-PREMIUM
# ==========================================
st.set_page_config(page_title="Gestão de Projetos | High-End", layout="wide")

# CSS Avançado para mudar a cara do Streamlit
st.markdown("""
    <style>
    /* Fundo principal e Sidebar */
    .main { background-color: #0b0e14; }
    [data-testid="stSidebar"] { background-color: #0e1117; border-right: 1px solid #1f2937; }
    
    /* Customização dos Cards de Métrica (Glassmorphism) */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(5px);
        transition: transform 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border: 1px solid #00ffcc;
    }
    
    /* Texto das Métricas */
    div[data-testid="stMetricValue"] { font-size: 32px !important; color: #ffffff !important; font-weight: 700 !important; }
    div[data-testid="stMetricLabel"] { font-size: 14px !important; color: #9ca3af !important; text-transform: uppercase; letter-spacing: 1px; }

    /* Subtextos Customizados */
    .subtext-chamativo { color: #00ffcc; font-size: 12px; font-weight: 600; margin-top: -5px; }
    .subtext-alerta { color: #ff4b4b; font-size: 12px; font-weight: 600; margin-top: -5px; }
    .meta-label { color: #ffaa00; font-size: 11px; font-weight: bold; }

    /* Estilização das Abas (Modernas) */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        border-radius: 8px 8px 0 0;
        padding: 10px 25px;
        color: #9ca3af;
        border: 1px solid transparent;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #00ffcc; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #1f2937;
        color: #00ffcc;
        border: 1px solid #30363d;
        border-bottom: 2px solid #00ffcc;
    }

    /* Tabelas (Dataframe) */
    .stDataFrame { border: 1px solid #30363d; border-radius: 12px; }
    
    /* Headers */
    h1, h2, h3 { color: #ffffff; letter-spacing: -1px; }
    </style>
    """, unsafe_allow_html=True)

# --- Conexão Supabase ---
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
    colunas_data = ['RECEBIDO', 'DESPACHADO', 'PREVISÃO ENVIO', 'ENVIADO']
    for col in colunas_data:
        if col in data.columns:
            data[col] = pd.to_datetime(data[col], errors='coerce').dt.date
    return data

def get_iso_week_label(date_obj):
    if pd.isna(date_obj): return None
    iso_year, iso_week, _ = date_obj.isocalendar()
    return f"Sem. {iso_week:02d} - {iso_year}"

# ==========================================
# 2. LÓGICA DE NEGÓCIO (INTACTA)
# ==========================================
try:
    df_raw = load_data()
    COLUNA_NOME, COLUNA_CAMPO, COLUNA_CLIENTE = 'RESPONSAVEL', 'PROFISSIONAL CAMPO', 'CLIENTE'
    
    # Tratamento de Strings
    for col in [COLUNA_NOME, COLUNA_CAMPO]:
        if col in df_raw.columns:
            df_raw[col] = df_raw[col].astype(str).str.strip().str.title()
    df_raw[COLUNA_CAMPO] = df_raw[COLUNA_CAMPO].str.upper()

    status_f = df_raw['FIM / AÇÃO'].astype(str).str.lower().str.strip()
    hoje = (datetime.utcnow() - timedelta(hours=3)).date()
    segunda = hoje - timedelta(days=hoje.weekday())
    domingo = segunda + timedelta(days=6)

    # Sidebar
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1087/1087815.png", width=80) # Placeholder para seu logo
    st.sidebar.title("Configurações")
    periodo = st.sidebar.date_input("Período de Análise", value=(segunda, domingo), format="DD/MM/YYYY")

    # Cálculos de Trimestre (Baseline de Meta)
    hoje_pd = pd.to_datetime(hoje)
    fim_tri = (hoje_pd.replace(day=1) - pd.Timedelta(days=1)).date()
    inicio_tri = (hoje_pd.replace(day=1) - pd.DateOffset(months=3)).date()
    semanas_tri = ((fim_tri - inicio_tri).days + 1) / 7

    # Cabeçalho Principal
    st.title("🏗️ Gestão de Projetos")
    st.markdown(f"<p style='color: #9ca3af; margin-top: -15px;'>Atualizado em: {datetime.now().strftime('%d/%m %H:%M')}</p>", unsafe_allow_html=True)
    
    tab_geral, tab_individual, tab_time, tab_campo = st.tabs(["📊 Visão Geral", "👤 Analista", "👥 Time", "👷 Campo"])

    # ==========================================
    # ABA 1: VISÃO GERAL
    # ==========================================
    with tab_geral:
        if isinstance(periodo, tuple) and len(periodo) == 2:
            inicio, fim = periodo
            
            # Filtros de Dados
            m_desp = (df_raw['DESPACHADO'] >= inicio) & (df_raw['DESPACHADO'] <= fim)
            m_env = (df_raw['ENVIADO'] >= inicio) & (df_raw['ENVIADO'] <= fim) & (status_f.str.contains('ok', na=False))
            m_canc = (df_raw['RECEBIDO'] >= inicio) & (df_raw['RECEBIDO'] <= fim) & (status_f.str.contains('cancelad', na=False))
            
            t_desp, t_env, t_canc = df_raw[m_desp].shape[0], df_raw[m_env].shape[0], df_raw[m_canc].shape[0]
            taxa = (t_env / t_desp * 100) if t_desp > 0 else 0

            # LINHA 1: MÉTRICAS ATUAIS
            st.subheader("Filtro Atual")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Despachados", t_desp)
            c2.metric("Enviados (OK)", t_env)
            c3.metric("Conversão", f"{taxa:.1f}%")
            c4.metric("Cancelados", t_canc)

            # LINHA 2: MÉDIAS E METAS
            m_desp_tri = (df_raw['DESPACHADO'] >= inicio_tri) & (df_raw['DESPACHADO'] <= fim_tri)
            m_env_tri = (df_raw['ENVIADO'] >= inicio_tri) & (df_raw['ENVIADO'] <= fim_tri) & (status_f.str.contains('ok', na=False))
            
            media_desp = df_raw[m_desp_tri].shape[0] / semanas_tri
            media_env = df_raw[m_env_tri].shape[0] / semanas_tri
            
            p_desp = ((t_desp - media_desp) / media_desp * 100) if media_desp > 0 else 0
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("Performance vs Média (Trimestre)")
            ca1, ca2, ca3, ca4 = st.columns(4)
            
            with ca1:
                st.metric("Média Despachos", f"{media_desp:.1f}")
                status_color = "subtext-chamativo" if p_desp >= 0 else "subtext-alerta"
                st.markdown(f"<p class='{status_color}'>{'▲' if p_desp >= 0 else '▼'} {abs(p_desp):.1f}% vs média</p>", unsafe_allow_html=True)
            
            with ca3:
                st.metric("Meta Equipe", f"{media_desp * 1.3:.1f}")
                st.markdown("<p class='meta-label'>GOAL: MÉDIA + 30%</p>", unsafe_allow_html=True)
            
            with ca4:
                st.metric("Meta Individual", f"{(media_desp * 1.3)/4:.1f}")
                st.markdown("<p class='meta-label'>BASE: 4 ANALISTAS</p>", unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("📈 Tendência de Movimentação")
            
            # Mantenha os DataFrames originais ( wide-form )
            rec_g = df_raw.groupby('RECEBIDO').size().rename('Recebidos')
            desp_g = df_raw.groupby('DESPACHADO').size().rename('Despachados')
            env_g = df_raw[status_f.str.contains('ok', na=False)].groupby('ENVIADO').size().rename('Enviados')
            
            # Mantenha o DataFrame df_chart original fatiado
            df_chart = pd.concat([rec_g, desp_g, env_g], axis=1).fillna(0).loc[inicio:fim]
            
            # --- [Início do Código de Gráfico Atualizado] ---
            
            # 1. Reformate os dados para o formato longo (melt) para adicionar rótulos de texto de forma limpa
            df_chart_long = df_chart.reset_index().melt(id_vars='index', var_name='Métrica', value_name='Quantidade')
            
            # 2. Crie o gráfico de área usando o formato longo, com o argumento text para rótulos
            fig_evol = px.area(df_chart_long, x='index', y='Quantidade', color='Métrica',
                               text='Quantidade', # Mostra os números sobre as áreas
                               color_discrete_map={'Recebidos': '#00d4ff', 'Despachados': '#ffaa00', 'Enviados': '#00ffcc'},
                               category_orders={'Métrica': ['Recebidos', 'Despachados', 'Enviados']}, # Garante a ordem de empilhamento original
                               template="plotly_dark")
            
            # 3. Personalize os traços:
            # - Posicionar rótulos de texto e formatar como número inteiro
            fig_evol.update_traces(textposition='top center', texttemplate='%{text:.0f}') 
            # - Personalizar o hover para remover o efeito cromático e mostrar apenas o número
            fig_evol.update_traces(hovertemplate='<b>%{y}</b>') 
            
            # 4. Personalize o layout:
            # - Configurar eixo X para mostrar apenas os dias (sem horas)
            fig_evol.update_xaxes(
                tickformat="%d %b, %Y", # Formato de data (ex: 11 May, 2026)
                dtick="D1", # Marcas a cada dia
                title_text="" # Ocultar título do eixo X "index"
            )
            # - Personalizar a legenda para o topo (manter visual original)
            fig_evol.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                legend=dict(
                    orientation="h", # Horizontal
                    yanchor="bottom", # Ancorar na parte inferior da legenda
                    y=1.02, # Posição Y acima do gráfico
                    xanchor="right", # Ancorar na parte direita da legenda
                    x=1, # Posição X no canto direito
                    title_text="" # Ocultar título da legenda "variable"
                ),
                yaxis_title_text="" # Ocultar título do eixo Y "value"
            )
            
            # Exiba o gráfico atualizado
            st.plotly_chart(fig_evol, use_container_width=True)
            
            # --- [Fim do Código de Gráfico Atualizado] ---

    # ==========================================
    # ABA 2: ANÁLISE INDIVIDUAL (INTACTA)
    # ==========================================
    with tab_individual:
        st.subheader("Análise por Orçamentista")
        responsaveis = sorted([r for r in df_raw[COLUNA_NOME].unique() if str(r).lower() != 'nan' and str(r).strip() != ''])
        
        for nome in responsaveis:
            df_pessoa = df_raw[df_raw[COLUNA_NOME] == nome]
            r_ind = df_pessoa[(df_pessoa['DESPACHADO'] >= inicio) & (df_pessoa['DESPACHADO'] <= fim)].shape[0]
            e_ind = df_pessoa[(df_pessoa['ENVIADO'] >= inicio) & (df_pessoa['ENVIADO'] <= fim) & (status_f.str.contains('ok'))].shape[0]
            tx_ind = (e_ind / r_ind * 100) if r_ind > 0 else 0
            
            with st.container():
                col_n, col_m1, col_m2, col_m3 = st.columns([2, 2, 2, 2])
                col_n.markdown(f"#### {nome}")
                col_m1.metric("Despachados", r_ind)
                col_m2.metric("Enviados", e_ind)
                col_m3.metric("Taxa", f"{tx_ind:.1f}%")
                st.markdown("<div style='height: 1px; background-color: #30363d; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # ==========================================
    # ABA 3: TIME (INTACTA)
    # ==========================================
    with tab_time:
        st.subheader("Volume Acumulado 2026")
        df_2026 = df_raw[df_raw['DESPACHADO'] >= pd.to_datetime('2026-01-01').date()]
        time_data = df_2026.groupby(COLUNA_NOME).size().reset_index(name='Qtd')
        
        fig_time = px.bar(time_data, x='Qtd', y=COLUNA_NOME, orientation='h',
                          color='Qtd', color_continuous_scale='GnBu',
                          template="plotly_dark")
        fig_time.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_time, use_container_width=True)

    # ==========================================
    # ABA 4: CAMPO (INTACTA)
    # ==========================================
    with tab_campo:
        termo = st.text_input("🔍 Buscar Profissional", placeholder="Nome do parceiro...").upper()
        profissionais = sorted([p for p in df_raw[COLUNA_CAMPO].unique() if str(p).lower() != 'nan' and termo in str(p)])
        
        for prof in profissionais:
            df_prof = df_raw[df_raw[COLUNA_CAMPO] == prof]
            with st.expander(f"👤 {prof} | {len(df_prof)} Projetos Totais"):
                c_data = df_prof[COLUNA_CLIENTE].value_counts().reset_index()
                c_data.columns = ['Cliente', 'Qtd']
                
                col_t, col_g = st.columns([1, 1])
                col_t.dataframe(c_data, hide_index=True, use_container_width=True)
                
                fig_pie = px.pie(c_data, values='Qtd', names='Cliente', hole=.5,
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=False)
                col_g.plotly_chart(fig_pie, use_container_width=True)

except Exception as e:
    st.error(f"Erro no Dashboard: {e}")
