import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Pro Configurator", layout="wide")

# CSS pentru panou de reglaje GIGANT și vizibilitate maximă
st.markdown("""
    <style>
    [data-testid="column"] { padding: 5px !important; }
    /* Mărire text etichete reglaje */
    .stSlider label, .stSelectbox label, .stNumberInput label {
        font-size: 22px !important;
        font-weight: 800 !important;
        color: #1a1a1a !important;
    }
    /* Mărire butoane și selectoare */
    .stSelectbox div[data-baseweb="select"] { font-size: 18px !important; }
    div.stButton > button { height: 4em; font-size: 20px !important; background-color: #cc0915; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- LISTĂ FONTURI ---
FONT_LIST = ["Roboto", "Open Sans", "Montserrat", "Oswald", "Ubuntu", "Bebas Neue", "Lobster", "Caveat"]

@st.cache_data
def get_google_font(font_name, weight="Regular"):
    # Încercăm să luăm fontul de pe GitHub Google Fonts
    clean_name = font_name.replace(" ", "")
    url = f"https://github.com/google/fonts/raw/main/ofl/{clean_name.lower()}/{font_name}-{weight}.ttf"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200: return io.BytesIO(r.content)
    except: pass
    return None

def creeaza_imagine_eticheta(row, font_size, line_spacing, l_scale, l_x_manual, l_y, font_name, font_style):
    W, H = 800, 1200
    img = Image.new('RGB', (W, H), color=(204, 9, 21))
    draw = ImageDraw.Draw(img)
    margine = 40
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=60, fill="white")

    # Logica de încărcare font cu fallback
    f_data = get_google_font(font_name, font_style)
    try:
        if f_data:
            # Titlul este cu 20% mai mare decât fontul ales pentru specificații
            f_titlu = ImageFont.truetype(f_data, int(font_size * 1.2))
            f_data.seek(0)
            f_valoare = ImageFont.truetype(f_data, font_size)
            # Pentru etichete încercăm varianta Bold
            f_b_data = get_google_font(font_name, "Bold") or f_data
            f_label = ImageFont.truetype(f_b_data, font_size)
        else:
            # Fallback la fontul sistemului dacă Google Fonts e inaccesibil
            f_titlu = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(font_size * 1.2))
            f_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            f_valoare = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except:
        f_titlu = f_label = f_valoare = ImageFont.load_default()

    # Model telefon centrat
    txt_m = f"{row['Brand']} {row['Model']}"
    w_m = draw.textlength(txt_m, font=f_titlu)
    draw.text(((W - w_m) // 2, margine * 3), txt_m, fill=(0, 51, 102), font=f_titlu)

    # Specificații (Display, RAM, etc.)
    y_pos = margine * 7.5
    specs = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Selfie", "Sanatate baterie", "Capacitate baterie"]
    
    for col in specs:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            draw.text((margine * 2, y_pos), f"{col}:", fill="black", font=f_label)
            offset = draw.textlength(f"{col}: ", font=f_label)
            draw.text((margine * 2 + offset, y_pos), val, fill="black", font=f_valoare)
            y_pos += line_spacing

    # Logo centrat
    try:
        url_l = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo = Image.open(io.BytesIO(requests.get(url_l).content)).convert("RGBA")
        lw = int(W * l_scale)
        lh = int(lw * (logo.size[1] / logo.size[0]))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        x_f = (W - lw) // 2 if l_x_manual == 100 else l_x_manual
        img.paste(logo, (x_f, l_y), logo)
    except: pass
    return img

# --- APLICAȚIE ---
try:
    df = pd.read_excel("https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx")
except:
    st.error("Nu s-a putut încărca Excel-ul.")
    st.stop()

st.sidebar.header("🔍 ZOOM PREVIEW")
zoom = st.sidebar.slider("Mărime ecran (px)", 200, 1000, 400)

col1, col2, col3 = st.columns(3)
cols = [col1, col2, col3]
imgs_list = []

for i in range(3):
    with cols[i]:
        # Dropdowns selectare telefon
        brand = st.selectbox(f"Brand {i+1}", sorted(df['Brand'].dropna().unique()), key=f"b_{i}")
        model = st.selectbox(f"Model {i+1}", df[df['Brand'] == brand]['Model'].dropna().unique(), key=f"m_{i}")
        r_data = df[(df['Brand'] == brand) & (df['Model'] == model)].iloc[0]
        
        # Panou reglaje mărit
        with st.expander("⚙️ AJUSTĂRI MARI", expanded=True):
            fn = st.selectbox("Font", sorted(FONT_LIST), key=f"fn_{i}")
            fs = st.selectbox("Stil", ["Regular", "Bold", "Italic", "BoldItalic"], key=f"fst_{i}")
            # Mărime font până la 150pt
            size = st.slider("MĂRIME FONT", 10, 150, 30, key=f"sz_{i}")
            sp = st.slider("SPAȚIU RÂNDURI", 10, 150, 40, key=f"sp_{i}")
            ls = st.slider("SCARĂ LOGO", 0.1, 2.0, 0.7, key=f"ls_{i}")
            lx = st.number_input("X Logo (100=Centru)", 0, 800, 100, key=f"lx_{i}")
            ly = st.number_input("Y Logo", 0, 1200, 1050, key=f"ly_{i}")

        res_img = creeaza_imagine_eticheta(r_data, size, sp, ls, lx, ly, fn, fs)
        st.image(res_img, width=zoom)
        imgs_list.append(res_img)

st.divider()
if st.button("🚀 GENEREAZĂ PDF FINAL"):
    final = Image.new('RGB', (2400, 1200))
    for i in range(3): final.paste(imgs_list[i], (i * 800, 0))
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    buf = io.BytesIO()
    final.save(buf, format='PNG')
    buf.seek(0)
    with open("temp.png", "wb") as f: f.write(buf.read())
    pdf.image("temp.png", x=5, y=5, w=287)
    st.download_button("💾 DESCARCĂ PDF", pdf.output(dest='S').encode('latin-1'), "Etichete.pdf", "application/pdf")
