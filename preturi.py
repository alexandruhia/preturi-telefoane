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

def get_specs_in_order(row_dict, original_columns, battery_override=None):
    clean = {}
    battery_col_found = False
    for col in original_columns:
        if col in ["Brand", "Model"]: continue
        is_battery_col = col.lower() in ["sanatate baterie", "sănătate baterie", "baterie", "battery"]
        if is_battery_col:
            battery_col_found = True
            if battery_override: clean["Baterie"] = f"{battery_override}%"
            continue
        val = row_dict.get(col)
        if pd.notnull(val) and str(val).strip() not in ["", "0", "nan", "None", "NaN"]:
            clean[col] = str(val).strip()
    if not battery_col_found and battery_override:
        clean["Baterie"] = f"{battery_override}%"
    return clean

# --- FUNCȚIE GENERARE PDF (ULTRA SLIM 35x72mm) ---
def create_pdf(selected_phones_list, prices, ag_values, battery_values, original_columns):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    margin_left = 15
    gutter = 4           
    label_width = 35     # Îngustată la 35mm
    label_height = 72    
    
    for i, phone in enumerate(selected_phones_list):
        if phone:
            specs = get_specs_in_order(phone, original_columns, battery_values[i])
            brand_model = f"{phone.get('Brand', '')} {phone.get('Model', '')}".upper()
            price_val = str(prices[i])
            
            current_x = margin_left + (i * (label_width + gutter))
            current_y = 20
            
            # Chenar Roșu
            pdf.set_draw_color(255, 0, 0)
            pdf.set_line_width(0.4)
            pdf.rect(current_x, current_y, label_width, label_height)
            
            # Titlu Model (Bold)
            pdf.set_y(current_y + 3)
            pdf.set_x(current_x + 1)
            pdf.set_font("Arial", "B", 7.5)
            pdf.multi_cell(label_width - 2, 3, txt=brand_model, align='C')
            
            # Specificații (Bold: Italic)
            pdf.set_y(current_y + 12)
            lines_shown = 0
            for key, val in specs.items():
                if lines_shown < 11:
                    clean_key = key.replace('ă','a').replace('ș','s').replace('ț','t').replace('â','a').replace('î','i')
                    clean_val = str(val).replace('ă','a').replace('ș','s').replace('ț','t').replace('â','a').replace('î','i')
                    
                    pdf.set_x(current_x + 2)
                    pdf.set_font("Arial", "B", 6) # Bold pentru coloană
                    pdf.write(3, f"{clean_key}: ")
                    pdf.set_font("Arial", "I", 6) # Italic pentru detaliu
                    pdf.write(3, f"{clean_val}")
                    pdf.ln(3.2)
                    lines_shown += 1
            
            # Preț (Mai compact)
            pdf.set_text_color(255, 0, 0)
            pdf.set_y(current_y + label_height - 14)
            pdf.set_x(current_x)
            pdf.set_font("Arial", "B", 7) 
            pdf.cell(8, 7, txt="Pret:", align='R')
            pdf.set_font("Arial", "B", 14) 
            pdf.cell(18, 7, txt=price_val, align='C')
            pdf.set_font("Arial", "B", 7) 
            pdf.cell(5, 7, txt="lei", ln=True, align='L')
            
            # Cod AG sub preț
            pdf.set_text_color(0, 0, 0)
            if ag_values[i]:
                pdf.set_font("Arial", "", 5)
                pdf.set_y(current_y + label_height - 5)
                pdf.set_x(current_x)
                pdf.cell(label_width, 4, txt=f"B32451@{ag_values[i]}", align='C')
            
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INTERFAȚĂ STREAMLIT ---
st.set_page_config(page_title="Etichete Ultra Slim 35x72", layout="wide")
st.title("📱 Generator Etichete 35mm (Slim)")

if df.empty:
    st.error("Nu s-au putut încărca datele.")
else:
    cols = st.columns(3)
    phones_to_export, prices_to_export, ag_to_export, battery_to_export = [None]*3, [0]*3, [None]*3, [None]*3

    for i, col in enumerate(cols):
        with col:
            brand_sel = st.selectbox(f"Brand {i+1}", ["-"] + sorted(df["Brand"].dropna().unique().tolist()), key=f"b_{i}")
            if brand_sel != "-":
                model_sel = st.selectbox(f"Model {i+1}", ["-"] + df[df["Brand"] == brand_sel]["Model"].dropna().tolist(), key=f"m_{i}")
                u_price = st.number_input(f"Preț {i+1}", min_value=0, key=f"p_{i}")
                ag_number = st.selectbox(f"Cod AG {i+1}", list(range(1, 56)), key=f"ag_{i}")
                battery_percent = st.number_input(f"Baterie % {i+1}", 1, 100, 100, key=f"bat_{i}")

                if model_sel != "-":
                    raw_specs = df[(df["Brand"] == brand_sel) & (df["Model"] == model_sel)].iloc[0].to_dict()
                    phones_to_export[i] = raw_specs
                    prices_to_export[i] = u_price
                    ag_to_export[i] = ag_number
                    battery_to_export[i] = battery_percent
                    
                    ordered_specs = get_specs_in_order(raw_specs, df.columns, battery_percent)
                    specs_html = "".join([f"<b>{k}:</b> <i>{v}</i><br>" for k, v in list(ordered_specs.items())[:11]])
                    
                    # Previzualizare vizuală la 35mm (aprox 190px în browser)
                    st.markdown(f"""
                    <div style="border: 2px solid #FF0000; padding: 8px; border-radius: 4px; background: white; width: 190px; margin: auto; font-family: Arial;">
                        <div style="text-align:center; font-weight: bold; font-size: 12px; margin-bottom: 8px; text-transform: uppercase;">
                            {brand_sel} {model_sel}
                        </div>
                        <div style="font-size: 10px; color: #222; line-height: 1.1; min-height: 200px;">
                            {specs_html}
                        </div>
                        <div style="text-align: center; border-top: 1px solid #ff0000; margin-top: 8px; padding-top: 5px;">
                            <span style="font-size: 18px; color: #FF0000; font-weight: bold;">{u_price} lei</span>
                            <div style="font-size:8px; color: gray;">B32451@{ag_number}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.divider()
    if any(phones_to_export):
        st.download_button(
            label="🔴 DESCARCĂ PDF ULTRA-SLIM (35x72mm)",
            data=create_pdf(phones_to_export, prices_to_export, ag_to_export, battery_to_export, df.columns),
            file_name="etichete_35mm.pdf",
            mime="application/pdf"
        )
