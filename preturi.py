import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests
import os

# --- CONFIGURARE PAGINĂ (Trebuie să fie prima) ---
st.set_page_config(page_title="Etichete Pro", layout="wide")

SHEET_ID = '1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA'
URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'
LOGO_URL = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"

# --- CACHE DATE ȘI LOGO (Viteză maximă) ---
@st.cache_data(ttl=3600)
def load_data():
    try:
        df = pd.read_csv(URL)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

@st.cache_resource
def get_logo():
    try:
        resp = requests.get(LOGO_URL, timeout=5)
        if resp.status_code == 200:
            return resp.content
    except:
        return None
    return None

df = load_data()
LOGO_DATA = get_logo()

# --- UTILITARE ---
def clean_for_pdf(text):
    if not text: return ""
    # Mapare rapidă pentru diacritice
    rep = {'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't', 'Ă': 'A', 'Â': 'A', 'Î': 'I', 'Ș': 'S', 'Ț': 'T'}
    t = "".join(rep.get(c, c) for c in str(text))
    return t.encode('latin-1', 'replace').decode('latin-1')

def get_specs_in_order(row_dict, original_columns, bat, acc, stoc, ram):
    clean = {}
    skip = {"brand", "model", "stocare", "ram", "sanatate baterie", "sănătate baterie", "baterie", "battery", "storage"}
    
    # Adăugăm întâi Stocare și RAM dacă există
    if stoc and stoc != "-": clean["Stocare"] = stoc
    if ram and ram != "-": clean["RAM"] = ram
    
    for col in original_columns:
        c_low = col.lower()
        if c_low in skip: continue
        val = row_dict.get(col)
        if pd.notnull(val) and str(val).strip() not in ["", "0", "nan", "NaN"]:
            clean[col] = str(val).strip()
    
    if bat: clean["Sanatate baterie"] = f"{bat}%"
    if acc: clean["Accesorii"] = ", ".join(acc)
    return clean

# --- GENERARE PDF OPTIMIZATĂ ---
def create_pdf(phones_data, original_cols):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    l_width, l_height = 60, 80
    margin_x = (210 - (l_width * 3)) / 2
    curr_y = 20

    # Salvăm logo-ul temporar o singură dată pentru sesiune
    if LOGO_DATA:
        with open("logo_temp.png", "wb") as f:
            f.write(LOGO_DATA)

    for i, data in enumerate(phones_data):
        if not data: continue
        curr_x = margin_x + (i * l_width)
        
        # Date etichetă
        phone = data['raw']
        specs = get_specs_in_order(phone, original_cols, data['bat'], data['acc'], data['stoc'], data['ram'])
        
        # Desenare
        pdf.set_draw_color(255, 0, 0)
        pdf.rect(curr_x, curr_y, l_width, l_height)
        
        # Titlu
        pdf.set_font("Arial", "B", 9)
        pdf.set_xy(curr_x, curr_y + 3)
        title = f"{phone.get('Brand', '')} {phone.get('Model', '')}".upper()
        pdf.multi_cell(l_width, 4, clean_for_pdf(title), align='C')
        
        # Specs
        pdf.set_font("Arial", "", 6.5)
        sy = pdf.get_y() + 2
        for k, v in list(specs.items())[:10]:
            pdf.set_xy(curr_x + 2, sy)
            pdf.set_font("Arial", "B", 6.5)
            pdf.write(3.5, f"{clean_for_pdf(k)}: ")
            pdf.set_font("Arial", "", 6.5)
            txt = clean_for_pdf(v)
            pdf.write(3.5, txt[:28] + "..." if len(txt) > 30 else txt)
            sy += 3.5

        # Preț & Cod
        pdf.set_draw_color(255, 0, 0)
        pdf.line(curr_x + 4, curr_y + l_height - 22, curr_x + l_width - 4, curr_y + l_height - 22)
        
        pdf.set_text_color(255, 0, 0)
        pdf.set_font("Arial", "B", 20)
        p_str = str(data['price'])
        pdf.set_xy(curr_x, curr_y + l_height - 18)
        pdf.cell(l_width, 10, f"{p_str} lei", align='C')
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "B", 6)
        pdf.set_xy(curr_x, curr_y + l_height - 12)
        pdf.cell(l_width - 2, 3, data['code'], align='R')

        # Footer
        pdf.set_fill_color(255, 0, 0)
        pdf.rect(curr_x + 0.1, curr_y + l_height - 8.1, l_width - 0.2, 8, 'F')
        if LOGO_DATA:
            pdf.image("logo_temp.png", x=curr_x + (l_width-30)/2, y=curr_y + l_height - 7, w=30)

    return pdf.output(dest='S').encode('latin-1')

# --- UI ---
st.title("📱 Etichete Express (Instant Load)")

if not df.empty:
    cols = st.columns(3)
    export_data = [None] * 3

    for i in range(3):
        with cols[i]:
            st.subheader(f"Telefon {i+1}")
            brand = st.selectbox(f"Brand", ["-"] + sorted(df["Brand"].unique().tolist()), key=f"b{i}")
            
            model = "-"
            if brand != "-":
                model = st.selectbox(f"Model", ["-"] + sorted(df[df["Brand"] == brand]["Model"].tolist()), key=f"m{i}")
            
            s1, s2 = st.columns(2)
            stoc = s1.selectbox("Stocare", ["-", "64 GB", "128 GB", "256 GB", "512 GB"], key=f"s{i}")
            ram = s2.selectbox("RAM", ["-", "4 GB", "6 GB", "8 GB", "12 GB"], key=f"r{i}")
            
            if brand != "-" and model != "-":
                price = st.number_input("Preț", min_value=0, key=f"p{i}")
                b_cod = st.text_input("Cod B", "32451", key=f"bc{i}")
                ag = st.selectbox("AG", list(range(1, 56)), 27, key=f"ag{i}")
                bat = st.number_input("Baterie %", 1, 100, 100, key=f"bt{i}")
                
                acc = [opt for opt in ["husă", "cutie", "încărcător"] if st.checkbox(opt, key=f"ac{i}{opt}")]
                
                raw = df[(df["Brand"] == brand) & (df["Model"] == model)].iloc[0].to_dict()
                export_data[i] = {'raw': raw, 'price': price, 'code': f"B{b_cod}@{ag}", 'bat': bat, 'acc': acc, 'stoc': stoc, 'ram': ram}

    st.divider()
    
    if any(export_data):
        pdf_bytes = create_pdf(export_data, df.columns)
        _, center_col, _ = st.columns([1, 1, 1])
        with center_col:
            st.download_button("🔴 DESCARCĂ PDF", pdf_bytes, "etichete.pdf", "application/pdf", use_container_width=True)

else:
    st.error("Baza de date nu a putut fi încărcată.")
