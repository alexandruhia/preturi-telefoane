import streamlit as st
import pandas as pd
from fpdf import FPDF

# --- CONFIGURARE ȘI ÎNCĂRCARE DATE ---
SHEET_ID = '1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA'
URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'

@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(URL)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Eroare la citirea tabelului: {e}")
        return pd.DataFrame()

df = load_data()

def get_clean_specs(row_dict):
    """Filtrează doar coloanele care au date completate."""
    clean = {}
    for k, v in row_dict.items():
        if pd.notnull(v) and str(v).strip() not in ["", "0", "nan", "None", "NaN"]:
            clean[k] = str(v).strip()
    return clean

# --- FUNCȚIE GENERARE PDF CU FRAME ROȘU ---
def create_pdf(selected_phones_list):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, txt="Specificatii Tehnice Telefoane", ln=True, align='C')
    pdf.ln(5)
    
    for phone in selected_phones_list:
        if phone:
            specs = get_clean_specs(phone)
            brand_model = f"{phone.get('Brand', '')} {phone.get('Model', '')}".upper()
            
            # Start poziție pentru frame
            start_y = pdf.get_y()
            pdf.set_font("Arial", "B", 12)
            
            # Calculăm înălțimea necesară aproximativă pentru frame
            # (Nr. linii * înălțime linie) + margini
            num_lines = len([k for k in specs if k not in ["Brand", "Model"]]) + 1
            frame_height = (num_lines * 7) + 10
            
            # Desenăm frame-ul roșu (RGB: 255, 0, 0)
            pdf.set_draw_color(255, 0, 0)
            pdf.set_line_width(0.8)
            pdf.rect(10, start_y, 190, frame_height)
            
            # Adăugăm conținutul în interiorul frame-ului
            pdf.set_y(start_y + 2)
            pdf.set_x(15)
            pdf.cell(180, 8, txt=brand_model, ln=True)
            
            pdf.set_font("Arial", "", 10)
            for key, value in specs.items():
                if key not in ["Brand", "Model"]:
                    pdf.set_x(15)
                    pdf.multi_cell(180, 6, txt=f"{key}: {value}")
            
            pdf.ln(10) # Spațiu între telefoane
            
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INTERFAȚA UTILIZATOR (UI) ---
st.set_page_config(page_title="Comparator Telefoane", layout="wide")

# CSS pentru frame-ul roșu în browser
st.markdown("""
    <style>
    .red-frame {
        border: 2px solid #FF0000;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
        background-color: #FFFafa;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📱 Comparator cu Frame Roșu")

if df.empty:
    st.error("Verifică setările de share ale Google Sheet-ului.")
else:
    cols = st.columns(3)
    phones_to_export = []

    for i, col in enumerate(cols):
        with col:
            st.subheader(f"Slot {i+1}")
            
            brands = sorted(df["Brand"].dropna().unique().tolist())
            brand_sel = st.selectbox(f"Selectează Brand", ["-"] + brands, key=f"b_{i}")
            
            if brand_sel != "-":
                models = df[df["Brand"] == brand_sel]["Model"].dropna().tolist()
                model_sel = st.selectbox(f"Selectează Model", ["-"] + models, key=f"m_{i}")
                
                if model_sel != "-":
                    raw_specs = df[(df["Brand"] == brand_sel) & (df["Model"] == model_sel)].iloc[0].to_dict()
                    final_specs = get_clean_specs(raw_specs)
                    phones_to_export.append(raw_specs)
                    
                    # Încadrarea în frame roșu în interfață
                    content = f"<h4>{brand_sel} {model_sel}</h4>"
                    for k, v in final_specs.items():
                        if k not in ["Brand", "Model"]:
                            content += f"<b>{k}:</b> {v}<br>"
                    
                    st.markdown(f'<div class="red-frame">{content}</div>', unsafe_allow_html=True)
                else:
                    phones_to_export.append(None)
            else:
                phones_to_export.append(None)

    st.divider()

    # --- BUTON EXPORT ---
    valid_selection = [p for p in phones_to_export if p is not None]
    if valid_selection:
        if st.button("🔴 Generează PDF cu Frame-uri Roșii"):
            pdf_data = create_pdf(valid_selection)
            st.download_button(
                label="📥 Descarcă Specificațiile",
                data=pdf_data,
                file_name="specificatii_telefoane_red.pdf",
                mime="application/pdf"
            )
