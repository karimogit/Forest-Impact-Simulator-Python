"""Export helpers matching the original web app CSV / JSON / GeoJSON formats."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List, Optional


CSV_HEADERS = [
    "timestamp", "simulator_version", "simulation_years",
    "latitude", "longitude", "region_north", "region_south", "region_east", "region_west",
    "soil_carbon_g_kg", "soil_ph", "soil_texture", "temperature_c", "precipitation_mm",
    "annual_carbon_sequestration_kg_co2_year", "total_carbon_kg_co2", "biodiversity_impact",
    "forest_resilience", "water_retention_percent", "air_quality_improvement_percent",
    "average_biodiversity", "average_resilience",
    "area_hectares", "total_trees", "spacing_meters", "density_trees_hectare",
    "years_to_complete", "trees_per_season",
    "tree_names", "tree_scientific_names", "tree_carbon_rates_kg_co2_year", "tree_percentages",
]


def _fmt(value: Any, decimals: Optional[int] = None) -> str:
    if value is None:
        return ""
    if decimals is not None and isinstance(value, (int, float)):
        return f"{float(value):.{decimals}f}"
    return str(value)


def results_to_csv_row(data: Dict[str, Any]) -> Dict[str, str]:
    meta = data["metadata"]
    env = data["environmentalData"]
    impact = data["impactResults"]
    planting = data.get("plantingData") or {}
    trees = meta["simulation"]["selectedTrees"]
    percentages = meta["simulation"].get("treePercentages") or {}
    region = (meta.get("location") or {}).get("region") or {}

    return {
        "timestamp": meta["timestamp"],
        "simulator_version": meta["simulatorVersion"],
        "simulation_years": _fmt(meta["simulation"]["years"]),
        "latitude": _fmt(meta["location"].get("latitude")),
        "longitude": _fmt(meta["location"].get("longitude")),
        "region_north": _fmt(region.get("north")),
        "region_south": _fmt(region.get("south")),
        "region_east": _fmt(region.get("east")),
        "region_west": _fmt(region.get("west")),
        "soil_carbon_g_kg": _fmt((env.get("soil") or {}).get("carbon")),
        "soil_ph": _fmt((env.get("soil") or {}).get("ph")),
        "soil_texture": _fmt((env.get("soil") or {}).get("texture")),
        "temperature_c": _fmt((env.get("climate") or {}).get("temperature")),
        "precipitation_mm": _fmt((env.get("climate") or {}).get("precipitation")),
        "annual_carbon_sequestration_kg_co2_year": _fmt(impact["carbonSequestration"], 1),
        "total_carbon_kg_co2": _fmt(impact["totalCarbon"], 1),
        "biodiversity_impact": _fmt(impact["biodiversityImpact"], 1),
        "forest_resilience": _fmt(impact["forestResilience"], 1),
        "water_retention_percent": _fmt(impact["waterRetention"], 0),
        "air_quality_improvement_percent": _fmt(impact["airQualityImprovement"], 0),
        "average_biodiversity": _fmt(impact["averageBiodiversity"], 1),
        "average_resilience": _fmt(impact["averageResilience"], 1),
        "area_hectares": _fmt(planting.get("area"), 2),
        "total_trees": _fmt(planting.get("totalTrees")),
        "spacing_meters": _fmt(planting.get("spacing")),
        "density_trees_hectare": _fmt(planting.get("density"), 0),
        "years_to_complete": _fmt((planting.get("timeline") or {}).get("yearsToComplete")),
        "trees_per_season": _fmt((planting.get("timeline") or {}).get("treesPerSeason")),
        "tree_names": ";".join(t["name"] for t in trees),
        "tree_scientific_names": ";".join(t.get("scientificName", "") for t in trees),
        "tree_carbon_rates_kg_co2_year": ";".join(str(t["carbonSequestration"]) for t in trees),
        "tree_percentages": ";".join(
            str(percentages.get(t["id"], percentages.get(t["name"], 0))) for t in trees
        ),
    }


def generate_csv(data: Dict[str, Any]) -> str:
    row = results_to_csv_row(data)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_HEADERS, lineterminator="\n")
    writer.writeheader()
    writer.writerow({h: row.get(h, "") for h in CSV_HEADERS})
    return buf.getvalue()


def generate_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, indent=2, default=str)


def generate_geojson(data: Dict[str, Any]) -> str:
    features: List[Dict[str, Any]] = []
    loc = data["metadata"]["location"]
    impact = data["impactResults"]
    planting = data.get("plantingData") or {}

    lat, lon = loc.get("latitude"), loc.get("longitude")
    if lat is not None and lon is not None:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "name": "Forest Impact Analysis Point",
                "carbonSequestration": impact["carbonSequestration"],
                "totalCarbon": impact["totalCarbon"],
                "biodiversityImpact": impact["biodiversityImpact"],
                "forestResilience": impact["forestResilience"],
                "waterRetention": impact["waterRetention"],
                "airQualityImprovement": impact["airQualityImprovement"],
                "simulationYears": data["metadata"]["simulation"]["years"],
                "selectedTreeCount": len(data["metadata"]["simulation"]["selectedTrees"]),
                "treeSpecies": ", ".join(t["name"] for t in data["metadata"]["simulation"]["selectedTrees"]),
            },
        })

    region = loc.get("region")
    if region:
        n, s, e, w = region["north"], region["south"], region["east"], region["west"]
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[w, s], [e, s], [e, n], [w, n], [w, s]]],
            },
            "properties": {
                "name": "Forest Planting Region",
                "area": planting.get("area"),
                "totalTrees": planting.get("totalTrees"),
                "spacing": planting.get("spacing"),
                "density": planting.get("density"),
                "yearsToComplete": (planting.get("timeline") or {}).get("yearsToComplete"),
                "treesPerSeason": (planting.get("timeline") or {}).get("treesPerSeason"),
            },
        })

    return json.dumps({
        "type": "FeatureCollection",
        "features": features,
        "properties": {
            "title": "Forest Impact Simulator Export",
            "description": f"Forest impact analysis for {data['metadata']['simulation']['years']} years",
            "timestamp": data["metadata"]["timestamp"],
            "simulatorVersion": data["metadata"]["simulatorVersion"],
        },
    }, indent=2)


def write_exports(data: Dict[str, Any], prefix: str) -> Dict[str, str]:
    paths = {
        "csv": f"{prefix}.csv",
        "json": f"{prefix}.json",
        "geojson": f"{prefix}.geojson",
    }
    with open(paths["csv"], "w", encoding="utf-8") as f:
        f.write(generate_csv(data))
    with open(paths["json"], "w", encoding="utf-8") as f:
        f.write(generate_json(data))
    with open(paths["geojson"], "w", encoding="utf-8") as f:
        f.write(generate_geojson(data))
    return paths
