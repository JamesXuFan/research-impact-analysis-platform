import streamlit as st

import theme

st.set_page_config(page_title="Sub-Question Index", page_icon="🗂️", layout="wide")
theme.inject()
theme.header(
    "Sub-Question Index",
    "Every sub-question from the brief across all 6 analyses, in one place — status, "
    "the exact source module that answers it, and a jump straight to its page.",
    shape="square",
    color=theme.BLACK,
)

st.caption(
    "✓ answered directly · ~ answered, aggregate/qualitative only · → answered on a "
    "different page · module references are `file.py :: function()` under `src/p36/` "
    "(app pages call these through the cached wrappers in `app/lib.py`, not listed "
    "separately below — see that file if a function isn't cached where you'd expect)."
)

theme.rule(theme.YELLOW)

# --- Item 16 -----------------------------------------------------------------

st.subheader("16 · Go8 / Peer Benchmarking")
st.page_link("pages/1_Go8_Benchmarking.py", label="Open this page →", icon="🏆")
theme.index_table(
    [
        ("How does Sydney compare in publication volume?", "done", "go8_benchmarking.py :: benchmark_summary()"),
        ("How does citation impact compare?", "done", "go8_benchmarking.py :: benchmark_summary()"),
        ("How does Q1 publication share compare?", "done", "go8_benchmarking.py :: benchmark_summary()"),
        ("How does highly cited publication performance compare?", "done", "go8_benchmarking.py :: benchmark_summary()"),
        ("How does international collaboration compare?", "done", "go8_benchmarking.py :: benchmark_summary()"),
        ("How does institutional collaboration compare?", "done", "go8_benchmarking.py :: benchmark_summary() — mean_institutions_per_paper"),
        ("Which research fields are Sydney's strongest relative to peers? Where are the largest gaps?", "done", "go8_benchmarking.py :: field_gap_vs_peers()"),
        ("Which Go8 universities are improving most rapidly?", "done", "go8_benchmarking.py :: growth_by_university()"),
        ("Are competitors using different journal-publishing patterns?", "done", "go8_benchmarking.py :: journal_pattern_by_university()"),
        ("Are competitors collaborating with different countries or institutions?", "partial", "go8_benchmarking.py :: top_countries_by_university() — countries only, one university at a time"),
        ("Which performance gaps appear realistically addressable?", "partial", "synthesis of field_gap_vs_peers() — no dedicated function"),
    ]
)

theme.rule(theme.YELLOW)

# --- Item 3 --------------------------------------------------------------------

st.subheader("3 · Journal Tier and Q1 Analysis")
st.page_link("pages/2_Journal_Tier.py", label="Open this page →", icon="🎯")
theme.index_table(
    [
        ("Do publications in Q1 journals receive more citations than Q2, Q3 or Q4 journals?", "done", "journal_tier.py :: impact_by_citescore_quartile()"),
        ("How large is the citation difference between journal tiers?", "done", "journal_tier.py :: impact_by_citescore_quartile()"),
        ("Which faculties/fields have the highest success rates in Q1 publishing?", "elsewhere", "→ item 6 page — journal_tier.py :: q1_share_by_field()"),
        ("Is the Q1 citation advantage consistent across disciplines, or concentrated in a few?", "done", "journal_tier.py :: q1_advantage_by_field()"),
        ("Compare highly-cited (top-decile) publication rates across quartiles.", "done", "journal_tier.py :: impact_by_citescore_quartile() — top_decile_share"),
        ("Compare uncited-publication rates across quartiles.", "done", "journal_tier.py :: impact_by_citescore_quartile() — uncited_share"),
        ("Does publishing in Q1 increase the probability of becoming highly cited?", "done", "journal_tier.py :: impact_by_citescore_quartile()"),
        ("Which fields have the highest / improving / declining Q1 share?", "elsewhere", "→ item 6 page — field_analysis.py :: field_growth(), journal_tier.py :: q1_share_by_field()"),
        ("Are there journals/publications within a tier that receive more citations than expected for that tier?", "done", "journal_tier.py :: overperforming_sources()"),
    ]
)

theme.rule(theme.YELLOW)

# --- Item 6 --------------------------------------------------------------------

st.subheader("6 · Research Field / Faculty Analysis")
st.page_link("pages/3_Field_Analysis.py", label="Open this page →", icon="🔬")
theme.index_table(
    [
        ("Which fields produce the highest publication volume?", "done", "field_analysis.py :: field_summary()"),
        ("Which fields achieve the strongest impact?", "done", "field_analysis.py :: field_summary()"),
        ("Which fields have the highest Q1 publication share?", "done", "field_analysis.py :: field_summary() — q1_share"),
        ("Which fields have high volume but relatively low citation impact?", "done", "field_analysis.py :: volume_vs_impact_quadrant()"),
        ("Which fields have relatively low volume but very strong citation impact?", "done", "field_analysis.py :: volume_vs_impact_quadrant()"),
        ("Which areas are improving most rapidly / declining?", "done", "field_analysis.py :: field_growth()"),
        ("Which fields produce the highest proportion of overperforming (top-decile) publications?", "done", "field_analysis.py :: field_summary() — top_decile_share"),
        ("Which fields produce the largest number of highly cited publications?", "done", "computed in-page from field_summary() — publications × top_decile_share"),
        ("Which fields appear to represent existing strengths, and where is the greatest potential for improvement?", "partial", "synthesis of field_summary()/volume_vs_impact_quadrant()/field_growth() — no dedicated function"),
        ("Are particular publication strategies more successful in some fields than others?", "done", "field_analysis.py :: collaboration_approach_by_field()"),
    ]
)

