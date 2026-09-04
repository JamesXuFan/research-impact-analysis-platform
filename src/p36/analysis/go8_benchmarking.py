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

from p36.config import CLIENT_UNIVERSITY, GO8_UNIVERSITIES, MAIN_YEAR_RANGE
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
