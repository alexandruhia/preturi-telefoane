import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO
from PIL import Image, ImageOps
import requests

# --- CONFIGURARE ȘI ÎNCĂRCARE DATE ---
SHEET_ID = '1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA'
URL_DATA = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'

@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(URL_DATA)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Eroare la citirea tabelului: {e}")
        return pd.DataFrame()

df = load_data()

# --- PROCESARE LOGO ---
def get_processed_logo(img_input):
    """Transformă logoul alb-pe-negru în negru-pe-transparent."""
    img = Image.open(img_input).convert("RGBA")
    r, g, b, a = img.split()
    rgb_img = Image.merge('RGB', (r, g, b))
    # Inversăm culorile: albul devine negru
    inverted_img = ImageOps.invert(rgb_img)
    
    # Creăm un fundal alb (opțional) sau păstrăm transparența
    final_img = Image.merge('RGBA', (inverted_img.split()[0], inverted_img.split()[1], inverted_img.split()[2], a))
    
    buf = BytesIO()
    final_img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def get_specs_in_order(row_dict, original_columns):
    clean = {}
    for col in original_columns:
        if col not in ["Brand", "Model"]:
            val = row_dict.get(col)
            if pd.notnull(val) and str(val).strip() not in ["", "0", "nan", "None", "NaN"]:
                clean[col] = str(val).strip()
    return clean

# --- FUNCȚIE GENERARE PDF ---
def create_pdf(selected_phones_list, prices, original_columns, logo_data):
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
            
            # 2. Logo Negru (Poziționat sus)
            if logo_data:
                pdf.image(logo_data, x=current_x + 5, y=current_y + 4, w=35)
            
            # 3. Titlu Telefon
            pdf.set_y(current_y + 14)
            pdf.set_x(current_x)
            pdf.set_font("Arial", "B", 8)
            pdf.multi_cell(label_width, 3.5, txt=brand_model, align='C')
            
            # 4. Specificații (Ordine din tabel)
            pdf.set_font("Arial", "", 6.2)
            pdf.set_y(current_y + 23)
            lines_shown = 0
            for key, val in specs.items():
                if lines_shown < 8:
                    pdf.set_x(current_x + 3)
                    pdf.multi_cell(label_width - 6, 2.8, txt=f"{key}: {val}", align='L')
                    lines_shown += 1
            
            # 5. Zonă Preț
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
st.set_page_config(page_title="Express Credit Labels", layout="wide")

st.title("📱 Generator Etichete Express Credit Amanet")

# Slot pentru logo - Poți să-l încarci o singură dată aici
logo_file = st.sidebar.file_uploader("Încarcă Logo-ul (logo.png)", type=["png"])

if df.empty:
    st.error("Nu s-au găsit date.")
else:
    cols = st.columns(3)
    phones_to_export = [None, None, None]
    prices_to_export = [0, 0, 0]

    for i, col in enumerate(cols):
        with col:
            brand_sel = st.selectbox(f"Brand {i+1}", ["-"] + sorted(df["Brand"].dropna().unique().tolist()), key=f"b_{i}")
            if brand_sel != "-":
                model_sel = st.selectbox(f"Model", ["-"] + df[df["Brand"] == brand_sel]["Model"].dropna().tolist(), key=f"m_{i}")
                u_price = st.number_input(f"Preț lei", min_value=0, key=f"p_{i}")
                
                if model_sel != "-":
                    raw_specs = df[(df["Brand"] == brand_sel) & (df["Model"] == model_sel)].iloc[0].to_dict()
                    phones_to_export[i] = raw_specs
                    prices_to_export[i] = u_price
                    
                    ordered_specs = get_specs_in_order(raw_specs, df.columns)
                    specs_preview = "".join([f"• {k}: {v}<br>" for k, v in list(ordered_specs.items())[:8]])
                    
                    st.markdown(f"""
                    <div style="border: 2px solid #FF0000; padding: 10px; border-radius: 8px; background: white; text-align: center;">
                        <p style="color: black; font-weight: bold; margin-bottom: 5px;">LOGO AICI</p>
                        <h6 style="margin: 5px 0;">{brand_sel} {model_sel}</h6>
                        <div style="text-align: left; font-size: 10px; color: #444;">{specs_preview}</div>
                        <div style="margin-top: 10px; border-top: 1px solid #ff0000; padding-top: 5px;">
                            <span style="color: #FF0000; font-weight: bold; font-size: 24px;">{u_price} lei</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.divider()

    if any(phones_to_export) and logo_file:
        if st.button("🔴 GENEREAZĂ PDF FINAL"):
            processed_logo = get_processed_logo(logo_file)
            pdf_data = create_pdf(phones_to_export, prices_to_export, df.columns, processed_logo)
            st.download_button(label="📥 Descarcă Etichete", data=pdf_data, file_name="etichete_express.pdf", mime="application/pdf")
    elif not logo_file:
        st.info("Vă rugăm să încărcați logoul în bara laterală pentru a genera PDF-ul.")
