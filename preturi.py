import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Apple Liquid Edition", layout="wide")

# CSS - APPLE LIQUID MODERN THEME
st.markdown("""
    <style>
    /* Fundal general și fonturi */
    .stApp {
        background-color: #F5F5F7;
    }
    
    /* Carduri pentru etichete (Glassmorphism) */
    [data-testid="column"] {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 24px;
        padding: 20px !important;
        border: 1px solid rgba(0,0,0,0.05);
        box-shadow: 0 8px 32px 0 rgba(0,0,0,0.05);
    }

    /* Input-uri stilizate Apple */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
        border-radius: 12px !important;
        border: 1px solid #D2D2D7 !important;
        background-color: rgba(255,255,255,0.8) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .stTextInput input:focus {
        border-color: #0071E3 !important;
        box-shadow: 0 0 0 4px rgba(0,113,227,0.1) !important;
    }

    /* Butonul de generare */
    div.stButton > button {
        width: 100%;
        background: linear-gradient(180deg, #0077ED 0%, #0066CC 100%);
        color: white;
        border: none;
        border-radius: 15px;
        height: 3.5em;
        font-weight: 600;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 12px rgba(0,113,227,0.3);
    }

    /* Titluri secțiuni */
    h3 {
        color: #1D1D1F;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }

    /* Expander stilizat */
    .stExpander {
        border: none !important;
        background-color: rgba(0,0,0,0.03) !important;
        border-radius: 12px !important;
    }
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
    img = Image.new('RGB', (W, H), color=(204, 9, 21)) # Roșul ExpressCredit
    draw = ImageDraw.Draw(img)
    margine = 40
    # Cardul alb interior cu colțuri foarte rotunjite (Apple style)
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=80, fill="white")

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

    # Titlu
    txt_m = f"{row['Brand']} {row['Model']}"
    w_m = draw.textlength(txt_m, font=f_titlu)
    draw.text(((W - w_m) // 2, margine * 3.5), txt_m, fill=(29, 29, 31), font=f_titlu)

    # Specificații
    y_pos = margine * 7.5
    specs = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Selfie", "Capacitate baterie"]
    for col in specs:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            draw.text((margine * 2.5, y_pos), f"{col}:", fill="#424245", font=f_label)
            offset = draw.textlength(f"{col}: ", font=f_label)
            draw.text((margine * 2.5 + offset, y_pos), val, fill="#1D1D1F", font=f_valoare)
            y_pos += line_spacing

    # Sănătate Baterie
    draw.text((margine * 2.5, y_pos), "Sanatate baterie:", fill="#424245", font=f_label)
    offset_bat = draw.textlength("Sanatate baterie: ", font=f_label)
    draw.text((margine * 2.5 + offset_bat, y_pos), f"{bat_val}%", fill="#1D1D1F", font=f_valoare)

    # Preț aliniat la bază
    if pret_val:
        t1, t2, t3 = "Pret: ", f"{pret_val}", " lei"
        w1 = draw.textlength(t1, font=f_pret_text)
        w2 = draw.textlength(t2, font=f_pret_cifra)
        w3 = draw.textlength(t3, font=f_pret_text)
        total_w = w1 + w2 + w3
        start_x = (W - total_w) // 2
        y_base = pret_y + cifra_size 
        draw.text((start_x, y_base - pret_size), t1, fill="#CC0915", font=f_pret_text)
        draw.text((start_x + w1, y_base - cifra_size), t2, fill="#CC0915", font=f_pret_cifra)
        draw.text((start_x + w1 + w2, y_base - pret_size), t3, fill="#CC0915", font=f_pret_text)
        
        # B@Ag
        txt_bag = f"B{b_text}@Ag{ag_val}"
        w_bag = draw.textlength(txt_bag, font=f_bag)
        draw.text((W - margine * 3 - w_bag, y_base + 30), txt_bag, fill="#86868B", font=f_bag)

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

# --- APLICAȚIE ---
df = pd.read_excel("https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx")

st.sidebar.markdown("### ⚙️ SETĂRI VIZUALE")
zoom = st.sidebar.slider("Zoom Previzualizare", 200, 800, 380)

FONT_NAMES = ["Montserrat", "Roboto", "Poppins", "Oswald", "Inter"]
ag_list = [str(i) for i in range(1, 56)]
battery_list = [str(i) for i in range(100, 0, -1)]

col_main = st.columns(3)
final_imgs = []

for i in range(3):
    with col_main[i]:
        st.markdown(f"### 📱 Eticheta {i+1}")
        brand = st.selectbox(f"BRAND", sorted(df['Brand'].dropna().unique()), key=f"b_{i}")
        model = st.selectbox(f"MODEL", df[df['Brand'] == brand]['Model'].dropna().unique(), key=f"m_{i}")
        r_data = df[(df['Brand'] == brand) & (df['Model'] == model)].iloc[0]
        
        # Layout 2 Coloane Lizibil
        c1, c2 = st.columns(2)
        with c1:
            bat_choice = st.selectbox(f"BATERIE %", battery_list, key=f"bat_{i}")
            b_input = st.text_input(f"COD B", key=f"bt_{i}", placeholder="ex: 123")
            t_size = st.number_input("TITLU (px)", 10, 150, 48, key=f"tsz_{i}")
            f_size = st.number_input("SPEC. (px)", 10, 100, 28, key=f"sz_{i}")
        with c2:
            pret_input = st.text_input(f"PRET", key=f"pr_{i}", placeholder="lei")
            ag_input = st.selectbox(f"VAL AG", ag_list, key=f"ag_{i}")
            fn = st.selectbox("FONT", FONT_NAMES, key=f"fn_{i}")
            c_size = st.number_input("CIFRĂ (px)", 20, 300, 90, key=f"csz_{i}")

        with st.expander("🛠️ POZIȚIONARE & LOGO"):
            e1, e2 = st.columns(2)
            with e1:
                p_y = st.slider("Înălțime Preț", 400, 1150, 850, key=f"py_{i}")
                p_size = st.slider("Mărime 'Pret:'", 20, 150, 55, key=f"psz_{i}")
                sp = st.slider("Spațiere Rânduri", 10, 100, 42, key=f"sp_{i}")
            with e2:
                ls = st.slider("Scară Logo", 0.1, 2.0, 0.6, key=f"ls_{i}")
                lx = st.number_input("X Logo (100=C)", 0, 800, 100, key=f"lx_{i}")
                ly = st.number_input("Y Logo", 0, 1200, 1060, key=f"ly_{i}")

        current_img = creeaza_imagine_eticheta(r_data, t_size, f_size, sp, ls, lx, ly, fn, pret_input, p_y, p_size, c_size, b_input, ag_input, bat_choice)
        st.image(current_img, width=zoom, use_container_width=False)
        final_imgs.append(current_img)

st.markdown("---")
if st.button(" GENEREAZĂ PDF APPLE STYLE"):
    canvas = Image.new('RGB', (2400, 1200))
    for i in range(3): canvas.paste(final_imgs[i], (i * 800, 0))
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    buf = io.BytesIO()
    canvas.save(buf, format='PNG')
    buf.seek(0)
    with open("temp_print.png", "wb") as f: f.write(buf.read())
    pdf.image("temp_print.png", x=5, y=5, w=287)
    st.download_button("💾 DESCARCĂ PDF", pdf.output(dest='S').encode('latin-1'), "Etichete_Premium.pdf", "application/pdf")
