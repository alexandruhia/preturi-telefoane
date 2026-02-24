import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Multi-Generator Compact", layout="wide")

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
def creeaza_imagine_eticheta(row, font_size, line_spacing, l_scale, l_x, l_y):
    W, H = 800, 1200
    rosu_express = (204, 9, 21)
    albastru_text = (0, 51, 102)
    
    img = Image.new('RGB', (W, H), color=rosu_express)
    draw = ImageDraw.Draw(img)
    margine = 40
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=60, fill="white")

    try:
        f_path_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        f_path_reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        f_titlu = ImageFont.truetype(f_path_bold, int(font_size * 1.2))
        f_bold = ImageFont.truetype(f_path_bold, font_size)
        f_normal = ImageFont.truetype(f_path_reg, font_size)
    except:
        f_titlu = f_bold = f_normal = ImageFont.load_default()

    draw.text((margine*2, margine*2.5), "FISA TEHNICA:", fill=albastru_text, font=f_titlu)
    draw.text((margine*2, margine*2.5 + 65), f"{row['Brand']} {row['Model']}", fill=albastru_text, font=f_titlu)

    y_pos = margine * 6.5
    spec_liste = ["Display", "OS", "Procesor", "Stocare", "RAM", "Capacitate baterie"]
    for col in spec_liste:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            draw.text((margine*2, y_pos), f"{col}:", fill="black", font=f_bold)
            offset = draw.textlength(f"{col}: ", font=f_bold)
            draw.text((margine*2 + offset, y_pos), val, fill="black", font=f_normal)
            y_pos += line_spacing

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
st.title("📱 Multi-Generator ExpressCredit")

# --- BUTON ZOOM GLOBAL ---
st.sidebar.header("🔍 Vizibilitate Interfață")
zoom_preview = st.sidebar.slider("Zoom Previzualizare (px)", 150, 600, 300, help="Micsorează sau mărește doar ce vezi pe ecran.")

df = incarca_date()

if df is not None:
    cols = st.columns(3)
    date_etichete = []
    reglaje_etichete = []

    for i in range(3):
        with cols[i]:
            brand = st.selectbox(f"Brand {i+1}", sorted(df['Brand'].dropna().unique()), key=f"b_{i}")
            modele = df[df['Brand'] == brand]['Model'].dropna().unique()
            model = st.selectbox(f"Model {i+1}", modele, key=f"m_{i}")
            row_data = df[(df['Brand'] == brand) & (df['Model'] == model)].iloc[0]
            
            with st.expander(f"⚙️ Reglaje E{i+1}"):
                f_size = st.slider("Font", 20, 60, 32, key=f"fs_{i}")
                l_space = st.slider("Rânduri", 20, 80, 40, key=f"ls_{i}")
                l_sc = st.slider("Logo Scara", 0.1, 1.2, 0.7, key=f"lsc_{i}")
                l_x = st.number_input("X", 0, 800, 100, key=f"lx_{i}")
                l_y = st.number_input("Y", 0, 1200, 1080, key=f"ly_{i}")
            
            date_etichete.append(row_data)
            reglaje_etichete.append({'fs': f_size, 'ls': l_space, 'lsc': l_sc, 'lx': l_x, 'ly': l_y})

    st.divider()

    # --- ZONA DE PREVIEW CONTROLATĂ DE ZOOM ---
    # Generăm imaginile
    imagini_finale = []
    for i in range(3):
        img = creeaza_imagine_eticheta(
            date_etichete[i], 
            reglaje_etichete[i]['fs'], 
            reglaje_etichete[i]['ls'], 
            reglaje_etichete[i]['lsc'], 
            reglaje_etichete[i]['lx'], 
            reglaje_etichete[i]['ly']
        )
        imagini_finale.append(img)

    # Afișare cu Zoom Controlat
    preview_cols = st.columns(3)
    for i in range(3):
        # Folosim parametrul width pentru a forța dimensiunea vizuală cerută de slider
        preview_cols[i].image(imagini_finale[i], width=zoom_preview, caption=f"Eticheta {i+1}")

    # --- BUTON PRINT ---
    st.divider()
    if st.button("🚀 GENEREAZĂ PDF FINAL (3 ETICHETE)", use_container_width=True):
        final_w = 800 * 3
        canvas = Image.new('RGB', (final_w, 1200))
        for i in range(3):
            canvas.paste(imagini_finale[i], (i * 800, 0))

        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        img_buf = io.BytesIO()
        canvas.save(img_buf, format='PNG')
        img_buf.seek(0)
        with open("temp.png", "wb") as f: f.write(img_buf.read())
        pdf.image("temp.png", x=5, y=5, w=287)
        
        st.download_button(
            label="💾 DESCARCĂ PDF-ul",
            data=pdf.output(dest='S').encode('latin-1'),
            file_name="Etichete_Express.pdf",
            mime="application/pdf",
            use_container_width=True
        )
