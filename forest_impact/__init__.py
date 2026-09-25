"""Forest Impact Simulator — Python port of the original web app calculations.

Aligned with https://github.com/karimogit/Forest-Impact-Simulator
"""

from .calculator import ForestImpactSimulator
from .planting import calculate_region_area, calculate_planting_timeline, format_area
from .tree_types import TREE_TYPES, get_tree_by_id, get_tree_by_name

__version__ = "1.1.0"

__all__ = [
    "ForestImpactSimulator",
    "TREE_TYPES",
    "get_tree_by_id",
    "get_tree_by_name",
    "calculate_region_area",
    "calculate_planting_timeline",
    "format_area",
    "__version__",
]
