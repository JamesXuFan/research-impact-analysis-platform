import pandas as pd

from p36.config import FRACTIONAL_FIELD_COUNTING, MAIN_YEAR_RANGE
from p36.metrics import mean_fwci, period_growth, q1_share, top_decile_share

FIELD_COLUMN = "Quacquarelli Symonds (QS) Subject area field name"
FIELD_COLUMN_EXPLODED = "field"

def explode_by_field(df: pd.DataFrame, field_col: str = FIELD_COLUMN) -> pd.DataFrame:
    if FRACTIONAL_FIELD_COUNTING:
        raise NotImplementedError(
            "FRACTIONAL_FIELD_COUNTING=True has no implementation yet — the "
            "weighting rule (e.g. 1/N per field) has not been confirmed by the "
            "client. See docs/methodology.md, Multi-field publications."
        )
    dropped = df[field_col].isna().sum()
    if dropped:
        print(
            f"explode_by_field: dropping {dropped}/{len(df)} rows "
            f"({dropped / len(df):.1%}) with no {field_col!r}"
        )
    working = df.dropna(subset=[field_col]).copy()
    working[field_col] = working[field_col].str.split("|")
    exploded = working.explode(field_col)
    exploded[FIELD_COLUMN_EXPLODED] = exploded[field_col].str.strip()
    return exploded

def field_summary(exploded_df: pd.DataFrame) -> pd.DataFrame:
    grouped = exploded_df.groupby(FIELD_COLUMN_EXPLODED)
    summary = pd.DataFrame(
        {
            "publications": grouped.size(),
            "mean_fwci": grouped.apply(mean_fwci, include_groups=False),
            "q1_share": grouped.apply(q1_share, include_groups=False),
            "top_decile_share": grouped.apply(top_decile_share, include_groups=False),
            "uncited_share": grouped["is_uncited"].mean(),
        }
    )
    return summary.sort_values("publications", ascending=False)

def volume_vs_impact_quadrant(summary: pd.DataFrame) -> pd.DataFrame:
    out = summary.copy()
    volume_median = out["publications"].median()
    impact_median = out["mean_fwci"].median()
    out["volume_band"] = out["publications"].ge(volume_median).map({True: "high", False: "low"})
    out["impact_band"] = out["mean_fwci"].ge(impact_median).map({True: "high", False: "low"})
    out["quadrant"] = out["volume_band"] + " volume / " + out["impact_band"] + " impact"
    return out

def field_trend(
    exploded_df: pd.DataFrame, year_range: tuple[int, int] = MAIN_YEAR_RANGE
) -> pd.DataFrame:
    lo, hi = year_range
    scoped = exploded_df[exploded_df["Year"].between(lo, hi)]
    return scoped.groupby([FIELD_COLUMN_EXPLODED, "Year"]).size().unstack("Year", fill_value=0)

def field_growth(exploded_df: pd.DataFrame, year_range: tuple[int, int] = MAIN_YEAR_RANGE) -> pd.Series:
    return exploded_df.groupby(FIELD_COLUMN_EXPLODED).apply(
        period_growth, year_range=year_range, include_groups=False
    ).sort_values(ascending=False)

COLLABORATION_APPROACH_COLUMN = "collaboration_approach"

def add_collaboration_approach(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df[COLLABORATION_APPROACH_COLUMN] = "Domestic, single institution"
    df.loc[df["is_multi_institution"], COLLABORATION_APPROACH_COLUMN] = "Domestic, multi-institution"
    df.loc[df["is_international"], COLLABORATION_APPROACH_COLUMN] = "International"
    return df

def collaboration_approach_by_field(exploded_df: pd.DataFrame) -> pd.DataFrame:
    from p36.metrics import mean_fwci

    grouped = exploded_df.groupby([FIELD_COLUMN_EXPLODED, COLLABORATION_APPROACH_COLUMN], observed=True)
    table = pd.DataFrame(
        {
            "publications": grouped.size(),
            "mean_fwci": grouped.apply(mean_fwci, include_groups=False),
        }
    )
    return table
