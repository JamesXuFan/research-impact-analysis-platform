"""README Analysis item 16 — Go8 / Peer Benchmarking.

Core question: how is Sydney performing relative to its peers, particularly the Go8?

Every function takes a **raw** prepared dataframe (p36.analysis.prepare.prepared_raw)
grouped by `source_university` — deliberately not deduplicated. A jointly-authored
Go8 paper is legitimately part of each contributing university's own output and
performance portfolio; deduplicating first would understate whichever university's
export happens to lose the drop_duplicates(keep="first") tie-break. See
data_dictionary.md, Data quality notes, and p36.ingest.deduplicate_by_eid.

`p36.config.CLIENT_UNIVERSITY` ("The University of Sydney") is the reference point;
`p36.config.GO8_UNIVERSITIES` minus that one are "peers".
"""

import pandas as pd

from p36.config import CLIENT_UNIVERSITY, GO8_UNIVERSITIES, HIGH_PERFORMING_PARTNER_MIN_PUBLICATIONS, MAIN_YEAR_RANGE
from p36.metrics import mean_fwci, period_growth, q1_share, top_decile_share


def benchmark_summary(df: pd.DataFrame) -> pd.DataFrame:
    """One row per university: volume, mean FWCI, Q1 share, top-decile share,
    international collaboration share, mean institutional collaboration.
    Answers the volume / citation impact / Q1 share / highly-cited /
    international collaboration / institutional collaboration sub-questions in
    one table. Sorted with the client university first."""
    grouped = df.groupby("source_university")
    summary = pd.DataFrame(
        {
            "publications": grouped.size(),
            "mean_fwci": grouped.apply(mean_fwci, include_groups=False),
            "q1_share": grouped.apply(q1_share, include_groups=False),
            "top_decile_share": grouped.apply(top_decile_share, include_groups=False),
            "international_collaboration_share": grouped["is_international"].mean(),
            "mean_institutions_per_paper": grouped["Number of Institutions"].mean(),
        }
    )
    order = [CLIENT_UNIVERSITY] + [u for u in GO8_UNIVERSITIES if u != CLIENT_UNIVERSITY]
    return summary.reindex(order)


def field_gap_vs_peers(
    exploded_df: pd.DataFrame, client: str = CLIENT_UNIVERSITY
) -> pd.DataFrame:
    """Per field: client's mean FWCI, the Go8-peer average, and the gap.
    Positive gap = client outperforms peers in that field. Pass a field-exploded
    dataframe (p36.analysis.field_analysis.explode_by_field) built on
    prepared_raw(). Answers "strongest fields", "largest gaps", "where Sydney
    outperforms/underperforms"."""
    from p36.analysis.field_analysis import FIELD_COLUMN_EXPLODED

    is_client = exploded_df["source_university"] == client
    client_fwci = exploded_df[is_client].groupby(FIELD_COLUMN_EXPLODED).apply(mean_fwci, include_groups=False)
    peer_fwci = exploded_df[~is_client].groupby(FIELD_COLUMN_EXPLODED).apply(mean_fwci, include_groups=False)
    out = pd.DataFrame({"client_fwci": client_fwci, "peer_avg_fwci": peer_fwci})
    out["gap"] = out["client_fwci"] - out["peer_avg_fwci"]
    return out.sort_values("gap", ascending=False)


def growth_by_university(
    df: pd.DataFrame, year_range: tuple[int, int] = MAIN_YEAR_RANGE
) -> pd.Series:
    """Total-period publication-count growth per university across `year_range`
    — see p36.metrics.period_growth for the exact definition (deliberately not
    called "growth rate": that name is p36.metrics.growth_rate, a
    year-over-year series, not this). Answers "which Go8 universities are
    improving most rapidly"."""
    return df.groupby("source_university").apply(
        period_growth, year_range=year_range, include_groups=False
    ).sort_values(ascending=False)


def top_countries_by_university(
    df: pd.DataFrame, university: str, top_n: int = 10
) -> pd.Series:
    """Most common international co-author countries for one university
    (excluding Australia itself). For "are competitors collaborating with
    different countries or institutions?" — call once per university and
    compare."""
    scoped = df[(df["source_university"] == university) & df["Country/Region"].notna()]
    countries = scoped["Country/Region"].str.split("|").explode().str.strip()
    countries = countries[countries != "Australia"]
    return countries.value_counts().head(top_n)


