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

# --- FUNCȚIE GENERARE PDF (A4 PORTRET - ÎNĂLȚIME REDUSĂ CU 40%) ---
def create_pdf(selected_phones_list, prices):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # Parametri dimensiuni
    margin_left = 7
    gutter = 4           
    label_width = 62     
    # Înălțimea inițială era 150mm. Redusă cu 40% => 90mm
    label_height = 90   
    
    for i, phone in enumerate(selected_phones_list):
        if phone:
            specs = get_clean_specs(phone)
            brand_model = f"{phone.get('Brand', '')} {phone.get('Model', '')}".upper()
            price_val = str(prices[i])
            
            current_x = margin_left + (i * (label_width + gutter))
            current_y = 20
            
            # 1. Frame Roșu
            pdf.set_draw_color(255, 0, 0)
            pdf.set_line_width(0.8)
            pdf.rect(current_x, current_y, label_width, label_height)
            
            # 2. Titlu (Font adaptat)
            pdf.set_y(current_y + 4)
            pdf.set_x(current_x)
            pdf.set_font("Arial", "B", 9)
            pdf.multi_cell(label_width, 4, txt=brand_model, align='C')
            
            # 3. Specificații (Font compact)
            pdf.set_font("Arial", "", 7.5)
            pdf.set_y(current_y + 14)
            # Limităm afișarea la câteva linii pentru a nu ieși din cadrul micșorat
            lines_count = 0
            for key, value in specs.items():
                if key not in ["Brand", "Model"] and lines_count < 10:
                    pdf.set_x(current_x + 3)
                    pdf.multi_cell(label_width - 6, 3.5, txt=f"{key}: {value}", align='L')
                    lines_count += 1
            
            # 4. Rubrica Preț (Mutată mai sus pentru a încăpea în 90mm)
            pdf.set_text_color(255, 0, 0)
            pdf.set_y(current_y + label_height - 18)
            pdf.set_x(current_x)
            
            pdf.set_font("Arial", "B", 13) 
            pdf.cell(15, 10, txt="Pret:", ln=False, align='R')
            
            pdf.set_font("Arial", "B", 22) 
            pdf.cell(32, 10, txt=price_val, ln=False, align='C')
            
            pdf.set_font("Arial", "B", 13) 
            pdf.cell(10, 10, txt="lei", ln=True, align='L')
            
            pdf.set_text_color(0, 0, 0)
            
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INTERFAȚĂ STREAMLIT ---
st.set_page_config(page_title="Etichete Compacte", layout="wide")

st.markdown("""
    <style>
    .label-container {
        border: 3px solid #FF0000;
        border-radius: 10px;
        padding: 10px;
        background-color: white;
        min-height: 350px; /* Redus vizual în browser */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .specs-text { font-size: 12px; line-height: 1.2; overflow: hidden; }
    .price-section {
        text-align: center;
        border-top: 1px solid #eee;
        padding-top: 5px;
    }
    .text-20 { font-size: 20px; font-weight: bold; color: #FF0000; }
    .text-40 { font-size: 40px; font-weight: bold; color: #FF0000; }
    </style>
    """, unsafe_allow_html=True)

st.title("📱 Etichete Compacte (H-40%)")

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
                specs_html = "".join([f"• {k}: {v}<br>" for k, v in list(clean_s.items())[:10] if k not in ["Brand", "Model"]])
                
                st.markdown(f"""
                <div class="label-container">
                    <div class="specs-text">
                        <h4 style="text-align:center; margin-bottom:5px;">{brand_sel} {model_sel}</h4>
                        {specs_html}
                    </div>
                    <div class="price-section">
                        <span class="text-20">Pret:</span>
                        <span class="text-40">{u_price}</span>
                        <span class="text-20">lei</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

st.divider()

if any(phones_to_export):
    if st.button("🔴 DESCARCĂ PDF COMPACT (90mm înălțime)"):
        pdf_data = create_pdf(phones_to_export, prices_to_export)
        st.download_button(label="📥 Salvează PDF", data=pdf_data, file_name="etichete_compacte.pdf", mime="application/pdf")
