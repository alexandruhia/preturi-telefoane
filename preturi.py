import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Workstation", layout="wide")

# CSS pentru a lipi coloanele și a centra zona de lucru
st.markdown("""
    <style>
    [data-testid="column"] {
        padding: 0px !important;
        margin: 0px !important;
    }
    .stSelectbox label {
        display:none;
    }
    div.stButton > button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCȚIE ÎNCĂRCARE DATE ---
@st.cache_data(ttl=60)
def incarca_date():
    sheet_url = "https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/edit?usp=sharing"
    try:
        url_export = sheet_url.split("/edit")[0] + "/export?format=xlsx"
        df = pd.read_excel(url_export)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Eroare: {e}")
        return None

# --- FUNCȚIE GENERARE ETICHETĂ ---
def creeaza_imagine_eticheta(row, font_size, line_spacing, l_scale, l_x, l_y):
    W, H = 800, 1200
    rosu_express = (204, 9, 21)
    albastru_text = (0, 51, 102)
    img = Image.new('RGB', (W, H), color=rosu_express)
    draw = ImageDraw.Draw(img)
    margine = 40
    # Card alb (fundal)
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=60, fill="white")

    try:
        f_path_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        f_path_reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        f_titlu = ImageFont.truetype(f_path_bold, int(font_size * 1.2))
        f_bold = ImageFont.truetype(f_path_bold, font_size)
        f_normal = ImageFont.truetype(f_path_reg, font_size)
    except:
        f_titlu = f_bold = f_normal = ImageFont.load_default()

    # Titluri
    draw.text((margine*2, margine*2.5), "FISA TEHNICA:", fill=albastru_text, font=f_titlu)
    draw.text((margine*2, margine*2.5 + 65), f"{row['Brand']} {row['Model']}", fill=albastru_text, font=f_titlu)

    # Toate specificațiile solicitate
    y_pos = margine * 6.5
    specs = [
        "Display", "OS", "Procesor", "Stocare", "RAM", 
        "Camera principala", "Selfie", "Sanatate baterie", "Capacitate baterie"
    ]
    
    for col in specs:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            # Scriem eticheta (BOLD)
            draw.text((margine*2, y_pos), f"{col}:", fill="black", font=f_bold)
            offset = draw.textlength(f"{col}: ", font=f_bold)
            # Scriem valoarea (NORMAL)
            draw.text((margine*2 + offset, y_pos), val, fill="black", font=f_normal)
            y_pos += line_spacing

    # Inserare Logo
    try:
        url_logo = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo = Image.open(io.BytesIO(requests.get(url_logo).content)).convert("RGBA")
        lw = int(W * l_scale)
        lh = int(lw * (logo.size[1] / logo.size[0]))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(logo, (l_x, l_y), logo)
    except: pass
    return img

# --- INTERFAȚĂ ---
df = incarca_date()

if df is not None:
    st.sidebar.header("🔍 Control Global")
    zoom_val = st.sidebar.slider("Zoom Previzualizare (px)", 100, 600, 300)

    # Cele 3 coloane principale
    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]
    
    date_etichete = []
    reglaje_etichete = []

    for i in range(3):
        with cols[i]:
            # Selectoare compacte (fără label-uri vizibile datorită CSS)
            brand = st.selectbox(f
