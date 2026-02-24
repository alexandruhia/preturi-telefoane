import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Pro Configurator", layout="wide")

# CSS pentru aspect profesional și text de reglaje mărit
st.markdown("""
    <style>
    [data-testid="column"] { padding: 0px !important; margin: 0px !important; }
    .stSelectbox label { display:none; }
    /* Mărire text în interiorul expander-ului de reglaje */
    .stSlider label, .stSelectbox label, .stNumberInput label, .stRadio label {
        font-size: 1.2rem !important;
        font-weight: bold !important;
    }
    div.stButton > button { width: 100%; height: 3em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- LISTĂ FONTURI ---
FONT_LIST = ["Roboto", "Open Sans", "Lato", "Montserrat", "Oswald", "Raleway", "Ubuntu", "Bebas Neue", "Lobster", "Dancing Script", "Caveat"]

@st.cache_data
def get_google_font(font_name, weight="Regular"):
    url = f"https://github.com/google/fonts/raw/main/ofl/{font_name.lower().replace(' ', '')}/{font_name}-{weight}.ttf"
    try:
        response = requests.get(url)
        if response.status_code == 200: return io.BytesIO(response.content)
    except: pass
    return None

def creeaza_imagine_eticheta(row, font_size, line_spacing, l_scale, l_x_manual, l_y, font_name, font_style):
    W, H = 800, 1200
    rosu_express = (204, 9, 21)
    albastru_text = (0, 51, 102)
    img = Image.new('RGB', (W, H), color=rosu_express)
    draw = ImageDraw.Draw(img)
    margine = 40
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=60, fill="white")

    font_data = get_google_font(font_name, font_style)
    try:
        if font_data:
            f_titlu = ImageFont.truetype(font_data, int(font_size * 1.2))
            font_data.seek(0)
            f_valoare = ImageFont.truetype(font_data, font_size)
            bold_data = get_google_font(font_name, "Bold") or font_data
            f_label = ImageFont.truetype(bold_data, font_size)
        else: raise Exception()
    except: f_titlu = f_label = f_valoare = ImageFont.load_default()

    # Centrare Nume Model
    txt_model = f"{row['Brand']} {row['Model']}"
    w_tm = draw.textlength(txt_model, font=f_titlu)
    draw.text(((W - w_tm) // 2, margine * 3.5), txt_model, fill=albastru_text, font=f_titlu)

    # Specificații
    y_pos = margine * 7.0
    specs = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Selfie", "Sanatate baterie", "Capacitate baterie"]
    
    for col in specs:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            draw.text((margine * 2, y_pos), f"{col}:", fill="black", font=f_label)
            offset = draw.textlength(f"{col}: ", font=f_label)
            draw.text((margine * 2 + offset, y_pos), val, fill="black", font=f_valoare)
            y_pos += line_spacing

    # Logo centrat sau manual
    try:
        url_logo = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo = Image.open(io.BytesIO(requests.get(url_logo).content)).convert("RGBA")
        lw = int(W * l_scale)
        lh = int(lw * (logo.size[1] / logo.size[0]))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        x_f = (W - lw) // 2 if l_x_manual == 100 else l_x_manual
        img.paste(logo, (x_f, l_y), logo)
    except: pass
    return img

# --- LOGICĂ APLICAȚIE ---
try:
    df = pd.read_excel("https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx")
except:
    st.error("Eroare la încărcarea Excel-ului.")
    st.stop()

st.sidebar.header("🔍 Control Vizual")
zoom = st.sidebar.slider("Lățime previzualizare (px)", 150, 800, 350)

col1, col2, col3 = st.columns(3)
cols = [col1, col2, col3]
reglaje = []

for i in range(3):
    with cols[i]:
        # Dropdowns
        brand = st.selectbox(f"B{i}", sorted(df['Brand'].dropna().unique()), key=f"b_{i}")
        model = st.selectbox(f"M{i}", df[df['Brand'] == brand]['Model'].dropna().unique(), key=f"m_{i}")
        row_data = df[(df['Brand'] == brand) & (df['Model'] == model)].iloc[0]
        
        # Panou reglaje - lățimea se adaptează la coloană
        with st.expander("🔧 SETĂRI ETICHETĂ", expanded=False):
            fn = st.selectbox("Font", sorted(FONT_LIST), key=f"fn_{i}")
            fs = st.selectbox("Stil", ["Regular", "Bold", "Italic", "BoldItalic"], key=f"fst_{i}")
            size = st.slider("Mărime Font (pt)", 10, 150, 25, key=f"sz_{i}")
            sp = st.slider("Spațiu Rânduri", 10, 100, 35, key=f"sp_{i}")
            ls = st.slider("Scară Logo", 0.1, 1.5, 0.7, key=f"ls_{i}")
            lx = st.number_input("X (100=Centru)", 0, 800, 100, key=f"lx_{i}")
            ly = st.number_input("Y Logo", 0, 1200, 1050, key=f"ly_{i}")

        img = creeaza_imagine_eticheta(row_data, size, sp, ls, lx, ly, fn, fs)
        st.image(img, width=zoom)
        reglaje.append({'img': img})

st.divider()
if st.button("🚀 DESCARCĂ PDF FINAL (3 ETICHETE)"):
    canvas = Image.new('RGB', (2400, 1200))
    for i in range(3): canvas.paste(reglaje[i]['img'], (i * 800, 0))
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    buf = io.BytesIO()
    canvas.save(buf, format='PNG')
    buf.seek(0)
    with open("temp.png", "wb") as f: f.write(buf.read())
    pdf.image("temp.png", x=5, y=5, w=287)
    st.download_button("💾 SALVEAZĂ PDF", pdf.output(dest='S').encode('latin-1'), "Etichete.pdf", "application/pdf")
