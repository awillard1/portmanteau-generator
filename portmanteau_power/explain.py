"""
explain.py – Provenance-aware Candidate dataclass + JSONL/TSV output helpers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Candidate:
    """A generated name with its score, breakdown, and provenance."""

    text: str
    score: float

    # Score breakdown (populated by scoring.score_candidate)
    score_breakdown: Dict[str, float] = field(default_factory=dict)

    # Provenance
    components: List[str] = field(default_factory=list)   # roots/morphemes joined
    join_strategy: str = "unknown"                          # overlap | smooth | splice | affix | seed
    affixes_used: List[str] = field(default_factory=list)  # prefix/suffix morphemes applied
    theme_sources: List[str] = field(default_factory=list) # theme names that contributed

    def as_tsv_row(self, include_breakdown: bool = False) -> str:
        if include_breakdown:
            bd = self.score_breakdown
            parts = [
                self.text,
                f"{self.score:.4f}",
                f"{bd.get('ngram', 0):.4f}",
                f"{bd.get('wordfreq', 0):.4f}",
                f"{bd.get('phoneme', 0):.4f}",
                f"{bd.get('seam', 0):.4f}",
                f"{bd.get('structure', 0):.4f}",
            ]
        else:
            parts = [self.text, f"{self.score:.4f}"]
        return "\t".join(parts)

    def as_jsonl_dict(self) -> Dict:
        return {
            "name":           self.text,
            "score":          round(self.score, 6),
            "score_breakdown":self.score_breakdown,
            "components":     self.components,
            "join_strategy":  self.join_strategy,
            "affixes_used":   self.affixes_used,
            "theme_sources":  self.theme_sources,
        }


def write_names_only(candidates: List[Candidate], path: str) -> None:
    """Write one name per line to *path*."""
    with open(path, "w", encoding="utf-8") as fh:
        for c in candidates:
            fh.write(c.text + "\n")


def write_tsv(
    candidates: List[Candidate],
    path: str,
    include_breakdown: bool = False,
) -> None:
    """Write TSV: name \\t score [\\t breakdown columns...]."""
    with open(path, "w", encoding="utf-8") as fh:
        # header
        if include_breakdown:
            fh.write("name\tscore\tngram\twordfreq\tphoneme\tseam\tstructure\n")
        else:
            fh.write("name\tscore\n")
        for c in candidates:
            fh.write(c.as_tsv_row(include_breakdown) + "\n")


def write_jsonl(candidates: List[Candidate], path: str) -> None:
    """Write one JSON object per line (JSONL) with full provenance."""
    with open(path, "w", encoding="utf-8") as fh:
        for c in candidates:
            fh.write(json.dumps(c.as_jsonl_dict(), ensure_ascii=False) + "\n")


TSV_SCORE_HEADER = "name\tscore"
TSV_FULL_HEADER  = "name\tscore\tngram\twordfreq\tphoneme\tseam\tstructure"
