import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# ==========================================
# CONFIGURARE UI MODERNĂ
# ==========================================
st.set_page_config(page_title="ExpressCredit Pro HD", layout="wide")

COLOR_BG_SITE = "#96c83f"  # Verde Lime
COLOR_ACCENT = "#cf1f2f"   # Roșu Express
COLOR_CARD = "#ffffff"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_BG_SITE}; }}
    div[data-testid="stExpander"] {{
        background-color: {COLOR_CARD};
        border-radius: 10px;
        border: 1px solid #ddd;
    }}
    .stButton>button {{
        width: 100%;
        border-radius: 20px;
        background-color: {COLOR_ACCENT} !important;
        color: white !important;
        font-weight: bold;
        height: 3em;
    }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# LOGICĂ DE RENDERIZARE (PROPORȚIONALĂ)
# ==========================================

def get_google_font(font_name, weight="Bold"):
    """Descarcă fontul direct de pe GitHub Google Fonts."""
    base_url = "https://github.com/google/fonts/raw/main/"
    paths = ["ofl/", "apache/", "googlefonts/"]
    font_clean = font_name.replace(" ", "")
    
    for p in paths:
        url = f"{base_url}{p}{font_name.lower().replace(' ', '')}/{font_clean}-{weight}.ttf"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                return io.BytesIO(res.content)
        except:
            continue
    return None

def create_label(data, settings):
    # Dimensiune Pânză (HD 200% din original)
    W, H = 768, 1176
    img = Image.new('RGB', (W, H), color=COLOR_ACCENT)
    draw = ImageDraw.Draw(img)
    
    # Margini și Fundal
    pad = 30
    draw.rounded_rectangle([pad, pad, W-pad, H-180], radius=45, fill="white")
    
    # LOGICĂ SCALARE: Un font de 14pt pe această pânză necesită un multiplicator de ~3.2
    scale = 3.2 
    
    # Încărcare Fonturi cu Securitate
    try:
        font_bytes_b = get_google_font(settings['font_family'], "Bold")
        font_bytes_r = get_google_font(settings['font_family'], "Regular") or font_bytes_b
        
        f_title = ImageFont.truetype(font_bytes_b, int(settings['t_size'] * scale))
        f_specs = ImageFont.truetype(font_bytes_b, int(settings['f_size'] * scale))
        f_vals = ImageFont.truetype(font_bytes_r, int(settings['f_size'] * scale))
        f_price_lbl = ImageFont.truetype(font_bytes_b, 50)
        f_price_val = ImageFont.truetype(font_bytes_b, 120)
        f_small = ImageFont.truetype(font_bytes_b, 30)
    except:
        f_title = f_specs = f_vals = f_price_lbl = f_price_val = f_small = ImageFont.load_default()

    # --- DESENARE TEXT (AUTO-LAYOUT) ---
    current_y = pad * 2.5
    
    # Titlu centrat
    brand_model = f"{data['Brand']} {data['Model']}"
    w_t = draw.textlength(brand_model, font=f_title)
    draw.text(((W - w_t) // 2, current_y), brand_model, fill="black", font=f_title)
    current_y += (settings['t_size'] * scale) + settings['spacing']

    # Specificații
    specs = [
        ("Display", data.get('Display', '-')),
        ("Procesor", data.get('Chipset', '-')),
        ("Stocare", settings['stocare']),
        ("RAM", settings['ram']),
        ("Baterie", data.get('Capacitate baterie', '-')),
        ("Sănătate", f"{settings['bat']}%")
    ]

    for label, val in specs:
        draw.text((pad * 3, current_y), f"{label}:", fill="#555555", font=f_specs)
        offset = draw.textlength(f"{label}: ", font=f_specs)
        draw.text((pad * 3 + offset, current_y), str(val), fill="black", font=f_vals)
        current_y += (settings['f_size'] * scale) + settings['spacing']

    # --- ZONA PREȚ ---
    y_price_section = H - 430
    if settings['pret']:
        p_label, p_suma, p_moneda = "Preț: ", str(settings['pret']), " lei"
        w_l, w_s, w_m = draw.textlength(p_label, font=f_price_lbl), draw.textlength(p_suma, font=f_price_val), draw.textlength(p_moneda, font=f_price_lbl)
        
        start_x = (W - (w_l + w_s + w_m)) // 2
        draw.text((start_x, y_price_section + 40), p_label, fill="black", font=f_price_lbl)
        draw.text((start_x + w_l, y_price_section), p_suma, fill="black", font=f_price_val)
        draw.text((start_x + w_l + w_s, y_price_section + 40), p_moneda, fill="black", font=f_price_lbl)
        
        cod_text = f"B{settings['cod_b']} @ Ag{settings['cod_ag']}"
        w_c = draw.textlength(cod_text, font=f_small)
        draw.text(((W - w_c) // 2, y_price_section + 150), cod_text, fill="#333333", font=f_small)

    # --- LOGO ---
    try:
        logo_url = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo_res = requests.get(logo_url, timeout=5)
        logo_img = Image.open(io.BytesIO(logo_res.content)).convert("RGBA")
        l_w = int(W * 0.5)
        l_h = int(l_w * (logo_img.size[1] / logo_img.size[0]))
        logo_img = logo_img.resize((l_w, l_h), Image.Resampling.LANCZOS)
        img.paste(logo_img, ((W - l_w) // 2, H - 145), logo_img)
    except: pass

    return img

# ==========================================
# INTERFAȚĂ UTILIZATOR
# ==========================================
def main():
    st.title("🏷️ Generator Etichete HD Pro")
    
    URL_DB = "https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/export?format=xlsx"
    try:
        df = pd.read_excel(URL_DB)
    except:
        st.error("Eroare la încărcarea bazei de date Excel.")
        return

    st.sidebar.header("🎨 Setări Vizuale")
    global_font = st.sidebar.selectbox("Alege Fontul", ["Montserrat", "Poppins", "Roboto", "Open Sans"])
    zoom = st.sidebar.slider("Previzualizare Zoom", 200, 800, 450)

    cols = st.columns(3)
    generated_images = []

    for i in range(3):
        with cols[i]:
            st.subheader(f"Eticheta {i+1}")
            brand = st.selectbox(f"Brand", sorted(df['Brand'].unique()), key=f"b{i}")
            model = st.selectbox(f"Model", df[df['Brand'] == brand]['Model'].unique(), key=f"m{i}")
            row_data = df[(df['Brand'] == brand) & (df['Model'] == model)].iloc[0]
            
            pret = st.text_input("Preț (Lei)", key=f"p{i}")
            
            with st.expander("🛠️ Personalizare HD"):
                t_size = st.number_input("Mărime Titlu", 10, 100, 22, key=f"ts{i}")
                f_size = st.number_input("Mărime Text (14 = real)", 5, 80, 14, key=f"fs{i}")
                spacing = st.slider("Spațiere (padding)", 0, 100, 20, key=f"sp{i}")
                
                stoc = st.selectbox("Stocare", ["64 GB", "128 GB", "256 GB", "512 GB", "1 TB"], index=1, key=f"st{i}")
                ram = st.selectbox("RAM", ["4 GB", "6 GB", "8 GB", "12 GB", "16 GB"], index=1, key=f"ra{i}")
                bat = st.slider("Baterie %", 70, 100, 95, key=f"bt{i}")
                c_b = st.text_input("Cod B", "001", key=f"cb{i}")
                c_ag = st.number_input("Cod Ag", 1, 55, 1, key=f"ca{i}")

            settings = {
                't_size': t_size, 'f_size': f_size, 'spacing': spacing,
                'font_family': global_font, 'pret': pret, 'stocare': stoc,
                'ram': ram, 'bat': bat, 'cod_b': c_b, 'cod_ag': c_ag
            }
            
            img = create_label(row_data, settings)
            st.image(img, width=zoom)
            generated_images.append(img)

    st.divider()
    if st.button("🚀 GENEREAZA PDF FINAL"):
        pdf = FPDF()
        pdf.add_page()
        for idx, pic in enumerate(generated_images):
            buf = io.BytesIO()
            pic.save(buf, format="PNG")
            temp_name = f"temp_{idx}.png"
            with open(temp_name, "wb") as f: f.write(buf.getvalue())
            # Plasare 3 etichete pe lățimea paginii A4
            pdf.image(temp_name, x=10 + (idx * 65), y=20, w=60)
        
        pdf_out = pdf.output(dest='S').encode('latin-1')
        st.download_button("💾 DESCARCĂ PDF", pdf_out, "Etichete_HD.pdf", "application/pdf")

if __name__ == "__main__":
    main()
