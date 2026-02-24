import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# ==========================================
# CONFIGURARE CULORI BRAND
# ==========================================
COLOR_SITE_BG = "#96c83f"      # Verdele lime pentru fundalul site-ului
COLOR_ETICHETA_BG = "#cf1f2f"  # Roșul pentru bordura etichetei
COLOR_TEXT_GLOBAL = "#000000"  # NEGRU TOTAL (SITE + ETICHETĂ)

# Configurare pagină Streamlit
st.set_page_config(page_title="ExpressCredit - Liquid Edition", layout="wide")

# ==========================================
# CSS - INTERFAȚĂ APPLE LIQUID CU TEXT NEGRU
# ==========================================
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {COLOR_SITE_BG};
        color: {COLOR_TEXT_GLOBAL} !important;
    }}
    
    h1, h2, h3, p, span, label, div {{
        color: {COLOR_TEXT_GLOBAL} !important;
    }}

    [data-testid="column"] {{
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: blur(15px);
        border-radius: 28px;
        padding: 25px !important;
        border: 1px solid rgba(255,255,255,0.4);
        box-shadow: 0 12px 40px rgba(0,0,0,0.12);
        margin-bottom: 20px;
    }}

    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {{
        border-radius: 14px !important;
        border: 1px solid rgba(0,0,0,0.2) !important;
        background-color: white !important;
        color: {COLOR_TEXT_GLOBAL} !important;
    }}

    div.stButton > button {{
        width: 100%;
        background: #FFFFFF;
        color: {COLOR_TEXT_GLOBAL} !important;
        border: 2px solid {COLOR_TEXT_GLOBAL};
        border-radius: 16px;
        height: 4em;
        font-weight: 800;
    }}
    
    div.stButton > button:hover {{
        background: {COLOR_TEXT_GLOBAL};
        color: #FFFFFF !important;
    }}

    .stExpander {{
        border: none !important;
        background-color: rgba(255,255,255,0.4) !important;
        border-radius: 16px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# FUNCȚII GENERARE FONT ȘI IMAGINE
# ==========================================
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
    img = Image.new('RGB', (W, H), color=COLOR_ETICHETA_BG) 
    draw = ImageDraw.Draw(img)
    margine = 40
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=90, fill="white")

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

    # Brand & Model - Negru
    txt_m = f"{row['Brand']} {row['Model']}"
    w_m = draw.textlength(txt_m, font=f_titlu)
    draw.text(((W - w_m) // 2, margine * 4), txt_m, fill="#000000", font=f_titlu)

    # Specificații - Negru
    y_pos = margine * 8.5
    specs = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Selfie", "Capacitate baterie"]
    for col in specs:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            draw.text((margine * 3, y_pos), f"{col}:", fill="#333333", font=f_label)
            offset = draw.textlength(f"{col}: ", font=f_label)
            draw.text((margine * 3 + offset, y_pos), val, fill="#000000", font=f_valoare)
            y_pos += line_spacing

    draw.text((margine * 3, y_pos), "Sanatate baterie:", fill="#333333", font=f_label)
    offset_bat = draw.textlength("Sanatate baterie: ", font=f_label)
    draw.text((margine * 3 + offset_bat, y_pos), f"{bat_val}%", fill="#000000", font=f_valoare)

    # PREȚ - MODIFICAT ÎN NEGRU
    if pret_val:
        t1, t2, t3 = "Pret: ", f"{pret_val}", " lei"
        w1, w2, w3 = draw.textlength(t1, font=f_pret_text), draw.textlength(t2, font=f_pret_cifra), draw.textlength(t3, font=f_pret_text)
        total_w = w1 + w2 + w3
        start_x = (W - total_w) // 2
        y_base = pret_y + cifra_size 
        
        # Aici am schimbat fill din COLOR_ETICHETA_BG în #000000
        draw.text((start_x, y_base - pret_size), t1, fill="#000000", font=f_pret_text)
        draw.text((start_x + w1, y_base - cifra_size), t2, fill="#000000", font=f_pret_cifra)
        draw.text((start_x + w1 + w2, y_base - pret_size), t3, fill="#000000", font=f_pret_text)
        
        txt_bag = f"B{b_text}@Ag{ag_val}"
        w_bag = draw.textlength(txt_bag, font=f_bag)
        draw.text((W - margine * 4 - w_bag, y_base + 35), txt_bag, fill="#333333", font=f_bag)

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

# ==========================================
# LOGICĂ APLICAȚIE
# ==========================================
df = pd.read_excel("https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx")

st.sidebar.markdown(f"### <span style='color:black'>●</span> SETĂRI VIZUALE", unsafe_allow_html=True)
zoom = st.sidebar.slider("Zoom Previzualizare", 200, 800, 380)

FONT_NAMES = ["Montserrat", "Roboto", "Inter", "Poppins", "Anton"]
ag_list = [str(i) for i in range(1, 56)]
battery_list = [str(i) for i in range(100, 0, -1)]

col_main = st.columns(3)
final_imgs = []

for i in range(3):
    with col_main[i]:
        st.markdown(f"### 📱 Eticheta {i+1}")
        brand = st.selectbox(f"Brand", sorted(df['Brand'].dropna().unique()), key=f"b_{i}")
        model = st.selectbox(f"Model", df[df['Brand'] == brand]['Model'].dropna().unique(), key=f"m_{i}")
        r_data = df[(df['Brand'] == brand) & (df['Model'] == model)].iloc[0]
        
        c1, c2 = st.columns(2)
        with c1:
            bat_choice = st.selectbox(f"Baterie %", battery_list, key=f"bat_{i}")
            b_input = st.text_input(f"Cod B", key=f"bt_{i}")
            t_size = st.number_input("Mărime Titlu", 10, 150, 48, key=f"tsz_{i}")
            f_size = st.number_input("Mărime Spec.", 10, 100, 28, key=f"sz_{i}")
        with c2:
            pret_input = st.text_input(f"Preț Lei", key=f"pr_{i}")
            ag_input = st.selectbox(f"Valoare Ag", ag_list, key=f"ag_{i}")
            fn = st.selectbox("Font", FONT_NAMES, key=f"fn_{i}")
            c_size = st.number_input("Cifră Preț", 20, 300, 95, key=f"csz_{i}")

        with st.expander("🛠️ POZIȚIONARE & LOGO"):
            e1, e2 = st.columns(2)
            with e1:
                p_y = st.slider("Înălțime Preț", 400, 1150, 850, key=f"py_{i}")
                p_size = st.slider("Mărime 'Pret:'", 20, 150, 55, key=f"psz_{i}")
                sp = st.slider("Spațiere", 10, 100, 42, key=f"sp_{i}")
            with e2:
                ls = st.slider("Scară Logo", 0.1, 2.0, 0.6, key=f"ls_{i}")
                lx = st.number_input("X Logo", 0, 800, 100, key=f"lx_{i}")
                ly = st.number_input("Y Logo", 0, 1200, 1060, key=f"ly_{i}")

        current_img = creeaza_imagine_eticheta(r_data, t_size, f_size, sp, ls, lx, ly, fn, pret_input, p_y, p_size, c_size, b_input, ag_input, bat_choice)
        st.image(current_img, width=zoom)
        final_imgs.append(current_img)

st.markdown("---")
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
    st.download_button("💾 DESCARCĂ PDF", pdf.output(dest='S').encode('latin-1'), "Etichete.pdf", "application/pdf")
