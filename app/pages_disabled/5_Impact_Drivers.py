import altair as alt
import pandas as pd
import streamlit as st

import theme
from lib.impact_drivers import get_impact_by_collaboration_breadth, load_deduplicated
from p36.analysis import impact_drivers

st.set_page_config(page_title="P36 · Impact Drivers", page_icon=theme.FAVICON, layout="wide")
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
        ("Which factors have the strongest association with citation impact?", "done", "id-coefficients"),
        ("Which factors remain important after controlling for other metrics?", "done", "id-coefficients"),
        ("Is journal quartile (Q1) still important after accounting for field?", "done", "id-coefficients"),
        ("Is international collaboration still important after accounting for journal quality?", "done", "id-coefficients"),
        ("Open Access → Citation Impact", "done", "id-coefficients"),
        ("Collaboration Size → Citation Impact", "done", "id-coefficients"),
        ("Document Type → Citation Impact", "done", "id-doctype"),
        ("Does international collaboration indirectly improve impact by increasing the likelihood of Q1 publishing?", "partial", "id-mediation"),
        ("Institutional Collaboration → Journal Choice → Citation Impact", "partial", "id-coefficients"),
        ("Is there an interaction between journal quality and international collaboration?", "done", "id-interaction"),
        ("What combination of factors is most commonly associated with high- vs. low-impact publications?", "done", "id-combination"),
        ("Are some drivers particularly important only in particular disciplines?", "done", "id-field-interaction"),
    ]
)
st.caption(
    "The two 'partial' items are indirect/mediation questions this single regression "
    "answers only qualitatively, not with a formal indirect-effect estimate: is_international "
    "and is_q1 are both included as direct predictors here, so a shrinking international "
    "coefficient relative to a model without is_q1 is consistent with (not proof of) part of "
    "its effect running *through* Q1 placement — see the breadth-vs-Q1 chart below for that "
    "comparison. 'Institutional collaboration → journal choice' has no journal-choice mediator "
    "variable defined; log_institutions below is its direct effect on impact only, not routed "
    "through journal tier. 'Field-specific importance' is answered directly below for "
    "is_international and is_q1 — the two predictors people actually ask this about — by adding "
    "a field interaction term for just that one predictor at a time, not for every predictor in "
    "the main model at once, which would need many more extra terms and enough rows per field "
    "to estimate them all precisely."
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

@st.cache_resource(show_spinner="Fitting the Q1 × international interaction model…")
def get_interaction_fit(_model_df):
    return impact_drivers.fit_interaction_model(_model_df)

@st.cache_resource(show_spinner="Fitting the per-field interaction model…")
def get_field_interaction_fit(_model_df, driver):
    return impact_drivers.fit_field_interaction_model(_model_df, driver)

@st.cache_data(show_spinner="Building the factor-combination table…")
def get_combination_summary():
    return impact_drivers.combination_summary(load_deduplicated())

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

theme.anchor("id-coefficients")
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

theme.anchor("id-mediation")
st.subheader("Does intl. collaboration work partly through Q1 placement?")
st.caption(
    "Not a mediation model — the same breadth-vs-Q1-share pattern used on the "
    "International Collaboration page, shown here next to the regression it's being "
    "read against. Both climbing together is consistent with (not proof of) part of "
    "international collaboration's effect running through Q1 placement, which is why "
    "is_international's coefficient above, with is_q1 already held constant, is smaller "
    "than the raw gap between international and domestic publications would suggest."
)
breadth = get_impact_by_collaboration_breadth()
breadth_df = breadth.reset_index(names="countries")
breadth_df["countries"] = breadth_df["countries"].astype(str)
med_fwci, med_q1 = st.columns(2)
with med_fwci:
    st.altair_chart(
        theme.style(
            alt.Chart(breadth_df)
            .mark_bar(color=theme.BLUE)
            .encode(
                x=alt.X("countries:N", title="Distinct co-author countries", sort=None),
                y=alt.Y("mean_fwci:Q", title="Mean FWCI"),
                tooltip=["countries", alt.Tooltip("mean_fwci:Q", format=".3f")],
            ),
            height=260,
        ),
        use_container_width=True,
    )
with med_q1:
    st.altair_chart(
        theme.style(
            alt.Chart(breadth_df)
            .mark_bar(color=theme.RED)
            .encode(
                x=alt.X("countries:N", title="Distinct co-author countries", sort=None),
                y=alt.Y("q1_share:Q", title="Q1 share", axis=alt.Axis(format="%")),
                tooltip=["countries", alt.Tooltip("q1_share:Q", format=".1%")],
            ),
            height=260,
        ),
        use_container_width=True,
    )

theme.rule(theme.YELLOW)

theme.anchor("id-doctype")
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

theme.anchor("id-interaction")
st.subheader("Interaction: journal quality × international collaboration")
st.caption(
    "A separate model from the main one above, not the main model with a term added — "
    "adding an interaction changes what is_q1 and is_international mean on their own "
    "(each becomes 'the effect when the other is False'), which is a different question "
    "from the main model's 'holding everything else constant' reading. Same predictors, "
    "same HC3 robust SE, plus one `is_q1 : is_international` term."
)
interaction_fit = get_interaction_fit(model_df_full)
inter_table = impact_drivers.interaction_summary_table(interaction_fit)
st.dataframe(
    inter_table.style.format({"coefficient": "{:.4f}", "std_err": "{:.4f}", "p_value": "{:.4f}", "ci_low": "{:.4f}", "ci_high": "{:.4f}"}),
    width="stretch",
)
inter_row = inter_table.loc["is_international[T.True]:is_q1[T.True]"]
q1_row = inter_table.loc["is_q1[T.True]"]
intl_row = inter_table.loc["is_international[T.True]"]
inter_sig = "statistically significant" if inter_row["p_value"] < 0.05 else "not statistically significant"
st.markdown(
    f"With the interaction term included, **is_international** on its own reads "
    f"**{intl_row['coefficient']:+.3f}** (its effect specifically for *non*-Q1 publications), "
    f"**is_q1** on its own reads **{q1_row['coefficient']:+.3f}** (its effect specifically for "
    f"*domestic* publications), and the interaction term is **{inter_row['coefficient']:+.3f}** "
    f"({inter_sig}, p = {inter_row['p_value']:.4f}) — the *extra* Q1 boost that international "
    "publications get on top of both main effects. "
    + (
        "Read together: international collaboration's benefit in this dataset is concentrated "
        "among Q1 publications, not a flat effect that applies equally regardless of journal "
        "tier — for non-Q1 publications specifically, being international is associated with "
        "*lower* mean FWCI once field, year, and the other predictors are held constant."
        if intl_row["coefficient"] < 0 < inter_row["coefficient"]
        else "Read the three rows together, not the interaction term alone, to describe how the "
        "two factors combine."
    )
)

theme.rule(theme.YELLOW)

theme.anchor("id-field-interaction")
st.subheader("Is a driver's importance the same in every discipline?")
st.caption(
    "A separate model per predictor below, each adding one `driver × field` interaction "
    "to the main model — not the field fixed effects already in the main model, which only "
    "let each field have a different *baseline* FWCI, not a different *is_q1* or "
    "*is_international* coefficient. Only 5 broad QS fields, so this is a handful of extra "
    "terms, not the dozens it would take to interact every predictor with field at once."
)
field_driver = st.selectbox(
    "Driver", ["is_international", "is_q1"],
    format_func=lambda d: "International collaboration" if d == "is_international" else "Q1 status",
)
field_fit = get_field_interaction_fit(model_df_full, field_driver)
field_table = impact_drivers.field_interaction_summary_table(field_fit, field_driver)
field_df = field_table.reset_index()
field_df["sign"] = field_df["effect"].apply(lambda v: "negative" if v < 0 else "positive")
field_sort = field_df.sort_values("effect", ascending=False)["field"].tolist()
field_whiskers = (
    alt.Chart(field_df)
    .mark_rule(strokeWidth=3)
    .encode(
        y=alt.Y("field:N", title="", sort=field_sort),
        x=alt.X("ci_low:Q", title=f"{field_driver} effect on mean FWCI (95% CI, HC3 robust SE)"),
        x2="ci_high:Q",
        color=alt.Color("sign:N", legend=None, scale=alt.Scale(domain=["negative", "positive"], range=[theme.RED, theme.BLUE])),
    )
)
field_points = (
    alt.Chart(field_df)
    .mark_point(filled=True, size=140, stroke="black", strokeWidth=1.5)
    .encode(
        y=alt.Y("field:N", title="", sort=field_sort),
        x=alt.X("effect:Q"),
        color=alt.Color("sign:N", legend=None, scale=alt.Scale(domain=["negative", "positive"], range=[theme.RED, theme.BLUE])),
        tooltip=["field", alt.Tooltip("effect:Q", format=".3f"), alt.Tooltip("p_value:Q", format=".4f")],
    )
)
field_zero = alt.Chart(field_df).mark_rule(color=theme.BLACK, strokeDash=[4, 4]).encode(x=alt.datum(0))
st.altair_chart(theme.style(field_zero + field_whiskers + field_points, height=260), use_container_width=True)
widest = field_table["effect"].idxmax()
narrowest = field_table["effect"].idxmin()
st.markdown(
    f"Widest range: **{widest}** at **{field_table.loc[widest, 'effect']:+.3f}**, "
    f"**{narrowest}** at **{field_table.loc[narrowest, 'effect']:+.3f}** — the effect isn't "
    "flat across disciplines, and for some fields the confidence interval crosses zero or "
    "flips sign entirely, holding the same other predictors, year, and document type constant."
)

theme.rule(theme.YELLOW)

theme.anchor("id-combination")
st.subheader("Which combination of factors goes with high vs. low impact?")
st.caption(
    "Descriptive group means on the full dataset, not a regression — every combination of "
    "is_q1 / is_international / is_open_access, sorted by mean FWCI. Confounding and all "
    "(unlike the coefficient tables above, nothing here is held constant) — pair with the "
    "main model for the 'holding everything else constant' version of the same question."
)
combo = get_combination_summary().reset_index()
combo["combination"] = combo.apply(
    lambda r: " + ".join(
        filter(None, [
            "Q1" if r["is_q1"] else None,
            "Intl" if r["is_international"] else None,
            "OA" if r["is_open_access"] else None,
        ])
    ) or "None of Q1 / Intl / OA",
    axis=1,
)
combo_chart = (
    alt.Chart(combo)
    .mark_bar()
    .encode(
        y=alt.Y("combination:N", title="", sort="-x"),
        x=alt.X("mean_fwci:Q", title="Mean FWCI"),
        color=alt.Color("mean_fwci:Q", legend=None, scale=alt.Scale(range=theme.SEQUENTIAL_RANGE)),
        tooltip=["combination", "publications", alt.Tooltip("mean_fwci:Q", format=".3f"), alt.Tooltip("top_decile_share:Q", format=".1%"), alt.Tooltip("uncited_share:Q", format=".1%")],
    )
)
st.altair_chart(theme.style(combo_chart, height=280), use_container_width=True)
top_combo = combo.iloc[0]
bottom_combo = combo.iloc[-1]
st.markdown(
    f"**Highest:** {top_combo['combination']} — {top_combo['mean_fwci']:.2f} mean FWCI, "
    f"{top_combo['top_decile_share']:.1%} highly cited, {top_combo['publications']:,} publications. "
    f"**Lowest:** {bottom_combo['combination']} — {bottom_combo['mean_fwci']:.2f} mean FWCI, "
    f"{bottom_combo['uncited_share']:.1%} uncited, {bottom_combo['publications']:,} publications."
)

theme.rule(theme.YELLOW)

diag_df = pd.DataFrame(
    {"actual": model_df_full["Field-Weighted Citation Impact"].values, "predicted": fit.fittedvalues.values}
)
diag_sample = diag_df.sample(min(3000, len(diag_df)), random_state=42)
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
