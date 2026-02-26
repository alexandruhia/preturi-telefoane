import streamlit as st
import pandas as pd
from fpdf import FPDF
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

def process_logo_to_black(uploaded_file):
    """Transformă logoul alb-pe-negru în negru-pe-alb/transparent."""
    img = Image.open(uploaded_file).convert("RGBA")
    # Separăm canalele
    r, g, b, a = img.split()
    rgb_img = Image.merge('RGB', (r, g, b))
    # Inversăm culorile (albul devine negru)
    inverted_rgb = ImageOps.invert(rgb_img)
    # Recombinăm cu canalul alfa original
    final_img = Image.merge('RGBA', (inverted_rgb.split()[0], inverted_rgb.split()[1], inverted_rgb.split()[2], a))
    
    buf = BytesIO()
    final_img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# --- FUNCȚIE GENERARE PDF (45x72mm cu Logo Negru) ---
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
            
            # 1. Frame Roșu
            pdf.set_draw_color(255, 0, 0)
            pdf.set_line_width(0.5)
            pdf.rect(current_x, current_y, label_width, label_height)
            
            # 2. Logo procesat (Negru)
            if logo_data:
                # Centrare logo: lățime 35mm într-un cadru de 45mm
                pdf.image(logo_data, x=current_x + 5, y=current_y + 3, w=35)
            
            # 3. Titlu (Poziționat sub logo)
            pdf.set_y(current_y + 13)
            pdf.set_x(current_x)
            pdf.set_font("Arial", "B", 8)
            pdf.multi_cell(label_width, 3.2, txt=brand_model, align='C')
            
            # 4. Specificații
            pdf.set_font("Arial", "", 6)
            pdf.set_y(current_y + 22)
            lines_shown = 0
            for key, val in specs.items():
                if lines_shown < 8:
                    pdf.set_x(current_x + 2)
                    pdf.multi_cell(label_width - 4, 2.7, txt=f"{key}: {val}", align='L')
                    lines_shown += 1
            
            # 5. Rubrica Preț
            pdf.set_text_color(255, 0, 0)
            pdf.set_y(current_y + label_height - 14)
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
st.set_page_config(page_title="Etichete Express Credit", layout="wide")

st.title("📱 Generator Etichete Slim (45x72mm)")

# Widget încărcare logo
uploaded_logo = st.file_uploader("Încarcă logoul original (cel negru cu scris alb)", type=["png", "jpg", "jpeg"])

if df.empty:
    st.error("Nu s-au putut încărca datele din tabel.")
else:
    cols = st.columns(3)
    phones_to_export = [None, None, None]
    prices_to_export = [0, 0, 0]

    for i, col in enumerate(cols):
        with col:
            st.subheader(f"Telefon {i+1}")
            brand_sel = st.selectbox(f"Brand", ["-"] + sorted(df["Brand"].dropna().unique().tolist()), key=f"b_{i}")
            
            if brand_sel != "-":
                model_sel = st.selectbox(f"Model", ["-"] + df[df["Brand"] == brand_sel]["Model"].dropna().tolist(), key=f"m_{i}")
                u_price = st.number_input(f"Preț lei", min_value=0, key=f"p_{i}")
                
                if model_sel != "-":
                    raw_specs = df[(df["Brand"] == brand_sel) & (df["Model"] == model_sel)].iloc[0].to_dict()
                    phones_to_export[i] = raw_specs
                    prices_to_export[i] = u_price
                    
                    ordered_specs = get_specs_in_order(raw_specs, df.columns)
                    specs_html = "".join([f"• {k}: {v}<br>" for k, v in list(ordered_specs.items())[:8]])
                    
                    # Previzualizare stilizată
                    st.markdown(f"""
                    <div style="border: 2px solid #FF0000; padding: 10px; border-radius: 8px; background: white; min-height: 350px;">
                        <div style="text-align: center; color: black; font-weight: bold; margin-bottom: 10px;">LOGO BLACK VERSION</div>
                        <div style="font-size: 10px; color: #333;">
                            <h6 style="text-align:center; color: black; margin-bottom: 5px;">{brand_sel} {model_sel}</h6>
                            {specs_html}
                        </div>
                        <div style="text-align: center; border-top: 1px solid #ff0000; margin-top: 10px; padding-top: 5px;">
                            <span style="font-size: 14px; color: #FF0000; font-weight: bold;">Pret:</span>
                            <span style="font-size: 28px; color: #FF0000; font-weight: bold;">{u_price}</span>
                            <span style="font-size: 14px; color: #FF0000; font-weight: bold;">lei</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.divider()

    if any(phones_to_export):
        if uploaded_logo:
            if st.button("🔴 DESCARCĂ PDF CU LOGO"):
                black_logo = process_logo_to_black(uploaded_logo)
                pdf_data = create_pdf(phones_to_export, prices_to_export, df.columns, black_logo)
                st.download_button(label="📥 Salvează PDF", data=pdf_data, file_name="etichete_express_credit.pdf", mime="application/pdf")
        else:
            st.info("ℹ️ Încarcă logoul în partea de sus pentru a activa descărcarea PDF-ului.")
