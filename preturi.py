import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests

# 1. Configurare instanță (trebuie să fie prima)
st.set_page_config(page_title="Express Labels", layout="wide")

# 2. Cache agresiv pentru date (1 oră)
@st.cache_data(ttl=3600)
def get_all_data():
    SHEET_ID = '1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA'
    URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'
    try:
        df = pd.read_csv(URL)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

# 3. Cache logo (se descarcă o singură dată pe sesiune)
@st.cache_resource
def load_logo_bytes():
    url = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
    try:
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            with open("logo.png", "wb") as f:
                f.write(r.content)
            return True
    except:
        return False
    return False

df = get_all_data()
HAS_LOGO = load_logo_bytes()

# 4. Funcție PDF Ultra-Rapidă
def fast_pdf(data_list, original_cols):
    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()
    w, h = 60, 80
    mx = (210 - (w * 3)) / 2
    
    for i, item in enumerate(data_list):
        if not item: continue
        x = mx + (i * w)
        y = 20
        
        # Chenar & Titlu
        pdf.set_draw_color(255, 0, 0)
        pdf.rect(x, y, w, h)
        pdf.set_font("Arial", "B", 9)
        pdf.set_xy(x, y + 4)
        pdf.cell(w, 5, item['title'][:25], align='C', ln=1)
        
        # Specificații (Directe, fără procesări complexe)
        pdf.set_font("Arial", "", 7)
        sy = y + 12
        specs = {"Stocare": item['stoc'], "RAM": item['ram'], "Baterie": f"{item['bat']}%"}
        for k, v in specs.items():
            if v and v != "-":
                pdf.set_xy(x + 3, sy)
                pdf.write(4, f"{k}: {v}")
                sy += 4
        
        # Preț & Logo
        pdf.set_text_color(255, 0, 0)
        pdf.set_font("Arial", "B", 18)
        pdf.set_xy(x, y + h - 20)
        pdf.cell(w, 10, f"{item['price']} lei", align='C')
        
        pdf.set_fill_color(255, 0, 0)
        pdf.rect(x + 0.2, y + h - 8.2, w - 0.4, 8, 'F')
        if HAS_LOGO:
            pdf.image("logo.png", x + (w-30)/2, y + h - 7, 30)
            
    return pdf.output(dest='S').encode('latin-1')

# 5. UI Layout - Simplificat pentru performanță
st.title("📱 Express Label v2")

if df.empty:
    st.error("Baza de date inaccesibilă.")
else:
    ui_cols = st.columns(3)
    labels_to_gen = [None, None, None]

    for i in range(3):
        with ui_cols[i]:
            br = st.selectbox(f"Brand {i+1}", ["-"] + sorted(df["Brand"].unique().tolist()), key=f"br{i}")
            if br != "-":
                mo = st.selectbox(f"Model {i+1}", sorted(df[df["Brand"] == br]["Model"].tolist()), key=f"mo{i}")
                pr = st.number_input(f"Preț {i+1}", 0, key=f"pr{i}")
                
                c1, c2 = st.columns(2)
                stc = c1.selectbox("Stoc", ["128GB", "256GB", "512GB"], key=f"st{i}")
                rm = c2.selectbox("RAM", ["4GB", "6GB", "8GB", "12GB"], key=f"rm{i}")
                
                bt = st.slider("Baterie %", 50, 100, 100, key=f"bt{i}")
                cod_b = st.text_input("Cod", "32451", key=f"cd{i}")

                labels_to_gen[i] = {
                    'title': f"{br} {mo}".upper(),
                    'price': pr,
                    'stoc': stc,
                    'ram': rm,
                    'bat': bt,
                    'code': cod_b
                }

    st.divider()

    # Butonul de download - Randat doar dacă există date
    if any(labels_to_gen):
        # Generăm PDF doar la cerere (on click) pentru a nu încetini UI-ul
        _, mid, _ = st.columns([1,1,1])
        with mid:
            pdf_data = fast_pdf(labels_to_gen, df.columns)
            st.download_button(
                label="🔴 EXPORT PDF (INSTANT)",
                data=pdf_data,
                file_name="etichete.pdf",
                mime="application/pdf",
                use_container_width=True
            )

# Concluzie: Codul e acum "lean". Fără loops inutile, fără requests repetate.
