#!/usr/bin/env python3
"""Generate complete HHE-200 form pages as DXF (AutoCAD 2004 compatible).
All 4 pages: form fields + drawings + soil table + cross section."""
import json, math, os, sys
from pathlib import Path
from typing import Optional
import ezdxf
from ezdxf.enums import TextEntityAlignment
from ezdxf.math import Vec2

OUT_DIR = Path(__file__).parent / "dxf_output"
PAGE_W, PAGE_H = 34.0, 44.0  # inches (2x scale from 8.5x11)
MARGIN = 1.0
FONT = "Standard"

def _setup_page(title: str, page_w: float = PAGE_W, page_h: float = PAGE_H) -> tuple:
    doc = ezdxf.new("R2000")
    doc.units = 2  # Feet
    msp = doc.modelspace()
    for name, color, lw in [
        ("TITLE", 1, 30), ("STRUCTURE", 1, 30), ("TEXT", 7, 15),
        ("DIMENSION", 4, 15), ("BOUNDARY", 5, 30), ("HATCH", 8, 15),
        ("TABLE", 7, 15), ("LABEL", 7, 15), ("GRID", 3, 9),
        ("ROAD", 6, 30), ("WELL", 5, 30), ("FILL", 8, 9),
    ]:
        doc.layers.add(name, color=color, lineweight=lw)
    doc.styles.add("txt.shx", font="txt.shx")
    msp.add_lwpolyline([
        (0, 0), (page_w, 0), (page_w, page_h), (0, page_h), (0, 0)
    ], dxfattribs={"layer": "BOUNDARY", "lineweight": 50})
    return doc, msp

def _txt(msp, text, x, y, size=0.3, layer="TEXT", align=TextEntityAlignment.LEFT, style=FONT):
    t = msp.add_text(text, dxfattribs={"layer": layer, "height": size, "style": "txt.shx"})
    t.set_placement((x, y), align=align)
    return t

def _rect(msp, x, y, w, h, layer="STRUCTURE"):
    msp.add_lwpolyline([
        (x, y), (x+w, y), (x+w, y+h), (x, y+h), (x, y)
    ], dxfattribs={"layer": layer})

