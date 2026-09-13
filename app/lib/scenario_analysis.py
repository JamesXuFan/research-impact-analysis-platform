"""Scenario Analysis's own data layer (README item 17,
app/pages_disabled/6_Scenario_Analysis.py — currently withdrawn from the
platform nav, see that folder's README.md).

Split out of the old lib.py. Honest caveat: Scenario Analysis is inherently
a "combine other analyses' outputs" feature (see docs/methodology.md,
Scenario Analysis) — get_scenario_table needs journal_tier's
source_performance_flag, get_client_institution_scenario needs
go8_benchmarking's institution_partner_flag, and get_field_gap_closure_scenario
needs go8_benchmarking's field_gap_vs_peers numbers. This file imports
p36.analysis.journal_tier and .go8_benchmarking directly for exactly that
reason — that is a real dependency of what this feature computes, not
something a lib split can remove. What this file *does* remove is the old
lib.py's incidental coupling to field_analysis and international_collaboration,
which scenario_analysis never actually needed.
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st

from p36.analysis import go8_benchmarking, journal_tier, prepare, scenario_analysis
from p36.config import CLIENT_UNIVERSITY

__all__ = [
    "CLIENT_UNIVERSITY",
    "get_scenario_table",
    "get_institution_partner_performance",
    "get_client_institution_scenario",
    "get_field_gap_vs_peers",
    "get_field_gap_closure_scenario",
]


@st.cache_data(show_spinner="Loading publication data (per-university)…")
def load_raw():
    return prepare.prepared_raw()


@st.cache_data(show_spinner="Loading publication data (deduplicated)…")
def load_deduplicated():
    return prepare.prepared_deduplicated()


@st.cache_data(show_spinner="Building field-level breakdown (per-university)…")
def _load_exploded_raw():
    from p36.analysis import field_analysis

    return field_analysis.explode_by_field(load_raw())


@st.cache_data(show_spinner="Computing scenario projections…")
def get_scenario_table(delta_pp: float):
    dedup = load_deduplicated()
    dedup = dedup.assign(is_source_overperforming=journal_tier.source_performance_flag(dedup))
    return scenario_analysis.scenario_table(dedup, delta_pp=delta_pp)


@st.cache_data(show_spinner="Ranking Sydney's partner institutions by performance…")
def get_institution_partner_performance():
    return go8_benchmarking.institution_partner_performance(load_raw())


@st.cache_data(show_spinner="Computing the high-performing-institution scenario…")
def get_client_institution_scenario(delta_pp: float):
    raw = load_raw()
    flag = go8_benchmarking.institution_partner_flag(raw, CLIENT_UNIVERSITY)
    return scenario_analysis.client_institution_scenario(raw, CLIENT_UNIVERSITY, flag, delta_pp=delta_pp)


@st.cache_data(show_spinner="Computing field gap vs. Go8 peers…")
def get_field_gap_vs_peers():
    return go8_benchmarking.field_gap_vs_peers(_load_exploded_raw())


@st.cache_data(show_spinner="Computing the research-area scenario…")
def get_field_gap_closure_scenario(field: str, gap_close_frac: float):
    from p36.config import FIELD_COLUMN_EXPLODED

    exploded = _load_exploded_raw()
    gap = get_field_gap_vs_peers().loc[field, "gap"]
    return scenario_analysis.estimate_uplift_from_field_gap_closure(
        exploded, FIELD_COLUMN_EXPLODED, field, gap, gap_close_frac=gap_close_frac
    )
