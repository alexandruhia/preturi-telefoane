import streamlit as st
import pandas as pd
from fpdf import FPDF

# --- CONFIGURARE ȘI ÎNCĂRCARE DATE ---
SHEET_ID = '1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA'
URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'

@st.cache_data(ttl=600) # Reîncarcă datele la fiecare 10 minute
def load_data():
    try:
        df = pd.read_csv(URL)
        # Curățăm numele coloanelor și datele de spații inutile
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Eroare la citirea tabelului: {e}")
        return pd.DataFrame()

df = load_data()

# --- FUNCȚIE FILTRARE SPECIFICAȚII COMPLETATE ---
def get_clean_specs(row_dict):
    """Returnează doar perechile cheie-valoare care nu sunt goale."""
    clean = {}
    for k, v in row_dict.items():
        # Verificăm dacă valoarea nu este NaN, null, 0 sau string gol
        if pd.notnull(v) and str(v).strip() not in ["", "0", "nan", "None"]:
            clean[k] = str(v).strip()
    return clean

# --- FUNCȚIE GENERARE PDF ---
def create_pdf(selected_phones_list):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, txt="Specificatii Tehnice Telefoane", ln=True, align='C')
    pdf.ln(10)
    
    for phone in selected_phones_list:
        if phone:
            # Header Telefon
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("Arial", "B", 12)
            brand_model = f"{phone.get('Brand', '')} {phone.get('Model', '')}"
            pdf.cell(190, 10, txt=brand_model.upper(), ln=True, fill=True)
            
            # Specificații (doar cele completate)
            pdf.set_font("Arial", "", 10)
            specs = get_clean_specs(phone)
            for key, value in specs.items():
                if key not in ["Brand", "Model"]:
                    # Formatare: Nume Coloană: Valoare
                    text = f"{key}: {value}"
                    pdf.multi_cell(190, 7, txt=text)
            
            pdf.ln(5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
            
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INTERFAȚA UTILIZATOR (UI) ---
st.set_page_config(page_title="Specificații Telefoane", layout="wide")
st.title("📱 Selector Specificații (Live din Sheets)")

if df.empty:
    st.error("Nu am putut prelua datele. Asigură-te că link-ul Google Sheet este Public (Anyone with the link).")
else:
    # Cele 3 coloane (Tab-uri)
    cols = st.columns(3)
    phones_to_export = []

    for i, col in enumerate(cols):
        with col:
            st.subheader(f"Telefon {i+1}")
            
            # 1. Selectare Brand
            brands = sorted(df["Brand"].dropna().unique().tolist())
            brand_sel = st.selectbox(f"Alege Brand", ["-"] + brands, key=f"b_{i}")
            
            if brand_sel != "-":
                # 2. Selectare Model (filtrat)
                models = df[df["Brand"] == brand_sel]["Model"].dropna().tolist()
                model_sel = st.selectbox(f"Alege Model", ["-"] + models, key=f"m_{i}")
                
                if model_sel != "-":
                    # Preluăm rândul întreg
                    raw_specs = df[(df["Brand"] == brand_sel) & (df["Model"] == model_sel)].iloc[0].to_dict()
                    # Filtrăm doar ce este completat
                    final_specs = get_clean_specs(raw_specs)
                    phones_to_export.append(raw_specs)
                    
                    # Afișare în platformă
                    with st.expander("Vezi Specificații", expanded=True):
                        for k, v in final_specs.items():
                            if k not in ["Brand", "Model"]:
                                st.write(f"**{k}:** {v}")
                else:
                    phones_to_export.append(None)
            else:
                phones_to_export.append(None)

    st.divider()

    # --- BUTON EXPORT ---
    valid_selection = [p for p in phones_to_export if p is not None]
    
    if valid_selection:
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("🚀 Pregătește PDF"):
                pdf_data = create_pdf(valid_selection)
                st.download_button(
                    label="📥 Descarcă PDF-ul",
                    data=pdf_data,
                    file_name="specificatii_telefoane.pdf",
                    mime="application/pdf"
                )
    else:
        st.info("Selectează cel puțin un telefon din listele de mai sus pentru a genera PDF-ul.")

# Buton de refresh manual în sidebar
if st.sidebar.button("🔄 Refresh Date Google Sheets"):
    st.cache_data.clear()
    st.rerun()
