"""README Analysis item 17 — Scenario Analysis.

Translates the historical associations found in items 3, 6, 9, 14, and 16 into
"what if" projections — e.g. "what would mean impact look like if the Q1 share
were 5 percentage points higher".

**These are not predictions.** Every scenario here assumes newly-shifted
publications behave like the historical average of the group they'd join — the
same assumption behind any "if we did more of X" claim built on observational
data, and it can be wrong (e.g. if X's benefit only holds for the kind of paper
that already does X, the marginal case may not repeat the historical gap). See
docs/methodology.md and .claude/agents/finding-checker.md: a scenario projection
must always be labelled a potential implication of the historical relationship,
never a guaranteed outcome, per the README's own instruction for this item.
"""

import pandas as pd

from p36.config import SCENARIO_DEFAULT_DELTA_PP

METRIC_COLUMN = "Field-Weighted Citation Impact"


def estimate_uplift_from_share_shift(
    df: pd.DataFrame,
    flag_column: str,
    delta_pp: float = SCENARIO_DEFAULT_DELTA_PP,
    metric_column: str = METRIC_COLUMN,
) -> dict:
    """Project the change in mean `metric_column` if the share of rows with
    `flag_column == True` shifted by `delta_pp` (e.g. 0.05 = +5 percentage
    points), assuming the newly-shifted publications perform like the existing
    average of the group they join. Linear reweighting:

        projected_mean = current_mean + delta_pp * (mean[flag=True] - mean[flag=False])

    Returns a dict with the current share, current mean, group means, and
    projected mean — report all of them together, not just the projection, so
    the assumption is visible alongside the number.
    """
    scoped = df[[flag_column, metric_column]].dropna()
    current_share = scoped[flag_column].mean()
    group_means = scoped.groupby(flag_column)[metric_column].mean()
    mean_true = group_means.get(True, float("nan"))
    mean_false = group_means.get(False, float("nan"))
    current_mean = scoped[metric_column].mean()
    projected_mean = current_mean + delta_pp * (mean_true - mean_false)
    return {
        "flag": flag_column,
        "delta_pp": delta_pp,
        "current_share": current_share,
        "projected_share": min(current_share + delta_pp, 1.0),
        "mean_when_true": mean_true,
        "mean_when_false": mean_false,
        "current_mean_metric": current_mean,
        "projected_mean_metric": projected_mean,
    }


def scenario_table(df: pd.DataFrame, delta_pp: float = SCENARIO_DEFAULT_DELTA_PP) -> pd.DataFrame:
    """Run the share-shift projection for every scenario in the README that
    maps onto an existing derived flag:

    - Increase Q1 publication share by `delta_pp`         (is_q1)
    - Increase international collaboration by `delta_pp`  (is_international)
    - Increase open-access publication by `delta_pp`      (is_open_access —
      **PROVISIONAL** null-handling, see p36.config.OPEN_ACCESS_NULL_MEANS_NOT_OA
      and docs/methodology.md; not confirmed by the client)
    - Reduce the share of low-impact (uncited) publications by `delta_pp`
      (is_uncited — note the sign: this scenario *reduces* a share, so pass
      delta_pp as negative when calling estimate_uplift_from_share_shift
      directly if you want the "reduce by" framing instead of "increase by")

    The remaining README scenarios — shifting toward specific high-performing
    institutions, or toward journals identified as strong opportunities — need
    institution- or journal-level targets identified first (see
    p36.analysis.go8_benchmarking.top_countries_by_university for the closest
    existing building block) and are not implemented here yet.

    Expects `df` to already carry `is_q1`, `is_international`, `is_open_access`,
    and `is_uncited` from p36.metrics.add_derived_flags — this function does not
    recompute them (see .claude/agents/metrics-consistency.md).
    """
    rows = [
        estimate_uplift_from_share_shift(df, "is_q1", delta_pp),
        estimate_uplift_from_share_shift(df, "is_international", delta_pp),
        estimate_uplift_from_share_shift(df, "is_open_access", delta_pp),
        estimate_uplift_from_share_shift(df, "is_uncited", -abs(delta_pp)),
    ]
    return pd.DataFrame(rows).set_index("flag")
