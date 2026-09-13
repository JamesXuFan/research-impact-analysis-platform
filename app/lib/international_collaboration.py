"""International Collaboration's own data layer (README item 9,
app/pages/4_International_Collaboration.py).

Split out of the old lib.py — depends only on
p36.analysis.international_collaboration, .prepare, and .field_analysis (for
the exploded dataset), not on go8_benchmarking, journal_tier, or
scenario_analysis. get_top_countries is go8_benchmarking's function, needed
here too for the top-co-author-countries panel; this is an independent copy,
not an import from lib_go8_benchmarking.py.
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st

from p36.analysis import field_analysis, go8_benchmarking, prepare
from p36.analysis import international_collaboration as intl
from p36.config import CLIENT_UNIVERSITY

__all__ = [
    "CLIENT_UNIVERSITY",
    "caveat",
    "load_raw",
    "get_impact_by_collaboration_status",
    "get_impact_gap_by_field",
    "get_impact_gap_by_year",
    "get_impact_by_collaboration_breadth",
    "get_collaboration_rate_trend",
    "get_fwci_by_collaboration_status",
    "get_top_countries",
]


def caveat(text: str) -> None:
    st.info(text, icon="⚠️")


@st.cache_data(show_spinner="Loading publication data (per-university)…")
def load_raw():
    return prepare.prepared_raw()


@st.cache_data(show_spinner="Loading publication data (deduplicated)…")
def load_deduplicated():
    return prepare.prepared_deduplicated()


@st.cache_data(show_spinner="Building field-level breakdown (deduplicated)…")
def _load_exploded_deduplicated():
    return field_analysis.explode_by_field(load_deduplicated())


@st.cache_data(show_spinner="Computing impact by collaboration status…")
def get_impact_by_collaboration_status():
    return intl.impact_by_collaboration_status(load_deduplicated())


@st.cache_data(show_spinner="Computing impact gap by field…")
def get_impact_gap_by_field():
    return intl.impact_gap_by_field(_load_exploded_deduplicated())


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
    df = load_deduplicated()
    return df[["is_international", "Field-Weighted Citation Impact"]].copy()


@st.cache_data(show_spinner="Computing top co-author countries…")
def get_top_countries(university: str, top_n: int = 10):
    return go8_benchmarking.top_countries_by_university(load_raw(), university, top_n=top_n)
