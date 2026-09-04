"""Shared bootstrap and cached data loaders for every page. Streamlit adds the
entrypoint script's directory (app/) to sys.path, so any page under app/pages/
can `from lib import ...` — see Home.py.

No analysis logic lives here — every function below just calls
src/p36/analysis/ and caches the result. If a number looks wrong, the bug is in
src/p36/, not here (see .claude/agents/metrics-consistency.md: one
implementation, everything else calls it).

**Every function a page calls must be wrapped in `@st.cache_data` here, not
called directly on the analysis module.** Streamlit reruns the whole page
script on every widget interaction — an uncached `groupby(...).apply(...)`
call (field_summary, growth_by_university, impact_by_collaboration_status,
...) costs 0.3-1.5s each on this dataset (measured 2026-09-02), and a page
with two or three of them uncached turns every click into a multi-second
wait. Each wrapper below takes no DataFrame arguments (only cache-friendly
scalars, if any) and loads its own input internally — passing a DataFrame
into a cached function makes Streamlit hash the whole thing on every call,
which defeats the purpose.
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from p36.analysis import field_analysis, go8_benchmarking, journal_tier, prepare, scenario_analysis  # noqa: E402
from p36.analysis import international_collaboration as intl  # noqa: E402
from p36.config import CLIENT_UNIVERSITY, GO8_UNIVERSITIES, MAIN_YEAR_RANGE  # noqa: E402

__all__ = [
    "CLIENT_UNIVERSITY",
    "GO8_UNIVERSITIES",
    "load_raw",
    "load_deduplicated",
    "load_exploded_raw",
    "load_exploded_deduplicated",
    "get_benchmark_summary",
    "get_growth_by_university",
    "get_field_gap_vs_peers",
    "get_top_countries",
    "get_journal_pattern",
    "get_q1_share_by_university",
    "get_q1_share_by_year",
    "get_citescore_percentile_distribution",
    "get_field_summary",
    "get_field_growth",
    "get_field_trend",
    "get_impact_by_collaboration_status",
    "get_impact_gap_by_field",
    "get_impact_gap_by_year",
    "get_impact_by_collaboration_breadth",
    "get_collaboration_rate_trend",
    "get_scenario_table",
    "get_fwci_by_collaboration_status",
    "get_fwci_by_field",
    "get_citescore_percentile_series",
    "get_q1_definition_agreement",
    "get_overlap_by_university",
    "get_impact_by_citescore_quartile",
    "get_q1_advantage_by_field",
    "get_overperforming_sources",
    "caveat",
    "provisional",
]


# --- Base data (Home.py, and every page's starting point) -------------------


@st.cache_data(show_spinner="Loading publication data (per-university)…")
def load_raw():
    """One row per (university, publication) claim — for any single
    university's own output figures."""
    return prepare.prepared_raw()


@st.cache_data(show_spinner="Loading publication data (deduplicated)…")
def load_deduplicated():
    """One row per unique publication — for any Go8-aggregate or
    cross-university figure."""
    return prepare.prepared_deduplicated()


@st.cache_data(show_spinner="Building field-level breakdown (per-university)…")
def load_exploded_raw():
    dropped_before = load_raw()[field_analysis.FIELD_COLUMN].isna().sum()
    exploded = field_analysis.explode_by_field(load_raw())
    return exploded, dropped_before


@st.cache_data(show_spinner="Building field-level breakdown (deduplicated)…")
def load_exploded_deduplicated():
    dropped_before = load_deduplicated()[field_analysis.FIELD_COLUMN].isna().sum()
    exploded = field_analysis.explode_by_field(load_deduplicated())
    return exploded, dropped_before


# --- Home.py ------------------------------------------------------------


