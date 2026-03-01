# --- FUNCȚIE GENERARE PDF CORECTATĂ ---
def create_pdf(selected_phones_list, prices, full_codes, battery_values, acc_values, stocare_values, ram_values, original_columns):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    margin_left, gutter, label_width, label_height = 15, 5, 40, 60
    
    logo_img = None
    try:
        response = requests.get(LOGO_URL)
        if response.status_code == 200:
            # Păstrăm datele în memorie
            logo_img = BytesIO(response.content)
    except:
        pass

    for i, phone in enumerate(selected_phones_list):
        if phone:
            specs = get_specs_in_order(phone, original_columns, battery_values[i], acc_values[i], stocare_values[i], ram_values[i])
            brand_model = f"{phone.get('Brand', '')} {phone.get('Model', '')}".upper()
            current_x = margin_left + (i * (label_width + gutter))
            current_y = 25
            
            # 1. Chenar și Titlu
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
            
            # 3. Bloc Preț și Cod
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

            # 4. FRAME ROȘU CU LOGO
            footer_h = 9.5
            pdf.set_fill_color(255, 0, 0)
            pdf.rect(current_x + 0.1, current_y + label_height - footer_h - 0.1, label_width - 0.2, footer_h, 'F')
            
            if logo_img:
                # REPARARE AICI: am adăugat type='PNG' pentru a evita eroarea
                # De asemenea, resetăm cursorul BytesIO la început pentru fiecare etichetă
                logo_img.seek(0)
                pdf.image(logo_img, x=current_x + 4, y=current_y + label_height - footer_h + 1.2, w=32, type='PNG')
            
    return pdf.output(dest='S').encode('latin-1')
