"""
scoring.py – Character n-gram model, seam scoring, and overall candidate strength.

v5 additions
------------
* rule_based_g2p_score  – phonotactic pronounceability for novel words
* stress_score          – trochee/iamb stress-pattern bonus via CMU dict
* melody_score          – alliteration + vowel-harmony signal
* score_candidate updated to include all five dimensions + new components
"""

from __future__ import annotations

import math
import re
from typing import Dict, Iterable, Optional, Tuple

try:
    import pronouncing as _pronouncing  # type: ignore
    _PRONOUNCING_OK = True
except Exception:
    _PRONOUNCING_OK = False

try:
    from wordfreq import zipf_frequency as _zipf  # type: ignore
    _WORDFREQ_OK = True
except Exception:
    _WORDFREQ_OK = False

VOWELS = "aeiou"
CONSONANTS = "bcdfghjklmnpqrstvwxyz"
_ALPHA_RE = re.compile(r"^[a-z]+$")

# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def is_alpha(word: str) -> bool:
    return bool(_ALPHA_RE.fullmatch(word))


def approx_syllables(word: str) -> int:
    groups = re.findall(r"[aeiouy]+", word)
    return max(1, len(groups))


def cmu_syllables(word: str) -> Optional[int]:
    if not _PRONOUNCING_OK:
        return None
    phones = _pronouncing.phones_for_word(word)
    if not phones:
        return None
    return _pronouncing.syllable_count(phones[0])


def zipf(word: str) -> float:
    if _WORDFREQ_OK:
        return _zipf(word, "en")
    return 0.0


# ---------------------------------------------------------------------------
# Character n-gram (trigram) model
# ---------------------------------------------------------------------------

NGramModel = Dict[str, float]


def build_ngram_model(words: Iterable[str], n: int = 3) -> NGramModel:
    """
    Build a smoothed character n-gram log-probability model from *words*.

    Uses add-k (Laplace) smoothing.  Returns a dict mapping n-gram strings
    to log-probabilities.  The special key "__UNSEEN__" holds the fallback.
    """
    counts: Dict[str, int] = {}
    total = 0

    for w in words:
        w = w.lower().strip()
        # keep only alpha
        w = re.sub(r"[^a-z]", "", w)
        if len(w) < n:
            continue
        padded = "^" * (n - 1) + w + "$" * (n - 1)
        for i in range(len(padded) - n + 1):
            gram = padded[i : i + n]
            counts[gram] = counts.get(gram, 0) + 1
            total += 1

    k = 0.5
    vocab_size = len(counts) + 500  # smoothed vocab size
    denom = total + k * vocab_size

    model: NGramModel = {}
    for gram, cnt in counts.items():
        model[gram] = math.log((cnt + k) / denom)

    model["__UNSEEN__"] = math.log(k / denom)
    return model


def ngram_logprob(word: str, model: NGramModel, n: int = 3) -> float:
    """Return per-character average log-probability under *model*."""
    if not model:
        return 0.0
    w = re.sub(r"[^a-z]", "", word.lower())
    if len(w) < n:
        return model.get("__UNSEEN__", -8.0)
    padded = "^" * (n - 1) + w + "$" * (n - 1)
    unseen = model.get("__UNSEEN__", -8.0)
    total = 0.0
    count = 0
    for i in range(len(padded) - n + 1):
        gram = padded[i : i + n]
        total += model.get(gram, unseen)
        count += 1
    return total / max(1, count)


# ---------------------------------------------------------------------------
# Phoneme-based scoring (optional, via pronouncing / CMU dict)
# ---------------------------------------------------------------------------

def phoneme_score(word: str) -> float:
    """
    Score pronounceability via CMU phoneme dictionary.
    Returns a value in roughly [0, 1]; unknown words score 0.
    """
    if not _PRONOUNCING_OK:
        return 0.0
    phones = _pronouncing.phones_for_word(word)
    if not phones:
        return 0.0
    # Being *in* the dict is already a strong signal
    base = 0.6
    syl = _pronouncing.syllable_count(phones[0])
    # Prefer 2-3 syllables
    syl_bonus = 0.4 if syl in (2, 3) else (0.2 if syl == 1 else 0.1)
    return base + syl_bonus


# ---------------------------------------------------------------------------
# Seam penalty
# ---------------------------------------------------------------------------

