import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Label System", layout="wide")

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

# --- RESURSE ---
@st.cache_data(show_spinner=False)
def get_font_bytes(font_name, weight="Bold"):
    # Folosim Open Sans ca fallback stabil pentru rubrica B@Ag
    url = f"https://github.com/google/fonts/raw/main/ofl/opensans/static/OpenSans-{weight}.ttf"
    try:
        r = requests.get(url, timeout=2)
        if r.status_code == 200: return r.content
    except: return None

def creeaza_imagine_eticheta(row, f_size, l_space, l_scale, l_y, pret_val, p_y, p_size, b_val, ag_val):
    W, H = 800, 1200
    img = Image.new('RGB', (W, H), color=(204, 9, 21))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([40, 40, 760, 980], radius=60, fill="white")

    # Fonturi
    font_raw = get_font_bytes("OpenSans", "Bold")
    try:
        f_titlu = ImageFont.truetype(io.BytesIO(font_raw), 45)
        f_spec = ImageFont.truetype(io.BytesIO(font_raw), int(f_size))
        # MĂRIRE PREȚ (Până la 500)
        f_pret = ImageFont.truetype(io.BytesIO(font_raw), int(p_size))
        f_b_ag = ImageFont.truetype(io.BytesIO(font_raw), 30)
    except:
        f_titlu = f_spec = f_pret = f_b_ag = ImageFont.load_default()

    # Model
    txt_m = f"{row['Brand']} {row['Model']}"
    draw.text(((W - draw.textlength(txt_m, font=f_titlu)) // 2, 120), txt_m, fill=(0, 51, 102), font=f_titlu)

    # Specificații
    specs = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Sanatate baterie"]
    y_s = 260
    for s in specs:
        if s in row and pd.notna(row[s]):
            draw.text((80, y_s), f"{s}: {row[s]}", fill="black", font=f_spec)
            y_s += l_space

    # --- PREȚ ---
    if pret_val:
        txt_p = f"Pret: {pret_val} lei"
        w_p = draw.textlength(txt_p, font=f_pret)
        draw.text(((W - w_p) // 2, p_y), txt_p, fill=(204, 9, 21), font=f_pret)

    # --- RUBRICA NOUĂ: Btext@AgX (Aliniat Dreapta) ---
    txt_bag = f"B{b_val}@{ag_val}"
    w_bag = draw.textlength(txt_bag, font=f_b_ag)
    draw.text((720 - w_bag, 920), txt_bag, fill="black", font=f_b_ag)

    # Logo
    try:
        url_l = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo = Image.open(io.BytesIO(requests.get(url_l).content)).convert("RGBA")
        lw = int(W * l_scale)
        lh = int(lw * (logo.size[1] / logo.size[0]))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(logo, ((W - lw) // 2, l_y), logo)
    except: pass
    
    return img

# --- INTERFAȚĂ ---
df = pd.read_excel("https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx")

# Listă pentru Dropdown Ag (1-52)
ag_options = [str(i) for i in range(1, 53)]

col_p = st.columns(3)
final_imgs = []

for i in range(3):
    with col_p[i]:
        brand = st.selectbox(f"Brand {i+1}", sorted(df['Brand'].unique()), key=f"b{i}")
        model = st.selectbox(f"Model {i+1}", df[df['Brand'] == brand]['Model'].unique(), key=f"m{i}")
        row_data = df[(df['Brand'] == brand) & (df['Model'] == model)].iloc[0]
        
        # Inputuri principale
        p_val = st.text_input(f"Preț (lei) {i+1}", "1500", key=f"pv{i}")
        
        # --- RUBRICA B @ Ag ---
        c1, c2 = st.columns(2)
        with c1:
            b_val = st.text_input(f"B (text/cifre) {i+1}", "32511", key=f"bv{i}")
        with c2:
            ag_val = st.selectbox(f"Cifră Ag {i+1}", ag_options, index=27, key=f"av{i}")

        with st.expander("🎨 Ajustări Dimensiuni", expanded=True):
            p_size = st.slider("Mărime Preț (Max 500)", 20, 500, 80, key=f"ps{i}")
            p_y = st.slider("Poziție Verticală Preț", 400, 950, 820, key=f"py{i}")
            f_size = st.slider("Mărime Specificații", 10, 80, 26, key=f"fs{i}")
            l_space = st.slider("Spațiu Rânduri", 20, 100, 40, key=f"ls{i}")
            l_scale = st.slider("Scară Logo", 0.1, 1.5, 0.7, key=f"lc{i}")
            l_y = st.slider("Poziție Logo", 900, 1150, 1050, key=f"ly{i}")

        img = creeaza_imagine_eticheta(row_data, f_size, l_space, l_scale, l_y, p_val, p_y, p_size, b_val, ag_val)
        st.image(img, use_container_width=True)
        final_imgs.append(img)

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
    st.download_button("💾 Descarcă PDF", pdf.output(dest='S').encode('latin-1'), "Etichete.pdf")
