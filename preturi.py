import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

st.set_page_config(page_title="ExpressCredit Label Pro", layout="wide")

# --- RESURSE CACHE ---
@st.cache_data(ttl=3600)
def load_excel():
    url = "https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx"
    return pd.read_excel(url)

@st.cache_data(ttl=3600)
def get_font_data():
    url = "https://github.com/google/fonts/raw/main/ofl/opensans/static/OpenSans-Bold.ttf"
    try:
        return requests.get(url, timeout=10).content
    except:
        return None

# --- GENERARE IMAGINE ---
def generate_label(row, p_text, b_text, ag_text, p_size, p_y, f_size, f_space, l_scale, l_y):
    W, H = 800, 1200
    img = Image.new('RGB', (W, H), color=(204, 9, 21)) # Fundal Roșu
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([40, 40, 760, 980], radius=60, fill="white")

    font_raw = get_font_data()
    
    # Creare fonturi cu dimensiuni dinamice (Slidere)
    try:
        f_titlu = ImageFont.truetype(io.BytesIO(font_raw), 45) if font_raw else ImageFont.load_default()
        f_spec = ImageFont.truetype(io.BytesIO(font_raw), int(f_size)) if font_raw else ImageFont.load_default()
        f_pret = ImageFont.truetype(io.BytesIO(font_raw), int(p_size)) if font_raw else ImageFont.load_default()
        f_bag = ImageFont.truetype(io.BytesIO(font_raw), 30) if font_raw else ImageFont.load_default()
    except:
        f_titlu = f_spec = f_pret = f_bag = ImageFont.load_default()

    # 1. Titlu Model
    txt_m = f"{row.get('Brand', '')} {row.get('Model', '')}".strip()
    draw.text(((W - draw.textlength(txt_m, font=f_titlu)) // 2, 100), txt_m, fill=(0, 51, 102), font=f_titlu)

    # 2. Specificații (Iterăm prin coloanele utile)
    useful_cols = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Sanatate baterie", "Capacitate baterie"]
    y_current = 240
    for col in useful_cols:
        if col in row and pd.notna(row[col]):
            val = str(row[col])
            # Desenăm Label: Valoare
            txt_full = f"{col}: {val}"
            draw.text((80, y_current), txt_full, fill="black", font=f_spec)
            y_current += f_space

    # 3. Preț (Mărire până la 500)
    if p_text:
        txt_p = f"Pret: {p_text} lei"
        w_p = draw.textlength(txt_p, font=f_pret)
        draw.text(((W - w_p) // 2, p_y), txt_p, fill=(204, 9, 21), font=f_pret)

    # 4. Rubrica B@Ag (Aliniat Dreapta, Fix 30pt)
    txt_bag = f"B{b_text}@{ag_text}"
    w_bag = draw.textlength(txt_bag, font=f_bag)
    draw.text((740 - w_bag, 920), txt_bag, fill="black", font=f_bag)

    # 5. Logo
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
df = load_excel()
ag_list = [str(i) for i in range(1, 53)]

cols = st.columns(3)
final_images = []

for i in range(3):
    with cols[i]:
        brand = st.selectbox(f"Selectează Brand {i+1}", sorted(df['Brand'].unique()), key=f"b_{i}")
        model = st.selectbox(f"Selectează Model {i+1}", df[df['Brand'] == brand]['Model'].unique(), key=f"m_{i}")
        row_data = df[(df['Brand'] == brand) & (df['Model'] == model)].iloc[0].to_dict()
        
        p_input = st.text_input(f"Preț {i+1}", "1500", key=f"pi_{i}")
        c1, c2 = st.columns(2)
        with c1: b_input = st.text_input(f"B{i+1}", "32511", key=f"bi_{i}")
        with c2: a_input = st.selectbox(f"Ag{i+1}", ag_list, index=27, key=f"ai_{i}")

        with st.expander("🎨 Ajustări Dimensiuni", expanded=True):
            ps = st.slider("Mărime Preț (Max 500)", 20, 500, 80, key=f"psl_{i}")
            py = st.slider("Poziție Y Preț", 300, 950, 820, key=f"pyl_{i}")
            fs = st.slider("Mărime Specificații", 10, 100, 26, key=f"fsl_{i}")
            ss = st.slider("Spațiu Rânduri", 10, 100, 40, key=f"ssl_{i}")
            ls = st.slider("Scară Logo", 0.1, 1.5, 0.7, key=f"lsl_{i}")
            ly = st.slider("Poziție Logo", 900, 1150, 1040, key=f"lyl_{i}")

        # Generare și Afișare
        img_label = generate_label(row_data, p_input, b_input, a_input, ps, py, fs, ss, ls, ly)
        st.image(img_label, use_container_width=True)
        final_images.append(img_label)

# PDF
if st.button("🚀 GENEREAZĂ PDF FINAL"):
    canvas = Image.new('RGB', (2400, 1200))
    for idx, im in enumerate(final_images): canvas.paste(im, (idx * 800, 0))
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    buf = io.BytesIO()
    canvas.save(buf, format='PNG')
    buf.seek(0)
    with open("temp_print.png", "wb") as f: f.write(buf.read())
    pdf.image("temp_print.png", x=5, y=5, w=287)
    st.download_button("💾 DESCARCĂ PDF", pdf.output(dest='S').encode('latin-1'), "Etichete.pdf")
