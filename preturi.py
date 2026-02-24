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
COLOR_TEXT_GLOBAL = "#000000"  # NEGRU TOTAL

st.set_page_config(page_title="ExpressCredit - Manual Liquid", layout="wide")

# ==========================================
# CSS - INTERFAȚĂ APPLE LIQUID
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
        transition: all 0.3s ease;
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
# CONSTANTE ȘI FUNCȚII
# ==========================================
STOCARE_OPTIUNI = ["8 GB", "16 GB", "32 GB", "64 GB", "128 GB", "256 GB", "512 GB", "1 TB"]
RAM_OPTIUNI = ["1 GB", "2 GB", "3 GB", "4 GB", "6 GB", "8 GB", "12 GB", "16 GB", "24 GB", "32 GB"]

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

def creeaza_imagine_eticheta(row, titlu_size, font_size, line_spacing, font_name, pret_val, b_text, ag_val, bat_val, stocare_manuala, ram_manual):
    W, H = 800, 1200
    img = Image.new('RGB', (W, H), color=COLOR_ETICHETA_BG) 
    draw = ImageDraw.Draw(img)
    margine = 40
    
    # --- VALORI BLOCATE (POZITIONARE FIXA) ---
    PRET_Y_FIX = 810       # Pozitie verticala pret
    PRET_SIZE_FIX = 50     # Dimensiune "Pret:" si "lei"
    CIFRA_SIZE_FIX = 105   # Dimensiune cifra pret
    B_AG_SIZE_FIX = 42     # Dimensiune cod B@Ag
    # -----------------------------------------

    # Fundalul alb rotunjit
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=90, fill="white")

    f_reg_bytes = get_font_bytes(font_name, "Regular")
    f_bold_bytes = get_font_bytes(font_name, "Bold") or f_reg_bytes
    
    try:
        if f_reg_bytes:
            f_titlu = ImageFont.truetype(io.BytesIO(f_bold_bytes), titlu_size)
            f_label = ImageFont.truetype(io.BytesIO(f_bold_bytes), font_size)
            f_valoare = ImageFont.truetype(io.BytesIO(f_reg_bytes), font_size)
            f_pret_text = ImageFont.truetype(io.BytesIO(f_bold_bytes), PRET_SIZE_FIX)
            f_pret_cifra = ImageFont.truetype(io.BytesIO(f_bold_bytes), CIFRA_SIZE_FIX)
            f_bag = ImageFont.truetype(io.BytesIO(f_bold_bytes), B_AG_SIZE_FIX)
        else:
            path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            f_titlu = ImageFont.truetype(path, titlu_size)
            f_label = ImageFont.truetype(path, font_size)
            f_valoare = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            f_pret_text = ImageFont.truetype(path, PRET_SIZE_FIX)
            f_pret_cifra = ImageFont.truetype(path, CIFRA_SIZE_FIX)
            f_bag = ImageFont.truetype(path, B_AG_SIZE_FIX)
    except:
        f_titlu = f_label = f_valoare = f_pret_text = f_pret_cifra = f_bag = ImageFont.load_default()

    # TITLU
    txt_brand = str(row['Brand'])
    txt_model = str(row['Model'])
    draw.text(((W - draw.textlength(txt_brand, font=f_titlu)) // 2, margine * 2.5), txt_brand, fill="#000000", font=f_titlu)
    draw.text(((W - draw.textlength(txt_model, font=f_titlu)) // 2, margine * 2.5 + titlu_size), txt_model, fill="#000000", font=f_titlu)

    # SPECIFICAȚII
    y_pos = margine * 10 
    specs = [
        ("Display", row.get("Display", "-")),
        ("OS", row.get("OS", "-")),
        ("Procesor", row.get("Procesor", "-")),
        ("Stocare", stocare_manuala),
        ("RAM", ram_manual),
        ("Camera principala", row.get("Camera principala", "-")),
        ("Selfie", row.get("Selfie", "-")),
        ("Capacitate baterie", row.get("Capacitate baterie", "-")),
        ("Sanatate baterie", f"{bat_val}%")
    ]

    for label, val in specs:
        t_label = f"{label}: "
        t_val = str(val) if pd.notna(val) else "-"
        draw.text((margine * 1.5, y_pos), t_label, fill="#333333", font=f_label)
        offset = draw.textlength(t_label, font=f_label)
        draw.text((margine * 1.5 + offset, y_pos), t_val, fill="#000000", font=f_valoare)
        y_pos += line_spacing

    # PREȚ (BLOCAT)
    if pret_val:
        t1, t2, t3 = "Pret: ", f"{pret_val}", " lei"
        w1, w2, w3 = draw.textlength(t1, font=f_pret_text), draw.textlength(t2, font=f_pret_cifra), draw.textlength(t3, font=f_pret_text)
        start_x = (W - (w1 + w2 + w3)) // 2
        y_base = PRET_Y_FIX
        
        # Aliniere pe aceeasi linie de baza (baseline)
        draw.text((start_x, y_base + (CIFRA_SIZE_FIX - PRET_SIZE_FIX) - 5), t1, fill="#000000", font=f_pret_text)
        draw.text((start_x + w1, y_base), t2, fill="#000000", font=f_pret_cifra)
        draw.text((start_x + w1 + w2, y_base + (CIFRA_SIZE_FIX - PRET_SIZE_FIX) - 5), t3, fill="#000000", font=f_pret_text)
        
        # RUBRICA B@Ag (BLOCATĂ ȘI CENTRATĂ)
        txt_bag = f"B{b_text}@Ag{ag_val}"
        w_bag = draw.textlength(txt_bag, font=f_bag)
        draw.text(((W - w_bag) // 0, y_base + CIFRA_SIZE_FIX + 15), txt_bag, fill="#333333", font=f_bag)

    # LOGO
    try:
        url_l = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo_resp = requests.get(url_l, timeout=5)
        logo = Image.open(io.BytesIO(logo_resp.content)).convert("RGBA")
        lw = int(W * 0.85) 
        lh = int(lw * (logo.size[1] / logo.size[0]))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(logo, ((W - lw) // 2, 1000), logo)
    except: pass
        
    return img

# ==========================================
# LOGICĂ APLICAȚIE
# ==========================================
url_sheet = "https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx"
df = pd.read_excel(url_sheet)

st.sidebar.markdown(f"### <span style='color:black'>●</span> CONTROL PANEL", unsafe_allow_html=True)
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
            stoc_manual = st.selectbox("Stocare", STOCARE_OPTIUNI, key=f"stoc_{i}")
            bat_choice = st.selectbox(f"Baterie %", battery_list, key=f"bat_{i}")
            b_input = st.text_input(f"Cod B", key=f"bt_{i}")
            t_size = st.number_input("Mărime Titlu", 10, 150, 48, key=f"tsz_{i}")
            
        with c2:
            ram_manual = st.selectbox("RAM", RAM_OPTIUNI, key=f"ram_{i}")
            pret_input = st.text_input(f"Preț Lei", key=f"pr_{i}")
            ag_input = st.selectbox(f"Valoare Ag", ag_list, key=f"ag_{i}")
            f_size = st.number_input("Mărime Spec.", 10, 100, 28, key=f"sz_{i}")

        with st.expander("🛠️ AJUSTARE DESIGN SPECIFICAȚII"):
            sp = st.slider("Spațiere rânduri", 10, 100, 42, key=f"sp_{i}")
            fn = st.selectbox("Font", FONT_NAMES, key=f"fn_{i}")

        # Apelare functie cu parametrii fixati intern
        current_img = creeaza_imagine_eticheta(r_data, t_size, f_size, sp, fn, pret_input, b_input, ag_input, bat_choice, stoc_manual, ram_manual)
        st.image(current_img, width=zoom)
        final_imgs.append(current_img)

st.markdown("---")
if st.button("🚀 GENEREAZĂ PDF FINAL"):
    canvas = Image.new('RGB', (2400, 1200))
    for i in range(3): 
        canvas.paste(final_imgs[i], (i * 800, 0))
    
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    
    buf = io.BytesIO()
    canvas.save(buf, format='PNG')
    buf.seek(0)
    
    with open("temp_print.png", "wb") as f: 
        f.write(buf.read())
        
    pdf.image("temp_print.png", x=5, y=5, w=287)
    pdf_output = pdf.output(dest='S').encode('latin-1')
    
    st.download_button("💾 DESCARCĂ PDF", pdf_output, "Etichete.pdf", "application/pdf")


