import pandas as pd

from p36.config import (
    CITESCORE_QUARTILE_BOUNDS,
    CITESCORE_QUARTILE_LABELS,
    EXCLUDE_RETRACTED,
    INSTITUTIONAL_COLLABORATION_MIN_INSTITUTIONS,
    INTERNATIONAL_COLLABORATION_MIN_COUNTRIES,
    OPEN_ACCESS_NULL_MEANS_NOT_OA,
    Q1_CITESCORE_PERCENTILE_MAX,
    TOP_1_PERCENT_PERCENTILE_MAX,
    TOP_DECILE_PERCENTILE_MAX,
)

CITESCORE_PERCENTILE_COL = "CiteScore percentile (publication year) *"
TOP_CITATION_PERCENTILE_COL = "Outputs in Top Citation Percentiles, per percentile"
COUNTRIES_COL = "Number of Countries/Regions"
INSTITUTIONS_COL = "Number of Institutions"

def add_derived_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["is_retracted"] = df["Publication type"] == "Retracted"
    is_q1 = (df[CITESCORE_PERCENTILE_COL] <= Q1_CITESCORE_PERCENTILE_MAX).astype("boolean")
    df["is_q1"] = is_q1.mask(df[CITESCORE_PERCENTILE_COL].isna())
    df["is_top_decile"] = (df[TOP_CITATION_PERCENTILE_COL] <= TOP_DECILE_PERCENTILE_MAX).astype(bool)
    df["is_top_1_percent"] = (df[TOP_CITATION_PERCENTILE_COL] <= TOP_1_PERCENT_PERCENTILE_MAX).astype(bool)
    df["is_international"] = (df[COUNTRIES_COL] >= INTERNATIONAL_COLLABORATION_MIN_COUNTRIES).astype(bool)
    df["is_multi_institution"] = (df[INSTITUTIONS_COL] >= INSTITUTIONAL_COLLABORATION_MIN_INSTITUTIONS).astype(bool)
    df["is_uncited"] = (df["Citations"] == 0).astype(bool)
    if OPEN_ACCESS_NULL_MEANS_NOT_OA:
        df["is_open_access"] = df["Open Access"].notna()
    else:
        raise NotImplementedError(
            "OPEN_ACCESS_NULL_MEANS_NOT_OA=False has no implementation — the "
            "alternative reading (null = status unknown, not 'closed') has no "
            "agreed rule for what is_open_access should be in that case."
        )
    return df

def citescore_quartile(df: pd.DataFrame) -> pd.Series:
    return pd.cut(
        df[CITESCORE_PERCENTILE_COL],
        bins=CITESCORE_QUARTILE_BOUNDS,
        labels=CITESCORE_QUARTILE_LABELS,
        include_lowest=True,
    )

def exclude_out_of_scope(df: pd.DataFrame) -> pd.DataFrame:
    if EXCLUDE_RETRACTED:
        df = df[df["Publication type"] != "Retracted"]
    return df

def q1_share(df: pd.DataFrame) -> float:
    col = df[CITESCORE_PERCENTILE_COL]
    scoped = col.dropna()
    if len(scoped) == 0:
        return float("nan")
    return float((scoped <= Q1_CITESCORE_PERCENTILE_MAX).mean())

def international_collaboration_share(df: pd.DataFrame) -> float:
    return float((df[COUNTRIES_COL] >= INTERNATIONAL_COLLABORATION_MIN_COUNTRIES).mean())

def citations_per_paper(df: pd.DataFrame) -> float:
    return float(df["Citations"].mean())

def top_decile_share(df: pd.DataFrame, threshold: int = TOP_DECILE_PERCENTILE_MAX) -> float:
    return float((df[TOP_CITATION_PERCENTILE_COL] <= threshold).mean())

def growth_rate(df: pd.DataFrame, year_column: str = "Year") -> pd.Series:
    counts = df.groupby(year_column).size().sort_index()
    return counts.pct_change()

def period_growth(
    df: pd.DataFrame, year_column: str = "Year", year_range: tuple[int, int] | None = None
) -> float:
    if year_range is not None:
        lo, hi = year_range
        df = df[df[year_column].between(lo, hi)]
    counts = df.groupby(year_column).size().sort_index()
    if len(counts) < 2 or counts.iloc[0] == 0:
        return float("nan")
    return float((counts.iloc[-1] - counts.iloc[0]) / counts.iloc[0])

def mean_fwci(df: pd.DataFrame) -> float:
    return float(df["Field-Weighted Citation Impact"].mean())
