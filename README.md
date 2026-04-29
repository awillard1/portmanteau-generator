# portmanteau_power

A **v5 portmanteau / name generator** with a full brand-quality scoring pipeline, international safety, domain checking, AI re-ranking, and an optional web API.

- ✅ Multi-domain, configurable **theme banks** (18 domains)
- ✅ Character **trigram** language model seeded with a **~500-name brand corpus**
- ✅ **Phoneme-based** scoring via CMU pronouncing dictionary (optional)
- ✅ **Rule-based G2P** pronounceability score for novel coined words
- ✅ **Stress-pattern** bonus (trochee/iamb preference, via CMU dict)
- ✅ **Melody score**: alliteration + vowel harmony
- ✅ **3 join strategies** (overlap, smooth, splice) + optional triple blends
- ✅ **MMR-style diversity** selection
- ✅ Full **explainability** (JSONL provenance + TSV scores)
- ✅ **International safety filter** (13 languages; `--safe-international`)
- ✅ **Domain availability check** via DNS (`--check-domains`)
- ✅ **AI re-ranking** via local Ollama LLM (`--rerank-top N`)
- ✅ **FastAPI web API** (optional; `pip install "portmanteau-power[api]"`)
- ✅ **Config file** (YAML or JSON) for all knobs
- ✅ Runs **offline** — no network access required after initial NLTK download

---

## Install

```bash
pip install nltk wordfreq pronouncing pyyaml
# One-time NLTK data download (requires network once):
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
```

Or install the package in editable mode:

```bash
pip install -e ".[dev]"
```

For the FastAPI web API:

```bash
pip install -e ".[api]"
```

---

## Quick Start

```bash
# Minimal run
python -m portmanteau_power.cli input.txt output.txt --target-size 200

# With theme selection and explainability
python -m portmanteau_power.cli input.txt output.txt \
    --target-size 5000 \
    --themes power,tech,government,business,healthcare,environment,religion \
    --config configs/default.yml \
    --explain out.jsonl

# With TSV score output (all 8 scoring dimensions)
python -m portmanteau_power.cli input.txt output.txt \
    --target-size 500 \
    --include-scores \
    --themes common,power,space

# International safety + domain checking
python -m portmanteau_power.cli input.txt output.txt \
    --target-size 200 \
    --safe-international \
    --check-domains \
    --domain-tlds com,io \
    --explain out.jsonl

# AI re-ranking via local Ollama (Ollama must be running)
python -m portmanteau_power.cli input.txt output.txt \
    --target-size 200 \
    --rerank-top 20 \
    --rerank-model llama3 \
    --rerank-context "AI-powered productivity app"
```

`input.txt` – one term per line:

```
power
nova
forge
tech
hope
```

---

## Full CLI Help

```
usage: portmanteau_power.cli [-h]
                              [--target-size TARGET_SIZE]
                              [--config PATH]
                              [--themes THEME,...]
                              [--min-len MIN_LEN] [--max-len MAX_LEN]
                              [--per-root-variants N] [--per-pair-keep N]
                              [--allow-triples]
                              [--banned-substrings A,B,...]
                              [--safe-international]
                              [--check-domains] [--domain-tlds com,net,...]
                              [--rerank-top N] [--rerank-model MODEL]
                              [--ollama-url URL] [--rerank-context TEXT]
                              [--include-scores]
                              [--explain JSONL_PATH]
                              [--version]
                              input output

portmanteau_power v5.0.0 – configurable portmanteau / name generator.

  --target-size N       Max number of names to output. (default: 5000)
  --config PATH         YAML or JSON config file (overrides built-in defaults).
  --themes THEME,...    Available: power, government, business, healthcare,
                          environment, religion, tech, finance, education,
                          security, energy, space, common, social, food,
                          sports, travel, arts
  --min-len / --max-len   Length constraints (default: 5–12).
  --per-root-variants N   Max WordNet variants per root. (default: 70)
  --per-pair-keep N       Top candidates per pairwise join. (default: 10)
  --allow-triples         Enable triple blends (slower).
  --banned-substrings     Comma-separated substrings to ban.
  --safe-international    Filter offensive names in 13 languages.
  --check-domains         DNS-check domain availability.
  --domain-tlds com,…     TLDs to check (default: com,net,io).
  --rerank-top N          Re-rank top N names via local Ollama LLM.
  --rerank-model MODEL    Ollama model (default: llama3).
  --ollama-url URL        Ollama server URL (default: http://localhost:11434).
  --rerank-context TEXT   Brand description for AI re-ranking.
  --include-scores        Write TSV with all 8 score breakdown columns.
  --explain JSONL_PATH    Write JSONL provenance file.
  --version               Show version and exit.
```

---

## Theme Banks

