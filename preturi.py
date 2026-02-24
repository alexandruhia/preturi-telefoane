import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Workstation Pro Custom", layout="wide")

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

# --- FUNCȚIE GENERARE ETICHETĂ ---
def creeaza_imagine_eticheta(row, font_size, line_spacing, l_scale, l_x_manual, l_y, font_type, font_style):
    W, H = 800, 1200
    rosu_express = (204, 9, 21)
    albastru_text = (0, 51, 102)
    img = Image.new('RGB', (W, H), color=rosu_express)
    draw = ImageDraw.Draw(img)
    margine = 40
    
    # Card alb central
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=60, fill="white")

    # Logica de selecție a fontului în funcție de stil
    # Mapare pentru fonturile DejaVu (standard pe majoritatea sistemelor Linux/Streamlit Cloud)
    font_map = {
        "DejaVuSans": {
            "Regular": "DejaVuSans.ttf",
            "Bold": "DejaVuSans-Bold.ttf",
            "Italic": "DejaVuSans-Oblique.ttf",
            "Bold Italic": "DejaVuSans-BoldOblique.ttf"
        },
        "DejaVuSerif": {
            "Regular": "DejaVuSerif.ttf",
            "Bold": "DejaVuSerif-Bold.ttf",
            "Italic": "DejaVuSerif-Italic.ttf",
            "Bold Italic": "DejaVuSerif-BoldItalic.ttf"
        }
    }

    try:
        base_path = "/usr/share/fonts/truetype/dejavu/"
        f_file = font_map[font_type][font_style]
        f_bold_file = font_map[font_type]["Bold"] # Folosit pentru etichete (Display, RAM, etc.)
        
        f_titlu = ImageFont.truetype(base_path + f_bold_file, int(font_size * 1.3))
        f_label = ImageFont.truetype(base_path + f_bold_file, font_size)
        f_valoare = ImageFont.truetype(base_path + f_file, font_size)
    except:
        f_titlu = f_label = f_valoare = ImageFont.load_default()

    # --- CENTRARE NUME MODEL ---
    txt_model = f"{row['Brand']} {row['Model']}"
    w_tm = draw.textlength(txt_model, font=f_titlu)
    draw.text(((W - w_tm) // 2, margine * 3.5), txt_model, fill=albastru_text, font=f_titlu)

    # --- SPECIFICAȚII ---
    y_pos = margine * 7.0
    specs = [
        "Display", "OS", "Procesor", "Stocare", "RAM", 
        "Camera principala", "Selfie", "Sanatate baterie", "Capacitate baterie"
    ]
    
    for col in specs:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            # Eticheta coloanei (mereu Bold pentru contrast)
            draw.text((margine * 2, y_pos), f"{col}:", fill="black", font=f_label)
            offset = draw.textlength(f"{col}: ", font=f_label)
            # Valoarea coloanei (stilul ales de utilizator)
            draw.text((margine * 2 + offset, y_pos), val, fill="black", font=f_valoare)
            y_pos += line_spacing

    # --- CENTRARE LOGO ---
    try:
        url_logo = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo_res = requests.get(url_logo)
        logo = Image.open(io.BytesIO(logo_res.content)).convert("RGBA")
        lw = int(W * l_scale)
        lh = int(lw * (logo.size[1] / logo.size[0]))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        x_final = (W - lw) // 2 if l_x_manual == 100 else l_x_manual
        img.paste(logo, (x_final, l_y), logo)
    except: pass
        
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
            
            with st.expander("⚙️ Stil & Poziție"):
                # Stil Font
                f_type = st.radio("Tip Font", ["DejaVuSans", "DejaVuSerif"], key=f"ft_{i}", horizontal=True)
                f_style = st.selectbox("Stil Valori", ["Regular", "Bold", "Italic", "Bold Italic"], key=f"fst_{i}")
                
                # Dimensiuni
                fs = st.slider("Mărime Font", 15, 45, 25, key=f"fs_{i}")
                ls = st.slider("Spațiu Linii", 15, 60, 32, key=f"ls_{i}")
                
                # Logo
                sc = st.slider("Scară Logo", 0.1, 1.2, 0.7, key=f"lsc_{i}")
                lx = st.number_input("X (100=Centru)", 0, 800, 100, key=f"lx_{i}")
                ly = st.number_input("Y", 0, 1200, 1080, key=f"ly_{i}")
            
            date_etichete.append(row_data)
            reglaje_etichete.append({'fs': fs, 'ls': ls, 'lsc': sc, 'lx': lx, 'ly': ly, 'ft': f_type, 'fst': f_style})

            img_res = creeaza_imagine_eticheta(row_data, fs, ls, sc, lx, ly, f_type, f_style)
            st.image(img_res, width=zoom_preview)
            reglaje_etichete[i]['img'] = img_res

    st.divider()
    if st.button("🚀 GENEREAZĂ PDF FINAL"):
        final_canvas = Image.new('RGB', (2400, 1200))
        for i in range(3):
            final_canvas.paste(reglaje_etichete[i]['img'], (i * 800, 0))

        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        buf = io.BytesIO()
        final_canvas.save(buf, format='PNG')
        buf.seek(0)
        with open("temp_print.png", "wb") as f: f.write(buf.read())
        pdf.image("temp_print.png", x=5, y=5, w=287)
        
        st.download_button(
            label="💾 DESCARCĂ PDF",
            data=pdf.output(dest='S').encode('latin-1'),
            file_name="Etichete_Express_Custom.pdf",
            mime="application/pdf"
        )
