import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Workstation Pro", layout="wide")

# CSS pentru eliminarea spațiilor și centrarea elementelor în coloane
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
        st.error(f"Eroare la baza de date: {e}")
        return None

# --- FUNCȚIE GENERARE ETICHETĂ (FĂRĂ FISA TEHNICA + CENTRARE) ---
def creeaza_imagine_eticheta(row, font_size, line_spacing, l_scale, l_x_manual, l_y):
    W, H = 800, 1200
    rosu_express = (204, 9, 21)
    albastru_text = (0, 51, 102)
    img = Image.new('RGB', (W, H), color=rosu_express)
    draw = ImageDraw.Draw(img)
    margine = 40
    
    # Card alb central
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=60, fill="white")

    try:
        f_path_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        f_path_reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        f_titlu = ImageFont.truetype(f_path_bold, int(font_size * 1.3)) # Titlu model puțin mai mare
        f_bold = ImageFont.truetype(f_path_bold, font_size)
        f_normal = ImageFont.truetype(f_path_reg, font_size)
    except:
        f_titlu = f_bold = f_normal = ImageFont.load_default()

    # --- CENTRARE NUME MODEL (Singur în partea de sus) ---
    txt_model = f"{row['Brand']} {row['Model']}"
    w_tm = draw.textlength(txt_model, font=f_titlu)
    
    # Poziționăm modelul mai jos de marginea de sus pentru echilibru
    draw.text(((W - w_tm) // 2, margine * 3.5), txt_model, fill=albastru_text, font=f_titlu)

    # --- SPECIFICAȚII ---
    y_pos = margine * 7.0 # Coborâm puțin startul specificațiilor
    specs = [
        "Display", "OS", "Procesor", "Stocare", "RAM", 
        "Camera principala", "Selfie", "Sanatate baterie", "Capacitate baterie"
    ]
    
    for col in specs:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            draw.text((margine * 2, y_pos), f"{col}:", fill="black", font=f_bold)
            offset = draw.textlength(f"{col}: ", font=f_bold)
            draw.text((margine * 2 + offset, y_pos), val, fill="black", font=f_normal)
            y_pos += line_spacing

    # --- CENTRARE LOGO ---
    try:
        # Folosim logo-ul alb
        url_logo = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo_res = requests.get(url_logo)
        logo = Image.open(io.BytesIO(logo_res.content)).convert("RGBA")
        
        lw = int(W * l_scale)
        lh = int(lw * (logo.size[1] / logo.size[0]))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        
        x_final = (W - lw) // 2 if l_x_manual == 100 else l_x_manual
        img.paste(logo, (x_final, l_y), logo)
    except:
        pass
        
    return img

# --- INTERFAȚĂ ---
df = incarca_date()

if df is not None:
    st.sidebar.header("🔍 Vizibilitate")
    zoom_preview = st.sidebar.slider("Zoom Previzualizare (px)", 100, 600, 320)

    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]
    
    date_etichete = []
    reglaje_etichete = []

    for i in range(3):
        with cols[i]:
            brand = st.selectbox(f"B{i}", sorted(df['Brand'].dropna().unique()), key=f"b_{i}")
            model = st.selectbox(f"M{i}", df[df['Brand'] == brand]['Model'].dropna().unique(), key=f"m_{i}")
            row_data = df[(df['Brand'] == brand) & (df['Model'] == model)].iloc[0]
            
            with st.expander("⚙️"):
                fs = st.slider("Font", 15, 45, 25, key=f"fs_{i}")
                ls = st.slider("Spațiu", 15, 60, 32, key=f"ls_{i}")
                sc = st.slider("Logo", 0.1, 1.2, 0.7, key=f"lsc_{i}")
                lx = st.number_input("X (100=Centru)", 0, 800, 100, key=f"lx_{i}")
                ly = st.number_input("Y", 0, 1200, 1080, key=f"ly_{i}")
            
            date_etichete.append(
