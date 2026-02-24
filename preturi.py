import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Mega Font System", layout="wide")

# CSS pentru panou de reglaje GIGANT
st.markdown("""
    <style>
    [data-testid="column"] { padding: 5px !important; }
    .stSlider label, .stSelectbox label, .stNumberInput label, .stTextInput label {
        font-size: 20px !important;
        font-weight: 800 !important;
        color: #000000 !important;
    }
    div.stButton > button { height: 4em; font-weight: bold; background-color: #cc0915; color: white; border-radius: 10px; }
    .stExpander { border: 2px solid #cc0915 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- LISTĂ 100 FONTURI GOOGLE ---
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
    folders = ['ofl', 'apache', 'googlefonts']
    clean_name = font_name.lower().replace(" ", "")
    for folder in folders:
        url = f"https://github.com/google/fonts/raw/main/{folder}/{clean_name}/{font_name.replace(' ', '')}-{weight}.ttf"
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200: return r.content
        except: continue
    return None

def creeaza_imagine_eticheta(row, font_size, line_spacing, l_scale, l_x_manual, l_y, font_name, font_style, pret_val, pret_y, pret_size, b_text, ag_val):
    W, H = 800, 1200
    img = Image.new('RGB', (W, H), color=(204, 9, 21))
    draw = ImageDraw.Draw(img)
    margine = 40
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=60, fill="white")

    f_bytes = get_font_bytes(font_name, font_style)
    f_bold_bytes = get_font_bytes(font_name, "Bold") or f_bytes
    
    try:
        if f_bytes:
            f_titlu = ImageFont.truetype(io.BytesIO(f_bold_bytes), int(font_size * 1.3))
            f_label = ImageFont.truetype(io.BytesIO(f_bold_bytes), font_size)
            f_valoare = ImageFont.truetype(io.BytesIO(f_bytes), font_size)
            f_pret = ImageFont.truetype(io.BytesIO(f_bold_bytes), pret_size)
            f_bag = ImageFont.truetype(io.BytesIO(f_bold_bytes), 50) # Font fixat la 50
        else:
            path_b = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            f_titlu = ImageFont.truetype(path_b, int(font_size * 1.3))
            f_label = ImageFont.truetype(path_b, font_size)
            f_valoare = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            f_pret = ImageFont.truetype(path_b, pret_size)
            f_bag = ImageFont.truetype(path_b, 50)
    except:
        f_titlu = f_label = f_valoare = f_pret = f_bag = ImageFont.load_default()

    # Model
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

    # --- TEXT PREȚ ---
    if pret_val:
        txt_p = f"Pret: {pret_val} lei"
        w_p = draw.textlength(txt_p, font=f_pret)
        draw.text(((W - w_p) // 2, pret_y), txt_p, fill=(204, 9, 21), font=f_pret)
        
        # --- RUBRICA B@Ag (Sub preț, în dreapta) ---
        txt_bag = f"B{b_text}@Ag{ag_val}"
        w_bag = draw.textlength(txt_bag, font=f_bag)
        draw.text((W - margine * 2 - w_bag, pret_y + pret_size + 10), txt_bag, fill="black", font=f_bag)

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

# --- LOGICĂ APLICAȚIE ---
@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx"
    return pd.read_excel(url)

df = load_data()

st.sidebar.header("🔍 CONTROL VIZUAL")
zoom = st.sidebar.slider("Lățime Previzualizare", 200, 1000, 400)

col1, col2, col3 = st.columns(3)
cols = [col1, col2, col3]
final_imgs = []

# Opțiuni pentru dropdown Ag
ag_list = [str(i) for i in range(1, 56)]

for i in range(3):
    with cols[i]:
        brand = st.selectbox(f"Brand Telefon {i+1}", sorted(df['Brand'].dropna().unique()), key=f"b_{i}")
        model = st.selectbox(f"Model Telefon {i+1}", df[df['Brand'] == brand]['Model'].dropna().unique(), key=f"m_{i}")
        r_data = df[(df['Brand'] == brand) & (df['Model'] == model)].iloc[0]
        
        # Secțiune Preț dedicată
        pret_input = st.text_input(f"Pret Telefon {i+1}", value="", key=f"pr_{i}", placeholder="Ex: 1500")
        
        # Secțiune B@Ag adăugată sub preț conform cerinței
        sub_c1, sub_c2 = st.columns(2)
        with sub_c1:
            b_input = st.text_input(f"Text B {i+1}", value="", key=f"bt_{i}", placeholder="cod")
        with sub_c2:
            ag_input = st.selectbox(f"Ag {i+1}", ag_list, index=0, key=f"ag_{i}")

        with st.expander("⚙️ CONFIGURARE AVANSATĂ", expanded=False):
            fn = st.selectbox("ALEGE FONT", FONT_NAMES, key=f"fn_{i}")
            fs = st.selectbox("STIL TEXT", ["Regular", "Bold", "Italic"], key=f"fst_{i}")
            size = st.slider("MĂRIME FONT SPEC.", 10, 100, 30, key=f"sz_{i}")
            sp = st.slider("SPAȚIERE RÂNDURI", 10, 100, 38, key=f"sp_{i}")
            
            st.markdown("---")
            p_size = st.slider("MĂRIME TEXT PREȚ", 20, 150, 60, key=f"psz_{i}")
            p_y = st.slider("POZIȚIE Y PREȚ", 500, 1100, 850, key=f"py_{i}")
            
            st.markdown("---")
            ls = st.slider("SCARĂ LOGO", 0.1, 2.0, 0.7, key=f"ls_{i}")
            lx = st.number_input("X Logo (100=Centrat)", 0, 800, 100, key=f"lx_{i}")
            ly = st.number_input("Y Logo", 0, 1200, 1050, key=f"ly_{i}")

        current_img = creeaza_imagine_eticheta(r_data, size, sp, ls, lx, ly, fn, fs, pret_input, p_y, p_size, b_input, ag_input)
        st.image(current_img, width=zoom)
        final_imgs.append(current_img)

# --- GENERARE PDF ---
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
    st.download_button("💾 DESCARCĂ PDF", pdf.output(dest='S').encode('latin-1'), "Etichete.pdf", "application/pdf")
