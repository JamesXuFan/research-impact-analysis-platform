import pandas as pd

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
    df = df.copy()
    for col in INT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype("Int64")
    return df
