"""
data.py – Static datasets for portmanteau_power v5.

Provides:
  BRAND_NAMES  – ~500 successful brand/product names used to train the n-gram
                 model so it "knows" what a catchy name sounds like.
  I18N_BLOCKLIST – mapping of ISO-639-1 language code → set of romanised
                   strings that are offensive/vulgar in that language.
                   Used by safe_international_filter().
"""

from __future__ import annotations

from typing import Dict, FrozenSet, Tuple

# ---------------------------------------------------------------------------
# Brand-name corpus
# ---------------------------------------------------------------------------
# ~500 well-known single-token brand / product names (all lowercase).
# Carefully selected to represent diverse phonetic patterns and categories.
# Only publicly known names are included; no trademark claim is made.

BRAND_NAMES: Tuple[str, ...] = (
    # Tech / Software
    "google", "apple", "amazon", "meta", "netflix", "spotify", "slack",
    "zoom", "uber", "lyft", "airbnb", "twitter", "instagram", "snapchat",
    "pinterest", "reddit", "discord", "twitch", "shopify", "stripe",
    "brex", "robinhood", "coinbase", "figma", "notion", "airtable",
    "linear", "vercel", "netlify", "github", "gitlab", "bitbucket",
    "docker", "datadog", "splunk", "elastic", "mongodb", "redis",
    "kafka", "snowflake", "databricks", "palantir", "nvidia", "qualcomm",
    "broadcom", "cisco", "oracle", "salesforce", "hubspot", "zendesk",
    "freshdesk", "intercom", "mixpanel", "amplitude", "segment",
    "twilio", "sendgrid", "mailchimp", "klaviyo", "braze", "iterable",
    "rollbar", "sentry", "pagerduty", "opsgenie", "statuspage",
    "cloudflare", "fastly", "akamai", "cloudinary", "imgix", "sanity",
    "contentful", "prismic", "strapi", "directus", "supabase",
    "firebase", "appwrite", "neon", "planetscale", "cockroach",
    "tidb", "fauna", "hasura", "prisma", "graphql", "apollo",
    "postman", "insomnia", "swagger", "redocly", "bump",
    "terraform", "ansible", "puppet", "chef", "nomad", "consul",
    "vault", "packer", "waypoint", "boundary", "envoy", "istio",
    "linkerd", "cilium", "calico", "flannel", "weave", "contour",
    "traefik", "caddy", "nginx", "apache", "haproxy", "varnish",
    "redis", "memcached", "rabbitmq", "celery", "sidekiq", "resque",
    "airflow", "prefect", "dagster", "mage", "temporal", "conductor",
    "camunda", "zeebe", "activemq", "nats", "pulsar", "kinesis",
    # Consumer / Retail
    "nike", "adidas", "puma", "reebok", "vans", "converse", "skechers",
    "timberland", "columbia", "patagonia", "lululemon", "underarmour",
    "champion", "hanes", "levis", "wrangler", "carhartt", "dickies",
    "gap", "zara", "mango", "uniqlo", "primark", "forever",
    "asos", "zalando", "revolve", "farfetch", "ssense", "mytheresa",
    "nordstrom", "saks", "neiman", "bloomingdale", "macys",
    "target", "walmart", "costco", "kroger", "safeway", "trader",
    "whole", "sprouts", "lidl",
    # Food / Beverage
    "starbucks", "dunkin", "subway", "chipotle", "panera", "sweetgreen",
    "shake", "whataburger", "sonic", "wendys", "chick",
    "dominos", "papa", "little", "wingstop", "popeyes",
    "panda", "taco", "denny", "waffle", "cracker",
    "yoplait", "chobani", "siggi", "noosa", "oikos",
    "oatly", "ripple", "califia", "silk", "almond",
    "kombucha", "kefir", "soylent", "huel", "athletic",
    "red", "monster", "rockstar", "celsius", "reign",
    "nespresso", "keurig", "breville", "vitamix", "ninja",
    "instant", "cuisinart", "kitchenaid", "dyson", "shark",
    "roomba", "irobot",
    # Fintech / Finance
    "stripe", "square", "paypal", "venmo", "cashapp", "zelle",
    "chime", "revolut", "monzo", "nubank", "dave",
    "current", "varo", "sofi", "affirm", "klarna", "afterpay",
    "sezzle", "zip", "upstart", "prosper", "lending",
    "betterment", "wealthfront", "acorns", "stash", "qapital",
    "webull", "tastyworks", "tradier", "alpaca", "polygon",
    "coinbase", "kraken", "binance", "gemini", "ftx", "dydx",
    # Healthcare
    "hims", "hers", "ro", "noom", "calm", "headspace", "sanvello",
    "teladoc", "amwell", "doxy", "doximity", "zocdoc", "practo",
    "pillpack", "alto", "capsule", "truepill", "epocrates",
    "veracyte", "illumina", "pacbio", "nanopore", "grail",
    "guardant", "tempus", "flatiron", "veeva", "medidata",
    "cerner", "epic", "allscripts", "athena", "eclinicalworks",
    # Energy / Sustainability
    "tesla", "rivian", "lucid", "fisker", "lordstown", "canoo",
    "proterra", "workhorse", "nikola", "hyliion",
    "bloom", "sunrun", "vivint", "sunnova", "sunpower",
    "nextera", "enphase", "solaredge", "sma", "huawei",
    "orsted", "vestas", "siemens", "ge", "vestas",
    # Media / Entertainment
    "spotify", "tidal", "deezer", "soundcloud", "bandcamp",
    "youtube", "vimeo", "wistia", "loom", "screencast",
    "substack", "medium", "ghost", "wordpress", "squarespace",
    "wix", "webflow", "framer", "cargo", "format",
    "canva", "adobe", "figma", "sketch", "invision", "zeplin",
    "miro", "mural", "lucid", "whimsical", "figjam",
    # SaaS / Productivity
    "notion", "roam", "obsidian", "logseq", "craft", "bear",
    "evernote", "onenote", "simplenote", "standard",
    "todoist", "things", "omnifocus", "asana", "monday",
    "trello", "jira", "linear", "height", "shortcut",
    "basecamp", "campfire", "twist", "flock", "pumble",
    "teams", "webex", "whereby", "jitsi", "livekit",
    "mattermost", "rocket", "chatwoot", "freshchat",
    # Travel / Mobility
    "airbnb", "vrbo", "booking", "expedia", "kayak", "hopper",
    "turo", "getaround", "zipcar", "bird", "lime", "spin",
    "scoot", "wheels", "super", "hyrecar",
    # Education
    "coursera", "udemy", "edx", "udacity", "pluralsight",
    "duolingo", "babbel", "rosetta", "pimsleur", "busuu",
    "quizlet", "kahoot", "nearpod", "classkick", "seesaw",
    "canvas", "blackboard", "schoology", "moodle", "brightspace",
    # Misc / Short punchy names
    "bolt", "brex", "deel", "dolt", "drip", "drift",
    "dune", "flow", "frax", "gust", "heap", "helm",
    "hull", "iris", "kite", "lark", "lens", "lift",
    "lime", "link", "loom", "lore", "lume", "lyra",
    "mars", "mesh", "mist", "monk", "moon", "muse",
    "myth", "nest", "nova", "novu", "nuru", "orca",
    "oryx", "otis", "otto", "pace", "pact", "path",
    "peak", "pear", "pike", "pika", "pine", "ping",
    "pipe", "plex", "plot", "poke", "pond", "port",
    "post", "prism", "prose", "puck", "pulp", "pump",
    "pure", "push", "rack", "rain", "ramp", "rasa",
    "rate", "raze", "reef", "reel", "rem", "rent",
    "repo", "rest", "ring", "riot", "rise", "roam",
    "roca", "rock", "rode", "roll", "rome", "root",
    "rope", "rose", "rove", "rumi", "rune", "rush",
    "rust", "safe", "sage", "sail", "salt", "sand",
    "sard", "seed", "seek", "seep", "seer", "send",
    "sera", "shed", "ship", "shot", "show", "side",
    "sift", "sign", "silk", "sing", "sire", "site",
    "skew", "skip", "slab", "slag", "slap", "slat",
    "slim", "slip", "slot", "snow", "soil", "sold",
    "sole", "soma", "song", "sort", "soul", "span",
    "spec", "spin", "spot", "sprout", "squad", "star",
    "stem", "step", "stir", "stop", "such", "suit",
    "sunk", "surf", "swat", "swipe", "sync", "tack",
    "tags", "tale", "talk", "tall", "tank", "tape",
    "task", "team", "tell", "temp", "term", "text",
    "thin", "tide", "tile", "tilt", "time", "ting",
    "tint", "tips", "toll", "tome", "tone", "tool",
    "tore", "torn", "toss", "tour", "town", "tray",
    "trek", "trim", "trip", "trot", "troy", "tune",
    "turf", "turn", "twin", "type", "vale", "vela",
    "vibe", "vice", "view", "vile", "vine", "vise",
    "void", "vole", "volt", "vote", "wade", "wake",
    "walk", "wall", "wand", "ward", "warp", "watt",
    "wave", "weld", "well", "wend", "wide", "wiki",
    "wild", "wilt", "wind", "wing", "wire", "wise",
    "wish", "with", "woke", "womb", "wood", "word",
    "work", "worm", "wrap", "writ", "xeon", "xero",
    "yell", "yield", "zeal", "zero", "zest", "zinc",
    "zone", "zoom",
)

