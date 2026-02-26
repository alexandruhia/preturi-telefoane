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
    clean = {}
    for k, v in row_dict.items():
        if pd.notnull(v) and str(v).strip() not in ["", "0", "nan", "None", "NaN"]:
            clean[k] = str(v).strip()
    return clean

# --- FUNCȚIE GENERARE PDF CU PREȚ EDITABIL ---
def create_pdf(selected_phones_list, prices):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, txt="Specificatii Tehnice si Preturi", ln=True, align='C')
    pdf.ln(5)
    
    for i, phone in enumerate(selected_phones_list):
        if phone:
            specs = get_clean_specs(phone)
            brand_model = f"{phone.get('Brand', '')} {phone.get('Model', '')}".upper()
            price_val = prices[i]
            
            start_y = pdf.get_y()
            # Calculăm înălțimea: linii specificații + 1 linie pentru preț + margini
            num_lines = len([k for k in specs if k not in ["Brand", "Model"]]) + 2
            frame_height = (num_lines * 7) + 12
            
            # Frame Roșu
            pdf.set_draw_color(255, 0, 0)
            pdf.set_line_width(0.8)
            pdf.rect(10, start_y, 190, frame_height)
            
            # Conținut
            pdf.set_y(start_y + 3)
            pdf.set_x(15)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(180, 8, txt=brand_model, ln=True)
            
            # Linie Preț (Bold)
            pdf.set_x(15)
            pdf.set_text_color(200, 0, 0) # Prețul cu roșu în PDF
            pdf.cell(180, 8, txt=f"Pret: {price_val} lei", ln=True)
            pdf.set_text_color(0, 0, 0) # Reset la negru
            
            # Restul specificațiilor
            pdf.set_font("Arial", "", 10)
            for key, value in specs.items():
                if key not in ["Brand", "Model"]:
                    pdf.set_x(15)
                    pdf.multi_cell(180, 6, txt=f"{key}: {value}")
            
            pdf.ln(15) 
            
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INTERFAȚA UTILIZATOR ---
st.set_page_config(page_title="Comparator Telefoane", layout="wide")

st.markdown("""
    <style>
    .red-frame {
        border: 3px solid #FF0000;
        border-radius: 10px;
        padding: 15px;
        margin-top: 10px;
        background-color: #FFFFFF;
    }
    .price-text {
        color: #FF0000;
        font-size: 20px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📱 Comparator cu Preț Editabil")

if df.empty:
    st.error("Conectează Google Sheet-ul.")
else:
    cols = st.columns(3)
    phones_to_export = []
    prices_to_export = []

    for i, col in enumerate(cols):
        with col:
            st.subheader(f"Telefon {i+1}")
            
            brand_sel = st.selectbox(f"Selectează Brand", ["-"] + sorted(df["Brand"].dropna().unique().tolist()), key=f"b_{i}")
            
            if brand_sel != "-":
                model_sel = st.selectbox(f"Selectează Model", ["-"] + df[df["Brand"] == brand_sel]["Model"].dropna().tolist(), key=f"m_{i}")
                
                # --- RUBRICA DE PREȚ ---
                user_price = st.number_input(f"Introduceți Preț (lei)", min_value=0, value=0, key=f"p_{i}")
                
                if model_sel != "-":
                    raw_specs = df[(df["Brand"] == brand_sel) & (df["Model"] == model_sel)].iloc[0].to_dict()
                    final_specs = get_clean_specs(raw_specs)
                    
                    phones_to_export.append(raw_specs)
                    prices_to_export.append(user_price)
                    
                    # Previzualizare cu Frame
                    content = f"<h4>{brand_sel} {model_sel}</h4>"
                    content += f"<p class='price-text'>Pret: {user_price} lei</p><hr>"
                    for k, v in final_specs.items():
                        if k not in ["Brand", "Model"]:
                            content += f"<b>{k}:</b> {v}<br>"
                    
                    st.markdown(f'<div class="red-frame">{content}</div>', unsafe_allow_html=True)
                else:
                    phones_to_export.append(None)
                    prices_to_export.append(0)
            else:
                phones_to_export.append(None)
                prices_to_export.append(0)

    st.divider()

    # --- EXPORT ---
    valid_selection = [p for p in phones_to_export if p is not None]
    if valid_selection:
        # Filtrăm și prețurile doar pentru telefoanele selectate
        active_prices = [prices_to_export[i] for i, p in enumerate(phones_to_export) if p is not None]
        
        if st.button("🔴 Descarcă PDF cu Prețuri"):
            pdf_data = create_pdf(valid_selection, active_prices)
            st.download_button(
                label="📥 Salvează Fișierul PDF",
                data=pdf_data,
                file_name="oferta_telefoane.pdf",
                mime="application/pdf"
            )
