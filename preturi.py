import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO
from PIL import Image, ImageOps
import requests

# --- CONFIGURARE DATE ȘI LOGO GITHUB ---
SHEET_ID = '1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA'
DATA_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'
# Înlocuiește 'utilizator', 'repo' și 'cale/catre/logo.png' cu datele tale reale de GitHub
LOGO_GITHUB_URL = "https://raw.githubusercontent.com/utilizator/repo/main/logo.png"

@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(DATA_URL)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Eroare la citirea tabelului: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_and_process_logo(url):
    """Descarcă logoul de pe GitHub și îl transformă în negru pe transparent/alb."""
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content)).convert("RGBA")
        
        # Inversăm culorile pentru a transforma albul în negru
        r, g, b, a = img.split()
        rgb_img = Image.merge('RGB', (r, g, b))
        inverted_rgb = ImageOps.invert(rgb_img)
        
        # Recombinăm cu canalul alfa (transparența)
        final_img = Image.merge('RGBA', (inverted_rgb.split()[0], inverted_rgb.split()[1], inverted_rgb.split()[2], a))
        
        buf = BytesIO()
        final_img.save(buf, format="PNG")
        buf.seek(0)
        return buf
    except Exception as e:
        st.error(f"Nu s-a putut încărca logoul din GitHub: {e}")
        return None

df = load_data()
logo_processed = fetch_and_process_logo(LOGO_GITHUB_URL)

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
            
            # 2. Logo din GitHub (Poziționat sus)
            if logo_data:
                # Imaginea este deja procesată ca fiind neagră
                pdf.image(logo_data, x=current_x + 5, y=current_y + 4, w=35)
            
            # 3. Titlu
            pdf.set_y(current_y + 14)
            pdf.set_x(current_x)
            pdf.set_font("Arial", "B", 8)
            pdf.multi_cell(label_width, 3.5, txt=brand_model, align='C')
            
            # 4. Specificații
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

st.title("📱 Generator Etichete Express Credit (GitHub Logo)")

if df.empty:
    st.error("Datele nu sunt disponibile.")
else:
    cols = st.columns(3)
    phones_to_export = [None, None, None]
    prices_to_export = [0, 0, 0]

    for i, col in enumerate(cols):
        with col:
            brand_sel = st.selectbox(f"Brand {i+1}", ["-"] + sorted(df["Brand"].dropna().unique().tolist()), key=f"b_{i}")
            if brand_sel != "-":
                model_sel = st.selectbox(f"Model {i+1}", ["-"] + df[df["Brand"] == brand_sel]["Model"].dropna().tolist(), key=f"m_{i}")
                u_price = st.number_input(f"Preț lei", min_value=0, key=f"p_{i}")
                
                if model_sel != "-":
                    raw_specs = df[(df["Brand"] == brand_sel) & (df["Model"] == model_sel)].iloc[0].to_dict()
                    phones_to_export[i] = raw_specs
                    prices_to_export[i] = u_price
                    
                    ordered_specs = get_specs_in_order(raw_specs, df.columns)
                    specs_prev = "".join([f"• {k}: {v}<br>" for k, v in list(ordered_specs.items())[:8]])
                    
                    st.markdown(f"""
                    <div style="border: 2px solid #FF0000; padding: 10px; border-radius: 8px; background: white; text-align: center;">
                        <img src="{LOGO_GITHUB_URL}" style="width: 100px; filter: invert(1); margin-bottom: 5px;">
                        <h6 style="margin: 0;">{brand_sel} {model_sel}</h6>
                        <div style="text-align: left; font-size: 10px; color: #444; margin-top: 5px;">{specs_prev}</div>
                        <div style="margin-top: 10px; border-top: 1px solid #ff0000; padding-top: 5px;">
                            <span style="color: #FF0000; font-weight: bold; font-size: 22px;">{u_price} lei</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.divider()

    if any(phones_to_export):
        if st.button("🔴 GENEREAZĂ PDF FINAL"):
            if logo_processed:
                pdf_data = create_pdf(phones_to_export, prices_to_export, df.columns, logo_processed)
                st.download_button(label="📥 Descarcă Etichete", data=pdf_data, file_name="etichete_express_github.pdf", mime="application/pdf")
            else:
                st.error("Logoul nu a putut fi procesat. Verifică URL-ul GitHub.")
