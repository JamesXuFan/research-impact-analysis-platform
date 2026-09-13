"""Journal Tier's own data layer (README item 3, app/pages/2_Journal_Tier.py).

Split out of the old lib.py — depends only on p36.analysis.journal_tier,
.prepare, and .field_analysis (for the exploded dataset), not on
go8_benchmarking, international_collaboration, or scenario_analysis.
get_field_summary is field_analysis's function, needed here too for the
per-field CiteScore breakdown; this is an independent copy, not an import
from lib_field_analysis.py.
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st

from p36.analysis import field_analysis, journal_tier, prepare
from p36.config import CLIENT_UNIVERSITY, FIELD_COLUMN_EXPLODED, MAIN_YEAR_RANGE

__all__ = [
    "CLIENT_UNIVERSITY",
    "provisional",
    "get_q1_share_by_university",
    "get_q1_share_by_year",
    "get_citescore_percentile_distribution",
    "get_citescore_percentile_series",
    "get_q1_definition_agreement",
    "get_impact_by_citescore_quartile",
    "get_q1_advantage_by_field",
    "get_overperforming_sources",
    "get_q1_share_change_by_field",
    "get_field_summary",
]


def provisional(text: str) -> None:
    st.warning(text, icon="🚧")


@st.cache_data(show_spinner="Loading publication data (deduplicated)…")
def load_deduplicated():
    return prepare.prepared_deduplicated()


@st.cache_data(show_spinner="Building field-level breakdown (deduplicated)…")
def _load_exploded_deduplicated():
    return field_analysis.explode_by_field(load_deduplicated())


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
    from p36.metrics.metrics import CITESCORE_PERCENTILE_COL

    return load_deduplicated()[CITESCORE_PERCENTILE_COL].dropna()


@st.cache_data(show_spinner="Comparing CiteScore-based and SJR-based Q1…")
def get_q1_definition_agreement():
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
    return journal_tier.q1_advantage_by_field(_load_exploded_deduplicated())


@st.cache_data(show_spinner="Finding sources that over/under-perform their own tier…")
def get_overperforming_sources():
    return journal_tier.overperforming_sources(load_deduplicated())


@st.cache_data(show_spinner="Checking which fields' Q1 share is rising or falling…")
def get_q1_share_change_by_field():
    return journal_tier.q1_share_change_by_field(_load_exploded_deduplicated(), FIELD_COLUMN_EXPLODED, MAIN_YEAR_RANGE)


@st.cache_data(show_spinner="Computing field summary…")
def get_field_summary():
    return field_analysis.field_summary(_load_exploded_deduplicated())
