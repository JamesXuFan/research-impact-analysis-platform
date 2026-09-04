# Publication Intelligence & Research Impact Analysis Platform
### COMP3888 Capstone Project · Team W11_02_P36

An analytical platform for exploring university publication performance, research impact, collaboration patterns, and data quality using publication-level bibliometric data.

## Project Overview

This project aims to develop an interactive analytical platform for exploring university publication performance, research impact, and collaboration patterns using publication-level bibliometric data. The platform will support data cleaning, exploratory analysis, visualisation, and research-performance analysis. It is intended to help users identify publication trends, research strengths, collaboration patterns, and potential improvement opportunities. The final system will provide evidence-based insights to support strategic research planning.

## Project Goals
## Dataset
[Data](https://github.sydney.edu.au/xili0060/COMP3888_W11_02_P36/tree/main/data)
## Wiki Page
[Goup Wiki](https://github.sydney.edu.au/xili0060/COMP3888_W11_02_P36/wiki/COMP3888_W11_02_P36-wiki)

## Setup

The raw QS/Scopus per-university exports (`data/*.xlsx`) and the processed
dataset built from them (`data/processed/*.parquet`) are **not in this repo** —
they're licensed data, excluded via `.gitignore` rather than pushed to git
history. Get them from the [Data](https://github.sydney.edu.au/xili0060/COMP3888_W11_02_P36/tree/main/data)
link above and place the eight `.xlsx` files directly under `data/` before
doing anything else; every step below depends on them.

```bash
pip install -r requirements.txt

# One-time: clean + dedupe the raw exports into data/processed/*.parquet.
# Re-run this after the raw .xlsx files change; the app itself never reads
# the raw exports directly, only this processed output. Run from src/ (no
# pyproject.toml/setup.py yet, so `p36` is only importable with src/ as the
# working directory — `python -m p36.build_dataset` from the repo root fails
# with ModuleNotFoundError).
cd src
python -m p36.build_dataset
cd ..

# Launch the platform (http://localhost:8501) — from the repo root
streamlit run app/Home.py
```

Deploying instead of running locally? See [docs/deployment-azure.md](docs/deployment-azure.md).

## Analysis
3. Journal Tier and Q1 Analysis
- ...
6. Research Field / Faculty Analysis
  - ...
9. International Collaboration Analysis
- ...
14. Integrated Research Impact Driver Analysis
  - ...
16. Go8 / Peer Benchmarking
- ...
17. Scenario Analysis
- ...
