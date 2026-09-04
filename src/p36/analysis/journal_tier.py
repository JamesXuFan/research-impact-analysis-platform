"""README Analysis item 3 — Journal Tier and Q1 Analysis.

Core question: what share of output appears in top-tier (Q1) journals, and how
does that vary by university, field, and year?

Q1 definition: source `CiteScore percentile <= 25` — direction verified, exact
cutoff PROVISIONAL (see docs/methodology.md, `p36.config.Q1_CITESCORE_PERCENTILE_MAX`).
Every function below excludes rows with no CiteScore percentile from the
denominator (Q1 status is undefined for them, not false) — see `p36.metrics.q1_share`.
"""

import pandas as pd

from p36.config import OVERPERFORMING_SOURCE_MIN_PUBLICATIONS
from p36.metrics import mean_fwci, q1_share, top_decile_share
from p36.metrics.metrics import CITESCORE_PERCENTILE_COL, citescore_quartile


def q1_share_by_university(df: pd.DataFrame) -> pd.Series:
    """Q1 share for each university. Use a deduplicated dataframe for a Go8-wide
    comparison, or prepare.prepared_raw() if you want each university's own claim
    on jointly-authored papers included."""
    return df.groupby("source_university").apply(q1_share, include_groups=False)


def q1_share_by_year(df: pd.DataFrame, year_range: tuple[int, int] | None = None) -> pd.Series:
    """Q1 share trend by publication year. Pass `year_range` (e.g.
    p36.config.MAIN_YEAR_RANGE) to exclude straggler years with too few rows to
    be meaningful — see data_dictionary.md, Year range note."""
    if year_range is not None:
        lo, hi = year_range
        df = df[df["Year"].between(lo, hi)]
    return df.groupby("Year").apply(q1_share, include_groups=False)


def q1_share_by_field(df: pd.DataFrame, field_col: str) -> pd.Series:
    """Q1 share by research field. Pass an already-exploded-by-field dataframe
    (see p36.analysis.field_analysis.explode_by_field) as `df`, and the name of
    the single-value field column it produced, as `field_col`."""
    return df.groupby(field_col).apply(q1_share, include_groups=False)


def citescore_percentile_distribution(df: pd.DataFrame) -> pd.Series:
    """Descriptive summary of the CiteScore percentile column itself (remember:
    lower is better). Useful as a sanity check before quoting a Q1 share."""
    return df[CITESCORE_PERCENTILE_COL].describe()


def impact_by_citescore_quartile(df: pd.DataFrame) -> pd.DataFrame:
    """Mean FWCI, highly-cited (top-decile) share, and uncited share by
    CiteScore quartile (Q1-Q4). Directly answers three of item 3's possible-
    analysis bullets in one table: "compare citation performance across Q1,
    Q2, Q3, Q4", "compare highly-cited/uncited-publication rates across
    quartiles", and "does publishing in Q1 increase the probability of
    becoming highly cited" — none of which the binary `is_q1` flag alone can
    show, since it collapses Q2/Q3/Q4 into a single "not Q1" bucket. Rows
    with no CiteScore percentile are excluded (tier undefined), not folded
    into any bucket.
    """
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
    """Q1-minus-non-Q1 mean-FWCI gap, computed separately within each field —
    "is the Q1 advantage consistent across disciplines, or concentrated in a
    few?" (README item 3). Same pattern as
    p36.analysis.international_collaboration.impact_gap_by_field. Pass an
    already field-exploded dataframe (p36.analysis.field_analysis.explode_by_field)
    that still has `is_q1`; rows with an undefined is_q1 (no CiteScore
    percentile) are dropped first.
    """
    from p36.analysis.field_analysis import FIELD_COLUMN_EXPLODED

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
    """Shared computation behind `overperforming_sources` and
    `source_performance_flag`: per-source mean FWCI vs. its own CiteScore-
    quartile mean. One row per (quartile, normalised source key) meeting
    `min_publications`; `gap` = source mean FWCI minus quartile mean FWCI.

    `Scopus Source title` is exported independently per university with no
    cross-export normalisation (see data_dictionary.md) — the same journal
    can appear as two different strings differing only in case or whitespace
    (verified 2026-09-03: 316 of 29,754 raw titles collapse once
    case/whitespace-normalised). Grouping on the raw string would silently
    split such a journal's publications across two rows, understating its
    count (possibly below `min_publications`, dropping it entirely) and
    computing mean_fwci from an incomplete subset — so grouping uses a
    normalised key, with the most common raw spelling kept for display.
    """
    df = df.copy()
    df["_quartile"] = citescore_quartile(df)
    scoped = df.dropna(subset=["_quartile", "Scopus Source title"]).copy()
    scoped["_source_key"] = scoped["Scopus Source title"].str.strip().str.casefold()

    quartile_mean = scoped.groupby("_quartile", observed=True)["Field-Weighted Citation Impact"].mean()

    # Most common raw spelling per normalised key, for display.
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
    # .map() on a categorical column can itself come back categorical (pandas
    # infers the mapped dtype from the *codes*, not the mapped values, in some
    # versions) — force plain float so the subtraction below isn't trying to
    # do arithmetic on a Categorical.
    sources["quartile_mean_fwci"] = sources["quartile"].map(quartile_mean).astype(float)
    sources["gap"] = sources["mean_fwci"] - sources["quartile_mean_fwci"]
    return sources.sort_values("gap", ascending=False)


def overperforming_sources(
    df: pd.DataFrame, min_publications: int = OVERPERFORMING_SOURCE_MIN_PUBLICATIONS
) -> pd.DataFrame:
    """Per-source (journal) mean FWCI compared to its own CiteScore-quartile
    average — "are there journals or publications within a tier that receive
    more citations than would be expected for that tier?" (README item 3,
    previously unaddressed by any Q1/non-Q1 split). Restricted to sources
    with at least `min_publications` publications within that quartile, so a
    single highly-cited paper can't make a small source look like an
    outlier. `gap` = source's own mean FWCI minus its quartile's mean FWCI;
    sort by `gap` for the strongest over-/under-performers.
    """
    sources = _source_level_gap(df, min_publications)
    return sources.drop(columns=["_source_key"])


def source_performance_flag(
    df: pd.DataFrame, min_publications: int = OVERPERFORMING_SOURCE_MIN_PUBLICATIONS
) -> pd.Series:
    """Per-*publication* nullable boolean: True if this publication's source
    out-performs its own CiteScore-quartile average (by `_source_level_gap`
    above), False if it under-performs, NaN if the source doesn't meet
    `min_publications` in that quartile or has no quartile/source at all.
    Aligned to `df`'s index — built for feeding
    `p36.analysis.scenario_analysis.estimate_uplift_from_share_shift`, to
    answer README item 17's "shift some publications toward journals
    identified as strong opportunities" (README item 3's over-performing-
    sources table, wired into a projection rather than left as a shortlist).
    """
    working = df.copy()
    working["_quartile"] = citescore_quartile(working)
    working["_source_key"] = working["Scopus Source title"].str.strip().str.casefold()

    gap_lookup = _source_level_gap(df, min_publications).set_index(["quartile", "_source_key"])["gap"]
    key = pd.MultiIndex.from_arrays([working["_quartile"], working["_source_key"]])
    gap = pd.Series(gap_lookup.reindex(key).values, index=working.index)
    return (gap > 0).astype("boolean").mask(gap.isna())
