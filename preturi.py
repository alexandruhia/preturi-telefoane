import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Configurator Etichete", layout="wide")

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

# --- FUNCȚIE GENERARE ETICHETĂ CU LOGO PNG ---
def genereaza_eticheta_imagine(row, font_size, line_spacing, zoom_level):
    W = int(800 * zoom_level)
    H = int(1200 * zoom_level)
    rosu_express = (204, 9, 21)
    albastru_text = (0, 51, 102)
    
    img = Image.new('RGB', (W, H), color=rosu_express)
    draw = ImageDraw.Draw(img)

    # 1. Cardul alb
    margine = int(40 * zoom_level)
    draw.rounded_rectangle([margine, margine, W-margine, H-int(180*zoom_level)], 
                           radius=int(60*zoom_level), fill="white")

    # 2. Setare fonturi
    try:
        f_path_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        f_path_reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        f_titlu = ImageFont.truetype(f_path_bold, int(font_size * 1.2 * zoom_level))
        f_bold = ImageFont.truetype(f_path_bold, int(font_size * zoom_level))
        f_normal = ImageFont.truetype(f_path_reg, int(font_size * zoom_level))
    except:
        f_titlu = f_bold = f_normal = ImageFont.load_default()

    # 3. Titlu
    draw.text((margine*2, margine*2.5), "FISA TEHNICA:", fill=albastru_text, font=f_titlu)
    draw.text((margine*2, margine*2.5 + int(65*zoom_level)), f"{row['Brand']} {row['Model']}", fill=albastru_text, font=f_titlu)

    # 4. Specificații (Bold pt. Nume, Normal pt. Valoare)
    y_pos = margine * 6.5
    spec_liste = ["Display", "OS", "Procesor", "Stocare", "RAM", "Capacitate baterie"]
    
    for col in spec_liste:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            draw.text((margine*2, y_pos), f"{col}:", fill="black", font=f_bold)
            latime_label = draw.textlength(f"{col}: ", font=f_bold)
            draw.text((margine*2 + latime_label, y_pos), val, fill="black", font=f_normal)
            y_pos += int(line_spacing * zoom_level)

    # 5. INSERARE LOGO PNG ÎN SUBSOL
    try:
        # Folosim URL-ul imaginii tale (link direct)
        url_logo = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        response = requests.get(url_logo)
        logo = Image.open(io.BytesIO(response.content)).convert("RGBA")
        
        # Redimensionăm logo-ul să fie cam 60% din lățimea etichetei
        logo_w = int(W * 0.6)
        aspect_ratio = logo.size[1] / logo.size[0]
        logo_h = int(logo_w * aspect_ratio)
        logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
        
        # Îl centrăm jos în zona roșie
        x_logo = (W - logo_w) // 2
        y_logo = H - logo_h - int(40 * zoom_level)
        
        # Lipim logo-ul (folosind el însuși ca mască pentru transparență)
        img.paste(logo, (x_logo, y_logo), logo)
    except Exception as e:
        # Dacă logo-ul nu se încarcă, scriem textul ca rezervă
        draw.text((W//4, H - int(100*zoom_level)), "ExpressCredit AMANET", fill="white", font=f_bold)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

# --- INTERFAȚA ---
st.title("🎨 Configurator Etichete ExpressCredit")
df = incarca_date()

if df is not None:
    st.sidebar.header("⚙️ Reglaje Design")
    zoom_ref = st.sidebar.slider("Zoom imagine", 0.5, 2.0, 1.0, 0.1)
    font_ref = st.sidebar.slider("Mărime scris", 20, 60, 35)
    spatiere_ref = st.sidebar.slider("Distanța între rânduri", 30, 100, 50)

    col1, col2 = st.columns(2)
    with col1:
        brand_sel = st.selectbox("Alege Brand:", sorted(df['Brand'].dropna().unique()))
    with col2:
        modele = df[df['Brand'] == brand_sel]['Model'].dropna().unique()
        model_sel = st.selectbox("Alege Model:", modele)

    date_tel = df[(df['Brand'] == brand_sel) & (df['Model'] == model_sel)].iloc[0]
    st.divider()

    img_bytes = genereaza_eticheta_imagine(date_tel, font_ref, spatiere_ref, zoom_ref)
    
    col_prev, col_info = st.columns([1, 1])
    with col_prev:
        st.subheader("🖼️ Previzualizare")
        st.image(img_bytes, use_container_width=False, width=int(400 * zoom_ref))
    with col_info:
        st.subheader("📥 Acțiuni")
        st.download_button(label="💾 Descarcă Eticheta", data=img_bytes, file_name=f"Eticheta_{model_sel}.png", mime="image/png")
