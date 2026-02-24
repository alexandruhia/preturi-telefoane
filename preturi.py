import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# ==========================================
# CONFIGURARE CULORI BRAND
# ==========================================
COLOR_SITE_BG = "#96c83f"      # Verdele lime pentru fundalul site-ului
COLOR_ETICHETA_BG = "#cf1f2f"  # Roșul pentru bordura etichetei
COLOR_TEXT_GLOBAL = "#000000"  # NEGRU TOTAL (SITE + ETICHETĂ)

# Configurare pagină Streamlit
st.set_page_config(page_title="ExpressCredit - Liquid Edition", layout="wide")

# ==========================================
# CSS - INTERFAȚĂ APPLE LIQUID
# ==========================================
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {COLOR_SITE_BG};
        color: {COLOR_TEXT_GLOBAL} !important;
    }}
    
    h1, h2, h3, p, span, label, div {{
        color: {COLOR_TEXT_GLOBAL} !important;
    }}

    [data-testid="column"] {{
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: blur(15px);
        border-radius: 28px;
        padding: 25px !important;
        border: 1px solid rgba(255,255,255,0.4);
        box-shadow: 0 12px 40px rgba(0,0,0,0.12);
        margin-bottom: 20px;
    }}

    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {{
        border-radius: 14px !important;
        border: 1px solid rgba(0,0,0,0.2) !important;
        background-color: white !important;
        color: {COLOR_TEXT_GLOBAL} !important;
    }}

    div.stButton > button {{
        width: 100%;
        background: #FFFFFF;
        color: {COLOR_TEXT_GLOBAL} !important;
        border: 2px solid {COLOR_TEXT_GLOBAL};
        border-radius: 16px;
        height: 4em;
        font-weight: 800;
        transition: all 0.3s ease;
    }}
    
    div.stButton > button:hover {{
        background: {COLOR_TEXT_GLOBAL};
        color: #FFFFFF !important;
    }}

    .stExpander {{
        border: none !important;
        background-color: rgba(255,255,255,0.4) !important;
        border-radius: 16px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# FUNCȚII GENERARE FONT ȘI IMAGINE
# ==========================================
@st.cache_data(show_spinner=False)
def get_font_bytes(font_name, weight):
    folders = ['ofl', 'apache', 'googlefonts']
    clean_name = font_name.lower().replace(" ", "")
    for folder in folders:
        url = f"https://github.com/google/fonts/raw/main/{folder}/{clean_name}/{font_name.replace(' ', '')}-{weight}.ttf"
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200: return r.content
        except: continue
    return None

def creeaza_imagine_eticheta(row, titlu_size, font_size, line_spacing, font_name, pret_val, pret_y, pret_size, cifra_size, b_text, ag_val, bat_val):
    W, H = 800, 1200
    img = Image.new('RGB', (W, H), color=COLOR_ETICHETA_BG) 
    draw = ImageDraw.Draw(img)
    margine = 40
    
    # Fundalul alb rotunjit
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=90, fill="white")

    f_reg_bytes = get_font_bytes(font_name, "Regular")
    f_bold_bytes = get_font_bytes(font_name, "Bold") or f_reg_bytes
    
    try:
        if f_reg_bytes:
            f_titlu = ImageFont.truetype(io.BytesIO(f_bold_bytes), titlu_size)
            f_label = ImageFont.truetype(io.BytesIO(f_bold_bytes), font_size)
            f_valoare = ImageFont.truetype(io.BytesIO(f_reg_bytes), font_size)
            f_pret_text = ImageFont.truetype(io.BytesIO(f_bold_bytes), pret_size)
            f_pret_cifra = ImageFont.truetype(io.BytesIO(f_bold_bytes), cifra_size)
            f_bag = ImageFont.truetype(io.BytesIO(f_bold_bytes), 40)
        else:
            path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            f_titlu = ImageFont.truetype(path, titlu_size)
            f_label = ImageFont.truetype(path, font_size)
            f_valoare = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            f_pret_text = ImageFont.truetype(path, pret_size)
            f_pret_cifra = ImageFont.truetype(path, cifra_size)
            f_bag = ImageFont.truetype(path, 40)
    except:
        f_titlu = f_label = f_valoare = f_pret_text = f_pret_cifra = f_bag = ImageFont.load_default()

    #
