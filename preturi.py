import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# CONFIGURARE CULOARE BRAND
BRAND_GREEN = "#96c83f"

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Liquid Green Edition", layout="wide")

# CSS - APPLE LIQUID MODERN THEME cu accent pe verdele ales
st.markdown(f"""
    <style>
    .stApp {{
        background-color: #F8F9FA;
    }}
    
    /* Carduri etichete */
    [data-testid="column"] {{
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(12px);
        border-radius: 24px;
        padding: 20px !important;
        border: 1px solid rgba(0,0,0,0.05);
        box-shadow: 0 10px 40px rgba(0,0,0,0.03);
    }}

    /* Input-uri */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {{
        border-radius: 14px !important;
        border: 1px solid #E5E5E7 !important;
    }}
    
    .stTextInput input:focus {{
        border-color: {BRAND_GREEN} !important;
        box-shadow: 0 0 0 4px rgba(150, 200, 63, 0.2) !important;
    }}

    /* Buton principal */
    div.stButton > button {{
        width: 100%;
        background: {BRAND_GREEN};
        color: white;
        border: none;
        border-radius: 16px;
        height: 3.8em;
        font-weight: 700;
        transition: transform 0.2s ease;
    }}
    
    div.stButton > button:hover {{
        transform: scale(1.02);
        color: white;
    }}

    .stExpander {{
        border: none !important;
        background-color: rgba(0,0,0,0.02) !important;
        border-radius: 14px !important;
    }}
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
    # FUNDALUL ETICHETEI CU CULOAREA TA (#96c83f)
    img = Image.new('RGB', (W, H), color=BRAND_GREEN) 
    draw = ImageDraw.Draw(img)
    margine = 40
    
    # Corpul alb cu margini Liquid
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=85, fill="white")

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

    # Titlu Telefon
    txt_m = f"{row['Brand']} {row['Model']}"
    w_m = draw.textlength(txt_m, font=f_titlu)
    draw.text(((W - w_m) // 2, margine * 3.8), txt_m, fill="#1D1D1F", font=f_titlu)

    # Specificații
    y_pos = margine * 8
    specs = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Selfie", "Capacitate baterie"]
    for col in specs:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            draw.text((margine * 2.8, y_pos), f"{col}:", fill="#6E6E73", font=f_label)
            offset = draw.textlength(f"{col}: ", font=f_label)
            draw.text((margine * 2.8 + offset, y_pos), val, fill="#1D1D1F", font=f_valoare)
            y_pos += line_spacing

    # Sănătate Baterie
    draw.text((margine * 2.8, y_pos), "Sanatate baterie:", fill="#6E6E73", font=f_label)
    offset_bat = draw.textlength("Sanatate baterie: ", font=f_label)
    draw.text((margine * 2.8 + offset_bat, y_pos), f"{bat_val}%", fill="#1D1D1F", font=f_valoare)

    # Preț (Aliniat la bază)
    if pret_val:
        t1, t2, t3 = "Pret: ", f"{pret_val}", " lei"
        w1, w2, w3 = draw.textlength(t1, font=f_pret_text), draw.textlength(t2, font=f_pret_cifra), draw.textlength(t3, font=f_pret_text)
        total_w = w1 + w2 + w3
        start_x = (W - total_w) // 2
        y_base = pret_y + cifra_size 
        
        # Culoarea prețului (Verdele tău sau negru pentru contrast pe alb)
        c_p = BRAND_GREEN if BRAND_GREEN != "#FFFFFF" else "#000000"
        
        draw.text((start_x, y_base - pret_size), t1, fill=c_p, font=f_pret_text)
        draw.text((start_x + w1, y_base - cifra_size), t2, fill=c_p, font=f_pret_cifra)
        draw.text((start_x + w1 + w2, y_base - pret_size), t3, fill=c_p, font=f_pret_text)
        
        # B@Ag (Subtil)
        txt_bag = f"B{b_text}@Ag{ag_val}"
        w_bag = draw.textlength(txt_bag, font=f_bag)
        draw.text((W - margine * 3.5 - w_bag, y_base + 35), txt_bag, fill="#AEAEB2", font=f_bag)

    # Logo
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

# --- LOGICĂ ---
df = pd.read_excel("https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx")

st.sidebar.markdown(f"### <span style='color:{BRAND_GREEN}'>●</span> CONTROL PANOU", unsafe_allow_html=True)
zoom = st.sidebar.slider("Zoom Etichete", 200, 800, 380)

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
        
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            bat_choice = st.selectbox(f"Baterie %", battery_list, key=f"bat_{i}")
            b_input = st.text_input(f"Cod B", key=f"bt_{i}")
            t_size = st.number_input("Mărime Titlu", 10, 150, 48, key=f"tsz_{i}")
            f_size = st.number_input("Mărime Spec.", 10, 100, 28, key=f"sz_{i}")
        with c2:
            pret_input = st.text_input(f"Preț Lei", key=f"pr_{i}")
            ag_input = st.selectbox(f"Ag Val", ag_list, key=f"ag_{i}")
            fn = st.selectbox("Font Stil", FONT_NAMES, key=f"fn_{i}")
            c_size = st.number_input("Cifră Preț", 20, 300, 95, key=f"csz_{i}")

        with st.expander("🛠️ Ajustări Fine"):
            e1, e2 = st.columns(2)
            with e1:
                p_y = st.slider("Poziție Y Preț", 400, 1150, 850, key=f"py_{i}")
                p_size = st.slider("Mărime 'Pret:'", 20, 150, 55, key=f"psz_{i}")
                sp = st.slider("Spațiere", 10, 100, 42, key=f"sp_{i}")
            with e2:
                ls = st.slider("Scară Logo", 0.1, 2.0, 0.6, key=f"ls_{i}")
                lx = st.number_input("X Logo (100=C)", 0, 800, 100, key=f"lx_{i}")
                ly = st.number_input("Y Logo", 0, 1200, 1060, key=f"ly_{i}")

        current_img = creeaza_imagine_eticheta(r_data, t_size, f_size, sp, ls, lx, ly, fn, pret_input, p_y, p_size, c_size, b_input, ag_input, bat_choice)
        st.image(current_img, width=zoom)
        final_imgs.append(current_img)

st.markdown("<br>", unsafe_allow_html=True)
if st.button(f"🚀 GENERARE PDF FINAL ({BRAND_GREEN})"):
    canvas = Image.new('RGB', (2400, 1200))
    for i in range(3): canvas.paste(final_imgs[i], (i * 800, 0))
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    buf = io.BytesIO()
    canvas.save(buf, format='PNG')
    buf.seek(0)
    with open("temp_print.png", "wb") as f: f.write(buf.read())
    pdf.image("temp_print.png", x=5, y=5, w=287)
    st.download_button("💾 SALVEAZĂ PDF", pdf.output(dest='S').encode('latin-1'), "Etichete_Liquid_Green.pdf", "application/pdf")