@st.cache_data(show_spinner="Computing Go8-shared vs. exclusive output…")
def get_overlap_by_university():
    """Per university: how many of its raw publications share an EID with at
    least one other Go8 university's export (i.e. is a joint Go8 paper) vs.
    appear under this university alone. Not the same question as the global
    dedup count — this is *whose* output overlaps, not just how much."""
    raw = load_raw()
    eid_counts = raw["EID"].value_counts()
    shared = raw["EID"].map(eid_counts) > 1
    summary = pd.DataFrame(
        {
            "raw_publications": raw.groupby("source_university").size(),
            "shared_with_another_go8_university": raw.assign(_s=shared).groupby("source_university")["_s"].sum(),
        }
    )
    summary["exclusive_to_this_university"] = summary["raw_publications"] - summary["shared_with_another_go8_university"]
    summary["shared_share"] = summary["shared_with_another_go8_university"] / summary["raw_publications"]
    return summary


# --- 16. Go8 benchmarking (app/pages/1_Go8_Benchmarking.py) -----------------


@st.cache_data(show_spinner="Computing Go8 benchmark summary…")
def get_benchmark_summary():
    return go8_benchmarking.benchmark_summary(load_raw())


@st.cache_data(show_spinner="Computing university growth…")
def get_growth_by_university():
    return go8_benchmarking.growth_by_university(load_raw())


@st.cache_data(show_spinner="Computing field gap vs. Go8 peers…")
def get_field_gap_vs_peers():
    exploded, _ = load_exploded_raw()
    return go8_benchmarking.field_gap_vs_peers(exploded)


@st.cache_data(show_spinner="Computing top co-author countries…")
def get_top_countries(university: str, top_n: int = 10):
    return go8_benchmarking.top_countries_by_university(load_raw(), university, top_n=top_n)


@st.cache_data(show_spinner="Computing journal-publishing pattern…")
def get_journal_pattern():
    return go8_benchmarking.journal_pattern_by_university(load_raw())


# --- 3. Journal tier / Q1 (app/pages/2_Journal_Tier.py) ---------------------


@st.cache_data(show_spinner="Computing Q1 share by university…")
def get_q1_share_by_university():
    return journal_tier.q1_share_by_university(load_deduplicated())


@st.cache_data(show_spinner="Computing Q1 share by year…")
def get_q1_share_by_year():
    return journal_tier.q1_share_by_year(load_deduplicated(), MAIN_YEAR_RANGE)


@st.cache_data(show_spinner="Summarising CiteScore percentile…")
def get_citescore_percentile_distribution():
    return journal_tier.citescore_percentile_distribution(load_deduplicated())


@st.cache_data(show_spinner="Preparing CiteScore percentile series…")
def get_citescore_percentile_series():
    """Row-level series for a histogram — shows the actual right-skew (most
    publications cluster in the low, i.e. good, percentiles) that the
    describe() table alone doesn't make visible."""
    from p36.metrics.metrics import CITESCORE_PERCENTILE_COL

    return load_deduplicated()[CITESCORE_PERCENTILE_COL].dropna()


@st.cache_data(show_spinner="Comparing CiteScore-based and SJR-based Q1…")
def get_q1_definition_agreement():
    """How much would the open question in docs/methodology.md (CiteScore
    percentile vs SJR percentile as the Q1 basis) actually change the answer?
    Both use the same "<=" (lower-is-better) threshold and cutoff — only the
    underlying source column differs. Restricted to rows with both
    percentiles present, so the comparison is apples-to-apples.
    """
    from p36.config import Q1_CITESCORE_PERCENTILE_MAX
    from p36.metrics.metrics import CITESCORE_PERCENTILE_COL

    sjr_col = "SJR percentile (publication year) *"
    df = load_deduplicated()[[CITESCORE_PERCENTILE_COL, sjr_col]].dropna()
    citescore_q1 = df[CITESCORE_PERCENTILE_COL] <= Q1_CITESCORE_PERCENTILE_MAX
    sjr_q1 = df[sjr_col] <= Q1_CITESCORE_PERCENTILE_MAX
    return {
        "n": len(df),
        "both_q1": int((citescore_q1 & sjr_q1).sum()),
        "citescore_only": int((citescore_q1 & ~sjr_q1).sum()),
        "sjr_only": int((~citescore_q1 & sjr_q1).sum()),
        "neither": int((~citescore_q1 & ~sjr_q1).sum()),
        "agreement_rate": float((citescore_q1 == sjr_q1).mean()),
    }


