"""Planting area, spacing, timeline, and display helpers — from treePlanting.ts."""

from __future__ import annotations

import math
from typing import Dict, List, Optional, TypedDict


class RegionBounds(TypedDict):
    north: float
    south: float
    east: float
    west: float


TREE_SPACING_CONFIGS = {
    "dense": {"spacing": 2.5, "density": 1600},
    "standard": {"spacing": 3.0, "density": 1111},
    "wide": {"spacing": 4.0, "density": 625},
    "veryWide": {"spacing": 6.0, "density": 278},
}


def calculate_region_area(bounds: RegionBounds) -> float:
    """Area in hectares from lat/lon bounds (handles antimeridian crossing)."""
    lat_diff = abs(bounds["north"] - bounds["south"])
    raw_lng_diff = bounds["east"] - bounds["west"]
    lng_diff = raw_lng_diff + 360 if raw_lng_diff < 0 else raw_lng_diff

    lat_meters = lat_diff * 111_000
    mid_lat = (bounds["north"] + bounds["south"]) * math.pi / 360
    lng_meters = lng_diff * 111_000 * math.cos(mid_lat)

    area_ha = (lat_meters * lng_meters) / 10_000
    return max(0.0, area_ha)


def format_area(area_hectares: float) -> str:
    """Keep hectares primary; show km² in parentheses for large regions."""
    if area_hectares < 1:
        return f"{area_hectares * 10_000:.0f} m²"
    if area_hectares < 100:
        return f"{area_hectares:.1f} hectares"
    area_km2 = area_hectares / 100
    return f"{area_hectares:.0f} hectares ({area_km2:.1f} km²)"


def get_recommended_spacing(tree_type: str) -> str:
    name = tree_type.lower()
    dense = (
        "eucalyptus", "willow", "poplar", "birch", "bamboo", "papaya",
        "banana", "tulip_poplar", "sycamore", "juniper", "rowan", "olive",
        "fig", "pomegranate", "almond", "carob", "cherry", "avocado",
        "mango", "cashew", "marula", "shea", "sandalwood", "neem", "camphor",
    )
    very_wide = (
        "sequoia", "redwood", "cedar", "baobab", "douglas fir", "monkey puzzle",
    )
    wide = (
        "oak", "maple", "pine", "spruce", "fir", "mahogany", "teak", "beech",
        "ash", "hickory", "black walnut", "white oak", "sugar maple", "linden",
    )
    if any(k in name for k in dense):
        return "dense"
    if any(k in name for k in very_wide):
        return "veryWide"
    if any(k in name for k in wide):
        return "wide"
    return "standard"


def calculate_tree_planting(
    bounds: RegionBounds,
    tree_type: str,
    custom_spacing: Optional[float] = None,
) -> Dict[str, float]:
    area = calculate_region_area(bounds)
    if custom_spacing:
        spacing = custom_spacing
        density = 10_000 / (spacing * spacing)
    else:
        key = get_recommended_spacing(tree_type)
        cfg = TREE_SPACING_CONFIGS[key]
        spacing = cfg["spacing"]
        density = cfg["density"]
    total_trees = math.floor(area * density)
    return {
        "spacing": spacing,
        "density": density,
        "area": area,
        "total_trees": total_trees,
    }


def calculate_planting_timeline(total_trees: int) -> Dict[str, object]:
    if total_trees < 1000:
        project_scale = "Small-scale (Community/Backyard)"
        trees_per_person_per_day, planting_days, people = 50, 30, 2
        approach = "Manual planting with volunteers or small crew"
    elif total_trees < 10_000:
        project_scale = "Medium-scale (Local Restoration)"
        trees_per_person_per_day, planting_days, people = 200, 60, 5
        approach = "Semi-mechanized planting with professional crew"
    elif total_trees < 100_000:
        project_scale = "Large-scale (Commercial Forestry)"
        trees_per_person_per_day, planting_days, people = 500, 90, 10
        approach = "Professional forestry crew with mechanized assistance"
    elif total_trees < 1_000_000:
        project_scale = "Very Large-scale (Regional Restoration)"
        trees_per_person_per_day, planting_days, people = 800, 120, 25
        approach = "Multiple crews with specialized planting equipment"
    else:
        project_scale = "Massive-scale (National/International)"
        trees_per_person_per_day, planting_days, people = 1000, 150, 50
        approach = "Industrial-scale operations with advanced mechanization and multiple teams"

    daily_cap = 200 if total_trees < 100 else (1000 if total_trees < 10_000 else 2000)
    planting_window_days = 30 if total_trees < 100 else (60 if total_trees < 10_000 else 90)
    trees_per_day = min(trees_per_person_per_day * people, daily_cap)
    trees_per_year = trees_per_day * planting_days
    days_to_complete = max(1, math.ceil(total_trees / max(trees_per_day, 1)))
    years_to_complete = max(1, math.ceil(days_to_complete / planting_window_days))
    trees_per_season = math.ceil(total_trees / years_to_complete)

    return {
        "trees_per_year": trees_per_year,
        "years_to_complete": years_to_complete,
        "trees_per_season": trees_per_season,
        "project_scale": project_scale,
        "recommended_approach": approach,
    }


def get_planting_recommendations(area_hectares: float) -> List[str]:
    recommendations: List[str] = []
    if area_hectares < 0.1:
        recommendations.append("Small area - consider container planting or urban forestry")
    elif area_hectares < 1:
        recommendations.append("Medium area - suitable for community gardens or small woodlots")
    elif area_hectares < 10:
        recommendations.append("Large area - suitable for commercial forestry or restoration")
    else:
        recommendations.append("Very large area - consider mixed-species planting for biodiversity")
        recommendations.append("Plan for fire breaks and access roads")
    if area_hectares > 5:
        recommendations.append("Consider phased planting over multiple years")
    return recommendations
