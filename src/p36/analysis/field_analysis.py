"""README Analysis item 6 — Research Field / Faculty Analysis.

Answers: which fields have the highest volume / strongest impact / highest Q1
share; which are high-volume-low-impact or low-volume-high-impact; which are
improving or declining; which produce the most top-decile output; which look
like existing strengths vs room for improvement.

Field taxonomy: `Quacquarelli Symonds (QS) Subject area field name` — the QS
subject taxonomy, consistent with this being a QS-ranking-context project.
`ANZSRC FoR (2020) parent name` is available as an alternative taxonomy if the
client prefers it, by swapping FIELD_COLUMN below — but it is not a free swap:
it is null on 10.7% of rows, vs 2.45% for the QS column (see data_dictionary.md,
Data quality notes), so switching silently drops more publications from every
field-level total.

A publication can belong to more than one field (pipe-delimited). Multi-field
counting is PROVISIONAL — see p36.config.FRACTIONAL_FIELD_COUNTING. The current
default is whole counting: a paper in 2 fields counts fully toward each one's
volume, so field volumes sum to more than the true publication count. Every
function here works on the *exploded* dataframe (one row per publication-field
membership) — never mix an exploded and a non-exploded dataframe in the same
comparison.
"""

import pandas as pd

from p36.config import FRACTIONAL_FIELD_COUNTING, MAIN_YEAR_RANGE
from p36.metrics import mean_fwci, period_growth, q1_share, top_decile_share

FIELD_COLUMN = "Quacquarelli Symonds (QS) Subject area field name"
FIELD_COLUMN_EXPLODED = "field"


def explode_by_field(df: pd.DataFrame, field_col: str = FIELD_COLUMN) -> pd.DataFrame:
    """One row per (publication, field) membership.

    Whole counting only (FRACTIONAL_FIELD_COUNTING is currently False) — a paper
    listed under N fields becomes N rows, each carrying its full, unweighted
    Citations/FWCI/etc. This is why field volumes must never be summed and
    compared to the total publication count without accounting for the overlap.

    Publications with a null `field_col` are dropped (there is no field to
    explode into) — on the default column, that's 8,015/327,265 (2.45%) of the
    deduplicated dataset; on the ANZSRC alternative it's 35,124/327,265 (10.7%).
    Neither share is negligible enough to drop silently, so this prints a count
    every call — every field-level total in this module (and in
    go8_benchmarking.field_gap_vs_peers) is against that reduced denominator,
    not the true publication count.
    """
    if FRACTIONAL_FIELD_COUNTING:
        raise NotImplementedError(
            "FRACTIONAL_FIELD_COUNTING=True has no implementation yet — the "
            "weighting rule (e.g. 1/N per field) has not been confirmed by the "
            "client. See docs/methodology.md, Multi-field publications."
        )
    dropped = df[field_col].isna().sum()
    if dropped:
        print(
            f"explode_by_field: dropping {dropped}/{len(df)} rows "
            f"({dropped / len(df):.1%}) with no {field_col!r}"
        )
    working = df.dropna(subset=[field_col]).copy()
    working[field_col] = working[field_col].str.split("|")
    exploded = working.explode(field_col)
    exploded[FIELD_COLUMN_EXPLODED] = exploded[field_col].str.strip()
    return exploded


def field_summary(exploded_df: pd.DataFrame) -> pd.DataFrame:
    """Per-field volume, mean FWCI, Q1 share, top-decile share, uncited share.

    Pass the output of explode_by_field. Sorted by volume, descending.
    """
    grouped = exploded_df.groupby(FIELD_COLUMN_EXPLODED)
    summary = pd.DataFrame(
        {
            "publications": grouped.size(),
            "mean_fwci": grouped.apply(mean_fwci, include_groups=False),
            "q1_share": grouped.apply(q1_share, include_groups=False),
            "top_decile_share": grouped.apply(top_decile_share, include_groups=False),
            "uncited_share": grouped["is_uncited"].mean(),
        }
    )
    return summary.sort_values("publications", ascending=False)


