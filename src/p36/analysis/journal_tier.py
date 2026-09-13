import pandas as pd

from p36.config import FIELD_COLUMN_EXPLODED, OVERPERFORMING_SOURCE_MIN_PUBLICATIONS
from p36.metrics import mean_fwci, q1_share, top_decile_share
from p36.metrics.metrics import CITESCORE_PERCENTILE_COL, citescore_quartile

def q1_share_by_university(df: pd.DataFrame) -> pd.Series:
    return df.groupby("source_university").apply(q1_share, include_groups=False)

def q1_share_by_year(df: pd.DataFrame, year_range: tuple[int, int] | None = None) -> pd.Series:
    if year_range is not None:
        lo, hi = year_range
        df = df[df["Year"].between(lo, hi)]
    return df.groupby("Year").apply(q1_share, include_groups=False)

def q1_share_by_field(df: pd.DataFrame, field_col: str) -> pd.Series:
    return df.groupby(field_col).apply(q1_share, include_groups=False)

def q1_share_change_by_field(
    df: pd.DataFrame, field_col: str, year_range: tuple[int, int]
) -> pd.Series:
    lo, hi = year_range
    mid = (lo + hi) // 2
    scoped = df[df["Year"].between(lo, hi)]
    early = scoped[scoped["Year"] <= mid].groupby(field_col).apply(q1_share, include_groups=False)
    late = scoped[scoped["Year"] > mid].groupby(field_col).apply(q1_share, include_groups=False)
    return (late - early).dropna().sort_values(ascending=False)

def citescore_percentile_distribution(df: pd.DataFrame) -> pd.Series:
    return df[CITESCORE_PERCENTILE_COL].describe()

def impact_by_citescore_quartile(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_quartile"] = citescore_quartile(df)
    scoped = df.dropna(subset=["_quartile"])
    grouped = scoped.groupby("_quartile", observed=True)
    return pd.DataFrame(
        {
            "publications": grouped.size(),
            "mean_fwci": grouped.apply(mean_fwci, include_groups=False),
            "top_decile_share": grouped.apply(top_decile_share, include_groups=False),
            "uncited_share": grouped["is_uncited"].mean(),
        }
    )

def q1_advantage_by_field(exploded_df: pd.DataFrame) -> pd.DataFrame:
    scoped = exploded_df.dropna(subset=["is_q1"])
    pivot = scoped.pivot_table(
        index=FIELD_COLUMN_EXPLODED,
        columns="is_q1",
        values="Field-Weighted Citation Impact",
        aggfunc="mean",
    )
    pivot["gap"] = pivot.get(True) - pivot.get(False)
    return pivot.sort_values("gap", ascending=False)

def _source_level_gap(
    df: pd.DataFrame, min_publications: int = OVERPERFORMING_SOURCE_MIN_PUBLICATIONS
) -> pd.DataFrame:
    df = df.copy()
    df["_quartile"] = citescore_quartile(df)
    scoped = df.dropna(subset=["_quartile", "Scopus Source title"]).copy()
    scoped["_source_key"] = scoped["Scopus Source title"].str.strip().str.casefold()

    quartile_mean = scoped.groupby("_quartile", observed=True)["Field-Weighted Citation Impact"].mean()

    display_title = (
        scoped.groupby(["_source_key", "Scopus Source title"], observed=True)
        .size()
        .rename("_n")
        .reset_index()
        .sort_values("_n", ascending=False)
        .drop_duplicates("_source_key")
        .set_index("_source_key")["Scopus Source title"]
    )

    source_grouped = scoped.groupby(["_quartile", "_source_key"], observed=True)
    sources = pd.DataFrame(
        {
            "publications": source_grouped.size(),
            "mean_fwci": source_grouped["Field-Weighted Citation Impact"].mean(),
        }
    )
    sources = sources[sources["publications"] >= min_publications].reset_index()
    sources["source"] = sources["_source_key"].map(display_title)
    sources = sources.rename(columns={"_quartile": "quartile"})
    sources["quartile_mean_fwci"] = sources["quartile"].map(quartile_mean).astype(float)
    sources["gap"] = sources["mean_fwci"] - sources["quartile_mean_fwci"]
    return sources.sort_values("gap", ascending=False)

def overperforming_sources(
    df: pd.DataFrame, min_publications: int = OVERPERFORMING_SOURCE_MIN_PUBLICATIONS
) -> pd.DataFrame:
    sources = _source_level_gap(df, min_publications)
    return sources.drop(columns=["_source_key"])

def source_performance_flag(
    df: pd.DataFrame, min_publications: int = OVERPERFORMING_SOURCE_MIN_PUBLICATIONS
) -> pd.Series:
    working = df.copy()
    working["_quartile"] = citescore_quartile(working)
    working["_source_key"] = working["Scopus Source title"].str.strip().str.casefold()

    gap_lookup = _source_level_gap(df, min_publications).set_index(["quartile", "_source_key"])["gap"]
    key = pd.MultiIndex.from_arrays([working["_quartile"], working["_source_key"]])
    gap = pd.Series(gap_lookup.reindex(key).values, index=working.index)
    return (gap > 0).astype("boolean").mask(gap.isna())
