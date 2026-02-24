import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Pro Fix", layout="wide")

# CSS pentru panou de reglaje GIGANT
st.markdown("""
    <style>
    [data-testid="column"] { padding: 5px !important; }
    .stSlider label, .stSelectbox label, .stNumberInput label {
        font-size: 22px !important;
        font-weight: 900 !important;
        color: #000 !important;
    }
    div.stButton > button { height: 4em; font-size: 20px !important; background-color: #cc0915; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- LISTĂ FONTURI ---
FONT_URLS = {
    "Roboto": "https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-",
    "Montserrat": "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-",
    "Bebas Neue": "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-",
    "Lobster": "https://github.com/google/fonts/raw/main/ofl/lobster/Lobster-",
    "Anton": "https://github.com/google/fonts/raw/main/ofl/anton/Anton-",
    "Pacifico": "https://github.com/google/fonts/raw/main/ofl/pacifico/Pacifico-",
    "Oswald": "https://github.com/google/fonts/raw/main/ofl/oswald/Oswald-",
    "Caveat": "https://github.com/google/fonts/raw/main/ofl/caveat/Caveat-"
}

@st.cache_data(show_spinner=False)
def download_font(font_name, weight):
    base_url = FONT_URLS.get(font_name)
    if not base_url: return None
    try:
        r = requests.get(f"{base_url}{weight}.ttf", timeout=5)
        if r.status_code == 200: return r.content
    except: pass
    return None

def creeaza_imagine_eticheta(row, font_size, line_spacing, l_scale, l_x_manual, l_y, font_name, font_style):
    W, H = 800, 1200
    img = Image.new('RGB', (W, H), color=(204, 9, 21))
    draw = ImageDraw.Draw(img)
    margine = 40
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=60, fill="white")

    # Încărcare font cu RESET de cursor pentru fiecare etichetă
    f_bytes = download_font(font_name, font_style)
    f_bold_bytes = download_font(font_name, "Bold") or f_bytes
    
    try:
        if f_bytes:
            # Creăm fonturi separate folosind BytesIO proaspăt la fiecare rulare
            f_titlu = ImageFont.truetype(io.BytesIO(f_bold_bytes), int(font_size * 1.3))
            f_label = ImageFont.truetype(io.BytesIO(f_bold_bytes), font_size)
            f_valoare = ImageFont.truetype(io.BytesIO(f_bytes), font_size)
        else:
            path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            f_titlu = ImageFont.truetype(path, int(font_size * 1.3))
            f_label = ImageFont.truetype(path, font_size)
            f_valoare = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except:
        f_titlu = f_label = f_valoare = ImageFont.load_default()

    # Model
    txt_m = f"{row['Brand']} {row['Model']}"
    w_m = draw.textlength(txt_m, font=f_titlu)
    draw.text(((W - w_m) // 2, margine * 3), txt_m, fill=(0, 51, 102), font=f_titlu)

    # Specificații
    y_pos = margine * 7.5
    specs = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Selfie", "Sanatate baterie", "Capacitate baterie"]
    for col in specs:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            draw.text((margine * 2, y_pos), f"{col}:", fill="black", font=f_label)
            offset = draw.textlength(f"{col}: ", font=f_label)
            draw.text((margine * 2 + offset, y_pos), val, fill="black", font=f_valoare)
            y_pos += line_spacing

    # Logo
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

# --- INTERFAȚĂ ---
try:
    df = pd.read_excel("https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx")
except:
    st.error("Excel unreachable.")
    st.stop()

st.sidebar.header("🔍 ZOOM")
zoom = st.sidebar.slider("Lățime (px)", 200, 1000, 400)

col1, col2, col3 = st.columns(3)
cols = [col1, col2, col3]
imgs = []

for i in range(3):
    with cols[i]:
        b = st.selectbox(f"Brand {i+1}", sorted(df['Brand'].dropna().unique()), key=f"b_{i}")
        m = st.selectbox(f"Model {i+1}", df[df['Brand'] == b]['Model'].dropna().unique(), key=f"m_{i}")
        r_data = df[(df['Brand'] == b) & (df['Model'] == m)].iloc[0]
        
        with st.expander("⚙️ REGLAJE", expanded=True):
            fn = st.selectbox("FONT", list(FONT_URLS.keys()), key=f"fn_{i}")
            fs = st.selectbox("STIL", ["Regular", "Bold", "Italic"], key=f"fst_{i}")
            size = st.slider("MĂRIME FONT", 10, 150, 30, key=f"sz_{i}")
            sp = st.slider("SPAȚIU RÂNDURI", 10, 150, 40, key=f"sp_{i}")
            ls = st.slider("SCARĂ LOGO", 0.1, 2.0, 0.7, key=f"ls_{i}")
            lx = st.number_input("X Logo (100=Centru)", 0, 800, 100, key=f"lx_{i}")
            ly = st.number_input("Y Logo", 0, 1200, 1050, key=f"ly_{i}")

        res_img = creeaza_imagine_eticheta(r_data, size, sp, ls, lx, ly, fn, fs)
        st.image(res_img, width=zoom)
        imgs.append(res_img)

if st.button("🚀 PDF FINAL"):
    final = Image.new('RGB', (2400, 1200))
    for i in range(3): final.paste(imgs[i], (i * 800, 0))
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    buf = io.BytesIO()
    final.save(buf, format='PNG')
    buf.seek(0)
    with open("temp.png", "wb") as f: f.write(buf.read())
    pdf.image("temp.png", x=5, y=5, w=287)
    st.download_button("💾 DOWNLOAD PDF", pdf.output(dest='S').encode('latin-1'), "Etichete.pdf", "application/pdf")
