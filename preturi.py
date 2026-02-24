import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Mega Font System", layout="wide")

# CSS pentru panou de reglaje optimizat
st.markdown("""
    <style>
    [data-testid="column"] { padding: 5px !important; }
    .stSlider label, .stSelectbox label, .stNumberInput label {
        font-size: 20px !important;
        font-weight: 800 !important;
    }
    div.stButton > button { height: 4em; font-weight: bold; background-color: #cc0915; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- LISTA CELOR 100 DE FONTURI (Categorii variate) ---
FONT_NAMES = [
    "Roboto", "Open Sans", "Montserrat", "Lato", "Oswald", "Raleway", "Ubuntu", "Nunito", "Playfair Display", "Merriweather",
    "Bebas Neue", "Lora", "Kanit", "Fira Sans", "Quicksand", "Anton", "Josefin Sans", "Libre Baskerville", "Arvo", "Archivo",
    "Poppins", "Inter", "Source Sans Pro", "Dancing Script", "Pacifico", "Caveat", "Satisfy", "Lobster", "Abril Fatface", "Righteous",
    "Patua One", "Permanent Marker", "Shadows Into Light", "Amatic SC", "Cinzel", "Exo 2", "Orbitron", "Questrial", "Saira", "Teko",
    "Fjalla One", "Courgette", "Great Vibes", "Kaushan Script", "Yellowtail", "Bree Serif", "Alfa Slab One", "Crete Round", "Domine", "Old Standard TT",
    "Vollkorn", "Cardo", "Gelasio", "Crimson Text", "Philosopher", "Tinos", "Signika", "Asap", "Assistant", "Muli",
    "Catamaran", "Work Sans", "Dosis", "Titillium Web", "PT Sans Narrow", "Inconsolata", "Bitter", "Play", "Alegreya", "Chivo",
    "Rubik", "Mukta", "Hind", "Nanum Gothic", "Heebo", "Karla", "Spectral", "Zilla Slab", "Prata", "EB Garamond",
    "Cormorant", "Prompt", "Monda", "Rajdhani", "Jost", "Manrope", "Outfit", "Space Grotesk", "Sora", "Public Sans",
    "Syne", "Fraunces", "Biorhyme", "Space Mono", "JetBrains Mono", "Special Elite", "Bangers", "Luckiest Guy", "Press Start 2P", "Monoton"
]

@st.cache_data(show_spinner=False)
def get_font_bytes(font_name, weight):
    # Mapare pentru locațiile Google Fonts pe GitHub (majoritatea sunt în 'ofl' sau 'apache')
    folders = ['ofl', 'apache', 'googlefonts']
    clean_name = font_name.lower().replace(" ", "")
    
    for folder in folders:
        url = f"https://github.com/google/fonts/raw/main/{folder}/{clean_name}/{font_name.replace(' ', '')}-{weight}.ttf"
        try:
            r = requests.get(url, timeout=3)
            if r.status_code == 200: return r.content
        except: continue
    return None

def creeaza_imagine_eticheta(row, font_size, line_spacing, l_scale, l_x_manual, l_y, font_name, font_style):
    W, H = 800, 1200
    img = Image.new('RGB', (W, H), color=(204, 9, 21))
    draw = ImageDraw.Draw(img)
    margine = 40
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=60, fill="white")

    # Sistem de încărcare font cu fallback solid
    f_bytes = get_font_bytes(font_name, font_style)
    f_bold_bytes = get_font_bytes(font_name, "Bold") or f_bytes
    
    try:
        if f_bytes:
            f_titlu = ImageFont.truetype(io.BytesIO(f_bold_bytes), int(font_size * 1.3))
            f_label = ImageFont.truetype(io.BytesIO(f_bold_bytes), font_size)
            f_valoare = ImageFont.truetype(io.BytesIO(f_bytes), font_size)
        else:
            # Fallback local dacă GitHub nu răspunde
            path_b = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            f_titlu = ImageFont.truetype(path_b, int(font_size * 1.3))
            f_label = ImageFont.truetype(path_b, font_size)
            f_valoare = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except:
        f_titlu = f_label = f_valoare = ImageFont.load_default()

    # Titlu Model
    txt_m = f"{row['Brand']} {row['Model']}"
    w_m = draw.textlength(txt_m, font=f_titlu)
    draw.text(((W - w_m) // 2, margine * 3), txt_m, fill=(0, 51, 102), font=f_titlu)

    # Specificații
    y_pos = margine * 7.5
    specs = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Selfie", "Sanatate baterie", "Capacitate baterie"]
    for col in specs:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            draw.text((margine * 2, y_pos), f"{col}:", fill="black", font=f_label)
            offset = draw.textlength(f"{col}: ", font=f_label)
            draw.text((margine * 2 + offset, y_pos), val, fill="black", font=f_valoare)
            y_pos += line_spacing

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

# --- INTERFATA ---
try:
    df = pd.read_excel("https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx")
except:
    st.error("Eroare baza de date.")
    st.stop()

st.sidebar.header("🔍 VIZUALIZARE")
zoom = st.sidebar.slider("Lățime Previzualizare", 200, 1000, 400)

col1, col2, col3 = st.columns(3)
cols = [col1, col2, col3]
final_imgs = []

for i in range(3):
    with cols[i]:
        b = st.
