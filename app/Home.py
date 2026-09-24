import altair as alt
import streamlit as st

import theme
from lib.home import CLIENT_UNIVERSITY, GO8_UNIVERSITIES, caveat, get_overlap_by_university, load_deduplicated, load_raw

st.set_page_config(page_title="P36 · Publication Intelligence Platform", page_icon=theme.FAVICON, layout="wide")
theme.inject()
theme.header(
    "Publication Intelligence & Research Impact Analysis Platform",
    "COMP3888 Capstone · Team W11_02_P36 · Data: 8 Go8 university QS 2027 publication exports",
    shape="square",
    color=theme.RED,
)

st.markdown(
    """
This platform provides a comparative analysis of publication output, citation impact and
collaboration patterns across the eight Group of Eight (Go8) universities, based on
publication-level Scopus/QS records for 2020–2024. Each analysis addresses one item of the
project brief and is accessible from the sidebar.

**Definitions.** *Field-Weighted Citation Impact (FWCI)* is the ratio of the citations a
publication has received to the citations expected for publications of the same field, year
and document type; a value of 1.0 corresponds to the world average. *Q1* denotes sources in
the top quartile of their field by CiteScore percentile. *Highly cited* publications are
those in the top decile of citations within their field.
"""
)

st.subheader("Analyses")
guide_cols = st.columns(3)
guide = [
    ("Journal Tier / Q1", "3", "What share of output is in Q1 journals, and how does that vary?"),
    ("Field Analysis", "6", "Which fields are strongest, improving or under-performing?"),
    ("International Collaboration", "9", "Are internationally co-authored papers cited more, and does this hold within field and year?"),
    ("Impact Drivers", "14", "Holding other factors constant, which drivers are associated with impact?"),
    ("Go8 Benchmarking", "16", "How does Sydney compare with its Go8 peers on volume, impact, Q1 share and collaboration?"),
    ("Scenario Analysis", "17", "What would mean impact be under a hypothetical shift in these drivers?"),
]
for i, (name, item_no, question) in enumerate(guide):
    with guide_cols[i % 3]:
        st.markdown(
            f"**Item {item_no} · {name}**  \n{question}",
        )

theme.rule(theme.YELLOW)

raw = load_raw()
dedup = load_deduplicated()

col1, col2, col3, col4 = st.columns(4)
col1.metric("All listed publications", f"{len(raw):,}")
col2.metric("Unique publications", f"{len(dedup):,}")
dup_pct = 100 * (1 - len(dedup) / len(raw))
col3.metric("Shared between universities", f"{dup_pct:.1f}%")
col4.metric("Universities", len(GO8_UNIVERSITIES))

theme.rule(theme.YELLOW)

st.subheader("Publication output by university")
order = [CLIENT_UNIVERSITY] + [u for u in GO8_UNIVERSITIES if u != CLIENT_UNIVERSITY]
counts = raw["source_university"].value_counts().reindex(order)
tree_df = counts.rename_axis("university").reset_index(name="publications")
tree_df["is_client"] = tree_df["university"] == CLIENT_UNIVERSITY

col_bar, col_donut = st.columns(2)
with col_bar:
    bar = (
        alt.Chart(tree_df)
        .mark_bar()
        .encode(
            x=alt.X("university:N", sort=order, title="", axis=alt.Axis(labelAngle=-30)),
            y=alt.Y("publications:Q", title="Publications"),
            color=alt.Color(
                "is_client:N", legend=None,
                scale=alt.Scale(domain=[True, False], range=[theme.RED, theme.BLUE]),
            ),
            tooltip=["university", "publications"],
        )
    )
    st.altair_chart(theme.style(bar), use_container_width=True)

with col_donut:
    st.caption("Proportional distribution of the same counts.")
    donut = (
        alt.Chart(tree_df)
        .mark_arc(innerRadius=60)
        .encode(
            theta=alt.Theta("publications:Q"),
            color=alt.Color(
                "university:N", title="",
                scale=alt.Scale(domain=order, range=[theme.RED] + [theme.BLUE, theme.YELLOW, theme.BLACK, theme.GREY, "#6B8E23", "#8B5E3C", "#4A6D7C"]),
            ),
            tooltip=["university", "publications"],
        )
    )
    st.altair_chart(theme.style(donut, height=340), use_container_width=True)

theme.rule(theme.YELLOW)

st.subheader("Exclusive and jointly authored publications by university")
st.caption(
    "For each university, publications that also appear in the export of another Go8 "
    "university (jointly authored) are distinguished from those appearing in its own "
    "export only. A high shared proportion reflects a high degree of intra-Go8 "
    "co-authorship and does not imply inflation of that university's total."
)
overlap = get_overlap_by_university().reindex(order).rename_axis("University").rename(
    columns={
        "raw_publications": "Publications",
        "shared_with_another_go8_university": "Shared with another Go8 university",
        "exclusive_to_this_university": "This university only",
        "shared_share": "Shared share",
    }
)
st.table(
    overlap.style.format(
        {
            "Publications": "{:,.0f}",
            "Shared with another Go8 university": "{:,.0f}",
            "This university only": "{:,.0f}",
            "Shared share": "{:.1%}",
        }
    ),
)

theme.rule(theme.YELLOW)

st.subheader("Data description")
prov_cols = st.columns(4)
prov_cols[0].metric("Year range", "2020–2024")
prov_cols[1].metric("Data source", "Scopus")
prov_cols[2].metric("Exported on", "14 Aug 2026")
prov_cols[3].metric("Files (one per university)", "8")
st.caption(
    "Values are taken from the metadata of each export. Publication years are not strictly "
    "confined to the reference period: six records fall outside it (2013, 2014 and 2019), "
    "which is negligible, and 429 fall in 2025–2026, consistent with the export date. "
    "Trend analyses are restricted to the main period."
)

caveat(
    "Definitions applied throughout: a publication is classified as Q1 when its source lies "
    "within the top 25% of its field by CiteScore percentile; publications assigned to "
    "several fields are counted in each of them; retracted publications are excluded; and "
    "the most recent years are omitted from citation comparisons owing to the limited "
    "citation window."
)
