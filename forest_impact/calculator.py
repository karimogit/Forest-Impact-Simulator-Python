"""Core impact calculator aligned with ForestImpactCalculator.tsx."""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Union

from . import constants as C
from .growth import (
    average_annual_from_cumulative,
    calculate_clear_cutting_carbon,
    calculate_cumulative_planting_carbon,
    calculate_period_average_impact,
)
from .planting import TREE_SPACING_CONFIGS, calculate_planting_timeline, format_area, get_recommended_spacing
from .tree_types import get_tree_by_id, get_tree_by_name


TreeSpec = Union[str, Dict[str, Any]]


def _require_number(name: str, value: Any, *, minimum: Optional[float] = None) -> Union[int, float]:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    if minimum is not None and number < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    rounded = round(number)
    if abs(number - rounded) <= 1e-9:
        return int(rounded)
    return number


def _require_whole_number(name: str, value: Any, *, minimum: int) -> int:
    number = _require_number(name, value, minimum=minimum)
    if abs(number - round(number)) > 1e-9:
        raise ValueError(f"{name} must be a whole number")
    return int(round(number))


def _normalize_mode(mode: str) -> str:
    key = str(mode or "").strip().lower().replace("_", "-").replace(" ", "-")
    aliases = {
        "planting": "planting",
        "plant": "planting",
        "clear-cutting": "clear-cutting",
        "clearcutting": "clear-cutting",
        "clear-cut": "clear-cutting",
        "clearcut": "clear-cutting",
    }
    try:
        return aliases[key]
    except KeyError as exc:
        raise ValueError("mode must be 'planting' or 'clear-cutting'") from exc


def _normalize_calculation_mode(mode: str) -> str:
    key = str(mode or "").strip().lower().replace("_", "").replace("-", "")
    if key == "perarea":
        return "perArea"
    if key == "pertree":
        return "perTree"
    raise ValueError("calculation_mode must be 'perArea' or 'perTree'")


def _parse_optional_number(value: Any) -> Optional[float]:
    """Parse a plot field. Missing values are None; present non-numbers raise."""
    if value is None or value == "":
        return None
    if isinstance(value, str) and value.strip().lower() in {"nan", "none", "null"}:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Expected a number, got {value!r}") from exc
    if not math.isfinite(number):
        return None
    return number


def _unknown_tree(name: str) -> Dict[str, Any]:
    label = name.strip() or "Other"
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") or "other"
    tree_id = slug if get_tree_by_id(slug) is None else f"other-{slug}"
    return {
        "id": tree_id,
        "name": label,
        "scientificName": "Unknown species",
        "carbonSequestration": 18.0,
        "biodiversityValue": 3.0,
        "resilienceScore": 3.0,
    }


def _resolve_tree(spec: TreeSpec) -> Dict[str, Any]:
    if isinstance(spec, dict) and "carbonSequestration" in spec:
        return spec
    name = spec if isinstance(spec, str) else spec.get("name") or spec.get("tree_type")
    tree = get_tree_by_name(str(name)) if name else None
    if tree:
        return tree
    return _unknown_tree(str(name or "Other"))


def _species_key(tree: Dict[str, Any]):
    return tree.get("id") or tree.get("name") or id(tree)


