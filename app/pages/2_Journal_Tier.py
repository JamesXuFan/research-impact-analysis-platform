import altair as alt
import pandas as pd
import streamlit as st

import theme
from lib import (
    CLIENT_UNIVERSITY,
    get_citescore_percentile_distribution,
    get_citescore_percentile_series,
    get_impact_by_citescore_quartile,
    get_overperforming_sources,
    get_q1_advantage_by_field,
    get_q1_definition_agreement,
    get_q1_share_by_university,
    get_q1_share_by_year,
    provisional,
)
from p36.config import MAIN_YEAR_RANGE, OVERPERFORMING_SOURCE_MIN_PUBLICATIONS, Q1_CITESCORE_PERCENTILE_MAX

st.set_page_config(page_title="Journal Tier / Q1", page_icon="🎯", layout="wide")
theme.inject()
theme.header(
    "Journal Tier and Q1 Analysis",
    "README Analysis item 3 — what share of output is in Q1 journals, and how does that vary?",
    shape="circle",
    color=theme.BLUE,
)

theme.question_panel(
    [
        ("Do publications in Q1 journals receive more citations than Q2, Q3 or Q4 journals?", "done", "jt-quartile"),
        ("How large is the citation difference between journal tiers?", "done", "jt-quartile"),
        ("Which faculties/fields have the highest success rates in Q1 publishing?", "elsewhere", "/Field_Analysis#fa-q1-share"),
        ("Is the Q1 citation advantage consistent across disciplines, or concentrated in a few?", "done", "jt-consistency"),
        ("Compare highly-cited (top-decile) publication rates across quartiles.", "done", "jt-quartile"),
        ("Compare uncited-publication rates across quartiles.", "done", "jt-quartile"),
        ("Does publishing in Q1 increase the probability of becoming highly cited?", "done", "jt-quartile"),
        ("Which fields have the highest / improving / declining Q1 share?", "elsewhere", "/Field_Analysis#fa-q1-share"),
        ("Are there journals/publications within a tier that receive more citations than expected for that tier?", "done", "jt-overperform"),
    ]
)
st.caption(
    "'Elsewhere' items are answered on the **Field Analysis** page (Q1 share by field, "
    "and its growth trend), not duplicated here — they're field-level, not tier-level, "
    "questions."
)

provisional(
    f"Q1 = source `CiteScore percentile <= {Q1_CITESCORE_PERCENTILE_MAX}`. The direction "
    "(lower percentile = better) is verified against Field-Weighted Citation Impact, not "
    "assumed — but the exact cutoff, and whether Q1 should instead use SJR percentile, "
    "has not been confirmed by the client. See docs/methodology.md."
)

st.subheader("Q1 share by university")
q1_uni = get_q1_share_by_university().sort_values(ascending=False)
q1_uni_df = q1_uni.rename_axis("university").reset_index(name="q1_share")
q1_uni_df["is_client"] = q1_uni_df["university"] == CLIENT_UNIVERSITY
q1_bar = (
    alt.Chart(q1_uni_df)
    .mark_bar()
    .encode(
        y=alt.Y("university:N", title="", sort="-x"),
        x=alt.X("q1_share:Q", title="Q1 share", axis=alt.Axis(format="%")),
        color=alt.Color(
            "is_client:N", legend=None,
            scale=alt.Scale(domain=[True, False], range=[theme.RED, theme.BLUE]),
        ),
        tooltip=["university", alt.Tooltip("q1_share:Q", format=".1%")],
    )
)
st.altair_chart(theme.style(q1_bar, height=280), use_container_width=True)

theme.rule(theme.YELLOW)

st.subheader(f"Q1 share trend ({MAIN_YEAR_RANGE[0]}–{MAIN_YEAR_RANGE[1]})")
q1_year = get_q1_share_by_year()
q1_year_df = q1_year.rename_axis("year").reset_index(name="q1_share")
q1_line = (
    alt.Chart(q1_year_df)
    .mark_line(color=theme.BLUE, point=alt.OverlayMarkDef(color=theme.RED, size=100))
    .encode(
        x=alt.X("year:O", title="Year"),
        y=alt.Y("q1_share:Q", title="Q1 share", axis=alt.Axis(format="%")),
        tooltip=["year", alt.Tooltip("q1_share:Q", format=".1%")],
    )
)
st.altair_chart(theme.style(q1_line, height=300), use_container_width=True)

theme.rule(theme.YELLOW)

theme.anchor("jt-quartile")
st.subheader("Citation performance across Q1–Q4")
st.caption(
    "The binary Q1 flag above collapses Q2, Q3 and Q4 into a single 'not Q1' bucket — "
    "this breaks the same CiteScore-percentile column into all four tiers, for 'compare "
    "citation performance across Q1, Q2, Q3, Q4' and 'measure how large the difference is'."
)
quartile = get_impact_by_citescore_quartile()
quartile_df = quartile.rename_axis("quartile").reset_index()

