import altair as alt
import streamlit as st

import theme
from lib import (
    CLIENT_UNIVERSITY,
    caveat,
    get_collaboration_rate_trend,
    get_fwci_by_collaboration_status,
    get_impact_by_collaboration_breadth,
    get_impact_by_collaboration_status,
    get_impact_gap_by_field,
    get_impact_gap_by_year,
    get_top_countries,
    load_raw,
)
from p36.config import CITATION_WINDOW_TRAILING_YEARS_EXCLUDED

st.set_page_config(page_title="P36 · International Collaboration", page_icon=theme.FAVICON, layout="wide")
theme.inject()
theme.header(
    "International Collaboration Analysis",
    "README Analysis item 9 — are internationally co-authored papers cited more frequently?",
    shape="circle",
    color=theme.BLUE,
)

theme.question_panel(
    [
        ("Do internationally collaborative publications receive higher citation impact?", "done", "ic-status"),
        ("Does the relationship remain after considering research field?", "done", "ic-gap"),
        ("Does the relationship remain after considering publication year?", "done", "ic-gap"),
        ("Are internationally collaborative papers more likely to publish in Q1 journals?", "done", "ic-status"),
        ("Are they more likely to become highly cited?", "done", "ic-status"),
        ("Are they less likely to remain uncited?", "done", "ic-status"),
        ("Does the impact of international collaboration vary across disciplines?", "done", "ic-gap"),
        ("Are some forms of international collaboration more beneficial than others?", "done", "ic-breadth"),
        ("Has Sydney's international collaboration rate increased or declined over time?", "done", "ic-trend"),
    ]
)
st.caption(
    "Q1 / highly-cited / uncited likelihood come from one table (below) — three columns "
    "of the same 'impact by collaboration status' comparison, not three separate charts."
)

st.error(
    "**This does not establish causation.** An observed gap is equally consistent "
    "with international collaboration causing higher impact, or with researchers "
    "who already produce higher-impact work finding it easier to attract "
    "international co-authors. See docs/methodology.md and finding-checker.md.",
    icon="🚫",
)

theme.anchor("ic-status")
st.subheader("Impact by collaboration status")
status = get_impact_by_collaboration_status()
status.index = status.index.map({True: "International", False: "Domestic"})
col1, col2 = st.columns([1, 2])
with col1:
    st.dataframe(
        status.style.format(
            {
                "publications": "{:,.0f}",
                "mean_fwci": "{:.3f}",
                "q1_share": "{:.1%}",
                "top_decile_share": "{:.1%}",
                "uncited_share": "{:.1%}",
            }
        ),
        width="stretch",
    )
with col2:
    status_df = status[["mean_fwci"]].reset_index(names="status")
    status_bar = (
        alt.Chart(status_df)
        .mark_bar()
        .encode(
            x=alt.X("status:N", title=""),
            y=alt.Y("mean_fwci:Q", title="Mean FWCI"),
            color=alt.Color(
                "status:N", legend=None,
                scale=alt.Scale(domain=["International", "Domestic"], range=[theme.RED, theme.BLUE]),
            ),
            tooltip=["status", alt.Tooltip("mean_fwci:Q", format=".3f")],
        )
    )
    st.altair_chart(theme.style(status_bar, height=280), use_container_width=True)

st.caption(
    "The bar above shows means only — FWCI is heavy-tailed, so the two "
    "distributions overlap far more than a bar chart of means suggests:"
)
fwci_status = get_fwci_by_collaboration_status()
fwci_status_labelled = fwci_status.assign(
    status=fwci_status["is_international"].map({True: "International", False: "Domestic"})
)
p95 = fwci_status["Field-Weighted Citation Impact"].quantile(0.95)
box = (
    alt.Chart(fwci_status_labelled)
    .mark_boxplot(outliers=False)
    .encode(
        x=alt.X("status:N", title=""),
        y=alt.Y("Field-Weighted Citation Impact:Q", title="FWCI", scale=alt.Scale(domain=[0, p95])),
        color=alt.Color(
            "status:N", legend=None,
            scale=alt.Scale(domain=["International", "Domestic"], range=[theme.RED, theme.BLUE]),
        ),
    )
)
st.altair_chart(theme.style(box, height=320), use_container_width=True)

theme.rule(theme.YELLOW)

theme.anchor("ic-gap")
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Gap by field")
    st.caption("Checks the finding 'remains after considering research field' rather than assuming it.")
    gap_field = get_impact_gap_by_field().reset_index(names="field")
    gap_chart = (
        alt.Chart(gap_field)
        .mark_bar(color=theme.BLUE)
        .encode(
            y=alt.Y("field:N", title="", sort="-x"),
            x=alt.X("gap:Q", title="International − domestic mean FWCI"),
            tooltip=["field", alt.Tooltip("gap:Q", format=".3f")],
        )
    )
    st.altair_chart(theme.style(gap_chart), use_container_width=True)

