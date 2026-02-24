import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit Fix", layout="wide")

# --- FUNCȚII RESURSE ---
@st.cache_data(show_spinner=False)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx"
    return pd.read_excel(url)

@st.cache_data(show_spinner=False)
def get_font_bytes():
    # Descărcăm fontul o singură dată în cache
    url = "https://github.com/google/fonts/raw/main/ofl/opensans/static/OpenSans-Bold.ttf"
    return requests.get(url).content

# --- GENERARE IMAGINE (FĂRĂ CACHE) ---
def creeaza_imagine(row, p_text, b_text, ag_text, p_size, p_y, f_size, s_space, l_scale, l_y):
    W, H = 800, 1200
    img = Image.new('RGB', (W, H), color=(204, 9, 21))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([40, 40, 760, 980], radius=60, fill="white")

    font_bytes = get_font_bytes()
    
    # Creăm obiectele de font proaspete la fiecare rulare
    try:
        f_titlu = ImageFont.truetype(io.BytesIO(font_bytes), 45)
        f_spec = ImageFont.truetype(io.BytesIO(font_bytes), int(f_size))
        f_pret = ImageFont.truetype(io.BytesIO(font_bytes), int(p_size))
        f_bag = ImageFont.truetype(io.BytesIO(font_bytes), 30)
    except:
        f_titlu = f_spec = f_pret = f_bag = ImageFont.load_default()

    # Titlu
    txt_m = f"{row['Brand']} {row['Model']}"
    draw.text(((W - draw.textlength(txt_m, font=f_titlu)) // 2, 100), txt_m, fill=(0, 51, 102), font=f_titlu)

    # Specificații (Mărimea f_size se aplică aici)
    specs = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Sanatate baterie"]
    current_y = 240
    for s in specs:
        if s in row and pd.notna(row[s]):
            txt_s = f"{s}: {row[s]}"
            draw.text((80, current_y), txt_s, fill="black", font=f_spec)
            current_y += s_space

    # Preț (Mărimea p_size se aplică aici)
    if p_text:
        txt_p = f"Pret: {p_text} lei"
        w_p = draw.textlength(txt_p, font=f_pret)
        draw.text(((W - w_p) // 2, p_y), txt_p, fill=(204, 9, 21), font=f_pret)

    # B@Ag (Fix 30pt Bold)
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
df = load_data()
ag_list = [str(i) for i in range(1, 53)]

cols = st.columns(3)
final_images = []

for i in range(3):
    with cols[i]:
        br = st.selectbox(f"Brand {i+1}", sorted(df['Brand'].unique()), key=f"brand{i}")
        md = st.selectbox(f"Model {i+1}", df[df['Brand'] == br]['Model'].unique(), key=f"model{i}")
        row_sel = df[(df['Brand'] == br) & (df['Model'] == md)].iloc[0]
        
        # Câmpuri text
        pret_val = st.text_input(f"Preț {i+1}", "1500", key=f"p_txt{i}")
        c1, c2 = st.columns(2)
        with c1: b_val = st.text_input(f"B{i+1}", "32511", key=f"b_txt{i}")
        with c2: ag_val = st.selectbox(f"Ag{i+1}", ag_list, index=27, key=f"a_txt{i}")

        # Slidere
        with st.expander("⚙️ AJUSTĂRI DIMENSIUNI", expanded=True):
            p_size = st.slider(f"Mărime Preț (max 500)", 20, 500, 80, key=f"psize{i}")
            p_y_pos = st.slider(f"Înălțime Preț", 300, 950, 820, key=f"py{i}")
            f_size = st.slider(f"Mărime Specificații", 10, 100, 26, key=f"fsize{i}")
            s_spc = st.slider(f"Spațiere rânduri", 10, 100, 40, key=f"sspc{i}")
            l_sc = st.slider(f"Scară Logo", 0.1, 1.5, 0.7, key=f"lsc{i}")
            l_y_p = st.slider(f"Poziție Logo", 900, 1150, 1040, key=f"lyp{i}")

        # Generăm imaginea - FĂRĂ CACHE, se va actualiza la orice slider
        label_img = creeaza_imagine(row_sel, pret_val, b_val, ag_val, p_size, p_y_pos, f_size, s_spc, l_sc, l_y_p)
        st.image(label_img, use_container_width=True)
        final_images.append(label_img)

# PDF
if st.button("🚀 SALVEAZĂ PDF"):
    canvas = Image.new('RGB', (2400, 1200))
    for idx, img_obj in enumerate(final_images):
        canvas.paste(img_obj, (idx * 800, 0))
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    buf = io.BytesIO()
    canvas.save(buf, format='PNG')
    buf.seek(0)
    with open("temp.png", "wb") as f: f.write(buf.read())
    pdf.image("temp.png", x=5, y=5, w=287)
    st.download_button("💾 DESCARCĂ PDF", pdf.output(dest='S').encode('latin-1'), "Etichete.pdf")
