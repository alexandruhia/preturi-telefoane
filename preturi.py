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

# --- FUNCȚIE GENERARE ETICHETĂ (CU CENTRARE) ---
def creeaza_imagine_eticheta(row, font_size, line_spacing, l_scale, l_x_manual, l_y):
    W, H = 800, 1200
    rosu_express = (204, 9, 21)
    albastru_text = (0, 51, 102)
    img = Image.new('RGB', (W, H), color=rosu_express)
    draw = ImageDraw.Draw(img)
    margine = 40
    
    # Desenare card alb central
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=60, fill="white")

    try:
        f_path_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        f_path_reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        f_titlu = ImageFont.truetype(f_path_bold, int(font_size * 1.2))
        f_bold = ImageFont.truetype(f_path_bold, font_size)
        f_normal = ImageFont.truetype(f_path_reg, font_size)
    except:
        f_titlu = f_bold = f_normal = ImageFont.load_default()

    # --- CENTRARE TITLURI ---
    txt1 = "FISA TEHNICA:"
    txt2 = f"{row['Brand']} {row['Model']}"
    
    w_t1 = draw.textlength(txt1, font=f_titlu)
    w_t2 = draw.textlength(txt2, font=f_titlu)
    
    draw.text(((W - w_t1) // 2, margine * 2.5), txt1, fill=albastru_text, font=f_titlu)
    draw.text(((W - w_t2) // 2, margine * 2.5 + 70), txt2, fill=albastru_text, font=f_titlu)

    # --- SPECIFICAȚII (Aliniate la stânga în interiorul blocului central) ---
    y_pos = margine * 6.5
    specs = [
        "Display", "OS", "Procesor", "Stocare", "RAM", 
        "Camera principala", "Selfie", "Sanatate baterie", "Capacitate baterie"
    ]
    
    for col in specs:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            # Păstrăm un padding mic la stânga (margine * 2)
            draw.text((margine * 2, y_pos), f"{col}:", fill="black", font=f_bold)
            offset = draw.textlength(f"{col}: ", font=f_bold)
            draw.text((margine * 2 + offset, y_pos), val, fill="black", font=f_normal)
            y_pos += line_spacing

    # --- CENTRARE LOGO ---
    try:
        url_logo = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo_res = requests.get(url_logo)
        logo = Image.open(io.BytesIO(logo_res.content)).convert("RGBA")
        
        lw = int(W * l_scale)
        lh = int(lw * (logo.size[1] / logo.size[0]))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        
        # Dacă X este lăsat la 100 (default), centrăm automat. Altfel, mutăm manual.
        x_final = (W - lw) // 2 if l_x_manual == 100 else l_x_manual
        img.paste(logo, (x_final, l_y), logo)
    except:
        pass
        
    return img

# --- INTERFAȚĂ UTILIZATOR ---
df = incarca_date()

if df is not None:
    st.sidebar.header("🔍 Vizibilitate")
    zoom_preview = st.sidebar.slider("Zoom Previzualizare (px)", 100, 600, 320)

    # 3 Coloane pentru 3 etichete simultane
    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]
    
    date_etichete = []
    reglaje_etichete = []

    for i in range(3):
        with cols[i]:
            # Selectoare fără label-uri
            b_list = sorted(df['Brand'].dropna().unique())
            brand = st.selectbox(f"B{i}", b_list, key=f"b_{i}")
            
            m_list = df[df['Brand'] == brand]['Model'].dropna().unique()
            model = st.selectbox(f"M{i}", m_list, key=f"m_{i}")
            
            row_data = df[(df['Brand'] == brand) & (df['Model'] == model)].iloc[0]
            
            with st.expander("⚙️ Ajustări"):
                fs = st.slider("Font", 15, 45, 25, key=f"fs_{i}")
                ls = st.slider("Spațiu", 15, 60, 32, key=f"ls_{i}")
                sc = st.slider("Logo", 0.1, 1.2, 0.7, key=f"lsc_{i}")
                lx = st.number_input("X (100=Centrat)", 0, 800, 100, key=f"lx_{i}")
                ly = st.number_input("Y", 0, 1200, 1080, key=f"ly_{i}")
            
            date_etichete.append(row_data)
            reglaje_etichete.append({'fs': fs, 'ls': ls, 'lsc': sc, 'lx': lx, 'ly': ly})

            # Generare și Afișare Lipită
            img_res = creeaza_imagine_eticheta(row_data, fs, ls, sc, lx, ly)
            st.image(img_res, width=zoom_preview)
            reglaje_etichete[i]['img'] = img_res

    # --- BUTON PRINT PDF ---
    st.divider()
    if st.button("🚀 GENEREAZĂ PDF FINAL (TOATE 3)"):
        # Unim cele 3 etichete într-o imagine mare (2400x1200)
        final_canvas = Image.new('RGB', (2400, 1200))
        for i in range(3):
            final_canvas.paste(reglaje_etichete[i]['img'], (i * 800, 0))

        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        
        # Buffer pentru imaginea unită
        buf = io.BytesIO()
        final_canvas.save(buf, format='PNG')
        buf.seek(0)
        
        with open("temp_print.png", "wb") as f:
            f.write(buf.read())
        
        # Plasare pe A4 Landscape
        pdf.image("temp_print.png", x=5, y=5, w=287)
        
        st.download_button(
            label="💾 DESCARCĂ PDF",
            data=pdf.output(dest='S').encode('latin-1'),
            file_name="Etichete_ExpressCredit.pdf",
            mime="application/pdf"
        )
