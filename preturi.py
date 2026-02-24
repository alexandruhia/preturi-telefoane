import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from fpdf import FPDF

# Configurare pagină
st.set_page_config(page_title="ExpressCredit - Multi-Generator Individual", layout="wide")

# --- FUNCȚIE ÎNCĂRCARE DATE ---
@st.cache_data(ttl=60)
def incarca_date():
    sheet_url = "https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/edit?usp=sharing"
    try:
        url_export = sheet_url.split("/edit")[0] + "/export?format=xlsx"
        df = pd.read_excel(url_export)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Eroare la încărcarea datelor: {e}")
        return None

# --- FUNCȚIE GENERARE ETICHETĂ INDIVIDUALĂ ---
def creeaza_imagine_eticheta(row, font_size, line_spacing, l_scale, l_x, l_y):
    W, H = 800, 1200
    rosu_express = (204, 9, 21)
    albastru_text = (0, 51, 102)
    
    img = Image.new('RGB', (W, H), color=rosu_express)
    draw = ImageDraw.Draw(img)
    margine = 40
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=60, fill="white")

    try:
        # Fonturi standard Streamlit Cloud
        f_path_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        f_path_reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        f_titlu = ImageFont.truetype(f_path_bold, int(font_size * 1.2))
        f_bold = ImageFont.truetype(f_path_bold, font_size)
        f_normal = ImageFont.truetype(f_path_reg, font_size)
    except:
        f_titlu = f_bold = f_normal = ImageFont.load_default()

    draw.text((margine*2, margine*2.5), "FISA TEHNICA:", fill=albastru_text, font=f_titlu)
    draw.text((margine*2, margine*2.5 + 65), f"{row['Brand']} {row['Model']}", fill=albastru_text, font=f_titlu)

    y_pos = margine * 6.5
    spec_liste = ["Display", "OS", "Procesor", "Stocare", "RAM", "Capacitate baterie"]
    for col in spec_liste:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            draw.text((margine*2, y_pos), f"{col}:", fill="black", font=f_bold)
            offset = draw.textlength(f"{col}: ", font=f_bold)
            draw.text((margine*2 + offset, y_pos), val, fill="black", font=f_normal)
            y_pos += line_spacing

    try:
        url_logo = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo = Image.open(io.BytesIO(requests.get(url_logo).content)).convert("RGBA")
        lw = int(W * l_scale)
        lh = int(lw * (logo.size[1] / logo.size[0]))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(logo, (l_x, l_y), logo)
    except: pass
    return img

# --- INTERFAȚĂ ---
st.title("📱 ExpressCredit - Control Individual pe Etichetă")
df = incarca_date()

if df is not None:
    # Selecție și reglaje pe 3 coloane
    cols = st.columns(3)
    date_etichete = []
    reglaje_etichete = []

    for i in range(3):
        with cols[i]:
            st.markdown(f"### 🏷️ Eticheta {i+1}")
            
            # 1. Selecție Date
            brand = st.selectbox(f"Brand {i+1}:", sorted(df['Brand'].dropna().unique()), key=f"brand_{i}")
            modele = df[df['Brand'] == brand]['Model'].dropna().unique()
            model = st.selectbox(f"Model {i+1}:", modele, key=f"model_{i}")
            row_data = df[(df['Brand'] == brand) & (df['Model'] == model)].iloc[0]
            
            st.divider()
            st.write("🔧 **Reglaje Eticheta**")
            
            # 2. Slidere Individuale
            f_size = st.slider("Mărime Font", 20, 60, 35, key=f"fs_{i}")
            l_space = st.slider("Distanță Rânduri", 20, 100, 45, key=f"ls_{i}")
            l_sc = st.slider("Mărime Logo", 0.1, 1.0, 0.7, key=f"lsc_{i}")
            l_x = st.slider("Poziție Logo X", 0, 800, 100, key=f"lx_{i}")
            l_y = st.slider("Poziție Logo Y", 0, 1200, 1080, key=f"ly_{i}")
            
            # Salvăm datele și reglajele pentru generare
            date_etichete.append(row_data)
            reglaje_etichete.append({
                'fs': f_size, 'ls': l_space, 'lsc': l_sc, 'lx': l_x, 'ly': l_y
            })

    st.divider()

    # --- GENERARE PREVIEW ---
    imagini_finale = []
    for i in range(3):
        img = creeaza_imagine_eticheta(
            date_etichete[i], 
            reglaje_etichete[i]['fs'], 
            reglaje_etichete[i]['ls'], 
            reglaje_etichete[i]['lsc'], 
            reglaje_etichete[i]['lx'], 
            reglaje_etichete[i]['ly']
        )
        imagini_finale.append(img)

    # Afișare imagini rezultate sub reglaje
    preview_cols = st.columns(3)
    for i in range(3):
        preview_cols[i].image(imagini_finale[i], caption=f"Previzualizare {i+1}", use_container_width=True)

    # --- BUTON DESCARCĂ PDF ---
    st.divider()
    if st.button("🚀 GENEREAZĂ PDF FINAL (TOATE 3)"):
        # Lipim cele 3 imagini
        final_w = 800 * 3
        final_h = 1200
        canvas = Image.new('RGB', (final_w, final_h))
        for i in range(3):
            canvas.paste(imagini_finale[i], (i * 800, 0))

        # Creare PDF
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        
        img_buf = io.BytesIO()
        canvas.save(img_buf, format='PNG')
        img_buf.seek(0)
        
        # Salvăm un fișier temporar pentru FPDF
        with open("print_multi.png", "wb") as f:
            f.write(img_buf.read())
        
        pdf.image("print_multi.png", x=5, y=5, w=287)
        
        pdf_out = pdf.output(dest='S').encode('latin-1')
        st.download_button(
            label="💾 DESCARCĂ PDF PENTRU PRINT",
            data=pdf_out,
            file_name="Set_3_Etichete.pdf",
            mime="application/pdf"
        )
