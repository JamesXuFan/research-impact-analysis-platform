"""Home.py's own data layer — deliberately separate from lib.py.

lib.py imports all six analysis modules (field_analysis, go8_benchmarking,
journal_tier, international_collaboration, scenario_analysis) at module level,
so importing anything from it — even just load_raw() — pulls in every analysis
task's code. Home.py doesn't need any of that: it only ever touches the raw/
deduplicated dataset and a plain pandas overlap computation. This module gives
it that, and nothing else — no dependency on any app/pages/*.py analysis task.
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pandas as pd
import streamlit as st

from p36.analysis import prepare
from p36.config import CLIENT_UNIVERSITY, GO8_UNIVERSITIES

__all__ = [
    "CLIENT_UNIVERSITY",
    "GO8_UNIVERSITIES",
    "load_raw",
    "load_deduplicated",
    "get_overlap_by_university",
    "caveat",
]


@st.cache_data(show_spinner="Loading publication data (per-university)…")
def load_raw():
    return prepare.prepared_raw()


@st.cache_data(show_spinner="Loading publication data (deduplicated)…")
def load_deduplicated():
    return prepare.prepared_deduplicated()


@st.cache_data(show_spinner="Computing Go8-shared vs. exclusive output…")
def get_overlap_by_university():
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


def caveat(text: str) -> None:
    st.info(text, icon="⚠️")
