#!/usr/bin/env python3
import json, os, sys
sys.path.insert(0, ".")
from sheet_parser import parse_sheet_row, RAW_ROW
# Import generators
#!/usr/bin/env python3
"""DXF Generator for HHE-200 drawings (Pages 3-4).
Creates AutoCAD 2004-compatible DXF files with proper layers, 
dimensions, hatches, and standard fonts."""

import json, math, os, re, sys
from pathlib import Path
from typing import Optional

import ezdxf
from ezdxf.enums import InsertUnits
from ezdxf.enums import TextEntityAlignment
from ezdxf.math import Vec2

OUT_DIR = Path(__file__).parent / "dxf_output"

# Standard AutoCAD fonts - NO Carlson survey fonts
HEADER_FONT = "arial.ttf"   # Title text
LABEL_FONT = "arial.ttf"    # Labels  
NOTE_FONT = "simplex.shx"   # Notes/dimensions
TITLE_FONT = "bold.shx"     # Bold titles

def _setup_doc(title: str) -> tuple:
    doc = ezdxf.new("AC1018")  # AutoCAD 2004 format
    doc.units = InsertUnits.Feet
    msp = doc.modelspace()
    
    # Layers
    for name, color, lw in [
        ("GRID", 8, 0.15),        # gray grid
        ("BOUNDARY", 7, 0.50),    # white boundary
        ("STRUCTURE", 4, 0.35),   # cyan structures
        ("TEXT", 7, 0.25),        # white text
        ("DIMENSION", 3, 0.20),   # green dimensions
        ("HATCH", 8, 0.15),       # gray hatch
        ("ROAD", 6, 0.30),        # magenta road
        ("WELL", 5, 0.30),        # blue well
    ]:
        doc.layers.add(name, color=color, lineweight=int(lw*100))
    
    return doc, msp

# ── Drawing helpers ─────────────────────────────────────────────────────────

def _grid(msp, x0, y0, cols, rows, cell_w, cell_h):
    for c in range(cols + 1):
        msp.add_line((x0 + c * cell_w, y0), (x0 + c * cell_w, y0 + rows * cell_h),
                     dxfattribs={"layer": "GRID"})
    for r in range(rows + 1):
        msp.add_line((x0, y0 + r * cell_h), (x0 + cols * cell_w, y0 + r * cell_h),
                     dxfattribs={"layer": "GRID"})

def _rect(msp, x, y, w, h, layer="STRUCTURE"):
    msp.add_lwpolyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)],
                       close=True, dxfattribs={"layer": layer})

def _txt(msp, text, x, y, size=0.5, alignment=TextEntityAlignment.LEFT, 
         layer="TEXT", font=LABEL_FONT):
    msp.add_text(text, dxfattribs={"layer": layer, "height": size, "style": font}
                ).set_placement((x, y), align=alignment)

