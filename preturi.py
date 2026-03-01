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

# Funcție pentru a curăța textul de caractere care crapă PDF-ul (latin-1)
def clean_for_pdf(text):
    if not text: return ""
    # Înlocuim diacriticele cunoscute
    replacements = {
        'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't',
        'Ă': 'A', 'Â': 'A', 'Î': 'I', 'Ș': 'S', 'Ț': 'T'
    }
    t = str(text)
    for k, v in replacements.items():
        t = t.replace(k, v)
    # Eliminăm orice alt caracter care nu este în setul latin-1 standard
    return t.encode('latin-1', 'replace').decode('latin-1')

def get_specs_in_order(row_dict, original_columns, battery_override=None, accessories_list=None):
    clean = {}
    cap_bat_col = None
    for col in original_columns:
        if "capacitate baterie" in col.lower():
            cap_bat_col = col
            break

    for col in original_columns:
        if col in ["Brand", "Model"]: continue
        if col.lower() in ["sanatate baterie", "sănătate baterie", "baterie", "battery"]: continue

        val = row_dict.get(col)
        if pd.notnull(val) and str(val).strip() not in ["", "0", "nan", "None", "NaN"]:
            clean[col] = str(val).strip()
            if col == cap_bat_col:
                if battery_override: clean["Sănătate baterie"] = f"{battery_override}%"
                if accessories_list: clean["Accesorii"] = ", ".join(accessories_list)

    if battery_override and "Sănătate baterie" not in clean:
        temp = {"Sănătate baterie": f"{battery_override}%"}
        if accessories_list: temp["Accesorii"] = ", ".join(accessories_list)
        temp.update(clean)
        return temp
    return clean

# --- FUNCȚIE GENERARE PDF (REPARATĂ) ---
def create_pdf(selected_phones_list, prices, full_codes, battery_values, acc_values, original_columns):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    margin_left, gutter, label_width, label_height = 15, 5, 40, 60
    
    for i, phone in enumerate(selected_phones_list):
        if phone:
            specs = get_specs_in_order(phone, original_columns, battery_values[i], acc_values[i])
            brand_model = f"{phone.get('Brand', '')} {phone.get('Model', '')}".upper()
            price_val = str(prices[i])
            current_x = margin_left + (i * (label_width + gutter))
            current_y = 25
            
            pdf.set_draw_color(255, 0, 0)
            pdf.set_line_width(0.4)
            pdf.rect(current_x, current_y, label_width, label_height)
            
            # Titlu
            pdf.set_y(current_y + 3)
            pdf.set_x(current_x)
            pdf.set_font("Arial", "B", 8)
            pdf.multi_cell(label_width, 3.5, txt=clean_for_pdf(brand_model), align='C')
            
            # Specificații
            pdf.set_y(current_y + 11)
            lines_shown = 0
            for key, val in specs.items():
                if lines_shown < 9:
                    pdf.set_x(current_x + 2)
                    pdf.set_font("Arial", "B", 6.8)
                    pdf.write(3.2, f"{clean_for_pdf(key)}: ") 
                    pdf.set_font("Arial", "I", 6.8)
                    pdf.write(3.2, clean_for_pdf(val))    
                    pdf.ln(3.4) 
                    lines_shown += 1
            
            # Preț
            pdf.set_text_color(255, 0, 0)
            pdf.set_y(current_y + label_height - 12.5)
            pdf.set_x(current_x)
            pdf.set_font("Arial", "B", 8) 
            pdf.cell(10, 7, txt="Pret:", align='R')
            pdf.set_font("Arial", "B", 15) 
            pdf.cell(18, 7, txt=price_val, align='C')
            pdf.set_font("Arial", "B", 8) 
            pdf.cell(6, 7, txt="lei", ln=True, align='L')
            
            # Bon
            pdf.set_text_color(0, 0, 0)
            if full_codes[i]:
                pdf.set_font("Arial", "", 5.5)
                pdf.set_y(current_y + label_height - 4.5)
                pdf.set_x(current_x)
                pdf.cell(label_width, 3, txt=clean_for_pdf(full_codes[i]), align='C')
    
    # PDF output în mod 'S' (string/bytes)
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAȚĂ STREAMLIT ---
st.set_page_config(page_title="Etichete 40x60 Pro", layout="wide")
st.title("📱 Generator Etichete 40x60mm")