# ---------------------------------------------------------------------------
# International safety blocklist
# ---------------------------------------------------------------------------
# Maps language code → frozenset of *lowercase romanised* strings that are
# offensive/vulgar in that language.  Portmanteau candidates containing any
# of these as a substring will be flagged when --safe-international is used.
#
# Intentionally conservative: only clear, widely-agreed offensive terms.
# The purpose is to catch accidental matches (e.g. "cul" in French) that
# could embarrass a brand in foreign markets.

I18N_BLOCKLIST: Dict[str, FrozenSet[str]] = {
    "es": frozenset({
        "puta", "puto", "mierda", "culo", "culos", "pendejo", "pendeja",
        "joder", "follar", "verga", "polla", "cojon", "cojones",
        "chinga", "chingo", "cabron", "piche", "wuey", "guey",
        "pinche", "marica", "maricon",
    }),
    "fr": frozenset({
        "putain", "merde", "con", "cul", "couille", "couilles",
        "connard", "connasse", "baise", "foutre", "salope",
        "enculer", "encule", "nichon", "teub", "zob",
    }),
    "de": frozenset({
        "scheiße", "scheisse", "fick", "ficken", "arsch", "fotze",
        "wichser", "hurensohn", "schlampe", "miststuck", "kacke",
        "pissen", "wixen",
    }),
    "it": frozenset({
        "cazzo", "minchia", "stronzo", "vaffanculo", "puttana",
        "figa", "coglione", "merda", "culo", "porco",
    }),
    "pt": frozenset({
        "puta", "caralho", "merda", "cona", "foder", "foda",
        "viado", "porra", "buceta", "safado",
    }),
    "nl": frozenset({
        "kut", "lul", "neuken", "tering", "hoer", "tyfus",
        "kanker", "godverdomme", "slet", "eikel",
    }),
    "ru": frozenset({
        "khuy", "pizda", "blyat", "suka", "pidor", "ebat",
        "yebat", "mudak", "zalupa", "ebany",
    }),
    "ja": frozenset({
        "kuso", "manko", "chinpo", "chikushо", "chikusho",
        "omanko", "chinchiku", "yariman",
    }),
    "zh": frozenset({
        "tama", "wocao", "shabi", "caonima", "tamade", "gongyangde",
        "hundan", "pofu", "jiba",
    }),
    "hi": frozenset({
        "madarchod", "behenchod", "chutiya", "gaand", "lund",
        "chut", "bhosda", "randi", "saala", "haramzada",
    }),
    "ar": frozenset({
        "kus", "ayr", "zibb", "sharmouta", "ibn", "kalb",
        "wahsh", "metnaak",
    }),
    "ko": frozenset({
        "shibal", "ssibal", "gaeseki", "jot", "boji",
        "ssibalgom", "byeongsin", "michinom",
    }),
    # Universal / English vulgar substrings worth catching
    "en": frozenset({
        "fuck", "shit", "cunt", "nigga", "nigger", "faggot",
        "twat", "cock", "dick", "bitch", "whore", "slut",
        "pussy", "asshole", "bastard", "retard",
    }),
}

# Flattened set for fast membership testing across all languages
ALL_BLOCKLIST: FrozenSet[str] = frozenset(
    w for words in I18N_BLOCKLIST.values() for w in words
)


def safe_international_filter(word: str) -> bool:
    """
    Return True if *word* (lowercase) contains no entry from *ALL_BLOCKLIST*.
    This is a conservative, additive safety check; it is off by default.
    """
    for bad in ALL_BLOCKLIST:
        if bad in word:
            return False
    return True
