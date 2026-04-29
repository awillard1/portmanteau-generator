"""tests/test_basic.py – Validation tests for portmanteau_power v5."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from portmanteau_power.config import load_config, apply_cli_overrides, DEFAULT_CONFIG
from portmanteau_power.generator import generate
from portmanteau_power.themes import get_prefixes, get_suffixes, ALL_THEME_NAMES, DEFAULT_THEMES
from portmanteau_power.scoring import (
    build_ngram_model,
    ngram_logprob,
    passes_basic_filter,
    rule_based_g2p_score,
    stress_score,
    melody_score,
)
from portmanteau_power.explain import write_names_only, write_tsv, write_jsonl, Candidate
from portmanteau_power.data import safe_international_filter, I18N_BLOCKLIST, BRAND_NAMES
from portmanteau_power.domain import check_domain, domain_available_any


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
# Test: rule-based G2P score
# ---------------------------------------------------------------------------

def test_rule_based_g2p_score_range():
    """Scores must stay within [0, 1]."""
    for word in ("novacore", "techforge", "xzqvk", "streamline", "hello", "google"):
        s = rule_based_g2p_score(word)
        assert 0.0 <= s <= 1.0, f"G2P score for '{word}' out of range: {s}"


def test_rule_based_g2p_score_ordering():
    """Real-sounding words should score higher than consonant-cluster gibberish."""
    real = rule_based_g2p_score("streamline")
    bad = rule_based_g2p_score("xzkqvft")
    assert real > bad, f"Expected 'streamline' > 'xzkqvft', got {real:.3f} vs {bad:.3f}"


def test_rule_based_g2p_digraph_bonus():
    """Words with recognised digraphs should score above 0.5."""
    assert rule_based_g2p_score("thunder") > 0.5
    assert rule_based_g2p_score("shield") > 0.5


# ---------------------------------------------------------------------------
# Test: stress pattern score
# ---------------------------------------------------------------------------

def test_stress_score_range():
    """Scores must stay within [0, 1]."""
    for word in ("apple", "google", "twitter", "amazon", "zoom", "unknownxyz"):
        s = stress_score(word)
        assert 0.0 <= s <= 1.0, f"Stress score for '{word}' out of range: {s}"


def test_stress_score_known_trochee():
    """'apple' is a classic trochee (AP-ple) and should score high."""
    s = stress_score("apple")
    # Either high (trochee recognised) or 0.0 (CMU dict unavailable) – both ok
    assert s == 0.0 or s >= 0.65, f"Expected 0.0 or ≥0.65 for 'apple', got {s}"


# ---------------------------------------------------------------------------
# Test: melody score
# ---------------------------------------------------------------------------

def test_melody_score_range():
    """Scores must stay within [0, 1]."""
    for word in ("novacore", "techforge", "hello", "paypal", "twitter"):
        s = melody_score(word)
        assert 0.0 <= s <= 1.0, f"Melody score for '{word}' out of range: {s}"


def test_melody_alliteration_bonus():
    """'paypal' has alliterative onset /p/ and should score above baseline (0.3)."""
    s = melody_score("paypal")
    assert s > 0.3, f"Expected alliteration bonus for 'paypal', got {s}"


def test_melody_vowel_harmony():
    """'zoom' has dominant 'o' vowel — should score above baseline."""
    s = melody_score("zoom")
    assert s > 0.3


# ---------------------------------------------------------------------------
# Test: score breakdown includes all new keys
# ---------------------------------------------------------------------------

def test_score_breakdown_keys():
    from portmanteau_power.scoring import score_candidate, build_ngram_model
    model = build_ngram_model(["nova", "forge", "tech"])
    _, bd = score_candidate("novatech", model)
    for key in ("ngram", "wordfreq", "phoneme", "g2p", "seam", "structure", "stress", "melody"):
        assert key in bd, f"Missing key '{key}' in score breakdown"


# ---------------------------------------------------------------------------
# Test: brand corpus
# ---------------------------------------------------------------------------

def test_brand_names_non_empty():
    assert len(BRAND_NAMES) >= 200


def test_brand_names_lowercase_alpha():
    """All brand names in the corpus must be lowercase alpha strings."""
    for name in BRAND_NAMES:
        assert name.isalpha() and name == name.lower(), (
            f"Brand name '{name}' is not lowercase alpha"
        )


# ---------------------------------------------------------------------------
# Test: safe_international_filter
# ---------------------------------------------------------------------------

def test_safe_international_filter_clean_word():
    assert safe_international_filter("novacore") is True
    assert safe_international_filter("titanforge") is True


def test_safe_international_filter_blocked_word():
    # "fuck" is in the English blocklist
    assert safe_international_filter("nofuck") is False
    # "kut" is in the Dutch blocklist
    assert safe_international_filter("marketkut") is False


def test_i18n_blocklist_non_empty():
    for lang, words in I18N_BLOCKLIST.items():
        assert len(words) > 0, f"Blocklist for language '{lang}' is empty"


def test_safe_international_flag_in_generator():
    """Names containing English blocklist terms should be absent when safe_international=True."""
    cfg = _default_config()
    cfg["features"] = {"safe_international": True}
    cfg["constraints"]["banned_substrings"] = []  # rely only on i18n filter
    results = generate(SIMPLE_WORDS, cfg, target_size=200)
    for c in results:
        assert safe_international_filter(c.text), (
            f"Unsafe name '{c.text}' passed safe_international filter"
        )


# ---------------------------------------------------------------------------
# Test: domain checker
# ---------------------------------------------------------------------------

def test_check_domain_structure():
    """check_domain must return a dict with 'name' and one key per TLD."""
    with patch("portmanteau_power.domain._is_registered", return_value=False):
        result = check_domain("novaforge", tlds=["com", "io"])
    assert result["name"] == "novaforge"
    assert "com" in result
    assert "io" in result
    # _is_registered returns False (not registered) → domain is available (True)
    assert result["com"] is True
    assert result["io"] is True


def test_domain_available_any():
    result = {"name": "testname", "com": False, "net": True, "io": False}
    assert domain_available_any(result) is True

    result_taken = {"name": "testname", "com": False, "net": False, "io": False}
    assert domain_available_any(result_taken) is False

    result_failed = {"name": "testname", "com": None, "net": None}
    assert domain_available_any(result_failed) is None


# ---------------------------------------------------------------------------
# Test: AI re-ranker
# ---------------------------------------------------------------------------

def test_ai_rerank_returns_same_length():
    from portmanteau_power.rerank import ai_rerank, _parse_ranked_names

    cands = [_make_candidate(f"name{i}") for i in range(10)]
    # Ollama unavailable → original order returned
    with patch("portmanteau_power.rerank._ollama_generate", side_effect=OSError("connection refused")):
        result = ai_rerank(cands, context="test brand", top_n=5)
    assert len(result) == 10
    assert [c.text for c in result] == [c.text for c in cands]


def test_parse_ranked_names_valid_json():
    from portmanteau_power.rerank import _parse_ranked_names
    response = '[{"name": "novacore", "reason": "punchy"}, {"name": "techforge", "reason": "tech feel"}]'
    names = _parse_ranked_names(response)
    assert names == ["novacore", "techforge"]


def test_parse_ranked_names_with_markdown_fences():
    from portmanteau_power.rerank import _parse_ranked_names
    response = '```json\n[{"name": "alpha"}, {"name": "beta"}]\n```'
    names = _parse_ranked_names(response)
    assert names == ["alpha", "beta"]


def test_ai_rerank_applies_model_order():
    from portmanteau_power.rerank import ai_rerank

    cands = [_make_candidate(f"name{i}") for i in range(5)]
    # Model reverses order
    model_response = json.dumps([{"name": f"name{i}", "reason": "ok"} for i in range(4, -1, -1)])
    with patch("portmanteau_power.rerank._ollama_generate", return_value=model_response):
        result = ai_rerank(cands, context="test", top_n=5)
    assert [c.text for c in result] == ["name4", "name3", "name2", "name1", "name0"]


# ---------------------------------------------------------------------------
# Test: Candidate dataclass + output writers
# ---------------------------------------------------------------------------

def _make_candidate(text="testword", score=1.5) -> Candidate:
    return Candidate(
        text=text,
        score=score,
        score_breakdown={
            "ngram": 0.5, "wordfreq": 0.3, "phoneme": 0.2, "g2p": 0.6,
            "seam": 0.4, "structure": 0.6, "stress": 0.8, "melody": 0.5,
        },
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
    assert "stress" in lines[0]
    assert "melody" in lines[0]
    assert "g2p" in lines[0]
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


def test_write_jsonl_with_domain(tmp_path):
    cand = _make_candidate("alpha", 1.0)
    cand.domain_available = {"name": "alpha", "com": True, "io": False}
    cand.international_safe = True
    out = tmp_path / "out.jsonl"
    write_jsonl([cand], str(out))
    records = [json.loads(line) for line in out.read_text().strip().splitlines()]
    assert records[0]["domain_available"]["com"] is True
    assert records[0]["international_safe"] is True


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
    # New columns should be present
    assert "stress" in lines[0]
    assert "melody" in lines[0]
    assert "g2p" in lines[0]


def test_cli_safe_international(tmp_path):
    from portmanteau_power.cli import main

    input_file = tmp_path / "input.txt"
    input_file.write_text("power\ntech\nnova\n")
    output_file = tmp_path / "output.txt"

    ret = main([
        str(input_file),
        str(output_file),
        "--target-size", "20",
        "--themes", "power,common",
        "--safe-international",
    ])
    assert ret == 0
    names = output_file.read_text().strip().splitlines()
    for name in names:
        assert safe_international_filter(name), f"Unsafe name in output: {name}"


def test_cli_check_domains(tmp_path):
    from portmanteau_power.cli import main

    input_file = tmp_path / "input.txt"
    input_file.write_text("nova\ncore\n")
    output_file = tmp_path / "output.txt"
    explain_file = tmp_path / "explain.jsonl"

    with patch("portmanteau_power.domain._is_registered", return_value=False):
        ret = main([
            str(input_file),
            str(output_file),
            "--target-size", "5",
            "--themes", "power,common",
            "--check-domains",
            "--domain-tlds", "com,io",
            "--explain", str(explain_file),
        ])

    assert ret == 0
    records = [json.loads(l) for l in explain_file.read_text().strip().splitlines()]
    assert all("domain_available" in r for r in records)
    # All domains should be "available" (True) since we patched _is_registered → False
    for r in records:
        assert r["domain_available"]["com"] is True


def test_cli_rerank_unavailable(tmp_path):
    """--rerank-top should gracefully fall back when Ollama is unavailable."""
    from portmanteau_power.cli import main

    input_file = tmp_path / "input.txt"
    input_file.write_text("nova\ntech\n")
    output_file = tmp_path / "output.txt"

    with patch("portmanteau_power.rerank._ollama_generate", side_effect=OSError("connection refused")):
        ret = main([
            str(input_file),
            str(output_file),
            "--target-size", "10",
            "--themes", "power,common",
            "--rerank-top", "5",
        ])

    assert ret == 0
    names = output_file.read_text().strip().splitlines()
    assert len(names) > 0

