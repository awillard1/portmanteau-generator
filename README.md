# portmanteau_power

A small, maintainable **v4 portmanteau / name generator** with:

- ✅ Multi-domain, configurable **theme banks** (prefixes & suffixes)
- ✅ Character **trigram** language-model scoring for pronounceability
- ✅ **Phoneme-based** scoring via CMU pronouncing dictionary (optional)
- ✅ **Smarter join strategies**: overlap, smooth, splice — with seam scoring
- ✅ **Diversity** selection via MMR-style signature capping
- ✅ Full **explainability** output (JSONL provenance + TSV scores)
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

# With TSV score output
python -m portmanteau_power.cli input.txt output.txt \
    --target-size 500 \
    --include-scores \
    --themes common,power,space
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
                              [--min-len MIN_LEN]
                              [--max-len MAX_LEN]
                              [--per-root-variants PER_ROOT_VARIANTS]
                              [--per-pair-keep PER_PAIR_KEEP]
                              [--allow-triples]
                              [--banned-substrings A,B,...]
                              [--include-scores]
                              [--explain JSONL_PATH]
                              [--version]
                              input output

portmanteau_power v4.0.0 – configurable portmanteau / name generator.

positional arguments:
  input                 Input text file (one term per line).
  output                Output file for generated names.

options:
  -h, --help            show this help message and exit
  --target-size N       Max number of names to output. (default: 5000)
  --config PATH         YAML or JSON config file (overrides built-in defaults).
  --themes THEME,...    Comma-separated list of themes to enable.
                        Available: power, government, business, healthcare,
                          environment, religion, tech, finance, education,
                          security, energy, space, common, social, food, sports,
                          travel, arts
                        (default: power,government,business,healthcare,
                          environment,religion,tech,finance,education,security,
                          energy,space,common,social)
  --min-len MIN_LEN     Minimum output name length. (default: 5)
  --max-len MAX_LEN     Maximum output name length. (default: 12)
  --per-root-variants N Max WordNet variants kept per root. (default: 70)
  --per-pair-keep N     Top candidates kept per pairwise join. (default: 10)
  --allow-triples       Enable limited triple blends (slower).
  --banned-substrings   Comma-separated substrings to ban from output.
  --include-scores      Write TSV output (name + score breakdown columns).
  --explain JSONL_PATH  Write JSONL provenance file (one record per name).
  --version             Show version and exit.
```

---

## Theme Banks

The following themes ship with the generator. Each supplies **prefixes** and **suffixes** derived from domain vocabulary. Themes can be mixed freely.

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

## Config File

Copy and edit `configs/default.yml`:

```yaml
themes:
  enabled: [power, tech, common, space]

scoring:
  weights:
    ngram: 0.35
    wordfreq: 0.20
    phoneme: 0.15
    seam: 0.15
    structure: 0.15

constraints:
  min_length: 5
  max_length: 12
  banned_substrings:
    - "hate"
    - "crud"

join:
  per_root_variants: 70
  allow_triples: false
```

---

## Output Formats

### Plain text (default)
One name per line.

### TSV (`--include-scores`)
```
name    score   ngram   wordfreq    phoneme seam    structure
novacore    2.1470  0.7200  0.4800  1.0000  0.7133  0.5920
...
```

### JSONL (`--explain <file>`)
One JSON object per line with full provenance:
```json
{
  "name": "novacore",
  "score": 2.147,
  "score_breakdown": {"ngram": 0.72, "wordfreq": 0.48, "phoneme": 1.0, "seam": 0.71, "structure": 0.59},
  "components": ["nova", "core"],
  "join_strategy": "overlap",
  "affixes_used": [],
  "theme_sources": ["power", "space"]
}
```

---

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Package Structure

```
portmanteau_power/
├── __init__.py     Version constant
├── cli.py          CLI entry point (argparse)
├── generator.py    Core generation pipeline
├── scoring.py      Trigram model, phoneme & seam scoring
├── themes.py       Multi-domain morpheme banks (prefixes/suffixes)
├── config.py       YAML/JSON config loader + CLI override merger
└── explain.py      Candidate dataclass + JSONL/TSV writers
configs/
└── default.yml     Default configuration file
tests/
└── test_basic.py   Minimal validation tests
```

---

## License

MIT