def journal_pattern_by_university(df: pd.DataFrame) -> pd.DataFrame:
    """Distribution of source type (Journal / Conference Proceeding / Book
    Series / ...) by university, as a share of that university's output. For
    "are competitors using different journal-publishing patterns?"."""
    return (
        df.groupby("source_university")["Source type"]
        .value_counts(normalize=True)
        .unstack("Source type", fill_value=0)
    )


def _exploded_partners(df: pd.DataFrame, university: str = CLIENT_UNIVERSITY) -> pd.DataFrame:
    """Shared helper: one row per (publication, external co-author institution)
    for `university`'s own raw publications. Explodes the pipe-delimited
    `Institutions` column and drops `university` itself (its own name, not a
    partner).

    `_institution_key` is normalised (`.str.strip().str.casefold()`), not the
    raw spelling — same reasoning and same convention as
    `journal_tier._source_level_gap`'s `_source_key` for `Scopus Source
    title`: the same institution can be written slightly differently paper to
    paper even within one university's own export, and grouping on the raw
    string would silently split it across two rows, understating its
    publication count (possibly below a min_publications floor) and
    computing its mean FWCI from an incomplete subset. Self-exclusion is
    matched against this same normalised key, not a separate one-off
    comparison — verified 2026-09-05 for `CLIENT_UNIVERSITY`: "The
    University of Sydney" (the exact `source_university` string) appears in
    60,647 of Sydney's 60,648 own rows with `Institutions` data, so this
    isn't silently missing alternate self-spellings for the one university
    this module is actually called with; a different `university` argument
    hasn't been checked and could need a different canonical string.

    Drops empty-string tokens (a leading/trailing/doubled `|` in the source
    data would otherwise survive as a nameless "institution" that isn't
    caught by `dropna` or the self-exclusion check) — verified 2026-09-05:
    zero occurrences across all 385,599 non-null raw `Institutions` values,
    so this is a guard against future data, not a fix for a live bug today.
    """
    scoped = df[df["source_university"] == university].dropna(subset=["Institutions"]).copy()
    scoped["_institution"] = scoped["Institutions"].str.split("|")
    exploded = scoped.explode("_institution")
    exploded["_institution_key"] = exploded["_institution"].str.strip().str.casefold()
    exploded = exploded[exploded["_institution_key"] != ""]
    exploded = exploded[exploded["_institution_key"] != university.strip().casefold()]
    # Guard against the same institution appearing twice in one publication's
    # own pipe-delimited list (verified 2026-09-05: zero occurrences in
    # Sydney's own rows today) — without this, such a row would count twice
    # toward that institution's `publications` total below.
    is_dup_within_publication = pd.MultiIndex.from_arrays([exploded.index, exploded["_institution_key"]]).duplicated()
    return exploded[~is_dup_within_publication]


def _institution_level_gap(
    df: pd.DataFrame,
    university: str = CLIENT_UNIVERSITY,
    min_publications: int = HIGH_PERFORMING_PARTNER_MIN_PUBLICATIONS,
) -> pd.DataFrame:
    """Shared computation behind `institution_partner_performance` and
    `institution_partner_flag` — same split as `journal_tier`'s
    `_source_level_gap` vs. `overperforming_sources`/`source_performance_flag`,
    and for the same reason: `institution_partner_flag` must match against
    the *normalised* `_institution_key` (kept as this function's index), not
    the display-friendly name `institution_partner_performance` shows —
    matching against the display name would silently fail to find any
    institution whose display spelling isn't already normalised (which is
    every institution with mixed-case letters), since `institution_partner_flag`
    compares against the same normalised keys used everywhere else in this
    module, not display strings.

    Index: `_institution_key` (normalised). Columns: `institution` (most
    common raw spelling, for display), `publications`, `mean_fwci`,
    `university_mean_fwci`, `gap`.
    """
    exploded = _exploded_partners(df, university)
    university_mean = mean_fwci(df[df["source_university"] == university])

    # Most common raw spelling per normalised key, for display — same
    # pattern as journal_tier._source_level_gap's display_title.
    display_name = (
        exploded.groupby(["_institution_key", "_institution"])
        .size()
        .rename("_n")
        .reset_index()
        .sort_values("_n", ascending=False)
        .drop_duplicates("_institution_key")
        .set_index("_institution_key")["_institution"]
        .str.strip()
    )

    grouped = exploded.groupby("_institution_key")
    table = pd.DataFrame(
        {
            "publications": grouped.size(),
            "mean_fwci": grouped.apply(mean_fwci, include_groups=False),
        }
    )
    table = table[table["publications"] >= min_publications].copy()
    table["institution"] = table.index.map(display_name)
    table["university_mean_fwci"] = university_mean
    table["gap"] = table["mean_fwci"] - university_mean
    return table.sort_values("gap", ascending=False)


