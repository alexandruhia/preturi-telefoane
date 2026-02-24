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
COLOR_TEXT_GLOBAL = "#000000"  # NEGRU TOTAL

st.set_page_config(page_title="ExpressCredit - Manual Liquid", layout="wide")

# ==========================================
# CSS - INTERFAȚĂ
# ==========================================
st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_SITE_BG}; color: {COLOR_TEXT_GLOBAL} !important; }}
    h1, h2, h3, p, span, label, div {{ color: {COLOR_TEXT_GLOBAL} !important; }}
    [data-testid="column"] {{
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: blur(15px);
        border-radius: 28px;
        padding: 25px !important;
        box-shadow: 0 12px 40px rgba(0,0,0,0.12);
        margin-bottom: 20px;
    }}
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {{
        border-radius: 14px !important;
        background-color: white !important;
    }}
    div.stButton > button {{
        width: 100%; background: #FFFFFF; color: black !important;
        border: 2px solid black; border-radius: 16px; height: 4em; font-weight: 800;
    }}
    div.stButton > button:hover {{ background: black; color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# CONSTANTE ȘI FUNCȚII
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

def creeaza_imagine_eticheta(row, titlu_size, font_size, line_spacing, font_name, pret_val, b_text, ag_val, bat_val, stocare_manuala, ram_manual):
    W, H = 800, 1200
    img = Image.new('RGB', (W, H), color=COLOR_ETICHETA_BG) 
    draw = ImageDraw.Draw(img)
    margine = 40
    
    # --- PARAMETRI BLOCAȚI (STRICT) ---
    PRET_Y_FIX = 800       # Poziția pe verticală a prețului
    PRET_SIZE_FIX = 50     # Mărimea textului "Pret:" și "lei"
    CIFRA_SIZE_FIX = 110   # Mărimea cifrei mari a prețului
    B_TEXT_SIZE_FIX = 42   # Mărimea codului B@Ag
    # ----------------------------------

    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=90, fill="white")

    f_reg_bytes = get_font_bytes(font_name, "Regular")
    f_bold_bytes = get_font_bytes(font_name, "Bold") or f_reg_bytes
    
    try:
        f_titlu = ImageFont.truetype(io.BytesIO(f_bold_bytes), titlu_size)
        f_label = ImageFont.truetype(io.BytesIO(f_bold_bytes), font_size)
        f_valoare = ImageFont.truetype(io.BytesIO(f_reg_bytes), font_size)
        f_pret_txt = ImageFont.truetype(io.BytesIO(f_bold_bytes), PRET_SIZE_FIX)
        f_pret_num = ImageFont.truetype(io.BytesIO(f_bold_bytes), CIFRA_SIZE_FIX)
        f_bag = ImageFont.truetype(io.BytesIO(f_bold_bytes), B_TEXT_SIZE_FIX)
    except:
        f_titlu = f_label = f_valoare = f_pret_txt = f_pret_num = f_bag = ImageFont.load_default()

    # TITLU
    txt_brand = str(row['Brand'])
    txt_model = str(row['Model'])
    draw.text(((W - draw.textlength(txt_brand, font=f_titlu)) // 2, margine * 2.5), txt_brand, fill="#000000", font=f_titlu)
    draw.text(((W - draw.textlength(txt_model, font=f_titlu)) // 2, margine * 2.5 + titlu_size), txt_model, fill="#000000", font=f_titlu)

    # SPECIFICAȚII
    y_pos = margine * 10 
    specs = [
        ("Display", row.get("Display", "-")),
        ("OS", row.get("OS", "-")),
        ("Procesor", row.get("Procesor", "-")),
        ("Stocare", stocare_manuala),
        ("RAM", ram_manual),
        ("Camera principala", row.get("Camera principala", "-")),
        ("Selfie", row.get("Selfie", "-")),
        ("Capacitate baterie", row.get("Capacitate baterie", "-")),
        ("Sanatate baterie", f"{bat_val}%")
    ]

    for label, val in specs:
        t_label = f"{label}: "
        t_val = str(val) if pd.notna(val) else "-"
        draw.text
