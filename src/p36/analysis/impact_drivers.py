import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

PRIMARY_FIELD_COLUMN = "primary_field"
DOCUMENT_TYPE_COLUMN = "Publication type"

def build_driver_dataset(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()
    working[PRIMARY_FIELD_COLUMN] = (
        working["Quacquarelli Symonds (QS) Subject area field name"].str.split("|").str[0].str.strip()
    )
    working["log_authors"] = np.log1p(working["Number of Authors"])
    working["log_institutions"] = np.log1p(working["Number of Institutions"])

    columns = [
        "Field-Weighted Citation Impact",
        "is_international",
        "is_q1",
        "is_open_access",
        "log_authors",
        "log_institutions",
        "Year",
        PRIMARY_FIELD_COLUMN,
        DOCUMENT_TYPE_COLUMN,
    ]
    model_df = working[columns].dropna()
    model_df["is_q1"] = model_df["is_q1"].astype(bool)
    return model_df

def fit_impact_driver_model(model_df: pd.DataFrame):
    formula = (
        "Q('Field-Weighted Citation Impact') ~ "
        "is_international + is_q1 + is_open_access + log_authors + log_institutions "
        f"+ Year + C({PRIMARY_FIELD_COLUMN}) + C(Q('{DOCUMENT_TYPE_COLUMN}'))"
    )
    model = smf.ols(formula, data=model_df)
    return model.fit(cov_type="HC3")

def _fixed_effect_table(fit, prefix: str) -> pd.DataFrame:
    terms = [p for p in fit.params.index if p.startswith(prefix)]
    return pd.DataFrame(
        {
            "coefficient": fit.params[terms],
            "std_err": fit.bse[terms],
            "p_value": fit.pvalues[terms],
            "ci_low": fit.conf_int().loc[terms, 0],
            "ci_high": fit.conf_int().loc[terms, 1],
        }
    )

_FIXED_EFFECT_PREFIXES = (f"C({PRIMARY_FIELD_COLUMN}", f"C(Q('{DOCUMENT_TYPE_COLUMN}'))")

def driver_summary_table(fit) -> pd.DataFrame:
    params = fit.params
    non_fe = [p for p in params.index if not p.startswith(_FIXED_EFFECT_PREFIXES)]
    table = pd.DataFrame(
        {
            "coefficient": fit.params[non_fe],
            "std_err": fit.bse[non_fe],
            "p_value": fit.pvalues[non_fe],
            "ci_low": fit.conf_int().loc[non_fe, 0],
            "ci_high": fit.conf_int().loc[non_fe, 1],
        }
    )
    return table.reindex(table["coefficient"].abs().sort_values(ascending=False).index)

def document_type_summary_table(fit) -> pd.DataFrame:
    prefix = f"C(Q('{DOCUMENT_TYPE_COLUMN}'))"
    table = _fixed_effect_table(fit, prefix)

    def _category(term: str) -> str:
        rest = term[len(prefix):]
        if rest.startswith("[T."):
            rest = rest[len("[T."):]
        return rest.rstrip("]")

    table.index = [_category(i) for i in table.index]
    return table.sort_values("coefficient", ascending=False)

def fit_interaction_model(model_df: pd.DataFrame):
    formula = (
        "Q('Field-Weighted Citation Impact') ~ "
        "is_international * is_q1 + is_open_access + log_authors + log_institutions "
        f"+ Year + C({PRIMARY_FIELD_COLUMN}) + C(Q('{DOCUMENT_TYPE_COLUMN}'))"
    )
    model = smf.ols(formula, data=model_df)
    return model.fit(cov_type="HC3")

def interaction_summary_table(fit) -> pd.DataFrame:
    terms = [t for t in fit.params.index if t in ("is_international[T.True]", "is_q1[T.True]") or ":" in t]
    return pd.DataFrame(
        {
            "coefficient": fit.params[terms],
            "std_err": fit.bse[terms],
            "p_value": fit.pvalues[terms],
            "ci_low": fit.conf_int().loc[terms, 0],
            "ci_high": fit.conf_int().loc[terms, 1],
        }
    )

def combination_summary(df: pd.DataFrame) -> pd.DataFrame:
    from p36.metrics import mean_fwci, top_decile_share

    scoped = df.dropna(subset=["is_q1"]).copy()
    scoped["is_q1"] = scoped["is_q1"].astype(bool)
    grouped = scoped.groupby(["is_q1", "is_international", "is_open_access"], observed=True)
    table = pd.DataFrame(
        {
            "publications": grouped.size(),
            "mean_fwci": grouped.apply(mean_fwci, include_groups=False),
            "top_decile_share": grouped.apply(top_decile_share, include_groups=False),
            "uncited_share": grouped["is_uncited"].mean(),
        }
    )
    return table.sort_values("mean_fwci", ascending=False)
