import altair as alt
import streamlit as st

import theme
from lib.field_analysis import (
    caveat,
    get_collaboration_approach_by_field,
    get_field_growth,
    get_field_summary,
    get_field_trend,
    get_fwci_by_field,
    load_exploded_deduplicated,
)
from p36.analysis import field_analysis
from p36.analysis.field_analysis import FIELD_COLUMN_EXPLODED
from p36.config import FRACTIONAL_FIELD_COUNTING

st.set_page_config(page_title="P36 · Field Analysis", page_icon=theme.FAVICON, layout="wide")
theme.inject()
theme.header(
    "Research Field / Faculty Analysis",
    "README Analysis item 6 — which fields are strongest, improving, or under-performing?",
    shape="triangle",
    color=theme.YELLOW,
)

theme.question_panel(
    [
        ("Which fields produce the highest publication volume?", "done", "fa-summary"),
        ("Which fields achieve the strongest impact?", "done", "fa-summary"),
        ("Which fields have the highest Q1 publication share?", "done", "fa-summary"),
        ("Which fields have high volume but relatively low citation impact?", "done", "fa-quadrant"),
        ("Which fields have relatively low volume but very strong citation impact?", "done", "fa-quadrant"),
        ("Which areas are improving most rapidly / declining?", "done", "fa-growth"),
        ("Which fields produce the highest proportion of overperforming (top-decile) publications?", "done", "fa-summary"),
        ("Which fields produce the largest number of highly cited publications?", "done", "fa-highly-cited"),
        ("Which fields appear to represent existing strengths, and where is the greatest potential for improvement?", "partial", "fa-quadrant"),
        ("Are particular publication strategies more successful in some fields than others?", "done", "fa-approach"),
    ]
)
st.caption(
    "'Strengths / potential' links to the volume-vs-impact quadrant below — its four "
    "quadrants are the closest single chart to an answer (high-volume/high-impact reads "
    "as an existing strength, low-volume/high-impact as potential upside) — but the full "
    "answer is a synthesis with the Q1-share and growth sections too, not that chart alone. "
    "'Publication strategy' has no client-confirmed definition — answered below via the "
    "closest concrete stand-in this dataset supports (domestic-single-institution / "
    "domestic-multi-institution / international), not a broader notion of strategy (venue "
    "choice, career stage, etc.) this data can't speak to."
)

_, dropped = load_exploded_deduplicated()
if dropped:
    st.caption(
        f"{dropped:,} publications have no field classification and are excluded "
        "below — see data_dictionary.md."
    )
if FRACTIONAL_FIELD_COUNTING:
    st.caption("Fractional field counting is on.")
else:
    st.caption(
        "Whole counting (FRACTIONAL_FIELD_COUNTING=False, PROVISIONAL): a paper in "
        "N fields counts fully toward each — field totals below sum to more than "
        "the true publication count."
    )

field_summary = get_field_summary()

theme.anchor("fa-summary")
st.subheader("Field summary")
col_table, col_donut = st.columns([3, 2])
with col_table:
    st.dataframe(
        field_summary.style.format(
            {
                "publications": "{:,.0f}",
                "mean_fwci": "{:.3f}",
                "q1_share": "{:.1%}",
                "top_decile_share": "{:.1%}",
                "uncited_share": "{:.1%}",
            }
        ),
        width="stretch",
        height=380,
    )
with col_donut:
    st.caption("Share of publications by field (donut).")
    tree_df = field_summary.reset_index(names="field")
    donut = (
        alt.Chart(tree_df)
        .mark_arc(innerRadius=55)
        .encode(
            theta=alt.Theta("publications:Q"),
            color=alt.Color("field:N", title="", scale=alt.Scale(range=theme.PALETTE + ["#6B8E23", "#8B5E3C", "#4A6D7C", "#B08968"])),
            tooltip=["field", "publications"],
        )
    )
    st.altair_chart(theme.style(donut, height=380), use_container_width=True)

theme.rule(theme.YELLOW)

