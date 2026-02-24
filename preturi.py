import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit Pro", layout="wide")

# CSS pentru panou de reglaje
st.markdown("""
    <style>
    .stSlider label, .stSelectbox label, .stTextInput label {
        font-size: 16px !important;
        font-weight: bold !important;
    }
    div.stButton > button { height: 3em; background-color: #cc0915; color: white; width: 100%; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- ÎNCĂRCARE DATE ---
@st.cache_data
def load_excel_data():
    url = "https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx"
    try:
        return pd.read_excel(url)
    except:
        return pd.DataFrame(columns=["Brand", "Model"])

# --- FUNCȚIE FONT SIGURĂ ---
@st.cache_data(show_spinner=False)
def load_font_safe(font_name, size):
    # Încercăm să descărcăm fontul dorit
    clean_name = font_name.lower().replace(" ", "")
    url = f"https://github.com/google/fonts/raw/main/ofl/{clean_name}/{font_name.replace(' ', '')}-Bold.ttf"
    try:
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            return ImageFont.truetype(io.BytesIO(r.content), int(size))
    except:
        pass
    # Dacă nu merge, folosim fontul default al sistemului
    return ImageFont.load_default()

def draw_label(row, fs, ls, l_sc, l_y, p_val, p_y, p_size, b_val, ag_val, bag_size, font_name):
    W, H = 800, 1200
    img = Image.new('RGB', (W, H), color=(204, 9, 21))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([40, 40, 760, 980], radius=60, fill="white")

    # Incarcare fonturi cu protectie
    f_titlu = load_font_safe(font_name, 45)
    f_spec = load_font_safe(font_name, fs)
    f_pret = load_font_safe(font_name, p_size)
    f_bag = load_font_safe(font_name, bag_size)

    # 1. Model
    txt_m = f"{row.get('Brand', '')} {row.get('Model', '')}".strip()
    draw.text(((W - draw.textlength(txt_m, font=f_titlu)) // 2, 110), txt_m, fill=(0, 51, 102), font=f_titlu)

    # 2. Specificații
    specs = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Sanatate baterie"]
    y_curr = 260
    for s in specs:
        if s in row and pd.notna(row[s]):
            txt_s = f"{s}: {row[s]}"
            draw.text((80, y_curr), txt_s, fill="black", font=f_spec)
            y_curr += ls

    # 3. Preț
    if p_val:
        txt_p = f"Pret: {p_val} lei"
        w_p = draw.textlength(txt_p, font=f_pret)
        draw.text(((W - w_p) // 2, p_y), txt_p, fill=(204, 9, 21), font=f_pret)

    # 4. Rubrica B@Ag
    txt_bag = f"B{b_val}@Ag{ag_val}"
    w_bag = draw.textlength(txt_bag, font=f_bag)
    draw.text(((W - w_bag) // 2, p_y + p_size + 10), txt_bag, fill="black", font=f_bag)

    # 5. Logo
    try:
        l_url = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo = Image.open(io.BytesIO(requests.get(l_url).content)).convert("RGBA")
        lw = int(W * l_sc)
        lh = int(lw * (logo.size[1] / logo.size[0]))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(logo, ((W - lw) // 2, l_y), logo)
    except:
        pass

    return img

# --- INTERFATA ---
df = load_excel_data()
ag_list = [str(i) for i in range(1, 56)]

if df.empty:
    st.error("Baza de date nu a putut fi încărcată.")
else:
    cols = st.columns(3)
    imgs = []

    for i in range(3):
        with cols[i]:
            br = st.selectbox(f"Brand {i+1}", sorted(df['Brand'].unique()), key=f"br{i}")
            md = st.selectbox(f"Model {i+1}", df[df['Brand'] == br]['Model'].unique(), key=f"md{i}")
            row = df[(df['Brand'] == br) & (df['Model'] == md)].iloc[0]
            
            p_text = st.text_input(f"Preț {i+1}", "1500", key=f"pt{i}")
            c1, c2 = st.columns(2)
            with c1: b_v = st.text_input(f"B {i+1}", "32511", key=f"bv{i}")
            with c2: a_v = st.selectbox(f"Ag {i+1}", ag_list, index=27, key=f"av{i}")

            with st.expander("🎨 Setări", expanded=True):
                fn = st.selectbox("Font", ["Open Sans", "Roboto", "Montserrat"], key=f"fn{i}")
                ps = st.slider("Mărime Preț", 20, 500, 80, key=f"ps{i}")
                py = st.slider("Poziție Y Preț", 300, 900, 780, key=f"py{i}")
                bs = st.slider("Mărime B@Ag", 10, 150, 35, key=f"bs{i}")
                fs = st.slider("Mărime Specificații", 10, 80, 26, key=f"fs{i}")
                ls = st.slider("Spațiu Rânduri", 20, 100, 40, key=f"ls{i}")
                lsc = st.slider("Scară Logo", 0.1, 1.5, 0.7, key=f"lsc{i}")
                ly = st.slider("Poziție Logo", 900, 1150, 1050, key=f"ly{i}")

            res_img = draw_label(row, fs, ls, lsc, ly, p_text, py, ps, b_v, a_v, bs, fn)
            st.image(res_img, use_container_width=True)
            imgs.append(res_img)

    if st.button("🚀 GENERARE PDF"):
        canvas = Image.new('RGB', (2400, 1200))
        for idx, im in enumerate(imgs): canvas.paste(im, (idx * 800, 0))
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        buf = io.BytesIO()
        canvas.save(buf, format='PNG')
        buf.seek(0)
        with open("out.png", "wb") as f: f.write(buf.read())
        pdf.image("out.png", x=5, y=5, w=287)
        st.download_button("💾 Download PDF", pdf.output(dest='S').encode('latin-1'), "Etichete.pdf")
