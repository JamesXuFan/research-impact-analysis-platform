import altair as alt
import pandas as pd
import streamlit as st

import theme
from lib import load_deduplicated
from p36.analysis import impact_drivers

st.set_page_config(page_title="Impact Drivers", page_icon="📈", layout="wide")
theme.inject()
theme.header(
    "Integrated Research Impact Driver Analysis",
    "README Analysis item 14 — holding the other factors constant, which of Q1 status, "
    "international collaboration, institutional collaboration, and open access is "
    "actually associated with impact?",
    shape="square",
    color=theme.BLACK,
)

theme.question_panel(
    [
        ("Which factors have the strongest association with citation impact?", "done"),
        ("Which factors remain important after controlling for other metrics?", "done"),
        ("Is journal quartile (Q1) still important after accounting for field?", "done"),
        ("Is international collaboration still important after accounting for journal quality?", "done"),
        ("Open Access → Citation Impact", "done"),
        ("Collaboration Size → Citation Impact", "done"),
        ("Document Type → Citation Impact", "done"),
        ("Does international collaboration indirectly improve impact by increasing the likelihood of Q1 publishing?", "partial"),
        ("Institutional Collaboration → Journal Choice → Citation Impact", "partial"),
        ("Are some drivers particularly important only in particular disciplines? Are there interactions between journal quality and collaboration?", "open"),
        ("What combination of factors is most commonly associated with high- vs. low-impact publications?", "open"),
    ]
)
st.caption(
    "The two 'partial' items are indirect/mediation questions this single regression "
    "answers only qualitatively, not with a formal indirect-effect estimate: is_international "
    "and is_q1 are both included as direct predictors here, so a shrinking international "
    "coefficient relative to a model without is_q1 is consistent with (not proof of) part of "
    "its effect running *through* Q1 placement — see the International Collaboration page's "
    "breadth section for that comparison. 'Institutional collaboration → journal choice' has "
    "no journal-choice mediator variable defined; log_institutions below is its direct effect "
    "on impact only, not routed through journal tier. The two 'open' items — field-specific "
    "interaction effects, and a combination/pattern-mining view of what co-occurs in "
    "high/low-impact publications — are not implemented: this model estimates one global "
    "linear effect per predictor, not per-field interactions or combinations."
)

st.error(
    "**Still an observational, cross-sectional regression, not an experiment.** "
    "A significant coefficient is an association conditional on the other included "
    "predictors, not a causal effect. See docs/methodology.md and finding-checker.md.",
    icon="🚫",
)


@st.cache_resource(show_spinner="Fitting the impact-driver model…")
def get_fit():
    dedup = load_deduplicated()
    model_df = impact_drivers.build_driver_dataset(dedup)
    fit = impact_drivers.fit_impact_driver_model(model_df)
    return fit, len(dedup), len(model_df), model_df


fit, n_input, n_model, model_df_full = get_fit()

col1, col2, col3 = st.columns(3)
col1.metric("Sample used", f"{n_model:,} / {n_input:,}")
col2.metric("R²", f"{fit.rsquared:.4f}")
col3.metric("Predictors (+ field & doc-type FE)", "5")

st.caption(
    f"{n_input - n_model:,} rows dropped for missing predictors (no CiteScore "
    "percentile, no field classification, etc.) — see build_driver_dataset."
)

if fit.rsquared < 0.1:
    st.warning(
        f"R² = {fit.rsquared:.3f} — these factors together explain very little of "
        "the variance in any single publication's impact. State this plainly "
        "alongside any coefficient, not just the coefficients that are "
        "statistically significant.",
        icon="📉",
    )

theme.rule(theme.YELLOW)

st.subheader("Coefficients (Field-Weighted Citation Impact ~ predictors)")
table = impact_drivers.driver_summary_table(fit)
st.dataframe(
    table.style.format({"coefficient": "{:.4f}", "std_err": "{:.4f}", "p_value": "{:.4f}", "ci_low": "{:.4f}", "ci_high": "{:.4f}"}),
    width="stretch",
)

