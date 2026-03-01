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

def clean_for_pdf(text):
    if not text: return ""
    replacements = {
        'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't',
        'Ă': 'A', 'Â': 'A', 'Î': 'I', 'Ș': 'S', 'Ț': 'T'
    }
    t = str(text)
    for k, v in replacements.items():
        t = t.replace(k, v)
    return t.encode('latin-1', 'replace').decode('latin-1')

def get_specs_in_order(row_dict, original_columns, battery_override=None, accessories_list=None):
    clean = {}
    cap_bat_col = None
    
    for col in original_columns:
        if "capacitate baterie" in col.lower():
            cap_bat_col = col
            break

    # 1. Adăugăm restul specificațiilor (fără Baterie și Accesorii încă)
    for col in original_columns:
        if col in ["Brand", "Model"]: continue
        if col.lower() in ["sanatate baterie", "sănătate baterie", "baterie", "battery"]: continue

        val = row_dict.get(col)
        if pd.notnull(val) and str(val).strip() not in ["", "0", "nan", "None", "NaN"]:
            clean[col] = str(val).strip()
            
            # Inserăm Sănătate baterie imediat după Capacitate
            if col == cap_bat_col and battery_override:
                clean["Sănătate baterie"] = f"{battery_override}%"

    # 2. Siguranță: dacă Sănătate Baterie nu e în listă, o adăugăm (de regulă prima)
    if battery_override and "Sănătate baterie" not in clean:
        new_clean = {"Sănătate baterie": f"{battery_override}%"}
        new_clean.update(clean)
        clean = new_clean

    # 3. FORȚĂM ACCESORII SĂ FIE ULTIMA
    if accessories_list:
        # Dacă există deja în dicționar, o scoatem ca să o punem la final
        clean.pop("Accesorii", None) 
        clean["Accesorii"] = ", ".join(accessories_list)
        
    return clean

# --- FUNCȚIE GENERARE PDF (Limita 10 rânduri) ---
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
            
            pdf.set_y(current_y + 3)
            pdf.set_x(current_x)
            pdf.set_font("Arial", "B", 8)
            pdf.multi_cell(label_width, 3.2, txt=clean_for_pdf(brand_model), align='C')
            
            pdf.set_y(current_y + 10.5)
            # Luăm doar ultimele 10 dacă sunt prea multe, dar păstrăm ordinea
            items = list(specs.items())
            if len(items) > 10:
                # Ne asigurăm că Accesoriile rămân în listă dacă sunt la final
                display_items = items[:10]
            else:
                display_items = items

            lines_shown = 0
            font_size_specs = 6.8
            for key, val in display_items:
                pdf.set_x(current_x + 2)
                pdf.set_font("Arial", "B", font_size_specs)
                pdf.write(3.2, f"{clean_for_pdf(key)}: ") 
                pdf.set_font("Arial", "I", font_size_specs)
                
                raw_val = clean_for_pdf(val)
                display_val = raw_val if len(raw_val) < 28 else raw_val[:25] + "..."
                
                pdf.write(3.2, display_val)    
                pdf.ln(3.2)
                lines_shown += 1
            
            pdf.set_text_color(255, 0, 0)
            pdf.set_y(current_y + label_height - 12)
            pdf.set_x(current_x)
            pdf.set_font("Arial", "B", 8) 
            pdf.cell(10, 7, txt="Pret:", align='R')
            pdf.set_font("Arial", "B", 15) 
            pdf.cell(18, 7, txt=price_val, align='C')
            pdf.set_font("Arial", "B", 8) 
            pdf.cell(6, 7, txt="lei", ln=True, align='L')
            
            pdf.set_text_color(0, 0, 0)
            if full_codes[i]:
                pdf.set_font("Arial", "", 5.5)
                pdf.set_y(current_y + label_height - 4.5)
                pdf.set_x(current_x)
                pdf.cell(label_width, 3, txt=clean_for_pdf(full_codes[i]), align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAȚĂ STREAMLIT ---
st.set_page_config(page_title="Etichete 40x60 Pro", layout="wide")
st.title("📱 Generator Etichete (Accesorii la final)")

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
                
                c1, c2 = st.columns([2, 1])
                b_digits = c1.text_input(f"Bon consignație {i+1}", value="32451", key=f"b_dig_{i}")
                ag_val = c2.selectbox(f"AG {i+1}", list(range(1, 56)), index=28, key=f"ag_val_{i}")
                full_code = f"B{b_digits}@{ag_val}"
                
                battery_percent = st.number_input(f"Sănătate baterie (%) {i+1}", 1, 100, 100, key=f"bat_{i}")
                
                st.write("**Accesorii:**")
                acc_options = ["husă", "fără încărcător", "cutie", "cablu încărcare", "încărcător"]
                selected_acc = [opt for idx, opt in enumerate(acc_options) if st.checkbox(opt, key=f"acc_{i}_{idx}")]

                if model_sel != "-":
                    raw_specs = df[(df["Brand"] == brand_sel) & (df["Model"] == model_sel)].iloc[0].to_dict()
                    phones_to_export[i], prices_to_export[i], codes_to_export[i], battery_to_export[i], acc_to_export[i] = raw_specs, u_price, full_code, battery_percent, selected_acc
                    
                    ordered_specs = get_specs_in_order(raw_specs, df.columns, battery_percent, selected_acc)
                    specs_html = "".join([f"<b>{k}:</b> <i>{v}</i><br>" for k, v in list(ordered_specs.items())[:10]])
                    
                    st.markdown(f"""
                    <div style="border: 2px solid #FF0000; padding: 10px; border-radius: 5px; background: white; width: 220px; height: 335px; margin: auto; font-family: Arial;">
                        <h6 style="text-align:center; color: black; margin-bottom: 8px; font-weight: bold; font-size: 13px; text-transform: uppercase;">{brand_sel} {model_sel}</h6>
                        <div style="font-size: 11px; color: #333; line-height: 1.25; height: 185px; overflow: hidden;">{specs_html}</div>
                        <div style="text-align: center; border-top: 1px solid #ff0000; margin-top: 10px; padding-top: 5px;">
                            <span style="font-size: 19px; color: #FF0000; font-weight: bold;">{u_price} lei</span>
                            <div style="font-size:8.5px; color: gray; margin-top: 2px;">{full_code}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)

    st.divider()
    if any(phones_to_export):
        pdf_out = create_pdf(phones_to_export, prices_to_export, codes_to_export, battery_to_export, acc_to_export, df.columns)
        st.download_button(label="🔴 DESCARCĂ PDF", data=pdf_out, file_name="etichete_final.pdf", mime="application/pdf")
