import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Mega Font", layout="wide")

# CSS pentru slidere vizibile
st.markdown("""<style>
    .stSlider label { font-size: 20px !important; color: #cc0915 !important; font-weight: bold !important; }
    div.stButton > button { height: 3em; background-color: #cc0915; color: white; font-weight: bold; }
</style>""", unsafe_allow_html=True)

# --- RESURSE FONT ---
@st.cache_data(show_spinner=False)
def get_font_raw():
    # Descărcăm fontul o singură dată
    url = "https://github.com/google/fonts/raw/main/ofl/opensans/static/OpenSans-Bold.ttf"
    return requests.get(url).content

def creeaza_imagine(row, fs, ls, l_sc, l_y, p_val, p_y, p_size):
    W, H = 800, 1200
    img = Image.new('RGB', (W, H), color=(204, 9, 21))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([40, 40, 760, 980], radius=60, fill="white")

    font_data = get_font_raw()
    
    # --- CREARE FONTURI (FĂRĂ CACHE - PENTRU REACȚIE IMEDIATĂ) ---
    try:
        f_titlu = ImageFont.truetype(io.BytesIO(font_data), 45)
        f_spec = ImageFont.truetype(io.BytesIO(font_data), int(fs))
        f_pret = ImageFont.truetype(io.BytesIO(font_data), int(p_size)) # Mărire activă la 500
    except:
        f_titlu = f_spec = f_pret = ImageFont.load_default()

    # 1. Titlu Model
    txt_m = f"{row['Brand']} {row['Model']}"
    draw.text(((W - draw.textlength(txt_m, font=f_titlu)) // 2, 110), txt_m, fill=(0, 51, 102), font=f_titlu)

    # 2. Specificații
    specs = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Sanatate baterie"]
    y_curr = 250
    for s in specs:
        if s in row and pd.notna(row[s]):
            draw.text((80, y_curr), f"{s}: {row[s]}", fill="black", font=f_spec)
            y_curr += ls

    # 3. PREȚ - Sliderul de 500 acționează aici
    if p_val:
        txt_p = f"Pret: {p_val} lei"
        w_p = draw.textlength(txt_p, font=f_pret)
        draw.text(((W - w_p) // 2, p_y), txt_p, fill=(204, 9, 21), font=f_pret)

    # 4. Logo
    try:
        l_url = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo = Image.open(io.BytesIO(requests.get(l_url).content)).convert("RGBA")
        lw = int(W * l_sc)
        lh = int(lw * (logo.size[1] / logo.size[0]))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(logo, ((W - lw) // 2, l_y), logo)
    except: pass

    return img

# --- LOGICĂ INTERFAȚĂ ---
try:
    df = pd.read_excel("https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx")
except:
    st.error("Eroare la încărcarea bazei de date.")
    st.stop()

cols = st.columns(3)
etichete = []

for i in range(3):
    with cols[i]:
        br = st.selectbox(f"Brand {i+1}", sorted(df['Brand'].unique()), key=f"br{i}")
        md = st.selectbox(f"Model {i+1}", df[df['Brand'] == br]['Model'].unique(), key=f"md{i}")
        r_data = df[(df['Brand'] == br) & (df['Model'] == md)].iloc[0]
        
        pret = st.text_input(f"Preț Telefon {i+1}", "1500", key=f"pr{i}")

        with st.expander("⚙️ AJUSTĂRI DIMENSIUNI", expanded=True):
            # SLIDER PREȚ - LIMITĂ 500
            ps = st.slider("MĂRIME PREȚ (Max 500)", 20, 500, 80, key=f"ps{i}")
            py = st.slider("Înălțime Preț (Y)", 300, 950, 820, key=f"py{i}")
            
            fs = st.slider("Mărime Specificații", 10, 80, 26, key=f"fs{i}")
            ls = st.slider("Spațiu Rânduri", 20, 100, 40, key=f"ls{i}")
            lsc = st.slider("Scară Logo", 0.1, 1.5, 0.7, key=f"lsc{i}")
            ly = st.slider("Poziție Logo (Y)", 900, 1150, 1050, key=f"ly{i}")

        # Generare imagine
        img_res = creeaza_imagine(r_data, fs, ls, lsc, ly, pret, py, ps)
        st.image(img_res, use_container_width=True)
        etichete.append(img_res)

# PDF
if st.button("🚀 GENEREAZĂ PDF FINAL"):
    canvas = Image.new('RGB', (2400, 1200))
    for idx, e in enumerate(etichete): canvas.paste(e, (idx * 800, 0))
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    buf = io.BytesIO()
    canvas.save(buf, format='PNG')
    buf.seek(0)
    with open("print_temp.png", "wb") as f: f.write(buf.read())
    pdf.image("print_temp.png", x=5, y=5, w=287)
    st.download_button("💾 DESCARCĂ PDF", pdf.output(dest='S').encode('latin-1'), "Etichete.pdf")
