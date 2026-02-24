import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Mega Layout System", layout="wide")

# CSS pentru un design compact și lizibil
st.markdown("""
    <style>
    [data-testid="column"] { padding: 10px !important; }
    .stSlider label, .stSelectbox label, .stNumberInput label, .stTextInput label {
        font-size: 14px !important;
        font-weight: 700 !important;
        color: #333 !important;
        margin-bottom: 0px !important;
    }
    div.stButton > button { height: 3.5em; font-weight: bold; background-color: #cc0915; color: white; border-radius: 8px; width: 100%; }
    .stExpander { border: 1px solid #ddd !important; border-radius: 8px !important; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def get_font_bytes(font_name, weight):
    folders = ['ofl', 'apache', 'googlefonts']
    clean_name = font_name.lower().replace(" ", "")
    for folder in folders:
        url = f"https://github.com/google/fonts/raw/main/{folder}/{clean_name}/{font_name.replace(' ', '')}-{weight}.ttf"
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200: return r.content
        except: continue
    return None

def creeaza_imagine_eticheta(row, titlu_size, font_size, line_spacing, l_scale, l_x_manual, l_y, font_name, pret_val, pret_y, pret_size, cifra_size, b_text, ag_val, bat_val):
    W, H = 800, 1200
    img = Image.new('RGB', (W, H), color=(204, 9, 21))
    draw = ImageDraw.Draw(img)
    margine = 40
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=60, fill="white")

    f_reg_bytes = get_font_bytes(font_name, "Regular")
    f_bold_bytes = get_font_bytes(font_name, "Bold") or f_reg_bytes
    
    try:
        if f_reg_bytes:
            f_titlu = ImageFont.truetype(io.BytesIO(f_bold_bytes), titlu_size)
            f_label = ImageFont.truetype(io.BytesIO(f_bold_bytes), font_size)
            f_valoare = ImageFont.truetype(io.BytesIO(f_reg_bytes), font_size)
            f_pret_text = ImageFont.truetype(io.BytesIO(f_bold_bytes), pret_size)
            f_pret_cifra = ImageFont.truetype(io.BytesIO(f_bold_bytes), cifra_size)
            f_bag = ImageFont.truetype(io.BytesIO(f_bold_bytes), 40)
        else:
            path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            f_titlu = ImageFont.truetype(path, titlu_size)
            f_label = ImageFont.truetype(path, font_size)
            f_valoare = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            f_pret_text = ImageFont.truetype(path, pret_size)
            f_pret_cifra = ImageFont.truetype(path, cifra_size)
            f_bag = ImageFont.truetype(path, 40)
    except:
        f_titlu = f_label = f_valoare = f_pret_text = f_pret_cifra = f_bag = ImageFont.load_default()

    txt_m = f"{row['Brand']} {row['Model']}"
    w_m = draw.textlength(txt_m, font=f_titlu)
    draw.text(((W - w_m) // 2, margine * 3), txt_m, fill=(0, 51, 102), font=f_titlu)

    y_pos = margine * 7.5
    specs = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Selfie", "Capacitate baterie"]
    for col in specs:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            draw.text((margine * 2, y_pos), f"{col}:", fill="black", font=f_label)
            offset = draw.textlength(f"{col}: ", font=f_label)
            draw.text((margine * 2 + offset, y_pos), val, fill="black", font=f_valoare)
            y_pos += line_spacing

    label_bat = "Sanatate baterie:"
    draw.text((margine * 2, y_pos), label_bat, fill="black", font=f_label)
    offset_bat = draw.textlength(f"{label_bat} ", font=f_label)
    draw.text((margine * 2 + offset_bat, y_pos), f"{bat_val}%", fill="black", font=f_valoare)

    if pret_val:
        t1, t2, t3 = "Pret: ", f"{pret_val}", " lei"
        w1 = draw.textlength(t1, font=f_pret_text)
        w2 = draw.textlength(t2, font=f_pret_cifra)
        w3 = draw.textlength(t3, font=f_pret_text)
        total_w = w1 + w2 + w3
        start_x = (W - total_w) // 2
        y_base = pret_y + cifra_size 
        draw.text((start_x, y_base - pret_size), t1, fill=(204, 9, 21), font=f_pret_text)
        draw.text((start_x + w1, y_base - cifra_size), t2, fill=(204, 9, 21), font=f_pret_cifra)
        draw.text((start_x + w1 + w2, y_base - pret_size), t3, fill=(204, 9, 21), font=f_pret_text)
        
        txt_bag = f"B{b_text}@Ag{ag_val}"
        w_bag = draw.textlength(txt_bag, font=f_bag)
        draw.text((W - margine * 2 - w_bag, y_base + 20), txt_bag, fill="black", font=f_bag)

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

@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx"
    return pd.read_excel(url)

df = load_data()

st.sidebar.header("🔍 CONTROL VIZUAL")
zoom = st.sidebar.slider("Lățime Previzualizare", 200, 800, 380)

FONT_NAMES = ["Roboto", "Montserrat", "Open Sans", "Poppins", "Bebas Neue", "Anton"]
ag_list = [str(i) for i in range(1, 56)]
battery_list = [str(i) for i in range(100, 0, -1)]

col_main = st.columns(3)
final_imgs = []

for i in range(3):
    with col_main[i]:
        # --- SELECȚIE TELEFON (Coloană plină) ---
        brand = st.selectbox(f"BRAND {i+1}", sorted(df['Brand'].dropna().unique()), key=f"b_{i}")
        model = st.selectbox(f"MODEL {i+1}", df[df['Brand'] == brand]['Model'].dropna().unique(), key=f"m_{i}")
        r_data = df[(df['Brand'] == brand) & (df['Model'] == model)].iloc[0]
        
        st.markdown("---")
        
        # --- REGLAJE PE DOUĂ COLOANE ---
        reg_left, reg_right = st.columns(2)
        
        with reg_left:
            bat_choice = st.selectbox(f"BATERIE %", battery_list, index=0, key=f"bat_{i}")
            b_input = st.text_input(f"B TEXT", key=f"bt_{i}", placeholder="cod")
            t_size = st.number_input("MĂRIME TITLU", 10, 150, 45, key=f"tsz_{i}")
            f_size = st.number_input("MĂRIME SPEC.", 10, 100, 30, key=f"sz_{i}")
            p_size = st.number_input("MĂRIME 'PRET:'", 20, 150, 60, key=f"psz_{i}")

        with reg_right:
            pret_input = st.text_input(f"PRET LEI", value="", key=f"pr_{i}", placeholder="cifra")
            ag_input = st.selectbox(f"AG VAL", ag_list, key=f"ag_{i}")
            fn = st.selectbox("FONT", FONT_NAMES, key=f"fn_{i}")
            sp = st.number_input("SPAȚIERE", 10, 100, 38, key=f"sp_{i}")
            c_size = st.number_input("MĂRIME CIFRĂ", 20, 300, 85, key=f"csz_{i}")

        with st.expander("LOGO & POZIȚIE PREȚ"):
            ex_l, ex_r = st.columns(2)
            with ex_l:
                p_y = st.slider("Y PREȚ", 400, 1150, 850, key=f"py_{i}")
                ls = st.slider("SCARĂ LOGO", 0.1, 2.0, 0.7, key=f"ls_{i}")
            with ex_r:
                lx = st.number_input("X LOGO (100=C)", 0, 800, 100, key=f"lx_{i}")
                ly = st.number_input("Y LOGO", 0, 1200, 1050, key=f"ly_{i}")

        # --- PREVIZUALIZARE ---
        current_img = creeaza_imagine_eticheta(r_data, t_size, f_size, sp, ls, lx, ly, fn, pret_input, p_y, p_size, c_size, b_input, ag_input, bat_choice)
        st.image(current_img, width=zoom)
        final_imgs.append(current_img)

st.divider()
if st.button("🚀 GENEREAZĂ PDF FINAL"):
    canvas = Image.new('RGB', (2400, 1200))
    for i in range(3): canvas.paste(final_imgs[i], (i * 800, 0))
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    buf = io.BytesIO()
    canvas.save(buf, format='PNG')
    buf.seek(0)
    with open("temp_print.png", "wb") as f: f.write(buf.read())
    pdf.image("temp_print.png", x=5, y=5, w=287)
    st.download_button("💾 DESCARCĂ PDF ACUM", pdf.output(dest='S').encode('latin-1'), "Etichete_Express.pdf", "application/pdf")
