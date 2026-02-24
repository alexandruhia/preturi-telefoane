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
        font-size: 18px !important;
        font-weight: 800 !important;
        color: #000000 !important;
    }
    div.stButton > button { height: 4em; font-weight: bold; background-color: #cc0915; color: white; border-radius: 10px; }
    .stExpander { border: 2px solid #cc0915 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- LISTĂ FONTURI ---
FONT_NAMES = ["Roboto", "Open Sans", "Montserrat", "Lato", "Oswald", "Bebas Neue", "Anton", "Poppins"]

@st.cache_data(show_spinner=False)
def get_font_bytes(font_name, weight):
    clean_name = font_name.lower().replace(" ", "")
    # Încercăm structura standard Google Fonts
    url = f"https://github.com/google/fonts/raw/main/ofl/{clean_name}/{font_name.replace(' ', '')}-{weight}.ttf"
    try:
        r = requests.get(url, timeout=2)
        if r.status_code == 200: return r.content
    except: pass
    return None

def creeaza_imagine_eticheta(row, font_size, line_spacing, l_scale, l_y, font_name, font_style, pret_val, pret_y, pret_size, b_val, ag_val, bag_size):
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
            f_bag = ImageFont.truetype(io.BytesIO(f_bold_bytes), bag_size)
        else:
            f_titlu = f_label = f_valoare = f_pret = f_bag = ImageFont.load_default()
    except:
        f_titlu = f_label = f_valoare = f_pret = f_bag = ImageFont.load_default()

    # Model
    txt_m = f"{row['Brand']} {row['Model']}"
    draw.text(((W - draw.textlength(txt_m, font=f_titlu)) // 2, margine * 3), txt_m, fill=(0, 51, 102), font=f_titlu)

    # Specificații
    y_pos = margine * 7.5
    specs = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Sanatate baterie"]
    for col in specs:
        if col in row.index and pd.notna(row[col]):
            draw.text((margine * 2, y_pos), f"{col}:", fill="black", font=f_label)
            offset = draw.textlength(f"{col}: ", font=f_label)
            draw.text((margine * 2 + offset, y_pos), str(row[col]), fill="black", font=f_valoare)
            y_pos += line_spacing

    # --- TEXT PREȚ ---
    if pret_val:
        txt_p = f"Pret: {pret_val} lei"
        w_p = draw.textlength(txt_p, font=f_pret)
        draw.text(((W - w_p) // 2, pret_y), txt_p, fill=(204, 9, 21), font=f_pret)

    # --- RUBRICA B@Ag ---
    txt_bag = f"B{b_val}@{ag_val}"
    w_bag = draw.textlength(txt_bag, font=f_bag)
    # Poziționată sub preț (la distanță de mărimea fontului prețului)
    draw.text(((W - w_bag) // 2, pret_y + pret_size + 10), txt_bag, fill="black", font=f_bag)

    # Logo
    try:
        url_l = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo = Image.open(io.BytesIO(requests.get(url_l).content)).convert("RGBA")
        lw = int(W * l_scale)
        lh = int(lw * (logo.size[1] / logo.size[0]))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(logo, ((W - lw) // 2, l_y), logo)
    except: pass
    return img

# --- LOGICĂ ---
df = pd.read_excel("https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx")
ag_list = [str(i) for i in range(1, 56)]

col_main = st.columns(3)
final_imgs = []

for i in range(3):
    with col_main[i]:
        brand = st.selectbox(f"Brand {i+1}", sorted(df['Brand'].dropna().unique()), key=f"b_{i}")
        model = st.selectbox(f"Model {i+1}", df[df['Brand'] == brand]['Model'].dropna().unique(), key=f"m_{i}")
        r_data = df[(df['Brand'] == brand) & (df['Model'] == model)].iloc[0]
        
        pr_in = st.text_input(f"Pret {i+1}", value="1500", key=f"pr_{i}")
        
        # --- RUBRICA B@Ag ---
        c1, c2 = st.columns(2)
        with c1: b_in = st.text_input(f"Text B {i+1}", "32511", key=f"bin_{i}")
        with c2: ag_in = st.selectbox(f"Ag {i+1}", ag_list, index=27, key=f"agin_{i}")

        with st.expander("⚙️ REGLAJE DIMENSIUNI", expanded=True):
            fn = st.selectbox("FONT", FONT_NAMES, index=1, key=f"fn_{i}")
            # Mărire PREȚ până la 500
            p_sz = st.slider("MĂRIME PREȚ", 20, 500, 80, key=f"psz_{i}")
            p_y = st.slider("POZIȚIE Y PREȚ", 300, 900, 780, key=f"py_{i}")
            
            # Mărire rubrica B@Ag
            bag_sz = st.slider("MĂRIME B@Ag", 10, 150, 35, key=f"bagsz_{i}")
            
            st.divider()
            f_sz = st.slider("Mărime Specificații", 10, 80, 28, key=f"fsz_{i}")
            sp = st.slider("Spațiere Rânduri", 10, 80, 38, key=f"sp_{i}")
            ls = st.slider("Scară Logo", 0.1, 1.5, 0.7, key=f"ls_{i}")
            ly = st.slider("Poziție Logo Y", 900, 1150, 1050, key=f"ly_{i}")

        img = creeaza_imagine_eticheta(r_data, f_sz, sp, ls,
