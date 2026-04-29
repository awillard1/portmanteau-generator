"""tests/test_basic.py – Minimal validation tests for portmanteau_power."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from portmanteau_power.config import load_config, apply_cli_overrides, DEFAULT_CONFIG
from portmanteau_power.generator import generate
from portmanteau_power.themes import get_prefixes, get_suffixes, ALL_THEME_NAMES, DEFAULT_THEMES
from portmanteau_power.scoring import build_ngram_model, ngram_logprob, passes_basic_filter
from portmanteau_power.explain import write_names_only, write_tsv, write_jsonl, Candidate


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

SIMPLE_WORDS = ["power", "tech", "nova", "forge"]

def _default_config(**overrides):
    cfg = load_config(None)
    # small sizes for fast tests
    cfg["join"]["seed_keep"]   = 200
    cfg["join"]["join_pool"]   = 80
    cfg["join"]["per_pair_keep"] = 5
    cfg["join"]["local_window"]  = 10
    cfg["join"]["per_root_variants"] = 20
    cfg.update(overrides)
    return cfg


# ---------------------------------------------------------------------------
# Test: generator produces non-empty output
# ---------------------------------------------------------------------------

def test_generator_produces_output():
    cfg = _default_config()
    results = generate(SIMPLE_WORDS, cfg, target_size=50)
    assert len(results) > 0, "generate() must return at least one candidate"


# ---------------------------------------------------------------------------
# Test: respects target_size
# ---------------------------------------------------------------------------

def test_generator_respects_target_size():
    cfg = _default_config()
    target = 10
    results = generate(SIMPLE_WORDS, cfg, target_size=target)
    assert len(results) <= target, (
        f"generate() returned {len(results)} items but target was {target}"
    )


# ---------------------------------------------------------------------------
# Test: respects length constraints
# ---------------------------------------------------------------------------

def test_generator_respects_length_constraints():
    cfg = _default_config()
    min_len = 6
    max_len = 10
    cfg["constraints"]["min_length"] = min_len
    cfg["constraints"]["max_length"] = max_len

    results = generate(SIMPLE_WORDS, cfg, target_size=100)
    assert len(results) > 0
    for c in results:
        assert min_len <= len(c.text) <= max_len, (
            f"Name '{c.text}' (len={len(c.text)}) violates [{min_len}, {max_len}]"
        )


# ---------------------------------------------------------------------------
# Test: banned substrings are excluded
# ---------------------------------------------------------------------------

def test_banned_substrings_excluded():
    banned = ["oo", "xx"]
    cfg = _default_config()
    cfg["constraints"]["banned_substrings"] = banned

    results = generate(SIMPLE_WORDS, cfg, target_size=200)
    assert len(results) > 0
    for c in results:
        for sub in banned:
            assert sub not in c.text, (
                f"Banned substring '{sub}' found in output '{c.text}'"
            )


# ---------------------------------------------------------------------------
# Test: themes – get_prefixes / get_suffixes return non-empty lists
# ---------------------------------------------------------------------------

def test_theme_banks_non_empty():
    for theme in ALL_THEME_NAMES:
        prefixes = get_prefixes([theme])
        suffixes = get_suffixes([theme])
        assert len(prefixes) > 0, f"Theme '{theme}' has no prefixes"
        assert len(suffixes) > 0, f"Theme '{theme}' has no suffixes"


def test_theme_common_includes_everyday_words():
    """The 'common' theme must include emotional / everyday words like 'love', 'hope'."""
    prefixes = get_prefixes(["common"])
    suffixes = get_suffixes(["common"])
    all_morphemes = set(prefixes + suffixes)
    for word in ("love", "hope", "joy", "care", "life"):
        assert word in all_morphemes, (
            f"Expected everyday word '{word}' in 'common' theme morphemes"
        )


def test_themes_cli_override():
    cfg = load_config(None)
    apply_cli_overrides(cfg, themes=["power", "tech"])
    assert cfg["themes"]["enabled"] == ["power", "tech"]


# ---------------------------------------------------------------------------
# Test: n-gram model
# ---------------------------------------------------------------------------

def test_ngram_model_scores_known_word_higher():
    words = ["power", "forge", "nova", "titan", "storm"]
    model = build_ngram_model(words, n=3)

    # "power" was in training → should score better than random noise
    real_score = ngram_logprob("power", model, n=3)
    gibberish_score = ngram_logprob("qxzvwb", model, n=3)
    assert real_score > gibberish_score


def test_passes_basic_filter():
    assert passes_basic_filter("novaforg", 5, 12) is True
    assert passes_basic_filter("ab", 5, 12) is False        # too short (len=2 < min_len=5)
    assert passes_basic_filter("toolongstring123", 5, 12) is False  # too long AND non-alpha
    assert passes_basic_filter("novaforg", 5, 12, ["nova"]) is False  # banned substring


# ---------------------------------------------------------------------------
# Test: Candidate dataclass + output writers
# ---------------------------------------------------------------------------

def _make_candidate(text="testword", score=1.5) -> Candidate:
    return Candidate(
        text=text,
        score=score,
        score_breakdown={"ngram": 0.5, "wordfreq": 0.3, "phoneme": 0.2, "seam": 0.4, "structure": 0.6},
        components=["test", "word"],
        join_strategy="overlap",
        affixes_used=["tech"],
        theme_sources=["tech"],
    )


def test_write_names_only(tmp_path):
    cands = [_make_candidate("alpha"), _make_candidate("beta")]
    out = tmp_path / "out.txt"
    write_names_only(cands, str(out))
    lines = out.read_text().strip().splitlines()
    assert lines == ["alpha", "beta"]


def test_write_tsv(tmp_path):
    cands = [_make_candidate("alpha", 1.0)]
    out = tmp_path / "out.tsv"
    write_tsv(cands, str(out), include_breakdown=True)
    lines = out.read_text().strip().splitlines()
    assert lines[0].startswith("name\tscore")
    assert lines[1].startswith("alpha\t")


def test_write_jsonl(tmp_path):
    cands = [_make_candidate("alpha", 1.0)]
    out = tmp_path / "out.jsonl"
    write_jsonl(cands, str(out))
    records = [json.loads(line) for line in out.read_text().strip().splitlines()]
    assert len(records) == 1
    assert records[0]["name"] == "alpha"
    assert "score_breakdown" in records[0]
    assert "components" in records[0]
    assert "join_strategy" in records[0]
    assert "theme_sources" in records[0]


# ---------------------------------------------------------------------------
# Test: CLI end-to-end
# ---------------------------------------------------------------------------

def test_cli_end_to_end(tmp_path):
    from portmanteau_power.cli import main

    input_file = tmp_path / "input.txt"
    input_file.write_text("power\ntech\nnova\n")

    output_file = tmp_path / "output.txt"
    explain_file = tmp_path / "explain.jsonl"

    ret = main([
        str(input_file),
        str(output_file),
        "--target-size", "20",
        "--themes", "power,tech,common",
        "--explain", str(explain_file),
    ])
    assert ret == 0
    names = output_file.read_text().strip().splitlines()
    assert len(names) > 0
    assert len(names) <= 20

    # Explain file should exist and be valid JSONL
    records = [json.loads(l) for l in explain_file.read_text().strip().splitlines()]
    assert len(records) == len(names)
    assert all("name" in r for r in records)


def test_cli_include_scores(tmp_path):
    from portmanteau_power.cli import main

    input_file = tmp_path / "input.txt"
    input_file.write_text("nova\ncore\n")
    output_file = tmp_path / "out.tsv"

    ret = main([
        str(input_file),
        str(output_file),
        "--target-size", "10",
        "--include-scores",
        "--themes", "power,common",
    ])
    assert ret == 0
    lines = output_file.read_text().strip().splitlines()
    # First line is TSV header
    assert "\t" in lines[0]
