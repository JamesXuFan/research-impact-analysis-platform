"""README Analysis item 9 — International Collaboration Analysis.

Core question: are internationally co-authored papers cited more frequently?

Every impact comparison below uses Field-Weighted Citation Impact, not raw
Citations — FWCI is already field/year/document-type normalised, so an
international-vs-domestic gap in FWCI is not just an artefact of internationally
collaborative papers concentrating in higher-citation-culture fields. The by-field
and by-year breakdowns exist to check the finding actually holds within groups,
not just in aggregate (Simpson's paradox) — see .claude/agents/finding-checker.md.

**None of this establishes causation.** An observed gap is equally consistent with
international collaboration causing higher impact, or with researchers who
already produce higher-impact work finding it easier to attract international
co-authors. See docs/methodology.md and finding-checker.md.
"""

import pandas as pd

from p36.config import CITATION_WINDOW_TRAILING_YEARS_EXCLUDED, COLLABORATION_BREADTH_BINS, MAIN_YEAR_RANGE
from p36.metrics import mean_fwci, q1_share, top_decile_share
from p36.metrics.metrics import COUNTRIES_COL


def impact_by_collaboration_status(df: pd.DataFrame) -> pd.DataFrame:
    """Mean FWCI, Q1 share, top-decile share, and uncited share, international
    vs domestic. Answers the core question plus three of the possible
    questions (Q1 likelihood, highly-cited likelihood, uncited likelihood) in
    one table."""
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
    """International-minus-domestic mean-FWCI gap, computed separately within
    each field. Pass an already field-exploded dataframe (see
    p36.analysis.field_analysis.explode_by_field) that still has
    `is_international`. Checks the finding "remains after considering research
    field" rather than assuming it does."""
    from p36.analysis.field_analysis import FIELD_COLUMN_EXPLODED

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
    """International-minus-domestic mean-FWCI gap, by publication year. Checks
    the finding "remains after considering publication year".

    FWCI is citation-based, so this is exactly the kind of year-by-year series
    docs/methodology.md's citation-window artefact warns about: the most recent
    years understate impact because those publications haven't had time to
    accumulate citations. By default this drops the trailing
    CITATION_WINDOW_TRAILING_YEARS_EXCLUDED years of `year_range` (PROVISIONAL —
    see p36.config) rather than showing them uncaveated; pass
    exclude_trailing_years=False to see the full window, but say so if you do.
    """
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
    """Mean FWCI by number of distinct co-author countries (1 = domestic-only,
    2, 3, 4+), for "are some forms of international collaboration more
    beneficial than others?" — a simple binary international flag can't answer
    that, this bins on the actual country count."""
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
    """International collaboration share by year, for one university. For "has
    Sydney's international collaboration rate increased or declined over time?"
    — pass university=p36.config.CLIENT_UNIVERSITY, on a *raw* (not
    deduplicated) prepared dataframe so the figure is Sydney's own claim on its
    output, not diluted by which other Go8 members co-authored the same paper."""
    lo, hi = year_range
    scoped = df[(df["source_university"] == university) & (df["Year"].between(lo, hi))]
    return scoped.groupby("Year")["is_international"].mean()