with col_b:
    st.subheader("Gap by year")
    st.caption(
        f"Trailing {CITATION_WINDOW_TRAILING_YEARS_EXCLUDED} years excluded by default "
        "(citation-window artefact — see docs/methodology.md)."
    )
    gap_year = get_impact_gap_by_year().reset_index(names="year")
    gap_line = (
        alt.Chart(gap_year)
        .mark_line(color=theme.RED, point=alt.OverlayMarkDef(color=theme.RED, size=100))
        .encode(x=alt.X("year:O", title="Year"), y=alt.Y("gap:Q", title="Gap"), tooltip=["year", alt.Tooltip("gap:Q", format=".3f")])
    )
    st.altair_chart(theme.style(gap_line), use_container_width=True)

theme.rule(theme.YELLOW)

theme.anchor("ic-breadth")
st.subheader("Does more international breadth mean more impact?")
st.caption("Binary international flag can't answer this — bins on the actual country count.")
breadth = get_impact_by_collaboration_breadth()
breadth_df = breadth.reset_index(names="countries")
breadth_df["countries"] = breadth_df["countries"].astype(str)

col_breadth_fwci, col_breadth_q1 = st.columns(2)
with col_breadth_fwci:
    breadth_chart = (
        alt.Chart(breadth_df)
        .mark_bar(color=theme.BLUE)
        .encode(
            x=alt.X("countries:N", title="Distinct co-author countries", sort=None),
            y=alt.Y("mean_fwci:Q", title="Mean FWCI"),
            tooltip=["countries", alt.Tooltip("mean_fwci:Q", format=".3f")],
        )
    )
    st.altair_chart(theme.style(breadth_chart, height=300), use_container_width=True)
with col_breadth_q1:
    breadth_q1_chart = (
        alt.Chart(breadth_df)
        .mark_bar(color=theme.RED)
        .encode(
            x=alt.X("countries:N", title="Distinct co-author countries", sort=None),
            y=alt.Y("q1_share:Q", title="Q1 share", axis=alt.Axis(format="%")),
            tooltip=["countries", alt.Tooltip("q1_share:Q", format=".1%")],
        )
    )
    st.altair_chart(theme.style(breadth_q1_chart, height=300), use_container_width=True)

st.markdown(
    f"Domestic-only papers: **{breadth_df.iloc[0]['mean_fwci']:.2f}** mean FWCI, "
    f"**{breadth_df.iloc[0]['q1_share']:.1%}** Q1 share. 4+ countries: "
    f"**{breadth_df.iloc[-1]['mean_fwci']:.2f}** mean FWCI, **{breadth_df.iloc[-1]['q1_share']:.1%}** Q1 share. "
    "Both climb together with breadth — but see the Impact Drivers page: once Q1 "
    "status is controlled for alongside author/institution count, the "
    "international-collaboration effect on its own shrinks substantially, which "
    "is consistent with much of this breadth pattern running through Q1 "
    "placement rather than being an independent effect of breadth itself."
)

theme.rule(theme.YELLOW)

universities = sorted(load_raw()["source_university"].unique())
university = st.selectbox("University", universities, index=universities.index(CLIENT_UNIVERSITY))

theme.anchor("ic-trend")
col_trend, col_countries = st.columns(2)
with col_trend:
    st.subheader("Collaboration rate over time")
    trend = get_collaboration_rate_trend(university).rename_axis("year").reset_index(name="share")
    trend_line = (
        alt.Chart(trend)
        .mark_line(color=theme.RED, point=alt.OverlayMarkDef(color=theme.BLUE, size=100))
        .encode(
            x=alt.X("year:O", title="Year"),
            y=alt.Y("share:Q", title="International collaboration share", axis=alt.Axis(format="%")),
            tooltip=["year", alt.Tooltip("share:Q", format=".1%")],
        )
    )
    st.altair_chart(theme.style(trend_line), use_container_width=True)

with col_countries:
    st.subheader("Top co-author countries")
    countries = get_top_countries(university, top_n=10)
    countries_df = countries.rename_axis("country").reset_index(name="publications")
    countries_chart = (
        alt.Chart(countries_df)
        .mark_bar(color=theme.BLUE)
        .encode(
            x=alt.X("country:N", title="", sort="-y", axis=alt.Axis(labelAngle=-30)),
            y=alt.Y("publications:Q", title="Publications"),
            tooltip=["country", "publications"],
        )
    )
    st.altair_chart(theme.style(countries_chart), use_container_width=True)

caveat(
    "Every impact comparison here uses Field-Weighted Citation Impact, not raw "
    "Citations — FWCI is already field/year/document-type normalised."
)
