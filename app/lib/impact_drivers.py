"""Impact Drivers' own data layer (README item 14,
app/pages_disabled/5_Impact_Drivers.py — currently withdrawn from the
platform nav, see that folder's README.md).

Split out of the old lib.py. impact_drivers.py itself defines its own
@st.cache_resource wrappers for the fitted regression object (a heavier
object than @st.cache_data is meant for), so this file only needs the base
loader plus get_impact_by_collaboration_breadth — international_collaboration's
function, needed here too for one comparison panel; this is an independent
copy, not an import from lib_international_collaboration.py.
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st

from p36.analysis import international_collaboration as intl
from p36.analysis import prepare

__all__ = [
    "load_deduplicated",
    "get_impact_by_collaboration_breadth",
]


@st.cache_data(show_spinner="Loading publication data (deduplicated)…")
def load_deduplicated():
    return prepare.prepared_deduplicated()


@st.cache_data(show_spinner="Computing impact by collaboration breadth…")
def get_impact_by_collaboration_breadth():
    return intl.impact_by_collaboration_breadth(load_deduplicated())
