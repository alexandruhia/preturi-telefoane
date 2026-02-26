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

# --- FUNCȚIE GENERARE PDF (LATIME JUMATATE) ---
def create_pdf(selected_phones_list, prices):
    pdf = FPDF()
    pdf.add_page()
    
    # Setăm lățimea etichetei la ~95mm (aprox jumătate din A4 minus margini)
    label_width = 95 
    
    for i, phone in enumerate(selected_phones_list):
        if phone:
            specs = get_clean_specs(phone)
            brand_model = f"{phone.get('Brand', '')} {phone.get('Model', '')}".upper()
            price_val = str(prices[i])
            
            start_y = pdf.get_y()
            num_lines = len([k for k in specs if k not in ["Brand", "Model"]])
            frame_height = (num_lines * 6) + 50 
            
            # Desenare Frame Roșu (Centrat pe pagină sau aliniat la stânga)
            # Folosim x=57.5 pentru a-l centra pe foaia de 210mm
            pos_x = 57.5 
            pdf.set_draw_color(255, 0, 0)
            pdf.set_line_width(1)
            pdf.rect(pos_x, start_y, label_width, frame_height)
            
            # Titlu Model
            pdf.set_y(start_y + 5)
            pdf.set_x(pos_x + 5)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(label_width - 10, 8, txt=brand_model, ln=True, align='C')
            
            # Specificații
            pdf.set_font("Arial", "", 9)
            for key, value in specs.items():
                if key not in ["Brand", "Model"]:
                    pdf.set_x(pos_x + 5)
                    pdf.multi_cell(label_width - 10, 5, txt=f"{key}: {value}", align='L')
            
            # RUBRICA PREȚ
            pdf.set_y(start_y + frame_height - 25)
            pdf.set_text_color(255, 0, 0)
            pdf.set_x(pos_x)
            
            # Pret (20) + Cifra (40) + lei (20) - grupate la mijlocul etichetei
            pdf.set_font("Arial", "B", 16) # Scăzut puțin pentru a încăpea în 95mm
            pdf.cell(25, 15, txt="Pret: ", ln=False, align='R')
            pdf.set_font("Arial", "B", 30)
            pdf.cell(35, 15, txt=price_val, ln=False, align='C')
            pdf.set_font("Arial", "B", 16)
            pdf.cell(20, 15, txt=" lei", ln=True, align='L')
            
            pdf.set_text_color(0, 0, 0)
            pdf.ln(10)
            
            # Dacă eticheta următoare nu mai are loc pe pagină, adăugăm pagină nouă
            if pdf.get_y() > 220:
                pdf.add_page()
            
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INTERFAȚĂ STREAMLIT ---
st.set_page_config(page_title="Etichete Telefoane", layout="wide")

# CSS pentru lățime jumătate (max-width: 50%)
st.markdown("""
    <style>
    .red-frame {
        border: 4px solid #FF0000;
        border-radius: 15px;
        padding: 20px;
        margin: 10px auto; /* Centrare */
        background-color: #FFFFFF;
        width: 100%; /* Ocupă tot containerul coloanei care e deja 1/3 */
        max-width: 300px; /* Limităm lățimea efectivă */
        min-height: 450px;
        display: flex;
        flex-direction: column;
    }
    .specs-container { flex-grow: 1; font-size: 14px; }
    .price-container {
        text-align: center;
        margin-top: 15px;
        border-top: 2px solid #FF0000;
        padding-top: 15px;
    }
    .label-price { color: #FF0000; font-size: 18px; font-weight: bold; }
    .value-price { color: #FF0000; font-size: 36px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("📱 Generator Etichete Înguste")

cols = st.columns(3)
phones_to_export = []
prices_to_export = []

for i, col in enumerate(cols):
    with col:
        st.subheader(f"Slot {i+1}")
        brand_sel = st.selectbox(f"Brand", ["-"] + sorted(df["Brand"].dropna().unique().tolist()), key=f"b_{i}")
        
        if brand_sel != "-":
            model_sel = st.selectbox(f"Model", ["-"] + df[df["Brand"] == brand_sel]["Model"].dropna().tolist(), key=f"m_{i}")
            user_price = st.number_input(f"Pret lei", min_value=0, value=0, key=f"p_{i}")
            
            if model_sel != "-":
                raw_specs = df[(df["Brand"] == brand_sel) & (df["Model"] == model_sel)].iloc[0].to_dict()
                final_specs = get_clean_specs(raw_specs)
                phones_to_export.append(raw_specs)
                prices_to_export.append(user_price)
                
                specs_html = "".join([f"• {k}: {v}<br>" for k, v in final_specs.items() if k not in ["Brand", "Model"]])
                
                html_card = f"""
                <div class="red-frame">
                    <div class="specs-container">
                        <h3 style="text-align:center;">{brand_sel}<br>{model_sel}</h3>
                        {specs_html}
                    </div>
                    <div class="price-container">
                        <span class="label-price">Pret:</span>
                        <span class="value-price">{user_price}</span>
                        <span class="label-price">lei</span>
                    </div>
                </div>
                """
                st.markdown(html_card, unsafe_allow_html=True)
            else:
                phones_to_export.append(None)
                prices_to_export.append(0)
        else:
            phones_to_export.append(None)
            prices_to_export.append(0)

st.divider()

if any(phones_to_export):
    active_phones = [p for p in phones_to_export if p is not None]
    active_prices = [prices_to_export[i] for i, p in enumerate(phones_to_export) if p is not None]
    
    if st.button("🔴 DESCARCĂ ETICHETE PDF (95mm)"):
        pdf_data = create_pdf(active_phones, active_prices)
        st.download_button(label="📥 Salvează PDF", data=pdf_data, file_name="etichete_inguste.pdf", mime="application/pdf")
