import streamlit as st
import pandas as pd
from fpdf import FPDF

# 1. Configurarea și citirea datelor din Google Sheets
# Am convertit link-ul tău pentru a fi citit direct ca CSV
SHEET_ID = '1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA'
SHEET_NAME = 'Sheet1' # Asigură-te că numele tab-ului este corect
URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'

@st.cache_data # Această funcție salvează datele temporar pentru viteză
def load_data():
    try:
        df = pd.read_csv(URL)
        # Curățăm coloanele de spații libere dacă există
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Eroare la conectarea cu Google Sheets: {e}")
        return pd.DataFrame()

df = load_data()

# 2. Funcția pentru generare PDF
def create_pdf(selected_phones):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="Specificatii Telefoane Selectate", ln=True, align='C')
    pdf.ln(10)
    
    for phone in selected_phones:
        if phone:
            pdf.set_font("Arial", "B", 12)
            # Folosim 'Model' și 'Brand' conform coloanelor din sheet-ul tău
            model_name = phone.get('Model', 'Nespecificat')
            brand_name = phone.get('Brand', 'Nespecificat')
            
            pdf.cell(200, 10, txt=f"Telefon: {brand_name} {model_name}", ln=True)
            pdf.set_font("Arial", "", 10)
            
            for key, value in phone.items():
                if key not in ["Brand", "Model"]:
                    pdf.cell(200, 8, txt=f"- {key}: {value}", ln=True)
            pdf.ln(5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # Linie de separare
            pdf.ln(5)
            
    return pdf.output(dest='S').encode('latin-1')

# 3. Interfața Streamlit
st.set_page_config(page_title="Comparator Google Sheets", layout="wide")
st.title("📱 Comparator Telefoane (Live din Google Sheets)")

if df.empty:
    st.warning("Nu am putut încărca datele. Verifică dacă Google Sheet-ul este setat pe 'Oricine are linkul poate vizualiza' (Anyone with the link can view).")
else:
    # Creăm 3 coloane (cele 3 "tab-uri" cerute)
    cols = st.columns(3)
    selected_data = []

    for i, col in enumerate(cols):
        with col:
            st.markdown(f"### 📱 Selecție Telefon {i+1}")
            
            # Dropdown pentru Brand
            brands = sorted(df["Brand"].unique().tolist())
            brand = st.selectbox(f"Alege Brand", ["-"] + brands, key=f"brand_{i}")
            
            if brand != "-":
                # Dropdown pentru Model filtrat după Brand
                models = df[df["Brand"] == brand]["Model"].tolist()
                model = st.selectbox(f"Alege Model", ["-"] + models, key=f"model_{i}")
                
                if model != "-":
                    # Extragere rând specificații
                    specs = df[(df["Brand"] == brand) & (df["Model"] == model)].iloc[0].to_dict()
                    selected_data.append(specs)
                    
                    # Previzualizare în platformă
                    st.success(f"**Specificații {model}**")
                    for key, val in specs.items():
                        if key not in ["Brand", "Model"]:
                            st.write(f"**{key}:** {val}")
                else:
                    selected_data.append(None)
            else:
                selected_data.append(None)

    st.divider()

    # 4. Buton Export PDF
    valid_phones = [p for p in selected_data if p is not None]
    if valid_phones:
        if st.button("Generează PDF pentru selecția actuală"):
            try:
                pdf_bytes = create_pdf(valid_phones)
                st.download_button(
                    label="📥 Descarcă fișierul PDF",
                    data=pdf_bytes,
                    file_name="comparatie_telefoane.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Eroare la generarea PDF: {e}")
    else:
        st.info("Selectați cel puțin un telefon pentru a activa butonul de export PDF.")

# Instrucțiune pentru refresh
if st.button("🔄 Actualizează datele din Google Sheet"):
    st.cache_data.clear()
    st.rerun()
