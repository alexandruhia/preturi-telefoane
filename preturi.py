import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Workstation", layout="wide")

# CSS pentru a lipi coloanele și a ascunde label-urile inutile
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
    # Card alb
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

    # Toate specificațiile
    y_pos = margine * 6.5
    specs = [
        "Display", "OS", "Procesor", "Stocare", "RAM", 
        "Camera principala", "Selfie", "Sanatate baterie", "Capacitate baterie"
    ]
    
    for col in specs:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            draw.text((margine*2, y_pos), f"{col}:", fill="black", font=f_bold)
            offset = draw.textlength(f"{col}: ", font=f_bold)
            draw.text((margine*2 + offset, y_pos), val, fill="black", font=f_normal)
            y_pos += line_spacing

    # Inserare Logo
    try:
        url_logo = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo_res = requests.get(url_logo)
        logo = Image.open(io.BytesIO(logo_res.content)).convert("RGBA")
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

    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]
    
    date_etichete = []
    reglaje_etichete = []

    for i in range(3):
        with cols[i]:
            # Selectoare
            brand_list = sorted(df['Brand'].dropna().unique())
            brand = st.selectbox(f"Select Brand {i}", brand_list, key=f"b_{i}")
            
            modele_list = df[df['Brand'] == brand]['Model'].dropna().unique()
            model = st.selectbox(f"Select Model {i}", modele_list, key=f"m_{i}")
            
            row_data = df[(df['Brand'] == brand) & (df['Model'] == model)].iloc[0]
            
            with st.expander("⚙️ Reglaje"):
                fs = st.slider("Font", 15, 50, 24, key=f"fs_{i}")
                ls = st.slider("Spațiu", 15, 80, 32, key=f"ls_{i}")
                sc = st.slider("Logo", 0.1, 1.2, 0.7, key=f"lsc_{i}")
                lx = st.number_input("X", 0, 800, 100, key=f"lx_{i}")
                ly = st.number_input("Y", 0, 1200, 1080, key=f"ly_{i}")
            
            date_etichete.append(row_data)
            reglaje_etichete.append({'fs': fs, 'ls': ls, 'lsc': sc, 'lx': lx, 'ly': ly})

            # Generare și Afișare
            img_final = creeaza_imagine_eticheta(row_data, fs, ls, sc, lx, ly)
            st.image(img_final, width=zoom_val)
            reglaje_etichete[i]['img'] = img_final

    # --- BUTON PDF ---
    st.divider()
    if st.button("🚀 GENEREAZĂ PDF FINAL"):
        final_canvas = Image.new('RGB', (2400, 1200))
        for i in range(3):
            final_canvas.paste(reglaje_etichete[i]['img'], (i * 800, 0))

        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        img_buf = io.BytesIO()
        final_canvas.save(img_buf, format='PNG')
        img_buf.seek(0)
        
        with open("print_temp.png", "wb") as f:
            f.write(img_buf.read())
        
        pdf.image("print_temp.png", x=5, y=5, w=287)
        pdf_data = pdf.output(dest='S').encode('latin-1')
        
        st.download_button(
            label="💾 DESCARCĂ PDF",
            data=pdf_data,
            file_name="Etichete_Complet.pdf",
            mime="application/pdf"
        )