def generate_pg1(data: dict, path: Optional[Path] = None) -> Path:
    path = path or OUT_DIR / "PG1.dxf"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc, msp = _setup_page("PAGE 1")
    cx = PAGE_W / 2
    _txt(msp, "MAINE DEPARTMENT OF HEALTH AND HUMAN SERVICES", cx, PAGE_H - 0.8, size=0.3, align=TextEntityAlignment.CENTER, layer="TITLE")
    _txt(msp, "SUBSURFACE WASTEWATER DISPOSAL SYSTEM APPLICATION", cx, PAGE_H - 1.2, size=0.25, align=TextEntityAlignment.CENTER, layer="TITLE")
    _txt(msp, "HHE-200 - Page 1 of 4", cx, PAGE_H - 1.5, size=0.2, align=TextEntityAlignment.CENTER)
    y = PAGE_H - 2.5
    _txt(msp, "PROPERTY INFORMATION", MARGIN, y, size=0.22, layer="TITLE")
    y -= 0.5
    _txt(msp, f"Site Address: {data.get('street_name','')}", MARGIN+0.5, y, size=0.18)
    _txt(msp, f"Town: {data.get('town','')}", MARGIN+10, y, size=0.18)
    y -= 0.4
    _txt(msp, f"Map#: {data.get('map_number','')}  Lot#: {data.get('lot_number','')}", MARGIN+0.5, y, size=0.18)
    _txt(msp, f"Size: {data.get('property_size','')} ac.", MARGIN+10, y, size=0.18)
    y -= 0.6
    _txt(msp, "OWNER/APPLICANT", MARGIN, y, size=0.22, layer="TITLE")
    y -= 0.5
    _txt(msp, f"Owner: {data.get('owner_name','')}", MARGIN+0.5, y, size=0.18)
    _txt(msp, f"Phone: {data.get('owner_phone','')}", MARGIN+10, y, size=0.18)
    y -= 0.4
    _txt(msp, f"Mailing: {data.get('mailing_street','')}", MARGIN+0.5, y, size=0.18)
    _txt(msp, f"{data.get('mailing_city','')} {data.get('mailing_state','')} {data.get('mailing_zip','')}", MARGIN+10, y, size=0.18)
    y -= 0.6
    _txt(msp, "APPLICATION TYPE", MARGIN, y, size=0.22, layer="TITLE")
    y -= 0.5
    app = data.get('type_of_app','')
    _txt(msp, f"[{'X' if 'Replacement' in app else ' '}] Replacement", MARGIN+0.5, y, size=0.18)
    _txt(msp, f"[{'X' if 'New' in app else ' '}] New System", MARGIN+5, y, size=0.18)
    _txt(msp, f"[{'X' if 'Expansion' in app else ' '}] Expansion", MARGIN+10, y, size=0.18)
    y -= 0.6
    _txt(msp, "SYSTEM COMPONENTS", MARGIN, y, size=0.22, layer="TITLE")
    y -= 0.5
    _txt(msp, f"Field: {data.get('disposal_field_type','')}", MARGIN+0.5, y, size=0.18)
    _txt(msp, f"Flow: {data.get('design_flow_gpd','')} GPD", MARGIN+10, y, size=0.18)
    y -= 0.4
    _txt(msp, f"Bedrooms: {data.get('num_bedrooms_opt1','')}", MARGIN+0.5, y, size=0.18)
    y -= 0.6
    _txt(msp, "SITE EVALUATOR", MARGIN, y, size=0.22, layer="TITLE")
    y -= 0.5
    _txt(msp, f"Name: {data.get('evaluator_name','')}", MARGIN+0.5, y, size=0.18)
    _txt(msp, f"SE#: {data.get('se_number','')}", MARGIN+10, y, size=0.18)
    y -= 0.4
    _txt(msp, f"Phone: {data.get('evaluator_phone','')}", MARGIN+0.5, y, size=0.18)
    _txt(msp, f"Email: {data.get('evaluator_email','')}", MARGIN+10, y, size=0.18)
    y -= 0.6
    _txt(msp, "GPS COORDINATES", MARGIN, y, size=0.22, layer="TITLE")
    y -= 0.5
    _txt(msp, f"Lat: {data.get('latitude_deg','')} {data.get('latitude_min','')} {data.get('latitude_sec','')}", MARGIN+0.5, y, size=0.18)
    _txt(msp, f"Lng: {data.get('longitude_deg','')} {data.get('longitude_min','')} {data.get('longitude_sec','')}", MARGIN+10, y, size=0.18)
    y -= 0.4
    _txt(msp, f"Accuracy: +/-{data.get('gps_margin_error','30')} ft", MARGIN+0.5, y, size=0.18)
    doc.saveas(str(path))
    print(f"PG1: {path}")
    return path
def generate_pg2(data, path=None):
    path = path or OUT_DIR / "PG2.dxf"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc, msp = _setup_page("PAGE 2")
    cx = PAGE_W / 2.0
    
    _txt(msp, "SUBSURFACE WASTEWATER DISPOSAL SYSTEM APPLICATION", cx, PAGE_H - 0.6, size=0.25, align=TextEntityAlignment.CENTER, layer="TITLE")
    _txt(msp, "HHE-200 - Page 2 of 4  |  SITE DATA", cx, PAGE_H - 0.9, size=0.18, align=TextEntityAlignment.CENTER)
    
    y = PAGE_H - 1.5
    _txt(msp, "SITE DATA", MARGIN, y, size=0.22, layer="TITLE")
    y -= 0.5
    _txt(msp, "Owner: " + str(data.get("owner_name","")), MARGIN + 0.5, y, size=0.18)
    _txt(msp, "Address: " + str(data.get("address_line","")), MARGIN + 0.5, y - 0.35, size=0.18)
    y -= 0.7
    _txt(msp, "Property Size: " + str(data.get("acreage","")) + " ac.", MARGIN + 0.5, y, size=0.18)
    _txt(msp, "Current Use: " + str(data.get("current_use","")), MARGIN + 10, y, size=0.18)
    y -= 0.5
    _txt(msp, "Type of Water Supply: " + str(data.get("water_supply","")), MARGIN + 0.5, y, size=0.18)
    y -= 0.5
    _txt(msp, "Disposal System to Serve: " + str(data.get("disposal_system_to_serve","")), MARGIN + 0.5, y, size=0.18)
    _txt(msp, "Bedrooms: " + str(data.get("num_bedrooms_opt1","")), MARGIN + 10, y, size=0.18)
    y -= 0.5
    _txt(msp, "Design Flow: " + str(data.get("design_flow_gpd","")) + " gpd", MARGIN + 0.5, y, size=0.18)
    
    y -= 0.7
    _txt(msp, "SOIL DATA", MARGIN, y, size=0.22, layer="TITLE")
    y -= 0.5
    _txt(msp, "Limiting Factor: " + str(data.get("limiting_factor","")), MARGIN + 0.5, y, size=0.18)
    y -= 0.4
    _txt(msp, "Limiting Factor Depth: " + str(data.get("limiting_factor_depth","")), MARGIN + 0.5, y, size=0.18)
    
    y -= 0.7
    _txt(msp, "ADDITIONAL NOTES", MARGIN, y, size=0.22, layer="TITLE")
    y -= 0.5
    notes = data.get("site_notes", "")
    _txt(msp, str(notes), MARGIN + 0.5, y, size=0.16)
    
    doc.saveas(str(path))
    print("  PG2: " + str(path))
    return path

