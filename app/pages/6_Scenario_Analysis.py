import altair as alt
import pandas as pd
import streamlit as st

import theme
from lib import CLIENT_UNIVERSITY, get_client_institution_scenario, get_institution_partner_performance, get_scenario_table
from p36.config import HIGH_PERFORMING_PARTNER_MIN_PUBLICATIONS, SCENARIO_DEFAULT_DELTA_PP

st.set_page_config(page_title="Scenario Analysis", page_icon="🔮", layout="wide")
theme.inject()
theme.header(
    "Scenario Analysis",
    "README Analysis item 17 — what would mean impact look like under a hypothetical "
    "shift in Q1 share, international collaboration, open access, or the uncited share?",
    shape="triangle",
    color=theme.YELLOW,
)

theme.question_panel(
    [
        ("Increase Q1 publication share by N percentage points.", "done", "sc-scenarios"),
        ("Increase international collaboration by N percentage points.", "done", "sc-scenarios"),
        ("Increase open-access publication where evidence suggests a benefit.", "done", "sc-scenarios"),
        ("Reduce the proportion of low-impact publications.", "partial", "sc-scenarios"),
        ("Improve publication performance within selected research areas.", "elsewhere", "/Go8_Benchmarking#go8-fields"),
        ("Increase collaboration with selected high-performing institutions.", "done", "sc-institutions"),
        ("Shift some publications toward journals identified as strong opportunities.", "done", "sc-scenarios"),
    ]
)
st.caption(
    "'Reduce low-impact publications' is projected via the uncited share, the closest "
    "binary flag this dataset has — 'low-impact' itself is undefined by the client and is "
    "not the same claim as 'uncited'. 'Research areas' is the Go8 Benchmarking page's "
    "field-gap-vs-peers chart, which shows *where* Sydney trails, but is not turned into "
    "its own FWCI projection here. 'Strong-opportunity journals' uses the Journal Tier "
    "page's over-performing-sources table directly, restricted to publications whose "
    "source has enough volume in its tier to have a defined gap. 'High-performing "
    "institutions' turned out to be answerable after all — the `Institutions` column "
    "(pipe-delimited co-author affiliation names) supports the same kind of over/under-"
    "performer analysis as the journal one, just not spotted until asked about directly; "
    "see the dedicated section below, kept separate from the five scenarios above because "
    "it runs on a different population (Sydney's own raw publications, not the Go8-wide "
    "deduplicated set)."
)

st.error(
    "**These are not predictions.** Every scenario assumes newly-shifted "
    "publications behave like the historical average of the group they'd join. "
    "Present these as potential implications of a historical relationship, "
    "never as a guaranteed outcome — per the README's own instruction for this "
    "item. See docs/methodology.md and finding-checker.md.",
    icon="🚫",
)

delta_pp = st.slider(
    "Percentage-point shift",
    min_value=0.01,
    max_value=0.20,
    value=SCENARIO_DEFAULT_DELTA_PP,
    step=0.01,
    format="%.2f",
)

table = get_scenario_table(delta_pp)

label_map = {
    "is_q1": "↑ Q1 publication share",
    "is_international": "↑ International collaboration",
    "is_open_access": "↑ Open access (PROVISIONAL null-handling)",
    "is_uncited": "↓ Uncited-publication share",
    "is_source_overperforming": "↑ Publishing in stronger-tier journals",
}
table.index = table.index.map(label_map)

theme.rule(theme.YELLOW)

theme.anchor("sc-scenarios")
st.subheader("Projected mean FWCI under each scenario")
long_df = table[["current_mean_metric", "projected_mean_metric"]].reset_index(names="scenario")
long_df = long_df.melt(id_vars="scenario", var_name="series", value_name="mean_fwci")
long_df["series"] = long_df["series"].map({"current_mean_metric": "Current", "projected_mean_metric": "Projected"})
grouped_bar = (
    alt.Chart(long_df)
    .mark_bar()
    .encode(
        x=alt.X("series:N", title="", axis=None),
        y=alt.Y("mean_fwci:Q", title="Mean FWCI"),
        color=alt.Color(
            "series:N", title="",
            scale=alt.Scale(domain=["Current", "Projected"], range=[theme.BLUE, theme.RED]),
        ),
        column=alt.Column("scenario:N", title="", header=alt.Header(labelFontSize=11, labelAngle=0)),
        tooltip=["scenario", "series", alt.Tooltip("mean_fwci:Q", format=".3f")],
    )
    .properties(width=140, height=320)
)
st.altair_chart(grouped_bar, use_container_width=False)