theme.anchor("fa-quadrant")
col_scatter, col_box = st.columns(2)
with col_scatter:
    st.subheader("Volume vs. impact")
    st.caption("Median split — a relative statement about this dataset, not a universal 'high' threshold.")
    quadrant = field_analysis.volume_vs_impact_quadrant(field_summary).reset_index(names="field")
    scatter = (
        alt.Chart(quadrant)
        .mark_circle(size=200)
        .encode(
            x=alt.X("publications:Q", title="Publications"),
            y=alt.Y("mean_fwci:Q", title="Mean FWCI"),
            color=alt.Color("quadrant:N", title="", scale=alt.Scale(range=theme.PALETTE)),
            tooltip=["field", "publications", alt.Tooltip("mean_fwci:Q", format=".3f"), "quadrant"],
        )
    )
    labels = alt.Chart(quadrant).mark_text(dy=-14, font=theme.FONT_BODY, fontSize=10).encode(
        x="publications:Q", y="mean_fwci:Q", text="field:N", color=alt.value(theme.BLACK)
    )
    st.altair_chart(theme.style(scatter + labels), use_container_width=True)

with col_box:
    st.subheader("Impact spread by field")
    st.caption(
        "The mean alone hides this: FWCI is heavy-tailed, so two fields with the "
        "same mean can have very different spreads."
    )
    fwci_field = get_fwci_by_field()
    order_by_median = (
        fwci_field.groupby(FIELD_COLUMN_EXPLODED)["Field-Weighted Citation Impact"]
        .median()
        .sort_values(ascending=False)
        .index.tolist()
    )
    p95 = fwci_field["Field-Weighted Citation Impact"].quantile(0.95)
    box = (
        alt.Chart(fwci_field)
        .mark_boxplot(color=theme.BLUE, outliers=False)
        .encode(
            x=alt.X(f"{FIELD_COLUMN_EXPLODED}:N", title="", sort=order_by_median, axis=alt.Axis(labelAngle=-30)),
            y=alt.Y("Field-Weighted Citation Impact:Q", title="FWCI", scale=alt.Scale(domain=[0, p95])),
        )
    )
    st.altair_chart(theme.style(box), use_container_width=True)

theme.rule(theme.YELLOW)

theme.anchor("fa-q1-share")
st.subheader("Q1 share by field")
st.caption("Same PROVISIONAL Q1 definition as the Journal Tier page, broken out by field.")
q1_field_df = field_summary[["q1_share"]].reset_index(names="field")
q1_field_chart = (
    alt.Chart(q1_field_df)
    .mark_bar(color=theme.BLUE)
    .encode(
        y=alt.Y("field:N", title="", sort="-x"),
        x=alt.X("q1_share:Q", title="Q1 share", axis=alt.Axis(format="%")),
        tooltip=["field", alt.Tooltip("q1_share:Q", format=".1%")],
    )
)
st.altair_chart(theme.style(q1_field_chart, height=max(240, 24 * len(q1_field_df))), use_container_width=True)

theme.rule(theme.YELLOW)

theme.anchor("fa-highly-cited")
st.subheader("Highly cited publications by field")
st.caption(
    "top_decile_share above is a *rate* — this is the count it implies "
    "(publications × top_decile_share, rounded), for 'which fields produce the largest "
    "number of highly cited publications' as distinct from 'which fields have the "
    "highest highly-cited *rate*' (a small field can have a high rate but few papers)."
)
highly_cited_df = field_summary.reset_index(names="field").assign(
    highly_cited_count=lambda d: (d["publications"] * d["top_decile_share"]).round().astype(int)
)
highly_cited_chart = (
    alt.Chart(highly_cited_df)
    .mark_bar(color=theme.RED)
    .encode(
        y=alt.Y("field:N", title="", sort="-x"),
        x=alt.X("highly_cited_count:Q", title="Highly cited publications (top-decile)"),
        tooltip=["field", "highly_cited_count", alt.Tooltip("top_decile_share:Q", format=".1%")],
    )
)
st.altair_chart(theme.style(highly_cited_chart, height=max(240, 24 * len(highly_cited_df))), use_container_width=True)

theme.rule(theme.YELLOW)