@st.cache_data(show_spinner="Comparing citation performance across Q1-Q4…")
def get_impact_by_citescore_quartile():
    return journal_tier.impact_by_citescore_quartile(load_deduplicated())


@st.cache_data(show_spinner="Checking whether the Q1 advantage holds across every field…")
def get_q1_advantage_by_field():
    exploded, _ = load_exploded_deduplicated()
    return journal_tier.q1_advantage_by_field(exploded)


@st.cache_data(show_spinner="Finding sources that over/under-perform their own tier…")
def get_overperforming_sources():
    return journal_tier.overperforming_sources(load_deduplicated())


# --- 6. Field analysis (app/pages/3_Field_Analysis.py) ----------------------


@st.cache_data(show_spinner="Computing field summary…")
def get_field_summary():
    exploded, _ = load_exploded_deduplicated()
    return field_analysis.field_summary(exploded)


@st.cache_data(show_spinner="Computing field growth…")
def get_field_growth():
    exploded, _ = load_exploded_deduplicated()
    return field_analysis.field_growth(exploded)


@st.cache_data(show_spinner="Computing field trend…")
def get_field_trend():
    exploded, _ = load_exploded_deduplicated()
    return field_analysis.field_trend(exploded)


# --- 9. International collaboration (app/pages/4_International_Collaboration.py) --


@st.cache_data(show_spinner="Computing impact by collaboration status…")
def get_impact_by_collaboration_status():
    return intl.impact_by_collaboration_status(load_deduplicated())


@st.cache_data(show_spinner="Computing impact gap by field…")
def get_impact_gap_by_field():
    exploded, _ = load_exploded_deduplicated()
    return intl.impact_gap_by_field(exploded)


@st.cache_data(show_spinner="Computing impact gap by year…")
def get_impact_gap_by_year():
    return intl.impact_gap_by_year(load_deduplicated())


@st.cache_data(show_spinner="Computing impact by collaboration breadth…")
def get_impact_by_collaboration_breadth():
    return intl.impact_by_collaboration_breadth(load_deduplicated())


@st.cache_data(show_spinner="Computing collaboration-rate trend…")
def get_collaboration_rate_trend(university: str):
    return intl.collaboration_rate_trend(load_raw(), university)


@st.cache_data(show_spinner="Preparing FWCI distribution (international vs domestic)…")
def get_fwci_by_collaboration_status():
    """Row-level slice for a box plot — the shape of the distribution, not
    just its mean, matters for a claim this consequential (see
    finding-checker.md: FWCI is heavy-tailed, and status.mean_fwci in
    get_impact_by_collaboration_status hides how much the two groups
    actually overlap)."""
    df = load_deduplicated()
    return df[["is_international", "Field-Weighted Citation Impact"]].copy()


@st.cache_data(show_spinner="Preparing FWCI distribution by field…")
def get_fwci_by_field():
    """Row-level slice for a box plot, one row per (publication, field)
    membership — see p36.analysis.field_analysis on why this over-counts a
    multi-field paper (whole counting)."""
    from p36.analysis.field_analysis import FIELD_COLUMN_EXPLODED

    exploded, _ = load_exploded_deduplicated()
    return exploded[[FIELD_COLUMN_EXPLODED, "Field-Weighted Citation Impact"]].copy()


# --- 17. Scenario analysis (app/pages/6_Scenario_Analysis.py) ---------------


@st.cache_data(show_spinner="Computing scenario projections…")
def get_scenario_table(delta_pp: float):
    return scenario_analysis.scenario_table(load_deduplicated(), delta_pp=delta_pp)


# --- Shared UI components ----------------------------------------------------


def caveat(text: str) -> None:
    """A consistently-styled methodology caveat box — use for anything that
    would need finding-checker.md's attention before appearing in a report."""
    st.info(text, icon="⚠️")


def provisional(text: str) -> None:
    """A consistently-styled PROVISIONAL-definition box — use whenever a figure
    depends on a p36.config value marked PROVISIONAL (not yet confirmed by the
    client)."""
    st.warning(text, icon="🚧")
