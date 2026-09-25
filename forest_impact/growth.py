"""Growth-curve and clear-cutting carbon helpers — mirrored from treeCalculations.ts."""

from __future__ import annotations

from typing import Dict

from .constants import TREE_AGE_GROWTH_FACTORS, TREE_GROWTH_FACTORS


def get_planting_growth_factor(year: int) -> float:
    """Planting-mode growth factor for a given simulation year."""
    if year <= 1:
        return TREE_GROWTH_FACTORS["YEAR_1"]
    if year == 2:
        return TREE_GROWTH_FACTORS["YEAR_2"]
    if year == 3:
        return TREE_GROWTH_FACTORS["YEAR_3"]
    if year == 4:
        return TREE_GROWTH_FACTORS["YEAR_4"]
    if year == 5:
        return TREE_GROWTH_FACTORS["YEAR_5"]
    if year <= 10:
        return TREE_GROWTH_FACTORS["YEAR_6_TO_10"]
    if year <= 20:
        return TREE_GROWTH_FACTORS["YEAR_11_TO_20"]
    return TREE_GROWTH_FACTORS["YEAR_20_PLUS"]


def get_age_growth_factor(age: int) -> float:
    """Growth factor based on existing tree age (clear-cutting)."""
    if age <= 1:
        return TREE_AGE_GROWTH_FACTORS["AGE_1"]
    if age <= 2:
        return TREE_AGE_GROWTH_FACTORS["AGE_2"]
    if age <= 3:
        return TREE_AGE_GROWTH_FACTORS["AGE_3"]
    if age <= 4:
        return TREE_AGE_GROWTH_FACTORS["AGE_4"]
    if age <= 5:
        return TREE_AGE_GROWTH_FACTORS["AGE_5"]
    if age <= 6:
        return TREE_AGE_GROWTH_FACTORS["AGE_6"]
    if age <= 20:
        return TREE_AGE_GROWTH_FACTORS["AGE_7_TO_20"]
    if age <= 50:
        return TREE_AGE_GROWTH_FACTORS["AGE_21_TO_50"]
    return TREE_AGE_GROWTH_FACTORS["AGE_50_PLUS"]


def calculate_annual_carbon_with_growth(mature_rate: float, year: int) -> float:
    return mature_rate * get_planting_growth_factor(year)


def calculate_cumulative_planting_carbon(
    mature_annual_rate: float,
    years: int,
    growth_modifier: float = 1.0,
) -> float:
    """Sum annual sequestration over the simulation with the planting growth curve."""
    total = 0.0
    for year in range(1, years + 1):
        total += mature_annual_rate * get_planting_growth_factor(year) * growth_modifier
    return total


def calculate_clear_cutting_carbon(
    mature_rate: float,
    tree_age: int,
    simulation_years: int,
) -> Dict[str, float]:
    """Immediate release (stored lifetime carbon) + lost future sequestration."""
    immediate = sum(
        mature_rate * get_age_growth_factor(year) for year in range(1, tree_age + 1)
    )
    lost_future = sum(
        mature_rate * get_age_growth_factor(tree_age + year)
        for year in range(1, simulation_years + 1)
    )
    return {
        "immediate": immediate,
        "lost_future": lost_future,
        "total": immediate + lost_future,
    }


def average_annual_from_cumulative(total_carbon: float, years: int) -> float:
    """Period-average annual carbon (matches web UI labeling)."""
    if years <= 0:
        return 0.0
    return total_carbon / years
