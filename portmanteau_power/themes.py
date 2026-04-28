"""
themes.py – Thorough multi-domain morpheme banks for prefix/suffix injection.

Each theme entry maps to a dict with two lists:
  "prefixes": morphemes placed *before* a root
  "suffixes": morphemes placed *after* a root

Themes can be selected at runtime via --themes.
"""

from __future__ import annotations

import re
from typing import Dict, List, Set

# ---------------------------------------------------------------------------
# Theme definitions
# ---------------------------------------------------------------------------

THEME_BANKS: Dict[str, Dict[str, List[str]]] = {

    # ------------------------------------------------------------------
    # POWER / BRAND ENERGY
    # ------------------------------------------------------------------
    "power": {
        "prefixes": [
            "neo", "hyper", "ultra", "omni", "prime", "apex", "titan",
            "mega", "iron", "dark", "nova", "zen", "storm", "void",
            "chrono", "proto", "astro", "quant", "cyber", "inferno",
            "max", "super", "uber", "epic", "bold", "grand", "pure",
            "swift", "sharp", "hard", "great", "high", "strong", "wide",
            "vast", "deep", "rich", "core", "top", "pro", "fast", "smart",
            "bright", "live", "real", "true", "free", "new", "best",
        ],
        "suffixes": [
            "core", "forge", "force", "pulse", "vault", "engine", "nexus",
            "lab", "works", "ops", "matrix", "drive", "blade", "peak",
            "shift", "wave", "front", "link", "grid", "hub", "gate",
            "max", "prime", "edge", "flux", "base", "mark", "line",
            "craft", "sphere", "zone", "point", "field", "bridge",
            "chain", "beam", "arc", "stream", "path", "loop",
        ],
    },

    # ------------------------------------------------------------------
    # GOVERNMENT / CIVIC
    # ------------------------------------------------------------------
    "government": {
        "prefixes": [
            "civic", "demo", "legis", "nation", "state", "fed", "admin",
            "policy", "bureau", "public", "senate", "congress", "vote",
            "law", "justice", "govern", "republic", "union", "civil",
            "munici", "metro", "county", "district", "ward", "official",
            "agency", "decree", "charter", "mandate", "council",
            "execu", "judici", "legisla", "constitu", "sovereign",
            "diplo", "embassy", "treaty", "accord", "coalition",
            "reform", "audit", "regula", "comply", "enforce", "order",
        ],
        "suffixes": [
            "gov", "dept", "bureau", "office", "agency", "division",
            "authority", "board", "council", "commission", "committee",
            "ministry", "service", "corps", "force", "works",
            "act", "bill", "code", "law", "policy", "rule", "statute",
            "mandate", "charter", "accord", "treaty", "reform",
            "vote", "civic", "public", "state", "nation", "union",
        ],
    },

    # ------------------------------------------------------------------
    # BUSINESS / ENTERPRISE
    # ------------------------------------------------------------------
    "business": {
        "prefixes": [
            "corp", "ent", "brand", "mark", "trade", "biz", "com",
            "pro", "market", "profit", "venture", "supply", "demand",
            "client", "partner", "consult", "manage", "value", "growth",
            "scale", "launch", "boost", "build", "form", "found",
            "develop", "produce", "deliver", "service", "operate",
            "innova", "strateg", "mission", "vision", "lead", "direct",
            "capital", "asset", "invest", "fund", "budget", "revenue",
            "cost", "price", "sale", "deal", "offer", "contract",
            "network", "alliance", "merge", "acquire", "brand",
        ],
        "suffixes": [
            "corp", "co", "inc", "ltd", "llc", "group", "global",
            "world", "trade", "hub", "market", "shop", "store",
            "works", "solutions", "services", "consulting", "partners",
            "ventures", "holdings", "assets", "capital", "finance",
            "plus", "pro", "premier", "elite", "select", "prime",
            "direct", "express", "connect", "link", "net", "lab",
        ],
    },

    # ------------------------------------------------------------------
    # HEALTHCARE / MEDICAL / WELLNESS
    # ------------------------------------------------------------------
    "healthcare": {
        "prefixes": [
            "health", "med", "care", "bio", "vita", "thera", "pharma",
            "clinic", "cure", "heal", "nurse", "doctor", "patient",
            "safe", "well", "life", "body", "mind", "spirit", "pulse",
            "cardio", "neuro", "derma", "ortho", "pedia", "geriat",
            "immuno", "onco", "radio", "chemo", "physio", "psycho",
            "nutri", "diet", "fitness", "active", "prevent", "screen",
            "diagno", "recov", "rehab", "support", "protect", "guard",
            "sanit", "hygiene", "wellness", "balance", "natural",
            "herbal", "amino", "probiotic", "genomic",
        ],
        "suffixes": [
            "care", "health", "med", "clinic", "center", "lab",
            "pharma", "bio", "life", "well", "cure", "aid", "plus",
            "rx", "dose", "therapy", "treatment", "relief", "support",
            "protect", "shield", "guard", "safe", "fit", "active",
            "pulse", "vital", "gen", "solutions", "services",
        ],
    },

    # ------------------------------------------------------------------
    # ENVIRONMENT / SUSTAINABILITY / ECOLOGY
    # ------------------------------------------------------------------
    "environment": {
        "prefixes": [
            "eco", "terra", "green", "earth", "nature", "solar",
            "wind", "water", "clean", "sustain", "leaf", "tree",
            "forest", "ocean", "sky", "air", "bio", "geo", "hydro",
            "agri", "flora", "fauna", "marine", "alpine", "arctic",
            "climate", "carbon", "cycle", "renew", "recycl", "compost",
            "organic", "wild", "native", "pure", "fresh", "clear",
            "bright", "light", "warm", "cool", "grow", "bloom",
            "seed", "root", "soil", "stream", "river", "field",
        ],
        "suffixes": [
            "green", "eco", "earth", "nature", "planet", "world",
            "land", "zone", "park", "garden", "grove", "field",
            "stream", "bay", "coast", "ridge", "peak", "vale",
            "cycle", "flow", "grow", "bloom", "renew", "sustain",
            "care", "shield", "guard", "watch", "works", "lab",
        ],
    },

    # ------------------------------------------------------------------
    # RELIGION / SPIRITUALITY / FAITH
    # ------------------------------------------------------------------
    "religion": {
        "prefixes": [
            "spirit", "faith", "holy", "divine", "sacred", "blessed",
            "grace", "soul", "light", "truth", "heaven", "prayer",
            "praise", "love", "glory", "peace", "mercy", "hope",
            "angel", "saint", "prophet", "temple", "shrine", "altar",
            "creed", "gospel", "scripture", "covenant", "redemp",
            "salva", "sancti", "eternal", "infinite", "divine",
            "mystic", "zen", "karma", "dharma", "nirvana", "cosmic",
            "celestial", "transcen", "awaken", "enlighten", "bliss",
            "harmony", "virtue", "wisdom", "compassion",
        ],
        "suffixes": [
            "spirit", "faith", "soul", "grace", "love", "light",
            "truth", "hope", "glory", "peace", "mercy", "blessing",
            "prayer", "praise", "worship", "temple", "shrine",
            "heaven", "divine", "sacred", "holy", "eternal",
            "vision", "path", "way", "journey", "quest", "calling",
        ],
    },

    # ------------------------------------------------------------------
    # TECHNOLOGY / DIGITAL / AI
    # ------------------------------------------------------------------
    "tech": {
        "prefixes": [
            "tech", "cyber", "digi", "data", "code", "net", "web",
            "app", "ai", "cloud", "smart", "byte", "pixel", "logic",
            "system", "auto", "robot", "nano", "micro", "macro",
            "algo", "neural", "deep", "machine", "learn", "compute",
            "process", "stream", "sync", "async", "api", "sdk",
            "dev", "ops", "infra", "arch", "deploy", "scale",
            "agile", "lean", "sprint", "iter", "proto", "beta",
            "alpha", "release", "open", "source", "stack", "front",
            "back", "full", "platform", "infra", "server", "client",
        ],
        "suffixes": [
            "tech", "ware", "soft", "net", "sys", "lab", "hub",
            "io", "ai", "ml", "bot", "fy", "ly", "ify", "ize",
            "app", "platform", "service", "cloud", "grid", "flow",
            "stack", "base", "core", "engine", "layer", "module",
            "node", "cluster", "mesh", "fabric", "chain", "stream",
            "forge", "works", "craft", "build", "deploy", "ops",
        ],
    },

    # ------------------------------------------------------------------
    # FINANCE / INVESTMENT / WEALTH
    # ------------------------------------------------------------------
    "finance": {
        "prefixes": [
            "fin", "cap", "fund", "bank", "invest", "wealth", "money",
            "asset", "equity", "bond", "trade", "earn", "profit",
            "gain", "return", "value", "grow", "yield", "hedge",
            "risk", "port", "index", "market", "exchange", "broker",
            "credit", "debit", "loan", "debt", "spend", "save",
            "budget", "cost", "price", "rate", "quota", "ratio",
            "liquid", "solvent", "secure", "stable", "strong",
            "trust", "reserve", "treasury", "mint", "coin",
            "crypto", "token", "block", "chain", "ledger",
        ],
        "suffixes": [
            "fund", "capital", "invest", "wealth", "bank", "fin",
            "market", "trade", "exchange", "net", "profit", "gain",
            "yield", "value", "asset", "equity", "trust", "group",
            "holdings", "partners", "ventures", "solutions",
            "advisory", "management", "services", "analytics",
        ],
    },

    # ------------------------------------------------------------------
    # EDUCATION / KNOWLEDGE / LEARNING
    # ------------------------------------------------------------------
    "education": {
        "prefixes": [
            "edu", "learn", "know", "wise", "acad", "scholar",
            "mind", "teach", "study", "read", "write", "think",
            "skill", "train", "master", "class", "school", "college",
            "campus", "forum", "studio", "mentor", "coach", "guide",
            "lead", "inspire", "spark", "question", "discover",
            "explore", "create", "innovate", "solve", "design",
            "build", "maker", "craft", "lab", "open", "free",
            "digital", "online", "global", "future", "next",
            "life", "long", "early", "young", "grow", "evolve",
        ],
        "suffixes": [
            "edu", "learn", "academy", "school", "institute",
            "university", "college", "campus", "center", "lab",
            "studio", "workshop", "class", "course", "program",
            "hub", "network", "community", "forum", "circle",
            "think", "knowledge", "wisdom", "smart", "skills",
        ],
    },

    # ------------------------------------------------------------------
    # SECURITY / PROTECTION / TRUST
    # ------------------------------------------------------------------
    "security": {
        "prefixes": [
            "safe", "guard", "shield", "protect", "secure", "lock",
            "fort", "armor", "watch", "monitor", "defend", "alert",
            "trust", "verify", "certify", "auth", "encrypt", "firewall",
            "sentinel", "patrol", "scan", "detect", "prevent", "block",
            "barrier", "vault", "key", "access", "control", "manage",
            "risk", "threat", "audit", "comply", "enforce", "report",
            "intel", "counter", "rapid", "response", "recover",
            "resilient", "robust", "solid", "strong", "stable",
        ],
        "suffixes": [
            "guard", "shield", "watch", "protect", "secure", "safe",
            "lock", "vault", "key", "armor", "fort", "wall",
            "sentinel", "patrol", "scan", "detect", "alert", "monitor",
            "control", "auth", "trust", "verify", "certify",
            "audit", "comply", "solutions", "services", "systems",
        ],
    },

    # ------------------------------------------------------------------
    # ENERGY / POWER GENERATION / CLEAN TECH
    # ------------------------------------------------------------------
    "energy": {
        "prefixes": [
            "power", "volt", "amp", "flux", "ray", "wave", "beam",
            "charge", "spark", "blaze", "fuel", "burn", "glow",
            "bright", "radiant", "lumino", "photo", "thermo", "electro",
            "nuclear", "fusion", "fission", "plasma", "hydrogen",
            "solar", "wind", "hydro", "geotherm", "tidal", "biomass",
            "battery", "capacitor", "turbine", "generator", "grid",
            "micro", "macro", "smart", "green", "clean", "renew",
            "infra", "storage", "network", "distrib", "transmit",
        ],
        "suffixes": [
            "power", "energy", "volt", "watt", "flux", "charge",
            "spark", "beam", "ray", "light", "glow", "radiance",
            "cell", "battery", "grid", "network", "system",
            "generator", "turbine", "engine", "plant", "works",
            "solar", "wind", "hydro", "clean", "green", "renew",
        ],
    },

    # ------------------------------------------------------------------
    # SPACE / COSMOS / ASTRONOMY
    # ------------------------------------------------------------------
    "space": {
        "prefixes": [
            "astro", "cosmo", "orbit", "luna", "solar", "galaxy",
            "nova", "star", "cosmos", "deep", "beyond", "horizon",
            "infinite", "void", "aether", "nebula", "quasar", "pulsar",
            "comet", "meteor", "asteroid", "planet", "stellar", "interstellar",
            "cosmic", "celestial", "graviton", "photon", "quantum",
            "dark", "black", "white", "red", "blue", "hyper",
            "warp", "jump", "launch", "flight", "mission", "discovery",
            "pioneer", "voyager", "explorer", "craft", "probe",
        ],
        "suffixes": [
            "star", "nova", "orbit", "cosmos", "galaxy", "nebula",
            "space", "sky", "sphere", "field", "zone", "belt",
            "station", "base", "port", "dock", "launch", "mission",
            "explorer", "voyager", "pioneer", "craft", "ship",
            "probe", "lens", "scope", "view", "sight", "scape",
        ],
    },

    # ------------------------------------------------------------------
    # COMMON / EVERYDAY WORDS (emotional, descriptive, universal)
    # ------------------------------------------------------------------
    "common": {
        "prefixes": [
            # Emotions & values
            "love", "hope", "joy", "care", "kind", "brave", "true",
            "bold", "free", "pure", "good", "wise", "fair", "warm",
            "calm", "sure", "open", "real", "live", "vital",
            # Descriptive / sensory
            "bright", "clear", "clean", "fresh", "light", "soft",
            "swift", "sharp", "smooth", "cool", "wild", "raw",
            "rich", "vast", "wide", "deep", "high", "long", "strong",
            "full", "great", "grand", "fine", "last", "first",
            # Action / movement
            "rise", "grow", "build", "make", "move", "run", "lead",
            "reach", "seek", "find", "give", "help", "link", "flow",
            # Common nouns / concepts
            "life", "world", "home", "land", "mind", "hand", "time",
            "team", "city", "path", "way", "edge", "peak", "base",
            "point", "focus", "source", "scale", "loop", "bridge",
        ],
        "suffixes": [
            # Emotions & values
            "love", "hope", "joy", "care", "kind", "brave", "true",
            "bold", "free", "pure", "good", "wise", "fair",
            # Descriptive
            "bright", "light", "clear", "fresh", "strong", "sure",
            "sharp", "smooth", "swift", "wide", "deep", "rich",
            "full", "great", "fine", "real", "live",
            # Common nouns / concepts
            "life", "world", "home", "land", "mind", "time", "way",
            "path", "rise", "link", "flow", "edge", "peak", "hub",
            "zone", "side", "place", "land", "scape",
        ],
    },

    # ------------------------------------------------------------------
    # SOCIAL / COMMUNITY / PEOPLE
    # ------------------------------------------------------------------
    "social": {
        "prefixes": [
            "social", "people", "community", "connect", "share",
            "together", "group", "team", "crew", "tribe", "circle",
            "family", "friend", "partner", "ally", "fellow",
            "collab", "crowd", "public", "open", "civic", "citizen",
            "voice", "speak", "listen", "talk", "chat", "converse",
            "engage", "interact", "relate", "bond", "unite", "join",
            "belong", "include", "embrace", "welcome", "invite",
        ],
        "suffixes": [
            "social", "connect", "share", "link", "network", "hub",
            "community", "forum", "circle", "group", "team", "crew",
            "tribe", "squad", "family", "friends", "ally", "partner",
            "talk", "chat", "voice", "together", "collab",
        ],
    },

    # ------------------------------------------------------------------
    # FOOD & BEVERAGE / TASTE / NOURISHMENT
    # ------------------------------------------------------------------
    "food": {
        "prefixes": [
            "fresh", "pure", "natural", "organic", "whole", "raw",
            "craft", "artisan", "home", "local", "farm", "harvest",
            "taste", "flavor", "aroma", "savor", "relish", "gourmet",
            "feast", "dine", "bite", "sip", "brew", "bake", "roast",
            "spice", "herb", "sweet", "savory", "umami", "bold",
            "rich", "smooth", "crisp", "tender", "golden", "warm",
            "cool", "chill", "heat", "steam", "smoke", "blend",
        ],
        "suffixes": [
            "fresh", "pure", "taste", "flavor", "bite", "sip",
            "brew", "roast", "blend", "mix", "bake", "craft",
            "garden", "farm", "harvest", "market", "table",
            "feast", "fare", "kitchen", "pantry", "bar", "café",
        ],
    },

    # ------------------------------------------------------------------
    # SPORTS / FITNESS / PERFORMANCE
    # ------------------------------------------------------------------
    "sports": {
        "prefixes": [
            "athletic", "sport", "fit", "active", "agile", "speed",
            "power", "strength", "endure", "stamina", "peak", "max",
            "champion", "victor", "elite", "pro", "game", "play",
            "compete", "win", "score", "goal", "drive", "push",
            "train", "sprint", "climb", "lift", "throw", "kick",
            "strike", "block", "guard", "pivot", "flex", "lean",
            "swift", "quick", "fast", "strong", "tough", "hard",
            "fierce", "bold", "brave", "surge", "rally", "rise",
        ],
        "suffixes": [
            "sport", "fit", "active", "pro", "athlete", "champ",
            "victor", "elite", "peak", "max", "power", "force",
            "speed", "sprint", "endure", "strength", "flex", "surge",
            "game", "play", "match", "league", "club", "team",
            "arena", "stadium", "track", "field", "court", "ring",
        ],
    },

    # ------------------------------------------------------------------
    # TRAVEL / ADVENTURE / EXPLORATION
    # ------------------------------------------------------------------
    "travel": {
        "prefixes": [
            "wander", "explore", "discover", "venture", "roam", "trek",
            "journey", "voyage", "travel", "tour", "guide", "path",
            "trail", "route", "map", "compass", "horizon", "vista",
            "global", "world", "earth", "cross", "trans", "beyond",
            "far", "wide", "open", "free", "wild", "remote", "vast",
            "summit", "peak", "ridge", "valley", "shore", "coast",
            "sea", "sky", "cloud", "high", "deep", "below",
        ],
        "suffixes": [
            "wander", "explore", "journey", "voyage", "venture", "trek",
            "roam", "discover", "tour", "travel", "path", "trail",
            "route", "map", "horizon", "vista", "escape", "retreat",
            "getaway", "adventure", "quest", "expedition", "safari",
            "nomad", "pilgrim", "rover", "ranger", "explorer",
        ],
    },

    # ------------------------------------------------------------------
    # ARTS / CREATIVITY / DESIGN
    # ------------------------------------------------------------------
    "arts": {
        "prefixes": [
            "art", "create", "design", "craft", "make", "build",
            "draw", "paint", "sculpt", "compose", "write", "film",
            "photo", "music", "sound", "voice", "color", "form",
            "shape", "space", "light", "shadow", "texture", "rhythm",
            "harmony", "balance", "flow", "express", "imagine",
            "vision", "dream", "inspire", "spark", "idea", "concept",
            "story", "narrative", "scene", "frame", "lens", "stage",
        ],
        "suffixes": [
            "art", "craft", "design", "create", "make", "build",
            "studio", "lab", "works", "forge", "house", "gallery",
            "stage", "scene", "show", "print", "press", "publish",
            "media", "film", "sound", "music", "vision", "lens",
        ],
    },

}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CLEAN_RE = re.compile(r"[^a-z]")