col_q_fwci, col_q_shares = st.columns(2)
with col_q_fwci:
    q_bar = (
        alt.Chart(quartile_df)
        .mark_bar()
        .encode(
            x=alt.X("quartile:N", title="", sort=["Q1", "Q2", "Q3", "Q4"]),
            y=alt.Y("mean_fwci:Q", title="Mean FWCI"),
            color=alt.Color("quartile:N", legend=None, scale=alt.Scale(domain=["Q1", "Q2", "Q3", "Q4"], range=[theme.BLUE, theme.YELLOW, theme.RED, theme.BLACK])),
            tooltip=["quartile", "publications", alt.Tooltip("mean_fwci:Q", format=".3f")],
        )
    )
    st.altair_chart(theme.style(q_bar, height=300), use_container_width=True)
with col_q_shares:
    st.caption("Highly-cited (top-decile) and uncited shares, same four tiers.")
    shares_long = quartile_df.melt(
        id_vars="quartile", value_vars=["top_decile_share", "uncited_share"], var_name="metric", value_name="share"
    )
    shares_long["metric"] = shares_long["metric"].map({"top_decile_share": "Highly cited", "uncited_share": "Uncited"})
    shares_chart = (
        alt.Chart(shares_long)
        .mark_bar()
        .encode(
            x=alt.X("quartile:N", title="", sort=["Q1", "Q2", "Q3", "Q4"]),
            y=alt.Y("share:Q", title="Share of publications", axis=alt.Axis(format="%")),
            color=alt.Color("metric:N", title="", scale=alt.Scale(domain=["Highly cited", "Uncited"], range=[theme.BLUE, theme.RED])),
            xOffset="metric:N",
            tooltip=["quartile", "metric", alt.Tooltip("share:Q", format=".1%")],
        )
    )
    st.altair_chart(theme.style(shares_chart, height=300), use_container_width=True)

st.markdown(
    f"**Q1 → Q4**, mean FWCI falls **{quartile.loc['Q1', 'mean_fwci']:.2f} → {quartile.loc['Q4', 'mean_fwci']:.2f}**, "
    f"highly-cited share **{quartile.loc['Q1', 'top_decile_share']:.1%} → {quartile.loc['Q4', 'top_decile_share']:.1%}**, "
    f"uncited share **{quartile.loc['Q1', 'uncited_share']:.1%} → {quartile.loc['Q4', 'uncited_share']:.1%}** — "
    "monotonic across all three metrics, not just a Q1-vs-the-rest step. That answers "
    "'does publishing in Q1 increase the probability of becoming highly cited' directly: "
    "yes, and the same gradient continues through Q2/Q3/Q4, it isn't a Q1-only cliff edge."
)

theme.rule(theme.YELLOW)

theme.anchor("jt-consistency")
st.subheader("Is the Q1 advantage consistent across disciplines?")
st.caption(
    "Q1-minus-non-Q1 mean-FWCI gap, computed separately within each field — the same "
    "stratification check used on the International Collaboration page, applied here to "
    "'is the Q1 advantage consistent across disciplines' rather than assumed from the "
    "aggregate gap alone."
)
advantage = get_q1_advantage_by_field().reset_index(names="field")
advantage_chart = (
    alt.Chart(advantage)
    .mark_bar(color=theme.BLUE)
    .encode(
        y=alt.Y("field:N", title="", sort="-x"),
        x=alt.X("gap:Q", title="Q1 − non-Q1 mean FWCI gap"),
        tooltip=["field", alt.Tooltip("gap:Q", format=".3f")],
    )
)
st.altair_chart(theme.style(advantage_chart, height=max(240, 24 * len(advantage))), use_container_width=True)
st.caption(
    f"Every field shows a positive gap (range {advantage['gap'].min():.2f}–{advantage['gap'].max():.2f}) "
    "— the Q1 advantage holds in every field in this dataset, though its *size* varies "
    f"{advantage['gap'].max() / advantage['gap'].min():.1f}× between the strongest and weakest field."
    if (advantage["gap"] > 0).all()
    else "Not every field shows the same direction — see the chart for which fields are the exception."
)

theme.rule(theme.YELLOW)

