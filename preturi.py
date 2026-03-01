import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests
from io import BytesIO

# --- CONFIGURARE ȘI ÎNCĂRCARE DATE ---
SHEET_ID = '1QnRcdnDRx7UoOhrnnVI5as39g0HFEt0wf0kGY8u-IvA'
URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'
# Adresa RAW pentru a putea citi imaginea în PDF
LOGO_URL = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"

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
    replacements = {'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't', 'Ă': 'A', 'Â': 'A', 'Î': 'I', 'Ș': 'S', 'Ț': 'T'}
    t = str(text)
    for k, v in replacements.items():
        t = t.replace(k, v)
    return t.encode('latin-1', 'replace').decode('latin-1')

def get_specs_in_order(row_dict, original_columns, battery_override=None, accessories_list=None, stocare_val=None, ram_val=None):
    clean = {}
    proc_found = False
    skip_cols = ["brand", "model", "stocare", "ram", "sanatate baterie", "sănătate baterie", "baterie", "battery", "storage"]

    for col in original_columns:
        col_lower = col.lower()
        if col_lower in skip_cols: continue
        val = row_dict.get(col)
        if pd.notnull(val) and str(val).strip() not in ["", "0", "nan", "None", "NaN"]:
            clean[col] = str(val).strip()
            if "procesor" in col_lower:
                if stocare_val and stocare_val != "-": clean["Stocare"] = stocare_val
                if ram_val and ram_val != "-": clean["RAM"] = ram_val
                proc_found = True
            if "capacitate baterie" in col_lower and battery_override:
                clean["Sănătate baterie"] = f"{battery_override}%"

    if not proc_found:
        final_clean = {}
        if stocare_val and stocare_val != "-": final_clean["Stocare"] = stocare_val
        if ram_val and ram_val != "-": final_clean["RAM"] = ram_val
        final_clean.update(clean)
        clean = final_clean

    if battery_override and "Sănătate baterie" not in clean:
        clean["Sănătate baterie"] = f"{battery_override}%"
    if accessories_list:
        clean["Accesorii"] = ", ".join(accessories_list)
    return clean

# --- FUNCȚIE GENERARE PDF CU FOOTER ROȘU + LOGO ---
def create_pdf(selected_phones_list, prices, full_codes, battery_values, acc_values, stocare_values, ram_values, original_columns):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    margin_left, gutter, label_width, label_height = 15, 5, 40, 60
    
    logo_img = None
    try:
        response = requests.get(LOGO_URL)
        if response.status_code == 200:
            logo_img = BytesIO(response.content)
    except:
        pass

    for i, phone in enumerate(selected_phones_list):
        if phone:
            specs = get_specs_in_order(phone, original_columns, battery_values[i], acc_values[i], stocare_values[i], ram_values[i])
            brand_model = f"{phone.get('Brand', '')} {phone.get('Model', '')}".upper()
            current_x = margin_left + (i * (label_width + gutter))
            current_y = 25
            
            # 1. Desenare Chenar și Titlu
            pdf.set_draw_color(255, 0, 0)
            pdf.set_line_width(0.4)
            pdf.rect(current_x, current_y, label_width, label_height)
            
            pdf.set_y(current_y + 2.5)
            pdf.set_x(current_x)
            pdf.set_font("Arial", "B", 9.5)
            pdf.multi_cell(label_width, 3.8, txt=clean_for_pdf(brand_model), align='C')
            
            # 2. Specificații
            start_specs_y = current_y + 11.5
            pdf.set_y(start_specs_y)
            display_items = list(specs.items())[:10]
            line_step = 3.3
            for key, val in display_items:
                pdf.set_x(current_x + 2)
                pdf.set_font("Arial", "B", 6.8)
                pdf.write(line_step, f"{clean_for_pdf(key)}: ") 
                pdf.set_font("Arial", "I", 6.8)
                v_str = clean_for_pdf(val)
                pdf.write(line_step, v_str if len(v_str) < 28 else v_str[:25] + "...")    
                pdf.ln(line_step)
            
            # 3. Bloc Preț și Cod (Compact)
            end_specs_y = start_specs_y + (len(display_items) * line_step)
            pdf.line(current_x + 5, end_specs_y + 1, current_x + label_width - 5, end_specs_y + 1)
            
            pdf.set_text_color(255, 0, 0)
            pdf.set_y(end_specs_y + 1.5)
            pdf.set_x(current_x)
            pdf.set_font("Arial", "B", 16) 
            pdf.cell(label_width, 7, txt=f"{prices[i]} lei", align='C', ln=True)
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", "", 5.5)
            pdf.set_x(current_x)
            pdf.cell(label_width, 2.5, txt=clean_for_pdf(full_codes[i]), align='C')

            # 4. FRAME ROȘU (FOOTER) CU LOGO
            footer_h = 9.5
            # Umplem fundalul cu roșu la baza etichetei
            pdf.set_fill_color(255, 0, 0)
            pdf.rect(current_x + 0.1, current_y + label_height - footer_h - 0.1, label_width - 0.2, footer_h, 'F')
            
            if logo_img:
                # Plasăm logo-ul peste banda roșie
                # x centrat, y în banda de footer, w scalat la 32mm pentru vizibilitate
                pdf.image(logo_img, x=current_x + 4, y=current_y + label_height - footer_h + 1.2, w=32)
            
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAȚĂ STREAMLIT ---
st.set_page_config(page_title="Etichete ExpressCredit", layout="wide")
st.title("📱 Generator Etichete Smartphone")

if df.empty:
    st.error("Eroare la baza de date.")
else:
    cols = st.columns(3)
    p_exp, pr_exp, c_exp, b_exp, a_exp, s_exp, r_exp = [None]*3, [0]*3, [None]*3, [None]*3, [None]*3, [None]*3, [None]*3

    for i, col in enumerate(cols):
        with col:
            brand_sel = st.selectbox(f"Brand {i+1}", ["-"] + sorted(df["Brand"].dropna().unique().tolist()), key=f"b_{i}")
            
            st.write("**Memorie:**")
            cm1, cm2 = st.columns(2)
            stoc_list = ["-", "2 GB", "4 GB", "8 GB", "16 GB", "32 GB", "64 GB", "128 GB", "256 GB", "512 GB", "1 TB"]
            ram_list = ["-", "1 GB", "2 GB", "3 GB", "4 GB", "6 GB", "8 GB", "12 GB", "16 GB", "20 GB", "24 GB"]
            s_val = cm1.selectbox(f"Stocare {i+1}", stoc_list, key=f"stoc_{i}")
            r_val = cm2.selectbox(f"RAM {i+1}", ram_list, key=f"ram_{i}")
            
            if brand_sel != "-":
                model_sel = st.selectbox(f"Model {i+1}", ["-"] + df[df["Brand"] == brand_sel]["Model"].dropna().tolist(), key=f"m_{i}")
                u_price = st.number_input(f"Preț lei {i+1}", min_value=0, key=f"p_{i}")
                
                cb1, cb2 = st.columns([2, 1])
                b_digits = cb1.text_input("Cod B", value="32451", key=f"b_dig_{i}")
                ag_val = cb2.selectbox("AG", list(range(1, 56)), index=28, key=f"ag_val_{i}")
                
                battery_percent = st.number_input(f"Sănătate baterie (%) {i+1}", 1, 100, 100, key=f"bat_{i}")
                
                st.write("**Accesorii:**")
                acc_options = ["husă", "fără încărcător", "cutie", "cablu încărcare", "încărcător"]
                selected_acc = [opt for idx, opt in enumerate(acc_options) if st.checkbox(opt, key=f"acc_{i}_{idx}")]

                if model_sel != "-":
                    raw_specs = df[(df["Brand"] == brand_sel) & (df["Model"] == model_sel)].iloc[0].to_dict()
                    p_exp[i], pr_exp[i], c_exp[i], b_exp[i], a_exp[i] = raw_specs, u_price, f"B{b_digits}@{ag_val}", battery_percent, selected_acc
                    s_exp[i], r_exp[i] = s_val, r_val
                    
                    ordered_specs = get_specs_in_order(raw_specs, df.columns, battery_percent, selected_acc, s_val, r_val)
                    specs_html = "".join([f"<b>{k}:</b> <i>{v}</i><br>" for k, v in list(ordered_specs.items())[:10]])
                    
                    st.markdown(f"""
                    <div style="border: 2px solid #FF0000; border-radius: 5px; background: white; width: 220px; min-height: 280px; margin: auto; font-family: Arial; overflow: hidden;">
                        <div style="padding: 10px;">
                            <h5 style="text-align:center; color: black; margin-bottom: 5px; font-weight: bold; font-size: 15px; text-transform: uppercase;">{brand_sel} {model_sel}</h5>
                            <div style="font-size: 10.8px; color: #333; line-height: 1.35;">{specs_html}</div>
                            <div style="text-align: center; border-top: 1.5px solid #ff0000; margin-top: 8px; padding-top: 5px;">
                                <span style="font-size: 22px; color: #FF0000; font-weight: bold;">{u_price} lei</span>
                                <div style="font-size:8.5px; color: gray;">B{b_digits}@{ag_val}</div>
                            </div>
                        </div>
                        <div style="background-color: #FF0000; height: 38px; display: flex; align-items: center; justify-content: center; padding: 5px;">
                             <img src="{LOGO_URL}" style="width: 160px;">
                        </div>
                    </div>""", unsafe_allow_html=True)

    st.divider()
    if any(p_exp):
        pdf_out = create_pdf(p_exp, pr_exp, c_exp, b_exp, a_exp, s_exp, r_exp, df.columns)
        st.download_button(label="🔴 DESCARCĂ PDF FINAL", data=pdf_out, file_name="etichete_expresscredit.pdf", mime="application/pdf")