if df.empty:
    st.error("Eroare la baza de date.")
else:
    cols = st.columns(3)
    phones_to_export, prices_to_export, codes_to_export, battery_to_export, acc_to_export = [None]*3, [0]*3, [None]*3, [None]*3, [None]*3

    for i, col in enumerate(cols):
        with col:
            brand_sel = st.selectbox(f"Brand {i+1}", ["-"] + sorted(df["Brand"].dropna().unique().tolist()), key=f"b_{i}")
            if brand_sel != "-":
                model_sel = st.selectbox(f"Model {i+1}", ["-"] + df[df["Brand"] == brand_sel]["Model"].dropna().tolist(), key=f"m_{i}")
                u_price = st.number_input(f"Preț lei {i+1}", min_value=0, key=f"p_{i}")
                
                st.write("**Bon consignație:**")
                c1, c2 = st.columns([2, 1])
                b_digits = c1.text_input("Cod B", value="32451", key=f"b_dig_{i}", label_visibility="collapsed")
                ag_val = c2.selectbox("AG", list(range(1, 56)), index=28, key=f"ag_val_{i}", label_visibility="collapsed")
                full_code = f"B{b_digits}@{ag_val}"
                
                battery_percent = st.number_input(f"Sănătate baterie (%) {i+1}", 1, 100, 100, key=f"bat_{i}")
                
                st.write("**Accesorii:**")
                acc_options = ["husă", "fără încărcător", "cutie", "cablu încărcare", "încărcător"]
                selected_acc = [opt for idx, opt in enumerate(acc_options) if st.checkbox(opt, key=f"acc_{i}_{idx}")]

                if model_sel != "-":
                    raw_specs = df[(df["Brand"] == brand_sel) & (df["Model"] == model_sel)].iloc[0].to_dict()
                    phones_to_export[i], prices_to_export[i], codes_to_export[i], battery_to_export[i], acc_to_export[i] = raw_specs, u_price, full_code, battery_percent, selected_acc
                    
                    ordered_specs = get_specs_in_order(raw_specs, df.columns, battery_percent, selected_acc)
                    specs_html = "".join([f"<b>{k}:</b> <i>{v}</i><br>" for k, v in list(ordered_specs.items())[:9]])
                    
                    st.markdown(f"""
                    <div style="border: 2px solid #FF0000; padding: 10px; border-radius: 5px; background: white; width: 220px; height: 335px; margin: auto; font-family: Arial;">
                        <h6 style="text-align:center; color: black; margin-bottom: 8px; font-weight: bold; font-size: 13px; text-transform: uppercase;">{brand_sel} {model_sel}</h6>
                        <div style="font-size: 11.5px; color: #333; line-height: 1.3; height: 185px; overflow: hidden;">{specs_html}</div>
                        <div style="text-align: center; border-top: 1px solid #ff0000; margin-top: 10px; padding-top: 5px;">
                            <span style="font-size: 19px; color: #FF0000; font-weight: bold;">{u_price} lei</span>
                            <div style="font-size:8.5px; color: gray; margin-top: 2px;">{full_code}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)

    st.divider()
    if any(phones_to_export):
        try:
            pdf_out = create_pdf(phones_to_export, prices_to_export, codes_to_export, battery_to_export, acc_to_export, df.columns)
            st.download_button(label="🔴 DESCARCĂ PDF", data=pdf_out, file_name="etichete.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"Eroare PDF: {e}")
