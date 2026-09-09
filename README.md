# 📊 Publication Intelligence & Research Impact Analysis Platform

<p>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white">
  <img alt="Streamlit" src="https://img.shields.io/badge/streamlit-1.63%2B-FF4B4B?logo=streamlit&logoColor=white">
  <img alt="pandas" src="https://img.shields.io/badge/pandas-3.0%2B-150458?logo=pandas&logoColor=white">
  <img alt="statsmodels" src="https://img.shields.io/badge/statsmodels-OLS%20%2B%20HC3-4C72B0">
  <img alt="Status" src="https://img.shields.io/badge/status-active-brightgreen">
  <img alt="Data" src="https://img.shields.io/badge/data-restricted%20%E2%80%94%20not%20redistributed-orange">
</p>

**COMP3888 Capstone · Team W11_02_P36**

An interactive analytical platform for exploring publication performance, research
impact, and collaboration patterns across the Go8 universities, built on
publication-level Scopus/SciVal bibliometric data. Six statistically-grounded
analyses, a Bauhaus-styled Streamlit interface, and a full bilingual documentation
set covering both the methodology and exactly which brief question each part
answers.

---

## Contents

- [Overview](#overview)
- [At a glance](#at-a-glance)
- [The six analyses](#the-six-analyses)
- [Documentation](#documentation)
- [Getting started](#getting-started)
- [Project structure](#project-structure)
- [Analysis pipeline](#analysis-pipeline)
- [Tech stack](#tech-stack)
- [Data & governance](#data--governance)
- [Deployment](#deployment)
- [Team](#team)

---

## Overview

This project develops an interactive analytical platform for exploring university
publication performance, research impact, and collaboration patterns using
publication-level bibliometric data. The platform supports data cleaning,
exploratory analysis, visualisation, and research-performance analysis — helping
identify publication trends, research strengths, collaboration patterns, and
potential improvement opportunities, with evidence-based insights to support
strategic research planning for the client, the University of Sydney.

**Design principles carried through every layer of this project:**
- **One implementation per metric.** Every derived figure (Q1 share, FWCI mean,
  top-decile share, …) is computed in exactly one place
  (`src/p36/metrics/metrics.py`) and imported everywhere else — never
  recomputed by hand in an analysis module or a Streamlit page.
- **Descriptive vs. tested, always labelled.** Five of the six analyses are
  descriptive statistics on the full (near-census) dataset; only the item 14
  regression carries p-values and confidence intervals — and every page says
  which kind of claim it's making.
- **Provisional assumptions, named and flagged.** Every threshold or scope
  decision the client hasn't confirmed yet (Q1 cutoff basis, self-citation
  handling, open-access null-handling, …) is a named constant in
  `src/p36/config.py`, marked `PROVISIONAL`, never presented as settled.

## At a glance

| | |
| --- | --- |
| **Universities covered** | 8 (Go8) — Adelaide, ANU, Monash, Sydney *(client)*, Melbourne, UNSW, UQ, UWA |
| **Publications, deduplicated** | 327,265 (from 385,664 raw per-university rows — 15.1% cross-university duplication) |
| **Analyses implemented** | 6 of the README's numbered items — 3, 6, 9, 14, 16, 17 |
| **Platform pages** | 6 Streamlit pages, Altair charts throughout, bilingual (EN/ZH) reference docs |
| **Regression model** | OLS, HC3-robust SE, field + document-type fixed effects, R² ≈ 0.019 |

## The six analyses

| # | Analysis | Core question | Module | Platform page |
| --- | --- | --- | --- | --- |
| 3 | Journal Tier & Q1 Analysis | What share of output sits in Q1 journals, and how does that vary — by tier, by field, by individual journal? | [`journal_tier.py`](src/p36/analysis/journal_tier.py) | [`2_Journal_Tier.py`](app/pages/2_Journal_Tier.py) |
| 6 | Research Field / Faculty Analysis | Which fields are strongest, improving, or under-performing? | [`field_analysis.py`](src/p36/analysis/field_analysis.py) | [`3_Field_Analysis.py`](app/pages/3_Field_Analysis.py) |
| 9 | International Collaboration Analysis | Are internationally co-authored papers cited more frequently — and does it hold within field and year? | [`international_collaboration.py`](src/p36/analysis/international_collaboration.py) | [`4_International_Collaboration.py`](app/pages/4_International_Collaboration.py) |
| 14 | Integrated Research Impact Driver Analysis | Holding the other factors constant, which of Q1 status, collaboration, open access, and document type actually associates with impact? | [`impact_drivers.py`](src/p36/analysis/impact_drivers.py) | [`5_Impact_Drivers.py`](app/pages/5_Impact_Drivers.py) |
| 16 | Go8 / Peer Benchmarking | How does Sydney perform relative to its Go8 peers, on volume, impact, Q1 share, and collaboration? | [`go8_benchmarking.py`](src/p36/analysis/go8_benchmarking.py) | [`1_Go8_Benchmarking.py`](app/pages/1_Go8_Benchmarking.py) |
| 17 | Scenario Analysis | What would mean impact look like under a hypothetical shift in Q1 share, collaboration, or open access? | [`scenario_analysis.py`](src/p36/analysis/scenario_analysis.py) | [`6_Scenario_Analysis.py`](app/pages/6_Scenario_Analysis.py) |

Every platform page opens with a **"Sub-questions this page answers"** panel —
a checklist mapping each chart back to the brief's actual bullet points,
including the ones not yet built (marked openly, not omitted).

## Documentation

| Document | What it's for |
| --- | --- |
| [Guidebook](https://claude.ai/code/artifact/680782eb-2079-4dc1-94e6-7efac2bfa886) | How to run and extend this project — bilingual EN/ZH |
| [Coverage Manual](https://claude.ai/code/artifact/fc3a9c2e-e2bf-45fa-a9fb-ab4f94bec688) | What the platform actually implements, and exactly which brief sub-question each part answers (✓/~/→/? per item) |
| [Methods Reference](https://claude.ai/code/artifact/795c53d8-ff1d-45b4-8a28-0faf1ecfb09d) | The statistics: why this threshold, why this chart type, full reasoning chains — one page per analysis item |
| [`docs/methodology.md`](docs/methodology.md) | The canonical, git-tracked metric definitions and PROVISIONAL flags — source of truth over the artifacts above if they ever drift |
| [`data/dictionary/data_dictionary.md`](data/dictionary/data_dictionary.md) | Every raw and derived column, with data-quality notes |
| [`docs/deployment-azure.md`](docs/deployment-azure.md) | Deploying this platform to Azure App Service |
| [Group Contract](Group%20contract.md) | Team working agreements, roles, and communication norms |

> The three linked pages above are private Claude Artifacts — share them from
> the page's own share menu if a teammate without access needs to open them.

## Getting started

The raw QS/Scopus per-university exports (`data/*.xlsx`) and the processed
dataset built from them (`data/processed/*.parquet`) are **not in this repo** —
they're licensed data, excluded via `.gitignore` rather than pushed to git
history (see [Data & governance](#data--governance)). Get the eight `.xlsx`
files from the [group data folder](https://github.sydney.edu.au/xili0060/COMP3888_W11_02_P36/tree/main/data)
and place them directly under `data/` before doing anything else — every step
below depends on them.

```bash
pip install -r requirements.txt

# One-time: clean + dedupe the raw exports into data/processed/*.parquet.
# Re-run after the raw .xlsx files change; the app itself never reads the
# raw exports directly, only this processed output. Run from src/ — there's
# no pyproject.toml/setup.py yet, so `p36` is only importable with src/ as
# the working directory.
cd src
python -m p36.build_dataset
cd ..

# Launch the platform — http://localhost:8501
streamlit run app/Home.py
```

## Project structure

```
comp3888/
├── app/                      Streamlit platform
│   ├── Home.py                 landing page
│   ├── theme.py                 Bauhaus design system + Altair theme
│   ├── lib.py                   cached data/analysis access (single source of truth for the UI)
│   └── pages/                   one page per analysis item (1_Go8_Benchmarking.py … 6_Scenario_Analysis.py)
├── src/p36/                  analysis package
│   ├── config.py                every named threshold/scope constant — PROVISIONAL ones flagged
│   ├── ingest.py, cleaning/     raw-export loading, dtype safety, deduplication
│   ├── dataset.py, build_dataset.py   processed-parquet read/write
│   ├── metrics/                 canonical metric implementations — the single source every module imports
│   └── analysis/                one module per README analysis item
├── data/
│   ├── dictionary/               data_dictionary.md (tracked)
│   ├── *.xlsx                    raw per-university exports (git-ignored — see above)
│   └── processed/                 built parquet files (git-ignored — see above)
├── docs/                      methodology.md, deployment-azure.md, meeting-notes/
├── .streamlit/config.toml     theme + toolbar config
└── requirements.txt
```

## Analysis pipeline

Every figure on every page passes through the same five layers, in the same
order — this is *why* the design principles above ("one implementation per
metric", cached wrappers only) work in practice, not just a rule on paper.

```
data/*.xlsx (8 raw per-university exports)
   │  src/p36/ingest.py + cleaning/        load, merge, enforce dtypes
   │  src/p36/build_dataset.py             run once, offline → writes parquet
   ▼
data/processed/*.parquet (raw + deduplicated)
   │  src/p36/dataset.py                   load_raw() / load_deduplicated() — reads the parquet, nothing else
   ▼
src/p36/analysis/prepare.py                prepared_raw() / prepared_deduplicated() — scope-filter +
   │                                         derived flags (is_international, …), shared by all six modules
   ▼
src/p36/analysis/<item>.py                 the actual statistics for one analysis item — groupby/apply,
   │                                         regression, etc. Imports metric implementations from
   │                                         src/p36/metrics/metrics.py and every named threshold from
   │                                         src/p36/config.py — never recomputes either by hand.
   ▼
app/lib.py                                 @st.cache_data wrapper — one get_*() function per analysis
   │                                         output, so Streamlit never recomputes on every widget click
   ▼
app/pages/N_*.py                           calls the lib.py wrapper, then only charts / formats / writes
                                             narrative — no statistics computed at this layer
```

**Worked example — Go8 Benchmarking, "Sydney's rank on mean FWCI"**
([1_Go8_Benchmarking.py](app/pages/1_Go8_Benchmarking.py), lines 49–58):

1. [`dataset.load_raw()`](src/p36/dataset.py) reads `publications_raw.parquet`.
2. [`prepare.prepared_raw()`](src/p36/analysis/prepare.py) scope-filters it and adds `is_international`.
3. [`lib.load_raw()`](app/lib.py) caches steps 1–2 for the session.
4. [`go8_benchmarking.benchmark_summary()`](src/p36/analysis/go8_benchmarking.py) groups by
   `source_university`, calls `metrics.mean_fwci` per group, orders the result with
   `config.CLIENT_UNIVERSITY` first.
5. [`lib.get_benchmark_summary()`](app/lib.py) caches step 4.
6. The page calls `get_benchmark_summary()` once and reuses the same table for the rank
   card, the bar chart, and the radar chart — one fetch, three visualisations.

**A cross-module dependency worth knowing:** `go8_benchmarking.institution_partner_flag()`
is imported and called directly by `scenario_analysis.py` (not routed through `app/lib.py`)
— see [scenario_analysis.py:129-131](src/p36/analysis/scenario_analysis.py#L129-L131). A
signature or behaviour change to that function affects the Scenario Analysis page too, even
though the two live in different analysis modules.

## Tech stack

- **Data:** pandas, pyarrow (parquet), openpyxl (reading the raw QS/Scopus exports)
- **Statistics:** statsmodels (OLS, HC3 robust SE), scipy
- **Platform:** Streamlit, Altair (Vega-Lite) — no Plotly, no JavaScript
- **Deployment:** Azure App Service (Linux, Python) — see [`docs/deployment-azure.md`](docs/deployment-azure.md)

## Data & governance

This project treats data provenance and metric consistency as first-class
concerns, not an afterthought:

- **Every threshold is a named constant**, not a magic number buried in an
  analysis module — see [`src/p36/config.py`](src/p36/config.py). Constants the
  client hasn't confirmed yet (the Q1 cutoff basis, self-citation handling,
  open-access null-handling, citation-window trimming, …) are explicitly
  marked `PROVISIONAL` and must carry that caveat wherever they appear in a
  finding.
- **The percentile direction was verified, not assumed** — Scopus/SciVal's
  convention is *lower percentile = better*, confirmed empirically against
  Field-Weighted Citation Impact before a single Q1 or highly-cited figure was
  computed (see `docs/methodology.md`).
- **Cross-field and cross-year comparisons always use a normalised metric**
  (FWCI or a SciVal percentile column), never raw citation counts, which
  differ 5–10× by citation culture alone.
- **The raw `.xlsx` exports and the processed `.parquet` files are
  deliberately excluded from git history** (`.gitignore`) — this is licensed
  Scopus/QS bibliometric data at individual-publication granularity, not ours
  to redistribute via a public or semi-public git remote. Anyone working on
  this repo needs to obtain the raw exports separately (see
  [Getting started](#getting-started)) and rebuild the processed dataset
  locally.

## Deployment

See [`docs/deployment-azure.md`](docs/deployment-azure.md) for the full,
tested command sequence to deploy this platform to Azure App Service,
including the WebSockets setting Streamlit requires, the pricing-tier
guidance, and — importantly — how to keep the deploy package from including
the raw per-university exports.

## Team

See [Group Contract](Group%20contract.md) for team members, roles, and working
agreements. [Group Wiki](https://github.sydney.edu.au/xili0060/COMP3888_W11_02_P36/wiki/COMP3888_W11_02_P36-wiki) ·
[Data folder](https://github.sydney.edu.au/xili0060/COMP3888_W11_02_P36/tree/main/data)
