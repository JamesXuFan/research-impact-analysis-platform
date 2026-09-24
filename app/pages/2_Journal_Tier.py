import altair as alt
import pandas as pd
import streamlit as st

import theme
from lib.journal_tier import (
    CLIENT_UNIVERSITY,
    get_citescore_percentile_distribution,
    get_citescore_percentile_series,
    get_field_summary,
    get_impact_by_citescore_quartile,
    get_overperforming_sources,
    get_q1_advantage_by_field,
    get_q1_definition_agreement,
    get_q1_share_by_university,
    get_q1_share_by_year,
    get_q1_share_change_by_field,
    provisional,
)
from p36.config import MAIN_YEAR_RANGE, OVERPERFORMING_SOURCE_MIN_PUBLICATIONS, Q1_CITESCORE_PERCENTILE_MAX

st.set_page_config(page_title="P36 · Journal Tier / Q1", page_icon=theme.FAVICON, layout="wide")
theme.inject()
theme.header(
    "Journal Tier and Q1 Analysis",
    "Analysis item 3 — what share of output is in Q1 journals, and how does that vary?",
    shape="circle",
    color=theme.BLUE,
)

theme.question_panel(
    [
        ("Do publications in Q1 journals receive more citations than Q2, Q3 or Q4 journals?", "done", "jt-quartile"),
        ("How large is the citation difference between journal tiers?", "done", "jt-quartile"),
        ("Which faculties/fields have the highest success rates in Q1 publishing?", "done", "jt-field-q1"),
        ("Is the Q1 citation advantage consistent across disciplines, or concentrated in a few?", "done", "jt-consistency"),
        ("Compare highly-cited (top-decile) publication rates across quartiles.", "done", "jt-quartile"),
        ("Compare uncited-publication rates across quartiles.", "done", "jt-quartile"),
        ("Does publishing in Q1 increase the probability of becoming highly cited?", "done", "jt-quartile"),
        ("Which fields have the highest / improving / declining Q1 share?", "done", "jt-field-q1"),
        ("Are there journals/publications within a tier that receive more citations than expected for that tier?", "done", "jt-overperform"),
    ]
)
st.caption(
    "Q1 shares by field are reported further below, alongside the analysis by journal tier."
)

provisional(
    f"A publication is classified as Q1 when its source lies within the top {Q1_CITESCORE_PERCENTILE_MAX}% "
    "of its field by CiteScore percentile. The final section compares this classification "
    "with one based on the SJR percentile to assess its sensitivity."
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
        x=alt.X("q1_share:Q", title="Share in Q1 journals", axis=alt.Axis(format="%")),
        color=alt.Color(
            "is_client:N", legend=None,
            scale=alt.Scale(domain=[True, False], range=[theme.RED, theme.BLUE]),
        ),
        tooltip=["university", alt.Tooltip("q1_share:Q", format=".1%")],
    )
)
st.altair_chart(theme.style(q1_bar, height=280), use_container_width=True)

theme.rule(theme.YELLOW)

st.subheader(f"Q1 share over time ({MAIN_YEAR_RANGE[0]}–{MAIN_YEAR_RANGE[1]})")
q1_year = get_q1_share_by_year()
q1_year_df = q1_year.rename_axis("year").reset_index(name="q1_share")
q1_line = (
    alt.Chart(q1_year_df)
    .mark_line(color=theme.BLUE, point=alt.OverlayMarkDef(color=theme.RED, size=100))
    .encode(
        x=alt.X("year:O", title="Year"),
        y=alt.Y("q1_share:Q", title="Share in Q1 journals", axis=alt.Axis(format="%")),
        tooltip=["year", alt.Tooltip("q1_share:Q", format=".1%")],
    )
)
st.altair_chart(theme.style(q1_line, height=300), use_container_width=True)

theme.rule(theme.YELLOW)

theme.anchor("jt-quartile")
st.subheader("Citation performance across Q1–Q4")
st.caption(
    "The binary Q1 indicator above pools Q2, Q3 and Q4 as 'not Q1'; the four quartiles "
    "are disaggregated here."
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
            y=alt.Y("mean_fwci:Q", title="Citation impact (FWCI)"),
            color=alt.Color("quartile:N", legend=None, scale=alt.Scale(domain=["Q1", "Q2", "Q3", "Q4"], range=[theme.BLUE, theme.YELLOW, theme.RED, theme.BLACK])),
            tooltip=["quartile", "publications", alt.Tooltip("mean_fwci:Q", format=".3f")],
        )
    )
    st.altair_chart(theme.style(q_bar, height=300), use_container_width=True)
