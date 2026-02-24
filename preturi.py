import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Mega Font System", layout="wide")

# CSS pentru panou de reglaje GIGANT și aspect profesional
st.markdown("""
    <style>
    [data-testid="column"] { padding: 5px !important; }
    .stSlider label, .stSelectbox label, .stTextInput label {
        font-size: 18px !important;
        font-weight: 800 !important;
        color: #000000 !important;
    }
    div.stButton > button { 
        height: 4em; 
        font-weight: bold; 
        background-color: #cc0915; 
        color: white; 
        border-radius: 10px; 
        border: none;
    }
    .stExpander { border: 2px solid #cc0915 !important; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- LISTĂ FONTURI ---
FONT_NAMES = ["Open Sans", "Roboto", "Montserrat", "Lato", "Oswald", "Bebas Neue", "Anton", "Poppins"]

@st.cache_data(show_spinner=False)
def get_font_bytes(font_name, weight):
    clean_name = font_name.lower().replace(" ", "")
    # Link-uri directe către Google Fonts GitHub
    url = f"https://github.com/google/fonts/raw/main/ofl/{clean_name}/{font_name.replace(' ', '')}-{weight}.ttf"
    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200: return r.content
    except: pass
    return None

def creeaza_imagine_eticheta(row, font_size, line_spacing, l_scale, l_y, font_name, pret_val, pret_y, pret_size, b_val, ag_val, bag_size):
    W, H = 800, 1200
    img = Image.new('RGB', (W, H), color=(204, 9, 21)) # Fundal roșu
    draw = ImageDraw.Draw(img)
    margine = 40
    # Dreptunghiul alb interior
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=60, fill="white")

    # Încărcare fonturi
    f_raw_reg = get_font_bytes(font_name, "Regular")
    f_raw_bold = get_font_bytes(font_name, "Bold") or f_raw_reg

    try:
        if f_raw_bold:
            f_titlu = ImageFont.truetype(io.BytesIO(f_raw_bold), 45)
            f_label = ImageFont.truetype(io.BytesIO(f_raw_bold), int(font_size))
            f_valoare = ImageFont.truetype(io.BytesIO(f_raw_reg), int(font_size))
            f_pret = ImageFont.truetype(io.BytesIO(f_raw_bold), int(pret_size))
            f_bag = ImageFont.truetype(io.BytesIO(f_raw_bold), int(bag_size))
        else:
            f_titlu = f_label = f_valoare = f_pret = f_bag = ImageFont.load_default()
    except:
        f_titlu = f_label = f_valoare = f_pret = f_bag = ImageFont.load_default()

    # 1. Titlu Model
    txt_m = f"{row['Brand']} {row['Model']}"
    w_m = draw.textlength(txt_m, font=f_titlu)
    draw.text(((W - w_m) // 2, 110), txt_m, fill=(0, 51, 102), font=f_titlu)

    # 2. Specificații
    y_pos = 260
    specs = ["Display", "OS", "Procesor", "Stocare", "RAM", "Camera principala", "Sanatate baterie"]
    for col in specs:
        if col in row.index and pd.notna(row[col]):
            label_txt = f"{col}: "
            val_txt = str(row[col])
            draw.text((80, y_pos), label_txt, fill="black", font=f_label)
            offset = draw.textlength(label_txt, font=f_label)
            draw.text((80 + offset, y_pos), val_txt, fill="black", font=f_valoare)
            y_pos += line_spacing

    # 3. TEXT PREȚ (Mărire până la 500)
    if pret_val:
        txt_p = f"Pret: {pret_val} lei"
        w_p = draw.textlength(txt_p, font=f_pret)
        draw.text(((W - w_p) // 2, pret_y), txt_p, fill=(204, 9, 21), font=f_pret)

    # 4. RUBRICA NOUĂ Btext@Ag (Sub preț)
    txt_bag = f"B{b_val}@Ag{ag_val}"
    w_bag = draw.textlength(txt_bag, font=f_bag)
    # Poziționare automată sub preț
    draw.text(((W - w_bag) // 2, pret_y + pret_size + 10), txt_bag, fill="black", font=f_bag)

    # 5. Logo
    try:
        url_l = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo = Image.open(io.BytesIO(requests.get(url_l).content)).convert("RGBA")
        lw = int(W * l_scale)
        lh = int(lw * (logo.size[1] / logo.size[0]))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(logo, ((W - lw) // 2, l_y), logo)
    except: pass
    
    return img

# --- LOGICĂ APLICAȚIE ---
@st.cache_data
def load_excel():
    url = "https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx"
    return pd.read_excel(url)

try:
    df = load_excel()
except:
    st.error("⚠️ Nu s-a putut încărca baza de date.")
    st.stop()

ag_options = [str(i) for i in range(1, 56)]
col_main = st.columns(3)
final_imgs = []

for i in range(3):
    with col_main[i]:
        # Selectoare de bază
        brand = st.selectbox(f"Brand Telefon {i+1}", sorted(df['Brand'].dropna().unique()), key=f"br_{i}")
        model = st.selectbox(f"Model Telefon {i+1}", df[df['Brand'] == brand]['Model'].dropna().unique(), key=f"md_{i}")
        r_data = df[(df['Brand'] == brand) & (df['Model'] == model)].iloc[0]
        
        # Preț și rubrica B@Ag
        p_input = st.text_input(f"Preț (lei) {i+1}", value="1500", key=f"pri_{i}")
        
        c1, c2 = st.columns(2)
        with c1:
            b_input = st.text_input(f"Text B {i+1}", value="32511", key=f"bi_{i}")
        with c2:
            ag_input = st.selectbox(f"Cifră Ag {i+1}", ag_options, index=27, key=f"ai_{i}")

        # Panou de control
        with st.expander("⚙️ CONFIGURARE DESIGN", expanded=True):
            f_choice = st.selectbox("FONT", FONT_NAMES, index=0, key=f"fn_{i}")
            
            st.markdown("**--- REGLAJE PREȚ ---**")
            p_size = st.slider("MĂRIME PREȚ (Max 500)", 20, 500, 80, key=f"ps_{i}")
            p_y_pos = st.slider("Poziție Y Preț", 300, 900, 780, key=f"py_{i}")
            
            st.markdown("**--- REGLAJE B@Ag ---**")
            bag_size = st.slider("MĂRIME B@Ag", 10, 150, 35, key=f"bs_{i}")
            
            st.markdown("**--- ALTE REGLAJE ---**")
            f_size = st.slider("Mărime Specificații", 10, 80, 26, key=f"fs_{i}")
            l_sp = st.slider("Spațiu între rânduri", 10, 80, 40, key=f"ls_{i}")
            l_sc = st.slider("Scară Logo", 0.1, 1.5, 0.7, key=f"lsc_{i}")
            l_y = st.slider("Poziție Logo Y", 900, 1150, 1050, key=f"ly_{i}")

        # Generare imagine în timp real
        img_res = creeaza_imagine_eticheta(
            r_data, f_size, l_sp, l_sc, l_y, f_choice, 
            p_input, p_y_pos, p_size, b_input, ag_input, bag_size
        )
        st.image(img_res, use_container_width=True)
        final_imgs.append(img_res)

# --- BUTON GENERARE PDF ---
st.divider()
if st.button("🚀 GENEREAZĂ PDF FINAL"):
    canvas = Image.new('RGB', (2400, 1200))
    for idx, image in enumerate(final_imgs):
        canvas.paste(image, (idx * 800, 0))
    
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    
    # Salvare temporară pentru PDF
    img_byte_arr = io.BytesIO()
    canvas.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    with open("temp_print.png", "wb") as f:
        f.write(img_byte_arr.read())
        
    pdf.image("temp_print.png", x=5, y=5, w=287)
    
    pdf_out = pdf.output(dest='S').encode('latin-1')
    st.download_button("💾 DESCARCĂ PDF", pdf_out, "Etichete_ExpressCredit.pdf", "application/pdf")