coef_df = table.reset_index(names="predictor")
coef_df["sign"] = coef_df["coefficient"].apply(lambda v: "negative" if v < 0 else "positive")
order = coef_df["coefficient"].abs().sort_values(ascending=False).index
sort_order = coef_df.loc[order, "predictor"].tolist()

whiskers = (
    alt.Chart(coef_df)
    .mark_rule(strokeWidth=3)
    .encode(
        y=alt.Y("predictor:N", title="", sort=sort_order),
        x=alt.X("ci_low:Q", title="Coefficient (95% CI, HC3 robust SE)"),
        x2="ci_high:Q",
        color=alt.Color(
            "sign:N", legend=None,
            scale=alt.Scale(domain=["negative", "positive"], range=[theme.RED, theme.BLUE]),
        ),
    )
)
points = (
    alt.Chart(coef_df)
    .mark_point(filled=True, size=140, stroke="black", strokeWidth=1.5)
    .encode(
        y=alt.Y("predictor:N", title="", sort=sort_order),
        x=alt.X("coefficient:Q"),
        color=alt.Color("sign:N", legend=None, scale=alt.Scale(domain=["negative", "positive"], range=[theme.RED, theme.BLUE])),
        tooltip=["predictor", alt.Tooltip("coefficient:Q", format=".4f"), alt.Tooltip("p_value:Q", format=".4f")],
    )
)
zero_line = alt.Chart(coef_df).mark_rule(color=theme.BLACK, strokeDash=[4, 4]).encode(x=alt.datum(0))
st.altair_chart(theme.style(zero_line + whiskers + points, height=280), use_container_width=True)

st.caption(
    "Field fixed-effect terms are omitted from the chart above (there can be "
    "dozens) — call `fit.summary()` directly for a specific field's effect. "
    "Document-type fixed effects (~8 categories) are small enough to show in full, below."
)

st.markdown("**Reading each coefficient:**")
for row in coef_df.sort_values("coefficient", key=abs, ascending=False).itertuples():
    if row.predictor.startswith("C(") or row.predictor == "Intercept":
        continue
    direction = "higher" if row.coefficient > 0 else "lower"
    sig = "statistically significant (p < 0.05)" if row.p_value < 0.05 else "not statistically significant at p < 0.05"
    st.markdown(
        f"- **{row.predictor}**: associated with **{abs(row.coefficient):.3f} {direction}** "
        f"mean FWCI, holding the other predictors constant — {sig} (p = {row.p_value:.4f})."
    )

theme.rule(theme.YELLOW)