# ═══════════════════════════════════════════════════════════════════════════════
# DRAWING 1 — Site Plan (Page 3)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_site_plan_dxf(data: dict, out_path=None) -> Path:
    out_path = out_path or OUT_DIR / "PG3.dxf"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    doc, msp = _setup_doc("SITE PLAN")
    
    # Layout: 16×30 grid, each cell = scale ft
    cell_w = 1.0
    cell_h = 1.0
    cols, rows = 16, 30
    grid_x, grid_y = 0.5, 0.5
    scale_val = float(data.get("scale_pg3", 80))
    ft_per_cell = scale_val / 6.0
    
    _grid(msp, grid_x, grid_y, cols, rows, cell_w, cell_h)
    
    # Road band (top)
    road_y = grid_y + rows - 1.5
    _rect(msp, grid_x, road_y, cols, 1.5, layer="ROAD")
    road_name = (data.get("road_name") or data.get("street_name") or "ROAD").upper()
    _txt(msp, road_name, grid_x + cols/2, road_y + 0.6, size=0.4,
         alignment=TextEntityAlignment.CENTER, layer="ROAD")
    
    # Lot boundary
    lot_x, lot_y = grid_x + 1, grid_y + 0.5
    lot_w, lot_h = cols - 2, 26
    _rect(msp, lot_x, lot_y, lot_w, lot_h, layer="BOUNDARY")
    
    # Map/Lot label
    tax_map = data.get("tax_map", data.get("map_number", ""))
    lot_no = data.get("lot_number", "")
    acres = float(data.get("acreage", 2.35))
    _txt(msp, f"MAP {tax_map}  LOT {lot_no}", lot_x + 0.1, lot_y + lot_h - 0.3, 
         size=0.25, layer="TEXT")
    _txt(msp, f"{acres:.2f} ACRES", lot_x + 0.1, lot_y + lot_h - 0.6,
         size=0.2, layer="TEXT")
    
    # House
    house_w = 1.5
    house_h = 1.0
    hx = lot_x + lot_w/2 - house_w/2
    hy = lot_y + lot_h - 3.0
    _rect(msp, hx, hy, house_w, house_h, layer="STRUCTURE")
    _txt(msp, "EXISTING\nHOUSE", hx + house_w/2, hy + house_h/2, size=0.3,
         alignment=TextEntityAlignment.CENTER, layer="TEXT")
    
    # Septic tank
    t_to_h = float(data.get("tank_to_house", 8)) / ft_per_cell
    tw, td = 0.7, 0.4
    tx = lot_x + lot_w/2 - tw/2
    ty = hy - t_to_h - td
    _rect(msp, tx, ty, tw, td, layer="STRUCTURE")
    tank_cap = data.get("tank_cap", "1000")
    _txt(msp, f"{tank_cap}G TANK", tx - 1.0, ty + td/2, size=0.2,
         alignment=TextEntityAlignment.RIGHT, layer="TEXT")
    
    # Distribution box
    dbs = 0.25
    db_to_t = float(data.get("dbox_to_tank", 5)) / ft_per_cell
    dx = lot_x + lot_w/2 - dbs/2
    dy = ty - db_to_t - dbs
    _rect(msp, dx, dy, dbs, dbs, layer="STRUCTURE")
    _txt(msp, "D-BOX", dx + dbs + 0.1, dy + dbs/2, size=0.2, layer="TEXT")
    
    # Disposal field (3 rows × 7 modules)
    num_rows = int(data.get("num_rows", 3))
    mods_per_row = int(data.get("mods_per_row", 7))
    mod_len = float(data.get("mod_len", 4.0)) / ft_per_cell
    mod_wid = float(data.get("mod_wid", 3.67)) / ft_per_cell
    
    cluster_w = num_rows * mod_wid + (num_rows - 1) * 0.15
    cluster_l = mods_per_row * mod_len + (mods_per_row - 1) * 0.15
    fx = lot_x + lot_w/2 - cluster_w/2
    fy = dy - 0.5 - cluster_l
    
    _rect(msp, fx, fy, cluster_w, cluster_l, layer="HATCH")
    for row_idx in range(num_rows):
        for mod_idx in range(mods_per_row):
            mx = fx + row_idx * (mod_wid + 0.15)
            my = fy + mod_idx * (mod_len + 0.15)
            _rect(msp, mx, my, mod_wid, mod_len, layer="STRUCTURE")
    
    brand = data.get("brand", "Eljen").upper()
    _txt(msp, f"{brand} {mods_per_row}×{num_rows} MODULES", 
         fx + cluster_w/2, fy - 0.3, size=0.2,
         alignment=TextEntityAlignment.CENTER, layer="TEXT")
    
    # Well (if data available)
    well_to_field = float(data.get("field_to_well", 100)) / ft_per_cell
    well_x = lot_x + lot_w + 0.5
    well_y = fy + cluster_l/2
    msp.add_circle((well_x, well_y), 0.25, dxfattribs={"layer": "WELL"})
    _txt(msp, "WELL", well_x + 0.3, well_y, size=0.2, layer="TEXT")
    _txt(msp, f"{data.get('field_to_well', 100)}' MIN.", 
         well_x + 0.3, well_y - 0.25, size=0.15, layer="DIMENSION")
    
    # North arrow
    nay = lot_y + 0.8
    msp.add_line((lot_x + lot_w - 0.8, nay), (lot_x + lot_w - 0.8, nay + 0.5),
                 dxfattribs={"layer": "BOUNDARY"})
    _txt(msp, "N", lot_x + lot_w - 0.8, nay + 0.6, size=0.2,
         alignment=TextEntityAlignment.CENTER, layer="TEXT")
    
    # Scale bar
    _txt(msp, f"SCALE: 1\" = {scale_val}'", grid_x + 0.2, grid_y + 0.2,
         size=0.2, layer="DIMENSION")
    
    # Header info
    owner = data.get("owner_name", "").upper()
    addr = data.get("address_line", "").upper()
    _txt(msp, f"{owner}  |  {addr}", grid_x + 0.2, grid_y + rows - 0.1,
         size=0.22, layer="TEXT")
    _txt(msp, "SITE PLAN", grid_x + cols - 0.2, grid_y + rows - 0.1,
         size=0.22, alignment=TextEntityAlignment.RIGHT, layer="TEXT")
    
    # SE info
    se_num = data.get("se_number", "")
    se_date = data.get("se_date", "")
    _txt(msp, f"SE #{se_num}  DATE: {se_date}", 
         grid_x + cols/2, grid_y + 0.2, size=0.18,
         alignment=TextEntityAlignment.CENTER, layer="DIMENSION")
    
    doc.saveas(str(out_path))
    print(f"  ✓ Site Plan DXF: {out_path}")
    return out_path

