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

st.set_page_config(page_title="ExpressCredit - Full Specs Nano", layout="wide")

# ==========================================
# CSS - INTERFAȚĂ
# ==========================================
st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_SITE_BG}; }}
    [data-testid="column"] {{
        background: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 10px !important;
        margin-bottom: 5px;
    }}
    h3 {{ color: #000 !important; font-weight: 800 !important; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# FUNCȚII ȘI RESURSE
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

def creeaza_imagine_eticheta(row, t_size, f_size, sp, font_name, pret, b_cod, ag_val, bat_val, stoc_man, ram_man):
    # Pânză calibrată pentru tot conținutul: 256x560 pixeli
    W, H = 256, 560 
    img = Image.new('RGB', (W, H), color=COLOR_ETICHETA_BG) 
    draw = ImageDraw.Draw(img)
    margine_ext = 10
    
    # Fundal alb
    draw.rounded_rectangle([margine_ext, margine_ext, W-margine_ext, H-80], radius=20, fill="white")

    f_bytes_reg = get_font_bytes(font_name, "Regular")
    f_bytes_bold = get_font_bytes(font_name, "Bold") or f_bytes_reg
    
    try:
        f_titlu = ImageFont.truetype(io.BytesIO(f_bytes_bold), t_size)
        f_label = ImageFont.truetype(io.BytesIO(f_bytes_bold), f_size)
        f_valoare = ImageFont.truetype(io.BytesIO(f_bytes_reg), f_size)
        f_pret_text = ImageFont.truetype(io.BytesIO(f_bytes_bold), 18)
        f_pret_cifra = ImageFont.truetype(io.BytesIO(f_bytes_bold), 42) # Cifre puțin mai mari
        f_bag = ImageFont.truetype(io.BytesIO(f_bytes_bold), 14)
    except:
        f_titlu = f_label = f_valoare = f_pret_text = f_pret_cifra = f_bag = ImageFont.load_default()

    # --- TITLU (BRAND & MODEL) ---
    y_ptr = margine_ext * 2.5
    for txt in [str(row['Brand']), str(row['Model'])]:
        w_txt = draw.textlength(txt, font=f_titlu)
        draw.text(((W - w_txt) // 2, y_ptr), txt, fill="#000000", font=f_titlu)
        y_ptr += t_size + 2

    # --- LISTĂ SPECIFICAȚII (Include Procesor) ---
    y_ptr += 10 
    specs = [
        ("Display", row.get("Display", "-")),
        ("Procesor", row.get("Chipset", "-")), # Procesor adăugat
        ("Stocare", stoc_man),
        ("RAM", ram_man),
        ("Camera", row.get("Camera principala", "-")),
        ("Baterie", row.get("Capacitate baterie", "-")),
        ("Sanatate", f"{bat_val}%")
    ]

    for lab, val in specs:
        t_lab = f"{lab}: "
        draw.text((margine_ext * 2, y_ptr), t_lab, fill="#444444", font=f_label)
        offset = draw.textlength(t_lab, font=f_label)
        draw.text((margine_ext * 2 + offset, y_ptr), str(val), fill="#000000", font=f_valoare)
        y_ptr += sp

    # --- ZONA PREȚ ALINIATĂ ---
    y_pret = H - 175
    if pret:
        t_label = "Pret: "
        t_suma = f"{pret}"
        t_moneda = " lei"
        
        # Calculăm lățimile pentru centrare perfectă
        w_l = draw.textlength(t_label, font=f_pret_text)
        w_s = draw.textlength(t_suma, font=f_pret_cifra)
        w_m = draw.textlength(t_moneda, font=f_pret_text)
        
        total_w = w_l + w_s + w_m
        start_x = (W - total_w) // 2
        
        # Desenăm elementele pe aceeași linie de bază (baseline)
        draw.text((start_x, y_pret + 15), t_label, fill="#000000", font=f_pret_text)
        draw.text((start_x + w_l, y_pret), t_suma, fill="#000000", font=f_pret_cifra)
        draw.text((start_x + w_l + w_s, y_pret + 15), t_moneda, fill="#000000", font=f_pret_text)
        
        # Codul B și AG
        txt_bag = f"B{b_cod}@Ag{ag_val}"
        w_bag = draw.textlength(txt_bag, font=f_bag)
        draw.text(((W - w_bag) // 2, y_pret + 55), txt_bag, fill="#333333", font=f_bag)

    # --- LOGO ---
    try:
        url_l = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo_res = requests.get(url_l, timeout=5)
        logo = Image.open(io.BytesIO(logo_res.content)).convert("RGBA")
        lw = int(W * 0.65)
        lh = int(lw * (logo.size[1] / logo.size[0]))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(logo, ((W - lw) // 2, H - 65), logo)
    except: pass
        
    return img

# ==========================================
# LOGICĂ STREAMLIT
# ==========================================
url_sheet = "https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx"
df = pd.read_excel(url_sheet)

st.sidebar.header("⚙️ Setări")
zoom_val = st.sidebar.slider("Previzualizare", 100, 600, 300)

col_labels = st.columns(3)
final_imgs = []

for i in range(3):
    with col_labels[i]:
        st.subheader(f"Eticheta {i+1}")
        b_sel = st.selectbox(f"Brand", sorted(df['Brand'].dropna().unique()), key=f"br_{i}")
        m_sel = st.selectbox(f"Model", df[df['Brand'] == b_sel]['Model'].dropna().unique(), key=f"mo_{i}")
        r_data = df[(df['Brand'] == b_sel) & (df['Model'] == m_sel)].iloc[0]
        
        p_val = st.text_input(f"Preț Lei", key=f"pr_{i}")
        b_val = st.text_input(f"Cod B", value="001", key=f"bc_{i}")
        
        with st.expander("Control Font (Max 500)"):
            ts = st.number_input("Mărime Titlu", 2, 500, 20, key=f"ts_{i}")
            fs = st.number_input("Mărime Specificații", 2, 500, 10, key=f"fs_{i}")
            ss = st.slider("Spațiere", 2, 500, 12, key=f"ss_{i}")
            
            stoc = st.selectbox("Stocare", STOCARE_OPTIUNI, index=4, key=f"st_{i}")
            ram = st.selectbox("RAM", RAM_OPTIUNI, index=3, key=f"ra_{i}")
            bat = st.selectbox("Sănătate Bat. %", [str(x) for x in range(100, 69, -1)], key=f"ba_{i}")
            ag = st.selectbox("Cod Ag", [str(x) for x in range(1, 56)], key=f"ag_{i}")
            fn = st.selectbox("Font", ["Montserrat", "Roboto", "Poppins", "Anton"], key=f"fn_{i}")

        img_res = creeaza_imagine_eticheta(r_data, ts, fs, ss, fn, p_val, b_val, ag, bat, stoc, ram)
        st.image(img_res, width=zoom_val)
        final_imgs.append(img_res)

st.markdown("---")
if st.button("🚀 GENEREAZĂ PDF FINAL"):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    w_mm, x_off, y_off, gap = 62, 8, 15, 2
    for idx, f_img in enumerate(final_imgs):
        buf = io.BytesIO()
        f_img.save(buf, format='PNG')
        buf.seek(0)
        t_path = f"temp_{idx}.png"
        with open(t_path, "wb") as f: f.write(buf.getbuffer())
        pdf.image(t_path, x=x_off + (idx * (w_mm + gap)), y=y_off, w=w_mm)
    
    pdf_bytes = pdf.output(dest='S')
    if isinstance(pdf_bytes, str): pdf_bytes = pdf_bytes.encode('latin-1')
    st.download_button("💾 DESCARCĂ PDF", pdf_bytes, "Etichete.pdf", "application/pdf")
