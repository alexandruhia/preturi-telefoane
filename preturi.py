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

st.set_page_config(page_title="ExpressCredit - Liquid Edition", layout="wide")

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
        width: 100%; background: #FFFFFF; border: 2px solid {COLOR_TEXT_GLOBAL};
        border-radius: 16px; height: 4em; font-weight: 800;
    }}
    div.stButton > button:hover {{ background: {COLOR_TEXT_GLOBAL}; color: #FFFFFF !important; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# FUNCȚII GENERARE
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
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=90, fill="white")

    f_reg_bytes = get_font_bytes(font_name, "Regular")
    f_bold_bytes = get_font_bytes(font_name, "Bold") or f_reg_bytes
    
    try:
        f_titlu = ImageFont.truetype(io.BytesIO(f_bold_bytes), titlu_size)
        f_label = ImageFont.truetype(io.BytesIO(f_bold_bytes), font_size)
        f_valoare = ImageFont.truetype(io.BytesIO(f_reg_bytes), font_size)
        f_pret_text = ImageFont.truetype(io.BytesIO(f_bold_bytes), pret_size)
        f_pret_cifra = ImageFont.truetype(io.BytesIO(f_bold_bytes), cifra_size)
        f_bag = ImageFont.truetype(io.BytesIO(f_bold_bytes), 40)
    except:
        f_titlu = f_label = f_valoare = f_pret_text = f_pret_cifra = f_bag = ImageFont.load_default()

    # TITLU
    txt_brand = str(row['Brand'])
    txt_model = str(row['Model'])
    draw.text(((W - draw.textlength(txt_brand, font=f_titlu)) // 2, margine * 2.5), txt_brand, fill="#000000", font=f_titlu)
    draw.text(((W - draw.textlength(txt_model, font=f_titlu)) // 2, margine * 2.5 + titlu_size), txt_model, fill="#000000", font=f_titlu)

    # SPECIFICAȚII
    y_pos = margine * 10
    specs = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Selfie", "Capacitate baterie"]
    for col in specs:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            draw.text((margine * 1.5, y_pos), f"{col}:", fill="#333333", font=f_label)
            offset = draw.textlength(f"{col}: ", font=f_label)
            draw.text((margine * 1.5 + offset, y_pos), val, fill="#000000", font=f_valoare)
            y_pos += line_spacing

    draw.text((margine * 1.5, y_pos), "Sanatate baterie:", fill="#333333", font=f_label)
    offset_bat = draw.textlength("Sanatate baterie: ", font=f_label)
    draw.text((margine * 1.5 + offset_bat, y_pos), f"{bat_val}%", fill="#000000", font=f_valoare)

    # PREȚ
    if pret_val:
        t1, t2, t3 = "Pret: ", f"{pret_val}", " lei"
        w1, w2, w3 = draw.textlength(t1, font=f_pret_text), draw.textlength(t2, font=f_pret_cifra), draw.textlength(t3, font=f_pret_text)
        start_x = (W - (w1 + w2 + w3)) // 2
        y_base = pret_y + cifra_size 
        draw.text((start_x, y_base - pret_size), t1, fill="#000000", font=f_pret_text)
        draw.text((start_x + w1, y_base - cifra_size), t2, fill="#000000", font=f_pret_cifra)
        draw.text((start_x + w1 + w2, y_base - pret_size), t3, fill="#000000", font=f_pret_text)
        
        txt_bag = f"B{b_text}@Ag{ag_val}"
        draw.text((W - margine * 4 - draw.textlength(txt_bag, font=f_bag), y_base + 35), txt_bag, fill="#333333", font=f_bag)

    # LOGO BLOCAT (Fixat jos, centrat)
    try:
        url_l = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo = Image.open(io.BytesIO(requests.get(url_l).content)).convert("RGBA")
        lw = int(W * 0.6) # Dimensiune fixă (60% din lățime)
        lh = int(lw * (logo.size[1] / logo.size[0]))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(logo, ((W - lw) // 2, 1060), logo) # Poziție fixă Y=1060
    except: pass
    return img

# ==========================================
# LOGICĂ APLICAȚIE
# ==========================================
url_sheet = "https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx"
df = pd.read_excel(url_sheet)

st.sidebar.markdown(f"### <span style='color:black'>●</span> CONTROL PANEL", unsafe_allow_html=True)
zoom = st.sidebar.slider("Zoom Vizualizare", 200, 800, 380)

FONT_NAMES = ["Montserrat", "Roboto", "Inter", "Poppins", "Anton"]
ag_list = [str(i) for i in range(1, 56)]
battery_list = [str(i) for i in range(100, 0, -1)]

col_main = st.columns(3)
final_imgs = []

for i in range(3):
    with col_main[i]:
        st.markdown(f"### 📱 Eticheta {i+1}")
        brand = st.selectbox(f"Brand", sorted(df['Brand'].dropna().unique()), key=f"b_{i}")
        model = st.selectbox(f"Model", df[df['Brand'] == brand]['Model'].dropna().unique(), key=f"m_{i}")