theme.rule(theme.YELLOW)

st.subheader("What if all five scenarios happened at once?")
st.caption(
    "Waterfall of each scenario's own delta stacked onto one baseline. This "
    "**additionally assumes the five shifts don't interact** — e.g. that the "
    "uplift from more Q1 publishing is the same whether or not international "
    "collaboration also rose — which is a stronger, less-tested assumption than "
    "any single scenario above on its own. Treat the 'combined' bar as the most "
    "speculative number on this page, not the headline one. It's more speculative "
    "still as of this scenario set: 'publishing in stronger-tier journals' is scoped "
    "to the ~74% of publications whose source has enough volume in its tier to have "
    "a defined over/under-performer classification, while the other four scenarios "
    "cover nearly the full dataset — stacking a smaller-population delta onto a "
    "full-population baseline is an extra approximation on top of the non-interaction "
    "assumption already flagged above."
)
baseline = table.loc["↑ International collaboration", "current_mean_metric"]
deltas = table["projected_mean_metric"] - table["current_mean_metric"]

steps = ["Current"] + list(table.index) + ["Combined (additive)"]
running = baseline
starts, ends, kinds = [], [], []
for i, step in enumerate(steps):
    if step == "Current":
        starts.append(0.0)
        ends.append(baseline)
        kinds.append("baseline")
    elif step == "Combined (additive)":
        starts.append(0.0)
        ends.append(running)
        kinds.append("total")
    else:
        d = deltas[step]
        starts.append(running)
        running += d
        ends.append(running)
        kinds.append("increase" if d >= 0 else "decrease")

waterfall_df = pd.DataFrame({"step": steps, "start": starts, "end": ends, "kind": kinds})
waterfall = (
    alt.Chart(waterfall_df)
    .mark_bar(size=45)
    .encode(
        x=alt.X("step:N", title="", sort=steps, axis=alt.Axis(labelAngle=-20)),
        y=alt.Y("start:Q", title="Mean FWCI"),
        y2="end:Q",
        color=alt.Color(
            "kind:N", title="",
            scale=alt.Scale(domain=["baseline", "increase", "decrease", "total"], range=[theme.BLUE, theme.RED, theme.BLUE, theme.BLACK]),
        ),
        tooltip=["step", alt.Tooltip("end:Q", format=".3f")],
    )
)
st.altair_chart(theme.style(waterfall, height=380), use_container_width=True)

st.subheader("Full detail")
st.dataframe(
    table.style.format(
        {
            "delta_pp": "{:+.0%}",
            "current_share": "{:.1%}",
            "projected_share": "{:.1%}",
            "mean_when_true": "{:.3f}",
            "mean_when_false": "{:.3f}",
            "current_mean_metric": "{:.3f}",
            "projected_mean_metric": "{:.3f}",
        }
    ),
    width="stretch",
)

st.caption(
    "The 'Open access' scenario inherits a PROVISIONAL, client-unconfirmed "
    "null-handling assumption — see p36.config.OPEN_ACCESS_NULL_MEANS_NOT_OA."
)

theme.rule(theme.YELLOW)

st.subheader("Sensitivity: does the projection scale linearly with the shift size?")
st.caption(
    "estimate_uplift_from_share_shift() is a linear extrapolation by construction "
    "(projected = current + delta_pp × group gap) — so yes, by design. This chart "
    "makes that assumption visible rather than leaving it implicit in a single "
    "slider value: a 20pp shift is projected as exactly 20× the effect of a 1pp "
    "shift, which is only as credible as the assumption that the group gap stays "
    "constant across that whole range."
)
sweep_points = [0.01, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20]
sweep_rows = []
for dp in sweep_points:
    sweep_table = get_scenario_table(dp)
    for scenario, row in sweep_table.iterrows():
        sweep_rows.append({"delta_pp": dp, "scenario": label_map.get(scenario, scenario), "projected_mean_metric": row["projected_mean_metric"]})
