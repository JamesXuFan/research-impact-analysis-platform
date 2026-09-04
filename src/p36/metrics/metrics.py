"""Canonical metric implementations.

Every function here corresponds 1:1 to a metric defined in docs/methodology.md.
If you add a function, add its definition to that file in the same commit —
metrics-consistency.md checks for exactly this drift before every merge.

No analysis module or notebook may recompute any of these by hand — import from
here (see .claude/agents/metrics-consistency.md and pandas-safety.md).
"""

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
    """Add the boolean/flag columns every analysis module needs, once.

    This is the single place these are computed — see data_dictionary.md
    "Derived columns" for the definition of each. Adds:

    - ``is_retracted``       Publication type == "Retracted"
    - ``is_q1``               source CiteScore percentile <= Q1_CITESCORE_PERCENTILE_MAX
                               (NaN, i.e. no CiteScore percentile, if the source column is null)
    - ``is_top_decile``       Outputs in Top Citation Percentiles <= TOP_DECILE_PERCENTILE_MAX
    - ``is_top_1_percent``    Outputs in Top Citation Percentiles <= TOP_1_PERCENT_PERCENTILE_MAX
    - ``is_international``    Number of Countries/Regions >= INTERNATIONAL_COLLABORATION_MIN_COUNTRIES
    - ``is_multi_institution`` Number of Institutions >= INSTITUTIONAL_COLLABORATION_MIN_INSTITUTIONS
                               (used by field_analysis.add_collaboration_approach's
                               "publication strategy" stand-in, README item 6 — see
                               p36.config, "Institutional collaboration")
    - ``is_uncited``          Citations == 0
    - ``is_open_access``      Open Access is non-null, i.e. OPEN_ACCESS_NULL_MEANS_NOT_OA is
                               assumed True — **PROVISIONAL**, not confirmed by the client (see
                               data_dictionary.md, Data quality notes). Any finding built on this
                               flag must carry that caveat.

    Does not filter or drop rows — call :func:`exclude_out_of_scope` for that.
    """
    df = df.copy()
    df["is_retracted"] = df["Publication type"] == "Retracted"
    # nullable boolean: NaN CiteScore percentile -> pd.NA ("Q1 status undefined"),
    # not False ("not Q1") — a plain bool comparison would silently conflate the two.
    # is_q1 is the one flag that is genuinely nullable; every other flag below is
    # cast to plain numpy bool even though its source column is nullable Int64/
    # Float64 (Number of Countries/Regions, Citations) and would otherwise produce
    # pandas' extension BooleanDtype — harmless in pandas itself, but statsmodels/
    # patsy (see p36.analysis.impact_drivers) cannot build a design matrix from it.
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
    """Bucket `CiteScore percentile` into Q1-Q4 tiers (Q1 = best), using the
    same low-is-better direction and the same PROVISIONAL basis as `is_q1`
    (see p36.config.CITESCORE_QUARTILE_BOUNDS). NaN is preserved — a
    publication with no CiteScore percentile has an undefined tier, not a
    default one — so callers must drop/mask NaN before grouping by the
    result, the same way `is_q1` is handled above.
    """
    return pd.cut(
        df[CITESCORE_PERCENTILE_COL],
        bins=CITESCORE_QUARTILE_BOUNDS,
        labels=CITESCORE_QUARTILE_LABELS,
        include_lowest=True,
    )


def exclude_out_of_scope(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the scope filters every analysis module should start from.

    Currently just the retracted-publication filter (PROVISIONAL — see
    config.EXCLUDE_RETRACTED and docs/methodology.md). Centralised so a future
    change in scope (e.g. document type filtering, once INCLUDED_DOCUMENT_TYPES
    is confirmed) only has to be made here.
    """
    if EXCLUDE_RETRACTED:
        df = df[df["Publication type"] != "Retracted"]
    return df


def q1_share(df: pd.DataFrame) -> float:
    """Share of publications in a Q1 journal (CiteScore percentile <= threshold).

    Denominator is publications with a non-null CiteScore percentile — Q1 status
    is undefined, not false, for a publication whose source has none.
    """
    col = df[CITESCORE_PERCENTILE_COL]
    scoped = col.dropna()
    if len(scoped) == 0:
        return float("nan")
    return float((scoped <= Q1_CITESCORE_PERCENTILE_MAX).mean())


def international_collaboration_share(df: pd.DataFrame) -> float:
    """Share of publications with author affiliations spanning at least
    INTERNATIONAL_COLLABORATION_MIN_COUNTRIES countries (>=, not >)."""
    return float((df[COUNTRIES_COL] >= INTERNATIONAL_COLLABORATION_MIN_COUNTRIES).mean())


def citations_per_paper(df: pd.DataFrame) -> float:
    """Mean citations per publication.

    Not the same figure as QS Citations per Faculty, which is a raw total, not a
    per-paper average — see finding-checker.md.
    """
    return float(df["Citations"].mean())


def top_decile_share(df: pd.DataFrame, threshold: int = TOP_DECILE_PERCENTILE_MAX) -> float:
    """Share of publications in the top `threshold` percent by citations,
    field/year/document-type normalised (via SciVal's own percentile column —
    never recomputed from raw Citations).
    """
    return float((df[TOP_CITATION_PERCENTILE_COL] <= threshold).mean())


def growth_rate(df: pd.DataFrame, year_column: str = "Year") -> pd.Series:
    """Year-over-year publication count growth rate.

    The final two to three years of any *citation-based* year-by-year series are
    expected to show an artificial decline (see docs/methodology.md, citation
    window artefact). Growth rate on raw publication counts is not subject to
    that artefact and needs no trailing-year exclusion.
    """
    counts = df.groupby(year_column).size().sort_index()
    return counts.pct_change()


def period_growth(
    df: pd.DataFrame, year_column: str = "Year", year_range: tuple[int, int] | None = None
) -> float:
    """Total change in publication count from the first to the last year present
    (or the first/last year of `year_range`, if given): (last - first) / first.

    Distinct from :func:`growth_rate`, which returns a year-over-year series —
    this collapses a multi-year span into a single figure, for "which X is
    improving/declining most rapidly" style ranking questions (README items 6
    and 16). Do not call this "growth rate" in a finding; it is a different
    metric with a different name for a reason — see docs/methodology.md.
    """
    if year_range is not None:
        lo, hi = year_range
        df = df[df[year_column].between(lo, hi)]
    counts = df.groupby(year_column).size().sort_index()
    if len(counts) < 2 or counts.iloc[0] == 0:
        return float("nan")
    return float((counts.iloc[-1] - counts.iloc[0]) / counts.iloc[0])


def mean_fwci(df: pd.DataFrame) -> float:
    """Mean Field-Weighted Citation Impact (1.0 = world average for the same
    field/year/document type; already field-normalised, safe to compare across
    fields directly)."""
    return float(df["Field-Weighted Citation Impact"].mean())
