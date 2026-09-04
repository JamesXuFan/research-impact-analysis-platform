"""Read/write the processed dataset — the persisted, cleaned form of the eight raw
QS exports, so downstream analysis never has to re-read and re-clean ~386k Excel
rows on every run.

Build it with ``python -m p36.build_dataset`` (see that module). Everything in this
file only *reads* what that script wrote.
"""

from pathlib import Path

import pandas as pd

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"

RAW_PATH = PROCESSED_DIR / "publications_raw.parquet"
DEDUPED_PATH = PROCESSED_DIR / "publications_deduplicated.parquet"


def load_raw() -> pd.DataFrame:
    """One row per (university, publication) claim — not de-duplicated.

    Use this for any *per-university* figure (a jointly-authored Go8 paper
    legitimately counts toward each contributing university's own output).
    """
    if not RAW_PATH.exists():
        raise FileNotFoundError(
            f"{RAW_PATH} does not exist yet. Run `python -m p36.build_dataset` first."
        )
    return pd.read_parquet(RAW_PATH)


def load_deduplicated() -> pd.DataFrame:
    """One row per unique publication (EID), collapsed across universities.

    Use this for any Go8-aggregate or cross-university benchmarking figure —
    see src/p36/ingest.py:deduplicate_by_eid for why this matters (15.1% of raw
    rows are duplicates of a publication already counted under another university).
    """
    if not DEDUPED_PATH.exists():
        raise FileNotFoundError(
            f"{DEDUPED_PATH} does not exist yet. Run `python -m p36.build_dataset` first."
        )
    return pd.read_parquet(DEDUPED_PATH)