theme.rule(theme.YELLOW)

# --- Item 9 --------------------------------------------------------------------

st.subheader("9 · International Collaboration Analysis")
st.page_link("pages/4_International_Collaboration.py", label="Open this page →", icon="🌏")
theme.index_table(
    [
        ("Do internationally collaborative publications receive higher citation impact?", "done", "international_collaboration.py :: impact_by_collaboration_status()"),
        ("Does the relationship remain after considering research field?", "done", "international_collaboration.py :: impact_gap_by_field()"),
        ("Does the relationship remain after considering publication year?", "done", "international_collaboration.py :: impact_gap_by_year()"),
        ("Are internationally collaborative papers more likely to publish in Q1 journals?", "done", "international_collaboration.py :: impact_by_collaboration_status() — q1_share"),
        ("Are they more likely to become highly cited?", "done", "international_collaboration.py :: impact_by_collaboration_status() — top_decile_share"),
        ("Are they less likely to remain uncited?", "done", "international_collaboration.py :: impact_by_collaboration_status() — uncited_share"),
        ("Does the impact of international collaboration vary across disciplines?", "done", "international_collaboration.py :: impact_gap_by_field()"),
        ("Are some forms of international collaboration more beneficial than others?", "done", "international_collaboration.py :: impact_by_collaboration_breadth()"),
        ("Has Sydney's international collaboration rate increased or declined over time?", "done", "international_collaboration.py :: collaboration_rate_trend()"),
    ]
)

theme.rule(theme.YELLOW)

# --- Item 14 -------------------------------------------------------------------

st.subheader("14 · Integrated Research Impact Driver Analysis")
st.page_link("pages/5_Impact_Drivers.py", label="Open this page →", icon="📈")
theme.index_table(
    [
        ("Which factors have the strongest association with citation impact?", "done", "impact_drivers.py :: fit_impact_driver_model(), driver_summary_table()"),
        ("Which factors remain important after controlling for other metrics?", "done", "impact_drivers.py :: fit_impact_driver_model()"),
        ("Is journal quartile (Q1) still important after accounting for field?", "done", "impact_drivers.py :: fit_impact_driver_model() — field fixed effects"),
        ("Is international collaboration still important after accounting for journal quality?", "done", "impact_drivers.py :: fit_impact_driver_model()"),
        ("Open Access → Citation Impact", "done", "impact_drivers.py :: fit_impact_driver_model() — is_open_access coefficient"),
        ("Collaboration Size → Citation Impact", "done", "impact_drivers.py :: fit_impact_driver_model() — log_authors coefficient"),
        ("Document Type → Citation Impact", "done", "impact_drivers.py :: document_type_summary_table()"),
        ("Does international collaboration indirectly improve impact by increasing the likelihood of Q1 publishing?", "partial", "qualitative only — cross-ref international_collaboration.py :: impact_by_collaboration_breadth()"),
        ("Institutional Collaboration → Journal Choice → Citation Impact", "partial", "impact_drivers.py :: fit_impact_driver_model() — log_institutions is a direct effect only, no mediator variable"),
        ("Is there an interaction between journal quality and international collaboration?", "done", "impact_drivers.py :: fit_interaction_model(), interaction_summary_table()"),
        ("What combination of factors is most commonly associated with high- vs. low-impact publications?", "done", "impact_drivers.py :: combination_summary()"),
        ("Are some drivers particularly important only in particular disciplines?", "elsewhere", "→ item 3 page (journal_tier.py :: q1_advantage_by_field()), item 9 page (international_collaboration.py :: impact_gap_by_field())"),
    ]
)

theme.rule(theme.YELLOW)

# --- Item 17 -------------------------------------------------------------------

st.subheader("17 · Scenario Analysis")
st.page_link("pages/6_Scenario_Analysis.py", label="Open this page →", icon="🔮")
theme.index_table(
    [
        ("Increase Q1 publication share by N percentage points.", "done", "scenario_analysis.py :: scenario_table() — is_q1 row"),
        ("Increase international collaboration by N percentage points.", "done", "scenario_analysis.py :: scenario_table() — is_international row"),
        ("Increase open-access publication where evidence suggests a benefit.", "done", "scenario_analysis.py :: scenario_table() — is_open_access row"),
        ("Reduce the proportion of low-impact publications.", "partial", "scenario_analysis.py :: scenario_table() — is_uncited row, a proxy for 'low-impact'"),
        ("Improve publication performance within selected research areas.", "elsewhere", "→ item 16 page — go8_benchmarking.py :: field_gap_vs_peers()"),
        ("Increase collaboration with selected high-performing institutions.", "done", "scenario_analysis.py :: client_institution_scenario(), go8_benchmarking.py :: institution_partner_performance()"),
        ("Shift some publications toward journals identified as strong opportunities.", "done", "scenario_analysis.py :: scenario_table() — is_source_overperforming row, journal_tier.py :: source_performance_flag()"),
    ]
)

theme.rule(theme.YELLOW)

st.caption(
    "This index is generated by hand from each page's own 'Sub-questions this page "
    "answers' panel — if a status or reference here ever looks stale relative to the "
    "page itself, the page is the source of truth, not this index. See also the "
    "**Coverage Manual** artifact (linked from the project README) for the same "
    "content with the functional \"what's on the page\" description alongside it."
)
