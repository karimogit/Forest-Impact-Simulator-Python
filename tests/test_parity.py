"""Parity checks against the original Forest Impact Simulator formulas."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from forest_impact import ForestImpactSimulator, format_area
from forest_impact.growth import (
    calculate_clear_cutting_carbon,
    calculate_cumulative_planting_carbon,
    get_planting_growth_factor,
)
from forest_impact.planting import calculate_region_area, calculate_planting_timeline
from forest_impact.tree_types import get_tree_by_name


def test_growth_curve_matches_documented_factors():
    assert get_planting_growth_factor(1) == 0.05
    assert get_planting_growth_factor(5) == 0.70
    assert get_planting_growth_factor(8) == 0.80
    assert get_planting_growth_factor(15) == 0.90
    assert get_planting_growth_factor(25) == 1.00


def test_oak_carbon_rates():
    oak = get_tree_by_name("Oak")
    assert oak is not None
    assert oak["carbonSequestration"] == 22
    assert oak["biodiversityValue"] == 5
    assert oak["resilienceScore"] == 4


def test_pine_and_eucalyptus_rates_match_original():
    assert get_tree_by_name("Pine")["carbonSequestration"] == 18
    assert get_tree_by_name("Eucalyptus")["carbonSequestration"] == 35
    assert get_tree_by_name("Coast Redwood")["carbonSequestration"] == 45


def test_cumulative_planting_carbon():
    # 1 tree @ 22 kg mature, 50 years
    total = calculate_cumulative_planting_carbon(22.0, 50)
    # Sum of factors: 0.05+0.15+0.30+0.50+0.70 + 5*0.80 + 10*0.90 + 30*1.00
    expected_factor_sum = 0.05 + 0.15 + 0.30 + 0.50 + 0.70 + 5 * 0.80 + 10 * 0.90 + 30 * 1.00
    assert abs(total - 22.0 * expected_factor_sum) < 1e-6


def test_clear_cutting_carbon_positive():
    result = calculate_clear_cutting_carbon(22.0, tree_age=20, simulation_years=10)
    assert result["immediate"] > 0
    assert result["lost_future"] > 0
    assert abs(result["total"] - (result["immediate"] + result["lost_future"])) < 1e-9


def test_sample_scenario_belarus_oaks():
    sim = ForestImpactSimulator()
    result = sim.simulate(
        trees=["Oak"],
        total_trees=69632,
        area_hectares=111.41,
        years=50,
        mode="planting",
        latitude=52.54243289988875,
        longitude=30.863468844692903,
        temperature=21,
        spacing_meters=4,
    )
    mature = 69632 * 22
    expected_total = calculate_cumulative_planting_carbon(mature, 50)
    assert abs(result["impactResults"]["totalCarbon"] - expected_total) < 1.0
    assert abs(result["impactResults"]["carbonSequestration"] - expected_total / 50) < 1.0
    # Biodiversity / resilience on 1-5 scale, not 0-100
    assert 0 <= result["impactResults"]["biodiversityImpact"] <= 5
    assert 0 <= result["impactResults"]["forestResilience"] <= 5
    # Water / air are percentages
    assert 0 <= result["impactResults"]["waterRetention"] <= 95
    assert 0 <= result["impactResults"]["airQualityImprovement"] <= 95


def test_format_area_large_region():
    assert format_area(0.5) == "5000 m²"
    assert format_area(12.34) == "12.3 hectares"
    assert "km²" in format_area(111.41)
    assert format_area(111.41).startswith("111 ")


def test_region_area_positive():
    area = calculate_region_area({
        "north": 52.546295697522886,
        "south": 52.53857010225461,
        "east": 30.873091485235967,
        "west": 30.85384620414984,
    })
    assert area > 50  # roughly ~100 ha plot


def test_planting_timeline_large_scale():
    timeline = calculate_planting_timeline(69632)
    assert timeline["project_scale"].startswith("Large-scale")
    assert timeline["years_to_complete"] >= 1


def test_maple_alias():
    maple = get_tree_by_name("Maple")
    assert maple is not None
    assert maple["id"] == "sugar_maple"


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"OK  {fn.__name__}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
    sys.exit(1 if failed else 0)
