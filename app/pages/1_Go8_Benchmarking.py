import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import theme
from lib.go8_benchmarking import (
    CLIENT_UNIVERSITY,
    caveat,
    get_benchmark_summary,
    get_field_gap_vs_peers,
    get_growth_by_university,
    get_journal_pattern,
    get_top_countries,
    load_raw,
)

METRIC_LABELS = {
    "publications": "Publications",
    "mean_fwci": "Citation impact (FWCI)",
    "q1_share": "Share in Q1 journals",
    "top_decile_share": "Share highly cited",
    "international_collaboration_share": "Share with international co-authors",
    "mean_institutions_per_paper": "Institutions per paper",
}

st.set_page_config(page_title="P36 · Go8 Benchmarking", page_icon=theme.FAVICON, layout="wide")
theme.inject()
theme.header(
    "Go8 / Peer Benchmarking",
    "Analysis item 16 — how is Sydney performing relative to its Go8 peers?",
    shape="square",
    color=theme.RED,
)

theme.question_panel(
    [
        ("How does Sydney compare in publication volume?", "done", "go8-rank"),
        ("How does citation impact compare?", "done", "go8-rank"),
        ("How does Q1 publication share compare?", "done", "go8-rank"),
        ("How does highly cited publication performance compare?", "done", "go8-rank"),
        ("How does international collaboration compare?", "done", "go8-rank"),
        ("How does institutional collaboration compare?", "done", "go8-rank"),
        ("Which research fields are Sydney's strongest relative to peers? Where are the largest gaps?", "done", "go8-fields"),
        ("Which Go8 universities are improving most rapidly?", "done", "go8-growth"),
        ("Are competitors using different journal-publishing patterns?", "done", "go8-countries-patterns"),
        ("Are competitors collaborating with different countries or institutions?", "partial", "go8-countries-patterns"),
        ("Which performance gaps appear realistically addressable?", "partial", "go8-fields"),
    ]
)
st.caption(
    "Two questions are addressed in part. Partner countries are reported for one university at "
    "a time, and no breakdown by partner institution is provided. The extent to which a gap is "
    "realistically addressable is a matter of judgement; the field-level comparison below is "
    "the principal evidence."
)

summary = get_benchmark_summary()

theme.anchor("go8-rank")
st.subheader("Sydney's rank within the Go8")
rank_metrics = ["publications", "mean_fwci", "q1_share", "top_decile_share", "international_collaboration_share", "mean_institutions_per_paper"]
for row_start in range(0, len(rank_metrics), 3):
    for col, m in zip(st.columns(3), rank_metrics[row_start:row_start + 3]):
        rank = int(summary[m].rank(ascending=False).loc[CLIENT_UNIVERSITY])
        col.metric(METRIC_LABELS[m], f"#{rank} of 8")
st.caption("Rank 1 denotes the highest value among the eight Go8 universities on that measure.")

theme.rule(theme.YELLOW)

st.subheader("Benchmark summary")
st.table(
    summary.rename_axis("University").rename(columns=METRIC_LABELS).style.format(
        {
            "Publications": "{:,.0f}",
            "Citation impact (FWCI)": "{:.3f}",
            "Share in Q1 journals": "{:.1%}",
            "Share highly cited": "{:.1%}",
            "Share with international co-authors": "{:.1%}",
            "Institutions per paper": "{:.2f}",
        }
    ),
)

metric_choice = st.selectbox(
    "Compare the universities on:",
    ["publications", "mean_fwci", "q1_share", "top_decile_share", "international_collaboration_share", "mean_institutions_per_paper"],
    format_func=lambda c: METRIC_LABELS[c],
)
bar_df = summary[[metric_choice]].reset_index(names="university")
bar_df["is_client"] = bar_df["university"] == CLIENT_UNIVERSITY
bar = (
    alt.Chart(bar_df)
    .mark_bar()
    .encode(
        x=alt.X("university:N", title="", sort="-y", axis=alt.Axis(labelAngle=-30)),
        y=alt.Y(f"{metric_choice}:Q", title=METRIC_LABELS[metric_choice]),
        color=alt.Color(
            "is_client:N", legend=None,
            scale=alt.Scale(domain=[True, False], range=[theme.RED, theme.BLUE]),
        ),
        tooltip=["university", metric_choice],
    )
)
st.altair_chart(theme.style(bar), use_container_width=True)

