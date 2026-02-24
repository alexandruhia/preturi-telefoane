import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io

# Configurare pagină
st.set_page_config(page_title="Generator Etichete ExpressCredit", page_icon="📱")

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
        st.error(f"⚠️ Eroare: {e}")
        return None

# --- FUNCȚIE GENERARE ETICHETĂ (STILUL DIN IMAGINE) ---
def genereaza_eticheta_imagine(row, coloane):
    # Dimensiuni imagine (Portret)
    W, H = 800, 1200
    rosu_express = (204, 9, 21) # Culoarea roșie din logo
    albastru_text = (0, 51, 102) # Culoarea titlului
    
    # 1. Creăm fundalul roșu
    img = Image.new('RGB', (W, H), color=rosu_express)
    draw = ImageDraw.Draw(img)

    # 2. Desenăm cardul alb cu colțuri rotunjite
    # [x0, y0, x1, y1]
    draw.rounded_rectangle([40, 40, 760, 1050], radius=60, fill="white")

    # 3. Încărcare Fonturi (Folosim default dacă nu găsește fișiere specifice)
    try:
        # Streamlit Cloud are de obicei fonturi DejaVu instalate
        font_titlu = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_subtitlu = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
        font_text = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    except:
        font_titlu = ImageFont.load_default()
        font_subtitlu = ImageFont.load_default()
        font_text = ImageFont.load_default()

    # 4. Scriem conținutul
    # Titlu
    draw.text((80, 120), "FISA TEHNICA:", fill=albastru_
