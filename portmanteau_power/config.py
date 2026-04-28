"""
config.py – Load and merge configuration from YAML/JSON file + defaults.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml  # type: ignore
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

from portmanteau_power.themes import DEFAULT_THEMES, ALL_THEME_NAMES

# ---------------------------------------------------------------------------
# Default configuration (used when no file is supplied or as fallback)
# ---------------------------------------------------------------------------

DEFAULT_CONFIG: Dict[str, Any] = {
    "themes": {
        "enabled": DEFAULT_THEMES,
    },
    "scoring": {
        "weights": {
            "ngram": 0.35,
            "wordfreq": 0.20,
            "phoneme": 0.15,
            "seam": 0.15,
            "structure": 0.15,
        },
        "morpheme_bonus": 0.55,
    },
    "constraints": {
        "min_length": 5,
        "max_length": 12,
        "min_syllables": 1,
        "max_syllables": 5,
        "banned_substrings": [],
    },
    "join": {
        "per_root_variants": 70,
        "seed_keep": 2500,
        "join_pool": 450,
        "per_pair_keep": 10,
        "local_window": 45,
        "min_overlap": 2,
        "max_overlap": 6,
        "allow_triples": False,
        "triple_pool": 120,
        "max_per_signature": 3,
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge *override* into a copy of *base*."""
    result = dict(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load config from *path* (YAML or JSON) and deep-merge it over the defaults.
    If *path* is None or the file does not exist, returns the defaults unchanged.
    """
    config = dict(DEFAULT_CONFIG)

    if path is None:
        return config

    p = Path(path)
    if not p.exists():
        return config

    with p.open("r", encoding="utf-8") as fh:
        raw_text = fh.read()

    file_config: Dict[str, Any] = {}
    suffix = p.suffix.lower()
    if suffix in (".yaml", ".yml"):
        if _YAML_AVAILABLE:
            file_config = yaml.safe_load(raw_text) or {}
        else:
            raise RuntimeError(
                "PyYAML is required to load .yaml/.yml config files. "
                "Install it with: pip install pyyaml"
            )
    elif suffix == ".json":
        file_config = json.loads(raw_text) or {}
    else:
        # Try YAML first, then JSON
        if _YAML_AVAILABLE:
            try:
                file_config = yaml.safe_load(raw_text) or {}
            except Exception:
                file_config = json.loads(raw_text)
        else:
            file_config = json.loads(raw_text)

    return _deep_merge(DEFAULT_CONFIG, file_config)


def apply_cli_overrides(
    config: Dict[str, Any],
    *,
    target_size: Optional[int] = None,
    min_len: Optional[int] = None,
    max_len: Optional[int] = None,
    themes: Optional[List[str]] = None,
    per_root_variants: Optional[int] = None,
    per_pair_keep: Optional[int] = None,
    allow_triples: Optional[bool] = None,
    banned_substrings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Apply CLI-level overrides onto an already-loaded config dict (in-place)."""
    if themes is not None:
        # Validate theme names
        unknown = [t for t in themes if t not in ALL_THEME_NAMES]
        if unknown:
            raise ValueError(
                f"Unknown theme(s): {unknown}. "
                f"Available: {ALL_THEME_NAMES}"
            )
        config["themes"]["enabled"] = themes

    if min_len is not None:
        config["constraints"]["min_length"] = min_len
    if max_len is not None:
        config["constraints"]["max_length"] = max_len
    if per_root_variants is not None:
        config["join"]["per_root_variants"] = per_root_variants
    if per_pair_keep is not None:
        config["join"]["per_pair_keep"] = per_pair_keep
    if allow_triples is not None:
        config["join"]["allow_triples"] = allow_triples
    if banned_substrings is not None:
        config["constraints"]["banned_substrings"] = (
            config["constraints"]["banned_substrings"] + banned_substrings
        )
    if target_size is not None:
        config["target_size"] = target_size

    return config
