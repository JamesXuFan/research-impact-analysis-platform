"""Field Analysis's own data layer (README item 6, app/pages/3_Field_Analysis.py).

Split out of the old lib.py — depends only on p36.analysis.field_analysis and
.prepare, not on go8_benchmarking, journal_tier, international_collaboration,
or scenario_analysis.
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st

from p36.analysis import field_analysis, prepare
from p36.config import FIELD_COLUMN_EXPLODED

__all__ = [
    "caveat",
    "load_exploded_deduplicated",
    "get_collaboration_approach_by_field",
    "get_field_summary",
    "get_field_growth",
    "get_field_trend",
    "get_fwci_by_field",
]


def caveat(text: str) -> None:
    st.info(text, icon="⚠️")


@st.cache_data(show_spinner="Loading publication data (deduplicated)…")
def load_deduplicated():
    return prepare.prepared_deduplicated()


@st.cache_data(show_spinner="Building field-level breakdown (deduplicated)…")
def load_exploded_deduplicated():
    dropped_before = load_deduplicated()[field_analysis.FIELD_COLUMN].isna().sum()
    exploded = field_analysis.explode_by_field(load_deduplicated())
    return exploded, dropped_before


@st.cache_data(show_spinner="Comparing collaboration approaches by field…")
def get_collaboration_approach_by_field():
    exploded, _ = load_exploded_deduplicated()
    exploded = field_analysis.add_collaboration_approach(exploded)
    return field_analysis.collaboration_approach_by_field(exploded)


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


@st.cache_data(show_spinner="Preparing FWCI distribution by field…")
def get_fwci_by_field():
    exploded, _ = load_exploded_deduplicated()
    return exploded[[FIELD_COLUMN_EXPLODED, "Field-Weighted Citation Impact"]].copy()
