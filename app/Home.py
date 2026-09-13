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
An interactive platform for exploring university publication performance, research
impact, and collaboration patterns from Scopus/QS bibliometric data — built on top of
`src/p36/analysis/`, the same code that answers README Analysis items 3, 6, 9, 14, 16
and 17. Use the sidebar to open each analysis.
"""
)

st.subheader("What each page answers")
guide_cols = st.columns(3)
guide = [
    ("🎯", "Journal Tier / Q1", "3", "What share of output is in Q1 journals, and how does that vary?"),
    ("🔬", "Field Analysis", "6", "Which fields are strongest, improving, or under-performing?"),
    ("🌏", "International Collaboration", "9", "Are internationally co-authored papers cited more? Does it hold within field and year?"),
    ("📈", "Impact Drivers", "14", "Holding other factors constant, which drivers actually move impact?"),
    ("🏆", "Go8 Benchmarking", "16", "How does Sydney compare to Go8 peers on volume, impact, Q1, and collaboration?"),
    ("🔮", "Scenario Analysis", "17", "What would mean impact look like under a hypothetical shift in these drivers?"),
]
for i, (icon, name, item_no, question) in enumerate(guide):
    with guide_cols[i % 3]:
        st.markdown(
            f"**{icon} {name}** <span style='color:{theme.GREY};font-size:0.8rem;'>"
            f"(item {item_no})</span>  \n{question}",
            unsafe_allow_html=True,
        )

theme.rule(theme.YELLOW)

raw = load_raw()
dedup = load_deduplicated()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Publications (raw, per-university)", f"{len(raw):,}")
col2.metric("Publications (deduplicated)", f"{len(dedup):,}")
dup_pct = 100 * (1 - len(dedup) / len(raw))
col3.metric("Cross-university duplication", f"{dup_pct:.1f}%")
col4.metric("Universities", len(GO8_UNIVERSITIES))

theme.rule(theme.YELLOW)

st.subheader("Publications by university (raw)")
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
    st.caption("Same data, as a share of total Go8 output (donut).")
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

st.subheader("Exclusive vs. Go8-shared output, by university")
st.caption(
    "Of each university's raw publication count, how many share an EID with at "
    "least one other Go8 export (a joint Go8 paper) vs. appear under this "
    "university alone. A high shared share means a lot of that university's "
    "output is collaborative within the Go8, not that its total output is "
    "inflated — see data_dictionary.md, Data quality notes."
)
overlap = get_overlap_by_university().reindex(order)
st.dataframe(
    overlap.style.format(
        {
            "raw_publications": "{:,.0f}",
            "shared_with_another_go8_university": "{:,.0f}",
            "exclusive_to_this_university": "{:,.0f}",
            "shared_share": "{:.1%}",
        }
    ),
    width="stretch",
)

theme.rule(theme.YELLOW)

st.subheader("Data provenance")
prov_cols = st.columns(4)
prov_cols[0].metric("Year range", "2020–2024")
prov_cols[1].metric("Data source", "Scopus")
prov_cols[2].metric("Date exported", "14 Aug 2026")
prov_cols[3].metric("Source files", "8 (one per university)")
st.caption(
    "As declared in each export's own metadata block — see data_dictionary.md, "
    "Source files. `Year` is not strictly bounded to this range: 6 rows sit "
    "outside it (2013/2014/2019, negligible) and 429 sit in 2025/2026 (plausible "
    "given the export date, not an error). See MAIN_YEAR_RANGE in p36.config for "
    "how trend charts on this platform handle that."
)

theme.rule(theme.YELLOW)

st.subheader("Data quality notes")
st.markdown(
    f"""
- **Cross-university duplication**: {dup_pct:.1f}% of raw rows are a publication
  already counted under another Go8 university (joint authorship). Per-university
  figures use the raw dataset; any Go8-aggregate figure uses the deduplicated one.
- **Retracted publications** are excluded by default (`p36.config.EXCLUDE_RETRACTED`
  — PROVISIONAL, not yet confirmed by the client).
- **Self-citation share cannot be quantified from this data.** These Scopus
  exports were not filtered for self-citations, and contain no citation-network
  detail (which paper cites which, or by whom) — only aggregate columns
  (`Citations`, `Field-Weighted Citation Impact`, ...). Every citation-based
  figure on this platform may include an unknown share of self-citations; the
  scale cannot be estimated from the columns available.
  `p36.config.EXCLUDE_SELF_CITATIONS` is a placeholder with no filtering logic
  behind it, for exactly this reason.
- **CiteScore / Top-Citation-Percentile columns use "lower is better"** — 1 = top 1%,
  100 = bottom. Verified against Field-Weighted Citation Impact, not assumed.
- Full list: `data/dictionary/data_dictionary.md`, Data quality notes.
"""
)

caveat(
    "Every number in this app reflects definitions marked PROVISIONAL in "
    "docs/methodology.md (Q1 threshold, document-type scope, open-access null "
    "handling, multi-field counting, citation-window trimming) — none of these "
    "have been confirmed by the client yet. Self-citations are handled "
    "separately — see Data quality notes above, not this list. Findings drawn from "
    "any page here should go through .claude/agents/finding-checker.md before "
    "being presented as a conclusion."
)
