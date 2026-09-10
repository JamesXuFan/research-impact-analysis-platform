import pandas as pd

from p36.config import CLIENT_UNIVERSITY, GO8_UNIVERSITIES, HIGH_PERFORMING_PARTNER_MIN_PUBLICATIONS, MAIN_YEAR_RANGE
from p36.metrics import mean_fwci, period_growth, q1_share, top_decile_share

def benchmark_summary(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby("source_university")
    summary = pd.DataFrame(
        {
            "publications": grouped.size(),
            "mean_fwci": grouped.apply(mean_fwci, include_groups=False),
            "q1_share": grouped.apply(q1_share, include_groups=False),
            "top_decile_share": grouped.apply(top_decile_share, include_groups=False),
            "international_collaboration_share": grouped["is_international"].mean(),
            "mean_institutions_per_paper": grouped["Number of Institutions"].mean(),
        }
    )
    order = [CLIENT_UNIVERSITY] + [u for u in GO8_UNIVERSITIES if u != CLIENT_UNIVERSITY]
    return summary.reindex(order)

def field_gap_vs_peers(
    exploded_df: pd.DataFrame, client: str = CLIENT_UNIVERSITY
) -> pd.DataFrame:
    from p36.analysis.field_analysis import FIELD_COLUMN_EXPLODED

    is_client = exploded_df["source_university"] == client
    client_fwci = exploded_df[is_client].groupby(FIELD_COLUMN_EXPLODED).apply(mean_fwci, include_groups=False)
    peer_fwci = exploded_df[~is_client].groupby(FIELD_COLUMN_EXPLODED).apply(mean_fwci, include_groups=False)
    out = pd.DataFrame({"client_fwci": client_fwci, "peer_avg_fwci": peer_fwci})
    out["gap"] = out["client_fwci"] - out["peer_avg_fwci"]
    return out.sort_values("gap", ascending=False)

def growth_by_university(
    df: pd.DataFrame, year_range: tuple[int, int] = MAIN_YEAR_RANGE
) -> pd.Series:
    return df.groupby("source_university").apply(
        period_growth, year_range=year_range, include_groups=False
    ).sort_values(ascending=False)

def top_countries_by_university(
    df: pd.DataFrame, university: str, top_n: int = 10
) -> pd.Series:
    scoped = df[(df["source_university"] == university) & df["Country/Region"].notna()]
    countries = scoped["Country/Region"].str.split("|").explode().str.strip()
    countries = countries[countries != "Australia"]
    return countries.value_counts().head(top_n)

def journal_pattern_by_university(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("source_university")["Source type"]
        .value_counts(normalize=True)
        .unstack("Source type", fill_value=0)
    )

def _exploded_partners(df: pd.DataFrame, university: str = CLIENT_UNIVERSITY) -> pd.DataFrame:
    scoped = df[df["source_university"] == university].dropna(subset=["Institutions"]).copy()
    scoped["_institution"] = scoped["Institutions"].str.split("|")
    exploded = scoped.explode("_institution")
    exploded["_institution_key"] = exploded["_institution"].str.strip().str.casefold()
    exploded = exploded[exploded["_institution_key"] != ""]
    exploded = exploded[exploded["_institution_key"] != university.strip().casefold()]
    is_dup_within_publication = pd.MultiIndex.from_arrays([exploded.index, exploded["_institution_key"]]).duplicated()
    return exploded[~is_dup_within_publication]

def _institution_level_gap(
    df: pd.DataFrame,
    university: str = CLIENT_UNIVERSITY,
    min_publications: int = HIGH_PERFORMING_PARTNER_MIN_PUBLICATIONS,
) -> pd.DataFrame:
    exploded = _exploded_partners(df, university)
    university_mean = mean_fwci(df[df["source_university"] == university])

    display_name = (
        exploded.groupby(["_institution_key", "_institution"])
        .size()
        .rename("_n")
        .reset_index()
        .sort_values("_n", ascending=False)
        .drop_duplicates("_institution_key")
        .set_index("_institution_key")["_institution"]
        .str.strip()
    )

    grouped = exploded.groupby("_institution_key")
    table = pd.DataFrame(
        {
            "publications": grouped.size(),
            "mean_fwci": grouped.apply(mean_fwci, include_groups=False),
        }
    )
    table = table[table["publications"] >= min_publications].copy()
    table["institution"] = table.index.map(display_name)
    table["university_mean_fwci"] = university_mean
    table["gap"] = table["mean_fwci"] - university_mean
    return table.sort_values("gap", ascending=False)

def institution_partner_performance(
    df: pd.DataFrame,
    university: str = CLIENT_UNIVERSITY,
    min_publications: int = HIGH_PERFORMING_PARTNER_MIN_PUBLICATIONS,
) -> pd.DataFrame:
    table = _institution_level_gap(df, university, min_publications)
    return table.set_index("institution")

def institution_partner_flag(
    df: pd.DataFrame,
    university: str = CLIENT_UNIVERSITY,
    min_publications: int = HIGH_PERFORMING_PARTNER_MIN_PUBLICATIONS,
) -> pd.Series:
    performance = _institution_level_gap(df, university, min_publications)
    high_performing = set(performance.index[performance["gap"] > 0])
    qualifying = set(performance.index)

    exploded = _exploded_partners(df, university)
    is_qualifying = exploded["_institution_key"].isin(qualifying)
    is_high_performing = exploded["_institution_key"].isin(high_performing)
    has_qualifying = is_qualifying.groupby(exploded.index).any()
    has_high_performing = is_high_performing.groupby(exploded.index).any()

    flag = pd.Series(pd.NA, index=df.index, dtype="boolean")
    flag.loc[has_qualifying.index[has_qualifying]] = False
    flag.loc[has_high_performing.index[has_high_performing]] = True
    return flag