def generate_pg3(data, path=None):
    path = path or OUT_DIR / "PG3.dxf"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc, msp = _setup_page("PAGE 3")
    cx = PAGE_W / 2.0
    
    _txt(msp, "SUBSURFACE WASTEWATER DISPOSAL SYSTEM APPLICATION", cx, PAGE_H - 0.6, size=0.25, align=TextEntityAlignment.CENTER, layer="TITLE")
    _txt(msp, "HHE-200 - Page 3 of 4  |  SITE PLAN", cx, PAGE_H - 0.9, size=0.18, align=TextEntityAlignment.CENTER)
    
    owner = str(data.get("owner_name","")).upper()
    addr = str(data.get("address_line",""))
    _txt(msp, owner + "  |  " + addr, MARGIN, PAGE_H - 1.3, size=0.16, layer="LABEL")
    
    plan_top = PAGE_H - 1.6
    plan_bot = 14.0
    plan_left = MARGIN + 0.5
    plan_right = PAGE_W - MARGIN - 0.5
    plan_w = plan_right - plan_left
    plan_h = plan_top - plan_bot
    
    cols, rows = 30, 18
    cell_w = plan_w / cols
    cell_h = plan_h / rows
    
    for i in range(cols + 1):
        x = plan_left + i * cell_w
        msp.add_line((x, plan_bot), (x, plan_top), dxfattribs={"layer": "GRID"})
    for i in range(rows + 1):
        y = plan_bot + i * cell_h
        msp.add_line((plan_left, y), (plan_right, y), dxfattribs={"layer": "GRID"})
    
    _rect(msp, plan_left, plan_bot, plan_w, plan_h, layer="BOUNDARY")
    _txt(msp, "SITE PLAN", plan_left + 0.5, plan_top - 0.4, size=0.2, layer="TITLE")
    
    road = str(data.get("road_name","")).upper()
    if road:
        road_y = plan_top - 1.2
        msp.add_solid([(plan_left, road_y - 0.1), (plan_right, road_y - 0.1), (plan_left, road_y + 0.2)], dxfattribs={"layer": "FILL"})
        _txt(msp, road, cx, road_y + 0.05, size=0.25, align=TextEntityAlignment.CENTER)
    
    house_cx = cx
    house_y = plan_top - 3.5
    hw, hh = 2.0, 1.5
    hx = house_cx - hw / 2.0
    _rect(msp, hx, house_y, hw, hh, layer="STRUCTURE")
    _txt(msp, "EXISTING", house_cx, house_y + hh + 0.1, size=0.15, align=TextEntityAlignment.CENTER)
    _txt(msp, "HOUSE", house_cx, house_y - 0.1, size=0.15, align=TextEntityAlignment.CENTER)
    
    tank_cap = str(data.get("tank_cap", "1000"))
    tw, td = 0.8, 0.4
    ty = house_y - 0.8
    tx = house_cx - tw / 2.0
    _rect(msp, tx, ty, tw, td, layer="STRUCTURE")
    _txt(msp, tank_cap + "G", tx + tw + 0.1, ty + td / 2.0 - 0.05, size=0.14)
    _txt(msp, "TANK", tx + tw + 0.1, ty + td / 2.0 - 0.2, size=0.12)
    
    dbs = 0.3
    dby = ty - 0.6
    dbx = house_cx - dbs / 2.0
    _rect(msp, dbx, dby, dbs, dbs, layer="STRUCTURE")
    _txt(msp, "D-BOX", dbx + dbs + 0.1, dby + dbs / 2.0 - 0.05, size=0.14)
    
    num_rows = int(data.get("num_rows", 3))
    mods_per_row = int(data.get("mods_per_row", 7))
    mod_len = max(0.1, float(data.get("mod_len", 4.0)) * 0.05)
    mod_wid = max(0.1, float(data.get("mod_wid", 3.67)) * 0.05)
    
    cluster_w = num_rows * mod_wid + (num_rows - 1) * 0.05
    cluster_l = mods_per_row * mod_len + (mods_per_row - 1) * 0.05
    fx = house_cx - cluster_w / 2.0
    fy = dby - 0.4 - cluster_l
    
    _rect(msp, fx, fy, cluster_w, cluster_l, layer="BOUNDARY")
    for ri in range(num_rows):
        for mi in range(mods_per_row):
            mx = fx + ri * (mod_wid + 0.05)
            my = fy + mi * (mod_len + 0.05)
            _rect(msp, mx, my, mod_wid, mod_len, layer="HATCH")
    
    _txt(msp, "ELJEN " + str(mods_per_row) + "x" + str(num_rows) + " MODULES", house_cx, fy - 0.2, size=0.14, align=TextEntityAlignment.CENTER)
    
    well_x = plan_right - 1.5
    well_y = (plan_bot + plan_top) / 2.0
    msp.add_circle((well_x, well_y), 0.2, dxfattribs={"layer": "WELL"})
    _txt(msp, "WELL", well_x + 0.3, well_y + 0.15, size=0.16)
    
    _txt(msp, "MAP " + str(data.get("tax_map","")) + "  LOT " + str(data.get("lot_number","")), plan_left + 0.5, plan_bot + 0.8, size=0.2)
    _txt(msp, str(data.get("acreage","")) + " ACRES", plan_left + 0.5, plan_bot + 0.5, size=0.16)
    
    scale_val = str(data.get("scale_pg3", 80))
    _txt(msp, "SCALE: 1 in = " + scale_val + " ft", plan_left + 0.5, plan_bot + 0.2, size=0.16, layer="DIMENSION")
    
    se_num = str(data.get("se_number", ""))
    se_date = str(data.get("se_date", ""))
    _txt(msp, "SE #" + se_num + "  DATE: " + se_date, cx, plan_bot + 0.2, size=0.16, align=TextEntityAlignment.CENTER, layer="DIMENSION")
    
    doc.saveas(str(path))
    print("  PG3: " + str(path))
    return path

