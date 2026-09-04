"""Shared entry point every analysis module starts from — load, scope-filter, add
derived flags, once. Prevents six modules from each writing a slightly different
version of "load the data and clean it up a bit".
"""

import pandas as pd

from p36 import dataset
from p36.metrics import add_derived_flags, exclude_out_of_scope


def prepared_deduplicated() -> pd.DataFrame:
    """One row per unique publication, scope-filtered, with derived flags.

    Use for any Go8-aggregate or cross-university figure, and for any
    single-university figure where you don't also need `source_university` to
    disambiguate multi-university co-authored rows (it's still present).
    """
    df = dataset.load_deduplicated()
    df = exclude_out_of_scope(df)
    df = add_derived_flags(df)
    return df


def prepared_raw() -> pd.DataFrame:
    """One row per (university, publication) claim, scope-filtered, with derived
    flags. Use for a single university's own output figures — a jointly-authored
    Go8 paper legitimately counts toward each contributing university's total.
    """
    df = dataset.load_raw()
    df = exclude_out_of_scope(df)
    df = add_derived_flags(df)
    return df


def for_university(df: pd.DataFrame, university: str) -> pd.DataFrame:
    """Filter a prepared dataframe (raw or deduplicated) to one university's rows."""
    return df[df["source_university"] == university]
