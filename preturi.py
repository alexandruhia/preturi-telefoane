import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io

# Configurare pagină
st.set_page_config(page_title="ExpressCredit Amanet - Etichete", page_icon="📱")

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
        st.error(f"Eroare la încărcarea datelor: {e}")
        return None

# --- FUNCȚIE GENERARE ETICHETĂ ---
def genereaza_eticheta_imagine(row):
    # Dimensiuni imagine
    W, H = 800, 1200
    rosu_express = (204, 9, 21)
    albastru_text = (0, 51, 102)
    
    # 1. Creăm fundalul roșu
    img = Image.new('RGB', (W, H), color=rosu_express)
    draw = ImageDraw.Draw(img)

    # 2. Cardul alb cu colțuri rotunjite
    draw.rounded_rectangle([40, 40, 760, 1050], radius=60, fill="white")

    # 3. Setare fonturi (Default pentru siguranță pe server)
    try:
        f_titlu = ImageFont.load_default() # Pe server vom folosi variantele default dacă nu sunt fonturi TTF
        f_text = ImageFont.load_default()
    except:
        f_titlu = ImageFont.load_default()
        f_text = ImageFont.load_default()

    # 4. Scriem textul
    draw.text((80, 120), "FISA TEHNICA:", fill=albastru_text, font=f_titlu)
    draw.text((80, 180), f"{row['Brand']} {row['Model']}", fill=albastru_text, font=f_titlu)

    # Specificații
    y_pos = 300
    spec_liste = ["Display", "OS", "Procesor", "Stocare", "RAM", "Capacitate baterie"]
    
    for col in spec_liste:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            draw.text((80, y_pos), f"{col}: {val}", fill="black", font=f_text)
            y_pos += 60

    # 5. Branding jos
    draw.text((150, 1080), "ExpressCredit", fill="white", font=f_titlu)
    draw.text((150, 1130), "AMANET", fill="white", font=f_text)

    # Export bytes
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

# --- INTERFAȚA ---
st.title("📱 Generator Etichete ExpressCredit")
df = incarca_date()

if df is not None:
    branduri = sorted(df['Brand'].dropna().unique())
    brand_sel = st.selectbox("Alege Brand:", branduri)
    
    modele = df[df['Brand'] == brand_sel]['Model'].dropna().unique()
    model_sel = st.selectbox("Alege Model:", modele)

    date_tel = df[(df['Brand'] == brand_sel) & (df['Model'] == model_sel)].iloc[0]

    if st.button("✨ Generează Eticheta"):
        img_bytes = genereaza_eticheta_imagine(date_tel)
        st.image(img_bytes, use_container_width=True)
        st.download_button("💾 Descarcă Imaginea", img_bytes, f"{model_sel}.png", "image/png")
