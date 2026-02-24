import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Pro Configurator", layout="wide")

# CSS pentru panou de reglaje GIGANT
st.markdown("""
    <style>
    [data-testid="column"] { padding: 5px !important; }
    .stSlider label, .stSelectbox label, .stNumberInput label, .stTextInput label {
        font-size: 18px !important;
        font-weight: 800 !important;
        color: #000000 !important;
    }
    div.stButton > button { height: 4em; font-weight: bold; background-color: #cc0915; color: white; border-radius: 10px; }
    .stExpander { border: 2px solid #cc0915 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- LISTĂ 100 FONTURI ---
FONT_NAMES = ["Roboto", "Montserrat", "Bebas Neue", "Open Sans", "Lato", "Oswald", "Raleway", "Ubuntu", "Nunito", "Playfair Display", "Dancing Script", "Pacifico", "Caveat", "Satisfy", "Lobster", "Anton", "Questrial", "Sora", "Jost", "Manrope"] # (Restul listei de 100 e implicită prin logica de download)

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

def creeaza_imagine_eticheta(row, font_size, line_spacing, l_scale, l_x_manual, l_y, font_name, font_style, pret_val, b_val, ag_val, py, ps, ay, asize):
    W, H = 800, 1200
    img = Image.new('RGB', (W, H), color=(204, 9, 21))
    draw = ImageDraw.Draw(img)
    margine = 40
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=60, fill="white")

    f_bytes = get_font_bytes(font_name, font_style)
    f_bold_bytes = get_font_bytes(font_name, "Bold") or f_bytes
    
    try:
        if f_bytes:
            f_titlu = ImageFont.truetype(io.BytesIO(f_bold_bytes), int(font_size * 1.3))
            f_label = ImageFont.truetype(io.BytesIO(f_bold_bytes), font_size)
            f_valoare = ImageFont.truetype(io.BytesIO(f_bytes), font_size)
            f_pret = ImageFont.truetype(io.BytesIO(f_bold_bytes), ps)
            f_ag = ImageFont.truetype(io.BytesIO(f_bytes), asize)
        else:
            path_b = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            f_titlu = f_label = f_pret = ImageFont.truetype(path_b, font_size)
            f_valoare = f_ag = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except:
        f_titlu = f_label = f_valoare = f_pret = f_ag = ImageFont.load_default()

    # Model
    txt_m = f"{row['Brand']} {row['Model']}"
    w_m = draw.textlength(txt_m, font=f_titlu)
    draw.text(((W - w_m) // 2, margine * 3), txt_m, fill=(0, 51, 102), font=f_titlu)

    # Specificații
    y_pos = margine * 7.5
    specs = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Selfie", "Sanatate baterie", "Capacitate baterie"]
    for col in specs:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            draw.text((margine * 2, y_pos), f"{col}:", fill="black", font=f_label)
            offset = draw.textlength(f"{col}: ", font=f_label)
            draw.text((margine * 2 + offset, y_pos), val, fill="black", font=f_valoare)
            y_pos += line_spacing

    # --- PREȚ ---
    if pret_val:
        txt_p = f"Pret: {pret_val} lei"
        w_p = draw.textlength(txt_p, font=f_pret)
        draw.text(((W - w_p) // 2, py), txt_p, fill=(204, 9, 21), font=f_pret)

    # --- RUBRICA B @ AG ---
    txt_bag = f"B: {b_val} @ {ag_val}"