def seam_score(left: str, right: str) -> float:
    """
    Score the boundary between *left* (end) and *right* (start).
    Higher is better; returned values roughly in [-2, +1].
    """
    if not left or not right:
        return -1.0
    x = left[-1]
    y = right[0]
    p = 0.0

    # vowel-vowel collision → usually mushy
    if x in VOWELS and y in VOWELS:
        p -= 0.8
    # consonant pileup
    if x in CONSONANTS and y in CONSONANTS:
        p -= 0.4

    # same letter doubled (unless l, s, which are accepted in English)
    if x == y and x not in "ls":
        p -= 0.5

    # pleasant endings into vowels
    if x in "nrml" and y in VOWELS:
        p += 0.35
    if x in VOWELS and y in "nrlm":
        p += 0.25
    if x in "tkrx" and y in VOWELS:
        p += 0.20

    # common English digrams at a boundary
    good_pairs = {
        "st", "tr", "pr", "cr", "bl", "fl", "gr", "sl", "sp", "sw",
        "th", "sh", "ch", "wh", "ph", "sc", "sk", "sm", "sn",
    }
    if (x + y) in good_pairs:
        p += 0.30

    return p


# ---------------------------------------------------------------------------
# Rule-based G2P pronounceability score (no external dependency)
# ---------------------------------------------------------------------------

# Valid English onset clusters (initial consonant groups before a vowel)
_VALID_ONSETS = frozenset({
    "bl", "br", "cl", "cr", "dr", "dw", "fl", "fr", "gl", "gr",
    "ph", "pl", "pr", "sc", "sh", "sk", "sl", "sm", "sn", "sp",
    "sq", "st", "sw", "th", "tr", "tw", "wh", "wr",
    "scr", "shr", "spl", "spr", "str", "thr",
    "ch", "ck", "ct", "gn", "kn", "mn", "ng", "nk", "pn", "pt",
})

# Valid English coda clusters (final consonant groups after a vowel)
_VALID_CODAS = frozenset({
    "ck", "ct", "ft", "ld", "lk", "ll", "lm", "ln", "lp", "lt",
    "lf", "lv", "mp", "nd", "ng", "nk", "nt", "pt", "rb", "rd",
    "rf", "rk", "rl", "rm", "rn", "rp", "rs", "rt", "rv", "rz",
    "sk", "sp", "ss", "st", "sh", "th", "wn",
    "mpt", "nct", "ngth", "nks", "rld", "rst",
})

# Digraphs that represent a single English phoneme
_DIGRAPHS = frozenset({"ph", "th", "sh", "ch", "wh", "gh", "ck", "ng", "qu"})

# Known silent/ugly consonant clusters to penalise
_BAD_CLUSTERS = re.compile(r"(xk|kx|vd|dv|bf|fb|gv|vg|mf|fm|pk|kp)")


def rule_based_g2p_score(word: str) -> float:
    """
    Phonotactic pronounceability score in [0, 1] based on English grapheme rules.

    Rewards:
      • recognised digraph patterns (th, sh, ch …)
      • valid onset / coda clusters
      • good vowel-to-consonant ratio
    Penalises:
      • impossible consonant clusters
      • bizarre grapheme sequences
    """
    w = word.lower()
    score = 0.5  # neutral starting point

    # Digraph bonus
    dg_count = sum(1 for dg in _DIGRAPHS if dg in w)
    score += min(0.15, dg_count * 0.05)

    # Valid onset at word start
    for onset in _VALID_ONSETS:
        if w.startswith(onset):
            score += 0.05
            break

    # Valid coda at word end
    for coda in _VALID_CODAS:
        if w.endswith(coda):
            score += 0.05
            break

    # Bad cluster penalty
    if _BAD_CLUSTERS.search(w):
        score -= 0.20

    # Vowel ratio (ideal 0.35–0.50 for English)
    vc = sum(1 for c in w if c in VOWELS)
    ratio = vc / len(w) if w else 0
    score += max(0.0, 0.15 - abs(ratio - 0.42) * 0.6)

    # Alternating consonant-vowel pattern bonus
    cv_changes = sum(
        1 for i in range(len(w) - 1)
        if (w[i] in VOWELS) != (w[i + 1] in VOWELS)
    )
    cv_ratio = cv_changes / max(1, len(w) - 1)
    score += cv_ratio * 0.10

    return max(0.0, min(1.0, score))


# ---------------------------------------------------------------------------
# Stress-pattern score (trochee / iamb preference)
# ---------------------------------------------------------------------------

