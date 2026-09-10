import pandas as pd

from p36.config import SCENARIO_DEFAULT_DELTA_PP

METRIC_COLUMN = "Field-Weighted Citation Impact"

def estimate_uplift_from_share_shift(
    df: pd.DataFrame,
    flag_column: str,
    delta_pp: float = SCENARIO_DEFAULT_DELTA_PP,
    metric_column: str = METRIC_COLUMN,
) -> dict:
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
    rows = [
        estimate_uplift_from_share_shift(df, "is_q1", delta_pp),
        estimate_uplift_from_share_shift(df, "is_international", delta_pp),
        estimate_uplift_from_share_shift(df, "is_open_access", delta_pp),
        estimate_uplift_from_share_shift(df, "is_uncited", -abs(delta_pp)),
        estimate_uplift_from_share_shift(df, "is_source_overperforming", delta_pp),
    ]
    return pd.DataFrame(rows).set_index("flag")

def client_institution_scenario(
    raw_df: pd.DataFrame,
    university: str,
    delta_pp: float = SCENARIO_DEFAULT_DELTA_PP,
) -> dict:
    from p36.analysis import go8_benchmarking

    flag = go8_benchmarking.institution_partner_flag(raw_df, university)
    scoped = raw_df[raw_df["source_university"] == university].assign(is_high_performing_partner=flag)
    return estimate_uplift_from_share_shift(scoped, "is_high_performing_partner", delta_pp)
