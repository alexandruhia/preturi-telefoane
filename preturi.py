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

# --- FUNCȚIE GENERARE PDF (REDUSE CU ÎNCĂ 20%) ---
def create_pdf(selected_phones_list, prices):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # Parametri noi (Reduși cu 20% față de versiunea anterioară)
    margin_left = 15
    gutter = 8           
    label_width = 50     # Redus de la 62mm
    label_height = 72    # Redus de la 90mm
    
    for i, phone in enumerate(selected_phones_list):
        if phone:
            specs = get_clean_specs(phone)
            brand_model = f"{phone.get('Brand', '')} {phone.get('Model', '')}".upper()
            price_val = str(prices[i])
            
            current_x = margin_left + (i * (label_width + gutter))
            current_y = 25
            
            # 1. Frame Roșu
            pdf.set_draw_color(255, 0, 0)
            pdf.set_line_width(0.6)
            pdf.rect(current_x, current_y, label_width, label_height)
            
            # 2. Titlu (Font micșorat)
            pdf.set_y(current_y + 3)
            pdf.set_x(current_x)
            pdf.set_font("Arial", "B", 8)
            pdf.multi_cell(label_width, 3.5, txt=brand_model, align='C')
            
            # 3. Specificații (Font foarte mic pentru a încăpea în 72mm)
            pdf.set_font("Arial", "", 6.5)
            pdf.set_y(current_y + 11)
            lines_shown = 0
