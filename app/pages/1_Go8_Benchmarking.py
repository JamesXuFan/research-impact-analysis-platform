import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import theme
from lib_go8_benchmarking import (
    CLIENT_UNIVERSITY,
    caveat,
    get_benchmark_summary,
    get_field_gap_vs_peers,
    get_growth_by_university,
    get_journal_pattern,
    get_top_countries,
    load_raw,
)

st.set_page_config(page_title="P36 · Go8 Benchmarking", page_icon=theme.FAVICON, layout="wide")
theme.inject()
theme.header(
    "Go8 / Peer Benchmarking",
    "README Analysis item 16 — how is Sydney performing relative to its Go8 peers?",
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
    "'Different countries or institutions' is only answered for countries (co-author-country "
    "chart below, one university at a time) — no per-university partner-*institution* "
    "breakdown is built. 'Realistically addressable gaps' is a judgement call the field-gap "
    "chart below is the input for, not a chart on its own."
)

summary = get_benchmark_summary()

theme.anchor("go8-rank")
st.subheader("Sydney's rank within the Go8")
rank_metrics = ["publications", "mean_fwci", "q1_share", "top_decile_share", "international_collaboration_share", "mean_institutions_per_paper"]
rank_cols = st.columns(len(rank_metrics))
for col, m in zip(rank_cols, rank_metrics):
    rank = int(summary[m].rank(ascending=False).loc[CLIENT_UNIVERSITY])
    col.metric(m.replace("_", " ").title(), f"#{rank} of 8")
st.caption("Rank 1 = highest of the 8 Go8 universities on that metric, computed live from the table below.")

theme.rule(theme.YELLOW)

st.subheader("Benchmark summary")
st.dataframe(
    summary.style.format(
        {
            "publications": "{:,.0f}",
            "mean_fwci": "{:.3f}",
            "q1_share": "{:.1%}",
            "top_decile_share": "{:.1%}",
            "international_collaboration_share": "{:.1%}",
            "mean_institutions_per_paper": "{:.2f}",
        }
    ),
    width="stretch",
)

metric_choice = st.selectbox(
    "Compare universities on:",
    ["publications", "mean_fwci", "q1_share", "top_decile_share", "international_collaboration_share", "mean_institutions_per_paper"],
    format_func=lambda c: c.replace("_", " ").title(),
)
bar_df = summary[[metric_choice]].reset_index(names="university")
bar_df["is_client"] = bar_df["university"] == CLIENT_UNIVERSITY
bar = (
    alt.Chart(bar_df)
    .mark_bar()
    .encode(
        x=alt.X("university:N", title="", sort="-y", axis=alt.Axis(labelAngle=-30)),
        y=alt.Y(f"{metric_choice}:Q", title=metric_choice.replace("_", " ").title()),
        color=alt.Color(
            "is_client:N", legend=None,
            scale=alt.Scale(domain=[True, False], range=[theme.RED, theme.BLUE]),
        ),
        tooltip=["university", metric_choice],
    )
)
st.altair_chart(theme.style(bar), use_container_width=True)

theme.rule(theme.YELLOW)

st.subheader("Sydney vs. Go8-peer average, across dimensions")
st.caption(
    "Each axis min-max scaled across all 8 universities (0 = lowest of the Go8, "
    "1 = highest) so metrics with very different units (raw publication counts vs. "
    "shares) can sit on one chart. Reveals shape, not just single-number gaps — "
    "e.g. an all-round-mid-table profile looks very different from a spiky one "
    "even at the same average rank. Vega-Lite has no polar coordinate system, so "
    "this is manually projected from (share, angle) to (x, y)."
)
radar_metrics = ["publications", "mean_fwci", "q1_share", "top_decile_share", "international_collaboration_share", "mean_institutions_per_paper"]
radar_labels = [m.replace("_", " ").title() for m in radar_metrics]
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
    [{"metric": label, "x": 1.28 * np.cos(a), "y": 1.28 * np.sin(a)} for a, label in zip(angles, radar_labels)]
)
boundary_df = pd.DataFrame(
    [{"x": np.cos(t), "y": np.sin(t)} for t in np.linspace(0, 2 * np.pi, 100)]
)

spokes = alt.Chart(spokes_df).mark_rule(color="#C9C4B8", strokeWidth=1).encode(
    x=alt.X("x0:Q", axis=None, scale=alt.Scale(domain=[-1.5, 1.5])),
    y=alt.Y("y0:Q", axis=None, scale=alt.Scale(domain=[-1.5, 1.5])),
    x2="x:Q", y2="y:Q",
)
boundary = alt.Chart(boundary_df).mark_line(color="#C9C4B8", strokeWidth=1).encode(x="x:Q", y="y:Q")
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
    .mark_area(opacity=0.15)
    .encode(
        x="x:Q", y="y:Q", order="order:Q",
        color=alt.Color("series:N", legend=None, scale=alt.Scale(domain=["Sydney", "Go8 peer average"], range=[theme.RED, theme.BLUE])),
    )
)
radar_chart = (boundary + spokes + radar_fill + radar_shapes + labels).properties(width="container", height=420).configure_view(strokeWidth=0)
st.altair_chart(radar_chart, use_container_width=True)

theme.rule(theme.YELLOW)

theme.anchor("go8-growth")
st.subheader("Publication-count growth (total-period, within MAIN_YEAR_RANGE)")
st.caption(
    "Not a year-over-year growth rate — see docs/methodology.md, Total-period growth. "
    "For 'which Go8 universities are improving most rapidly'."
)
growth = get_growth_by_university()
growth_df = growth.rename_axis("university").reset_index(name="growth")
growth_df["is_client"] = growth_df["university"] == CLIENT_UNIVERSITY
growth_bar = (
    alt.Chart(growth_df)
    .mark_bar()
    .encode(
        y=alt.Y("university:N", title="", sort="-x"),
        x=alt.X("growth:Q", title="Total-period growth", axis=alt.Axis(format="%")),
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
st.subheader("Strongest / weakest fields vs. Go8 peers")
st.caption("Sydney's mean FWCI minus the Go8-peer average, by field. Positive = Sydney outperforms.")
gap = get_field_gap_vs_peers()
gap_df = gap.reset_index(names="field")
gap_chart = (
    alt.Chart(gap_df)
    .mark_bar()
    .encode(
        y=alt.Y("field:N", title="", sort="-x"),
        x=alt.X("gap:Q", title="Mean FWCI gap (Sydney − Go8 peer average)"),
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
st.caption(
    "Both lists computed live from the chart above, most recent run of "
    "field_gap_vs_peers() — see p36.analysis.go8_benchmarking."
)

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
    st.caption("Share of output by source type — 'are competitors using different publishing patterns?'")
    patterns = get_journal_pattern()
    st.dataframe(patterns.style.format("{:.1%}"), width="stretch")

caveat(
    "All figures on this page use the RAW (non-deduplicated) dataset — a jointly-"
    "authored Go8 paper legitimately counts toward each contributing university's "
    "own output. See data_dictionary.md, Data quality notes, before comparing these "
    "to any total-Go8-output figure, which must be deduplicated instead."
)