# ═══════════════════════════════════════════════════════════════════════════════
# DRAWING 2 — Disposal Plan (Page 4 top)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_disposal_plan_dxf(data: dict, out_path=None) -> Path:
    out_path = out_path or OUT_DIR / "PG4_disposal.dxf"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    doc, msp = _setup_doc("DISPOSAL PLAN")
    
    cell_w, cell_h = 1.0, 1.0
    cols, rows = 16, 30
    gx, gy = 0.5, 0.5
    _grid(msp, gx, gy, cols, rows, cell_w, cell_h)
    
    ft_per_cell = 3.67
    
    num_rows = int(data.get("num_rows", 3))
    mods_per_row = int(data.get("mods_per_row", 7))
    mod_len = float(data.get("mod_len", 4.0)) / ft_per_cell
    mod_wid = float(data.get("mod_wid", 3.67)) / ft_per_cell
    cluster_w = num_rows * mod_wid + (num_rows - 1) * 0.15
    cluster_l = mods_per_row * mod_len + (mods_per_row - 1) * 0.15
    
    cx = gx + cols / 2
    field_bot = 1.5
    field_x = cx - cluster_w / 2
    field_y = field_bot
    _rect(msp, field_x, field_y, cluster_w, cluster_l, layer="HATCH")
    
    for ri in range(num_rows):
        for mi in range(mods_per_row):
            mx = field_x + ri * (mod_wid + 0.15)
            my = field_y + mi * (mod_len + 0.15)
            _rect(msp, mx, my, mod_wid, mod_len, layer="STRUCTURE")
    
    brand = data.get("brand", "Eljen").upper()
    _txt(msp, f"{brand} {mods_per_row}×{num_rows} MODULES",
         cx, field_y - 0.3, size=0.2, alignment=TextEntityAlignment.CENTER, layer="TEXT")
    
    # D-box above field
    dbox_size = 0.3
    dbox_y = field_y + cluster_l + 0.5
    _rect(msp, cx - dbox_size/2, dbox_y, dbox_size, dbox_size, layer="STRUCTURE")
    _txt(msp, "D-BOX", cx + dbox_size/2 + 0.1, dbox_y + dbox_size/2, size=0.18, layer="TEXT")
    
    # Tank above d-box
    tw, td = 0.8, 0.4
    tank_y = dbox_y + dbox_size + 0.4
    _rect(msp, cx - tw/2, tank_y, tw, td, layer="STRUCTURE")
    tank_cap = data.get("tank_cap", "1000")
    _txt(msp, f"{tank_cap} GAL SEPTIC TANK", cx - tw/2 - 0.5, tank_y + td/2, 
         size=0.2, alignment=TextEntityAlignment.RIGHT, layer="TEXT")
    
    # House above tank
    hw, hh = 1.2, 0.8
    house_y = tank_y + td + 0.4
    house_x = cx - hw/2
    _rect(msp, house_x, house_y, hw, hh, layer="STRUCTURE")
    _txt(msp, "SINGLE FAMILY\nDWELLING", cx, house_y + hh/2, size=0.22,
         alignment=TextEntityAlignment.CENTER, layer="TEXT")
    
    # Pipes
    msp.add_line((cx, tank_y + td), (cx, dbox_y + dbox_size), 
                 dxfattribs={"layer": "DIMENSION"})
    msp.add_line((cx, house_y), (cx, tank_y + td),
                 dxfattribs={"layer": "DIMENSION"})
    _txt(msp, '4" PIPE', cx + 0.1, (tank_y + td + house_y) / 2, 
         size=0.15, layer="DIMENSION")
    
    # Header
    owner = data.get("owner_name", "").upper()
    _txt(msp, f"{owner}", gx + 0.2, gy + rows - 0.2, size=0.22, layer="TEXT")
    _txt(msp, "DISPOSAL PLAN", gx + cols - 0.2, gy + rows - 0.2, 
         size=0.22, alignment=TextEntityAlignment.RIGHT, layer="TEXT")
    
    doc.saveas(str(out_path))
    print(f"  ✓ Disposal Plan DXF: {out_path}")
    return out_path

