"""Tree species database — ported from the original web app."""

from __future__ import annotations

import json
import re
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


def _normalize_key(value: str) -> str:
    """Lowercase and treat hyphens, underscores, and other separators as spaces."""
    cleaned = re.sub(r"[^a-z0-9]+", " ", value.strip().lower())
    return " ".join(cleaned.split())


def _tokens(value: str) -> set:
    return set(_normalize_key(value).split())


def get_tree_by_id(tree_id: str) -> Optional[Dict[str, Any]]:
    if not tree_id or not str(tree_id).strip():
        return None
    raw = str(tree_id).strip()
    canonical = TREE_ID_ALIASES.get(raw, TREE_ID_ALIASES.get(raw.lower(), raw))
    canonical_key = _normalize_key(canonical)
    for tree in TREE_TYPES:
        if tree["id"] == canonical or _normalize_key(tree["id"]) == canonical_key:
            return tree
    return None


def get_tree_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Look up a species by common name, id, or scientific name.

    Matching is case-insensitive. Aliases such as "Maple" resolve first.
    A non-exact query matches only when every word is a whole word of the
    species name or id, and only when that match is unique. Substring
    matches like "ash" inside "cashew" are not used.
    """
    if name is None:
        return None
    raw = str(name).strip()
    if not raw:
        return None

    key = _normalize_key(raw)
    alias_candidates = (
        raw.lower(),
        key,
        key.replace(" ", "-"),
        key.replace(" ", "_"),
    )
    for candidate in alias_candidates:
        alias_id = TREE_ID_ALIASES.get(candidate)
        if alias_id:
            found = get_tree_by_id(alias_id)
            if found:
                return found

    for tree in TREE_TYPES:
        if _normalize_key(tree["name"]) == key or _normalize_key(tree["id"]) == key:
            return tree
    for tree in TREE_TYPES:
        if _normalize_key(tree.get("scientificName") or "") == key:
            return tree

    query = _tokens(raw)
    if not query:
        return None
    matches = [
        tree
        for tree in TREE_TYPES
        if query <= (_tokens(tree["name"]) | _tokens(tree["id"]))
    ]
    if not matches:
        return None

    def rank(tree: Dict[str, Any]):
        extra = len(_tokens(tree["name"]) - query)
        starts = 0 if _normalize_key(tree["name"]).startswith(key) else 1
        return (extra, starts, len(tree["name"]), tree["id"])

    matches.sort(key=rank)
    best = matches[0]
    if sum(1 for tree in matches if rank(tree) == rank(best)) > 1:
        return None
    return best


def list_tree_names() -> List[str]:
    return [t["name"] for t in TREE_TYPES]
