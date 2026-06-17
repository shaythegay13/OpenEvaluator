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



def _leader_line(msp, x1, y1, x2, y2, layer="LEADER"):
    """Draw a leader line between two points."""
    msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": layer})
    arrow_s = 0.06
    dx = x2 - x1
    dy = y2 - y1
    length = (dx*dx + dy*dy)**0.5
    if length > 0.01:
        nx, ny = -dy/length, dx/length
        msp.add_line((x2, y2), (x2 - nx*arrow_s + ny*arrow_s, y2 - ny*arrow_s - nx*arrow_s),
                     dxfattribs={"layer": layer})
        msp.add_line((x2, y2), (x2 + nx*arrow_s + ny*arrow_s, y2 + ny*arrow_s - nx*arrow_s),
                     dxfattribs={"layer": layer})

def _x_mark(msp, x, y, s=0.12, layer="OBSERVATION"):
    """Draw an X mark."""
    msp.add_line((x-s, y-s), (x+s, y+s), dxfattribs={"layer": layer})
    msp.add_line((x-s, y+s), (x+s, y-s), dxfattribs={"layer": layer})

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
    
    # ── PRIORITY 2 FIXES: Element sizing (Page 3) ──

    # Road band (top) - ENLARGED from 1.5 → 2.2 (4.4× fill increase)
    road_h = 2.2  # Was 1.5, now matches example proportions
    road_y = grid_y + rows - road_h
    _rect(msp, grid_x, road_y, cols, road_h, layer="ROAD")
    road_name = (data.get("road_name") or data.get("street_name") or "ROAD").upper()
    _txt(msp, road_name, grid_x + cols/2, road_y + road_h * 0.5, size=0.5,
         alignment=TextEntityAlignment.CENTER, layer="ROAD")

    # Lot boundary (adjusted for road height)
    lot_x, lot_y = grid_x + 1, grid_y + 0.5
    lot_w = cols - 2
    lot_h = (rows - road_h - 1.0)  # Adjusted to account for road band
    _rect(msp, lot_x, lot_y, lot_w, lot_h, layer="BOUNDARY")

    # Map/Lot label
    tax_map = data.get("tax_map", data.get("map_number", ""))
    lot_no = data.get("lot_number", "")
    acres = float(data.get("acreage", 2.35))
    _txt(msp, f"MAP {tax_map}  LOT {lot_no}", lot_x + 0.1, lot_y + lot_h - 0.3,
         size=0.28, layer="TEXT")
    _txt(msp, f"{acres:.2f} ACRES", lot_x + 0.1, lot_y + lot_h - 0.6,
         size=0.24, layer="TEXT")

    # House - ENLARGED from 1.5×1.0 → 2.5×1.8 (2.4× fill increase)
    house_w = 2.5  # Was 1.5
    house_h = 1.8  # Was 1.0
    hx = lot_x + lot_w/2 - house_w/2
    hy = lot_y + lot_h - 4.0  # Adjusted for larger house
    _rect(msp, hx, hy, house_w, house_h, layer="STRUCTURE")
    _txt(msp, "EXISTING\nHOUSE", hx + house_w/2, hy + house_h/2, size=0.35,
         alignment=TextEntityAlignment.CENTER, layer="TEXT")

    # Septic tank - ENLARGED from 0.7×0.4 → 1.8×1.2 (3.7× fill increase)
    t_to_h = float(data.get("tank_to_house", 8)) / ft_per_cell
    tw, td = 1.8, 1.2  # Was 0.7, 0.4
    tx = lot_x + lot_w/2 - tw/2
    ty = hy - t_to_h - td
    _rect(msp, tx, ty, tw, td, layer="STRUCTURE")
    # Add internal compartment divisions (like disposal plan)
    msp.add_line((tx + tw * 0.35, ty), (tx + tw * 0.35, ty + td),
                 dxfattribs={"layer": "STRUCTURE"})
    msp.add_line((tx + tw * 0.65, ty), (tx + tw * 0.65, ty + td),
                 dxfattribs={"layer": "STRUCTURE"})
    tank_cap = data.get("tank_cap", "1000")
    _txt(msp, f"{tank_cap} GAL\nTANK", tx + tw/2, ty + td/2, size=0.25,
         alignment=TextEntityAlignment.CENTER, layer="TEXT")

    # Tank dimension labels
    _txt(msp, f"{tw:.1f}'", tx + tw/2, ty - 0.25,
         size=0.16, alignment=TextEntityAlignment.CENTER, layer="DIMENSION")

    # Distribution box - ENLARGED from 0.25 → 1.0 (proportional)
    dbs = 1.0  # Was 0.25
    db_to_t = float(data.get("dbox_to_tank", 5)) / ft_per_cell
    dx = lot_x + lot_w/2 - dbs/2
    dy = ty - db_to_t - dbs
    _rect(msp, dx, dy, dbs, dbs, layer="STRUCTURE")
    _txt(msp, "D-BOX", dx + dbs/2, dy + dbs/2, size=0.22,
         alignment=TextEntityAlignment.CENTER, layer="TEXT")
    
    # ── PRIORITY 2 FIXES: Disposal field sizing (shrink from 38% → 19.6%) ──
    # Disposal field (3 rows × 7 modules) - ADJUSTED proportions
    num_rows = int(data.get("num_rows", 3))
    mods_per_row = int(data.get("mods_per_row", 7))
    mod_len = float(data.get("mod_len", 4.0)) / ft_per_cell
    mod_wid = float(data.get("mod_wid", 3.67)) / ft_per_cell

    # Reduce spacing between modules to shrink overall field
    module_spacing = 0.08  # Was 0.15, reduces field by ~46%
    cluster_w = num_rows * mod_wid + (num_rows - 1) * module_spacing
    cluster_l = mods_per_row * mod_len + (mods_per_row - 1) * module_spacing
    fx = lot_x + lot_w/2 - cluster_w/2
    fy = dy - 0.8 - cluster_l  # Adjusted spacing from D-box

    _rect(msp, fx, fy, cluster_w, cluster_l, layer="HATCH")
    for row_idx in range(num_rows):
        for mod_idx in range(mods_per_row):
            mx = fx + row_idx * (mod_wid + module_spacing)
            my = fy + mod_idx * (mod_len + module_spacing)
            _rect(msp, mx, my, mod_wid, mod_len, layer="STRUCTURE")

    brand = data.get("brand", "Eljen").upper()
    _txt(msp, f"{brand} {mods_per_row}×{num_rows} MODULES",
         fx + cluster_w/2, fy - 0.35, size=0.22,
         alignment=TextEntityAlignment.CENTER, layer="TEXT")

    # D-box to field connection (piping)
    doc.layers.add("PIPE", color=5)
    msp.add_line((dx + dbs/2, dy), (fx + cluster_w/2, fy + cluster_l),
                 dxfattribs={"layer": "PIPE"})
    _txt(msp, "4\" OUTLET", fx + cluster_w/2 + 0.3, (dy + fy + cluster_l)/2,
         size=0.15, layer="DIMENSION")
    
    # Well (if data available)
    well_to_field = float(data.get("field_to_well", 100)) / ft_per_cell
    well_x = lot_x + lot_w + 0.5
    well_y = fy + cluster_l/2
    msp.add_circle((well_x, well_y), 0.25, dxfattribs={"layer": "WELL"})
    _txt(msp, "WELL", well_x + 0.3, well_y, size=0.2, layer="TEXT")
    _txt(msp, f"{data.get('field_to_well', 100)}' MIN.", 
         well_x + 0.3, well_y - 0.25, size=0.15, layer="DIMENSION")
    
    # Property corner cross-marks
    for cx, cy in [(lot_x, lot_y), (lot_x + lot_w, lot_y), 
                   (lot_x, lot_y + lot_h), (lot_x + lot_w, lot_y + lot_h)]:
        cross_s = 0.15
        msp.add_line((cx - cross_s, cy - cross_s), (cx + cross_s, cy + cross_s),
                     dxfattribs={"layer": "BOUNDARY"})
        msp.add_line((cx - cross_s, cy + cross_s), (cx + cross_s, cy - cross_s),
                     dxfattribs={"layer": "BOUNDARY"})
    
    # ── BUILDING ENVELOPE (setback boundary around house) ──
    env_margin_ft = 30.0  # 30' setback requirement
    env_margin = env_margin_ft / ft_per_cell
    env_x = hx - env_margin
    env_y = hy - env_margin
    env_w = house_w + 2 * env_margin
    env_h = house_h + 2 * env_margin
    # Use dashed/magenta for envelope
    doc.layers.add("ENVELOPE", color=6)  # magenta
    _rect(msp, env_x, env_y, env_w, env_h, layer="ENVELOPE")
    # Add cross-hatch pattern (diagonal lines)  
    step = 0.3
    for offset in range(0, int((env_w + env_h) / step)):
        x_off = offset * step
        msp.add_line(
            (env_x + max(0, x_off - env_h), env_y + max(0, env_h - x_off)),
            (env_x + min(env_w, x_off), env_y + max(0, env_h - x_off + env_w)),
            dxfattribs={"layer": "ENVELOPE"}
        )
    _txt(msp, "BUILDING ENVELOPE (30' SETBACK)", 
         env_x + env_w/2, env_y - 0.2, size=0.18,
         alignment=TextEntityAlignment.CENTER, layer="ENVELOPE")

    # ── PROPERTY DIMENSION CALLOUTS ──
    # Bottom edge dimension
    dim_y = lot_y - 0.4
    msp.add_line((lot_x, dim_y), (lot_x + lot_w, dim_y),
                 dxfattribs={"layer": "DIMENSION"})
    # Arrow ticks
    for ax in [lot_x, lot_x + lot_w]:
        arr_s = 0.1
        msp.add_line((ax, dim_y - arr_s), (ax, dim_y + arr_s),
                     dxfattribs={"layer": "DIMENSION"})
    lot_frontage_ft = int(math.sqrt(acres * 43560))
    _txt(msp, f"{lot_frontage_ft}'±", lot_x + lot_w/2, dim_y - 0.3,
         size=0.2, alignment=TextEntityAlignment.CENTER, layer="DIMENSION")

    # Right edge dimension
    dim_right_x = lot_x + lot_w + 0.4
    msp.add_line((dim_right_x, lot_y), (dim_right_x, lot_y + lot_h),
                 dxfattribs={"layer": "DIMENSION"})
    for ay in [lot_y, lot_y + lot_h]:
        arr_s = 0.1
        msp.add_line((dim_right_x - arr_s, ay), (dim_right_x + arr_s, ay),
                     dxfattribs={"layer": "DIMENSION"})
    lot_depth_ft = int(lot_frontage_ft * lot_h / lot_w)
    _txt(msp, f"{lot_depth_ft}'±", dim_right_x + 0.3, lot_y + lot_h/2,
         size=0.2, alignment=TextEntityAlignment.CENTER, layer="DIMENSION",)

    # ── LEADER LINES FOR KEY FEATURES ──
    doc.layers.add("LEADER", color=3)  # green
    # House leader
    _leader_line(msp, hx - 0.1, hy + house_h/2, hx - 0.8, hy + house_h/2 + 0.3)
    # Tank leader
    _leader_line(msp, tx - 0.1, ty + td/2, tx - 0.8, ty + td/2 - 0.2)
    
    # ── ADJACENT LOTS ──
    for adj_x, adj_label in [(lot_x - 0.8, "ADJ LOT 6"), (lot_x + lot_w + 0.1, "ADJ LOT 8")]:
        _txt(msp, adj_label, adj_x + 0.4, lot_y + lot_h/2, size=0.18,
             alignment=TextEntityAlignment.CENTER, layer="DIMENSION")
        msp.add_line((adj_x + 0.4, lot_y), (adj_x + 0.4, lot_y + lot_h),
                     dxfattribs={"layer": "BOUNDARY"})

    # ── DESIGN NOTES ──
    doc.layers.add("NOTE", color=7)
    notes = [
        f"TANK: {tank_cap}G  |  DISPOSAL FIELD: {brand} {mods_per_row}x{num_rows}",
    ]
    for i, note in enumerate(notes):
        _txt(msp, note, lot_x + 0.2, lot_y + lot_h - 1.0 - i * 0.3,
             size=0.18, layer="NOTE")

    # ── OBSERVATION HOLE MARKERS ──
    doc.layers.add("OBSERVATION", color=3)  # green
    oh_x1 = fx - 0.5
    oh_y1 = fy + cluster_l * 0.3
    oh_x2 = fx + cluster_w + 0.5
    oh_y2 = fy + cluster_l * 0.6
    _x_mark(msp, oh_x1, oh_y1, 0.12, layer="OBSERVATION")
    _x_mark(msp, oh_x2, oh_y2, 0.12, layer="OBSERVATION")
    _txt(msp, "OH-1", oh_x1 - 0.15, oh_y1 + 0.15, size=0.18, layer="OBSERVATION",
         alignment=TextEntityAlignment.CENTER)
    _txt(msp, "OH-2", oh_x2 + 0.15, oh_y2 + 0.15, size=0.18, layer="OBSERVATION",
         alignment=TextEntityAlignment.CENTER)

    # North arrow (improved)
    nay = lot_y + 0.8
    nar = 0.4
    msp.add_line((lot_x + lot_w - 1.2, nay), (lot_x + lot_w - 1.2, nay + nar),
                 dxfattribs={"layer": "BOUNDARY"})
    msp.add_line((lot_x + lot_w - 1.2 - 0.1, nay + nar * 0.7),
                 (lot_x + lot_w - 1.2, nay + nar),
                 dxfattribs={"layer": "BOUNDARY"})
    msp.add_line((lot_x + lot_w - 1.2 + 0.1, nay + nar * 0.7),
                 (lot_x + lot_w - 1.2, nay + nar),
                 dxfattribs={"layer": "BOUNDARY"})
    _txt(msp, "N", lot_x + lot_w - 1.2, nay + nar + 0.1, size=0.22,
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

    # ── PRIORITY 1 FIXES: Tank & System Components (TOP region) ──
    # Make tank MUCH larger (~50% of width) and add detailed components

    # Tank dimensions: ~8 units wide (50% of 16), proportional height
    tank_w = 8.0
    tank_h = 1.2
    cx = gx + cols / 2
    tank_x = cx - tank_w / 2
    tank_y = gy + rows - 3.5

    # Draw tank with outline + fill pattern
    _rect(msp, tank_x, tank_y, tank_w, tank_h, layer="STRUCTURE")
    # Add internal division line to show inlet/outlet compartments
    msp.add_line((tank_x + tank_w * 0.4, tank_y), (tank_x + tank_w * 0.4, tank_y + tank_h),
                 dxfattribs={"layer": "STRUCTURE"})
    msp.add_line((tank_x + tank_w * 0.6, tank_y), (tank_x + tank_w * 0.6, tank_y + tank_h),
                 dxfattribs={"layer": "STRUCTURE"})

    tank_cap = data.get("tank_cap", "1000")
    _txt(msp, f"{tank_cap} GALLON SEPTIC TANK", tank_x + tank_w / 2, tank_y + tank_h / 2,
         size=0.3, alignment=TextEntityAlignment.CENTER, layer="TEXT")

    # Tank dimension labels
    _txt(msp, f"{tank_w:.1f}'", tank_x + tank_w / 2, tank_y - 0.25,
         size=0.18, alignment=TextEntityAlignment.CENTER, layer="DIMENSION")
    _txt(msp, f"{tank_h:.1f}'", tank_x - 0.4, tank_y + tank_h / 2,
         size=0.18, alignment=TextEntityAlignment.CENTER, layer="DIMENSION")

    # D-box: positioned between tank and field
    dbox_w = 1.5
    dbox_h = 0.4
    dbox_x = cx - dbox_w / 2
    dbox_y = tank_y - 1.0 - dbox_h
    _rect(msp, dbox_x, dbox_y, dbox_w, dbox_h, layer="STRUCTURE")
    _txt(msp, "DISTRIBUTION BOX", dbox_x + dbox_w / 2, dbox_y + dbox_h / 2,
         size=0.22, alignment=TextEntityAlignment.CENTER, layer="TEXT")

    # Piping connections with arrows
    doc.layers.add("PIPE", color=5)
    # Tank outlet → D-box inlet (left side)
    msp.add_line((tank_x + tank_w * 0.35, tank_y), (dbox_x + dbox_w * 0.35, dbox_y + dbox_h),
                 dxfattribs={"layer": "PIPE"})
    _txt(msp, 'INLET', tank_x + tank_w * 0.35 - 0.4, tank_y - 0.35,
         size=0.15, layer="DIMENSION")

    # D-box outlet → right side (to field distribution lines)
    msp.add_line((dbox_x + dbox_w * 0.65, dbox_y + dbox_h), (dbox_x + dbox_w * 0.65, dbox_y - 0.5),
                 dxfattribs={"layer": "PIPE"})
    _txt(msp, 'OUTLET', dbox_x + dbox_w * 0.65 + 0.3, dbox_y - 0.3,
         size=0.15, layer="DIMENSION")

    # Baffle pipe indicator
    msp.add_line((tank_x + tank_w * 0.5, tank_y + tank_h), (tank_x + tank_w * 0.5, tank_y + tank_h + 0.15),
                 dxfattribs={"layer": "PIPE"})
    _txt(msp, 'OUTLET BAFFLE', tank_x + tank_w * 0.5 + 0.2, tank_y + tank_h + 0.08,
         size=0.12, layer="DIMENSION")

    # ── Disposal Field (below D-box) ──
    ft_per_cell = 3.67
    num_rows = int(data.get("num_rows", 3))
    mods_per_row = int(data.get("mods_per_row", 7))
    mod_len = float(data.get("mod_len", 4.0)) / ft_per_cell
    mod_wid = float(data.get("mod_wid", 3.67)) / ft_per_cell
    cluster_w = num_rows * mod_wid + (num_rows - 1) * 0.15
    cluster_l = mods_per_row * mod_len + (mods_per_row - 1) * 0.15

    field_y = dbox_y - 0.5 - cluster_l
    field_x = cx - cluster_w / 2

    _rect(msp, field_x, field_y, cluster_w, cluster_l, layer="HATCH")

    for ri in range(num_rows):
        for mi in range(mods_per_row):
            mx = field_x + ri * (mod_wid + 0.15)
            my = field_y + mi * (mod_len + 0.15)
            _rect(msp, mx, my, mod_wid, mod_len, layer="STRUCTURE")

    brand = data.get("brand", "Eljen").upper()
    _txt(msp, f"{brand} {mods_per_row}×{num_rows} MODULES",
         cx, field_y - 0.3, size=0.2, alignment=TextEntityAlignment.CENTER, layer="TEXT")

    # Tank-to-field distance callout
    dist_x = field_x - 0.8
    msp.add_line((dist_x, tank_y), (dist_x, field_y + cluster_l),
                 dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dist_x - 0.1, tank_y), (dist_x + 0.1, tank_y),
                 dxfattribs={"layer": "DIMENSION"})
    msp.add_line((dist_x - 0.1, field_y + cluster_l), (dist_x + 0.1, field_y + cluster_l),
                 dxfattribs={"layer": "DIMENSION"})
    distance_ft = dbox_y - (field_y + cluster_l) - 0.5
    _txt(msp, f"{distance_ft:.1f}' MIN", dist_x - 1.0, (tank_y + field_y + cluster_l) / 2,
         size=0.15, alignment=TextEntityAlignment.CENTER, layer="DIMENSION")

    # ── PRIORITY 2 FIXES: Scale/Table sizing (BOTTOM region) ──
    # Setback requirements table - reduced size
    table_y = gy + 0.3
    table_x = gx + 0.3
    table_w = cols - 0.6
    table_h = 0.6  # Reduced from default

    # Table header
    _rect(msp, table_x, table_y, table_w, table_h, layer="STRUCTURE")
    _txt(msp, "SETBACK REQUIREMENTS", table_x + 0.2, table_y + table_h - 0.2,
         size=0.14, layer="TEXT")

    # Scale bar - significantly reduced
    scale_bar_x = gx + 1.0
    scale_bar_y = gy + 1.5
    scale_bar_w = 2.0  # Much smaller than original
    msp.add_line((scale_bar_x, scale_bar_y), (scale_bar_x + scale_bar_w, scale_bar_y),
                 dxfattribs={"layer": "DIMENSION"})
    for sx in [scale_bar_x, scale_bar_x + scale_bar_w / 2, scale_bar_x + scale_bar_w]:
        msp.add_line((sx, scale_bar_y - 0.08), (sx, scale_bar_y + 0.08),
                     dxfattribs={"layer": "DIMENSION"})
    _txt(msp, "0         10         20 FT", scale_bar_x, scale_bar_y - 0.25,
         size=0.12, layer="DIMENSION")

    # ── Header ──
    owner = data.get("owner_name", "").upper()
    _txt(msp, f"{owner}", gx + 0.2, gy + rows - 0.2, size=0.22, layer="TEXT")
    _txt(msp, "DISPOSAL PLAN", gx + cols - 0.2, gy + rows - 0.2,
         size=0.22, alignment=TextEntityAlignment.RIGHT, layer="TEXT")

    # North arrow
    na_x = gx + cols - 1.5
    na_y = gy + 1.0
    msp.add_line((na_x, na_y), (na_x, na_y + 0.5), dxfattribs={"layer": "BOUNDARY"})
    msp.add_line((na_x - 0.15, na_y + 0.35), (na_x, na_y + 0.5),
                 dxfattribs={"layer": "BOUNDARY"})
    msp.add_line((na_x + 0.15, na_y + 0.35), (na_x, na_y + 0.5),
                 dxfattribs={"layer": "BOUNDARY"})
    _txt(msp, "N", na_x, na_y + 0.65, size=0.18, alignment=TextEntityAlignment.CENTER,
         layer="TEXT")

    doc.saveas(str(out_path))
    print(f"  ✓ Disposal Plan DXF (improved): {out_path}")
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
