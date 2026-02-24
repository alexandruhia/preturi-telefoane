import streamlit as st
import pandas as pd
from fpdf import FPDF

# Configurare interfață
st.set_page_config(page_title="Preturi Telefoane", page_icon="📱", layout="centered")

# --- FUNCȚIE ÎNCĂRCARE DATE DIN GOOGLE DRIVE ---
@st.cache_data(ttl=60) # Actualizează datele la fiecare minut
def incarca_date():
    sheet_url = "https://docs.google.com/spreadsheets/d/1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA/edit?usp=sharing"
    try:
        url_export = sheet_url.split("/edit")[0] + "/export?format=xlsx"
        df = pd.read_excel(url_export)
        # Curățăm numele coloanelor (eliminăm spații invizibile)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"⚠️ Eroare la conexiune: {e}")
        return None

# --- FUNCȚIE GENERARE PDF ---
def genereaza_pdf(row, coloane):
    pdf = FPDF()
    pdf.add_page()
    
    # Stil Header
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(33, 150, 243) 
    pdf.cell(200, 15, txt=f"FISA TEHNICA: {row['Brand']} {row['Model']}", ln=True, align='C')
    pdf.ln(5)
    
    # Tabel specificații
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 10)
    
    for col in coloane:
        if col in row.index:
            # Protecție pentru caractere speciale
            nume_col = str(col).encode('latin-1', 'replace').decode('latin-1')
            valoare = str(row[col]).encode('latin-1', 'replace').decode('latin-1')
            
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(55, 10, txt=f"{nume_col}:", border=1)
            pdf.set_font("Arial", size=10)
            pdf.cell(135, 10, txt=f" {valoare}", border=1, ln=True)
            
    return pdf.output(dest='S').encode('latin-1')

# --- LOGICA APLICAȚIEI ---
st.title("💰 Aplicația Preturi")

df = incarca_date()

# Definirea coloanelor tale exacte
coloanele_tale = [
    "Brand", "Model", "Display", "OS", "Procesor", 
    "Stocare", "RAM", "Camera principala", "Selfie", 
    "Sanatate baterie", "Capacitate baterie"
]

if df is not None:
    # 1. Filtre Dropdown
    col_a, col_b = st.columns(2)
    
    with col_a:
        branduri = sorted(df['Brand'].dropna().unique())
        brand_ales = st.selectbox("Alege Brandul:", branduri)

    with col_b:
        modele_filtrate = df[df['Brand'] == brand_ales]['Model'].dropna().unique()
        model_ales = st.selectbox("Alege Modelul:", modele_filtrate)

    # 2. Preluare date model selectat
    date_tel = df[(df['Brand'] == brand_ales) & (df['Model'] == model_ales)].iloc[0]

    # 3. Afișare pe ecran
    st.info(f"### Specificații {model_ales}")
    
    # Împărțim specificațiile în două coloane vizuale
    c1, c2 = st.columns(2)
    specificatii_afisare = coloanele_tale[2:] # Sărim peste Brand și Model la afișare text
    
    for i, col in enumerate(specificatii_afisare):
        if col in date_tel.index:
            val = date_tel[col] if pd.notna(date_tel[col]) else "-"
            if i % 2 == 0:
                c1.write(f"**{col}:** {val}")
            else:
                c2.write(f"**{col}:** {val}")

    st.divider()

    # 4. Buton Export PDF
    if st.button("📄 Descarcă Specificații (PDF)"):
        try:
            pdf_out = genereaza_pdf(date_tel, coloanele_tale)
            st.download_button(
                label="Confirmă Descărcarea",
                data=pdf_out,
                file_name=f"Specificatii_{model_ales}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Eroare PDF: {e}")
else:
    st.warning("Verifică link-ul Google Sheets și conexiunea la internet.")