def stress_score(word: str) -> float:
    """
    Score the stress pattern using CMU pronouncing dictionary.

    Trochee (STRESS-unstress, e.g. "Twitter", "Apple") → 1.0
    Dactyl  (STRESS-u-u, e.g. "Amazon")                → 0.85
    Iamb    (unstress-STRESS, e.g. "Slack")            → 0.75
    Single syllable                                     → 0.65
    Other                                               → 0.40

    Returns 0.0 when CMU data is unavailable.
    """
    if not _PRONOUNCING_OK:
        return 0.0
    phones_list = _pronouncing.phones_for_word(word)
    if not phones_list:
        return 0.0

    phones = phones_list[0]
    # Extract stress digits (0 = unstressed, 1 = primary, 2 = secondary)
    stresses = [ch for ph in phones.split() for ch in ph if ch.isdigit()]
    n = len(stresses)

    if n == 0:
        return 0.0
    if n == 1:
        return 0.65
    if n == 2:
        if stresses[0] in "12" and stresses[1] == "0":
            return 1.00  # trochee
        if stresses[0] == "0" and stresses[1] in "12":
            return 0.75  # iamb
        return 0.50
    if n == 3:
        if stresses[0] in "12" and stresses[1] == "0" and stresses[2] == "0":
            return 0.85  # dactyl
        if stresses[0] == "0" and stresses[1] == "0" and stresses[2] in "12":
            return 0.60  # anapest
    # Longer words: reward initial stress
    if stresses[0] in "12":
        return 0.70
    return 0.40


# ---------------------------------------------------------------------------
# Melody score: alliteration + vowel harmony
# ---------------------------------------------------------------------------

def melody_score(word: str) -> float:
    """
    Score sound-aesthetic properties of *word* in [0, 1].

    Signals rewarded:
      • Alliteration: same consonant appears at start of multiple syllables
      • Vowel harmony: one vowel type dominates (like brand names *Zoom*, *Slack*)
      • Pleasant liquid consonants (l, r, m, n) — associated with brand memorability
    """
    if not word:
        return 0.0
    w = word.lower()
    score = 0.3  # baseline

    # --- Alliteration: same consonant at syllable onsets ---
    # Approximate syllable onsets as positions right after each vowel
    onsets = [w[0]] if w[0] in CONSONANTS else []
    for i in range(1, len(w)):
        if w[i - 1] in VOWELS and w[i] in CONSONANTS:
            onsets.append(w[i])
    if len(onsets) >= 2:
        from collections import Counter
        top_count = Counter(onsets).most_common(1)[0][1]
        if top_count >= 2:
            score += 0.20

    # --- Vowel harmony: one vowel dominates ---
    vowels_in_word = [c for c in w if c in VOWELS]
    if vowels_in_word:
        from collections import Counter
        top_v, top_vcount = Counter(vowels_in_word).most_common(1)[0]
        harmony_ratio = top_vcount / len(vowels_in_word)
        score += harmony_ratio * 0.20

    # --- Liquid / sonorant consonants (l, r, m, n) ---
    liquid_ratio = sum(1 for c in w if c in "lrmn") / len(w)
    score += min(0.15, liquid_ratio * 0.50)

    # --- Penalise harsh sibilant overload ---
    sibilant_ratio = sum(1 for c in w if c in "sz") / len(w)
    if sibilant_ratio > 0.35:
        score -= 0.10

    return max(0.0, min(1.0, score))


# ---------------------------------------------------------------------------
# Overall strength score
# ---------------------------------------------------------------------------

_UGLY_SUBSTRINGS = re.compile(r"(qx|qj|jq|wv|vw|cj|zf|bx|fq|vq|zx)")
_TRIPLE_RE = re.compile(r"(.)\1\1")
_CONSONANT_RUN = re.compile(rf"[{CONSONANTS}]{{5,}}")
_VOWEL_RUN = re.compile(rf"[{VOWELS}]{{4,}}")


def passes_basic_filter(
    word: str,
    min_len: int,
    max_len: int,
    banned_substrings: Iterable[str] = (),
) -> bool:
    """Hard filter: length, alpha, structure, banned substrings."""
    if not (min_len <= len(word) <= max_len):
        return False
    if not is_alpha(word):
        return False
    if _TRIPLE_RE.search(word):
        return False
    if _CONSONANT_RUN.search(word):
        return False
    if _VOWEL_RUN.search(word):
        return False
    if _UGLY_SUBSTRINGS.search(word):
        return False
    if word[0] in "qx":
        return False
    for sub in banned_substrings:
        if sub and sub in word:
            return False
    return True


