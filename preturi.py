# --- FUNCȚIE GENERARE ETICHETĂ CENTRATĂ ---
def creeaza_imagine_eticheta(row, font_size, line_spacing, l_scale, l_x_manual, l_y):
    W, H = 800, 1200
    rosu_express = (204, 9, 21)
    albastru_text = (0, 51, 102)
    img = Image.new('RGB', (W, H), color=rosu_express)
    draw = ImageDraw.Draw(img)
    margine = 40
    draw.rounded_rectangle([margine, margine, W-margine, H-220], radius=60, fill="white")

    try:
        f_path_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        f_path_reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        f_titlu = ImageFont.truetype(f_path_bold, int(font_size * 1.2))
        f_bold = ImageFont.truetype(f_path_bold, font_size)
        f_normal = ImageFont.truetype(f_path_reg, font_size)
    except:
        f_titlu = f_bold = f_normal = ImageFont.load_default()

    # --- CENTRARE TITLU ---
    text_titlu1 = "FISA TEHNICA:"
    text_titlu2 = f"{row['Brand']} {row['Model']}"
    
    # Calculăm lățimea pentru a centra
    w_t1 = draw.textlength(text_titlu1, font=f_titlu)
    w_t2 = draw.textlength(text_titlu2, font=f_titlu)
    
    draw.text(((W - w_t1) // 2, margine * 2.5), text_titlu1, fill=albastru_text, font=f_titlu)
    draw.text(((W - w_t2) // 2, margine * 2.5 + 65), text_titlu2, fill=albastru_text, font=f_titlu)

    # --- SPECIFICAȚII (Aliniate la stânga în interiorul cardului, dar centrate ca bloc) ---
    y_pos = margine * 6.5
    specs = [
        "Display", "OS", "Procesor", "Stocare", "RAM", 
        "Camera principala", "Selfie", "Sanatate baterie", "Capacitate baterie"
    ]
    
    for col in specs:
        if col in row.index:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            # Păstrăm specificațiile aliniate la un offset fix pentru lizibilitate
            draw.text((margine * 2.5, y_pos), f"{col}:", fill="black", font=f_bold)
            offset = draw.textlength(f"{col}: ", font=f_bold)
            draw.text((margine * 2.5 + offset, y_pos), val, fill="black", font=f_normal)
            y_pos += line_spacing

    # --- CENTRARE LOGO ---
    try:
        url_logo = "https://raw.githubusercontent.com/alexandruhia/preturi-telefoane/main/logo.png"
        logo_res = requests.get(url_logo)
        logo = Image.open(io.BytesIO(logo_res.content)).convert("RGBA")
        
        lw = int(W * l_scale)
        lh = int(lw * (logo.size[1] / logo.size[0]))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        
        # Dacă l_x_manual este 0 (default), centrăm automat. 
        # Altfel, folosim valoarea din slider.
        if l_x_manual == 100: # Valoarea ta default din cod
            x_logo = (W - lw) // 2
        else:
            x_logo = l_x_manual
            
        img.paste(logo, (x_logo, l_y), logo)
    except: pass
    return img
