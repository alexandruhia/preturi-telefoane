import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit Mega Font", layout="wide")

# CSS pentru vizibilitate controlere
st.markdown("""<style>
    .stSlider label { font-size: 22px !important; color: #cc0915 !important; font-weight: 800 !important; }
    div.stButton > button { height: 3em; background-color: #cc0915; color: white; font-weight: bold; font-size: 20px; }
</style>""", unsafe_allow_html=True)

# --- RESURSE FONT ---
FONT_LINKS = {
    "Open Sans": "https://github.com/google/fonts/raw/main/ofl/opensans/static/OpenSans-Bold.ttf",
    "Roboto": "https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Bold.ttf",
    "Bebas Neue": "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf"
}

@st.cache_data(show_spinner=False)
def load_font_bytes(url):
    return requests.get(url).content

def creeaza_imagine(row, fs_spec, ls_rande, l_scale, l_y, pr_val, b_val, ag_val, py_pret, ps_pret, font_choice):
    W, H = 800, 1200
    img = Image.new('RGB', (W, H), color=(204, 9, 21))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([40, 40, 760, 980], radius=60, fill="white")

    # Încărcare fonturi
    try:
        f_data_main = load_font_bytes(FONT_LINKS[font_choice])
        f_data_os = load_font_bytes(FONT_LINKS["Open Sans"])
        
        font_titlu = ImageFont.truetype(io.BytesIO(f_data_main), 45)
        font_spec = ImageFont.truetype(io.BytesIO(f_data_main), int(fs_spec))
        # LIMITA NOUĂ: ps_pret poate ajunge acum la 500
        font_pret = ImageFont.truetype(io.BytesIO(f_data_main), int(ps_pret)) 
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

    # 3. PREȚ (Mărire până la 500pt)
    if pr_val:
        txt_p = f"Pret: {pr_val} lei"
        w_p = draw.textlength(txt_p, font=font_pret)
        draw.text(((W - w_p) // 2, py_pret), txt_p, fill=(204, 9, 21), font=font_pret)

    # 4. Rubrica Btext@text (Dreapta, Open Sans Bold 30pt)
    txt_bag = f"B{b_val}@{ag_val}"
    draw.text((730 - draw.textlength(txt_bag, font=font_b_ag), 920), txt_bag, fill="black", font=font_b_ag)

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
    st.error("Eroare bază de date Excel.")
    st.stop()

ag_list = [str(i) for i in range(1, 53)]
cols = st.columns(3)
etichete_finale = []

for i in range(3):
    with cols[i]:
        brand = st.selectbox(f"Brand {i+1}", sorted(df['Brand'].unique()), key=f"b{i}")
        model = st.selectbox(f"Model {i+1}", df[df['Brand'] == brand]['Model'].unique(), key=f"m{i}")
        row_data = df[(df['Brand'] == brand) & (df['Model'] == model)].iloc[0]
        
        pret_input = st.text_input(f"Preț (lei) {i+1}", "1500", key=f"p_in{i}")
        c1, c2 = st.columns(2)
        with c1: b_v = st.text_input(f"B (Cifre) {i+1}", "32511", key=f"b_in{i}")
        with c2: a_v = st.selectbox(f"Ag (@) {i+1}", ag_list, index=27, key=f"a_in{i}")

        with st.expander(f"⚙️ AJUSTĂRI DESIGN {i+1}", expanded=True):
            f_choice = st.selectbox("Font", list(FONT_LINKS.keys()), key=f"f_ch{i}")
            
            # --- SLIDER MĂRIME PREȚ MĂRIT LA 500 ---
            ps = st.slider("MĂRIME PREȚ (Max 500)", 20, 500, 80, key=f"ps_sl{i}")
            py = st.slider("Poziție Verticală Preț", 400, 950, 820, key=f"py_sl{i}")
            
            fs = st.slider("Mărime Specificații", 10, 80, 28, key=f"fs_sl{i}")
            ls = st.slider("Spațiu între rânduri", 20, 100, 40, key=f"ls_sl{i}")
            
            l_sc = st.slider("Scară Logo", 0.1, 1.5, 0.7, key=f"lc_sl{i}")
            l_y_pos = st.slider("Poziție Logo (Y)", 900, 1150, 1050, key=f"ly_sl{i}")

        # Generare
        img_res = creeaza_imagine(row_data, fs, ls, l_sc, l_y_pos, pret_input, b_v, a_v, py, ps, f_choice)
        st.image(img_res, use_container_width=True)
        etichete_finale.append(img_res)

# PDF
st.divider()
if st.button("🚀 GENEREAZĂ PDF FINAL"):
    canvas = Image.new('RGB', (2400, 1200))
    for idx, img in enumerate(etichete_finale):
        canvas.paste(img, (idx * 800, 0))
    
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    buf = io.BytesIO()
    canvas.save(buf, format='PNG')
    buf.seek(0)
    with open("temp_print.png", "wb") as f:
        f.write(buf.read())
    pdf.image("temp_print.png", x=5, y=5, w=287)
    
    st.download_button("💾 DESCARCĂ PDF", pdf.output(dest='S').encode('latin-1'), "Etichete_Express.pdf", "application/pdf")
