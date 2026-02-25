import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# ==========================================
# CONFIGURARE CULORI BRAND
# ==========================================
COLOR_SITE_BG = "#96c83f"
COLOR_ETICHETA_BG = "#cf1f2f"
COLOR_TEXT_GLOBAL = "#000000"

st.set_page_config(page_title="ExpressCredit - Manual Liquid", layout="wide")

# ==========================================
# CSS - INTERFAȚĂ
# ==========================================
st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_SITE_BG}; color: {COLOR_TEXT_GLOBAL} !important; }}
    h1, h2, h3, p, span, label, div {{ color: {COLOR_TEXT_GLOBAL} !important; }}
    [data-testid="column"] {{
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 15px !important;
        border: 1px solid rgba(255,255,255,0.4);
        margin-bottom: 10px;
    }}
    div.stButton > button {{
        width: 100%; background: #FFFFFF; color: {COLOR_TEXT_GLOBAL} !important;
        border: 2px solid {COLOR_TEXT_GLOBAL}; border-radius: 16px; font-weight: 800;
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
    # AM MODIFICAT LATIMEA: de la 800 la 600 pentru a fi mai ingusta
    W, H = 600, 1150 
    img = Image.new('RGB', (W, H), color=COLOR_ETICHETA_BG) 
    draw = ImageDraw.Draw(img)
    margine = 30
    
    PRET_Y_FIX = 780       
    PRET_SIZE_FIX = 45     
    CIFRA_SIZE_FIX = 95   
    B_AG_SIZE_FIX = 38     

    # Fundal alb
    draw.rounded_rectangle([margine, margine, W-margine, H-200], radius=70, fill="white")

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
            f_titlu = f_label = f_valoare = f_pret_text = f_pret_cifra = f_bag = ImageFont.load_default()
    except:
        f_titlu = f_label = f_valoare = f_pret_text = f_pret_cifra = f_bag = ImageFont.load_default()

    # TITLU (Brand & Model)
    txt_brand = str(row['Brand'])
    txt_model = str(row['Model'])
    draw.text(((W - draw.textlength(txt_brand, font=f_titlu)) // 2, margine * 3), txt_brand, fill="#000000", font=f_titlu)
    draw.text(((W - draw.textlength(txt_model, font=f_titlu)) // 2, margine * 3 + titlu_size), txt_model, fill="#000000", font=f_titlu)

    # SPECIFICAȚII
    y_pos = margine * 11 
    specs = [
        ("Display", row.get("Display", "-")),
        ("OS", row.get("OS", "-")),
        ("Stocare", stocare_manuala),
        ("RAM", ram_manual),
        ("Camera", row.get("Camera principala", "-")),
        ("Baterie", row.get("Capacitate baterie", "-")),
        ("Sanatate", f"{bat_val}%")
    ]

    for label, val in specs:
        t_label = f"{label}: "
        t_val = str(val)[:20] # Limitare text sa nu iasa din eticheta ingusta
        draw.text((margine * 1.5, y_pos), t_label, fill="#333333", font=f_label)
        offset = draw.textlength(t_label, font=f_label)
        draw.text((margine * 1.5 + offset, y_pos), t_val, fill="#000000", font=f_valoare)
        y_pos += line_spacing

    # PREȚ
    if pret_val:
        t1, t2, t3 = "Pret: ", f"{pret_val}", " lei"
        w1, w2, w3 = draw.textlength(t1, font=f_pret_text), draw.textlength(t2, font=f_pret_cifra), draw.textlength(t3, font=f_pret_text)
        start_x = (W - (w1 + w2 + w3)) // 2
        draw.text((start_x, PRET_Y_FIX + 30), t1, fill="#000000", font=f_pret_text)
        draw.text((start_x + w1, PRET_Y_FIX), t2, fill="#000000", font=f_pret_cifra)
        draw.text((start_x + w1 + w2, PRET_Y_FIX + 30), t3, fill="#000000", font=f_pret_text)
        
        txt_bag = f"B{b_text}@Ag{ag_val}"
        w_bag = draw.textlength(txt_bag, font=f_bag)
        draw.text(((W - w_bag) // 2, PRET_Y_FIX + 110), txt_bag, fill="#333333", font=f_bag)

    # LOGO
    try:
        url_l = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo_resp = requests.get(url_l, timeout=5)
        logo = Image.open(io.BytesIO(logo_resp.content)).convert("RGBA")
        lw = int(W * 0.8) 
        lh = int(lw * (logo.size[1] / logo.size[0]))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(logo, ((W - lw) // 2, 920), logo)
    except: pass
        
    return img

# ==========================================
# LOGICĂ STREAMLIT
# ==========================================
url_sheet = "https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx"
df = pd.read_excel(url_sheet)

st.sidebar.title("Setări")
zoom = st.sidebar.slider("Zoom Previzualizare", 100, 500, 300)

FONT_NAMES = ["Montserrat", "Roboto", "Inter", "Poppins"]
ag_list = [str(i) for i in range(1, 56)]
battery_list = [str(i) for i in range(100, 0, -1)]

col_main = st.columns(3)
final_imgs = []

for i in range(3):
    with col_main[i]:
        st.subheader(f"Eticheta {i+1}")
        brand = st.selectbox(f"Brand", sorted(df['Brand'].dropna().unique()), key=f"b_{i}")
        model = st.selectbox(f"Model", df[df['Brand'] == brand]['Model'].dropna().unique(), key=f"m_{i}")
        r_data = df[(df['Brand'] == brand) & (df['Model'] == model)].iloc[0]
        
        pret_input = st.text_input(f"Preț Lei", key=f"pr_{i}")
        b_input = st.text_input(f"Cod B", key=f"bt_{i}")
        
        with st.expander("Mai multe detalii"):
            stoc_manual = st.selectbox("Stocare", STOCARE_OPTIUNI, index=4, key=f"stoc_{i}")
            ram_manual = st.selectbox("RAM", RAM_OPTIUNI, index=3, key=f"ram_{i}")
            bat_choice = st.selectbox(f"Baterie %", battery_list, key=f"bat_{i}")
            ag_input = st.selectbox(f"Valoare Ag", ag_list, key=f"ag_{i}")
            t_size = st.number_input("Mărime Titlu", 10, 80, 42, key=f"tsz_{i}")
            f_size = st.number_input("Mărime Spec.", 10, 50, 24, key=f"sz_{i}")
            sp = st.slider("Spațiere", 10, 80, 38, key=f"sp_{i}")
            fn = st.selectbox("Font", FONT_NAMES, key=f"fn_{i}")

        current_img = creeaza_imagine_eticheta(r_data, t_size, f_size, sp, fn, pret_input, b_input, ag_input, bat_choice, stoc_manual, ram_manual)
        st.image(current_img, width=zoom)
        final_imgs.append(current_img)

# ==========================================
# GENERARE PDF (3 PE LĂȚIME A4 VERTICAL)
# ==========================================
st.markdown("---")
if st.button("🚀 GENEREAZĂ PDF A4 VERTICAL (3 PE RÂND)"):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # Parametrii pentru 3 etichete pe latime
    # A4 are 210mm. 3 etichete x 65mm = 195mm. Margini ramase = 15mm (7.5mm stanga/dreapta)
    latime_mm = 63 
    inaltime_mm = latime_mm * (1150/600) # Pastram proportia imaginii (~120mm)
    x_start = 7
    y_start = 20
    spatiu_intre = 2 # mm intre etichete
    
    for i in range(len(final_imgs)):
        buf = io.BytesIO()
        final_imgs[i].save(buf, format='PNG')
        buf.seek(0)
        
        # Salvare temporara pentru FPDF
        temp_name = f"temp_{i}.png"
        with open(temp_name, "wb") as f:
            f.write(buf.getbuffer())
        
        # Calcul pozitie X: x_start + (latime + spatiu) * i
        current_x = x_start + (latime_mm + spatiu_intre) * i
        pdf.image(temp_name, x=current_x, y=y_start, w=latime_mm)

    pdf_bytes = pdf.output(dest='S')
    if isinstance(pdf_bytes, str): pdf_bytes = pdf_bytes.encode('latin-1')
    
    st.download_button("💾 DESCARCĂ PDF", pdf_bytes, "Etichete_A4_3_pe_rand.pdf", "application/pdf")
