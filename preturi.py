import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests
from io import BytesIO
from PIL import Image, ImageOps

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

# --- PROCESARE LOGO (Inversare culori pentru PDF) ---
def get_black_logo(uploaded_file):
    img = Image.open(uploaded_file).convert("RGBA")
    # Dacă logoul e alb pe fundal negru, îl inversăm
    # Extragem masca de alfa pentru a păstra transparența dacă există
    r, g, b, a = img.split()
    rgb_img = Image.merge('RGB', (r, g, b))
    inverted_img = ImageOps.invert(rgb_img)
    # Recombinăm cu alfa
    final_img = Image.merge('RGBA', (inverted_img.split()[0], inverted_img.split()[1], inverted_img.split()[2], a))
    
    buf = BytesIO()
    final_img.save(buf, format="PNG")
    return buf

# --- FUNCȚIE GENERARE PDF (45x72mm cu Logo) ---
def create_pdf(selected_phones_list, prices, original_columns, logo_bytes=None):
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
            
            # 1. Frame Roșu
            pdf.set_draw_color(255, 0, 0)
            pdf.set_line_width(0.5)
            pdf.rect(current_x, current_y, label_width, label_height)
            
            # 2. Logo (Negru)
            if logo_bytes:
                # Plasăm logoul la începutul etichetei
                pdf.image(logo_bytes, x=current_x + 7.5, y=current_y + 2, w=30)
            
            # 3. Titlu (Sub logo)
            pdf.set_y(current_y + 12)
            pdf.set_x(current_x)
            pdf.set_font("Arial", "B", 8)
            pdf.multi_cell(label_width, 3.2, txt=brand_model, align='C')
            
            # 4. Specificații
            pdf.set_font("Arial", "", 6)
            pdf.set_y(current_y + 20)
            lines_shown = 0
            for key, val in specs.items():
                if lines_shown < 8:
                    pdf.set_x(current_x + 2)
                    pdf.multi_cell(label_width - 4, 2.7, txt=f"{key}: {val}", align='L')
                    lines_shown += 1
            
            # 5. Rubrica Preț
            pdf.set_text_color(255, 0, 0)
            pdf.set_y(current_y + label_height - 13)
            pdf.set_x(current_x)
            
            pdf.set_font("Arial", "B", 9) 
            pdf.cell(10, 8, txt="Pret:", ln=False, align='R')
            pdf.set_font("Arial", "B", 16) 
            pdf.cell(24, 8, txt=price_val, ln=False, align='C')
            pdf.set_font("Arial", "B", 9) 
            pdf.cell(8, 8, txt="lei", ln=True, align='L')
            
            pdf.set_text_color(0, 0, 0)
            
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INTERFAȚĂ STREAMLIT ---
st.set_page_config(page_title="Generator Etichete Express Credit", layout="wide")

# CSS pentru previzualizarea logoului negru
st.markdown("""
    <style>
    .slim-label {
        border: 2px solid #FF0000;
        border-radius: 8px;
        padding: 5px;
        background-color: white;
        min-height: 350px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .logo-placeholder { text-align: center; margin-bottom: 5px; font-weight: bold; color: black; }
    .specs-slim { font-size: 10px; line-height: 1.1; }
    .price-slim { text-align: center; border-top: 1px solid #ff0000; padding-top: 5px; }
    .p20 { font-size: 15px; font-weight: bold; color: #FF0000; }
    .p40 { font-size: 30px; font-weight: bold; color: #FF0000; }
    </style>
    """, unsafe_allow_html=True)

st.title("📱 Generator Etichete cu Logo (Express Credit)")

# Încărcare Logo
logo_file = st.file_uploader("Încarcă logoul (logo.png)", type=["png", "jpg"])
processed_logo = None
if logo_file:
    processed_logo = get_black_logo(logo_file)

if df.empty:
    st.error("Eroare date.")
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
                    specs_html = "".join([f"• {k}: {v}<br>" for k, v in list(ordered_specs.items())[:8]])
                    
                    st.markdown(f"""
                    <div class="slim-label">
                        <div class="logo-placeholder">EXPRESS CREDIT AMANET</div>
                        <div class="specs-slim">
                            <h6 style="text-align:center; margin:2px 0;">{brand_sel} {model_sel}</h6>
                            {specs_html}
                        </div>
                        <div class="price-slim">
                            <span class="p20">Pret:</span>
                            <span class="p40">{u_price}</span>
                            <span class="p20">lei</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.divider()
    if any(phones_to_export) and logo_file:
        if st.button("🔴 GENEREAZĂ PDF FINAL"):
            pdf_data = create_pdf(phones_to_export, prices_to_export, df.columns, processed_logo)
            st.download_button(label="📥 Salvează PDF", data=pdf_data, file_name="etichete_cu_logo.pdf", mime="application/pdf")
    elif not logo_file:
        st.warning("Vă rugăm să încărcați logoul pentru a activa descărcarea PDF-ului.")
