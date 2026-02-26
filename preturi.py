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

def get_specs_in_order(row_dict, original_columns):
    clean = {}
    for col in original_columns:
        if col not in ["Brand", "Model"]:
            val = row_dict.get(col)
            if pd.notnull(val) and str(val).strip() not in ["", "0", "nan", "None", "NaN"]:
                clean[col] = str(val).strip()
    return clean

# --- FUNCȚIE GENERARE PDF ---
def create_pdf(selected_phones_list, prices, original_columns):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    margin_left = 7
    gutter = 4           
    label_width = 62     # Lățime adaptată pentru fonturi mari
    label_height = 140   # Înălțime crescută pentru a cuprinde textul mare
    
    for i, phone in enumerate(selected_phones_list):
        if phone:
            specs = get_specs_in_order(phone, original_columns)
            brand_model = f"{phone.get('Brand', '')} {phone.get('Model', '')}".upper()
            price_val = str(prices[i])
            
            current_x = margin_left + (i * (label_width + gutter))
            current_y = 20
            
            # 1. Frame Roșu
            pdf.set_draw_color(255, 0, 0)
            pdf.set_line_width(1)
            pdf.rect(current_x, current_y, label_width, label_height)
            
            # 2. Titlu (Font 35 conform cerinței)
            # Notă: 35pt este foarte mare, am folosit multi_cell pentru a evita ieșirea din cadru
            pdf.set_y(current_y + 5)
            pdf.set_x(current_x + 2)
            pdf.set_font("Arial", "B", 35)
            pdf.multi_cell(label_width - 4, 12, txt=brand_model, align='C')
            
            # 3. Specificații (Font 20 conform cerinței)
            pdf.set_font("Arial", "", 20)
            pdf.set_y(pdf.get_y() + 5)
            
            lines_shown = 0
            for key, val in specs.items():
                if pdf.get_y() < (current_y + label_height - 35): # Verificăm să nu se suprapună peste preț
                    pdf.set_x(current_x + 3)
                    pdf.multi_cell(label_width - 6, 8, txt=f"• {val}", align='L')
                    lines_shown += 1
            
            # 4. Rubrica Preț (Păstrat dimensiunile anterioare pentru echilibru)
            pdf.set_text_color(255, 0, 0)
            pdf.set_y(current_y + label_height - 25)
            pdf.set_x(current_x)
            
            pdf.set_font("Arial", "B", 20) 
            pdf.cell(15, 15, txt="Pret:", ln=False, align='R')
            pdf.set_font("Arial", "B", 40) 
            pdf.cell(32, 15, txt=price_val, ln=False, align='C')
            pdf.set_font("Arial", "B", 20) 
            pdf.cell(10, 15, txt="lei", ln=True, align='L')
            
            pdf.set_text_color(0, 0, 0)
            
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INTERFAȚĂ STREAMLIT ---
st.set_page_config(page_title="Etichete Font Mare", layout="wide")

st.markdown("""
    <style>
    .big-label {
        border: 4px solid #FF0000;
        border-radius: 15px;
        padding: 20px;
        background-color: white;
        min-height: 600px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .title-35 { 
        font-size: 35px; 
        font-weight: bold; 
        text-align: center; 
        line-height: 1;
        margin-bottom: 20px;
        text-transform: uppercase;
    }
    .specs-20 { 
        font-size: 20px; 
        line-height: 1.3;
    }
    .price-box {
        text-align: center;
        border-top: 2px solid #ff0000;
        padding-top: 15px;
    }
    .p-label { font-size: 20px; font-weight: bold; color: #FF0000; }
    .p-value { font-size: 40px; font-weight: bold; color: #FF0000; }
    </style>
    """, unsafe_allow_html=True)

st.title("📱 Etichete Font 35/20")

if df.empty:
    st.error("Datele nu pot fi încărcate.")
else:
    cols = st.columns(3)
    phones_to_export = [None, None, None]
    prices_to_export = [0, 0, 0]

    for i, col in enumerate(cols):
        with col:
            brand_sel = st.selectbox(f"Brand {i+1}", ["-"] + sorted(df["Brand"].dropna().unique().tolist()), key=f"b_{i}")
            if brand_sel != "-":
                model_sel = st.selectbox(f"Model {i+1}", ["-"] + df[df["Brand"] == brand_sel]["Model"].dropna().tolist(), key=f"m_{i}")
                u_price = st.number_input(f"Pret lei {i+1}", min_value=0, key=f"p_{i}")
                
                if model_sel != "-":
                    raw_specs = df[(df["Brand"] == brand_sel) & (df["Model"] == model_sel)].iloc[0].to_dict()
                    phones_to_export[i] = raw_specs
                    prices_to_export[i] = u_price
                    
                    ordered_specs = get_specs_in_order(raw_specs, df.columns)
                    specs_html = "".join([f"• {v}<br>" for k, v in list(ordered_specs.items())[:6]])
                    
                    st.markdown(f"""
                    <div class="big-label">
                        <div>
                            <div class="title-35">{brand_sel}<br>{model_sel}</div>
                            <div class="specs-20">{specs_html}</div>
                        </div>
                        <div class="price-box">
                            <span class="p-label">Pret:</span>
                            <span class="p-value">{u_price}</span>
                            <span class="p-label">lei</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.divider()
    if any(phones_to_export):
        if st.button("🔴 DESCARCĂ PDF FONT MARE"):
            pdf_data = create_pdf(phones_to_export, prices_to_export, df.columns)
            st.download_button(label="📥 Salvează PDF", data=pdf_data, file_name="etichete_mari.pdf", mime="application/pdf")
