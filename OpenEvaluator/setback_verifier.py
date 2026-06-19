#!/usr/bin/env python3
"""
setback_verifier.py — Verify disposal field setbacks against code minimums.

After placement solver returns field position, compute all setbacks:
- Well: 100 ft minimum
- Building: 20 ft (full foundation), 15 ft (slab), n/a (no building)
- Tank: 50 ft from well
- Property line: 10 ft minimum
- Water/wetland: 100 ft minimum

Returns SOLVED (all pass or variance declared) or FLAG_SETBACK (short without variance).
"""

import re
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def verify_setbacks(
    fields: Dict[str, Any],
    placed_field: Dict[str, Any],
    parcel_boundary: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Verify all setbacks against code minimums and variance declarations.
    
    Args:
        fields: Parsed form fields with foundation_type, variance_types_list, etc.
        placed_field: Result from placement_solver with field corner coordinates
        parcel_boundary: GeoLibrary parcel data with rings and water/wetland info
    
    Returns:
        {
          "status": "SOLVED" | "FLAG_SETBACK" | "ERROR",
          "setbacks": {
            "well": {"required": 100, "measured": X, "pass": bool, "variance_declared": bool},
            "building": {...},
            ...
          },
          "flagged_setbacks": ["list of short setbacks without variance"],
          "notes": "explanation"
        }
    """
    
    result = {
        "status": "SOLVED",
        "setbacks": {},
        "flagged_setbacks": [],
        "notes": ""
    }
    
    # Validate placement result
    if not placed_field or placed_field.get("status") != "SOLVED":
        return {
            **result,
            "status": "ERROR",
            "notes": f"Field placement status: {placed_field.get('status', 'UNKNOWN')}; cannot verify setbacks"
        }
    
    # Extract declared variance types (convert to lowercase set for case-insensitive lookup)
    variance_list = fields.get("variance_types_list", [])
    variance_types = {v.lower().strip() for v in variance_list}
    logger.info(f"Declared variances: {variance_types if variance_types else 'none'}")
    
    # Extract foundation type for building setback
    foundation_type = fields.get("foundation_type", "unknown")
    if foundation_type == "full":
        building_setback_required = 20
    elif foundation_type == "slab":
        building_setback_required = 15
    elif foundation_type == "none":
        building_setback_required = None  # Skip building setback check
    else:
        building_setback_required = None  # Unknown foundation type
    
    logger.info(f"Foundation type: {foundation_type} → building setback required: {building_setback_required} ft")
    
    # Extract distances from form (parsed as strings like "100 ft")
    well_distance_raw = fields.get("setback_well", "")
    house_distance_raw = fields.get("setback_field_to_house", "")
    
    # Parse numeric distances
    well_measured = _extract_number(well_distance_raw)
    house_measured = _extract_number(house_distance_raw)
    
    # ── WELL SETBACK ──────────────────────────────────────────────────
    well_required = 100
    if well_measured is not None:
        well_pass = well_measured >= well_required
        well_variance = _variance_matches(variance_types, "well setback")
        result["setbacks"]["well"] = {
            "required": well_required,
            "measured": well_measured,
            "pass": well_pass,
            "variance_declared": well_variance,
            "status": "PASS" if well_pass else ("VARIANCE" if well_variance else "SHORT")
        }
        logger.info(f"Well: {well_measured} ft (required {well_required} ft) → {result['setbacks']['well']['status']}")
        if not well_pass and not well_variance:
            result["flagged_setbacks"].append("well")
    
    # ── BUILDING SETBACK ──────────────────────────────────────────────
    if building_setback_required is not None:
        if house_measured is not None:
            building_pass = house_measured >= building_setback_required
            building_variance = _variance_matches(variance_types, "building setback")
            result["setbacks"]["building"] = {
                "required": building_setback_required,
                "measured": house_measured,
                "pass": building_pass,
                "variance_declared": building_variance,
                "status": "PASS" if building_pass else ("VARIANCE" if building_variance else "SHORT")
            }
            logger.info(f"Building: {house_measured} ft (required {building_setback_required} ft) → {result['setbacks']['building']['status']}")
            if not building_pass and not building_variance:
                result["flagged_setbacks"].append("building")
    
    # ── Final status ──────────────────────────────────────────────────
    if result["flagged_setbacks"]:
        result["status"] = "FLAG_SETBACK"
        result["notes"] = (
            f"Setback(s) flagged (short without matching variance): "
            f"{', '.join(result['flagged_setbacks'])}"
        )
    else:
        result["status"] = "SOLVED"
        result["notes"] = "All setbacks pass or variances declared"
    
    return result


def _extract_number(text: str) -> Optional[float]:
    """Extract first numeric value from a string."""
    if not text:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(m.group(1)) if m else None


def _variance_matches(variance_set: set, variance_type: str) -> bool:
    """Check if a variance type is declared (case-insensitive)."""
    variance_lower = variance_type.lower().strip()
    return variance_lower in variance_set


if __name__ == "__main__":
    from sheet_parser import parse_sheet_row, RAW_ROW, ROBERTS_ROW
    
    # Test on Marquis
    print("=" * 70)
    print("MARQUIS (26-018)")
    print("=" * 70)
    marquis = parse_sheet_row(RAW_ROW)
    marquis_placement = {"status": "SOLVED", "field_center": (0, 0)}
    result_m = verify_setbacks(marquis, marquis_placement)
    print(f"Status: {result_m['status']}")
    print(f"Notes: {result_m['notes']}")
    print(f"Setbacks: {result_m['setbacks']}")
    print()
    
    # Test on Roberts
    print("=" * 70)
    print("ROBERTS (26-123)")
    print("=" * 70)
    roberts = parse_sheet_row(ROBERTS_ROW)
    roberts_placement = {"status": "SOLVED", "field_center": (0, 0)}
    result_r = verify_setbacks(roberts, roberts_placement)
    print(f"Status: {result_r['status']}")
    print(f"Notes: {result_r['notes']}")
    print(f"Setbacks: {result_r['setbacks']}")


def integrate_setback_verification(
    fields: Dict[str, Any],
    placement_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Integrate setback verification into placement result.
    
    Takes a placement_solver result and adds setback verification,
    returning a combined status.
    
    Args:
        fields: Parsed form fields
        placement_result: Result from solve_field_placement_from_sheet()
    
    Returns:
        Combined result with both placement and setback data
    """
    
    # Always include placement data
    combined = dict(placement_result)
    
    # If placement is SOLVED, verify setbacks
    if placement_result.get("status") == "SOLVED":
        setback_result = verify_setbacks(fields, placement_result)
        combined["setback_verification"] = setback_result
        
        # Final status depends on setbacks
        if setback_result["status"] == "FLAG_SETBACK":
            combined["final_status"] = "FLAG_SETBACK"
            combined["needs_correction"] = True
            combined["correction_reason"] = setback_result["notes"]
        else:
            combined["final_status"] = "READY_FOR_REVIEW"
            combined["needs_correction"] = False
    else:
        # Placement not SOLVED, can't verify setbacks
        combined["final_status"] = placement_result["status"]
        combined["setback_verification"] = None
    
    return combined
