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

def get_specs_in_order(row_dict, original_columns, battery_override=None, accessories_list=None):
    clean = {}
    cap_bat_col = None
    
    # Căutăm coloana de Capacitate Baterie pentru poziționare
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
            
            # Inserăm Sănătate și Accesorii imediat după Capacitate Baterie
            if col == cap_bat_col:
                if battery_override:
                    clean["Sănătate baterie"] = f"{battery_override}%"
                if accessories_list:
                    clean["Accesorii"] = ", ".join(accessories_list)

    # Siguranță: dacă nu a găsit coloana Capacitate Baterie, le punem la început
    if battery_override and "Sănătate baterie" not in clean:
        temp = {"Sănătate baterie": f"{battery_override}%"}
        if accessories_list:
            temp["Accesorii"] = ", ".join(accessories_list)
        temp.update(clean)
        return temp
        
    return clean

# --- FUNCȚIE GENERARE PDF (40x60mm) ---
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
            
            # Chenar
            pdf.set_draw_color(255, 0, 0)
            pdf.set_line_width(0.4)
            pdf.rect(current_x, current_y, label_width, label_height)
            
            # Titlu Model
            pdf.set_y(current_y + 3)
            pdf.set_x(current_x)
            pdf.set_font("Arial", "B", 8)
            pdf.multi_cell(label_width, 3.5, txt=brand_model, align='C')
            
            # Specificații (Mix Bold/Italic)
            pdf.set_y(current_y + 11)
            lines_shown = 0
            font_size_specs = 6.8
            for key, val in specs.items():
                if lines_shown < 9:
                    # Curățare diacritice pentru PDF standard
                    ck = key.replace('ă','a').replace('ș','s').replace('ț','t').replace('â','a').replace('î','i')
                    cv = str(val).replace('ă','a').replace('ș','s').replace('ț','t').replace('â','a').replace('î','i')
                    
                    pdf.set_x(current_x + 2)
                    pdf.set_font("Arial", "B", font_size_specs)
                    pdf.write(3.2, f"{ck}: ") 
                    pdf.set_font("Arial", "I", font_size_specs)
                    # multi_cell nu merge bine cu write, așa că folosim o logică de tăiere dacă textul e prea lung la accesorii
                    display_val = cv if len(cv) < 30 else cv[:27] + "..."
                    pdf.write(3.2, display_val)    
                    pdf.ln(3.4) 
                    lines_shown += 1
            
            # Zonă Preț
            pdf.set_text_color(255, 0, 0)
            pdf.set_y(current_y + label_height - 12.5)
            pdf.set_x(current_x)
            pdf.set_font("Arial", "B", 8) 
            pdf.cell(10, 7, txt="Preț:", align='R')
            pdf.set_font("Arial", "B", 15) 
            pdf.cell(18, 7, txt=price_val, align='C')
            pdf.set_font("Arial", "B", 8) 
            pdf.cell(6, 7, txt="lei", ln=True, align='L')
            
            # Bon Consignație (B... @ AG...)
            pdf.set_text_color(0, 0, 0)
            if full_codes[i]:
                pdf.set_font("Arial", "", 5.5)
                pdf.set_y(current_y + label_height - 4.5)
                pdf.set_x(current_x)
                pdf.cell(label_width, 3, txt=full_codes[i], align='C')
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INTERFAȚĂ STREAMLIT ---
st.set_page_config(page_title="Etichete 40x60 Pro", layout="wide")
st.title("📱 Generator Etichete 40x60mm")

if df.empty:
    st.error("Eroare la încărcarea bazei de date.")
else:
    cols = st.columns(3)
    phones_to_export, prices_to_export, codes_to_export, battery_to_export, acc_to_export = [None]*3, [0]*3, [None]*3, [None]*3, [None]*3

    for i, col in enumerate(cols):
        with col:
            brand_sel = st.selectbox(f"Brand {i+1}", ["-"] + sorted(df["Brand"].dropna().unique().tolist()), key=f"b_{i}")
            if brand_sel != "-":
                model_sel = st.selectbox(f"Model {i+1}", ["-"] + df[df["Brand"] == brand_sel]["Model"].dropna().tolist(), key=f"m_{i}")
                u_price = st.number_input(f"Preț (lei) {i+1}", min_value=0, key=f"p_{i}")
                
                # Bon Consignație
                st.write("**Bon consignație:**")
                c1, c2 = st.columns([2, 1])
                b_digits = c1.text_input("Cod B", value="32451", key=f"b_dig_{i}", label_visibility="collapsed")
                ag_val = c2.selectbox("AG", list(range(1, 56)), index=28, key=f"ag_val_{i}", label_visibility="collapsed")
                full_code = f"B{b_digits}@{ag_val}"
                
                battery_percent = st.number_input(f"Sănătate baterie (%) {i+1}", 1, 100, 100, key=f"bat_{i}")
                
                # Accesorii cu diacritice
                st.write("**Accesorii:**")
                acc_options = ["husă", "fără încărcător", "cutie", "cablu încărcare", "încărcător"]
                selected_acc = []
                acc_grid = st.columns(2)
                for idx, opt in enumerate(acc_options):
                    if acc_grid[idx % 2].checkbox(opt, key=f"acc_{i}_{idx}"):
                        selected_acc.append(opt)

                if model_sel != "-":
                    raw_specs = df[(df["Brand"] == brand_sel) & (df["Model"] == model_sel)].iloc[0].to_dict()
                    phones_to_export[i] = raw_specs
                    prices_to_export[i] = u_price
                    codes_to_export[i] = full_code
                    battery_to_export[i] = battery_percent
                    acc_to_export[i] = selected_acc
                    
                    ordered_specs = get_specs_in_order(raw_specs, df.columns, battery_percent, selected_acc)
                    specs_html = "".join([f"<b>{k}:</b> <i>{v}</i><br>" for k, v in list(ordered_specs.items())[:9]])
                    
                    # Preview Card
                    st.markdown(f"""
                    <div style="border: 2px solid #FF0000; padding: 10px; border-radius: 5px; background: white; width: 220px; height: 335px; margin: auto; font-family: Arial;">
                        <h6 style="text-align:center; color: black; margin-bottom: 8px; font-weight: bold; font-size: 13px; text-transform: uppercase;">
                            {brand_sel} {model_sel}
                        </h6>
                        <div style="font-size: 11.5px; color: #333; line-height: 1.3; height: 185px; overflow: hidden;">
                            {specs_html}
                        </div>
                        <div style="text-align: center; border-top: 1px solid #ff0000; margin-top: 10px; padding-top: 5px;">
                            <span style="font-size: 19px; color: #FF0000; font-weight: bold;">{u_price} lei</span>
                            <div style="font-size:8.5px; color: gray; margin-top: 2px;">{full_code}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.divider()
    if any(phones_to_export):
        pdf_bytes = create_pdf(phones_to_export, prices_to_export, codes_to_export, battery_to_export, acc_to_export, df.columns)
        st.download_button(
            label="🔴 DESCARCĂ PDF ETICHETE",
            data=pdf_bytes,
            file_name="etichete_40x60_accesorii.pdf",
            mime="application/pdf"
        )
