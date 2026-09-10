import os
from pathlib import Path

import pandas as pd

_DEFAULT_PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
PROCESSED_DIR = Path(os.environ.get("P36_DATA_DIR", str(_DEFAULT_PROCESSED_DIR)))

RAW_PATH = PROCESSED_DIR / "publications_raw.parquet"
DEDUPED_PATH = PROCESSED_DIR / "publications_deduplicated.parquet"

def load_raw() -> pd.DataFrame:
    if not RAW_PATH.exists():
        raise FileNotFoundError(
            f"{RAW_PATH} does not exist yet. Run `python -m p36.build_dataset` first."
        )
    return pd.read_parquet(RAW_PATH)

def load_deduplicated() -> pd.DataFrame:
    if not DEDUPED_PATH.exists():
        raise FileNotFoundError(
            f"{DEDUPED_PATH} does not exist yet. Run `python -m p36.build_dataset` first."
        )
    return pd.read_parquet(DEDUPED_PATH)
