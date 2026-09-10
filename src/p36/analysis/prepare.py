import pandas as pd

from p36 import dataset
from p36.metrics import add_derived_flags, exclude_out_of_scope

def prepared_deduplicated() -> pd.DataFrame:
    df = dataset.load_deduplicated()
    df = exclude_out_of_scope(df)
    df = add_derived_flags(df)
    return df

def prepared_raw() -> pd.DataFrame:
    df = dataset.load_raw()
    df = exclude_out_of_scope(df)
    df = add_derived_flags(df)
    return df

def for_university(df: pd.DataFrame, university: str) -> pd.DataFrame:
    return df[df["source_university"] == university]