def _clean(s: str) -> str:
    return _CLEAN_RE.sub("", s.lower().strip())


def get_prefixes(themes: List[str]) -> List[str]:
    """Return a deduplicated, cleaned list of prefix morphemes for the given themes."""
    seen: Set[str] = set()
    out: List[str] = []
    for theme in themes:
        bank = THEME_BANKS.get(theme, {})
        for raw in bank.get("prefixes", []):
            cleaned = _clean(raw)
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                out.append(cleaned)
    return out


def get_suffixes(themes: List[str]) -> List[str]:
    """Return a deduplicated, cleaned list of suffix morphemes for the given themes."""
    seen: Set[str] = set()
    out: List[str] = []
    for theme in themes:
        bank = THEME_BANKS.get(theme, {})
        for raw in bank.get("suffixes", []):
            cleaned = _clean(raw)
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                out.append(cleaned)
    return out


def get_theme_source(morpheme: str, themes: List[str]) -> List[str]:
    """Return the theme(s) that contain a given morpheme (for provenance)."""
    m = _clean(morpheme)
    sources: List[str] = []
    for theme in themes:
        bank = THEME_BANKS.get(theme, {})
        all_m = [_clean(x) for x in bank.get("prefixes", []) + bank.get("suffixes", [])]
        if m in all_m:
            sources.append(theme)
    return sources


ALL_THEME_NAMES: List[str] = list(THEME_BANKS.keys())

DEFAULT_THEMES: List[str] = [
    "power", "government", "business", "healthcare", "environment",
    "religion", "tech", "finance", "education", "security",
    "energy", "space", "common", "social",
]
