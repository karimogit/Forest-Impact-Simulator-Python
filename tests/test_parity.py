"""Parity checks against the original Forest Impact Simulator formulas."""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from forest_impact import ForestImpactSimulator, format_area
from forest_impact.export import generate_geojson, generate_json
from forest_impact.growth import (
    calculate_clear_cutting_carbon,
    calculate_cumulative_planting_carbon,
    calculate_period_average_impact,
    get_planting_growth_factor,
)
from forest_impact.planting import calculate_region_area, calculate_planting_timeline, calculate_tree_planting, get_recommended_spacing
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


def test_species_lookup_uses_whole_words_and_scientific_names():
    assert get_tree_by_name("a") is None
    assert get_tree_by_name("Ash")["id"] == "ash"
    assert get_tree_by_name("Cashew")["id"] == "cashew"
    assert get_tree_by_name("Quercus robur")["id"] == "oak"
    assert get_tree_by_name("tulip tree")["id"] == "tulip_poplar"
    assert get_tree_by_name("unslash") is None


def test_spacing_terms_do_not_match_inside_other_words():
    assert get_recommended_spacing("unslash") == "standard"
    assert get_recommended_spacing("Cashew") == "dense"
    assert get_recommended_spacing("Douglas Fir") == "veryWide"
    assert get_recommended_spacing("Oak") == "wide"
    assert get_recommended_spacing("Slash Pine") == "wide"


def test_period_average_biodiversity_uses_growth_curve():
    sim = ForestImpactSimulator()
    result = sim.simulate(
        trees=["Oak"],
        total_trees=1,
        area_hectares=1,
        years=1,
        mode="planting",
        calculation_mode="perTree",
    )
    impact = result["impactResults"]
    assert impact["biodiversityImpact"] == 5
    assert abs(impact["averageBiodiversity"] - calculate_period_average_impact(5, 1)) < 1e-9
    assert abs(impact["averageBiodiversity"] - 0.5) < 1e-9
    assert abs(impact["averageResilience"] - impact["forestResilience"] * 0.10) < 1e-9


def test_clear_cutting_per_tree_is_not_divided_by_stand_size():
    sim = ForestImpactSimulator()
    result = sim.simulate(
        trees=["Oak"],
        total_trees=100,
        area_hectares=1,
        years=10,
        mode="clear-cutting",
        calculation_mode="perTree",
        average_tree_age=20,
    )
    expected = calculate_clear_cutting_carbon(22.0, 20, 10)
    breakdown = result["impactResults"]["clearCuttingBreakdown"]
    assert abs(breakdown["total"] - expected["total"]) < 1e-6
    assert abs(breakdown["immediate"] - expected["immediate"]) < 1e-6

    stand = sim.simulate(
        trees=["Oak"],
        total_trees=100,
        area_hectares=1,
        years=10,
        mode="clear-cutting",
        calculation_mode="perArea",
        average_tree_age=20,
    )
    assert abs(stand["impactResults"]["totalCarbon"] - expected["total"] * 100) < 1e-4


def test_mixed_plots_are_weighted_by_tree_count():
    sim = ForestImpactSimulator()
    result = sim.simulate_from_plots([
        {"area": 1, "tree_type": "Oak", "tree_count": 100},
        {"area": 1, "tree_type": "Eucalyptus", "tree_count": 300},
    ], years=1)
    expected = (100 * 22 + 300 * 35) / 400
    assert abs(result["impactResults"]["matureAnnualCarbon"] - expected * 400) < 1e-6
    percentages = result["metadata"]["simulation"]["treePercentages"]
    assert abs(percentages["oak"] - 25) < 1e-9
    assert abs(percentages["eucalyptus"] - 75) < 1e-9


def test_duplicate_species_do_not_inflate_social_score():
    sim = ForestImpactSimulator()
    single = sim.simulate(trees=["Oak"], total_trees=10, area_hectares=1, years=1)
    duplicated = sim.simulate(trees=["Oak", "Oak"], total_trees=10, area_hectares=1, years=1)
    mixed = sim.simulate(trees=["Oak", "Pine"], total_trees=10, area_hectares=1, years=1)
    assert duplicated["socialImpact"] == single["socialImpact"]
    assert mixed["socialImpact"] > single["socialImpact"]


def test_missing_counts_use_species_spacing():
    sim = ForestImpactSimulator()
    oaks = sim.simulate_from_plots([{"area": 2, "tree_type": "Oak"}])
    gums = sim.simulate_from_plots([{"area": 2, "tree_type": "Eucalyptus"}])
    assert oaks["plantingData"]["totalTrees"] == 2 * 625
    assert gums["plantingData"]["totalTrees"] == 2 * 1600


def test_invalid_mode_and_coordinates_raise():
    sim = ForestImpactSimulator()
    try:
        sim.simulate(trees=["Oak"], total_trees=1, area_hectares=1, mode="logging")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    try:
        sim.simulate(trees=["Oak"], total_trees=1, area_hectares=1, latitude=120)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_negative_plot_count_raises():
    sim = ForestImpactSimulator()
    try:
        sim.simulate_from_plots([{"area": 1, "tree_type": "Oak", "tree_count": -5}])
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_plot_count_accepts_decimal_strings():
    sim = ForestImpactSimulator()
    result = sim.simulate_from_plots([
        {"area": "1.5", "tree_type": "Oak", "tree_count": "10.0"},
    ])
    assert result["plantingData"]["totalTrees"] == 10


def test_point_export_has_no_invented_region_and_stays_valid_json():
    sim = ForestImpactSimulator()
    result = sim.simulate(
        trees=["Oak"],
        total_trees=10,
        area_hectares=1,
        latitude=0,
        longitude=0,
        temperature=21,
    )
    assert result["metadata"]["location"]["region"] is None
    payload = json.loads(generate_json(result))
    geo = json.loads(generate_geojson(result))
    assert payload["metadata"]["location"]["latitude"] == 0
    assert geo["features"][0]["geometry"]["coordinates"] == [0, 0]
    assert geo["features"][0]["properties"]["temperature"] == 21
    assert len(geo["features"]) == 1


def test_custom_spacing_must_be_positive():
    try:
        calculate_tree_planting(
            {"north": 1, "south": 0, "east": 1, "west": 0},
            "Oak",
            custom_spacing=0,
        )
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


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
