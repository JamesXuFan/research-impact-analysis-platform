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

def fit_field_interaction_model(model_df: pd.DataFrame, driver: str):
    other = {"is_international", "is_q1", "is_open_access"} - {driver}
    formula = (
        "Q('Field-Weighted Citation Impact') ~ "
        f"{driver} * C({PRIMARY_FIELD_COLUMN}) + {' + '.join(sorted(other))} "
        f"+ log_authors + log_institutions + Year + C(Q('{DOCUMENT_TYPE_COLUMN}'))"
    )
    model = smf.ols(formula, data=model_df)
    return model.fit(cov_type="HC3")

def _dummy_category(term: str, prefix: str) -> str:
    rest = term[len(prefix):]
    if rest.startswith("[T."):
        rest = rest[len("[T."):]
    return rest.rstrip("]")

def field_interaction_summary_table(fit, driver: str) -> pd.DataFrame:
    """Per-field total effect of `driver` (base coefficient, plus that field's
    interaction term where one exists — the reference field has none, since
    it's absorbed into the base coefficient itself)."""
    field_prefix = f"C({PRIMARY_FIELD_COLUMN})"
    base_term = f"{driver}[T.True]"
    interaction_prefix = f"{base_term}:{field_prefix}"

    all_fields = set(fit.model.data.frame[PRIMARY_FIELD_COLUMN].unique())
    interaction_terms = {
        _dummy_category(t, interaction_prefix): t
        for t in fit.params.index
        if t.startswith(interaction_prefix)
    }
    reference_field = next(iter(all_fields - interaction_terms.keys()))

    def _contrast_row(extra_term: str | None) -> dict:
        contrast = np.zeros(len(fit.params))
        contrast[fit.params.index.get_loc(base_term)] = 1
        if extra_term is not None:
            contrast[fit.params.index.get_loc(extra_term)] = 1
        effect = contrast @ fit.params.values
        se = np.sqrt(contrast @ fit.cov_params().values @ contrast)
        p_value = fit.pvalues[base_term] if extra_term is None else fit.pvalues[extra_term]
        return {
            "effect": effect,
            "std_err": se,
            "p_value": p_value,
            "ci_low": effect - 1.96 * se,
            "ci_high": effect + 1.96 * se,
        }

    rows = {reference_field: _contrast_row(None)}
    for field, term in interaction_terms.items():
        rows[field] = _contrast_row(term)

    table = pd.DataFrame(rows).T
    table.index.name = "field"
    return table.sort_values("effect", ascending=False)

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
