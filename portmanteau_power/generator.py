"""
generator.py – Core generation pipeline:
  1. Load & expand roots via WordNet
  2. Apply theme affixes
  3. Pairwise / triple blends (overlap, smooth, splice)
  4. Score every candidate with the n-gram + seam + wordfreq model
  5. Diversity selection (MMR-style signature capping + edit-distance check)
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional, Set, Tuple, Any

try:
    from nltk.corpus import wordnet as _wn  # type: ignore
    _WN_OK = True
except Exception:
    _WN_OK = False

try:
    from wordfreq import top_n_list as _wf_top_n_list  # type: ignore
    _WORDFREQ_TOP_OK = True
except Exception:
    _WORDFREQ_TOP_OK = False

from portmanteau_power.themes import get_prefixes, get_suffixes, get_theme_source
from portmanteau_power.scoring import (
    build_morpheme_pattern,
    build_ngram_model,
    score_candidate,
    passes_basic_filter,
    approx_syllables,
    seam_score,
    VOWELS,
    CONSONANTS,
    zipf,
    is_alpha,
    NGramModel,
)
from portmanteau_power.explain import Candidate

_CLEAN_RE = re.compile(r"[^a-z]")


def _clean(w: str) -> str:
    return _CLEAN_RE.sub("", w.lower().strip())


# ---------------------------------------------------------------------------
# Diversity helpers
# ---------------------------------------------------------------------------

def _signature(word: str) -> str:
    """Near-duplicate signature: collapse repeated chars + normalise vowels."""
    w = re.sub(r"(.)\1+", r"\1", word)
    w = re.sub(r"[aeiou]", "a", w)
    return w


def _edit_distance_normalized(a: str, b: str) -> float:
    """Normalized Levenshtein distance in [0, 1].  0 = identical, 1 = maximally different."""
    la, lb = len(a), len(b)
    if la == 0 and lb == 0:
        return 0.0
    if la == 0 or lb == 0:
        return 1.0
    prev = list(range(lb + 1))
    for ca in a:
        curr = [prev[0] + 1]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[lb] / max(la, lb)


def _mmr_diversify(
    candidates: List[Candidate],
    target_size: int,
    max_per_signature: int = 3,
    min_edit_distance: float = 0.25,
) -> List[Candidate]:
    """Cap near-duplicates using signature capping and edit-distance checks.

    *min_edit_distance* is the minimum normalized Levenshtein distance a new
    candidate must have from every recently accepted candidate; candidates that
    are too similar are skipped.  The edit-distance check is applied against a
    rolling window of the last 40 accepted words to keep runtime linear.
    """
    out: List[Candidate] = []
    sig_counts: Dict[str, int] = {}
    for c in candidates:
        sig = _signature(c.text)
        if sig_counts.get(sig, 0) >= max_per_signature:
            continue
        # Edit-distance check against the last window of accepted candidates
        too_similar = any(
            _edit_distance_normalized(c.text, prev.text) < min_edit_distance
            for prev in out[-40:]
        )
        if too_similar:
            continue
        sig_counts[sig] = sig_counts.get(sig, 0) + 1
        out.append(c)
        if len(out) >= target_size:
            break
    return out


# ---------------------------------------------------------------------------
# WordNet expansion
# ---------------------------------------------------------------------------

def _wn_expand(
    word: str,
    max_per_word: int = 70,
    allow_pos: Set[str] = frozenset({"n", "a", "s"}),
) -> List[str]:
    """Return WordNet-related terms for *word*, sorted by relevance."""
    if not _WN_OK:
        return [word]

    scored: Dict[str, float] = {}

    def _add(term: str, bonus: float) -> None:
        t = _clean(term)
        if not t or len(t) < 3:
            return
        if not is_alpha(t):
            return
        if "_" in term:
            return
        if zipf(t) < 1.5 and len(t) > 10:
            return
        scored[t] = max(scored.get(t, -1e9), bonus)

    _add(word, 2.5)
    for syn in _wn.synsets(word):
        if syn.pos() not in allow_pos:
            continue
        for lem in syn.lemmas():
            _add(lem.name(), 2.0)
            for rel in lem.derivationally_related_forms():
                _add(rel.name(), 1.4)
        for hyper in syn.hypernyms():
            for lem in hyper.lemmas():
                _add(lem.name(), 0.6)
        for hypo in syn.hyponyms():
            for lem in hypo.lemmas():
                _add(lem.name(), 0.3)

    items = sorted(
        scored.items(),
        key=lambda kv: (kv[1], zipf(kv[0])),
        reverse=True,
    )
    return [t for t, _ in items[:max_per_word]]


# ---------------------------------------------------------------------------
# Join strategies
# ---------------------------------------------------------------------------

def _overlap_joins(a: str, b: str, min_ov: int = 2, max_ov: int = 6) -> List[str]:
    out: List[str] = []
    limit = min(max_ov, len(a), len(b))
    for k in range(limit, min_ov - 1, -1):
        if a.endswith(b[:k]):
            out.append(a + b[k:])
    return out


_CONNECTORS = ("", "a", "o", "i", "e", "x")
# Common vowel connectors in English portmanteaus; "x" added for tech/brand aesthetics.


def _smooth_joins(a: str, b: str) -> List[str]:
    out = [a + b]
    if a and b:
        if a[-1] == b[0]:
            out.append(a + b[1:])
        if a[-1] in VOWELS and b[0] in VOWELS:
            out.append(a[:-1] + b)
            out.append(a + b[1:])
        elif a[-1] in CONSONANTS and b[0] in CONSONANTS:
            for c in _CONNECTORS[1:]:
                out.append(a + c + b)
    return out


def _syllable_boundary_positions(word: str) -> List[int]:
    """Return approximate syllable-boundary character positions in *word*.

    A boundary is placed at the midpoint of each consonant cluster that sits
    between two vowel groups.  For a word like "power" (p-ow-er) this returns
    [3] (after "pow"), and for "titan" (ti-tan) it returns [2] (after "ti").
    Returns an empty list for monosyllabic words.
    """
    vowel_groups = list(re.finditer(r"[aeiouy]+", word))
    positions: List[int] = []
    for i in range(1, len(vowel_groups)):
        prev_end = vowel_groups[i - 1].end()
        curr_start = vowel_groups[i].start()
        # Place the boundary at the midpoint of the consonant cluster.
        # The +1 ensures we round up for odd-length clusters, biasing the
        # split slightly toward the following syllable (more natural in English).
        mid = prev_end + (curr_start - prev_end + 1) // 2
        positions.append(mid)
    return positions


def _splice_joins(a: str, b: str) -> List[str]:
    """Return splice blends of *a* and *b*.

    Syllable-boundary cuts are tried first (higher linguistic quality); the
    original arbitrary range cuts are then applied as a fallback so that short
    or monosyllabic words still produce candidates.
    """
    out: List[str] = []
    seen: Set[str] = set()

    def _add(left: str, right: str) -> None:
        if left and right:
            text = left + right
            if text not in seen:
                seen.add(text)
                out.append(text)

    # Syllable-boundary cuts (higher quality)
    for cut_a in _syllable_boundary_positions(a):
        if 2 <= cut_a <= len(a) - 1:
            for cut_b in _syllable_boundary_positions(b):
                if 1 <= cut_b <= len(b) - 1:
                    _add(a[:cut_a], b[cut_b:])

    # Arbitrary range cuts – original behaviour; covers short/monosyllabic words
    for cut_a in range(max(3, len(a) - 4), len(a) - 1):
        for cut_b in range(1, min(4, len(b) - 2)):
            _add(a[:cut_a], b[cut_b:])

    return out


def _all_joins(a: str, b: str, min_ov: int = 2, max_ov: int = 6) -> List[Tuple[str, str]]:
    """Return (candidate_text, strategy_label) pairs for both join orders."""
    results: List[Tuple[str, str]] = []
    seen: Set[str] = set()

    def _add(text: str, strat: str) -> None:
        if text not in seen:
            seen.add(text)
            results.append((text, strat))

    for s in _overlap_joins(a, b, min_ov, max_ov):
        _add(s, "overlap")
    for s in _overlap_joins(b, a, min_ov, max_ov):
        _add(s, "overlap")
    for s in _smooth_joins(a, b):
        _add(s, "smooth")
    for s in _smooth_joins(b, a):
        _add(s, "smooth")
    for s in _splice_joins(a, b):
        _add(s, "splice")
    for s in _splice_joins(b, a):
        _add(s, "splice")

    return results


# ---------------------------------------------------------------------------
# Affix application
# ---------------------------------------------------------------------------

def _affix_candidates(
    base: str,
    prefixes: List[str],
    suffixes: List[str],
    themes: List[str],
) -> List[Tuple[str, List[str], List[str]]]:
    """
    Return (text, affixes_used, theme_sources) triples for prefix/suffix combos.
    """
    results: List[Tuple[str, List[str], List[str]]] = []

    def _src(m: str) -> List[str]:
        return get_theme_source(m, themes)

    for p in prefixes:
        results.append((p + base, [p], _src(p)))
    for s in suffixes:
        results.append((base + s, [s], _src(s)))
    # limited both-sides (top 8 of each to avoid explosion)
    for p in prefixes[:8]:
        for s in suffixes[:8]:
            results.append((p + base + s, [p, s], list(set(_src(p) + _src(s)))))
    return results


# ---------------------------------------------------------------------------
# Main generate function
# ---------------------------------------------------------------------------

def generate(
    input_words: List[str],
    config: Dict[str, Any],
    target_size: int = 5000,
) -> List[Candidate]:
    """
    Full generation pipeline.  Returns a list of *Candidate* objects sorted by
    descending score, capped at *target_size* after diversity filtering.
    """
    # ----- Unpack config -----
    themes           = config["themes"]["enabled"]
    weights          = config["scoring"]["weights"]
    min_len          = config["constraints"]["min_length"]
    max_len          = config["constraints"]["max_length"]
    min_syl          = config["constraints"]["min_syllables"]
    max_syl          = config["constraints"]["max_syllables"]
    banned           = config["constraints"]["banned_substrings"]
    per_root_vars    = config["join"]["per_root_variants"]
    seed_keep        = config["join"]["seed_keep"]
    join_pool_size   = config["join"]["join_pool"]
    per_pair_keep    = config["join"]["per_pair_keep"]
    local_window     = config["join"]["local_window"]
    min_ov           = config["join"]["min_overlap"]
    max_ov           = config["join"]["max_overlap"]
    allow_triples    = config["join"]["allow_triples"]
    triple_pool_size = config["join"]["triple_pool"]
    max_per_sig      = config["join"]["max_per_signature"]

    prefixes = get_prefixes(themes)
    suffixes = get_suffixes(themes)

    # ----- Clean roots -----
    roots: List[str] = []
    seen_roots: Set[str] = set()
    for w in input_words:
        c = _clean(w)
        if c and len(c) >= 3 and is_alpha(c) and c not in seen_roots:
            seen_roots.add(c)
            roots.append(c)

    # ----- Build n-gram training corpus -----
    training: Set[str] = set(roots)
    # Add theme morphemes for better brand-word coverage
    training.update(prefixes)
    training.update(suffixes)
    # Add WordNet lemmas of roots
    if _WN_OK:
        for r in roots:
            for syn in _wn.synsets(r)[:6]:
                for lem in syn.lemmas()[:15]:
                    t = _clean(lem.name())
                    if t and len(t) >= 3 and is_alpha(t) and "_" not in lem.name():
                        training.add(t)
    # Seed the model with the most common English words so that the trigram
    # distribution is well-calibrated and novel portmanteaus are not unfairly
    # penalised for lacking obscure letter patterns.
    # Note: top_n_list does internal lazy loading; the first call may take a
    # fraction of a second, but subsequent calls are fast.
    if _WORDFREQ_TOP_OK:
        try:
            for w in _wf_top_n_list("en", 5000):
                if w.isalpha() and len(w) >= 3:
                    training.add(w.lower())
        except Exception:
            pass

    ngram_model = build_ngram_model(training, n=3)

    # Morpheme bonus pattern – precompiled once for O(word_length) matching
    # instead of O(morphemes × word_length) per candidate.
    morpheme_bonus_pattern = build_morpheme_pattern(prefixes + suffixes)

    # ----- Helper: score + filter a string -----
    def _score_str(
        text: str,
        components: List[str],
        strategy: str,
        affixes: List[str],
        theme_srcs: List[str],
    ) -> Optional[Candidate]:
        text = text.lower()
        if not passes_basic_filter(text, min_len, max_len, banned):
            return None
        syl = approx_syllables(text)
        if not (min_syl <= syl <= max_syl):
            return None
        total, bd = score_candidate(
            text, ngram_model,
            weights=weights,
            morpheme_bonus_pattern=morpheme_bonus_pattern,
        )
        return Candidate(
            text=text,
            score=total,
            score_breakdown=bd,
            components=components,
            join_strategy=strategy,
            affixes_used=affixes,
            theme_sources=theme_srcs,
        )

    # ----- Seed pool: roots + WordNet expansions + affixes of roots -----
    best: Dict[str, Candidate] = {}

    def _maybe_add(cand: Optional[Candidate]) -> None:
        if cand is None:
            return
        existing = best.get(cand.text)
        if existing is None or cand.score > existing.score:
            best[cand.text] = cand

    expanded_map: Dict[str, List[str]] = {}
    for r in roots:
        expanded_map[r] = _wn_expand(r, max_per_word=per_root_vars)

    # Seeds from roots + expansions
    for r, variants in expanded_map.items():
        for v in variants:
            c = _score_str(v, [v], "seed", [], [])
            _maybe_add(c)

    # Affix seeds
    for r in roots:
        for text, affixes, tsrcs in _affix_candidates(r, prefixes, suffixes, themes):
            c = _score_str(text, [r], "affix", affixes, tsrcs)
            _maybe_add(c)

    # ----- Build join pool (top seeds sorted by score) -----
    seed_sorted = sorted(best.values(), key=lambda x: x.score, reverse=True)[:seed_keep]
    join_pool = [c.text for c in seed_sorted[:join_pool_size]]

    # Also include theme morphemes directly in pool for richer combos
    for m in prefixes[:100] + suffixes[:100]:
        if m not in join_pool:
            join_pool.append(m)

    # ----- Pairwise joins -----
    for i, a in enumerate(join_pool):
        end = min(i + 1 + local_window, len(join_pool))
        for b in join_pool[i + 1 : end]:
            for text, strat in _all_joins(a, b, min_ov, max_ov):
                # Determine components & seam quality quickly
                sp = max(seam_score(a, b), seam_score(b, a))
                if sp < -1.2:
                    continue
                c = _score_str(text, [a, b], strat, [], [])
                _maybe_add(c)
            # top-K per pair enforced via best dict (score keeps best only)

    # Per-pair-keep: after adding all joins, we still keep the global best dict.
    # Trim to seed_keep + join window to avoid memory bloat
    if len(best) > seed_keep * 4:
        trimmed = sorted(best.values(), key=lambda x: x.score, reverse=True)[: seed_keep * 4]
        best = {c.text: c for c in trimmed}

    # ----- Optional triple blends -----
    if allow_triples and len(join_pool) >= 20:
        join_candidates_sorted = sorted(
            (c for c in best.values() if c.join_strategy in ("overlap", "smooth", "splice")),
            key=lambda x: x.score,
            reverse=True,
        )[:triple_pool_size]

        third_pool = join_pool[:60]
        # Include theme morphemes so triple blends can end/start with brand affixes
        for m in prefixes[:40] + suffixes[:40]:
            if m not in third_pool:
                third_pool.append(m)
        for mid in join_candidates_sorted:
            for third in third_pool:
                if third in mid.text or mid.text in third:
                    continue
                for text, strat in _all_joins(mid.text, third, min_ov, max_ov):
                    c = _score_str(text, mid.components + [third], "triple", mid.affixes_used, mid.theme_sources)
                    _maybe_add(c)

    # ----- Final sort, diversify, trim -----
    final_sorted = sorted(best.values(), key=lambda x: x.score, reverse=True)
    final = _mmr_diversify(final_sorted, target_size=target_size, max_per_signature=max_per_sig)
    return final[:target_size]