sweep_df = pd.DataFrame(sweep_rows)
sweep_chart = (
    alt.Chart(sweep_df)
    .mark_line(point=alt.OverlayMarkDef(size=80))
    .encode(
        x=alt.X("delta_pp:Q", title="Percentage-point shift", axis=alt.Axis(format="%")),
        y=alt.Y("projected_mean_metric:Q", title="Projected mean FWCI"),
        color=alt.Color("scenario:N", title="", scale=alt.Scale(range=theme.PALETTE)),
        tooltip=["scenario", alt.Tooltip("delta_pp:Q", format=".0%"), alt.Tooltip("projected_mean_metric:Q", format=".3f")],
    )
)
st.altair_chart(theme.style(sweep_chart, height=340), use_container_width=True)

theme.rule(theme.YELLOW)

theme.anchor("sc-institutions")
st.subheader("Increase collaboration with high-performing institutions")
st.caption(
    "A separate scenario from the five above — runs on Sydney's own raw publications "
    "(not the Go8-wide deduplicated set), because 'which institutions should Sydney work "
    "with more' is inherently a single-university question. The `Institutions` column "
    "(pipe-delimited co-author affiliation names on every publication) supports the same "
    "kind of over/under-performer analysis the Journal Tier page runs on journals: per "
    f"partner institution, mean FWCI of Sydney's publications with that co-author vs. "
    f"Sydney's own overall mean, restricted to partners with at least "
    f"{HIGH_PERFORMING_PARTNER_MIN_PUBLICATIONS} co-authored publications."
)

partner_perf = get_institution_partner_performance()
tab_top, tab_bottom = st.tabs(["Strongest partners", "Weakest partners"])
with tab_top:
    top_partners = partner_perf.nlargest(12, "gap").reset_index()
    top_chart = (
        alt.Chart(top_partners)
        .mark_bar(color=theme.BLUE)
        .encode(
            y=alt.Y("institution:N", title="", sort="-x"),
            x=alt.X("gap:Q", title="Partner mean FWCI − Sydney's own overall mean FWCI"),
            tooltip=["institution", "publications", alt.Tooltip("mean_fwci:Q", format=".2f"), alt.Tooltip("gap:Q", format=".2f")],
        )
    )
    st.altair_chart(theme.style(top_chart, height=360), use_container_width=True)
with tab_bottom:
    bottom_partners = partner_perf.nsmallest(12, "gap").reset_index()
    bottom_chart = (
        alt.Chart(bottom_partners)
        .mark_bar(color=theme.RED)
        .encode(
            y=alt.Y("institution:N", title="", sort="x"),
            x=alt.X("gap:Q", title="Partner mean FWCI − Sydney's own overall mean FWCI"),
            tooltip=["institution", "publications", alt.Tooltip("mean_fwci:Q", format=".2f"), alt.Tooltip("gap:Q", format=".2f")],
        )
    )
    st.altair_chart(theme.style(bottom_chart, height=360), use_container_width=True)

institution_scenario = get_client_institution_scenario(delta_pp)
st.markdown(
    f"**Projection:** {institution_scenario['current_share']:.1%} of Sydney's publications "
    "with at least one qualifying partner already involve a high-performing one "
    f"(mean FWCI **{institution_scenario['mean_when_true']:.2f}** vs. "
    f"**{institution_scenario['mean_when_false']:.2f}** for publications whose qualifying "
    f"partners are all below-average). Shifting {delta_pp:.0%} more of that group toward "
    f"high-performing partners projects mean FWCI from "
    f"**{institution_scenario['current_mean_metric']:.3f}** to "
    f"**{institution_scenario['projected_mean_metric']:.3f}** — over that subset only, not "
    "Sydney's full publication count (publications with no partner meeting the volume floor "
    "are excluded, not counted as a negative)."
)
caveat_gap = partner_perf.nlargest(3, "gap")
st.caption(
    "Strongest partners skew toward large multi-site clinical/medical collaborations "
    "(" + ", ".join(caveat_gap.index) + ", among others) — plausibly genuine high-value "
    "partnerships, but also exactly the pattern a handful of huge multi-author clinical "
    "trials would produce even without the partner institution itself adding anything "
    "beyond being part of that trial. Treat this list as a shortlist to investigate, "
    "same caveat as the Journal Tier page's over-performing sources."
)
