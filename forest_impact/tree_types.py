"""Tree species database — ported from the original web app."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

_DATA_PATH = Path(__file__).with_name("tree_types_data.json")

with _DATA_PATH.open(encoding="utf-8") as f:
    TREE_TYPES: List[Dict[str, Any]] = json.load(f)

TREE_ID_ALIASES = {
    "maple": "sugar_maple",
    "tulip-tree": "tulip_poplar",
    "redwood": "redwood",  # Coast Redwood id
}


def get_tree_by_id(tree_id: str) -> Optional[Dict[str, Any]]:
    canonical = TREE_ID_ALIASES.get(tree_id, tree_id)
    for tree in TREE_TYPES:
        if tree["id"] == canonical:
            return tree
    return None


def get_tree_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Look up by common name (case-insensitive). Also accepts aliases like Maple."""
    if not name:
        return None
    key = name.strip().lower()
    alias_id = TREE_ID_ALIASES.get(key)
    if alias_id:
        found = get_tree_by_id(alias_id)
        if found:
            return found
    for tree in TREE_TYPES:
        if tree["name"].lower() == key or tree["id"].lower() == key:
            return tree
    # Partial match as last resort (e.g. "Redwood" -> "Coast Redwood")
    for tree in TREE_TYPES:
        if key in tree["name"].lower() or key in tree["id"].lower():
            return tree
    return None


def list_tree_names() -> List[str]:
    return [t["name"] for t in TREE_TYPES]
