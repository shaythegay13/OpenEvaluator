#!/usr/bin/env python3
"""
render_dxf.py — Scale-calibrated cross-section rendering for HHE-200.

Renders disposal field cross-sections at proper vertical/horizontal scales,
with backfill depths, ground profile, and scale bar.
"""

import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def render_cross_section(
    fields: Dict[str, str],
    output_path: Path,
    dpi: int = 96,
) -> Dict[str, Any]:
    """
    Render a disposal field cross-section at proper vertical/horizontal scales.

    Inputs (from sheet_parser):
    - finish_grade_elevation (reference, inches)
    - top_of_distribution_pipe_elevation (inches)
    - bottom_of_proprietary_device_elevation (inches)
    - bottom_of_disposal_field_elevation (inches)
    - water_table_depth_hole1 (inches below grade)
    - backfill_upslope_inches (optional)
    - backfill_downslope_inches (optional)
    - cross_section_vertical_scale_ft_per_in (e.g., "2.5" = 1"=2.5 ft)
    - cross_section_horizontal_scale_ft_per_in (e.g., "5.0" = 1"=5 ft)

    Returns:
    {
        "status": "RENDERED" | "ERROR",
        "output_file": Path,
        "dimensions": {"width_px": int, "height_px": int},
        "elevations": {...},
        "backfill": {"upslope": float, "downslope": float},
        "scales": {"vertical_ft_per_in": float, "horizontal_ft_per_in": float},
    }
    """
    from PIL import Image, ImageDraw, ImageFont

    # Parse elevation inputs (inches → feet)
    try:
        finish_grade_in = float(fields.get("finish_grade_elevation", "0") or "0")
        top_of_pipe_in = float(fields.get("top_of_distribution_pipe_elevation", "-12") or "-12")
        bottom_of_device_in = float(fields.get("bottom_of_proprietary_device_elevation", "-24") or "-24")
        bottom_of_field_in = float(fields.get("bottom_of_disposal_field_elevation", "-30") or "-30")
        water_table_depth_in = float(fields.get("water_table_depth_hole1", "24") or "24")

        finish_grade = finish_grade_in / 12.0
        top_of_pipe = top_of_pipe_in / 12.0
        bottom_of_device = bottom_of_device_in / 12.0
        bottom_of_field = bottom_of_field_in / 12.0

        # Sanity: fix wrong-signed values
        if bottom_of_device > finish_grade:
            bottom_of_device = -(abs(bottom_of_device_in) / 12.0)
        if bottom_of_field > finish_grade:
            bottom_of_field = -(abs(bottom_of_field_in) / 12.0)

        water_table_elev = finish_grade - (water_table_depth_in / 12.0)

        # Backfill (inches, optional)
        backfill_upslope_in = float(fields.get("backfill_upslope_inches", "") or "0")
        backfill_downslope_in = float(fields.get("backfill_downslope_inches", "") or "0")
        backfill_upslope = backfill_upslope_in / 12.0
        backfill_downslope = backfill_downslope_in / 12.0

    except (ValueError, TypeError) as e:
        logger.error(f"Error parsing elevations: {e}")
        return {"status": "ERROR", "error": str(e)}

    # Parse scales (feet per inch)
    try:
        vert_scale = float(fields.get("cross_section_vertical_scale_ft_per_in", "2.5") or "2.5")
        horiz_scale = float(fields.get("cross_section_horizontal_scale_ft_per_in", "5.0") or "5.0")
    except (ValueError, TypeError):
        vert_scale = 2.5
        horiz_scale = 5.0

    # ── Calculate drawing dimensions ────────────────────────────────────
    # Elevation range
    elev_min = min(finish_grade, top_of_pipe, bottom_of_device, bottom_of_field, water_table_elev) - 1
    elev_max = max(finish_grade, top_of_pipe, bottom_of_device, bottom_of_field, water_table_elev) + 1
    elev_range = elev_max - elev_min

    # Physical field width and depth (feet)
    field_width_ft = 11.0  # From intake: 11'x28' cluster, showing width on cross-section
    field_depth_ft = bottom_of_field - top_of_pipe

    # Convert to inches for drawing (at proper scales)
    elev_height_in = elev_range / vert_scale
    horiz_width_in = field_width_ft / horiz_scale

    # Add margins (inches)
    margin_in = 0.5
    total_width_in = horiz_width_in + 2 * margin_in + 1  # +1 for labels
    total_height_in = elev_height_in + 2 * margin_in + 1  # +1 for title/scale bar

    # Convert to pixels
    width_px = int(total_width_in * dpi)
    height_px = int(total_height_in * dpi)
    margin_px = int(margin_in * dpi)

    # Drawable area
    drawable_width_px = int(horiz_width_in * dpi)
    drawable_height_px = int(elev_height_in * dpi)

    # Coordinate mappers
    def elev_to_px(elev: float) -> int:
        """Elevation to pixel Y (top=max, bottom=min)."""
        return margin_px + int((elev_max - elev) / elev_range * drawable_height_px)

    def horiz_to_px(horiz_ft: float) -> int:
        """Horizontal distance to pixel X (0 = left edge)."""
        return margin_px + int(horiz_ft / field_width_ft * drawable_width_px)

    # ── Create image ────────────────────────────────────────────────────
    img = Image.new("RGB", (width_px, height_px), color="white")
    draw = ImageDraw.Draw(img)

    # Load font
    try:
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8)
        font_md = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)
    except OSError:
        font_sm = font_md = ImageFont.load_default()

    # ── Draw grid and axes ──────────────────────────────────────────────
    # Vertical axis (elevation labels)
    elev_step = 2.5
    elev = int(elev_min * 4) / 4  # Round to nearest 0.25
    while elev <= elev_max:
        y_px = elev_to_px(elev)
        draw.line([(margin_px - 5, y_px), (margin_px, y_px)], fill="black", width=1)
        label = f"{elev:.1f}'"
        draw.text((margin_px - 30, y_px - 4), label, fill="black", font=font_sm)
        elev += elev_step

    # Axes
    x_left = margin_px
    x_right = margin_px + drawable_width_px
    y_top = elev_to_px(elev_max)
    y_bottom = elev_to_px(elev_min)

    draw.line([(x_left, y_top), (x_left, y_bottom)], fill="black", width=2)  # Vertical axis
    draw.line([(x_left, y_bottom), (x_right, y_bottom)], fill="black", width=2)  # Horizontal axis

    # Grid
    elev = int(elev_min * 4) / 4
    while elev <= elev_max:
        y_px = elev_to_px(elev)
        draw.line([(x_left, y_px), (x_right, y_px)], fill="lightgray", width=1)
        elev += elev_step

    # ── Draw key elevations ─────────────────────────────────────────────
    # Finish grade (ground surface)
    fg_y = elev_to_px(finish_grade)
    draw.line([(x_left, fg_y), (x_right, fg_y)], fill="brown", width=3)
    draw.text((x_left + 5, fg_y - 12), "Grade", fill="brown", font=font_sm)

    # Top of pipe (positioned at field position 3ft)
    top_pipe_y = elev_to_px(top_of_pipe)
    draw.line([(horiz_to_px(3), top_pipe_y), (horiz_to_px(5), top_pipe_y)], fill="blue", width=2)
    draw.text((horiz_to_px(3), top_pipe_y - 12), "Top Pipe", fill="blue", font=font_sm)

    # Bottom of device (positioned at field position 5.5ft)
    bottom_device_y = elev_to_px(bottom_of_device)
    draw.line([(horiz_to_px(5.5), bottom_device_y), (horiz_to_px(7.5), bottom_device_y)], fill="purple", width=2)
    draw.text((horiz_to_px(5.5), bottom_device_y - 12), "Bot Device", fill="purple", font=font_sm)

    # Bottom of field (positioned at field position 8ft)
    bottom_field_y = elev_to_px(bottom_of_field)
    draw.line([(horiz_to_px(8), bottom_field_y), (horiz_to_px(10), bottom_field_y)], fill="darkgreen", width=2)
    draw.text((horiz_to_px(8), bottom_field_y - 12), "Bot Field", fill="darkgreen", font=font_sm)

    # Water table (spans full width)
    water_y = elev_to_px(water_table_elev)
    draw.line([(x_left, water_y), (x_right, water_y)], fill="cyan", width=2)
    draw.text((x_left + 5, water_y + 3), "Water Table", fill="cyan", font=font_sm)

    # ── Draw field disposal area box ────────────────────────────────────
    # Field is 11 feet wide, drawn at horizontal scale
    field_left = horiz_to_px(0)
    field_right = horiz_to_px(field_width_ft)
    field_top = top_pipe_y
    field_bottom = bottom_field_y

    draw.rectangle([(field_left, field_top), (field_right, field_bottom)], outline="darkgreen", width=2)
    draw.text((field_left + 3, field_top + 3), "FIELD", fill="darkgreen", font=font_sm)

    # Depth annotation
    field_depth_label = f"{field_depth_ft:.1f}'"
    draw.text((field_right + 3, (field_top + field_bottom) // 2), field_depth_label, fill="darkgreen", font=font_sm)

    # ── Draw backfill (if present) ──────────────────────────────────────
    if backfill_upslope > 0:
        # Upslope backfill: typically to the left of the field
        upslope_top = elev_to_px(finish_grade)
        upslope_bottom = elev_to_px(finish_grade - backfill_upslope)
        draw.line([(field_left - 10, upslope_top), (field_left, upslope_top)], fill="orange", width=2)
        draw.line([(field_left - 10, upslope_top), (field_left - 10, upslope_bottom)], fill="orange", width=2)
        label_up = f"{backfill_upslope_in:.0f}\""
        draw.text((field_left - 25, (upslope_top + upslope_bottom) // 2), label_up, fill="orange", font=font_sm)

    if backfill_downslope > 0:
        # Downslope backfill: typically to the right of the field
        downslope_top = elev_to_px(finish_grade)
        downslope_bottom = elev_to_px(finish_grade - backfill_downslope)
        draw.line([(field_right, downslope_top), (field_right + 10, downslope_top)], fill="orange", width=2)
        draw.line([(field_right + 10, downslope_top), (field_right + 10, downslope_bottom)], fill="orange", width=2)
        label_down = f"{backfill_downslope_in:.0f}\""
        draw.text((field_right + 12, (downslope_top + downslope_bottom) // 2), label_down, fill="orange", font=font_sm)

    # ── Draw scale bar ──────────────────────────────────────────────────
    scale_y = height_px - int(0.3 * dpi)
    scale_bar_len_in = 5  # 5 feet
    scale_bar_len_px = int(scale_bar_len_in / horiz_scale * dpi)
    scale_x = x_right - scale_bar_len_px - 20

    draw.line([(scale_x, scale_y), (scale_x + scale_bar_len_px, scale_y)], fill="black", width=2)
    draw.line([(scale_x, scale_y - 5), (scale_x, scale_y + 5)], fill="black", width=1)
    draw.line([(scale_x + scale_bar_len_px, scale_y - 5), (scale_x + scale_bar_len_px, scale_y + 5)], fill="black", width=1)
    draw.text((scale_x, scale_y + 8), f"{scale_bar_len_in} ft (horiz)", fill="black", font=font_sm)

    # ── Title ───────────────────────────────────────────────────────────
    client = fields.get("owner_name", "HHE-200")
    address = fields.get("site_address", "")
    title = f"{client} - {address} | Cross-Section"
    draw.text((margin_px, 5), title, fill="black", font=font_md)

    # Scale info
    scale_text = f"V: 1\"={vert_scale}ft | H: 1\"={horiz_scale}ft"
    draw.text((margin_px, 20), scale_text, fill="gray", font=font_sm)

    # ── Save ────────────────────────────────────────────────────────────
    img.save(str(output_path))
    logger.info(f"✓ Cross-section rendered: {output_path} ({width_px}x{height_px}px)")

    return {
        "status": "RENDERED",
        "output_file": output_path,
        "dimensions": {"width_px": width_px, "height_px": height_px},
        "elevations": {
            "finish_grade": finish_grade,
            "top_of_pipe": top_of_pipe,
            "bottom_of_device": bottom_of_device,
            "bottom_of_field": bottom_of_field,
            "water_table": water_table_elev,
        },
        "backfill": {
            "upslope_inches": backfill_upslope_in,
            "downslope_inches": backfill_downslope_in,
        },
        "scales": {
            "vertical_ft_per_in": vert_scale,
            "horizontal_ft_per_in": horiz_scale,
        },
    }


def render_soil_profile(
    fields: Dict[str, str],
    output_path: Path,
    dpi: int = 96,
) -> Dict[str, Any]:
    """
    Render a soil profile grid for page 3 lower half.

    Inputs (from sheet_parser):
    - soil_layers: list of dicts with 'depth' (str like "0-3 in") and 'soil' (description)
    - water_table_depth_hole1: water table depth in inches
    - owner_name: client name
    - site_address: property address

    Returns:
    {
        "status": "RENDERED" | "ERROR",
        "output_file": Path,
        "dimensions": {"width_px": int, "height_px": int},
        "soil_layers": [...],
    }
    """
    from PIL import Image, ImageDraw, ImageFont

    # Parse soil layers
    soil_layers = fields.get("soil_layers", [])
    if not soil_layers:
        logger.warning("No soil layers found; rendering empty profile")
        soil_layers = []

    water_table_depth = float(fields.get("water_table_depth_hole1", "24") or "24")

    # ── Calculate drawing dimensions ────────────────────────────────────
    # Soil profile grid: 0 to 48+ inches depth
    max_depth = 48
    depth_per_inch_px = 8  # pixels per depth inch (for a 48" deep profile)
    total_depth_px = max_depth * depth_per_inch_px

    # Layout dimensions
    left_margin_px = 60
    right_margin_px = 40
    top_margin_px = 40
    bottom_margin_px = 40
    grid_width_px = 200  # Width of the soil layer display area

    width_px = left_margin_px + grid_width_px + right_margin_px
    height_px = top_margin_px + total_depth_px + bottom_margin_px

    # ── Create image ────────────────────────────────────────────────────
    img = Image.new("RGB", (width_px, height_px), color="white")
    draw = ImageDraw.Draw(img)

    # Load fonts
    try:
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8)
        font_md = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)
    except OSError:
        font_sm = font_md = ImageFont.load_default()

    # ── Draw depth scale (left side) ────────────────────────────────────
    grid_left = left_margin_px
    grid_right = left_margin_px + grid_width_px
    grid_top = top_margin_px
    grid_bottom = grid_top + total_depth_px

    # Depth tick marks and labels (every 6 inches)
    for depth_in in range(0, max_depth + 1, 6):
        y_px = grid_top + depth_in * depth_per_inch_px
        # Tick mark
        draw.line([(grid_left - 10, y_px), (grid_left, y_px)], fill="black", width=1)
        # Depth label
        label = f"{depth_in}\""
        draw.text((grid_left - 35, y_px - 4), label, fill="black", font=font_sm)

    # ── Draw grid ───────────────────────────────────────────────────────
    # Vertical lines (left and right borders)
    draw.line([(grid_left, grid_top), (grid_left, grid_bottom)], fill="black", width=2)
    draw.line([(grid_right, grid_top), (grid_right, grid_bottom)], fill="black", width=2)

    # Horizontal lines (every 6 inches)
    for depth_in in range(0, max_depth + 1, 6):
        y_px = grid_top + depth_in * depth_per_inch_px
        draw.line([(grid_left, y_px), (grid_right, y_px)], fill="lightgray", width=1)

    # ── Draw soil layers ────────────────────────────────────────────────
    # Parse depth ranges from soil_layers
    colors = ["#D2B48C", "#8B7355", "#A0826D", "#696969", "#4B5C6F"]
    color_idx = 0

    for layer in soil_layers:
        depth_str = layer.get("depth", "unknown")
        soil_desc = layer.get("soil", "").strip()

        # Parse depth range (e.g., "0-3 in" or "0-24 in")
        if depth_str and depth_str != "unknown" and "-" in depth_str:
            try:
                parts = depth_str.replace(" in", "").split("-")
                depth_top = float(parts[0])
                depth_bottom = float(parts[1])
            except (ValueError, IndexError):
                continue
        else:
            continue

        # Convert to pixels
        y_top = grid_top + depth_top * depth_per_inch_px
        y_bottom = grid_top + depth_bottom * depth_per_inch_px

        # Draw soil layer box
        color = colors[color_idx % len(colors)]
        draw.rectangle(
            [(grid_left + 2, y_top), (grid_right - 2, y_bottom)],
            outline="black",
            fill=color,
            width=1,
        )

        # Label with soil description
        if soil_desc:
            # Wrap text to fit in the box
            lines = soil_desc.split()
            current_line = ""
            text_y = y_top + 3
            max_width = grid_width_px - 8

            for word in lines:
                test_line = current_line + (" " if current_line else "") + word
                # Rough estimate: font_sm is ~8px per char
                if len(test_line) * 5 > max_width:
                    if current_line:
                        draw.text((grid_left + 4, text_y), current_line, fill="black", font=font_sm)
                        text_y += 10
                    current_line = word
                else:
                    current_line = test_line

            if current_line:
                draw.text((grid_left + 4, text_y), current_line, fill="black", font=font_sm)

        color_idx += 1

    # ── Draw water table indicator ──────────────────────────────────────
    if water_table_depth > 0 and water_table_depth < max_depth:
        water_y = grid_top + water_table_depth * depth_per_inch_px
        draw.line([(grid_left - 15, water_y), (grid_right + 15, water_y)], fill="cyan", width=3)
        draw.text((grid_right + 5, water_y - 8), "WT", fill="cyan", font=font_sm)

    # ── Title ───────────────────────────────────────────────────────────
    client = fields.get("owner_name", "HHE-200")
    address = fields.get("site_address", "")
    title = f"SOIL PROFILE: {client} - {address}"
    draw.text((left_margin_px, 10), title, fill="black", font=font_md)

    # Depth label
    draw.text((grid_left - 35, grid_top - 20), "Depth (in)", fill="black", font=font_sm)

    # ── Save ────────────────────────────────────────────────────────────
    img.save(str(output_path))
    logger.info(f"✓ Soil profile rendered: {output_path} ({width_px}x{height_px}px)")

    return {
        "status": "RENDERED",
        "output_file": output_path,
        "dimensions": {"width_px": width_px, "height_px": height_px},
        "soil_layers": soil_layers,
        "water_table_depth": water_table_depth,
    }


if __name__ == "__main__":
    from sheet_parser import RAW_ROW, ROBERTS_ROW, parse_sheet_row

    logger.info("Testing render_dxf with both Marquis and Roberts…\n")

    # Marquis (no backfill)
    print("=" * 70)
    print("MARQUIS (26-018) - No backfill")
    print("=" * 70)
    fields_marquis = parse_sheet_row(RAW_ROW)
    output_cs_marquis = Path("/home/workspace/OpenEvaluator/cross_section_marquis_v2.png")
    result_marquis = render_cross_section(fields_marquis, output_cs_marquis)
    print(f"Cross-section: {result_marquis['status']}")
    print(f"Backfill: upslope={result_marquis['backfill']['upslope_inches']}\", downslope={result_marquis['backfill']['downslope_inches']}\"")

    output_soil_marquis = Path("/home/workspace/OpenEvaluator/soil_profile_marquis.png")
    result_soil_marquis = render_soil_profile(fields_marquis, output_soil_marquis)
    print(f"Soil profile: {result_soil_marquis['status']}")
    print(f"Layers: {len(result_soil_marquis['soil_layers'])} found\n")

    # Roberts (with backfill)
    print("=" * 70)
    print("ROBERTS (26-123) - With backfill 4\"/10\"")
    print("=" * 70)
    fields_roberts = parse_sheet_row(ROBERTS_ROW)
    output_cs_roberts = Path("/home/workspace/OpenEvaluator/cross_section_roberts_v2.png")
    result_roberts = render_cross_section(fields_roberts, output_cs_roberts)
    print(f"Cross-section: {result_roberts['status']}")
    print(f"Backfill: upslope={result_roberts['backfill']['upslope_inches']}\", downslope={result_roberts['backfill']['downslope_inches']}\"")

    output_soil_roberts = Path("/home/workspace/OpenEvaluator/soil_profile_roberts.png")
    result_soil_roberts = render_soil_profile(fields_roberts, output_soil_roberts)
    print(f"Soil profile: {result_soil_roberts['status']}")
    print(f"Layers: {len(result_soil_roberts['soil_layers'])} found\n")
