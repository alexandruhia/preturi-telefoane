import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# ==========================================
# CONFIGURARE CULORI BRAND
# ==========================================
COLOR_SITE_BG = "#96c83f"      # Verde lime
COLOR_ETICHETA_BG = "#cf1f2f"  # Roșu brand
COLOR_TEXT_GLOBAL = "#000000"  # Negru

st.set_page_config(page_title="ExpressCredit - Label Designer", layout="wide")

# ==========================================
# CSS - INTERFAȚĂ MODERNĂ
# ==========================================
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {COLOR_SITE_BG};
    }}
    [data-testid="column"] {{
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 20px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }}
    h3 {{ color: #000 !important; font-weight: 800 !important; }}
    label {{ color: #333 !important; font-weight: 600 !important; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# FUNCȚII ȘI RESURSE
# ==========================================
STOCARE_OPTIUNI = ["8 GB", "16 GB", "32 GB", "64 GB", "128 GB", "256 GB", "512 GB", "1 TB"]
RAM_OPTIUNI = ["1 GB", "2 GB", "3 GB", "4 GB", "6 GB", "8 GB", "12 GB", "16 GB", "24 GB", "32 GB"]

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

def creeaza_imagine_eticheta(row, t_size, f_size, sp, font_name, pret, b_cod, ag_val, bat_val, stoc_man, ram_man):
    # Rezoluție calibrată pentru ca fontul de 500 să fie vizibil uriaș
    W, H = 1200, 2200 
    img = Image.new('RGB', (W, H), color=COLOR_ETICHETA_BG) 
    draw = ImageDraw.Draw(img)
    margine_ext = 60
    
    # Fundal alb rotunjit (lăsăm spațiu jos pentru logo)
    draw.rounded_rectangle([margine_ext, margine_ext, W-margine_ext, H-300], radius=120, fill="white")

    f_bytes_reg = get_font_bytes(font_name, "Regular")
    f_bytes_bold = get_font_bytes(font_name, "Bold") or f_bytes_reg
    
    try:
        f_titlu = ImageFont.truetype(io.BytesIO(f_bytes_bold),