theme.anchor("fa-growth")
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Field growth (total-period)")
    st.caption("Not year-over-year — see docs/methodology.md, Total-period growth.")
    growth = get_field_growth()
    growth_df = growth.rename_axis("field").reset_index(name="growth")
    growth_bar = (
        alt.Chart(growth_df)
        .mark_bar()
        .encode(
            y=alt.Y("field:N", title="", sort="-x"),
            x=alt.X("growth:Q", title="Total-period growth", axis=alt.Axis(format="%")),
            color=alt.Color("growth:Q", legend=None, scale=theme.diverging_scale(growth_df["growth"].min(), growth_df["growth"].max())),
            tooltip=["field", alt.Tooltip("growth:Q", format=".1%")],
        )
    )
    st.altair_chart(theme.style(growth_bar), use_container_width=True)
    top_growth = growth_df.nlargest(3, "growth")
    bottom_growth = growth_df.nsmallest(3, "growth")
    st.markdown(
        "**Most improved:** "
        + ", ".join(f"{r.field} ({r.growth:+.0%})" for r in top_growth.itertuples())
    )
    st.markdown(
        "**Most declined:** "
        + ", ".join(f"{r.field} ({r.growth:+.0%})" for r in bottom_growth.itertuples())
    )

with col_b:
    st.subheader("Publications by field and year")
    trend = get_field_trend()
    trend_long = trend.reset_index(names="field").melt(id_vars="field", var_name="year", value_name="publications")
    heatmap = (
        alt.Chart(trend_long)
        .mark_rect()
        .encode(
            x=alt.X("year:O", title="Year"),
            y=alt.Y("field:N", title=""),
            color=alt.Color("publications:Q", title="", scale=alt.Scale(range=theme.SEQUENTIAL_RANGE)),
            tooltip=["field", "year", "publications"],
        )
    )
    st.altair_chart(theme.style(heatmap), use_container_width=True)

theme.rule(theme.YELLOW)

theme.anchor("fa-approach")
st.subheader("Are particular collaboration approaches more successful in some fields?")
st.caption(
    "'Publication strategy' has no client-confirmed definition, so this uses the closest "
    "concrete stand-in this dataset supports — domestic/single-institution vs. "
    "domestic/multi-institution vs. international authorship — crossed with field. "
    "Descriptive group means, not a regression: a field where international shows the "
    "highest mean FWCI is consistent with, not proof of, international collaboration being "
    "the more effective approach specifically in that field."
)
approach_df = get_collaboration_approach_by_field().reset_index()
approach_chart = (
    alt.Chart(approach_df)
    .mark_bar()
    .encode(
        y=alt.Y(f"{FIELD_COLUMN_EXPLODED}:N", title="", sort="-x"),
        x=alt.X("mean_fwci:Q", title="Mean FWCI"),
        color=alt.Color(
            "collaboration_approach:N", title="",
            scale=alt.Scale(
                domain=["International", "Domestic, multi-institution", "Domestic, single institution"],
                range=[theme.RED, theme.BLUE, theme.GREY],
            ),
        ),
        xOffset="collaboration_approach:N",
        tooltip=[FIELD_COLUMN_EXPLODED, "collaboration_approach", "publications", alt.Tooltip("mean_fwci:Q", format=".3f")],
    )
)
st.altair_chart(theme.style(approach_chart, height=max(280, 26 * approach_df[FIELD_COLUMN_EXPLODED].nunique())), use_container_width=True)
gap_by_field = (
    approach_df.pivot(index=FIELD_COLUMN_EXPLODED, columns="collaboration_approach", values="mean_fwci")
    .assign(intl_gap=lambda d: d["International"] - d[["Domestic, multi-institution", "Domestic, single institution"]].mean(axis=1))
    .sort_values("intl_gap", ascending=False)
)
st.caption(
    f"International's advantage over the two domestic approaches (averaged) is largest in "
    f"**{gap_by_field.index[0]}** (+{gap_by_field['intl_gap'].iloc[0]:.2f} FWCI) and smallest in "
    f"**{gap_by_field.index[-1]}** ({gap_by_field['intl_gap'].iloc[-1]:+.2f} FWCI) — international "
    "shows the highest mean FWCI in every field here, but by a very different margin field to field."
)

caveat(
    "Cross-field comparisons above use Field-Weighted Citation Impact and SciVal's "
    "own citation-percentile columns, never raw Citations — clinical medicine can "
    "average 5–10× the citations of mathematics for citation-culture reasons alone, "
    "not quality. See docs/methodology.md, Cross-field / cross-year comparison."
)
