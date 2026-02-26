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

# --- FUNCȚIE GENERARE PDF ---
def create_pdf(selected_phones_list, prices):
    pdf = FPDF()
    pdf.add_page()
    
    for i, phone in enumerate(selected_phones_list):
        if phone:
            specs = get_clean_specs(phone)
            brand_model = f"{phone.get('Brand', '')} {phone.get('Model', '')}".upper()
            price_val = str(prices[i])
            
            start_y = pdf.get_y()
            num_lines = len([k for k in specs if k not in ["Brand", "Model"]])
            # Calculăm înălțimea pentru a include și zona de preț mare de jos
            frame_height = (num_lines * 7) + 45 
            
            # Frame Roșu
            pdf.set_draw_color(255, 0, 0)
            pdf.set_line_width(1)
            pdf.rect(10, start_y, 190, frame_height)
            
            # Titlu Model
            pdf.set_y(start_y + 5)
            pdf.set_x(15)
            pdf.set_font("Arial", "B", 14)
            pdf.cell(180, 8, txt=brand_model, ln=True, align='L')
            
            # Specificații
            pdf.set_font("Arial", "", 10)
            for key, value in specs.items():
                if key not in ["Brand", "Model"]:
                    pdf.set_x(15)
                    pdf.multi_cell(180, 6, txt=f"{key}: {value}")
            
            # RUBRICA PREȚ (Jos, Mijloc)
            pdf.set_y(start_y + frame_height - 25)
            pdf.set_text_color(255, 0, 0)
            
            # Calculăm poziționarea manuală pentru a simula dimensiuni diferite pe aceeași linie
            current_y = pdf.get_y()
            full_text_width = 80 # Aproximativ
            start_x = (210 - full_text_width) / 2
            
            pdf.set_x(start_x)
            pdf.set_font("Arial", "B", 20)
            pdf.cell(20, 15, txt="Pret: ", ln=False)
            
            pdf.set_font("Arial", "B", 40)
            pdf.cell(40, 15, txt=price_val, ln=False)
            
            pdf.set_font("Arial", "B", 20)
            pdf.cell(20, 15, txt=" lei", ln=True)
            
            pdf.set_text_color(0, 0, 0)
            pdf.ln(15) # Spațiu până la următorul telefon
            
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INTERFAȚĂ STREAMLIT ---
st.set_page_config(page_title="Oferte Telefoane", layout="wide")

# CSS pentru stilizarea prețului pe mijloc
st.markdown("""
    <style>
    .red-frame {
        border: 4px solid #FF0000;
        border-radius: 15px;
        padding: 20px;
        margin-top: 10px;
        background-color: #FFFFFF;
        min-height: 400px;
        display: flex;
        flex-direction: column;
    }
    .specs-container {
        flex-grow: 1;
    }
    .price-container {
        text-align: center;
        margin-top: 20px;
        border-top: 1px solid #eee;
        padding-top: 20px;
    }
    .label-price {
        color: #FF0000;
        font-size: 20px;
        font-weight: bold;
    }
    .value-price {
        color: #FF0000;
        font-size: 40px;
        font-weight: bold;
        margin: 0 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📱 Generator Oferte (Google Sheets)")

cols = st.columns(3)
phones_to_export = []
prices_to_export = []

for i, col in enumerate(cols):
    with col:
        st.subheader(f"Telefon {i+1}")
        brand_sel = st.selectbox(f"Brand", ["-"] + sorted(df["Brand"].dropna().unique().tolist()), key=f"b_{i}")
        
        if brand_sel != "-":
            model_sel = st.selectbox(f"Model", ["-"] + df[df["Brand"] == brand_sel]["Model"].dropna().tolist(), key=f"m_{i}")
            user_price = st.number_input(f"Pret lei", min_value=0, value=0, key=f"p_{i}")
            
            if model_sel != "-":
                raw_specs = df[(df["Brand"] == brand_sel) & (df["Model"] == model_sel)].iloc[0].to_dict()
                final_specs = get_clean_specs(raw_specs)
                phones_to_export.append(raw_specs)
                prices_to_export.append(user_price)
                
                # Construcție vizuală Frame
                specs_html = "".join([f"<b>{k}:</b> {v}<br>" for k, v in final_specs.items() if k not in ["Brand", "Model"]])
                
                html_card = f"""
                <div class="red-frame">
                    <div class="specs-container">
                        <h3>{brand_sel} {model_sel}</h3>
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

# --- BUTON EXPORT ---
valid_selection = [p for p in phones_to_export if p is not None]
if valid_selection:
    active_prices = [prices_to_export[i] for i, p in enumerate(phones_to_export) if p is not None]
    if st.button("🔴 GENEREAZĂ PDF FINAL"):
        pdf_data = create_pdf(valid_selection, active_prices)
        st.download_button(label="📥 Descarcă PDF", data=pdf_data, file_name="oferta.pdf", mime="application/pdf")
