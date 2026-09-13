"""Go8 Benchmarking's own data layer (README item 16, app/pages/1_Go8_Benchmarking.py).

Split out of the old lib.py so this page depends only on the modules it
actually needs (p36.analysis.go8_benchmarking, .prepare, .field_analysis for
the exploded dataset) — not on journal_tier, international_collaboration, or
scenario_analysis, which the old shared lib.py imported unconditionally for
every page. get_top_countries and get_institution_partner_performance are
also used elsewhere (International Collaboration, Scenario Analysis); this
file is the canonical owner and theirs are independent copies, not imports
from here.
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st

from p36.analysis import field_analysis, go8_benchmarking, prepare
from p36.config import CLIENT_UNIVERSITY

__all__ = [
    "CLIENT_UNIVERSITY",
    "caveat",
    "load_raw",
    "get_benchmark_summary",
    "get_growth_by_university",
    "get_field_gap_vs_peers",
    "get_top_countries",
    "get_journal_pattern",
    "get_institution_partner_performance",
]


def caveat(text: str) -> None:
    st.info(text, icon="⚠️")


@st.cache_data(show_spinner="Loading publication data (per-university)…")
def load_raw():
    return prepare.prepared_raw()


@st.cache_data(show_spinner="Building field-level breakdown (per-university)…")
def _load_exploded_raw():
    return field_analysis.explode_by_field(load_raw())


@st.cache_data(show_spinner="Computing Go8 benchmark summary…")
def get_benchmark_summary():
    return go8_benchmarking.benchmark_summary(load_raw())


@st.cache_data(show_spinner="Computing university growth…")
def get_growth_by_university():
    return go8_benchmarking.growth_by_university(load_raw())


@st.cache_data(show_spinner="Computing field gap vs. Go8 peers…")
def get_field_gap_vs_peers():
    return go8_benchmarking.field_gap_vs_peers(_load_exploded_raw())


@st.cache_data(show_spinner="Computing top co-author countries…")
def get_top_countries(university: str, top_n: int = 10):
    return go8_benchmarking.top_countries_by_university(load_raw(), university, top_n=top_n)


@st.cache_data(show_spinner="Computing journal-publishing pattern…")
def get_journal_pattern():
    return go8_benchmarking.journal_pattern_by_university(load_raw())


@st.cache_data(show_spinner="Ranking Sydney's partner institutions by performance…")
def get_institution_partner_performance():
    return go8_benchmarking.institution_partner_performance(load_raw())