def institution_partner_performance(
    df: pd.DataFrame,
    university: str = CLIENT_UNIVERSITY,
    min_publications: int = HIGH_PERFORMING_PARTNER_MIN_PUBLICATIONS,
) -> pd.DataFrame:
    """Per external partner institution: mean FWCI of `university`'s own
    publications co-authored with that institution, vs. `university`'s own
    overall mean FWCI (`gap`) — README item 17's "increase collaboration
    with selected high-performing institutions", previously unaddressed
    because no institution-level performance data was thought to be
    available. The `Institutions` column (pipe-delimited affiliation names)
    turns out to support exactly this, the same way `Scopus Source title`
    supports `journal_tier.overperforming_sources` for journals.

    Uses the **raw** (not deduplicated) dataframe, scoped to `university`'s
    own rows — this is inherently a "who should *this* university work with
    more" question, not a Go8-aggregate one. Restricted to partner
    institutions with at least `min_publications` co-authored publications,
    so a single highly-cited paper can't make a rarely-used partner look
    like a standout. `gap` = partner's mean FWCI minus `university`'s own
    overall mean FWCI (across all its publications, not just ones with this
    partner); sort by `gap` for the strongest partners. Indexed by display
    name (unlike the internal `_institution_level_gap`) — for matching
    against a specific institution programmatically, use
    `institution_partner_flag` instead, not this table's index.
    """
    table = _institution_level_gap(df, university, min_publications)
    return table.set_index("institution")


def institution_partner_flag(
    df: pd.DataFrame,
    university: str = CLIENT_UNIVERSITY,
    min_publications: int = HIGH_PERFORMING_PARTNER_MIN_PUBLICATIONS,
) -> pd.Series:
    """Per-*publication* nullable boolean, aligned to `df`'s index and
    defined only for `university`'s own rows that have at least one partner
    meeting `min_publications` (NaN everywhere else, including
    single-institution papers and rows whose only partners fall below the
    threshold — there's no basis to call those "not collaborating with a
    high performer" when none of their partners' performance is known):
    True if the publication has at least one co-author institution
    classified as high-performing by `institution_partner_performance`
    (positive gap), False if it has qualifying partners but none with a
    positive gap. Built for
    `p36.analysis.scenario_analysis.estimate_uplift_from_share_shift`.
    """
    # Uses the internal, normalised-key-indexed table, not the public
    # institution_partner_performance (display-name-indexed) — matching
    # against a display name here would silently match nothing whenever the
    # display spelling isn't already lower-cased, which is most of them.
    performance = _institution_level_gap(df, university, min_publications)
    high_performing = set(performance.index[performance["gap"] > 0])
    qualifying = set(performance.index)  # already threshold-filtered; high_performing is a subset

    exploded = _exploded_partners(df, university)
    # Vectorised .isin() + groupby(...).any() — not a per-group Python lambda
    # (a naive .agg(lambda s: s.isin(...).any()) is dramatically slower here:
    # it re-runs the lambda, and therefore the .isin() scan, once per group
    # instead of once over the whole column).
    is_qualifying = exploded["_institution_key"].isin(qualifying)
    is_high_performing = exploded["_institution_key"].isin(high_performing)
    has_qualifying = is_qualifying.groupby(exploded.index).any()
    has_high_performing = is_high_performing.groupby(exploded.index).any()

    flag = pd.Series(pd.NA, index=df.index, dtype="boolean")
    flag.loc[has_qualifying.index[has_qualifying]] = False
    flag.loc[has_high_performing.index[has_high_performing]] = True
    return flag