def score_candidate(
    word: str,
    ngram_model: NGramModel,
    *,
    weights: Optional[Dict[str, float]] = None,
    morpheme_bonus_words: Iterable[str] = (),
    ngram_n: int = 3,
) -> Tuple[float, Dict[str, float]]:
    """
    Compute a total score plus a breakdown dict for *word*.

    Returns (total_score, breakdown_dict).
    breakdown keys: ngram, wordfreq, phoneme, g2p, seam, structure, stress, melody
    """
    w = weights or {}
    w_ngram    = w.get("ngram",     0.28)
    w_wordfreq = w.get("wordfreq",  0.16)
    w_phoneme  = w.get("phoneme",   0.08)
    w_g2p      = w.get("g2p",       0.10)
    w_seam     = w.get("seam",      0.13)
    w_struct   = w.get("structure", 0.12)
    w_stress   = w.get("stress",    0.07)
    w_melody   = w.get("melody",    0.06)

    # --- n-gram ---
    ng = ngram_logprob(word, ngram_model, n=ngram_n)
    # Average log-prob per position is typically in [-7, -1] for a small
    # training corpus.  Shift and scale so that -8 → 0, -1 → ~0.875.
    ng_scaled = max(0.0, min(1.0, (ng + 8.0) / 8.0))

    # --- wordfreq ---
    z = zipf(word)
    wf_scaled = max(0.0, (z - 1.0) / 5.0)  # normalise to ~[0,1]

    # --- phoneme (CMU dict) ---
    ph = phoneme_score(word)

    # --- rule-based G2P ---
    g2p = rule_based_g2p_score(word)

    # --- seam (self-seam: consecutive pairs) ---
    seam_total = 0.0
    seam_count = 0
    for i in range(len(word) - 1):
        seam_total += seam_score(word[i : i + 1], word[i + 1 : i + 2])
        seam_count += 1
    seam_avg = (seam_total / seam_count) if seam_count else 0.0
    seam_scaled = (seam_avg + 2.0) / 3.0  # shift to [0,1]

    # --- structure ---
    # Syllable preference
    syl = cmu_syllables(word)
    if syl is None:
        syl = approx_syllables(word)
    if syl in (2, 3):
        syl_s = 1.0
    elif syl in (1, 4):
        syl_s = 0.6
    else:
        syl_s = 0.2

    # vowel ratio (ideal ≈ 0.38-0.50)
    vcount = sum(1 for c in word if c in VOWELS)
    ratio = vcount / len(word)
    ratio_s = max(0.0, 1.0 - abs(ratio - 0.44) * 4)

    # Hard endings (brand-friendly)
    hard_end = 0.4 if word[-1] in "xtrknd" else 0.0

    # consonant quality
    hard_c = sum(1 for c in word if c in "ktxzvgdrp") / len(word)
    liquid_c = sum(1 for c in word if c in "rlmn") / len(word)
    sibilant = sum(1 for c in word if c in "s") / len(word)
    struct_s = 0.4 * syl_s + 0.2 * ratio_s + 0.1 * hard_end + 0.15 * hard_c + 0.15 * liquid_c - 0.2 * max(0, sibilant - 0.3)

    # --- stress pattern ---
    st = stress_score(word)

    # --- melody ---
    mel = melody_score(word)

    # morpheme bonus
    mb = 0.0
    for m in morpheme_bonus_words:
        if m in word:
            mb += 0.55
    mb = min(mb, 2.0)  # cap

    breakdown = {
        "ngram":    round(ng_scaled,   4),
        "wordfreq": round(wf_scaled,   4),
        "phoneme":  round(ph,          4),
        "g2p":      round(g2p,         4),
        "seam":     round(seam_scaled, 4),
        "structure":round(struct_s,    4),
        "stress":   round(st,          4),
        "melody":   round(mel,         4),
    }

    total = (
        w_ngram    * ng_scaled
        + w_wordfreq * wf_scaled
        + w_phoneme  * ph
        + w_g2p      * g2p
        + w_seam     * seam_scaled
        + w_struct   * struct_s
        + w_stress   * st
        + w_melody   * mel
        + mb
    )

    return total, breakdown