def volume_vs_impact_quadrant(summary: pd.DataFrame) -> pd.DataFrame:
    """Classify each field as high/low volume x high/low impact (median split),
    for the "high volume but low impact" / "low volume but high impact"
    sub-questions. Median split, not an absolute threshold — this is a relative
    statement about this dataset, not a universal definition of "high"."""
    out = summary.copy()
    volume_median = out["publications"].median()
    impact_median = out["mean_fwci"].median()
    out["volume_band"] = out["publications"].ge(volume_median).map({True: "high", False: "low"})
    out["impact_band"] = out["mean_fwci"].ge(impact_median).map({True: "high", False: "low"})
    out["quadrant"] = out["volume_band"] + " volume / " + out["impact_band"] + " impact"
    return out


def field_trend(
    exploded_df: pd.DataFrame, year_range: tuple[int, int] = MAIN_YEAR_RANGE
) -> pd.DataFrame:
    """Publication count by field and year, restricted to `year_range` (default
    p36.config.MAIN_YEAR_RANGE — the straggler years outside the declared export
    window have too few rows per field to show a real trend)."""
    lo, hi = year_range
    scoped = exploded_df[exploded_df["Year"].between(lo, hi)]
    return scoped.groupby([FIELD_COLUMN_EXPLODED, "Year"]).size().unstack("Year", fill_value=0)


def field_growth(exploded_df: pd.DataFrame, year_range: tuple[int, int] = MAIN_YEAR_RANGE) -> pd.Series:
    """Total-period publication-count growth per field across `year_range` — see
    p36.metrics.period_growth for the exact definition (deliberately not called
    "growth rate": that name is p36.metrics.growth_rate, a year-over-year
    series, not this). For "which areas are improving/declining"."""
    return exploded_df.groupby(FIELD_COLUMN_EXPLODED).apply(
        period_growth, year_range=year_range, include_groups=False
    ).sort_values(ascending=False)


COLLABORATION_APPROACH_COLUMN = "collaboration_approach"


def add_collaboration_approach(df: pd.DataFrame) -> pd.DataFrame:
    """Add a 3-category `collaboration_approach` column — the closest thing
    this dataset has to a "publication strategy" variable (README item 6:
    "are particular publication strategies more successful in some fields
    than others?", previously unanswered because no strategy variable was
    defined). Not a client-confirmed definition of "strategy" — a documented
    stand-in built from two flags already in use elsewhere (`is_international`,
    `is_multi_institution`), not a new concept:

    - "International"                 — is_international is True
    - "Domestic, multi-institution"    — is_international is False, is_multi_institution is True
    - "Domestic, single institution"   — is_international is False, is_multi_institution is False

    Expects `df` to already carry `is_international` and `is_multi_institution`
    from p36.metrics.add_derived_flags — this function does not recompute the
    institution-count threshold itself (see .claude/agents/metrics-consistency.md:
    that threshold is named in p36.config and cast to plain bool in
    add_derived_flags, same as every other nullable-Int64-derived flag).
    """
    df = df.copy()
    df[COLLABORATION_APPROACH_COLUMN] = "Domestic, single institution"
    df.loc[df["is_multi_institution"], COLLABORATION_APPROACH_COLUMN] = "Domestic, multi-institution"
    df.loc[df["is_international"], COLLABORATION_APPROACH_COLUMN] = "International"
    return df


def collaboration_approach_by_field(exploded_df: pd.DataFrame) -> pd.DataFrame:
    """Mean FWCI and publication count for every (field, collaboration
    approach) combination — README item 6's "publication strategy" question,
    made concrete via `add_collaboration_approach` above. Pass an
    already field-exploded dataframe that also has `collaboration_approach`
    (call `add_collaboration_approach` before or after exploding — the
    column doesn't depend on field). Purely descriptive group means, not a
    regression — a field where "International" shows the highest mean FWCI
    is consistent with, not proof of, international collaboration being the
    more effective approach specifically in that field.
    """
    from p36.metrics import mean_fwci

    grouped = exploded_df.groupby([FIELD_COLUMN_EXPLODED, COLLABORATION_APPROACH_COLUMN], observed=True)
    table = pd.DataFrame(
        {
            "publications": grouped.size(),
            "mean_fwci": grouped.apply(mean_fwci, include_groups=False),
        }
    )
    return table