# ═══════════════════════════════════════════════════════════════════════════════
# DRAWING 3 — Cross-Section (Page 4 bottom)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_cross_section_dxf(data: dict, out_path=None) -> Path:
    out_path = out_path or OUT_DIR / "PG4_cross_section.dxf"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    doc, msp = _setup_doc("CROSS-SECTION")
    
    cell_w, cell_h = 1.0, 1.0
    cols, rows = 16, 20
    gx, gy = 0.5, 0.5
    _grid(msp, gx, gy, cols, rows, cell_w, cell_h)
    
    cx = gx + cols / 2
    
    # Ground surface
    gs_y = gy + rows - 2
    msp.add_line((gx + 1, gs_y), (gx + cols - 1, gs_y), 
                 dxfattribs={"layer": "BOUNDARY"})
    _txt(msp, "GROUND SURFACE", cx, gs_y + 0.2, size=0.2,
         alignment=TextEntityAlignment.CENTER, layer="TEXT")
    
    # Loam/topsoil layer
    loam_top = gs_y
    loam_bot = gs_y - 0.3
    _rect(msp, gx + 1, loam_bot, cols - 2, 0.3, layer="HATCH")
    _txt(msp, "LOAM/TOPSOIL 6\" MIN.", cx, loam_bot - 0.15, size=0.18,
         alignment=TextEntityAlignment.CENTER, layer="TEXT")
    
    # Sand layer  
    sand_top = loam_bot
    sand_bot = sand_top - 1.0
    _rect(msp, gx + 2, sand_bot, cols - 4, 1.0, layer="HATCH")
    _txt(msp, "SPECIFIED SAND 18\" MIN.", cx, (sand_top + sand_bot) / 2, 
         size=0.18, alignment=TextEntityAlignment.CENTER, layer="TEXT")
    
    # Module row
    mod_top = sand_bot
    mod_bot = mod_top - 0.3
    mod_w = 5.0
    _rect(msp, cx - mod_w/2, mod_bot, mod_w, 0.3, layer="STRUCTURE")
    _txt(msp, "GSF-B43 MODULE", cx, (mod_top + mod_bot) / 2, size=0.18,
         alignment=TextEntityAlignment.CENTER, layer="TEXT")
    
    # Fill below module
    fill_top = mod_bot
    fill_bot = fill_top - 1.5
    _rect(msp, gx + 2, fill_bot, cols - 4, 1.5, layer="HATCH")
    _txt(msp, "CLEAN FILL", cx, (fill_top + fill_bot) / 2, size=0.18,
         alignment=TextEntityAlignment.CENTER, layer="TEXT")
    
    # Elevation labels
    fg = data.get("finished_grade_elevation", "0\"")
    tp = data.get("top_of_distribution_pipe_elevation", "-12\"")
    bf = data.get("bottom_of_disposal_field_elevation", "30\"")
    
    elev_x = gx + 0.5
    _txt(msp, "CONSTRUCTION ELEVATIONS:", elev_x, gy + rows - 0.5, 
         size=0.2, layer="DIMENSION")
    _txt(msp, f"FINISHED GRADE: {fg}", elev_x, gy + rows - 0.9, 
         size=0.18, layer="DIMENSION")
    _txt(msp, f"TOP OF PIPE: {tp}", elev_x, gy + rows - 1.2, 
         size=0.18, layer="DIMENSION")
    _txt(msp, f"BOTTOM OF FIELD: {bf}", elev_x, gy + rows - 1.5, 
         size=0.18, layer="DIMENSION")
    
    # Limiting factor
    lf_depth = data.get("limiting_factor", "24")
    _txt(msp, f"LIMITING FACTOR @ {lf_depth}\"", cx, fill_bot - 0.2,
         size=0.18, alignment=TextEntityAlignment.CENTER, layer="DIMENSION")
    
    # Title
    _txt(msp, "CROSS-SECTION: DISPOSAL FIELD INSTALLATION", cx, gy + rows - 0.2,
         size=0.22, alignment=TextEntityAlignment.CENTER, layer="TEXT")
    
    doc.saveas(str(out_path))
    print(f"  ✓ Cross-Section DXF: {out_path}")
    return out_path