def generate_pg4(data, path=None):
    path = path or OUT_DIR / "PG4.dxf"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc, msp = _setup_page("PAGE 4")
    cx = PAGE_W / 2.0
    
    _txt(msp, "SUBSURFACE WASTEWATER DISPOSAL SYSTEM APPLICATION", cx, PAGE_H - 0.6, size=0.25, align=TextEntityAlignment.CENTER, layer="TITLE")
    _txt(msp, "HHE-200 - Page 4 of 4  |  DISPOSAL PLAN & CROSS-SECTION", cx, PAGE_H - 0.9, size=0.18, align=TextEntityAlignment.CENTER)
    
    owner = str(data.get("owner_name","")).upper()
    addr = str(data.get("address_line",""))
    _txt(msp, owner + "  |  " + addr, MARGIN, PAGE_H - 1.3, size=0.16, layer="LABEL")
    
    mid_y = PAGE_H / 2.0
    _txt(msp, "DISPOSAL PLAN VIEW", MARGIN + 0.5, mid_y + 10, size=0.2, layer="TITLE")
    
    y = mid_y + 8
    _rect(msp, MARGIN + 2, y, 1.5, 1.0, layer="STRUCTURE")
    _txt(msp, "SINGLE FAMILY DWELLING", MARGIN + 2.75, y + 0.3, size=0.14)
    msp.add_line((MARGIN + 3.5, y + 0.5), (cx - 0.4, y + 0.5), dxfattribs={"layer": "DIMENSION"})
    _txt(msp, "4 in PIPE", cx - 0.4, y + 0.7, size=0.12, align=TextEntityAlignment.CENTER)
    
    ty = y - 0.5
    _rect(msp, cx - 0.4, ty, 0.8, 0.4, layer="STRUCTURE")
    _txt(msp, "1000 GAL TANK", cx + 0.6, ty + 0.05, size=0.14)
    
    dby = ty - 0.4
    _rect(msp, cx - 0.15, dby, 0.3, 0.3, layer="STRUCTURE")
    _txt(msp, "D-BOX", cx + 0.35, dby + 0.05, size=0.12)
    
    fmy = dby - 1.5
    num_rows = int(data.get("num_rows", 3))
    mods_per_row = int(data.get("mods_per_row", 7))
    
    cluster_w = num_rows * 0.5 + (num_rows - 1) * 0.05
    cluster_l = mods_per_row * 0.35 + (mods_per_row - 1) * 0.05
    fx = cx - cluster_w / 2.0
    
    _rect(msp, fx, fmy, cluster_w, cluster_l, layer="BOUNDARY")
    for ri in range(num_rows):
        for mi in range(mods_per_row):
            mx = fx + ri * (0.5 + 0.05)
            my = fmy + mi * (0.35 + 0.05)
            _rect(msp, mx, my, 0.5, 0.35, layer="HATCH")
    _txt(msp, "ELJEN " + str(mods_per_row) + "x" + str(num_rows) + " MODULES", cx, fmy - 0.2, size=0.14, align=TextEntityAlignment.CENTER)
    
    _txt(msp, "CROSS SECTION: DISPOSAL FIELD INSTALLATION", MARGIN + 0.5, mid_y - 3, size=0.2, layer="TITLE")
    
    cxsec = mid_y - 6
    _txt(msp, "Construction Elevations:", MARGIN + 0.5, cxsec + 1.5, size=0.16)
    _txt(msp, "Finished Grade: " + str(data.get("finished_grade_elevation","0 in")), MARGIN + 2, cxsec + 1.0, size=0.14)
    _txt(msp, "Top of Pipe: " + str(data.get("top_of_distribution_pipe_elevation","-12 in")), MARGIN + 2, cxsec + 0.6, size=0.14)
    _txt(msp, "Bottom of Field: " + str(data.get("bottom_of_disposal_field_elevation","-30 in")), MARGIN + 2, cxsec + 0.2, size=0.14)
    
    lf = str(data.get("limiting_factor", ""))
    if lf:
        _txt(msp, "Limiting Factor at " + lf + "in", MARGIN + 12, cxsec + 1.0, size=0.14)
    
    se_num = str(data.get("se_number", ""))
    se_date = str(data.get("se_date", ""))
    _txt(msp, "SE #" + se_num + "  DATE: " + se_date, cx, MARGIN + 0.5, size=0.16, align=TextEntityAlignment.CENTER, layer="DIMENSION")
    
    doc.saveas(str(path))
    print("  PG4: " + str(path))
    return path

