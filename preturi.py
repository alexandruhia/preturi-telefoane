import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF
import time

# Configurare pagină
st.set_page_config(page_title="ExpressCredit Fix", layout="wide")

# CSS pentru vizibilitate
st.markdown("""<style>
    .stSlider label { font-size: 20px !important; color: #cc0915 !important; font-weight: bold !important; }
    div.stButton > button { height: 3em; background-color: #cc0915; color: white; font-weight: bold; }
</style>""", unsafe_allow_html=True)

# --- RESURSE FONT ---
# Folosim link-uri directe către fișierele TTF brute pentru viteză
FONT_LINKS = {
    "Open Sans": "https://github.com/google/fonts/raw/main/ofl/opensans/static/OpenSans-Bold.ttf",
    "Roboto": "https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Bold.ttf",
    "Bebas Neue": "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf"
}

@st.cache_data(show_spinner=False)
def load_font_bytes(url):
    return requests.get(url).content

def creeaza_imagine(row, fs_spec, ls_rande, l_scale, l_y, pr_val, b_val, ag_val, py_pret, ps_pret, font_choice):
    # Creăm imaginea de la zero la fiecare rulare
    W, H = 800, 1200
    img = Image.new('RGB', (W, H), color=(204, 9, 21))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([40, 40, 760, 980], radius=60, fill="white")

    # Încărcare fonturi FĂRĂ CACHE pe dimensiune
    try:
        f_data_main = load_font_bytes(FONT_LINKS[font_choice])
        f_data_os = load_font_bytes(FONT_LINKS["Open Sans"])
        
        # AICI ESTE CHEIA: Creăm instanțe noi de font cu dimensiunile din slidere
        font_titlu = ImageFont.truetype(io.BytesIO(f_data_main), 45)
        font_spec = ImageFont.truetype(io.BytesIO(f_data_main), int(fs_spec))
        font_pret = ImageFont.truetype(io.BytesIO(f_data_main), int(ps_pret)) # Dimensiune din slider
        font_b_ag = ImageFont.truetype(io.BytesIO(f_data_os), 30)
    except:
        font_titlu = font_spec = font_pret = font_b_ag = ImageFont.load_default()

    # 1. Titlu Model
    txt_m = f"{row['Brand']} {row['Model']}"
    draw.text(((W - draw.textlength(txt_m, font=font_titlu)) // 2, 120), txt_m, fill=(0, 51, 102), font=font_titlu)

    # 2. Specificații
    specs = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Sanatate baterie"]
    y_p = 260
    for s in specs:
        if s in row:
            val = str(row[s]) if pd.notna(row[s]) else "-"
            draw.text((80, y_p), f"{s}: {val}", fill="black", font=font_spec)
            y_p += ls_rande

    # 3. PREȚ - VERIFICĂ MĂRIREA AICI
    if pr_val:
        txt_p = f"Pret: {pr_val} lei"
        w_p = draw.textlength(txt_p, font=font_pret)
        draw.text(((W - w_p) // 2, py_pret), txt_p, fill=(204, 9, 21), font=font_pret)

    # 4. Rubrica B@Ag (Dreapta)
    txt_bag = f"B{b_val}@{ag_val}"
    draw.text((740 - draw.textlength(txt_bag, font=font_b_ag), 920), txt_bag, fill="black", font=font_b_ag)

    # 5. Logo
    try:
        logo_url = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo = Image.open(io.BytesIO(requests.get(logo_url).content)).convert("RGBA")
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
    st.error("Eroare bază de date.")
    st.stop()

ag_list = [str(i) for i in range(1, 53)]
cols = st.columns(3)
etichete_finale = []

for i in range(3):
    with cols[i]:
        # Date
        brand = st.selectbox(f"Brand {i+1}", sorted(df['Brand'].unique()), key=f"b{i}")
        model = st.selectbox(f"Model {i+1}", df[df['Brand'] == brand]['Model'].unique(), key=f"m{i}")
        row_data = df[(df['Brand'] == brand) & (df['Model'] == model)].iloc[0]
        
        # Inputs
        pret = st.text_input(f"Preț {i+1}", "1500", key=f"p_in{i}")
        c1, c2 = st.columns(2)
        with c1: b_v = st.text_input(f"B {i+1}", "32511", key=f"b_in{i}")
        with c2: a_v = st.selectbox(f"Ag {i+1}", ag_list, index=27, key=f"a_in{i}")

        # Ajustări
        with st.expander(f"⚙️ REGLAJE ETICHETA {i+1}", expanded=True):
            f_choice = st.selectbox("Font", list(FONT_LINKS.keys()), key=f"f_ch{i}")
            
            # SLIDER-UL CARE TREBUIE SĂ MEARGĂ
            ps = st.slider("MĂRIME PREȚ", 30, 200, 80, key=f"ps_sl{i}")
            py = st.slider("Înălțime Preț (Y)", 600, 950, 820, key=f"py_sl{i}")
            
            fs = st.slider("Mărime Text Spec.", 10, 60, 28, key=f"fs_sl{i}")
            ls = st.slider("Spațiere rânduri", 20, 80, 40, key=f"ls_sl{i}")
            
            l_sc = st.slider("Scară Logo", 0.1, 1.2, 0.7, key=f"lc_sl{i}")
            l_y_pos = st.slider("Y Logo", 900, 1150, 1050, key=f"ly_sl{i}")

        # Generare imagine
        img_res = creeaza_imagine(row_data, fs, ls, l_sc, l_y_pos, pret, b_v, a_v, py, ps, f_choice)
        
        # Forțăm Streamlit să nu folosească imaginea veche din cache-ul browserului
        st.image(img_res, use_container_width=True, caption=f"Previzualizare {i+1}")
        etichete_finale.append(img_res)

# PDF
if st.button("🚀 GENEREAZĂ PDF FINAL"):
    canvas = Image.new('RGB', (2400, 1200))
    for i in range(3): canvas.paste(etichete_finale[i], (i * 800, 0))
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    buf = io.BytesIO()
    canvas.save(buf, format='PNG')
    buf.seek(0)
    with open("temp_print.png", "wb") as f: f.write(buf.read())
    pdf.image("temp_print.png", x=5, y=5, w=287)
    st.download_button("💾 SALVEAZĂ", pdf.output(dest='S').encode('latin-1'), "Etichete.pdf")