with col_q_shares:
    st.caption("Proportions of highly cited (top decile) and uncited publications, by quartile.")
    shares_long = quartile_df.melt(
        id_vars="quartile", value_vars=["top_decile_share", "uncited_share"], var_name="metric", value_name="share"
    )
    shares_long["metric"] = shares_long["metric"].map({"top_decile_share": "Highly cited", "uncited_share": "Never cited"})
    shares_chart = (
        alt.Chart(shares_long)
        .mark_bar()
        .encode(
            x=alt.X("quartile:N", title="", sort=["Q1", "Q2", "Q3", "Q4"]),
            y=alt.Y("share:Q", title="Share of publications", axis=alt.Axis(format="%")),
            color=alt.Color("metric:N", title="", scale=alt.Scale(domain=["Highly cited", "Never cited"], range=[theme.BLUE, theme.RED])),
            xOffset="metric:N",
            tooltip=["quartile", "metric", alt.Tooltip("share:Q", format=".1%")],
        )
    )
    st.altair_chart(theme.style(shares_chart, height=300), use_container_width=True)

st.markdown(
    f"From Q1 to Q4, mean FWCI declines from **{quartile.loc['Q1', 'mean_fwci']:.2f}** to **{quartile.loc['Q4', 'mean_fwci']:.2f}**, "
    f"the highly cited share changes from **{quartile.loc['Q1', 'top_decile_share']:.1%}** to **{quartile.loc['Q4', 'top_decile_share']:.1%}**, "
    f"and the uncited share changes from **{quartile.loc['Q1', 'uncited_share']:.1%}** to **{quartile.loc['Q4', 'uncited_share']:.1%}**. "
    "All three indicators vary monotonically across quartiles, so the advantage is not confined "
    "to a Q1 versus non-Q1 contrast. Publication in a Q1 source is associated with a higher "
    "probability of being highly cited."
)

theme.rule(theme.YELLOW)

theme.anchor("jt-field-q1")
st.subheader("Q1 share by field")
st.caption(
    "The left panel reports the Q1 share by field. The right panel reports the change in that "
    "share between the first and second half of the period, in percentage points."
)
field_summary = get_field_summary()
col_field_level, col_field_trend = st.columns(2)
with col_field_level:
    field_q1_df = field_summary[["q1_share"]].reset_index(names="field")
    field_q1_chart = (
        alt.Chart(field_q1_df)
        .mark_bar(color=theme.BLUE)
        .encode(
            y=alt.Y("field:N", title="", sort="-x"),
            x=alt.X("q1_share:Q", title="Share in Q1 journals", axis=alt.Axis(format="%")),
            tooltip=["field", alt.Tooltip("q1_share:Q", format=".1%")],
        )
    )
    st.altair_chart(theme.style(field_q1_chart, height=max(240, 24 * len(field_q1_df))), use_container_width=True)
with col_field_trend:
    field_q1_change = get_q1_share_change_by_field().rename_axis("field").reset_index(name="change")
    field_q1_change_chart = (
        alt.Chart(field_q1_change)
        .mark_bar()
        .encode(
            y=alt.Y("field:N", title="", sort="-x"),
            x=alt.X("change:Q", title="Change in Q1 share (percentage points)", axis=alt.Axis(format="+.0%")),
            color=alt.Color(
                "change:Q", legend=None,
                scale=theme.diverging_scale(field_q1_change["change"].min(), field_q1_change["change"].max()),
            ),
            tooltip=["field", alt.Tooltip("change:Q", format="+.1%")],
        )
    )
    st.altair_chart(theme.style(field_q1_change_chart, height=max(240, 24 * len(field_q1_change))), use_container_width=True)

theme.rule(theme.YELLOW)

