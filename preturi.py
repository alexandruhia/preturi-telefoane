import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# CONFIGURARE CULORI
COLOR_SITE_BG = "#96c83f"  # Verdele lime pentru fundalul site-ului
COLOR_ETICHETA_BG = "#cf1f2f"  # Roșul pentru eticheta propriu-zisă

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Liquid Edition", layout="wide")

# CSS - APPLE LIQUID MODERN THEME
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {COLOR_SITE_BG};
    }}
    
    /* Carduri etichete cu efect de sticlă */
    [data-testid="column"] {{
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(15px);
        border-radius: 28px;
        padding: 20px !important;
        border: 1px solid rgba(255,255,255,0.3);
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
    }}

    /* Input-uri stilizate */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {{
        border-radius: 12px !important;
        border: 1px solid rgba(0,0,0,0.1) !important;
        background-color: white !important;
    }}

    /* Buton generare */
    div.stButton > button {{
        width: 100%;
        background: #1D1D1F;
        color: white;
        border: none;
        border-radius: 14px;
        height: 3.5em;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    
    div.stButton > button:hover {{
        background: #000000;
        transform: translateY(-2px);
    }}

    .stExpander {{
        border: none !important;
        background-color: rgba(0,0,0,0.04) !important;
        border-radius: 14px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

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

def creeaza_imagine_eticheta(row, titlu_size, font_size, line_spacing, l_scale, l_x_manual, l_y, font_name, pret_val, pret_y, pret_size, cifra_size, b_text, ag_val, bat_val):
    W, H = 800, 1200
    # FUNDALUL ETICHETEI (#cf1f2f)
    img = Image.new('RGB', (W, H), color=COLOR_ETICHETA_BG) 
    draw = ImageDraw.Draw(img)
    margine = 40
    
    # Corpul alb interior
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=85, fill="white")

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

    # Brand & Model
    txt_m = f"{row['Brand']} {row['Model']}"
    w_m = draw.textlength(txt_m, font=f_titlu)
    draw.text(((W - w_m) // 2, margine * 3.8), txt_m, fill="#1D1D1F", font=f_titlu)

    # Specificații
    y_pos = margine * 8
    specs = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Selfie", "Capacitate baterie"]
    for col in specs:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            draw.text((margine * 2.8, y_pos), f"{col}:", fill="#6E6E73", font=f_label)
            offset = draw.textlength(f"{col}: ", font=f_label)
            draw.text((margine * 2.8 + offset, y_pos), val, fill="#1D1D1F", font=f_valoare)
            y_pos += line_spacing

    # Baterie
    draw.text((margine * 2.8, y_pos), "Sanatate baterie:", fill="#6E6E73", font=f_label)
    offset_bat = draw.textlength("Sanatate baterie: ", font=f_label)
    draw.text((margine * 2.8 + offset_bat, y_pos), f"{bat_val}%", fill="#1D1D1F", font=f_valoare)

    # Zonă Preț aliniată la bază
    if pret_val:
        t1, t2, t3 = "Pret: ", f"{pret_val}", " lei"
        w1, w2, w3 = draw.textlength(t1, font=f_pret_text), draw.textlength(t2, font=f_pret_cifra), draw.textlength(t3, font=f_pret_text)
        total_w = w1 + w2 + w3
        start_x = (W - total_w) // 2
        y_base = pret_y + cifra_size 
        
        draw.text((start_x, y_base - pret_size), t1, fill=COLOR_ETICHETA_BG, font=f_pret_text)
        draw.text((start_x + w1, y_base - cifra_size), t2, fill=COLOR_ETICHETA_BG, font=f_pret_cifra)
        draw.text((start_x + w1 + w2, y_base - pret_size), t3, fill=COLOR_ETICHETA_BG, font=f_pret_text)
        
        txt_bag = f"B{b_text}@Ag{ag_val}"
        w_bag = draw.textlength(txt_bag, font=f_bag)
        draw.text((W - margine * 3.5 - w_bag, y_base + 35), txt_bag, fill="#AEAEB2", font=f_bag)

    # Logo
    try:
        url_l = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo = Image.open(io.BytesIO(requests.get(url_l).content)).convert("RGBA")
        lw = int(W * l_scale)
        lh = int(lw * (logo.size[1] / logo.size[0]))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        x_f = (W - lw) // 2 if l_x_manual == 100 else l_x_manual
        img.paste(logo, (x_f, l_y), logo)
    except: pass
    return img

# --- INTERFAȚĂ ---
df = pd.read_excel("https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx")

st.sidebar.markdown(f"### ⚙️ PARAMETRI")
zoom = st.sidebar.slider("Zoom Etichete", 200, 800, 380)

FONT_NAMES = ["Montserrat", "Roboto", "Inter",