st.subheader("CiteScore percentile distribution")
st.caption(
    "Remember: lower is better. The right-skew here — most publications cluster "
    "toward 1 — is exactly what confirmed the percentile direction in the first "
    "place (see docs/methodology.md): it means Go8 output disproportionately sits "
    "in high-CiteScore journals, not that percentiles are uniformly spread."
)
series = get_citescore_percentile_series()
hist_df = series.to_frame("citescore_percentile")
histogram = (
    alt.Chart(hist_df)
    .mark_bar(color=theme.BLUE)
    .encode(
        x=alt.X("citescore_percentile:Q", bin=alt.Bin(maxbins=50), title="CiteScore percentile (lower = better)"),
        y=alt.Y("count():Q", title="Publications"),
    )
)
threshold_rule = (
    alt.Chart(pd.DataFrame({"x": [Q1_CITESCORE_PERCENTILE_MAX]}))
    .mark_rule(color=theme.RED, strokeWidth=3, strokeDash=[6, 4])
    .encode(x="x:Q")
)
st.altair_chart(theme.style(histogram + threshold_rule, height=320), use_container_width=True)
st.caption(f"Dashed red line: Q1 threshold ({Q1_CITESCORE_PERCENTILE_MAX}).")

desc = get_citescore_percentile_distribution()
st.dataframe(desc.to_frame("CiteScore percentile").T, width="stretch")

theme.rule(theme.YELLOW)

theme.anchor("jt-overperform")
st.subheader("Do individual journals over- or under-perform their own tier?")
st.caption(
    "The previously-unaddressed sub-question: a tier average can hide individual sources "
    "that punch well above or below it. Per-source (Scopus source title) mean FWCI minus "
    f"its own quartile's mean FWCI, restricted to sources with at least "
    f"{OVERPERFORMING_SOURCE_MIN_PUBLICATIONS} publications in that quartile so a single "
    "highly-cited paper can't make a small source look like an outlier."
)
sources = get_overperforming_sources()
tab_over, tab_under = st.tabs(["Strongest over-performers", "Strongest under-performers"])
with tab_over:
    top_sources = sources.nlargest(12, "gap")
    over_chart = (
        alt.Chart(top_sources)
        .mark_bar(color=theme.BLUE)
        .encode(
            y=alt.Y("source:N", title="", sort="-x"),
            x=alt.X("gap:Q", title="Source mean FWCI − its quartile's mean FWCI"),
            tooltip=["source", "quartile", "publications", alt.Tooltip("mean_fwci:Q", format=".2f"), alt.Tooltip("gap:Q", format=".2f")],
        )
    )
    st.altair_chart(theme.style(over_chart, height=360), use_container_width=True)
with tab_under:
    bottom_sources = sources.nsmallest(12, "gap")
    under_chart = (
        alt.Chart(bottom_sources)
        .mark_bar(color=theme.RED)
        .encode(
            y=alt.Y("source:N", title="", sort="x"),
            x=alt.X("gap:Q", title="Source mean FWCI − its quartile's mean FWCI"),
            tooltip=["source", "quartile", "publications", alt.Tooltip("mean_fwci:Q", format=".2f"), alt.Tooltip("gap:Q", format=".2f")],
        )
    )
    st.altair_chart(theme.style(under_chart, height=360), use_container_width=True)
st.caption(
    f"{len(sources):,} (quartile, source) pairs clear the {OVERPERFORMING_SOURCE_MIN_PUBLICATIONS}-publication "
    "floor. This is descriptive, not a recommendation — a source's gap here can reflect genuine "
    "editorial quality, a narrow high-citation-culture sub-field, or a handful of outlier papers "
    "even past the publication floor; treat it as a shortlist to investigate, not a verdict."
)

theme.rule(theme.YELLOW)

st.subheader("Does the Q1 basis actually matter? CiteScore vs. SJR")
st.caption(
    "The open question flagged above, answered with actual numbers instead of "
    "left abstract: restricted to publications with both percentiles present, "
    "how often would classifying Q1 by SJR percentile instead of CiteScore "
    "percentile change the answer?"
)
agreement = get_q1_definition_agreement()
a1, a2, a3, a4 = st.columns(4)
a1.metric("Both call it Q1", f"{agreement['both_q1']:,}")
a2.metric("CiteScore Q1 only", f"{agreement['citescore_only']:,}")
a3.metric("SJR Q1 only", f"{agreement['sjr_only']:,}")
a4.metric("Neither", f"{agreement['neither']:,}")
disagreement_n = agreement["citescore_only"] + agreement["sjr_only"]
st.markdown(
    f"**{agreement['agreement_rate']:.1%} agreement** across {agreement['n']:,} publications with both "
    f"percentiles present — {disagreement_n:,} publications ({disagreement_n / agreement['n']:.1%}) would "
    "flip Q1 status depending on which basis is used. That's the size of the "
    "uncertainty behind every Q1 share on this page until the client confirms "
    "which basis to use."
)
