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

# --- FUNCȚIE GENERARE PDF (REDUSE CU ÎNCĂ 20%) ---
def create_pdf(selected_phones_list, prices):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # Parametri noi (Reduși cu 20% față de versiunea anterioară)
    margin_left = 15
    gutter = 8           
    label_width = 50     # Redus de la 62mm
    label_height = 72    # Redus de la 90mm
    
    for i, phone in enumerate(selected_phones_list):
        if phone:
            specs = get_clean_specs(phone)
            brand_model = f"{phone.get('Brand', '')} {phone.get('Model', '')}".upper()
            price_val = str(prices[i])
            
            current_x = margin_left + (i * (label_width + gutter))
            current_y = 25
            
            # 1. Frame Roșu
            pdf.set_draw_color(255, 0, 0)
            pdf.set_line_width(0.6)
            pdf.rect(current_x, current_y, label_width, label_height)
            
            # 2. Titlu (Font micșorat)
            pdf.set_y(current_y + 3)
            pdf.set_x(current_x)
            pdf.set_font("Arial", "B", 8)
            pdf.multi_cell(label_width, 3.5, txt=brand_model, align='C')
            
            # 3. Specificații (Font foarte mic pentru a încăpea în 72mm)
            pdf.set_font("Arial", "", 6.5)
            pdf.set_y(current_y + 11)
            lines_shown = 0
            for key, value in specs.items():
                if key not in ["Brand", "Model"] and lines_shown < 8: # Maxim 8 rânduri
                    pdf.set_x(current_x + 2)
                    pdf.multi_cell(label_width - 4, 3, txt=f"{key}: {value}", align='L')
                    lines_shown += 1
            
            # 4. Rubrica Preț (Adaptată la spațiul mic)
            pdf.set_text_color(255, 0, 0)
            pdf.set_y(current_y + label_height - 15)
            pdf.set_x(current_x)
            
            # Ajustare proporțională fonturi preț
            pdf.set_font("Arial", "B", 11) # "Pret:"
            pdf.cell(12, 10, txt="Pret:", ln=False, align='R')
            
            pdf.set_font("Arial", "B", 18) # Valoare
            pdf.cell(26, 10, txt=price_val, ln=False, align='C')
            
            pdf.set_font("Arial", "B", 11) # "lei"
            pdf.cell(8, 10, txt="lei", ln=True, align='L')
            
            pdf.set_text_color(0, 0, 0)
            
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INTERFAȚĂ STREAMLIT ---
st.set_page_config(page_title="Etichete Mini", layout="wide")

st.markdown("""
    <style>
    .mini-label {
        border: 2px solid #FF0000;
        border-radius: 8px;
        padding: 8px;
        background-color: white;
        width: 100%;
        max-width: 240px; /* Reducere vizuală și în browser */
        min-height: 280px;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .specs-small { font-size: 11px; line-height: 1.1; overflow: hidden; }
    .price-mini {
        text-align: center;
        border-top: 1px solid #ff0000;
        padding-top: 5px;
        margin-top: 5px;
    }
    .p20 { font-size: 16px; font-weight: bold; color: #FF0000; }
    .p40 { font-size: 32px; font-weight: bold; color: #FF0000; }
    </style>
    """, unsafe_allow_html=True)

st.title("📱 Etichete Mini (-20%)")

cols = st.columns(3)
phones_to_export = [None, None, None]
prices_to_export = [0, 0, 0]

for i, col in enumerate(cols):
    with col:
        st.subheader(f"Slot {i+1}")
        brand_sel = st.selectbox(f"Brand", ["-"] + sorted(df["Brand"].dropna().unique().tolist()), key=f"b_{i}")
        
        if brand_sel != "-":
            model_sel = st.selectbox(f"Model", ["-"] + df[df["Brand"] == brand_sel]["Model"].dropna().tolist(), key=f"m_{i}")
            u_price = st.number_input(f"Pret", min_value=0, key=f"p_{i}")
            
            if model_sel != "-":
                raw_specs = df[(df["Brand"] == brand_sel) & (df["Model"] == model_sel)].iloc[0].to_dict()
                phones_to_export[i] = raw_specs
                prices_to_export[i] = u_price
                
                clean_s = get_clean_specs(raw_specs)
                # Afișăm doar primele 8 specificații pentru previzualizare
                specs_html = "".join([f"• {k}: {v}<br>" for k, v in list(clean_s.items())[:8] if k not in ["Brand", "Model"]])
                
                st.markdown(f"""
                <div class="mini-label">
                    <div class="specs-small">
                        <h5 style="text-align:center; margin:0 0 5px 0;">{brand_sel}<br>{model_sel}</h5>
                        {specs_html}
                    </div>
                    <div class="price-mini">
                        <span class="p20">Pret:</span>
                        <span class="p40">{u_price}</span>
                        <span class="p20">lei</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

st.divider()

if any(phones_to_export):
    if st.button("🔴 DESCARCĂ PDF MINI (50x72mm)"):
        pdf_data = create_pdf(phones_to_export, prices_to_export)
        st.download_button(label="📥 Salvează PDF", data=pdf_data, file_name="etichete_mini.pdf", mime="application/pdf")