def _unique_species(trees: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    unique: List[Dict[str, Any]] = []
    seen = set()
    for tree in trees:
        key = _species_key(tree)
        if key in seen:
            continue
        seen.add(key)
        unique.append(tree)
    return unique


class ForestImpactSimulator:
    """Simulate planting / clear-cutting impacts using the original web-app formulas."""

    def __init__(self):
        self.version = C.SIMULATOR_VERSION

    def weighted_bases(
        self,
        trees: Sequence[TreeSpec],
        percentages: Optional[Dict[str, float]] = None,
    ) -> Dict[str, float]:
        resolved = _unique_species([_resolve_tree(t) for t in trees])
        if not resolved:
            return {"carbon": 0.0, "biodiversity": 0.0, "resilience": 0.0}

        if percentages:
            def _percentage(tree: Dict[str, Any]) -> float:
                value = percentages.get(tree["id"], percentages.get(tree["name"], 0))
                if value is None or value == "":
                    return 0.0
                return float(value)

            total_pct = sum(_percentage(t) for t in resolved)
            if abs(total_pct - 100) < 0.01:
                carbon = biodiversity = resilience = 0.0
                for t in resolved:
                    w = _percentage(t) / 100.0
                    carbon += t["carbonSequestration"] * w
                    biodiversity += t["biodiversityValue"] * w
                    resilience += t["resilienceScore"] * w
                return {"carbon": carbon, "biodiversity": biodiversity, "resilience": resilience}

        n = len(resolved)
        return {
            "carbon": sum(t["carbonSequestration"] for t in resolved) / n,
            "biodiversity": sum(t["biodiversityValue"] for t in resolved) / n,
            "resilience": sum(t["resilienceScore"] for t in resolved) / n,
        }

    def calculate_impact(
        self,
        *,
        trees: Sequence[TreeSpec],
        total_trees: int,
        years: int,
        mode: str = "planting",
        latitude: float = 0.0,
        soil_carbon: Optional[float] = None,
        precipitation: Optional[float] = None,
        temperature: Optional[float] = None,
        percentages: Optional[Dict[str, float]] = None,
        calculation_mode: str = "perArea",
    ) -> Dict[str, float]:
        bases = self.weighted_bases(trees, percentages)
        carbon_base = bases["carbon"]
        biodiversity_base = bases["biodiversity"]
        resilience_base = bases["resilience"]

        if soil_carbon is not None:
            carbon_base += soil_carbon * C.CARBON_CONVERSION["SOIL_CARBON_MODIFIER"]
        if precipitation is not None:
            resilience_base += precipitation * C.ENVIRONMENTAL_MODIFIERS["PRECIPITATION_TO_RESILIENCE"]

        multiplier = total_trees if calculation_mode == "perArea" else 1
        carbon_sequestration = max(0.0, carbon_base * multiplier)

        if mode == "planting":
            biodiversity_time = min(1.0, years * C.IMPACT_CAPS["BIODIVERSITY_TIME_BONUS"])
            resilience_time = min(1.0, years * C.IMPACT_CAPS["RESILIENCE_TIME_BONUS"])
            size_bonus = min(1.0, math.log10(max(total_trees, 1)) * 0.2) if calculation_mode == "perArea" else 0.0
        else:
            biodiversity_time = max(-1.0, -years * C.IMPACT_CAPS["BIODIVERSITY_TIME_BONUS"])
            resilience_time = max(-1.0, -years * C.IMPACT_CAPS["RESILIENCE_TIME_BONUS"])
            size_bonus = -min(1.0, math.log10(max(total_trees, 1)) * 0.2) if calculation_mode == "perArea" else 0.0

        biodiversity = min(
            C.IMPACT_CAPS["MAX_BIODIVERSITY"],
            max(C.IMPACT_CAPS["MIN_BIODIVERSITY"], biodiversity_base + biodiversity_time + size_bonus),
        )
        resilience = min(
            C.IMPACT_CAPS["MAX_RESILIENCE"],
            max(C.IMPACT_CAPS["MIN_RESILIENCE"], resilience_base + resilience_time + size_bonus),
        )

        # Water retention (%)
        if precipitation is None:
            abs_lat = abs(latitude)
            water_base = 85 if abs_lat < 30 else (75 if abs_lat < 60 else 70)
        else:
            precip_bonus = 15 if precipitation > 1500 else (10 if precipitation > 1000 else (5 if precipitation > 500 else 0))
            water_base = max(60, min(90, 70 + precip_bonus))

        if mode == "planting":
            water_time = years * C.WATER_RETENTION["ANNUAL_IMPROVEMENT"]
            water_size = min(10, math.log10(max(total_trees, 1)) * 2) if calculation_mode == "perArea" else 0
        else:
            water_time = -years * C.WATER_RETENTION["ANNUAL_DEGRADATION"]
            water_size = -min(15, math.log10(max(total_trees, 1)) * 3) if calculation_mode == "perArea" else 0

        water_retention = min(
            C.WATER_RETENTION["MAX_RETENTION"],
            max(0.0, water_base + water_time + water_size),
        )

        # Air quality (%)
        if temperature is None or precipitation is None:
            abs_lat = abs(latitude)
            air_base = 70 if abs_lat < 30 else (60 if abs_lat < 60 else 50)
        else:
            temp_bonus = 5 if temperature > 20 else (0 if temperature > 10 else -5)
            precip_bonus = 3 if precipitation > 1000 else (0 if precipitation > 500 else -3)
            air_base = max(40, min(80, 60 + temp_bonus + precip_bonus))

        if mode == "planting":
            air_time = years * C.AIR_QUALITY["ANNUAL_IMPROVEMENT"]
            air_size = min(15, math.log10(max(total_trees, 1)) * 3) if calculation_mode == "perArea" else 0
            air_quality = min(C.AIR_QUALITY["MAX_IMPROVEMENT"], max(0.0, air_base + air_time + air_size))
        else:
            immediate = min(30, math.log10(max(total_trees, 1)) * 5) if calculation_mode == "perArea" else 10
            air_quality = max(
                C.AIR_QUALITY["MAX_DEGRADATION"],
                -(immediate + years * C.AIR_QUALITY["ANNUAL_DEGRADATION"]),
            )

        return {
            "carbon_sequestration_mature_kg_co2_year": carbon_sequestration,
            "biodiversity_impact": biodiversity,
            "forest_resilience": resilience,
            "water_retention_percent": water_retention,
            "air_quality_improvement_percent": air_quality,
        }

    def calculate_social_impact(
        self,
        *,
        mode: str,
        years: int,
        area_hectares: float,
        num_species: int,
    ) -> float:
        if mode == "planting":
            score = C.SOCIAL_IMPACT["PLANTING_BASE_SCORE"]
            diversity = min(num_species * C.SOCIAL_IMPACT["TREE_DIVERSITY_MULTIPLIER"], C.SOCIAL_IMPACT["MAX_DIVERSITY_BONUS"]) if num_species > 1 else 0
            time_b = min(years * C.SOCIAL_IMPACT["TIME_MULTIPLIER_PLANTING"], C.SOCIAL_IMPACT["MAX_TIME_BONUS"])
            area_b = min(area_hectares * C.SOCIAL_IMPACT["AREA_MULTIPLIER_PLANTING"], C.SOCIAL_IMPACT["MAX_AREA_BONUS"])
            return min(score + diversity + time_b + area_b, C.SOCIAL_IMPACT["MAX_SCORE"])
        score = C.SOCIAL_IMPACT["CLEAR_CUTTING_BASE_SCORE"]
        diversity = min(num_species * C.SOCIAL_IMPACT["TREE_DIVERSITY_PENALTY"], 0.5) if num_species > 1 else 0
        time_p = min(years * C.SOCIAL_IMPACT["TIME_MULTIPLIER_CLEARING"], 0.5)
        area_p = min(area_hectares * C.SOCIAL_IMPACT["AREA_MULTIPLIER_CLEARING"], 0.5)
        return max(score - diversity - time_p - area_p, C.SOCIAL_IMPACT["MIN_SCORE"])

    def calculate_land_use_impact(
        self,
        *,
        mode: str,
        years: int,
        area_hectares: float,
    ) -> Dict[str, float]:
        L = C.LAND_USE_IMPACT
        if mode == "planting":
            return {
                "erosion_change_percent": min(area_hectares * L["EROSION_AREA_FACTOR"], L["MAX_PERCENTAGE"]),
                "soil_change_percent": min(years * L["SOIL_TIME_FACTOR"], L["MAX_DEGRADATION"]),
                "habitat_change_percent": min(area_hectares * L["HABITAT_AREA_FACTOR"], 90),
                "water_quality_change_percent": min(years * L["WATER_TIME_FACTOR"], 85),
            }
        return {
            "erosion_change_percent": min(area_hectares * L["EROSION_AREA_FACTOR_CLEARING"], L["MAX_PERCENTAGE"]),
            "soil_change_percent": min(years * L["SOIL_TIME_FACTOR_CLEARING"], L["MAX_DEGRADATION"]),
            "habitat_change_percent": min(area_hectares * L["HABITAT_AREA_FACTOR_CLEARING"], 90),
            "water_quality_change_percent": min(years * L["WATER_TIME_FACTOR_CLEARING"], 85),
        }

    def real_world_comparisons(self, total_carbon_kg: float) -> Dict[str, float]:
        return {
            "car_years": total_carbon_kg / C.COMPARISON_FACTORS["CAR_EMISSIONS_PER_YEAR"],
            "ny_london_flights": total_carbon_kg / C.COMPARISON_FACTORS["FLIGHT_NY_LONDON"],
            "household_electricity_years": total_carbon_kg / C.COMPARISON_FACTORS["HOUSEHOLD_ELECTRICITY_PER_YEAR"],
        }

    def simulate(
        self,
        *,
        trees: Sequence[TreeSpec],
        total_trees: int,
        area_hectares: float,
        years: int = 50,
        mode: str = "planting",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        region: Optional[Dict[str, float]] = None,
        soil_carbon: Optional[float] = None,
        soil_ph: Optional[float] = None,
        soil_texture: Optional[str] = None,
        temperature: Optional[float] = None,
        precipitation: Optional[float] = None,
        percentages: Optional[Dict[str, float]] = None,
        spacing_meters: Optional[float] = None,
        average_tree_age: int = 20,
        calculation_mode: str = "perArea",
    ) -> Dict[str, Any]:
        mode = _normalize_mode(mode)
        calculation_mode = _normalize_calculation_mode(calculation_mode)
        years = _require_whole_number("years", years, minimum=1)
        total_trees = _require_number("total_trees", total_trees, minimum=0)
        area_hectares = _require_number("area_hectares", area_hectares, minimum=0)
        average_tree_age = _require_whole_number("average_tree_age", average_tree_age, minimum=0)
        if latitude is not None:
            latitude = _require_number("latitude", latitude)
            if not -90 <= latitude <= 90:
                raise ValueError("latitude must be between -90 and 90")
        if longitude is not None:
            longitude = _require_number("longitude", longitude)
            if not -180 <= longitude <= 180:
                raise ValueError("longitude must be between -180 and 180")
        if spacing_meters is not None:
            spacing_meters = _require_number("spacing_meters", spacing_meters)
            if spacing_meters <= 0:
                raise ValueError("spacing_meters must be positive")
        if soil_carbon is not None:
            soil_carbon = _require_number("soil_carbon", soil_carbon)
        if soil_ph is not None:
            soil_ph = _require_number("soil_ph", soil_ph)
        if temperature is not None:
            temperature = _require_number("temperature", temperature)
        if precipitation is not None:
            precipitation = _require_number("precipitation", precipitation)

        lat = latitude if latitude is not None else 0.0
        resolved = [_resolve_tree(t) for t in trees]
        species = _unique_species(resolved)
        density = (total_trees / area_hectares) if area_hectares > 0 else 0.0
        spacing = spacing_meters if spacing_meters is not None else (
            math.sqrt(10_000 / density) if density > 0 else 0.0
        )

        impact = self.calculate_impact(
            trees=resolved,
            total_trees=total_trees,
            years=years,
            mode=mode,
            latitude=lat,
            soil_carbon=soil_carbon,
            precipitation=precipitation,
            temperature=temperature,
            percentages=percentages,
            calculation_mode=calculation_mode,
        )

        mature_annual = impact["carbon_sequestration_mature_kg_co2_year"]

        if mode == "planting":
            total_carbon = calculate_cumulative_planting_carbon(mature_annual, years)
            clear_cut = None
            # Period-average annual (web UI): total / years
            annual_displayed = average_annual_from_cumulative(total_carbon, years)
        else:
            # perArea mature rate is already stand-wide; divide back to a per-tree rate
            # before the clear-cut curve, then scale the result. perTree is already per tree.
            if calculation_mode == "perArea" and total_trees:
                per_tree_rate = mature_annual / total_trees
                scale = total_trees
            else:
                per_tree_rate = mature_annual
                scale = 1
            clear_cut = calculate_clear_cutting_carbon(per_tree_rate, average_tree_age, years)
            clear_cut = {k: v * scale for k, v in clear_cut.items()}
            total_carbon = clear_cut["total"]
            annual_displayed = average_annual_from_cumulative(total_carbon, years)

        timeline = calculate_planting_timeline(total_trees)
        social = self.calculate_social_impact(
            mode=mode, years=years, area_hectares=area_hectares, num_species=len(species)
        )
        land_use = self.calculate_land_use_impact(mode=mode, years=years, area_hectares=area_hectares)
        comparisons = self.real_world_comparisons(total_carbon)

        if not species:
            tree_percentages: Dict[str, float] = {}
        elif percentages:
            tree_percentages = {}
            for key, value in percentages.items():
                tree_percentages[str(key)] = float(_require_number("percentage", value))
        else:
            share = 100.0 / len(species)
            tree_percentages = {t["id"]: share for t in species}

        return {
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "simulatorVersion": self.version,
                "location": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "region": region,
                },
                "simulation": {
                    "mode": mode,
                    "years": years,
                    "selectedTrees": species,
                    "treePercentages": tree_percentages,
                    "averageTreeAge": average_tree_age if mode == "clear-cutting" else None,
                },
            },
            "environmentalData": {
                "soil": {
                    "carbon": soil_carbon,
                    "ph": soil_ph,
                    "texture": soil_texture,
                },
                "climate": {
                    "temperature": temperature,
                    "precipitation": precipitation,
                },
            },
            "impactResults": {
                "carbonSequestration": annual_displayed,
                "biodiversityImpact": impact["biodiversity_impact"],
                "forestResilience": impact["forest_resilience"],
                "waterRetention": impact["water_retention_percent"],
                "airQualityImprovement": impact["air_quality_improvement_percent"],
                "totalCarbon": total_carbon,
                "averageBiodiversity": calculate_period_average_impact(impact["biodiversity_impact"], years),
                "averageResilience": calculate_period_average_impact(impact["forest_resilience"], years),
                "matureAnnualCarbon": mature_annual,
                "clearCuttingBreakdown": clear_cut,
            },
            "plantingData": {
                "area": area_hectares,
                "areaFormatted": format_area(area_hectares),
                "totalTrees": total_trees,
                "spacing": round(spacing, 2) if spacing else None,
                "density": round(density),
                "timeline": {
                    "yearsToComplete": timeline["years_to_complete"],
                    "treesPerSeason": timeline["trees_per_season"],
                    "projectScale": timeline["project_scale"],
                    "recommendedApproach": timeline["recommended_approach"],
                },
            },
            "socialImpact": social,
            "landUseImpact": land_use,
            "comparisons": comparisons,
        }

    def simulate_from_plots(
        self,
        plots: List[Dict[str, Any]],
        *,
        years: int = 50,
        mode: str = "planting",
        average_tree_age: int = 20,
        temperature: Optional[float] = None,
        precipitation: Optional[float] = None,
        soil_carbon: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Aggregate multi-plot CSV-style inputs into one simulation."""
        if not plots:
            raise ValueError("No plots provided")

        total_area = 0.0
        total_trees = 0
        counts_by_name: Dict[str, int] = {}
        unique_trees: List[str] = []
        for p in plots:
            name = str(p.get("tree_type") or p.get("tree_names") or "Oak").strip() or "Oak"
            area = _parse_optional_number(p.get("area", p.get("area_hectares"))) or 0.0
            if area < 0:
                raise ValueError("plot area must be >= 0")
            count_value = _parse_optional_number(p.get("tree_count", p.get("total_trees")))
            density_value = _parse_optional_number(p.get("tree_density", p.get("density_trees_hectare")))
            if count_value is not None and count_value < 0:
                raise ValueError("tree_count must be >= 0")
            if density_value is not None and density_value < 0:
                raise ValueError("tree_density must be >= 0")
            count = int(math.floor(count_value)) if count_value and count_value > 0 else 0
            density = density_value if density_value and density_value > 0 else 0.0
            if count <= 0 and density > 0 and area > 0:
                count = int(math.floor(area * density))
            if count <= 0 and area > 0:
                tree = get_tree_by_name(name)
                spacing_name = tree["name"] if tree else name
                spacing_key = get_recommended_spacing(spacing_name)
                count = int(math.floor(area * TREE_SPACING_CONFIGS[spacing_key]["density"]))
            total_area += area
            total_trees += count
            if name not in counts_by_name:
                unique_trees.append(name)
                counts_by_name[name] = 0
            counts_by_name[name] += count

        lat = next((p.get("latitude") for p in plots if p.get("latitude") not in (None, "")), None)
        lon = next((p.get("longitude") for p in plots if p.get("longitude") not in (None, "")), None)
        lat = _parse_optional_number(lat)
        lon = _parse_optional_number(lon)

        percentages = None
        if total_trees > 0 and unique_trees:
            percentages = {}
            for name in unique_trees:
                tree = get_tree_by_name(name)
                key = tree["id"] if tree else _unknown_tree(name)["id"]
                percentages[key] = percentages.get(key, 0.0) + (100.0 * counts_by_name[name] / total_trees)

        return self.simulate(
            trees=unique_trees,
            total_trees=total_trees,
            area_hectares=total_area,
            years=years,
            mode=mode,
            latitude=lat,
            longitude=lon,
            soil_carbon=soil_carbon,
            temperature=temperature,
            precipitation=precipitation,
            percentages=percentages,
            average_tree_age=average_tree_age,
        )
