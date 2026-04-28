"""
cli.py – Command-line entry point for portmanteau_power.

Usage:
    python -m portmanteau_power.cli input.txt output.txt [options]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from portmanteau_power import __version__
from portmanteau_power.themes import ALL_THEME_NAMES, DEFAULT_THEMES
from portmanteau_power.config import load_config, apply_cli_overrides
from portmanteau_power.generator import generate
from portmanteau_power.explain import (
    write_names_only,
    write_tsv,
    write_jsonl,
)


def _parse_themes(raw: str) -> List[str]:
    return [t.strip() for t in raw.split(",") if t.strip()]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="portmanteau_power.cli",
        description=(
            "portmanteau_power v{ver} – configurable portmanteau / name generator.\n\n"
            "Example:\n"
            "  python -m portmanteau_power.cli input.txt output.txt \\\n"
            "      --target-size 5000 \\\n"
            "      --themes power,tech,government,business,healthcare,environment,religion \\\n"
            "      --config configs/default.yml \\\n"
            "      --explain out.jsonl"
        ).format(ver=__version__),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Positional
    ap.add_argument("input",  help="Input text file (one term per line).")
    ap.add_argument("output", help="Output file for generated names.")

    # Core
    ap.add_argument(
        "--target-size", type=int, default=5000,
        help="Max number of names to output. (default: 5000)",
    )
    ap.add_argument(
        "--config", metavar="PATH",
        help="Path to a YAML or JSON config file (overrides built-in defaults).",
    )
    ap.add_argument(
        "--themes", metavar="THEME,...",
        help=(
            "Comma-separated list of themes to enable. "
            f"Available: {', '.join(ALL_THEME_NAMES)}. "
            f"(default: {','.join(DEFAULT_THEMES)})"
        ),
    )

    # Length constraints
    ap.add_argument("--min-len", type=int, help="Minimum output name length. (default: 5)")
    ap.add_argument("--max-len", type=int, help="Maximum output name length. (default: 12)")

    # Generation controls
    ap.add_argument(
        "--per-root-variants", type=int,
        help="Max WordNet variants kept per root. (default: 70)",
    )
    ap.add_argument(
        "--per-pair-keep", type=int,
        help="Top candidates kept per pairwise join. (default: 10)",
    )
    ap.add_argument(
        "--allow-triples", action="store_true",
        help="Enable limited triple blends (slower).",
    )
    ap.add_argument(
        "--banned-substrings", metavar="A,B,...",
        help="Comma-separated substrings to ban from output.",
    )

    # Output modes
    ap.add_argument(
        "--include-scores", action="store_true",
        help="Write TSV output with name and score columns.",
    )
    ap.add_argument(
        "--explain", metavar="JSONL_PATH",
        help=(
            "Write full provenance (score breakdown, components, join strategy, "
            "affixes, theme sources) to a JSONL file."
        ),
    )

    # Meta
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    return ap


def main(argv: Optional[List[str]] = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)

    # ---- Validate input file ----
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        return 1

    with input_path.open("r", encoding="utf-8") as fh:
        raw_words = [line.strip() for line in fh if line.strip()]

    if not raw_words:
        print("Error: input file is empty.", file=sys.stderr)
        return 1

    # ---- Load config ----
    config = load_config(args.config)

    # ---- Apply CLI overrides ----
    themes_list = _parse_themes(args.themes) if args.themes else None
    banned = [s.strip() for s in args.banned_substrings.split(",") if s.strip()] if args.banned_substrings else None

    try:
        config = apply_cli_overrides(
            config,
            target_size=args.target_size,
            min_len=args.min_len,
            max_len=args.max_len,
            themes=themes_list,
            per_root_variants=args.per_root_variants,
            per_pair_keep=args.per_pair_keep,
            allow_triples=args.allow_triples if args.allow_triples else None,
            banned_substrings=banned,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    target_size = config.get("target_size", args.target_size)

    # ---- Ensure output directory exists ----
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # ---- Generate ----
    print(
        f"Generating up to {target_size} names from {len(raw_words)} input term(s) "
        f"using themes: {', '.join(config['themes']['enabled'])} …",
        flush=True,
    )
    results = generate(raw_words, config, target_size=target_size)

    # ---- Write main output ----
    if args.include_scores:
        write_tsv(results, str(out_path), include_breakdown=True)
    else:
        write_names_only(results, str(out_path))

    # ---- Write JSONL explain ----
    if args.explain:
        explain_path = Path(args.explain)
        explain_path.parent.mkdir(parents=True, exist_ok=True)
        write_jsonl(results, str(explain_path))
        print(f"Explain output → {args.explain}  ({len(results)} records)")

    print(f"Done. Generated {len(results)} names → {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