theme.rule(theme.YELLOW)

st.subheader("Sydney relative to the Go8 peer average")
st.caption(
    "Each measure is min–max scaled across the eight universities (0 = lowest, 1 = highest) "
    "so that measures with different units can be displayed together. The profile indicates "
    "whether performance is uniformly intermediate or uneven across dimensions."
)
radar_metrics = ["publications", "mean_fwci", "q1_share", "top_decile_share", "international_collaboration_share", "mean_institutions_per_paper"]
RADAR_LABELS = {
    "publications": "Publications",
    "mean_fwci": "Citation impact",
    "q1_share": "Q1 share",
    "top_decile_share": "Highly cited share",
    "international_collaboration_share": "International co-authorship",
    "mean_institutions_per_paper": "Institutions per paper",
}
radar_labels = [RADAR_LABELS[m] for m in radar_metrics]
normalised = (summary[radar_metrics] - summary[radar_metrics].min()) / (
    summary[radar_metrics].max() - summary[radar_metrics].min()
)
sydney_values = normalised.loc[CLIENT_UNIVERSITY].tolist()
peer_values = normalised.drop(index=CLIENT_UNIVERSITY).mean().tolist()

n = len(radar_metrics)
angles = [2 * np.pi * i / n - np.pi / 2 for i in range(n)]

def _radar_points(series_name: str, values: list[float]) -> list[dict]:
    pts = list(zip(values, angles, radar_labels))
    pts.append(pts[0])
    return [
        {"series": series_name, "order": i, "metric": label, "r": r, "x": r * np.cos(a), "y": r * np.sin(a)}
        for i, (r, a, label) in enumerate(pts)
    ]

radar_df = pd.DataFrame(_radar_points("Go8 peer average", peer_values) + _radar_points("Sydney", sydney_values))

spokes_df = pd.DataFrame(
    [{"metric": label, "x": np.cos(a), "y": np.sin(a), "x0": 0.0, "y0": 0.0} for a, label in zip(angles, radar_labels)]
)
label_df = pd.DataFrame(
    [{"metric": label, "x": 1.22 * np.cos(a), "y": 1.22 * np.sin(a)} for a, label in zip(angles, radar_labels)]
)
boundary_df = pd.DataFrame(
    [{"t": i, "x": np.cos(t), "y": np.sin(t)} for i, t in enumerate(np.linspace(0, 2 * np.pi, 100))]
)

spokes = alt.Chart(spokes_df).mark_rule(color="#8C8C86", strokeWidth=1).encode(
    x=alt.X("x0:Q", axis=None, scale=alt.Scale(domain=[-1.55, 1.55])),
    y=alt.Y("y0:Q", axis=None, scale=alt.Scale(domain=[-1.55, 1.55])),
    x2="x:Q", y2="y:Q",
)
boundary = alt.Chart(boundary_df).mark_line(color="#8C8C86", strokeWidth=1, point=False).encode(
    x=alt.X("x:Q", axis=None, scale=alt.Scale(domain=[-1.55, 1.55])),
    y=alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[-1.55, 1.55])),
    order="t:Q",
)
labels = alt.Chart(label_df).mark_text(font=theme.FONT_BODY, fontSize=11, fontWeight="bold", color=theme.BLACK).encode(
    x="x:Q", y="y:Q", text="metric:N"
)
radar_shapes = (
    alt.Chart(radar_df)
    .mark_line(strokeWidth=3, point=alt.OverlayMarkDef(filled=True, size=60))
    .encode(
        x="x:Q", y="y:Q",
        order="order:Q",
        color=alt.Color(
            "series:N", title="",
            scale=alt.Scale(domain=["Sydney", "Go8 peer average"], range=[theme.RED, theme.BLUE]),
        ),
        tooltip=["series", "metric", alt.Tooltip("r:Q", format=".2f")],
    )
)
radar_fill = (
    alt.Chart(radar_df)
    .mark_line(filled=True, opacity=0.15, strokeWidth=0, point=False, interpolate="linear-closed")
    .encode(
        x="x:Q", y="y:Q", order="order:Q",
        color=alt.Color("series:N", legend=None, scale=alt.Scale(domain=["Sydney", "Go8 peer average"], range=[theme.RED, theme.BLUE])),
    )
)
radar_chart = (boundary + spokes + radar_fill + radar_shapes + labels).properties(width=520, height=520).configure_view(strokeWidth=0)
_, radar_col, _ = st.columns([1, 3, 1])
with radar_col:
    st.altair_chart(radar_chart, use_container_width=False)
    st.markdown(
        f"<span style='color:{theme.RED};font-weight:700;'>Red</span>: Sydney"
        "<br><br>"
        f"<span style='color:{theme.BLUE};font-weight:700;'>Blue</span>: mean of the other seven Go8 universities",
        unsafe_allow_html=True,
    )

