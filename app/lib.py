import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pandas as pd
import streamlit as st

from p36.analysis import field_analysis, go8_benchmarking, journal_tier, prepare, scenario_analysis
from p36.analysis import international_collaboration as intl
from p36.config import CLIENT_UNIVERSITY, FIELD_COLUMN_EXPLODED, GO8_UNIVERSITIES, MAIN_YEAR_RANGE

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
    "get_collaboration_approach_by_field",
    "get_field_growth",
    "get_field_trend",
    "get_impact_by_collaboration_status",
    "get_impact_gap_by_field",
    "get_impact_gap_by_year",
    "get_impact_by_collaboration_breadth",
    "get_collaboration_rate_trend",
    "get_scenario_table",
    "get_institution_partner_performance",
    "get_client_institution_scenario",
    "get_fwci_by_collaboration_status",
    "get_fwci_by_field",
    "get_citescore_percentile_series",
    "get_q1_definition_agreement",
    "get_overlap_by_university",
    "get_impact_by_citescore_quartile",
    "get_q1_advantage_by_field",
    "get_overperforming_sources",
    "get_q1_share_change_by_field",
    "get_field_gap_closure_scenario",
    "caveat",
    "provisional",
]

@st.cache_data(show_spinner="Loading publication data (per-university)…")
def load_raw():
    return prepare.prepared_raw()

@st.cache_data(show_spinner="Loading publication data (deduplicated)…")
def load_deduplicated():
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
    exploded, _ = load_exploded_deduplicated()
    return journal_tier.q1_advantage_by_field(exploded)

@st.cache_data(show_spinner="Finding sources that over/under-perform their own tier…")
def get_overperforming_sources():
    return journal_tier.overperforming_sources(load_deduplicated())

@st.cache_data(show_spinner="Checking which fields' Q1 share is rising or falling…")
def get_q1_share_change_by_field():
    exploded, _ = load_exploded_deduplicated()
    return journal_tier.q1_share_change_by_field(exploded, FIELD_COLUMN_EXPLODED, MAIN_YEAR_RANGE)

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
    df = load_deduplicated()
    return df[["is_international", "Field-Weighted Citation Impact"]].copy()

@st.cache_data(show_spinner="Preparing FWCI distribution by field…")
def get_fwci_by_field():
    exploded, _ = load_exploded_deduplicated()
    return exploded[[FIELD_COLUMN_EXPLODED, "Field-Weighted Citation Impact"]].copy()

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

@st.cache_data(show_spinner="Computing the research-area scenario…")
def get_field_gap_closure_scenario(field: str, gap_close_frac: float):
    exploded, _ = load_exploded_raw()
    gap = get_field_gap_vs_peers().loc[field, "gap"]
    return scenario_analysis.estimate_uplift_from_field_gap_closure(
        exploded, FIELD_COLUMN_EXPLODED, field, gap, gap_close_frac=gap_close_frac
    )

def caveat(text: str) -> None:
    st.info(text, icon="⚠️")

def provisional(text: str) -> None:
    st.warning(text, icon="🚧")
