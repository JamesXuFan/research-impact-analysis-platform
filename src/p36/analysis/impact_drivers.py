"""README Analysis item 14 — Integrated Research Impact Driver Analysis.

Where items 3, 6, 9, and 16 look at one factor at a time (Q1 status, field,
international collaboration, ...), this module puts them in a single regression
so each factor's association with impact is estimated *holding the others
constant* — international collaboration and Q1 status are themselves correlated,
so a one-factor-at-a-time comparison risks attributing one factor's effect to
another (see .claude/agents/finding-checker.md, "correlation stated as
causation").

**This is still an observational, cross-sectional regression, not an experiment.**
A significant coefficient is an association conditional on the other included
predictors, not a causal effect — do not present it as one (see docs/methodology.md
and finding-checker.md). Every finding drawn from this model must go through
finding-checker.md before being written up.

Target: `Field-Weighted Citation Impact` — already field/year/document-type
normalised, so it can be compared and pooled across fields directly (unlike raw
Citations). Predictors use each publication's **primary** (first-listed) field
only, as a fixed effect — using every pipe-delimited field would duplicate rows
(see p36.analysis.field_analysis) and bias the standard errors.
"""

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

PRIMARY_FIELD_COLUMN = "primary_field"
DOCUMENT_TYPE_COLUMN = "Publication type"


def build_driver_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Build the model-ready dataframe: one row per publication, predictors and
    target with no missing values. Returns the dataframe alongside dropping
    diagnostics are the caller's responsibility — compare len(input) vs
    len(output) and report the sample restriction in any write-up.

    Expects `df` to already carry `is_international`, `is_q1`, and
    `is_open_access` from p36.metrics.add_derived_flags — this function does
    not recompute them, to avoid a second, independently-maintained definition
    of any flag (see .claude/agents/metrics-consistency.md). Note in
    particular: `is_open_access` treats a null `Open Access` as "not open
    access" — **PROVISIONAL**, not confirmed by the client — see
    p36.config.OPEN_ACCESS_NULL_MEANS_NOT_OA and docs/methodology.md.
    """
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
    # is_q1 is nullable boolean (pd.NA where CiteScore percentile is missing);
    # dropna() above already removed those rows, so this is now a plain bool.
    model_df["is_q1"] = model_df["is_q1"].astype(bool)
    return model_df


def fit_impact_driver_model(model_df: pd.DataFrame):
    """OLS: Field-Weighted Citation Impact ~ international + Q1 + open access +
    log(authors) + log(institutions) + year + primary-field fixed effects +
    document-type fixed effects. HC3 robust standard errors — FWCI is
    heavy-tailed, so homoskedastic OLS standard errors would understate
    uncertainty. Returns the fitted statsmodels RegressionResultsWrapper (use
    .summary() for the full diagnostic output, driver_summary_table() for the
    main predictors, or document_type_summary_table() for the document-type
    terms specifically).

    Document type (`Publication type`) is included as a fixed effect for
    README item 14's "Document Type -> Citation Impact" chain. FWCI is
    already document-type-normalised by SciVal's own methodology (see module
    docstring), so a naive expectation is that this term should wash out to
    ~0 — it does not (verified 2026-09-03: relative to Article, Conference
    Paper and Chapter carry statistically significant *positive* coefficients
    of around +1.0 and +0.76, Data Paper a significant *negative* ~-1.3; see
    document_type_summary_table). Report that as the actual finding — FWCI's
    normalisation does not fully equalise mean impact across document types
    in this dataset — rather than assuming it must be near-zero. `Q(...)`
    wraps the column name for patsy because it contains a space.
    """
    formula = (
        "Q('Field-Weighted Citation Impact') ~ "
        "is_international + is_q1 + is_open_access + log_authors + log_institutions "
        f"+ Year + C({PRIMARY_FIELD_COLUMN}) + C(Q('{DOCUMENT_TYPE_COLUMN}'))"
    )
    model = smf.ols(formula, data=model_df)
    return model.fit(cov_type="HC3")


def _fixed_effect_table(fit, prefix: str) -> pd.DataFrame:
    """Shared helper: coefficient/SE/p-value/95% CI for every term whose name
    starts with `prefix`."""
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
    """Coefficient, standard error, p-value, and 95% CI for every non-fixed-
    effect predictor — both the field and document-type fixed-effect terms
    are excluded (there can be dozens of fields; inspect fit.summary()
    directly, or document_type_summary_table() below, for those). Sorted by
    absolute coefficient size, largest first.

    Excludes by the two known fixed-effect prefixes specifically, not a bare
    "starts with C(" check — the latter would also silently swallow any
    future predictor a caller wraps in patsy's C(...) for an unrelated
    reason (e.g. forcing a numeric column to be treated categorically).
    """
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
    """Coefficient, SE, p-value and 95% CI for each document-type fixed-effect
    term, relative to the baseline category statsmodels drops (Article,
    alphabetically first). Small enough (~8 categories, vs. dozens of fields)
    to show on its own — this table *is* the answer to README item 14's
    "Document Type -> Citation Impact" question: Conference Paper and Chapter
    both run significantly above Article-level mean FWCI, Data Paper
    significantly below, despite FWCI already being document-type-normalised
    — see fit_impact_driver_model's docstring. Editorial (3), Letter (3),
    Note (9), and Book (14) have very wide CIs — that's their count in the
    *regression sample*, not the full dataset: Book has 2,491 publications
    overall (see p36.config.INCLUDED_DOCUMENT_TYPES), but 99.4% of them have
    no CiteScore percentile (a journal-level metric that mostly doesn't apply
    to books) and are dropped by build_driver_dataset's dropna — same for
    Chapter, 86.1% dropped, though its remaining 2,746 rows are enough for a
    tight CI. Read the Book/Editorial/Letter/Note coefficients as describing
    that small, non-random surviving slice, not document-type publishing as
    a whole.
    """
    prefix = f"C(Q('{DOCUMENT_TYPE_COLUMN}'))"
    table = _fixed_effect_table(fit, prefix)

    def _category(term: str) -> str:
        # e.g. "C(Q('Publication type'))[T.Review]" -> "Review"
        rest = term[len(prefix):]
        if rest.startswith("[T."):
            rest = rest[len("[T."):]
        return rest.rstrip("]")

    table.index = [_category(i) for i in table.index]
    return table.sort_values("coefficient", ascending=False)