# ═══════════════════════════════════════════════════════════════════════════════
# COMBINED GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

def generate_all_dxf(data: dict) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    
    for key, fn in [
        ("site_plan", generate_site_plan_dxf),
        ("disposal_plan", generate_disposal_plan_dxf),
        ("cross_section", generate_cross_section_dxf),
    ]:
        try:
            p = fn(data)
            results[key] = str(p)
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"  ✗ {key}: {e}")
    
    return results

if __name__ == "__main__":
    test = {
        "owner_name": "KRISTEN MARQUIS",
        "address_line": "17 ASPEN WAY, TURNER, ME 04282",
        "road_name": "ASPEN WAY",
        "street_name": "ASPEN WAY",
        "town": "TURNER",
        "tax_map": "26",
        "map_number": "26",
        "lot_number": "18",
        "acreage": 2.35,
        "tank_cap": "1000",
        "se_number": "338",
        "se_date": "03/01/2026",
        "evaluator_name": "GEORGE BOUCHLES",
        "num_rows": 3,
        "mods_per_row": 7,
        "mod_len": 4.0,
        "mod_wid": 3.67,
        "cluster_w": 11.0,
        "cluster_l": 28.0,
        "brand": "Eljen",
        "scale_pg3": 80,
        "field_to_well": 100,
        "field_to_house": 40,
        "tank_to_house": 8.0,
        "finished_grade_elevation": '0"',
        "top_of_distribution_pipe_elevation": '-12"',
        "bottom_of_disposal_field_elevation": '30"',
        "limiting_factor": 24,
    }
    results = generate_all_dxf(test)
    print(f"\n✓ Generated {len(results)} DXF files")
    for k, v in results.items():
        print(f"  {k}: {v}")