| Theme | Domain | Example morphemes |
|---|---|---|
| `power` | Brand energy / strength | neo, hyper, ultra, titan, apex, core, forge, pulse, vault |
| `government` | Civic / political | civic, demo, nation, state, legis, bureau, council, charter |
| `business` | Enterprise / commerce | corp, brand, market, venture, capital, scale, launch, trade |
| `healthcare` | Medical / wellness | med, bio, vita, thera, pharma, clinic, heal, wellness, care |
| `environment` | Ecology / sustainability | eco, terra, green, solar, hydro, renew, bloom, sustain |
| `religion` | Spirituality / faith | spirit, faith, holy, divine, grace, soul, light, bliss, peace |
| `tech` | Technology / AI / digital | tech, cyber, digi, data, cloud, ai, neural, algo, deploy |
| `finance` | Investment / wealth | fin, cap, fund, equity, hedge, crypto, token, yield, asset |
| `education` | Knowledge / learning | edu, learn, wise, acad, mentor, skill, train, discover |
| `security` | Protection / trust | safe, guard, shield, protect, secure, vault, sentinel, audit |
| `energy` | Power generation | volt, flux, beam, spark, solar, hydro, turbine, grid, clean |
| `space` | Astronomy / cosmos | astro, cosmo, orbit, luna, nova, stellar, nebula, horizon |
| `common` | Everyday / emotional | **love**, hope, joy, care, kind, brave, true, life, world, home |
| `social` | Community / people | social, connect, share, tribe, collab, voice, together |
| `food` | Cuisine / taste | fresh, craft, artisan, harvest, roast, blend, savor, aroma |
| `sports` | Fitness / performance | athletic, agile, sprint, champion, elite, surge, rally |
| `travel` | Adventure / exploration | wander, explore, voyage, trek, horizon, vista, nomad |
| `arts` | Creativity / design | art, design, craft, compose, vision, narrative, studio |

---

## Scoring (v5)

Eight weighted components feed the final score:

| Component | Weight | Description |
|---|---|---|
| `ngram` | 0.28 | Character-trigram fit against brand corpus + WordNet + roots |
| `wordfreq` | 0.16 | English word frequency (Zipf score via `wordfreq`) |
| `phoneme` | 0.08 | CMU pronouncing-dict presence (rewards real/near-real words) |
| `g2p` | 0.10 | Rule-based grapheme-to-phoneme phonotactic score for novel words |
| `seam` | 0.13 | Smoothness of letter transitions at join boundaries |
| `structure` | 0.12 | Syllable count, vowel ratio, hard-consonant balance |
| `stress` | 0.07 | Stress pattern (trochee > iamb > other) via CMU dict |
| `melody` | 0.06 | Alliteration + vowel harmony |

Plus an additive **morpheme bonus** (0.55 per recognised theme morpheme, capped at 2.0).

---

## Config File

Copy and edit `configs/default.yml`:

```yaml
themes:
  enabled: [power, tech, common, space]

scoring:
  weights:
    ngram: 0.28
    wordfreq: 0.16
    phoneme: 0.08
    g2p: 0.10
    seam: 0.13
    structure: 0.12
    stress: 0.07
    melody: 0.06

constraints:
  min_length: 5
  max_length: 12
  banned_substrings: ["hate", "crud"]

join:
  per_root_variants: 70
  allow_triples: false

features:
  safe_international: false
  domain_check_tlds: [com, net, io]
  rerank:
    top_n: 20
    model: llama3
    ollama_url: "http://localhost:11434"
    context: "a modern brand"
```

---

## Output Formats

### Plain text (default)
One name per line.

### TSV (`--include-scores`)
```
name    score   ngram   wordfreq    phoneme g2p seam    structure   stress  melody
novacore    2.1470  0.7200  0.4800  1.0000  0.72  0.7133  0.5920  0.65  0.55
```

### JSONL (`--explain <file>`)
```json
{
  "name": "novacore",
  "score": 2.147,
  "score_breakdown": {"ngram": 0.72, "wordfreq": 0.48, "phoneme": 1.0,
                      "g2p": 0.74, "seam": 0.71, "structure": 0.59,
                      "stress": 0.65, "melody": 0.55},
  "components": ["nova", "core"],
  "join_strategy": "overlap",
  "affixes_used": [],
  "theme_sources": ["power", "space"],
  "domain_available": {"name": "novacore", "com": false, "net": true, "io": true},
  "international_safe": true
}
```

---

## International Safety Filter

`--safe-international` blocks names containing offensive substrings in:
Spanish, French, German, Italian, Portuguese, Dutch, Russian (romanised),
Japanese (romanised), Chinese (pinyin), Hindi (romanised), Arabic (romanised),
Korean (romanised), and English.

---

## Domain Availability Check

`--check-domains` performs a DNS lookup for `<name>.<tld>` across each requested
TLD (default `.com`, `.net`, `.io`). Uses stdlib `socket` — **no external dependency**.
Runs concurrently for fast bulk checking.

> DNS non-resolution is a proxy for availability; always confirm through a registrar.

---

## AI Re-ranking (Ollama)

```bash
# Install and start Ollama
ollama serve && ollama pull llama3

python -m portmanteau_power.cli input.txt output.txt \
    --rerank-top 30 --rerank-model llama3 \
    --rerank-context "B2B SaaS security platform"
```

Uses stdlib `urllib` — **no extra Python package**. Falls back to score-order gracefully.

---

## FastAPI Web API

```bash
pip install "portmanteau-power[api]"
uvicorn portmanteau_power.api:app --reload --port 8000
```

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"words": ["power","nova","forge"], "target_size": 20,
       "themes": ["power","tech"], "safe_international": true}'
```

Interactive docs at `http://localhost:8000/docs`.

---

## Running Tests

```bash
pip install pytest
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
pytest tests/ -v
```

---

## Package Structure

```
portmanteau_power/
├── __init__.py     Version constant
├── cli.py          CLI entry point
├── generator.py    Core generation pipeline
├── scoring.py      Trigram, G2P, stress, melody, seam, phoneme scoring
├── themes.py       18-domain morpheme banks
├── data.py         Brand-name corpus + i18n safety blocklist
├── domain.py       DNS domain-availability checker
├── rerank.py       Ollama AI re-ranking (stdlib urllib)
├── api.py          FastAPI web API (optional)
├── config.py       YAML/JSON config loader
└── explain.py      Candidate dataclass + JSONL/TSV writers
configs/
└── default.yml     Default configuration (v5)
tests/
└── test_basic.py   39 tests covering all features
```

---

## License

MIT
