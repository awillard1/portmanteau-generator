"""
scoring.py – Character n-gram model, seam scoring, and overall candidate strength.
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
# Overall strength score
# ---------------------------------------------------------------------------

_UGLY_SUBSTRINGS = re.compile(r"(qx|qj|jq|wv|vw|cj|zf|xq|bx|fq|vq|zx)")
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
    breakdown keys: ngram, wordfreq, phoneme, seam, structure
    """
    w = weights or {}
    w_ngram    = w.get("ngram",     0.35)
    w_wordfreq = w.get("wordfreq",  0.20)
    w_phoneme  = w.get("phoneme",   0.15)
    w_seam     = w.get("seam",      0.15)
    w_struct   = w.get("structure", 0.15)

    # --- n-gram ---
    ng = ngram_logprob(word, ngram_model, n=ngram_n)
    # Average log-prob per position is typically in [-7, -1] for a small
    # training corpus.  Shift and scale so that -8 → 0, -1 → ~0.875.
    ng_scaled = max(0.0, min(1.0, (ng + 8.0) / 8.0))

    # --- wordfreq ---
    z = zipf(word)
    wf_scaled = max(0.0, (z - 1.0) / 5.0)  # normalise to ~[0,1]

    # --- phoneme ---
    ph = phoneme_score(word)

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
        "seam":     round(seam_scaled, 4),
        "structure":round(struct_s,    4),
    }

    total = (
        w_ngram    * ng_scaled
        + w_wordfreq * wf_scaled
        + w_phoneme  * ph
        + w_seam     * seam_scaled
        + w_struct   * struct_s
        + mb
    )

    return total, breakdown
