"""Canonical dtype coercion applied after ingest, before anything is persisted or
analysed. Kept separate from ``ingest.py`` — ingest only fixes what would otherwise
break on read (ID columns as float, the "-" missing-value sentinel); this module
applies the count-column casts documented as the "processing rule" for each field in
data/dictionary/data_dictionary.md.
"""

import pandas as pd

# Count-like columns documented in data_dictionary.md as "cast float64 -> Int64".
# Nullable Int64 (not int64) because every one of these can be null in this dataset.
INT_COLUMNS: list[str] = [
    "Number of Authors",
    "Year",
    "Views",
    "Citations",
    "Main patent families",
    "Policy citations",
    "Number of Institutions",
    "Number of Countries/Regions",
]


def apply_canonical_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Cast documented count columns from float64 to nullable Int64.

    Only touches columns present in ``df`` and listed in ``INT_COLUMNS`` above, so
    it is safe to call on any subset of the full column set (e.g. in a notebook
    that only selected a few columns).
    """
    df = df.copy()
    for col in INT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype("Int64")
    return df
