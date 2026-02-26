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
    """Extrage specificațiile respectând ordinea coloanelor din tabel."""
    clean = {}
    for col in original_columns:
        if col not in ["Brand", "Model"]:
            val = row_dict.get(col)
            if pd.notnull(val) and str(val).strip() not in ["", "0", "nan", "None", "NaN"]:
                clean[col] = str(val).strip()
    return clean

# --- FUNCȚIE GENERARE PDF (45x72mm) ---
def create_pdf(selected_phones_list, prices, original_columns):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    margin_left = 20
    gutter = 6           
    label_width = 45     
    label_height = 72    
    
    for i, phone in enumerate(selected_phones_list):
        if phone:
            specs = get_specs_in_order(phone, original_columns)
            brand_model = f"{phone.get('Brand', '')} {phone.get('Model', '')}".upper()
            price_val = str(prices[i])
            
            current_x = margin_left + (i * (label_width + gutter))
            current_y = 25
            
            # 1. Chenar Roșu
            pdf.set_draw_color(255, 0, 0)
            pdf.set_line_width(0.5)
            pdf.rect(current_x, current_y, label_width, label_height)
            
            # 2. Titlu (Poziționat la începutul etichetei după eliminarea logoului)
            pdf.set_y(current_y + 4)
            pdf.set_x(current_x)
            pdf.set_font("Arial", "B", 8.5)
            pdf.multi_cell(label_width, 3.5, txt=brand_model, align='C')
            
            # 3. Specificații (Respectă ordinea din Google Sheets)
            pdf.set_font("Arial", "", 6.5)
            pdf.set_y(current_y + 14)
            
            lines_shown = 0
            for key, val in specs.items():
                if lines_shown < 10:
                    pdf.set_x(current_x + 3)
                    pdf.multi_cell(label_width - 6, 3, txt=f"{key}: {val}", align='L')
                    lines_shown += 1
            
            # 4. Zona Preț
            pdf.set_text_color(255, 0, 0)
            pdf.set_y(current_y + label_height - 14)
            pdf.set_x(current_x)
            
            pdf.set_font("Arial", "B", 9) 
            pdf.cell(10, 8, txt="Pret:", ln=False, align='R')
            pdf.set_font("Arial", "B", 17) 
            pdf.cell(24, 8, txt=price_val, ln=False, align='C')
            pdf.set_font("Arial", "B", 9) 
            pdf.cell(8, 8, txt="lei", ln=True, align='L')
            
            pdf.set_text_color(0, 0, 0)
            
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INTERFAȚĂ STREAMLIT ---
st.set_page_config(page_title="Etichete 45x72mm", layout="wide")

st.title("📱 Generator Etichete Slim (Fără Logo)")

if df.empty:
    st.error("Nu s-au putut încărca datele.")
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
                    specs_html = "".join([f"• {k}: {v}<br>" for k, v in list(ordered_specs.items())[:10]])
                    
                    st.markdown(f"""
                    <div style="border: 2px solid #FF0000; padding: 10px; border-radius: 8px; background: white; min-height: 320px;">
                        <h6 style="text-align:center; color: black; margin-bottom: 10px;">{brand_sel} {model_sel}</h6>
                        <div style="font-size: 11px; color: #333;">{specs_html}</div>
                        <div style="text-align: center; border-top: 1px solid #ff0000; margin-top: 15px; padding-top: 10px;">
                            <span style="font-size: 24px; color: #FF0000; font-weight: bold;">{u_price} lei</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.divider()

    if any(phones_to_export):
        if st.button("🔴 DESCARCĂ PDF"):
            pdf_data = create_pdf(phones_to_export, prices_to_export, df.columns)
            st.download_button(label="📥 Salvează PDF", data=pdf_data, file_name="etichete_slim.pdf", mime="application/pdf")
