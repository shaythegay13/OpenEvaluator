#!/usr/bin/env python3
"""Phase 3: Professional soil profile table matching pinnacle example format."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def draw_soil_profile_grid(draw, x, y, w, h, data, title_font, header_font, normal_font):
    """Draw a professional soil profile grid table with columns and rows."""
    
    # Colors
    BLACK = (0, 0, 0)
    GRAY = (100, 100, 100)
    LIGHT_GRAY = (240, 240, 240)
    WHITE = (255, 255, 255)
    
    # Title
    draw.text((x + 15, y + 10), "SOIL PROFILE & OBSERVATION DATA", fill=BLACK, font=title_font)
    
    # Table header row
    header_y = y + 50
    col_widths = [90, 120, 150, 110, 80, 100]  # 670 total
    headers = ["DEPTH (in)", "COLOR", "TEXTURE", "CONSISTENCE", "STRUCTURE", "REDOX"]
    
    # Draw header background
    hx = x + 20
    for i, (hw, hd) in enumerate(zip(col_widths, headers)):
        draw.rectangle([(hx, header_y), (hx + hw, header_y + 30)],
                       outline=BLACK, width=1, fill=LIGHT_GRAY)
        draw.text((hx + 5, header_y + 5), hd, fill=BLACK, font=normal_font)
        hx += hw
    
    # Soil layers from data
    obs_holes = data.get("observation_holes", [])
    layers = []
    if obs_holes and len(obs_holes) > 0:
        layers = obs_holes[0].get("soil_layers", [])
    
    if not layers:
        # Default data from our test case
        layers = [
            {"depth_start_in": 0, "depth_end_in": 3, "color": "Brown", "texture": "Fine Sandy Loam",
             "consistence": "Friable", "structure": "Granular", "redox": "None"},
            {"depth_start_in": 3, "depth_end_in": 24, "color": "Yellowish Brown", "texture": "Fine Sandy Loam",
             "consistence": "Firm", "structure": "Sub-angular Blocky", "redox": "Few"},
            {"depth_start_in": 24, "depth_end_in": 36, "color": "Olive Gray", "texture": "Fine Sandy Loam",
             "consistence": "Firm", "structure": "Massive", "redox": "Common"},
        ]
    
    # Draw data rows
    row_y = header_y + 30
    for idx, layer in enumerate(layers):
        row_h = 28
        bg = WHITE if idx % 2 == 0 else (248, 248, 248)
        row_data = [
            f"{layer.get('depth_start_in', 0)}-{layer.get('depth_end_in', 0)}",
            layer.get("color", ""),
            layer.get("texture", ""),
            layer.get("consistence", ""),
            layer.get("structure", ""),
            layer.get("redox", ""),
        ]
        
        cx = x + 20
        for i, (cell, cw) in enumerate(zip(row_data, col_widths)):
            draw.rectangle([(cx, row_y), (cx + cw, row_y + row_h)],
                           outline=BLACK, width=1, fill=bg)
            if cell:
                draw.text((cx + 5, row_y + 5), cell, fill=GRAY, font=normal_font)
            cx += cw
        
        # Add observation hole label for first layer
        if idx == 0 and obs_holes:
            oh1_num = obs_holes[0].get("number", "OH-1")
            draw.text((x + 20, row_y - 18), f"OBSERVATION HOLE #{oh1_num}", fill=BLACK, font=normal_font)
        
        row_y += row_h
    
    # Bottom of table line
    table_bottom = row_y
    draw.line([(x + 20, table_bottom), (x + 20 + sum(col_widths), table_bottom)], fill=BLACK, width=2)
    
    # Limiting factor / water table info
    lf_y = table_bottom + 15
    limiting_factor = data.get("limiting_factor", 24) or "24"
    draw.text((x + 20, lf_y), 
              f"Limiting Factor: Ground Water @ {limiting_factor}\u201d    Depth to Limiting Factor: {limiting_factor}\u201d",
              fill=BLACK, font=normal_font)
    
    return table_bottom

def add_soil_profile_to_page3(page3_path, data, output_path=None):
    """Add a professional soil profile table to the page 3 consolidated image."""
    from pathlib import Path
    
    page_path = Path(page3_path) if not isinstance(page3_path, Path) else page3_path
    page = Image.open(page_path)
    draw = ImageDraw.Draw(page)
    
    # Load fonts
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        normal_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        title_font = header_font = normal_font = ImageFont.load_default()
    
    # Find the soil legend area on the page 
    # The existing page has a white box at approximately (630, 1030, 1070, 1380)
    # Replace this area with our improved table
    section_x, section_y = 630, 1050
    section_w, section_h = 420, 360
    
    # Clear the area with white
    draw.rectangle([(section_x, section_y), (section_x + section_w, section_y + section_h)],
                   fill=(255, 255, 255), outline=(0, 0, 0), width=2)
    
    # Draw improved soil profile table
    try:
        title_font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        header_font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
        normal_font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except:
        title_font_sm = header_font_sm = normal_font_sm = ImageFont.load_default()
    
    # Only draw the table portion that fits
    obs_holes = data.get("observation_holes", [])
    layers = []
    if obs_holes and len(obs_holes) > 0:
        layers = obs_holes[0].get("soil_layers", [])
    
    if not layers:
        layers = [
            {"depth_start_in": 0, "depth_end_in": 3, "color": "Brown", "texture": "Fine Sandy Loam",
             "consistence": "Friable", "redox": "None"},
            {"depth_start_in": 3, "depth_end_in": 24, "color": "Yellowish Brown", "texture": "Fine Sandy Loam",
             "consistence": "Firm", "redox": "Few"},
            {"depth_start_in": 24, "depth_end_in": 36, "color": "Olive Gray", "texture": "Fine Sandy Loam",
             "consistence": "Firm", "redox": "Common"},
        ]
    
    col_widths = [70, 100, 110, 80, 60]
    headers = ["DEPTH", "COLOR", "TEXTURE", "CONSIST.", "REDOX"]
    
    hx = section_x + 10
    hy = section_y + 40
    
    # Draw header row
    for i, (cw, hd) in enumerate(zip(col_widths, headers)):
        draw.rectangle([(hx, hy), (hx + cw, hy + 22)], outline=(0,0,0), width=1, fill=(220, 220, 220))
        draw.text((hx + 3, hy + 3), hd, fill=(0,0,0), font=header_font_sm)
        hx += cw
    
    # Data rows
    ry = hy + 22
    for idx, layer in enumerate(layers[:4]):  # Max 4 rows
        bg = (255, 255, 255) if idx % 2 == 0 else (245, 245, 245)
        row_data = [
            f"{layer.get('depth_start_in', 0)}-{layer.get('depth_end_in', 0)}\"",
            layer.get("color", ""),
            layer.get("texture", ""),
            layer.get("consistence", ""),
            layer.get("redox", ""),
        ]
        cx = section_x + 10
        for i, (cell, cw) in enumerate(zip(row_data, col_widths)):
            draw.rectangle([(cx, ry), (cx + cw, ry + 22)], outline=(0,0,0), width=1, fill=bg)
            if cell:
                draw.text((cx + 3, ry + 3), cell, fill=(80, 80, 80), font=normal_font_sm)
            cx += cw
        ry += 22
    
    # Limiting factor below table
    lf = data.get("limiting_factor", "24")
    draw.text((section_x + 10, ry + 5),
              f"Limiting Factor: Ground Water @ {lf}\u201d", fill=(0, 0, 0), font=normal_font_sm)
    
    out_path = output_path or page3_path
    page.save(out_path, quality=95)
    print(f"  ✓ Soil profile table added to {out_path}")
    return Path(out_path)

if __name__ == "__main__":
    import sys, json
    data_path = sys.argv[1] if len(sys.argv) > 1 else ""
    data = {}
    if data_path:
        with open(data_path) as f:
            data = json.load(f)
    add_soil_profile_to_page3("page3_consolidated.png", data)
