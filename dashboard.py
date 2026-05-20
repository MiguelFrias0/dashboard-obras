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
    /* Estilização para as Abas */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-size: 18px; }
    /* Estilização do Expander */
    .streamlit-expanderHeader { font-size: 18px; font-weight: bold; color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

URL = "https://mzoxfeamysrxyxhydroa
