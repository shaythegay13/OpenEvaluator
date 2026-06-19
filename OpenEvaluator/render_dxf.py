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


def render_boundary_layer(
    fields: Dict[str, str],
    output_path: Path,
    dpi: int = 96,
) -> Dict[str, Any]:
    """
    Render a boundary layer for the plan view (page 3 upper half).

    Inputs (from sheet_parser + parcel_enricher):
    - map_number, lot_number: parcel ID
    - town, site_address: for GeoLibrary lookup
    - acreage: for scoring multiple matches

    Outputs:
    - PNG of plan view showing parcel boundary, corner markers, dimensioned edges, lot number
    """
    from PIL import Image, ImageDraw, ImageFont
    from parcel_enricher import get_parcel_dimensions

    town = fields.get("town", "")
    address = fields.get("site_address", "")
    acres = float(fields.get("acreage", 0)) if fields.get("acreage") else None
    map_num = fields.get("map_number", "")
    lot_num = fields.get("lot_number", "")

    # Fetch parcel boundary from GeoLibrary
    parcel = get_parcel_dimensions(town, address, acres)
    if not parcel.get("found"):
        logger.error(f"Parcel not found: {address}, {town}")
        return {
            "status": "ERROR",
            "error": "Parcel not found in GeoLibrary",
            "output_file": None,
        }

    rings = parcel.get("rings", [])
    corners = parcel.get("corners", [])
    if not rings or not corners:
        logger.error("No geometry returned from GeoLibrary")
        return {
            "status": "ERROR",
            "error": "No boundary geometry",
            "output_file": None,
        }

    # Use exterior ring (first ring) as the parcel boundary
    exterior_ring = rings[0]

    # Convert from meters to feet
    ring_ft = [[pt[0] * 3.28084, pt[1] * 3.28084] for pt in exterior_ring]
    corners_ft = [[pt[0] * 3.28084, pt[1] * 3.28084] for pt in corners]

    # Find bounding box and center
    xs = [pt[0] for pt in ring_ft]
    ys = [pt[1] for pt in ring_ft]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    width_ft = max_x - min_x
    height_ft = max_y - min_y

    # Plan view scale: 1" = 10 ft
    plan_scale_ft_per_in = 10.0

    # Calculate image dimensions (with margins)
    margin_px = 60
    scale_px_per_ft = dpi / plan_scale_ft_per_in
    polygon_width_px = int(width_ft * scale_px_per_ft)
    polygon_height_px = int(height_ft * scale_px_per_ft)

    width_px = polygon_width_px + 2 * margin_px
    height_px = polygon_height_px + 2 * margin_px

    # Create image
    img = Image.new("RGB", (width_px, height_px), color="white")
    draw = ImageDraw.Draw(img)

    # Load fonts
    try:
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8)
        font_md = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)
        font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
    except OSError:
        font_sm = font_md = font_lg = ImageFont.load_default()

    # Convert feet coordinates to pixels (with local origin at center)
    def feet_to_px(x_ft, y_ft):
        px_x = margin_px + polygon_width_px // 2 + int((x_ft - center_x) * scale_px_per_ft)
        px_y = margin_px + polygon_height_px // 2 - int((y_ft - center_y) * scale_px_per_ft)  # Y inverted for screen coords
        return (px_x, px_y)

    # ── Draw parcel boundary polygon ──────────────────────────────────
    polygon_pts = [feet_to_px(pt[0], pt[1]) for pt in ring_ft]
    draw.polygon(polygon_pts, outline="darkblue", width=3, fill="lightyellow")

    # ── Draw corner/pin markers ──────────────────────────────────────
    corner_radius = 5
    for i, corner_ft in enumerate(corners_ft):
        cx, cy = feet_to_px(corner_ft[0], corner_ft[1])
        # Draw small circle for corner
        draw.ellipse([(cx - corner_radius, cy - corner_radius),
                      (cx + corner_radius, cy + corner_radius)],
                     outline="red", width=2, fill="lightyellow")
        # Label corner number
        draw.text((cx + 8, cy - 5), str(i + 1), fill="red", font=font_sm)

    # ── Dimension edges ──────────────────────────────────────────────
    for i in range(len(polygon_pts)):
        pt1_ft = ring_ft[i]
        pt2_ft = ring_ft[(i + 1) % len(ring_ft)]
        pt1_px = polygon_pts[i]
        pt2_px = polygon_pts[(i + 1) % len(polygon_pts)]

        # Calculate edge distance in feet
        dx_ft = pt2_ft[0] - pt1_ft[0]
        dy_ft = pt2_ft[1] - pt1_ft[1]
        edge_length_ft = (dx_ft ** 2 + dy_ft ** 2) ** 0.5

        # Mid-point for label
        mid_px = ((pt1_px[0] + pt2_px[0]) // 2, (pt1_px[1] + pt2_px[1]) // 2)

        # Draw dimension line (offset from edge)
        offset_px = 15
        # Perpendicular direction (rotated 90 degrees)
        dx_px = pt2_px[0] - pt1_px[0]
        dy_px = pt2_px[1] - pt1_px[1]
        length_px = (dx_px ** 2 + dy_px ** 2) ** 0.5
        if length_px > 0:
            norm_x = -dy_px / length_px
            norm_y = dx_px / length_px
            offset_x = norm_x * offset_px
            offset_y = norm_y * offset_px

            dim_pt1 = (pt1_px[0] + offset_x, pt1_px[1] + offset_y)
            dim_pt2 = (pt2_px[0] + offset_x, pt2_px[1] + offset_y)
            draw.line([dim_pt1, dim_pt2], fill="darkgreen", width=1)

            # Label with distance
            label = f"{edge_length_ft:.0f}'"
            draw.text((mid_px[0] + offset_x // 2, mid_px[1] + offset_y // 2), label, fill="darkgreen", font=font_sm)

    # ── Add lot number and parcel info ───────────────────────────────
    lot_text = f"Map {map_num}, Lot {lot_num}"
    area_ac = parcel.get("area_ac", 0)
    area_text = f"{area_ac} acres"

    info_y = margin_px + 10
    draw.text((margin_px, info_y), lot_text, fill="black", font=font_md)
    draw.text((margin_px, info_y + 20), area_text, fill="darkblue", font=font_sm)

    # ── Title ────────────────────────────────────────────────────────
    client = fields.get("owner_name", "HHE-200")
    address = fields.get("site_address", "")
    title = f"BOUNDARY: {client} - {address}"
    draw.text((margin_px, 5), title, fill="black", font=font_lg)

    # Scale info
    scale_text = f"Plan View: 1\"={plan_scale_ft_per_in}ft"
    draw.text((margin_px, height_px - 25), scale_text, fill="gray", font=font_sm)

    # ── Save ─────────────────────────────────────────────────────────
    img.save(str(output_path))
    logger.info(f"✓ Boundary rendered: {output_path} ({width_px}x{height_px}px)")

    return {
        "status": "RENDERED",
        "output_file": output_path,
        "dimensions": {"width_px": width_px, "height_px": height_px},
        "parcel": {
            "map_bk_lot": parcel.get("map_bk_lot"),
            "area_ac": parcel.get("area_ac"),
            "corners": len(corners_ft),
        },
    }


if __name__ == "__main__":
    from sheet_parser import RAW_ROW, ROBERTS_ROW, parse_sheet_row

    logger.info("Testing render_dxf with both Marquis and Roberts…\n")

    # Marquis (no backfill)
    print("=" * 70)
    print("MARQUIS (26-018) - Boundary + Cross-section + Soil")
    print("=" * 70)
    fields_marquis = parse_sheet_row(RAW_ROW)

    # Boundary
    output_boundary_marquis = Path("/home/workspace/OpenEvaluator/boundary_marquis.png")
    result_boundary_marquis = render_boundary_layer(fields_marquis, output_boundary_marquis)
    print(f"Boundary: {result_boundary_marquis['status']}")
    if result_boundary_marquis['status'] == 'RENDERED':
        print(f"  Parcel: {result_boundary_marquis['parcel']}")

    # Cross-section
    output_cs_marquis = Path("/home/workspace/OpenEvaluator/cross_section_marquis_v2.png")
    result_marquis = render_cross_section(fields_marquis, output_cs_marquis)
    print(f"Cross-section: {result_marquis['status']}")
    print(f"Backfill: upslope={result_marquis['backfill']['upslope_inches']}\", downslope={result_marquis['backfill']['downslope_inches']}\"")

    # Soil profile
    output_soil_marquis = Path("/home/workspace/OpenEvaluator/soil_profile_marquis.png")
    result_soil_marquis = render_soil_profile(fields_marquis, output_soil_marquis)
    print(f"Soil profile: {result_soil_marquis['status']}")
    print(f"Layers: {len(result_soil_marquis['soil_layers'])} found\n")

    # Roberts (with backfill)
    print("=" * 70)
    print("ROBERTS (26-123) - With backfill 4\"/10\"")
    print("=" * 70)
    fields_roberts = parse_sheet_row(ROBERTS_ROW)

    # Boundary
    output_boundary_roberts = Path("/home/workspace/OpenEvaluator/boundary_roberts.png")
    result_boundary_roberts = render_boundary_layer(fields_roberts, output_boundary_roberts)
    print(f"Boundary: {result_boundary_roberts['status']}")
    if result_boundary_roberts['status'] == 'RENDERED':
        print(f"  Parcel: {result_boundary_roberts['parcel']}")

    # Cross-section
    output_cs_roberts = Path("/home/workspace/OpenEvaluator/cross_section_roberts_v2.png")
    result_roberts = render_cross_section(fields_roberts, output_cs_roberts)
    print(f"Cross-section: {result_roberts['status']}")
    print(f"Backfill: upslope={result_roberts['backfill']['upslope_inches']}\", downslope={result_roberts['backfill']['downslope_inches']}\"")

    # Soil profile
    output_soil_roberts = Path("/home/workspace/OpenEvaluator/soil_profile_roberts.png")
    result_soil_roberts = render_soil_profile(fields_roberts, output_soil_roberts)
    print(f"Soil profile: {result_soil_roberts['status']}")
    print(f"Layers: {len(result_soil_roberts['soil_layers'])} found\n")


def solve_field_placement(
    parcel_data: Dict[str, Any],
    field_width_ft: float = 11.0,
    field_length_ft: float = 28.0,
    tie_point_a: Optional[Tuple[float, float]] = None,
    tie_point_b: Optional[Tuple[float, float]] = None,
    distance_a_to_corner_c1_ft: float = 0.0,
    distance_b_to_corner_c2_ft: float = 0.0,
    pin_name: str = "PIN",
    system_type: str = "replacement",
) -> Dict[str, Any]:
    """
    Trilateration placement solver for disposal field rectangle.

    Inputs:
    - parcel_data: boundary rings + corner coordinates from GeoLibrary
    - field_width_ft, field_length_ft: disposal field dimensions (default 11x28)
    - tie_point_a, tie_point_b: (x, y) coordinates of two fixed field reference points
    - distance_a_to_corner_c1_ft: distance from tie point A to field corner C1
    - distance_b_to_corner_c2_ft: distance from tie point B to field corner C2
    - pin_name: which corner is the anchor (e.g., "PIN" or "SE")
    - system_type: "replacement" or "new" (affects phantom rejection logic)

    Returns:
    {
        "status": "SOLVED" | "AMBIGUOUS" | "NO_SOLUTION" | "SETBACK_FLAG",
        "field_center": (x, y) or None,
        "field_rotation_degrees": float,
        "field_corners": [(x1, y1), (x2, y2), (x3, y3), (x4, y4)] or [],
        "candidates": [...],  # For AMBIGUOUS case
        "violated_setbacks": [...],
        "message": str,
    }
    """
    import math

    result = {
        "status": "NO_SOLUTION",
        "field_center": None,
        "field_rotation_degrees": 0.0,
        "field_corners": [],
        "candidates": [],
        "violated_setbacks": [],
        "message": "",
    }

    # Validate inputs
    if not tie_point_a or not tie_point_b:
        result["message"] = "Tie points A and B required"
        return result

    if distance_a_to_corner_c1_ft <= 0 or distance_b_to_corner_c2_ft <= 0:
        result["message"] = "Distances must be positive"
        return result

    rings = parcel_data.get("rings", [])
    if not rings:
        result["message"] = "No parcel boundary available"
        return result

    # Step 3: Circle intersection for two candidates
    # Two circles: center=tie_point_a, radius=distance_a; center=tie_point_b, radius=distance_b
    xa, ya = tie_point_a
    xb, yb = tie_point_b
    ra = distance_a_to_corner_c1_ft
    rb = distance_b_to_corner_c2_ft

    d = math.sqrt((xb - xa) ** 2 + (yb - ya) ** 2)

    if d > ra + rb or d < abs(ra - rb) or d == 0:
        result["message"] = f"Circles do not intersect (d={d:.1f}, ra={ra:.1f}, rb={rb:.1f})"
        return result

    # Circle intersection formula
    a = (ra ** 2 - rb ** 2 + d ** 2) / (2 * d)
    h_sq = ra ** 2 - a ** 2
    if h_sq < 0:
        result["message"] = "No valid intersection"
        return result

    h = math.sqrt(h_sq)

    # Intersection point along the line between tie points
    px = xa + a * (xb - xa) / d
    py = ya + a * (yb - ya) / d

    # Two candidate perpendicular offsets
    candidates = []
    for sign in [1, -1]:
        # One of the two field corners
        cx = px + sign * h * (yb - ya) / d
        cy = py - sign * h * (xb - xa) / d

        # The field is a rectangle with known dimensions
        # For this prototype, assume corner is at bottom-left
        field_center = (cx + field_width_ft / 2, cy + field_length_ft / 2)

        candidates.append({
            "corner_c1": (cx, cy),
            "field_center": field_center,
            "rotation": 0.0,
        })

    # Step 4: Phantom rejection using constraints
    valid_candidates = []
    for cand in candidates:
        # For prototype v1: accept all valid circle intersections
        # In production: would check point-in-polygon, setbacks, etc.
        valid_candidates.append(cand)

    if len(valid_candidates) == 0:
        result["status"] = "NO_SOLUTION"
        result["message"] = "No valid placement satisfies constraints"
        return result

    if len(valid_candidates) == 1:
        cand = valid_candidates[0]
        result["status"] = "SOLVED"
        result["field_center"] = cand["field_center"]
        result["field_rotation_degrees"] = cand["rotation"]
        result["field_corners"] = get_field_corners(
            cand["field_center"], field_width_ft, field_length_ft, cand["rotation"]
        )
        result["message"] = "Field placement solved"
        return result

    if len(valid_candidates) > 1:
        result["status"] = "AMBIGUOUS"
        result["candidates"] = valid_candidates
        result["message"] = f"{len(valid_candidates)} candidate placements satisfy constraints"
        return result

    return result


def point_in_polygon(point: Tuple[float, float], polygon: List[Tuple[float, float]]) -> bool:
    """Ray casting algorithm for point-in-polygon test."""
    x, y = point
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def get_field_corners(
    center: Tuple[float, float],
    width_ft: float,
    length_ft: float,
    rotation_degrees: float = 0.0,
) -> List[Tuple[float, float]]:
    """Compute the four corners of a field rectangle."""
    import math

    cx, cy = center
    rad = math.radians(rotation_degrees)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    # Half dimensions
    hw = width_ft / 2
    hl = length_ft / 2

    # Corner offsets in local coordinates
    offsets = [(-hw, -hl), (hw, -hl), (hw, hl), (-hw, hl)]

    # Rotate and translate
    corners = []
    for dx, dy in offsets:
        x = cx + dx * cos_a - dy * sin_a
        y = cy + dx * sin_a + dy * cos_a
        corners.append((x, y))

    return corners


def solve_field_placement_from_sheet(
    fields: Dict[str, str],
    parcel_data: Optional[Dict[str, Any]] = None,
    bearing_a_degrees: Optional[float] = None,
    bearing_b_degrees: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Wire parsed tie-point data from sheet_parser to the placement solver.

    Inputs (from sheet_parser fields dict):
    - tie_point_a_object, tie_point_a_distance, tie_point_a_corner
    - tie_point_b_object, tie_point_b_distance, tie_point_b_corner
    - pin_object, pin_distance
    - map_number, lot_number, town, mailing_state (for GeoLibrary lookup)
    - cluster_width_ft, cluster_length_ft (field dimensions)

    Optional:
    - bearing_a_degrees: magnetic bearing from pin to tie point A (degrees, 0-360)
    - bearing_b_degrees: magnetic bearing from pin to tie point B (degrees, 0-360)
    - If not provided, defaults to 45° and 135° (NE and SE)

    Returns placement result with status, field corners, etc.
    """
    from parcel_enricher import get_parcel_dimensions

    # Extract parsed tie-point data
    tp_a_obj = fields.get("tie_point_a_object", "")
    tp_a_dist = fields.get("tie_point_a_distance", "0")
    tp_a_corner = fields.get("tie_point_a_corner", "")
    tp_b_obj = fields.get("tie_point_b_object", "")
    tp_b_dist = fields.get("tie_point_b_distance", "0")
    tp_b_corner = fields.get("tie_point_b_corner", "")
    pin_obj = fields.get("pin_object", "")
    pin_dist = fields.get("pin_distance", "0")

    # Field dimensions
    field_width = float(fields.get("cluster_width_ft", "11") or "11")
    field_length = float(fields.get("cluster_length_ft", "28") or "28")

    # Application type
    app_type = fields.get("application_type", fields.get("Application Type", "replacement")).lower()
    system_type = "replacement" if "replacement" in app_type else "new"

    # Validate critical inputs
    if not tp_a_obj or not tp_a_dist or not tp_a_corner:
        return {
            "status": "ERROR",
            "message": "Tie Point A incomplete (object, distance, corner required)",
        }

    if not tp_b_obj or not tp_b_dist or not tp_b_corner:
        return {
            "status": "ERROR",
            "message": "Tie Point B incomplete (object, distance, corner required)",
        }

    # Fetch parcel data if not provided
    if parcel_data is None:
        site_address = fields.get("site_address", "")
        town = fields.get("town", "")
        acreage = fields.get("acreage", "")

        if not site_address or not town:
            return {
                "status": "ERROR",
                "message": "Missing parcel identifiers (address/town)",
            }

        try:
            acres_float = float(acreage) if acreage else None
        except ValueError:
            acres_float = None

        parcel_data = get_parcel_dimensions(
            town=town,
            address=site_address,
            acres=acres_float,
        )

        if not parcel_data.get("found"):
            return {
                "status": "ERROR",
                "message": f"Parcel lookup failed for {site_address}, {town}",
            }

    # ── For now: use mock tie-point coordinates based on pin ──────────────
    # Production: would need direction/bearing data in the intake form
    # The tie points are placed at distances from the pin, but without bearing,
    # we use reasonable defaults based on field observations
    exterior_ring = parcel_data.get("corners", parcel_data.get("rings", [[]])[0])

    if not exterior_ring:
        return {
            "status": "ERROR",
            "message": "Could not get parcel boundary from GeoLibrary",
        }

    # Use first vertex of the exterior ring as the pin coordinate (in meters from WGS84)
    pin_coord = exterior_ring[0]

    try:
        pin_x, pin_y = float(pin_coord[0]), float(pin_coord[1])
        tp_a_dist_ft = float(tp_a_dist)
        tp_b_dist_ft = float(tp_b_dist)
    except (ValueError, TypeError) as e:
        return {
            "status": "ERROR",
            "message": f"Invalid coordinate/distance values: {e}",
        }

    # Tie-point placement: offset from pin at specified bearings
    import math

    # Extract bearings from corner labels if not explicitly provided
    if bearing_a_degrees is None:
        # Infer bearing from the corner label
        corner_to_bearing_map = {
            "NE": 45.0, "northeast": 45.0,
            "SE": 135.0, "southeast": 135.0,
            "SW": 225.0, "southwest": 225.0,
            "NW": 315.0, "northwest": 315.0,
        }
        bearing_a = corner_to_bearing_map.get(tp_a_corner.upper(), 45.0)
    else:
        bearing_a = bearing_a_degrees

    if bearing_b_degrees is None:
        corner_to_bearing_map = {
            "NE": 45.0, "northeast": 45.0,
            "SE": 135.0, "southeast": 135.0,
            "SW": 225.0, "southwest": 225.0,
            "NW": 315.0, "northwest": 315.0,
        }
        bearing_b = corner_to_bearing_map.get(tp_b_corner.upper(), 135.0)
    else:
        bearing_b = bearing_b_degrees

    # Place tie point A at specified bearing and distance from pin
    angle_a = math.radians(bearing_a)
    tie_point_a = (pin_x + tp_a_dist_ft * math.cos(angle_a),
                   pin_y + tp_a_dist_ft * math.sin(angle_a))

    # Place tie point B at specified bearing and distance from pin
    angle_b = math.radians(bearing_b)
    tie_point_b = (pin_x + tp_b_dist_ft * math.cos(angle_b),
                   pin_y + tp_b_dist_ft * math.sin(angle_b))

    # Call the placement solver
    result = solve_field_placement(
        parcel_data=parcel_data,
        field_width_ft=field_width,
        field_length_ft=field_length,
        tie_point_a=tie_point_a,
        tie_point_b=tie_point_b,
        distance_a_to_corner_c1_ft=tp_a_dist_ft,
        distance_b_to_corner_c2_ft=tp_b_dist_ft,
        pin_name=pin_obj,
        system_type=system_type,
    )

    return result


def render_boundary_with_field(
    parcel_data: Dict[str, Any],
    field_placement: Dict[str, Any],
    output_path: str,
    dpi: int = 96,
) -> None:
    """
    Render boundary layer with placed field rectangle on top.
    Uses the first candidate if ambiguous.
    """
    from PIL import Image, ImageDraw, ImageFont

    rings = parcel_data.get("rings", [])
    if not rings:
        logger.error("No parcel rings found")
        return

    # Convert to feet
    ring_ft = [[pt[0]*3.28084, pt[1]*3.28084] for pt in rings[0]]
    
    # Find bounds
    xs = [pt[0] for pt in ring_ft]
    ys = [pt[1] for pt in ring_ft]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    # Plan scale: 1" = 10 ft
    plan_scale = 10.0
    px_per_ft = dpi / plan_scale
    
    margin = 60
    width_px = int((max_x - min_x) * px_per_ft) + 2 * margin
    height_px = int((max_y - min_y) * px_per_ft) + 2 * margin
    
    img = Image.new("RGB", (width_px, height_px), "white")
    draw = ImageDraw.Draw(img)
    
    # Convert coordinate to pixel
    def to_px(x_ft, y_ft):
        px_x = margin + (x_ft - min_x) * px_per_ft
        px_y = margin + (y_ft - min_y) * px_per_ft
        return (px_x, px_y)
    
    # Draw boundary
    boundary_pts = [to_px(pt[0], pt[1]) for pt in ring_ft]
    draw.polygon(boundary_pts, outline="darkblue", width=2, fill="lightyellow")
    
    # Draw field placement (if solved)
    if field_placement['status'] in ['SOLVED', 'AMBIGUOUS']:
        # Use first candidate if ambiguous
        if field_placement['status'] == 'AMBIGUOUS':
            cand = field_placement['candidates'][0]
        else:
            cand = {
                'field_center': field_placement['field_center'],
                'rotation': field_placement['field_rotation_degrees'],
            }

        # Get corners (in meters from projection)
        corners = field_placement.get('field_corners', [])
        if not corners and 'field_center' in field_placement and field_placement['field_center']:
            # Reconstruct corners from field_center
            field_width = 11.0
            field_length = 28.0
            corners = get_field_corners(field_placement['field_center'], field_width, field_length, field_placement.get('field_rotation_degrees', 0))

        if not corners and cand:
            # Reconstruct from candidate (for AMBIGUOUS case)
            field_width = 11.0
            field_length = 28.0
            corners = get_field_corners(cand['field_center'], field_width, field_length, cand['rotation'])

        if corners:
            # Convert corners from meters to feet, then to pixels
            corners_ft = [[c[0]*3.28084, c[1]*3.28084] for c in corners]
            field_pts = [to_px(c[0], c[1]) for c in corners_ft]
            draw.polygon(field_pts, outline="red", width=3, fill="lightcoral")

            # Label field
            center_px = (int(sum(p[0] for p in field_pts) / len(field_pts)),
                        int(sum(p[1] for p in field_pts) / len(field_pts)))
            draw.text(center_px, "FIELD", fill="darkred", font=None)
    
    img.save(output_path)
    logger.info(f"✓ Boundary + field rendered: {output_path} ({width_px}x{height_px}px)")

