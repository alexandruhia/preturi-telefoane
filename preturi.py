import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# ==========================================
# CONFIGURARE UI COMPACTĂ
# ==========================================
st.set_page_config(page_title="ExpressCredit - Ultra Compact", layout="wide")

COLOR_BG_SITE = "#96c83f"
COLOR_ACCENT = "#cf1f2f"
COLOR_CARD = "#ffffff"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_BG_SITE}; }}
    div[data-testid="stExpander"] {{
        background-color: {COLOR_CARD};
        border-radius: 8px;
    }}
    .stButton>button {{
        width: 100%;
        border-radius: 15px;
        background-color: {COLOR_ACCENT} !important;
        color: white !important;
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# LOGICĂ DE RENDERIZARE (ULTRA COMPACT)
# ==========================================

def get_google_font(font_name, weight="Bold"):
    base_url = "https://github.com/google/fonts/raw/main/"
    paths = ["ofl/", "apache/", "googlefonts/"]
    font_clean = font_name.replace(" ", "")
    for p in paths:
        url = f"{base_url}{p}{font_name.lower().replace(' ', '')}/{font_clean}-{weight}.ttf"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200: return io.BytesIO(res.content)
        except: continue
    return None

def create_label(data, settings):
    # Pânză micșorată cu 150%: 261 x 400 pixeli
    W, H = 261, 400
    img = Image.new('RGB', (W, H), color=COLOR_ACCENT)
    draw = ImageDraw.Draw(img)
    
    pad = 10
    draw.rounded_rectangle([pad, pad, W-pad, H-65], radius=15, fill="white")
    
    # Scalare adaptată pentru rezoluție mică
    scale = 1.0 
    
    try:
        font_bytes_b = get_google_font(settings['font_family'], "Bold")
        font_bytes_r = get_google_font(settings['font_family'], "Regular") or font_bytes_b
        
        f_title = ImageFont.truetype(font_bytes_b, int(settings['t_size'] * scale))
        f_specs = ImageFont.truetype(font_bytes_b, int(settings['f_size'] * scale))
        f_vals = ImageFont.truetype(font_bytes_r, int(settings['f_size'] * scale))
        f_price_lbl = ImageFont.truetype(font_bytes_b, 16)
        f_price_val = ImageFont.truetype(font_bytes_b, 38)
        f_small = ImageFont.truetype(font_bytes_b, 10)
    except:
        f_title = f_specs = f_vals = f_price_lbl = f_price_val = f_small = ImageFont.load_default()

    current_y = pad * 2.5
    
    # Titlu
    brand_model = f"{data['Brand']} {data['Model']}"
    w_t = draw.textlength(brand_model, font=f_title)
    draw.text(((W - w_t) // 2, current_y), brand_model, fill="black", font=f_title)
    current_y += (settings['t_size'] * scale) + settings['spacing']

    # Specificații (Versiune simplificată pentru spațiu mic)
    specs = [
        ("Stoc", settings['stocare']),
        ("RAM", settings['ram']),
        ("Bat", f"{settings['bat']}%")
    ]

    for label, val in specs:
        txt = f"{label}: {val}"
        w_txt = draw.textlength(txt, font=f_specs)
        draw.text(((W - w_txt) // 2, current_y), txt, fill="black", font=f_specs)
        current_y += (settings['f_size'] * scale) + settings['spacing']

    # Preț
    y_price_section = H - 145
    if settings['pret']:
        p_suma = f"{settings['pret']} lei"
        w_s = draw.textlength(p_suma, font=f_price_val)
        draw.text(((W - w_s) // 2, y_price_section), p_suma, fill="black", font=f_price_val)
        
        cod_text = f"B{settings['cod_b']}@Ag{settings['cod_ag']}"
        w_c = draw.textlength(cod_text, font=f_small)
        draw.text(((W - w_c) // 2, y_price_section + 45), cod_text, fill="#333333", font=f_small)

    # Logo
    try:
        logo_url = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo_img = Image.open(io.BytesIO(requests.get(logo_url).content)).convert("RGBA")
        l_w = int(W * 0.5)
        l_h = int(l_w * (logo_img.size[1] / logo_img.size[0]))
        logo_img = logo_img.resize((l_w, l_h), Image.Resampling.LANCZOS)
        img.paste(logo_img, ((W - l_w) // 2, H - 55), logo_img)
    except: pass

    return img

# ==========================================
# INTERFAȚĂ
# ==========================================
def main():
    st.title("🏷️ Etichete Ultra Compact")
    URL_DB = "https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx"
    df = pd.read_excel(URL_DB)

    st.sidebar.header("🎨 Design")
    global_font = st.sidebar.selectbox("Font", ["Montserrat", "Poppins", "Roboto"])
    zoom = st.sidebar.slider("Previzualizare", 100, 500, 300)

    cols = st.columns(3)
    generated_images = []

    for i in range(3):
        with cols[i]:
            brand = st.selectbox(f"Brand", sorted(df['Brand'].unique()), key=f"b{i}")
            model = st.selectbox(f"Model", df[df['Brand'] == brand]['Model'].unique(), key=f"m{i}")
            row_data = df[(df['Brand'] == brand) & (df['Model'] == model)].iloc[0]
            pret = st.text_input("Preț", key=f"p{i}")
            
            with st.expander("🛠️ Setări"):
                t_size = st.number_input("Titlu", 8, 40, 14, key=f"ts{i}")
                f_size = st.number_input("Text", 5, 30, 10, key=f"fs{i}")
                spacing = st.slider("Spațiu", 0, 30, 8, key=f"sp{i}")
                stoc = st.selectbox("Stoc", ["128GB", "256GB", "512GB"], key=f"st{i}")
                ram = st.selectbox("RAM", ["6GB", "8GB", "12GB"], key=f"ra{i}")
                bat = st.slider("Bat%", 70, 100, 90, key=f"bt{i}")
                c_ag = st.number_input("Ag", 1, 55, 1, key=f"ca{i}")

            settings = {'t_size': t_size, 'f_size': f_size, 'spacing': spacing, 'font_family': global_font, 'pret': pret, 'stocare': stoc, 'ram': ram, 'bat': bat, 'cod_b': "001", 'cod_ag': c_ag}
            img = create_label(row_data, settings)
            st.image(img, width=zoom)
            generated_images.append(img)

    if st.button("🚀 GENERARE PDF"):
        pdf = FPDF()
        pdf.add_page()
        for idx, pic in enumerate(generated_images):
            buf = io.BytesIO()
            pic.save(buf, format="PNG")
            temp_name = f"temp_{idx}.png"
            with open(temp_name, "wb") as f: f.write(buf.getvalue())
            pdf.image(temp_name, x=10 + (idx * 40), y=20, w=35)
        st.download_button("💾 DESCARCĂ", pdf.output(dest='S').encode('latin-1'), "Etichete_Compact.pdf")

if __name__ == "__main__":
    main()
