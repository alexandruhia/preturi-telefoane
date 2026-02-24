import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Configurator Avansat", layout="wide")

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
def genereaza_eticheta_imagine(row, font_size, line_spacing, zoom_level, logo_scale, logo_x_off, logo_y_off):
    # Dimensiuni bază (ajustate de Zoom)
    W = int(800 * zoom_level)
    H = int(1200 * zoom_level)
    rosu_express = (204, 9, 21)
    albastru_text = (0, 51, 102)
    
    img = Image.new('RGB', (W, H), color=rosu_express)
    draw = ImageDraw.Draw(img)

    # 1. Cardul alb (fundalul pentru specificații)
    margine = int(40 * zoom_level)
    draw.rounded_rectangle([margine, margine, W-margine, H-int(220 * zoom_level)], 
                           radius=int(60 * zoom_level), fill="white")

    # 2. Setare fonturi
    try:
        f_path_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        f_path_reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        f_titlu = ImageFont.truetype(f_path_bold, int(font_size * 1.2 * zoom_level))
        f_bold = ImageFont.truetype(f_path_bold, int(font_size * zoom_level))
        f_normal = ImageFont.truetype(f_path_reg, int(font_size * zoom_level))
    except:
        f_titlu = f_bold = f_normal = ImageFont.load_default()

    # 3. Titluri
    draw.text((margine*2, margine*2.5), "FISA TEHNICA:", fill=albastru_text, font=f_titlu)
    draw.text((margine*2, margine*2.5 + int(65*zoom_level)), f"{row['Brand']} {row['Model']}", fill=albastru_text, font=f_titlu)

    # 4. Specificații (Mix Bold/Normal)
    y_pos = margine * 6.5
    spec_liste = ["Display", "OS", "Procesor", "Stocare", "RAM", "Capacitate baterie"]
    
    for col in spec_liste:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            draw.text((margine*2, y_pos), f"{col}:", fill="black", font=f_bold)
            offset = draw.textlength(f"{col}: ", font=f_bold)
            draw.text((margine*2 + offset, y_pos), val, fill="black", font=f_normal)
            y_pos += int(line_spacing * zoom_level)

    # 5. INSERARE LOGO CU COORDONATE X/Y REGLABILE
    try:
        url_logo = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        response = requests.get(url_logo)
        logo = Image.open(io.BytesIO(response.content)).convert("RGBA")
        
        # Redimensionare logo
        logo_w = int(W * logo_scale)
        aspect_ratio = logo.size[1] / logo.size[0]
        logo_h = int(logo_w * aspect_ratio)
        logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
        
        # Coordonatele vin din slidere (ajustate automat cu zoom)
        # Coordonata X: 0 este stânga, W-logo_w este maxim dreapta
        pos_x = int(logo_x_off * zoom_level)
        # Coordonata Y: 0 este sus, H-logo_h este maxim jos
        pos_y = int(logo_y_off * zoom_level)
        
        img.paste(logo, (pos_x, pos_y), logo)
    except:
        draw.text((W//2 - 100, H - 100), "LOGO NEGASIT", fill="white", font=f_bold)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

# --- INTERFAȚĂ ---
st.title("🎨 ExpressCredit - Control Total Design")
df = incarca_date()

if df is not None:
    # --- SIDEBAR PENTRU CONTROL ---
    st.sidebar.header("⚙️ Setări Aspect")
    zoom_ref = st.sidebar.slider("Zoom Pagină", 0.5, 2.5, 1.0, 0.1)
    font_ref = st.sidebar.slider("Mărime Font", 20, 80, 35)
    spatiere_ref = st.sidebar.slider("Distanță Rânduri", 20, 100, 45)
    
    st.sidebar.divider()
    st.sidebar.header("🖼️ Control Logo")
    l_scale = st.sidebar.slider("Scalare Logo", 0.1, 1.2, 0.7, 0.05)
    # Slidere pentru coordonate (X între 0 și 800, Y între 0 și 1200)
    l_x = st.sidebar.slider("Poziție Logo X (Orizontal)", 0, 800, 100)
    l_y = st.sidebar.slider("Poziție Logo Y (Vertical)", 0, 1200, 1080)

    # --- SELECȚIE DATE ---
    c1, c2 = st.columns(2)
    with c1:
        brand_sel = st.selectbox("Brand:", sorted(df['Brand'].dropna().unique()))
    with c2:
        modele = df[df['Brand'] == brand_sel]['Model'].dropna().unique()
        model_sel = st.selectbox("Model:", modele)

    date_tel = df[(df['Brand'] == brand_sel) & (df['Model'] == model_sel)].iloc[0]
    st.divider()

    # --- GENERARE ȘI PREVIEW ---
    img_bytes = genereaza_eticheta_imagine(date_tel, font_ref, spatiere_ref, zoom_ref, l_scale, l_x, l_y)
    
    col_p, col_a = st.columns([1.5, 1])
    with col_p:
        st.subheader("🖼️ Previzualizare")
        st.image(img_bytes, width=int(400 * zoom_ref))
    with col_a:
        st.subheader("📥 Export")
        st.download_button(
            label="💾 Descarcă Eticheta", 
            data=img_bytes, 
            file_name=f"Eticheta_{model_sel}.png", 
            mime="image/png"
        )