theme.rule(theme.YELLOW)

theme.anchor("go8-growth")
st.subheader("Growth in publication output")
st.caption(
    "Cumulative change over the full period; this is not an annual growth rate."
)
growth = get_growth_by_university()
growth_df = growth.rename_axis("university").reset_index(name="growth")
growth_df["is_client"] = growth_df["university"] == CLIENT_UNIVERSITY
growth_bar = (
    alt.Chart(growth_df)
    .mark_bar()
    .encode(
        y=alt.Y("university:N", title="", sort="-x"),
        x=alt.X("growth:Q", title="Growth over the period", axis=alt.Axis(format="%")),
        color=alt.Color(
            "is_client:N", legend=None,
            scale=alt.Scale(domain=[True, False], range=[theme.RED, theme.BLUE]),
        ),
        tooltip=["university", alt.Tooltip("growth:Q", format=".1%")],
    )
)
st.altair_chart(theme.style(growth_bar, height=280), use_container_width=True)

theme.rule(theme.YELLOW)

theme.anchor("go8-fields")
st.subheader("Field-level citation impact relative to Go8 peers")
st.caption("Difference between Sydney's mean FWCI and the Go8 peer mean, by field. Positive values indicate that Sydney exceeds the peer average.")
gap = get_field_gap_vs_peers()
gap_df = gap.reset_index(names="field")
gap_chart = (
    alt.Chart(gap_df)
    .mark_bar()
    .encode(
        y=alt.Y("field:N", title="", sort="-x"),
        x=alt.X("gap:Q", title="Citation impact gap (Sydney minus peer average)"),
        color=alt.Color("gap:Q", legend=None, scale=theme.diverging_scale(gap_df["gap"].min(), gap_df["gap"].max())),
        tooltip=["field", alt.Tooltip("gap:Q", format=".3f")],
    )
)
st.altair_chart(theme.style(gap_chart, height=max(280, 24 * len(gap_df))), use_container_width=True)

top5 = gap_df.nlargest(5, "gap")
bottom5 = gap_df.nsmallest(5, "gap")
col_strength, col_weak = st.columns(2)
with col_strength:
    st.markdown("**Sydney's 5 largest advantages**")
    for _, row in top5.iterrows():
        st.markdown(f"- {row['field']} — <span style='color:{theme.BLUE};font-weight:700;'>+{row['gap']:.3f}</span>", unsafe_allow_html=True)
with col_weak:
    st.markdown("**Sydney's 5 largest gaps**")
    for _, row in bottom5.iterrows():
        sign = "+" if row["gap"] >= 0 else ""
        color = theme.BLUE if row["gap"] >= 0 else theme.RED
        st.markdown(f"- {row['field']} — <span style='color:{color};font-weight:700;'>{sign}{row['gap']:.3f}</span>", unsafe_allow_html=True)

theme.rule(theme.YELLOW)

theme.anchor("go8-countries-patterns")
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("International co-author countries")
    raw = load_raw()
    university = st.selectbox("University", sorted(raw["source_university"].unique()), index=0)
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
    st.altair_chart(theme.style(countries_chart, height=320), use_container_width=True)

with col_b:
    st.subheader("Journal-publishing pattern by university")
    st.caption("Distribution of each university's output by source type.")
    patterns = get_journal_pattern()
    st.table(patterns.style.format("{:.1%}"))