def generate_all_pages(data=None):
    if data is None:
        data = test_data()
    results = {}
    for fn, name in [(generate_pg1, "PG1"), (generate_pg2, "PG2"), (generate_pg3, "PG3"), (generate_pg4, "PG4")]:
        try:
            p = fn(data)
            results[name] = str(p)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print("FAIL " + name + ": " + str(e))
    return results

def test_data():
    return {"owner_name": "KRISTEN MARQUIS", "street_name": "17 ASPEN WAY", "town": "TURNER", "mailing_state": "ME", "mailing_zip": "04282", "map_number": "26", "lot_number": "18", "acreage": 2.35, "property_size": 2.35, "owner_phone": "", "mailing_street": "", "mailing_city": "TURNER", "type_of_app": "Replacement", "disposal_field_type": "Proprietary Device", "design_flow_gpd": 270, "num_bedrooms_opt1": 3, "evaluator_name": "GEORGE BOUCHLES", "se_number": "338", "evaluator_phone": "207-240-5567", "evaluator_email": "gsb@cadmasterr.com", "tax_map": "26", "address_line": "17 ASPEN WAY, TURNER, ME 04282", "road_name": "ROAD", "scale_pg3": 80, "tank_cap": "1000", "num_rows": 3, "mods_per_row": 7, "mod_len": 4.0, "mod_wid": 3.67, "tank_to_house": 8, "field_to_well": 100, "water_supply": "Drilled Well", "disposal_system_to_serve": "Single Family Dwelling Unit", "current_use": "Year-round", "limiting_factor": "Ground Water", "limiting_factor_depth": "24", "site_notes": "Existing 1000-gallon septic tank shall be exposed, inspected for structural integrity.", "finished_grade_elevation": "0 in", "top_of_distribution_pipe_elevation": "-12 in", "bottom_of_disposal_field_elevation": "-30 in", "se_date": "03/01/2026"}

if __name__ == "__main__":
    results = generate_all_pages()
    print("\nGenerated: " + ", ".join([v for v in results.values()]))