theme.anchor("jt-consistency")
st.subheader("Is the Q1 advantage consistent across disciplines?")
st.caption(
    "The difference in mean FWCI between Q1 and non-Q1 publications, estimated within each "
    "field, to test whether the advantage is consistent across disciplines rather than "
    "concentrated in a few."
)
advantage = get_q1_advantage_by_field().reset_index(names="field")
advantage_chart = (
    alt.Chart(advantage)
    .mark_bar(color=theme.BLUE)
    .encode(
        y=alt.Y("field:N", title="", sort="-x"),
        x=alt.X("gap:Q", title="Citation impact gap (Q1 minus non-Q1)"),
        tooltip=["field", alt.Tooltip("gap:Q", format=".3f")],
    )
)
st.altair_chart(theme.style(advantage_chart, height=max(240, 24 * len(advantage))), use_container_width=True)
st.caption(
    f"The gap is positive in every field (range {advantage['gap'].min():.2f}–{advantage['gap'].max():.2f}), "
    "indicating that the Q1 advantage is present across all fields, although its magnitude varies "
    f"by a factor of approximately {advantage['gap'].max() / advantage['gap'].min():.1f} between the largest and smallest."
    if (advantage["gap"] > 0).all()
    else "The direction of the gap is not uniform across fields; exceptions are visible in the chart."
)

theme.rule(theme.YELLOW)

st.subheader("Distribution of CiteScore percentile")
st.caption(
    "Lower values indicate a higher ranking (1 = top). The distribution is concentrated near 1, "
    "indicating that Go8 output is disproportionately published in highly ranked sources."
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
st.caption(f"The dashed red line marks the Q1 threshold (percentile {Q1_CITESCORE_PERCENTILE_MAX}).")

desc = get_citescore_percentile_distribution()
st.table(desc.to_frame("CiteScore percentile").T)

theme.rule(theme.YELLOW)

theme.anchor("jt-overperform")
st.subheader("Sources deviating from their tier average")
st.caption(
    "A tier mean can conceal sources that perform well above or below it. Each source's mean "
    "FWCI is compared with the mean of its own quartile. To limit the influence of individual "
    f"papers, only sources with at least {OVERPERFORMING_SOURCE_MIN_PUBLICATIONS} publications "
    "in the quartile are included."
)
sources = get_overperforming_sources()
tab_over, tab_under = st.tabs(["Positive deviation", "Negative deviation"])
with tab_over:
    top_sources = sources.nlargest(12, "gap")
    over_chart = (
        alt.Chart(top_sources)
        .mark_bar(color=theme.BLUE)
        .encode(
            y=alt.Y("source:N", title="", sort="-x"),
            x=alt.X("gap:Q", title="Citation impact gap versus own tier"),
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
            x=alt.X("gap:Q", title="Citation impact gap versus own tier"),
            tooltip=["source", "quartile", "publications", alt.Tooltip("mean_fwci:Q", format=".2f"), alt.Tooltip("gap:Q", format=".2f")],
        )
    )
    st.altair_chart(theme.style(under_chart, height=360), use_container_width=True)
st.caption(
    f"{len(sources):,} source–quartile combinations meet the minimum of {OVERPERFORMING_SOURCE_MIN_PUBLICATIONS} publications. "
    "The results are descriptive. A deviation may reflect editorial quality, the citation "
    "practices of a specific sub-field, or a small number of outlying papers, and should be "
    "interpreted as a basis for further investigation rather than as a conclusion."
)

theme.rule(theme.YELLOW)

st.subheader("Sensitivity of Q1 classification: CiteScore and SJR")
st.caption(
    "For publications with both percentiles available, the table reports the frequency with "
    "which the two classification bases agree on Q1 status."
)
agreement = get_q1_definition_agreement()
a1, a2, a3, a4 = st.columns(4)
a1.metric("Both call it Q1", f"{agreement['both_q1']:,}")
a2.metric("Q1 by CiteScore only", f"{agreement['citescore_only']:,}")
a3.metric("Q1 by SJR only", f"{agreement['sjr_only']:,}")
a4.metric("Neither", f"{agreement['neither']:,}")
disagreement_n = agreement["citescore_only"] + agreement["sjr_only"]
st.markdown(
    f"**The two bases agree for {agreement['agreement_rate']:.1%}** of the {agreement['n']:,} publications "
    f"with both percentiles available. {disagreement_n:,} publications ({disagreement_n / agreement['n']:.1%}) "
    "would change Q1 status depending on the basis used, which indicates the sensitivity of the "
    "Q1 figures on this page to the choice of classification."
)
