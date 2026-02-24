import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit Pro - Font Maxim", layout="wide")

# CSS pentru aspect profesional
st.markdown("""
    <style>
    .stSlider label, .stSelectbox label, .stTextInput label {
        font-size: 16px !important;
        font-weight: bold !important;
    }
    div.stButton > button { height: 3em; background-color: #cc0915; color: white; width: 100%; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- LISTĂ FONTURI ---
FONT_URLS = {
    "Open Sans": "https://github.com/google/fonts/raw/main/ofl/opensans/static/OpenSans-",
    "Roboto": "https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-",
    "Montserrat": "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-",
    "Bebas Neue": "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-",
}

@st.cache_data(show_spinner=False)
def get_raw_font(name, style):
    base = FONT_URLS.get(name)
    if base:
        try:
            r = requests.get(f"{base}{style}.ttf", timeout=5)
            if r.status_code == 200: return r.content
        except: pass
    return None

def creeaza_imagine_eticheta(row, f_size, l_space, l_scale, l_y, f_name, pret, b_val, ag_val, py, ps):
    W, H = 800, 1200
    img = Image.new('RGB', (W, H), color=(204, 9, 21))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([40, 40, 760, 980], radius=60, fill="white")

    # Încărcare date brute fonturi
    raw_reg = get_raw_font(f_name, "Regular")
    raw_bold = get_raw_font(f_name, "Bold") or raw_reg
    raw_os_bold = get_raw_font("Open Sans", "Bold")

    try:
        # Creare fonturi (FĂRĂ CACHE pe mărime pentru a permite mărirea instantanee)
        f_titlu = ImageFont.truetype(io.BytesIO(raw_bold), 45)
        f_label = ImageFont.truetype(io.BytesIO(raw_bold), int(f_size))
        f_valoare = ImageFont.truetype(io.BytesIO(raw_reg), int(f_size))
        # AICI este mărirea pentru PREȚ (ps vine din slider)
        f_pret = ImageFont.truetype(io.BytesIO(raw_bold), int(ps))
        f_b_ag = ImageFont.truetype(io.BytesIO(raw_os_bold), 30)
    except:
        f_titlu = f_label = f_valoare = f_pret = f_b_ag = ImageFont.load_default()

    # Model
    txt_m = f"{row['Brand']} {row['Model']}"
    w_m = draw.textlength(txt_m, font=f_titlu)
    draw.text(((W - w_m) // 2, 100), txt_m, fill=(0, 51, 102), font=f_titlu)

    # Specificații
    specs = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Sanatate baterie"]
    y_p = 250
    for s in specs:
        if s in row and pd.notna(row[s]):
            draw.text((80, y_p), f"{s}:", fill="black", font=f_label)
            off = draw.textlength(f"{s}: ", font=f_label)
            draw.text((80 + off, y_p), str(row[s]), fill="black", font=f_valoare)
            y_p += l_space

    # --- PREȚ (Mărire activă) ---
    if pret:
        txt_p = f"Pret: {pret} lei"
        w_p = draw.textlength(txt_p, font=f_pret)
        draw.text(((W - w_p) // 2, py), txt_p, fill=(204, 9, 21), font=f_pret)

    # --- Btext@text (Dreapta, 30pt Bold) ---
    txt_bag = f"B{b_val}@{ag_val}"
    w_bag = draw.textlength(txt_bag, font=f_b_ag)
    draw.text((740 - w_bag, 920), txt_bag, fill="black", font=f_b_ag)

    # Logo
    try:
        url = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo = Image.open(io.BytesIO(requests.get(url).content)).convert("RGBA")
        lw = int(W * l_scale)
        lh = int(lw * (logo.size[1] / logo.size[0]))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(logo, ((W - lw) // 2, l_y), logo)
    except: pass
    
    return img

# --- INTERFAȚĂ ---
try:
    df = pd.read_excel("https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx")
except:
    st.error("⚠️ Baza de date inaccesibilă.")
    st.stop()

ag_nums = [str(i) for i in range(1, 53)]
col_p = st.columns(3)
final_imgs = []

for i in range(3):
    with col_p[i]:
        b = st.selectbox(f"Brand {i+1}", sorted(df['Brand'].unique()), key=f"b{i}")
        m = st.selectbox(f"Model {i+1}", df[df['Brand'] == b]['Model'].unique(), key=f"m{i}")
        row = df[(df['Brand'] == b) & (df['Model'] == m)].iloc[0]
        
        pr = st.text_input(f"Preț {i+1}", "1500", key=f"p{i}")
        c1, c2 = st.columns(2)
        with c1: b_v = st.text_input("B (cifre):", key=f"bv{i}", placeholder="32511")
        with c2: a_v = st.selectbox("Ag:", ag_nums, index=27, key=f"av{i}")

        with st.expander("🎨 Ajustări Design", expanded=True):
            fn = st.selectbox("Font", list(FONT_URLS.keys()), key=f"fn{i}")
            # SLIDER PREȚ MĂRIT LA 500
            psize = st.slider("MĂRIME PREȚ", 20, 500, 80, key=f"ps{i}")
            py_pos = st.slider("Poziție Y Preț", 300, 950, 820, key=f"py{i}")
            
            fs = st.slider("Mărime Specificații", 10, 80, 25, key=f"fs{i}")
            ls = st.slider("Spațiu Rânduri", 10, 80, 35, key=f"ls{i}")
            lsc = st.slider("Logo Scara", 0.1, 1.5, 0.7, key=f"lc{i}")
            l_y = st.slider("Y Logo", 900, 1150, 1050, key=f"ly{i}")

        res = creeaza_imagine_eticheta(row, fs, ls, lsc, l_y, fn, pr, b_v, a_v, py_pos, psize)
        st.image(res, use_container_width=True)
        final_imgs.append(res)

if st.button("🚀 GENEREAZĂ PDF FINAL"):
    canvas = Image.new('RGB', (2400, 1200))
    for i in range(3): canvas.paste(final_imgs[i], (i * 800, 0))
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    buf = io.BytesIO()
    canvas.save(buf, format='PNG')
    buf.seek(0)
    with open("temp.png", "wb") as f: f.write(buf.read())
    pdf.image("temp.png", x=5, y=5, w=287)
    st.download_button("💾 Descarcă PDF", pdf.output(dest='S').encode('latin-1'), "Etichete.pdf", "application/pdf")
