import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests
import os
from io import BytesIO

# --- CONFIGURARE DATE ---
SHEET_ID = '1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA'
URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'
LOGO_URL = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"

@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(URL)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

df = load_data()

def clean_for_pdf(text):
    if not text: return ""
    replacements = {'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't', 'Ă': 'A', 'Â': 'A', 'Î': 'I', 'Ș': 'S', 'Ț': 'T'}
    t = str(text)
    for k, v in replacements.items():
        t = t.replace(k, v)
    return t.encode('latin-1', 'replace').decode('latin-1')

def get_specs_in_order(row_dict, original_columns, battery_override, accessories, stocare, ram):
    clean = {}
    # Prioritate Memorie
    if stocare and stocare != "-": clean["Stocare"] = stocare
    if ram and ram != "-": clean["RAM"] = ram
    
    skip = ["brand", "model", "stocare", "ram", "sanatate baterie", "sănătate baterie", "baterie"]
    for col in original_columns:
        if col.lower() in skip: continue
        val = row_dict.get(col)
        if pd.notnull(val) and str(val).strip() not in ["", "0", "nan", "NaN"]:
            clean[col] = str(val).strip()
    
    if battery_override: clean["Sanatate baterie"] = f"{battery_override}%"
    if accessories: clean["Accesorii"] = ", ".join(accessories)
    return clean

def create_pdf(selected_data, original_columns):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # Încercăm să luăm logo-ul în memorie
    logo_content = None
    try:
        r = requests.get(LOGO_URL, timeout=5)
        if r.status_code == 200:
            logo_content = BytesIO(r.content)
    except:
        pass

    margin_left, gutter, label_w, label_h = 15, 5, 40, 60

    for i, item in enumerate(selected_data):
        if item is None: continue
        
        current_x = margin_left + (i * (label_w + gutter))
        current_y = 25
        
        # Desenare Etichetă
        pdf.set_draw_color(255, 0, 0)
        pdf.rect(current_x, current_y, label_w, label_h)
        
        # Titlu
        pdf.set_font("Arial", "B", 9)
        pdf.set_xy(current_x, current_y + 2)
        title = f"{item['specs']['Brand']} {item['specs']['Model']}".upper()
        pdf.multi_cell(label_w, 4, clean_for_pdf(title), align='C')
        
        # Specificații (Max 8 rânduri pentru siguranță)
        pdf.set_font("Arial", "", 6.5)
        y_pos = current_y + 12
        display_specs = get_specs_in_order(item['specs'], original_columns, item['bat'], item['acc'], item['stoc'], item['ram'])
        
        for k, v in list(display_specs.items())[:8]:
            pdf.set_xy(current_x + 2, y_pos)
            line = f"{k}: {v}"
            pdf.cell(label_w - 4, 3, clean_for_pdf(line))
            y_pos += 3.2

        # Linie Preț
        pdf.line(current_x + 5, current_y + 40, current_x + label_w - 5, current_y + 40)
        
        # --- PREȚ (Cifre Mari + lei mic) ---
        pdf.set_text_color(255, 0, 0)
        p_val = str(item['price'])
        
        pdf.set_font("Arial", "B", 24) # Cifre duble
        w_p = pdf.get_string_width(p_val)
        pdf.set_font("Arial", "B", 9) # Lei mic
        w_l = pdf.get_string_width(" lei")
        
        start_x = current_x + (label_w - (w_p + w_l)) / 2
        pdf.set_xy(start_x, current_y + 42)
        pdf.set_font("Arial", "B", 24)
        pdf.write(10, p_val)
        
        pdf.set_xy(start_x + w_p + 1, current_y + 45) # Aliniat mai jos un pic
        pdf.set_font("Arial", "B", 9)
        pdf.write(10, " lei")
        
        # --- COD (Dreapta) ---
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "B", 6)
        pdf.set_xy(current_x, current_y + 49)
        pdf.cell(label_w - 2, 3, clean_for_pdf(item['code']), align='R')

        # BANDA ROȘIE + LOGO
        pdf.set_fill_color(255, 0, 0)
        pdf.rect(current_x + 0.2, current_y + 51, label_w - 0.4, 8.8, 'F')
        
        if logo_content:
            try:
                pdf.image(logo_content, x=current_x + 5, y=current_y + 52.5, w=30, type='PNG')
            except:
                pass

    return pdf.output(dest='S').encode('latin-1')

# --- UI ---
st.set_page_config(page_title="Express Labels", layout="wide")
st.title("📱 Generator Etichete Smart")

if df.empty:
    st.error("Nu s-au putut încărca datele.")
else:
    cols = st.columns(3)
    data_to_export = []

    for i in range(3):
        with cols[i]:
            brand = st.selectbox(f"Brand {i+1}", ["-"] + sorted(df["Brand"].unique().tolist()), key=f"b{i}")
            model = st.selectbox(f"Model {i+1}", ["-"] + sorted(df[df["Brand"]==brand]["Model"].unique().tolist()) if brand != "-" else ["-"], key=f"m{i}")
            
            st.write("---")
            c1, c2 = st.columns(2)
            stoc = c1.selectbox("Stocare", ["-", "64GB", "128GB", "256GB", "512GB"], key=f"s{i}")
            ram = c2.selectbox("RAM", ["-", "4GB", "6GB", "8GB", "12GB"], key=f"r{i}")
            
            price = st.number_input("Preț (lei)", min_value=0, key=f"p{i}")
            
            cx1, cx2 = st.columns([2,1])
            cod_b = cx1.text_input("Cod B", "32451", key=f"cb{i}")
            ag = cx2.selectbox("AG", list(range(1,56)), 28, key=f"ag{i}")
            
            bat = st.slider("Baterie %", 50, 100, 100, key=f"bt{i}")
            
            if brand != "-" and model != "-":
                row = df[(df["Brand"]==brand) & (df["Model"]==model)].iloc[0].to_dict()
                data_to_export.append({
                    'specs': row, 'price': price, 'code': f"B{cod_b}@{ag}",
                    'bat': bat, 'acc': [], 'stoc': stoc, 'ram': ram
                })
                # Previzualizare simplă
                st.info(f"Etichetă gata pentru {brand} {model}")

    st.divider()
    if data_to_export:
        try:
            pdf_bytes = create_pdf(data_to_export, df.columns)
            st.download_button(
                label="🔴 DESCARCĂ PDF ETICHETE",
                data=pdf_bytes,
                file_name="etichete_express.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Eroare la generare: {e}")
