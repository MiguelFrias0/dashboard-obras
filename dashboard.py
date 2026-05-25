import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import plotly.express as px

# ==========================================
# 1. CONFIGURAÇÃO E IDENTIDADE PREMIUM
# ==========================================
st.set_page_config(page_title="Gestão de Projetos", layout="wide")

st.markdown("""
    <style>
    /* Fundo principal e Sidebar */
    .main { background-color: #0b0e14; }
    
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
        transform: translateY(-3px);
        border: 1px solid #00ffcc;
    }
    
    /* Texto das Métricas */
    div[data-testid="stMetricValue"] { font-size: 34px !important; color: #ffffff !important; font-weight: bold !important; }
    div[data-testid="stMetricLabel"] { font-size: 14px !important; color: #a1a1a1 !important; text-transform: uppercase; letter-spacing: 1px;}
    
    /* Classes originais mantidas para não quebrar sua lógica */
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
    
    /* Estilização Moderna para as Abas */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        white-space: pre-wrap; 
        font-size: 16px; 
        background-color: #161b22;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        color: #a1a1a1;
        border: 1px solid transparent;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #00ffcc; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #1f2937;
        color: #00ffcc;
        border-bottom: 2px solid #00ffcc;
        font-weight: bold;
    }
    
    /* Estilização do Expander */
    .streamlit-expanderHeader { font-size: 16px; font-weight: bold; color: #ffffff; }
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
    
    colunas_data = ['RECEBIDO', 'DESPACHADO', 'PREVISÃO ENVIO', 'ENVIADO']
    for col in colunas_data:
        if col in data.columns:
            # Correção mantida intacta
            data[col] = pd.to_datetime(data[col], errors='coerce').dt.date
            
    return data

def get_iso_week_label(date_obj):
    if pd.isna(date_obj):
        return None
    iso_year, iso_week, _ = date_obj.isocalendar()
    return f"Sem. {iso_week:02d} - {iso_year}"

# ==========================================
# 2. PROCESSAMENTO E LÓGICA (INTACTO)
# ==========================================
try:
    df_raw = load_data()
    
    COLUNA_NOME = 'RESPONSAVEL'
    COLUNA_CAMPO = 'PROFISSIONAL CAMPO'
    COLUNA_CLIENTE = 'CLIENTE'
    
    if COLUNA_NOME in df_raw.columns:
        df_raw[COLUNA_NOME] = df_raw[COLUNA_NOME].astype(str).str.strip().str.title()
    if COLUNA_CAMPO in df_raw.columns:
        df_raw[COLUNA_CAMPO] = df_raw[COLUNA_CAMPO].astype(str).str.strip().str.upper()

    status_f = df_raw['FIM / AÇÃO'].astype(str).str.lower().str.strip()

    agora_brasil = datetime.utcnow() - timedelta(hours=3)
    hoje = agora_brasil.date()
    
    segunda = hoje - timedelta(days=agora_brasil.weekday())
    domingo = segunda + timedelta(days=6)
    
    st.sidebar.title("⚙️ Filtros")
    periodo = st.sidebar.date_input("Filtrar Período de Análise", value=(segunda, domingo), format="DD/MM/YYYY")

    hoje_pd = pd.to_datetime(hoje)
    primeiro_dia_mes_atual = hoje_pd.replace(day=1)
    
    fim_tri = (primeiro_dia_mes_atual - pd.Timedelta(days=1)).date()
    inicio_tri = (primeiro_dia_mes_atual - pd.DateOffset(months=3)).date()
    
    dias_tri = (fim_tri - inicio_tri).days + 1
    semanas_tri = dias_tri / 7 

    st.title("🏗️ Dashboard de Gestão")
    
    tab_geral, tab_individual, tab_time, tab_campo = st.tabs([
        "📊 Visão Geral", 
        "👤 Análise Individual", 
        "👥 Análise do Time", 
        "👷 Profissionais de Campo"
    ])

    # ==========================================
    # ABA 1: VISÃO GERAL
    # ==========================================
    with tab_geral:
        if isinstance(periodo, tuple) and len(periodo) == 2:
            inicio, fim = periodo
            
            mask_desp = (df_raw['DESPACHADO'] >= inicio) & (df_raw['DESPACHADO'] <= fim)
            total_despachados = df_raw[mask_desp].shape[0]

            mask_env = (df_raw['ENVIADO'] >= inicio) & (df_raw['ENVIADO'] <= fim) & (status_f.str.contains('ok', na=False))
            total_enviados = df_raw[mask_env].shape[0]

            mask_canc = (df_raw['RECEBIDO'] >= inicio) & (df_raw['RECEBIDO'] <= fim) & (status_f.str.contains('cancelad', na=False))
            total_cancelados = df_raw[mask_canc].shape[0]

            taxa_conversao = (total_enviados / total_despachados) * 100 if total_despachados > 0 else 0.0
            taxa_str = f"{taxa_conversao:.1f}%"

            mask_desp_tri = (df_raw['DESPACHADO'] >= inicio_tri) & (df_raw['DESPACHADO'] <= fim_tri)
            total_desp_tri = df_raw[mask_desp_tri].shape[0]

            mask_env_tri = (df_raw['ENVIADO'] >= inicio_tri) & (df_raw['ENVIADO'] <= fim_tri) & (status_f.str.contains('ok', na=False))
            total_env_tri = df_raw[mask_env_tri].shape[0]

            media_desp_semana = total_desp_tri / semanas_tri if semanas_tri > 0 else 0
            media_env_semana = total_env_tri / semanas_tri if semanas_tri > 0 else 0

            perc_desp = ((total_despachados - media_desp_semana) / media_desp_semana) * 100 if media_desp_semana > 0 else 0
            perc_env = ((total_enviados - media_env_semana) / media_env_semana) * 100 if media_env_semana > 0 else 0

            classe_desp = "subtext-chamativo" if perc_desp >= 0 else "subtext-alerta"
            sinal_desp = "+" if perc_desp >= 0 else ""
            classe_env = "subtext-chamativo" if perc_env >= 0 else "subtext-alerta"
            sinal_env = "+" if perc_env >= 0 else ""

            meta_equipe_semana = media_desp_semana * 1.30
            meta_individual_semana = meta_equipe_semana / 4

            st.subheader(f"🔍 Análise do Período Filtrado")
            st.write(f"De **{inicio.strftime('%d/%m/%Y')}** até **{fim.strftime('%d/%m/%Y')}**")

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
            st.subheader("📈 Tendência Diária do Período Filtrado")
            
            # Lógica original EXATA preservada (com sort_index)
            rec_g = df_raw.groupby('RECEBIDO').size().rename('Recebidos')
            desp_g = df_raw.groupby('DESPACHADO').size().rename('Despachados')
            env_g = df_raw[status_f.str.contains('ok', na=False)].groupby('ENVIADO').size().rename('Enviados')
            
            df_chart_diario = pd.concat([rec_g, desp_g, env_g], axis=1).fillna(0).astype(int)
            df_chart_diario = df_chart_diario[df_chart_diario.index.notna()].sort_index()
            
            # Trocando st.line_chart pelo Plotly estilizado
            df_plot_diario = df_chart_diario.loc[inicio:fim]
            fig_diario = px.area(df_plot_diario, x=df_plot_diario.index, y=['Recebidos', 'Despachados', 'Enviados'],
                                 color_discrete_map={'Recebidos': '#00d4ff', 'Despachados': '#ffaa00', 'Enviados': '#00ffcc'})
            fig_diario.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#ffffff',
                                     legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_diario, use_container_width=True)

            st.markdown("---")
            st.subheader("📊 Histórico Geral de Produção (Consolidado Semanal - A partir de 2026)")
            
            df_semanal = df_raw.copy()
            df_semanal['RECEBIDO'] = pd.to_datetime(df_semanal['RECEBIDO'])
            df_semanal['DESPACHADO'] = pd.to_datetime(df_semanal['DESPACHADO'])
            df_semanal['ENVIADO'] = pd.to_datetime(df_semanal['ENVIADO'])
            
            df_semanal['Semana_Recebido'] = df_semanal['RECEBIDO'].apply(get_iso_week_label)
            df_semanal['Semana_Despachado'] = df_semanal['DESPACHADO'].apply(get_iso_week_label)
            df_semanal['Semana_Enviado'] = df_semanal['ENVIADO'].apply(get_iso_week_label)
            mask_cancelados_geral = status_f.str.contains('cancelad', na=False)
            
            rec_semana = df_semanal[df_semanal['RECEBIDO'].dt.year >= 2026].groupby('Semana_Recebido').size().rename('Recebidos')
            desp_semana = df_semanal[df_semanal['DESPACHADO'].dt.year >= 2026].groupby('Semana_Despachado').size().rename('Despachados')
            env_semana = df_semanal[(status_f.str.contains('ok', na=False)) & (df_semanal['ENVIADO'].dt.year >= 2026)].groupby('Semana_Enviado').size().rename('Enviados')
            canc_semana = df_semanal[mask_cancelados_geral & (df_semanal['RECEBIDO'].dt.year >= 2026)].groupby('Semana_Recebido').size().rename('Cancelados')

            df_chart_semanal = pd.concat([rec_semana, desp_semana, env_semana, canc_semana], axis=1).fillna(0).astype(int)
            
            if not df_chart_semanal.empty:
                df_chart_semanal = df_chart_semanal[df_chart_semanal.index.notna()]
                df_chart_semanal.index = df_chart_semanal.index.astype(str)
                df_chart_semanal['sort_key'] = df_chart_semanal.index.str[-4:] + df_chart_semanal.index.str[5:7]
                df_chart_semanal = df_chart_semanal.sort_values('sort_key').drop(columns=['sort_key'])

                fig = px.line(df_chart_semanal, x=df_chart_semanal.index, y=['Recebidos', 'Despachados', 'Enviados', 'Cancelados'],
                              labels={'value': 'Quantidade de Projetos', 'index': 'Semanas', 'variable': 'Métricas'},
                              color_discrete_map={'Recebidos': '#00d4ff', 'Despachados': '#ffaa00', 'Enviados': '#00ffcc', 'Cancelados': '#ff4b4b'})
                fig.update_layout(plot_bgcolor='#0b0e14', paper_bgcolor='#0b0e14', font_color='#ffffff')
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.subheader("📋 Detalhamento dos Projetos Ativos")
            df_table = df_raw[(df_raw['RECEBIDO'] >= inicio) | (df_raw['DESPACHADO'] >= inicio)]
            st.dataframe(df_table, use_container_width=True)

    # ==========================================
    # ABA 2: ANÁLISE INDIVIDUAL
    # ==========================================
    with tab_individual:
        st.subheader("🧑‍💼 Desempenho por Orçamentista")
        
        if isinstance(periodo, tuple) and len(periodo) == 2:
            inicio, fim = periodo
            st.write(f"Análise baseada no período dinâmico de **{inicio.strftime('%d/%m/%Y')}** até **{fim.strftime('%d/%m/%Y')}**")
            
            if COLUNA_NOME in df_raw.columns:
                responsaveis = sorted([r for r in df_raw[COLUNA_NOME].unique() if str(r).lower() != 'nan' and str(r).strip() != ''])
                
                for nome in responsaveis:
                    df_pessoa = df_raw[df_raw[COLUNA_NOME] == nome]
                    
                    rec_ind = df_pessoa[(df_pessoa['DESPACHADO'] >= inicio) & (df_pessoa['DESPACHADO'] <= fim)].shape[0]
                    env_ind = df_pessoa[(df_pessoa['ENVIADO'] >= inicio) & (df_pessoa['ENVIADO'] <= fim) & (df_pessoa['FIM / AÇÃO'].astype(str).str.lower().str.contains('ok'))].shape[0]
                    canc_ind = df_pessoa[(df_pessoa['DESPACHADO'] >= inicio) & (df_pessoa['DESPACHADO'] <= fim) & (df_pessoa['FIM / AÇÃO'].astype(str).str.lower().str.contains('cancelad'))].shape[0]
                    taxa_ind = (env_ind / rec_ind) * 100 if rec_ind > 0 else 0.0
                    
                    with st.container():
                        st.markdown(f"### {nome}")
                        col_cards, col_grafico = st.columns([7, 3])
                        with col_cards:
                            mc1, mc2, mc3, mc4 = st.columns(4)
                            mc1.metric("Recebidos (Despachados)", rec_ind)
                            mc2.metric("Enviados (OK)", env_ind)
                            mc3.metric("Cancelados", canc_ind)
                            mc4.metric("Taxa de Envio", f"{taxa_ind:.1f}%")
                        with col_grafico:
                            df_graf_ind = pd.DataFrame({'Status': ['Recebidos', 'Enviados', 'Cancelados'], 'Qtd': [rec_ind, env_ind, canc_ind]})
                            # Cores atualizadas para combinar com o tema
                            fig_bar = px.bar(df_graf_ind, x='Status', y='Qtd', color='Status', color_discrete_map={'Recebidos': '#ffaa00', 'Enviados': '#00ffcc', 'Cancelados': '#ff4b4b'}, height=150)
                            fig_bar.update_layout(margin=dict(l=0, r=0, t=20, b=0), showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title=None, yaxis_title=None)
                            st.plotly_chart(fig_bar, use_container_width=True, key=f"bar_{nome}")
                        st.markdown("<hr style='border-top: 1px solid #333;'>", unsafe_allow_html=True)
            else:
                st.error(f"Coluna '{COLUNA_NOME}' não encontrada.")

    # ==========================================
    # ABA 3: ANÁLISE DO TIME
    # ==========================================
    with tab_time:
        st.subheader("👥 Comparativo do Time (Acumulado de 2026)")
        st.write("Filtro Fixo: Dados contabilizados a partir de **01/01/2026**.")
        
        if COLUNA_NOME in df_raw.columns:
            data_corte = pd.to_datetime('2026-01-01').date()
            
            df_rec_2026 = df_raw[df_raw['DESPACHADO'] >= data_corte]
            df_env_2026 = df_raw[(df_raw['ENVIADO'] >= data_corte) & (status_f.str.contains('ok', na=False))]
            
            rec_por_analista = df_rec_2026.groupby(COLUNA_NOME).size().rename('Recebidos')
            env_por_analista = df_env_2026.groupby(COLUNA_NOME).size().rename('Enviados')
            
            df_time_chart = pd.concat([rec_por_analista, env_por_analista], axis=1).fillna(0).astype(int).reset_index()
            
            if not df_time_chart.empty:
                df_time_chart = df_time_chart[df_time_chart[COLUNA_NOME].str.lower() != 'nan']
                
                # Cores Premium
                fig_time = px.bar(df_time_chart, x=COLUNA_NOME, y=['Recebidos', 'Enviados'], barmode='group', labels={'value': 'Total de Projetos', COLUNA_NOME: 'Responsável', 'variable': 'Status'}, color_discrete_map={'Recebidos': '#ffaa00', 'Enviados': '#00ffcc'})
                fig_time.update_layout(plot_bgcolor='#0b0e14', paper_bgcolor='#0b0e14', font_color='#ffffff', xaxis_title="Equipe", yaxis_title="Volume Acumulado")
                st.plotly_chart(fig_time, use_container_width=True)

    # ==========================================
    # ABA 4: PROFISSIONAIS DE CAMPO
    # ==========================================
    with tab_campo:
        st.subheader("👷 Alocação e Distribuição por Profissional de Campo")
        st.write("Visão do volume total do banco de dados (ignorando filtros de data).")
        
        termo_pesquisa = st.text_input("🔍 Pesquisar parceiro por nome...", placeholder="Ex: João Silva").strip().upper()
        
        st.markdown("---")
        
        if COLUNA_CAMPO in df_raw.columns and COLUNA_CLIENTE in df_raw.columns:
            
            profissionais_geral = sorted([p for p in df_raw[COLUNA_CAMPO].unique() if str(p).lower() != 'nan' and str(p).strip() != ''])
            
            if termo_pesquisa:
                profissionais = [p for p in profissionais_geral if termo_pesquisa in p]
            else:
                profissionais = profissionais_geral
                
            if not profissionais:
                st.warning("Nenhum parceiro encontrado com esse nome. Tente buscar por outro termo.")
            else:
                for prof in profissionais:
                    df_prof = df_raw[df_raw[COLUNA_CAMPO] == prof]
                    total_projetos = len(df_prof)
                    
                    with st.expander(f"🛠️ {prof} | Total Geral: {total_projetos} projetos"):
                        contagem_clientes = df_prof[COLUNA_CLIENTE].value_counts().reset_index()
                        contagem_clientes.columns = ['Cliente', 'Quantidade de Projetos']
                        
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            st.markdown("**Distribuição por Cliente:**")
                            st.dataframe(contagem_clientes, hide_index=True, use_container_width=True)
                            
                        with col2:
                            if not contagem_clientes.empty:
                                fig_pie = px.pie(
                                    contagem_clientes, 
                                    values='Quantidade de Projetos', 
                                    names='Cliente', 
                                    hole=0.4, 
                                    color_discrete_sequence=px.colors.qualitative.Pastel
                                )
                                fig_pie.update_layout(
                                    showlegend=True, 
                                    margin=dict(t=0, b=0, l=0, r=0),
                                    plot_bgcolor='rgba(0,0,0,0)', 
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    font_color='#ffffff'
                                )
                                st.plotly_chart(fig_pie, use_container_width=True, key=f"pie_{prof}")
        else:
            st.error(f"Certifique-se de que as colunas '{COLUNA_CAMPO}' e '{COLUNA_CLIENTE}' existem na sua base de dados.")

except Exception as e:
    st.error(f"Erro ao carregar o dashboard: {e}")
