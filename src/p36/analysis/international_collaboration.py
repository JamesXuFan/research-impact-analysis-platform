import pandas as pd

from p36.config import (
    CITATION_WINDOW_TRAILING_YEARS_EXCLUDED,
    COLLABORATION_BREADTH_BINS,
    FIELD_COLUMN_EXPLODED,
    MAIN_YEAR_RANGE,
)
from p36.metrics import mean_fwci, q1_share, top_decile_share
from p36.metrics.metrics import COUNTRIES_COL

def impact_by_collaboration_status(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby("is_international")
    return pd.DataFrame(
        {
            "publications": grouped.size(),
            "mean_fwci": grouped.apply(mean_fwci, include_groups=False),
            "q1_share": grouped.apply(q1_share, include_groups=False),
            "top_decile_share": grouped.apply(top_decile_share, include_groups=False),
            "uncited_share": grouped["is_uncited"].mean(),
        }
    )

def impact_gap_by_field(exploded_df: pd.DataFrame) -> pd.DataFrame:
    pivot = exploded_df.pivot_table(
        index=FIELD_COLUMN_EXPLODED,
        columns="is_international",
        values="Field-Weighted Citation Impact",
        aggfunc="mean",
    )
    pivot["gap"] = pivot.get(True) - pivot.get(False)
    return pivot.sort_values("gap", ascending=False)

def impact_gap_by_year(
    df: pd.DataFrame,
    year_range: tuple[int, int] = MAIN_YEAR_RANGE,
    exclude_trailing_years: bool = True,
) -> pd.DataFrame:
    lo, hi = year_range
    if exclude_trailing_years:
        hi = hi - CITATION_WINDOW_TRAILING_YEARS_EXCLUDED
    scoped = df[df["Year"].between(lo, hi)]
    pivot = scoped.pivot_table(
        index="Year", columns="is_international", values="Field-Weighted Citation Impact", aggfunc="mean"
    )
    pivot["gap"] = pivot.get(True) - pivot.get(False)
    return pivot

def impact_by_collaboration_breadth(df: pd.DataFrame) -> pd.DataFrame:
    bucketed = pd.cut(
        df[COUNTRIES_COL],
        bins=COLLABORATION_BREADTH_BINS + [df[COUNTRIES_COL].max()],
        labels=["1 (domestic only)", "2", "3", "4+"],
    )
    grouped = df.groupby(bucketed, observed=True)
    return pd.DataFrame(
        {
            "publications": grouped.size(),
            "mean_fwci": grouped.apply(mean_fwci, include_groups=False),
            "q1_share": grouped.apply(q1_share, include_groups=False),
        }
    )

def collaboration_rate_trend(
    df: pd.DataFrame, university: str, year_range: tuple[int, int] = MAIN_YEAR_RANGE
) -> pd.Series:
    lo, hi = year_range
    scoped = df[(df["source_university"] == university) & (df["Year"].between(lo, hi))]
    return scoped.groupby("Year")["is_international"].mean()
