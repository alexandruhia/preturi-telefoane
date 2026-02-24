import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit Pro", layout="wide")

# --- FUNCȚIE DESCARCARE FONT CU EROARE GESTIONATĂ ---
@st.cache_data(show_spinner=False)
def get_font_safe(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.content
    except:
        pass
    return None

# Link-uri fonturi
URL_BOLD = "https://github.com/google/fonts/raw/main/ofl/opensans/static/OpenSans-Bold.ttf"
URL_REG = "https://github.com/google/fonts/raw/main/ofl/opensans/static/OpenSans-Regular.ttf"

def draw_label(row, p_text, b_text, ag_text, p_size, p_y, f_size, s_space, l_scale, l_y):
    W, H = 800, 1200
    img = Image.new('RGB', (W, H), color=(204, 9, 21))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([40, 40, 760, 980], radius=60, fill="white")

    # Încercăm să luăm fonturile
    raw_b = get_font_safe(URL_BOLD)
    raw_r = get_font_safe(URL_REG)

    def get_font_obj(raw_data, size):
        try:
            if raw_data:
                return ImageFont.truetype(io.BytesIO(raw_data), int(size))
        except:
            pass
        return ImageFont.load_default()

    # Creare obiecte font (Mărimea p_size acum va funcționa până la 500)
    f_titlu = get_font_obj(raw_b, 45)
    f_spec = get_font_obj(raw_b, f_size)
    f_val = get_font_obj(raw_r, f_size)
    f_pret = get_font_obj(raw_b, p_size) # AICI se aplică mărirea
    f_bag = get_font_obj(raw_b, 30)

    # Titlu
    txt_m = f"{row['Brand']} {row['Model']}"
    draw.text(((W - draw.textlength(txt_m, font=f_titlu)) // 2, 100), txt_m, fill=(0, 51, 102), font=f_titlu)

    # Specificații
    specs = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Sanatate baterie"]
    y = 240
    for s in specs:
        if s in row:
            val = str(row[s]) if pd.notna(row[s]) else "-"
            draw.text((80, y), f"{s}:", fill="black", font=f_spec)
            off = draw.textlength(f"{s}: ", font=f_spec)
            draw.text((80 + off, y), val, fill="black", font=f_val)
            y += s_space

    # Preț (Mărire până la 500)
    if p_text:
        txt_p = f"Pret: {p_text} lei"
        w_p = draw.textlength(txt_p, font=f_pret)
        draw.text(((W - w_p) // 2, p_y), txt_p, fill=(204, 9, 21), font=f_pret)

    # Rubrica B@Ag (Dreapta, 30pt Bold)
    txt_bag = f"B{b_text}@{ag_text}"
    w_bag = draw.textlength(txt_bag, font=f_bag)
    draw.text((740 - w_bag, 920), txt_bag, fill="black", font=f_bag)

    # Logo
    try:
        l_url = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo = Image.open(io.BytesIO(requests.get(l_url).content)).convert("RGBA")
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
    st.error("Nu pot încărca Excel-ul.")
    st.stop()

ag_list = [str(i) for i in range(1, 53)]
cols = st.columns(3)
final_images = []

for i in range(3):
    with cols[i]:
        br = st.selectbox(f"Brand {i+1}", sorted(df['Brand'].unique()), key=f"br{i}")
        md = st.selectbox(f"Model {i+1}", df[df['Brand'] == br]['Model'].unique(), key=f"md{i}")
        row = df[(df['Brand'] == br) & (df['Model'] == md)].iloc[0]
        
        pr_text = st.text_input(f"Preț {i+1}", "1500", key=f"pt{i}")
        c1, c2 = st.columns(2)
        with c1: b_text = st.text_input(f"B{i+1}", "32511", key=f"bt{i}")
        with c2: ag_text = st.selectbox(f"Ag{i+1}", ag_list, index=27, key=f"at{i}")

        with st.expander(f"REGLAJE", expanded=True):
            p_size = st.slider("MĂRIME PREȚ", 20, 500, 80, key=f"ps{i}")
            p_y = st.slider("Poziție Y Preț", 300, 950, 820, key=f"py{i}")
            f_size = st.slider("Mărime Specificații", 10, 80, 26, key=f"fs{i}")
            s_space = st.slider("Spațiere rânduri", 20, 100, 40, key=f"ss{i}")
            l_sc = st.slider("Scară Logo", 0.1, 1.5, 0.7, key=f"ls{i}")
            l_y_pos = st.slider("Poziție Logo", 900, 1150, 1040, key=f"ly{i}")

        img = draw_label(row, pr_text, b_text, ag_text, p_size, p_y, f_size, s_space, l_sc, l_y_pos)
        st.image(img, use_container_width=True)
        final_images.append(img)

if st.button("🚀 GENEREAZĂ PDF"):
    canvas = Image.new('RGB', (2400, 1200))
    for idx, image in enumerate(final_images): canvas.paste(image, (idx * 800, 0))
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    buf = io.BytesIO()
    canvas.save(buf, format='PNG')
    buf.seek(0)
    with open("print.png", "wb") as f: f.write(buf.read())
    pdf.image("print.png", x=5, y=5, w=287)
    st.download_button("💾 DESCARCĂ PDF", pdf.output(dest='S').encode('latin-1'), "Etichete.pdf")