st.subheader("Document Type → Citation Impact")
st.caption(
    "FWCI is already document-type-normalised by SciVal's own methodology — a naive "
    "expectation is that this term washes out to ~0. It does not: relative to Article "
    "(the baseline category), several document types carry a statistically significant, "
    "sizeable residual coefficient even after that normalisation."
)
doc_table = impact_drivers.document_type_summary_table(fit)
doc_df = doc_table.reset_index(names="document_type")
doc_df["sign"] = doc_df["coefficient"].apply(lambda v: "negative" if v < 0 else "positive")
doc_whiskers = (
    alt.Chart(doc_df)
    .mark_rule(strokeWidth=3)
    .encode(
        y=alt.Y("document_type:N", title="", sort=alt.EncodingSortField(field="coefficient", order="descending")),
        x=alt.X("ci_low:Q", title="Coefficient vs. Article (95% CI, HC3 robust SE)"),
        x2="ci_high:Q",
        color=alt.Color("sign:N", legend=None, scale=alt.Scale(domain=["negative", "positive"], range=[theme.RED, theme.BLUE])),
    )
)
doc_points = (
    alt.Chart(doc_df)
    .mark_point(filled=True, size=140, stroke="black", strokeWidth=1.5)
    .encode(
        y=alt.Y("document_type:N", title="", sort=alt.EncodingSortField(field="coefficient", order="descending")),
        x=alt.X("coefficient:Q"),
        color=alt.Color("sign:N", legend=None, scale=alt.Scale(domain=["negative", "positive"], range=[theme.RED, theme.BLUE])),
        tooltip=["document_type", alt.Tooltip("coefficient:Q", format=".3f"), alt.Tooltip("p_value:Q", format=".4f")],
    )
)
doc_zero = alt.Chart(doc_df).mark_rule(color=theme.BLACK, strokeDash=[4, 4]).encode(x=alt.datum(0))
st.altair_chart(theme.style(doc_zero + doc_whiskers + doc_points, height=280), use_container_width=True)
st.markdown(
    "- **Conference Paper** and **Chapter** both run significantly *above* Article-level "
    "mean FWCI, holding field, year, Q1 status, open access, and collaboration size constant.\n"
    "- **Data Paper** runs significantly *below* Article-level mean FWCI.\n"
    "- **Editorial / Letter / Note / Book** have very wide confidence intervals — only "
    "3 to 14 publications each *in this regression sample*, not the full dataset. Book "
    "alone has 2,491 publications overall, but 99.4% have no CiteScore percentile (a "
    "journal-level metric that mostly doesn't apply to books) and get dropped before "
    "fitting — treat these four coefficients as describing that small, non-random "
    "surviving slice, not document-type publishing as a whole."
)

theme.rule(theme.YELLOW)

diag_df = pd.DataFrame(
    {"actual": model_df_full["Field-Weighted Citation Impact"].values, "predicted": fit.fittedvalues.values}
)
diag_sample = diag_df.sample(min(3000, len(diag_df)), random_state=42)
# FWCI is heavy-tailed (median 0.85, 99th percentile ~12) — a domain fit to the
# 99th percentile crams ~80% of points into a sliver in the corner and makes the
# chart look empty at a glance. p95 keeps the axis to where the data actually is;
# clamp=True pins the handful of points beyond it to the edge instead of letting
# them silently vanish off-chart.
p95 = diag_df[["actual", "predicted"]].quantile(0.95).max()
beyond_p95 = int(((diag_sample["actual"] > p95) | (diag_sample["predicted"] > p95)).sum())

st.subheader("Model fit: predicted vs. actual")
st.caption(
    f"Every point is one publication (random sample of {len(diag_sample):,} of "
    f"{n_model:,}, for a renderable chart). A perfect model would sit on the "
    "diagonal — the spread here is the visual counterpart of the low R² above: "
    "individual-publication impact has a lot of variation these predictors don't "
    f"capture. Axis clipped to the 95th percentile ({p95:.1f}) so the bulk of the "
    f"heavy-tailed distribution isn't crushed into a corner — {beyond_p95} of "
    f"{len(diag_sample):,} sampled points fall beyond it and are pinned to the edge."
)
scatter_diag = (
    alt.Chart(diag_sample)
    .mark_circle(size=45, opacity=0.55, color=theme.BLUE)
    .encode(
        x=alt.X("predicted:Q", title="Predicted FWCI", scale=alt.Scale(domain=[0, p95], clamp=True)),
        y=alt.Y("actual:Q", title="Actual FWCI", scale=alt.Scale(domain=[0, p95], clamp=True)),
    )
)
diagonal = (
    alt.Chart(pd.DataFrame({"x": [0, p95], "y": [0, p95]}))
    .mark_line(color=theme.RED, strokeWidth=2, strokeDash=[6, 4])
    .encode(x="x:Q", y="y:Q")
)
st.altair_chart(theme.style(scatter_diag + diagonal, height=380), use_container_width=True)

with st.expander("Full statsmodels summary"):
    st.text(str(fit.summary()))
