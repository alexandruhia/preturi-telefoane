import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# ==========================================
# CONFIGURARE CULORI BRAND
# ==========================================
COLOR_SITE_BG = "#96c83f"
COLOR_ETICHETA_BG = "#cf1f2f"
COLOR_TEXT_GLOBAL = "#000000"

st.set_page_config(page_title="ExpressCredit - Nano Edition", layout="wide")

# ==========================================
# CSS - INTERFAȚĂ
# ==========================================
st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_SITE_BG}; }}
    [data-testid="column"] {{
        background: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 10px !important;
        margin-bottom: 5px;
    }}
    h3 {{ color: #000 !important; font-weight: 800 !important; }}
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
    # PÂNZĂ ULTRA-COMPACTĂ: 256x464 pixeli
    W, H = 256, 464 
    img = Image.new('RGB', (W, H), color=COLOR_ETICHETA_BG) 
    draw = ImageDraw.Draw(img)
    margine_ext = 10
    
    # Fundal alb rotunjit
    draw.rounded_rectangle([margine_ext, margine_ext, W-margine_ext, H-70], radius=20, fill="white")

    f_bytes_reg = get_font_bytes(font_name, "Regular")
    f_bytes_bold = get_font_bytes(font_name, "Bold") or f_bytes_reg
    
    try:
        # Paranteze închise corect pentru a preveni SyntaxError
        f_titlu = ImageFont.truetype(io.BytesIO(f_bytes_bold), t_size)
        f_label = ImageFont.truetype(io.BytesIO(f_bytes_bold), f_size)
        f_valoare = ImageFont.truetype(io.BytesIO(f_bytes_reg), f_size)
        f_pret_text = ImageFont.truetype(io.BytesIO(f_bytes_bold), 18)
        f_pret_cifra = ImageFont.truetype(io.BytesIO(f_bytes_bold), 38)
        f_bag = ImageFont.truetype(io.BytesIO(f_bytes_bold), 14)
    except:
        f_titlu = f_label = f_valoare = f_pret_text = f_pret_cifra = f_bag = ImageFont.load_default()

    # --- TITLU ---
    y_ptr = margine_ext * 2.5
    for txt in [str(row['Brand']), str(row['Model'])]:
        w_txt = draw.textlength(txt, font=f_titlu)
        draw.text(((W - w_txt) // 2, y_ptr), txt, fill="#000000", font=f_titlu)
        y_ptr += t_size + 2

    # --- SPECIFICAȚII ---
    y_ptr += 10 
    specs = [
        ("Stocare", stoc_man),
        ("RAM", ram_man),
        ("Baterie", f"{bat_val}%")
    ]

    for lab, val in specs:
        t_lab = f"{lab}: "
        draw.text((margine_ext * 2, y_ptr), t_lab, fill="#444444", font=f_label)
        offset = draw.textlength(t_lab, font=f_label)
        draw.text((margine_ext * 2 + offset, y_ptr), str(val), fill="#000000", font=f_valoare)
        y_ptr += sp

    # --- PREȚ ---
    y_pret = H - 150
    if pret:
        t1, t2, t3 = "Pret: ", f"{pret}", " lei"
        w1, w2, w3 = draw.textlength(t1, font=f_pret_text), draw.textlength(t2, font=f_pret_cifra), draw.textlength(t3, font=f_pret_text)
        start_x = (W - (w1 + w2 + w3)) // 2
        draw.text((start_x, y_pret + 12), t1, fill="#000000", font=f_pret_text)
        draw.text((start_x + w1, y_pret), t2, fill="#000000", font=f_pret_cifra)
        draw.text((start_x + w1 + w2, y_pret + 12), t3, fill="#000000", font=f_pret_text)
        
        txt_bag = f"B{b_cod}@Ag{ag_val}"
        w_bag = draw.textlength(txt_bag, font=f_bag)
        draw.text(((W - w_bag) // 2, y_pret + 50), txt_bag, fill="#333333", font=f_bag)

    # --- LOGO ---
    try:
        url_l = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo_res = requests.get(url_l, timeout=5)
        logo = Image.open(io.BytesIO(logo_res.content)).convert("RGBA")
        lw = int(W * 0.65)
        lh = int(lw * (logo.size[1] / logo.size[0]))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(logo, ((W - lw) // 2, H - 55), logo)
    except: pass
        
    return img

# ==========================================
# LOGICĂ STREAMLIT
# ==========================================
url_sheet = "https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx"
df = pd.read_excel(url_sheet)

st.sidebar.header("⚙️ Setări")
zoom_val = st.sidebar.slider("Previzualizare", 100, 600, 300)

col_labels = st.columns(3)
final_imgs = []

for i in range(3):
    with col_labels[i]:
        st.subheader(f"Eticheta {i+1}")
        b_sel = st.selectbox(f"Brand", sorted(df['Brand'].dropna().unique()), key=f"br_{i}")
