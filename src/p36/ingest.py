"""Load raw QS World University Rankings publication exports.

Source files live in ``data/`` — one .xlsx per Go8 university export. All eight files
share an identical structure (confirmed 2026-08-31, see
data/dictionary/data_dictionary.md for the full column reference):

- Sheet ``Sheet0``.
- Rows 0-18 are file-level export metadata (year range, data source, ...), not data.
- Row 19 is the real header row (70 columns).
- Data rows follow immediately.
- The file ends with exactly two non-data rows: a blank separator, then an Elsevier
  copyright footer. Both are dropped by filtering on a non-null ``EID`` — no genuine
  data row has a null EID.

See .claude/agents/pandas-safety.md for the failure modes this module guards
against: ID columns silently becoming float, the "-" missing-value code being
misread as a valid string, and cross-university duplication (46,969 publications
appear in more than one Go8 export — see data_dictionary.md "Data quality notes").
"""

from pathlib import Path

import pandas as pd

from p36.config import MISSING_VALUE_CODES

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

HEADER_ROW = 19  # 0-indexed row in the source sheet holding the real column names

# Columns that must be read as string, never numeric — Scopus/Institution IDs that
# lose precision as float, pipe-delimited lists of such IDs/codes, and identifier
# fields (Volume, Issue, Article number) that are numeric-looking but not numbers.
# Confirmed by directly auditing the python type of every value in every column
# (not just the pandas dtype label) on the Adelaide export: any of these columns
# that holds exactly one value for a given row is stored by Excel as a bare int,
# and as delimited text otherwise — pandas infers a mixed int/str "object" column
# unless dtype=str is forced here, which surfaces later as a hard-to-diagnose
# failure (e.g. on parquet write) rather than at ingest time. See data_dictionary.md.
ID_COLUMNS: list[str] = [
    "Source ID",
    "EID",
    "PubMed ID",
    "Scopus Author Ids",
    "Volume",
    "Issue",
    "Article number",
    "Institution IDs",
    "Scopus Affiliation IDs",
    "Scopus Author ID First Author",
    "Scopus Author ID Last Author",
    "Scopus Author ID Corresponding Author",
    "Scopus Author ID Single Author",
    "All Science Journal Classification (ASJC) code",
    "Quacquarelli Symonds (QS) Subject area code",
    "Quacquarelli Symonds (QS) Subject code",
    "Times Higher Education (THE) code",
    "ANZSRC FoR (2020) parent code",
    "ANZSRC FoR (2020) code",
    "Topic Cluster number",
    "Topic number",
]


def load_university_export(path: Path) -> pd.DataFrame:
    """Read one university's QS publication export.

    Skips the metadata block, forces missing-value recognition on the ``-``
    sentinel, forces string dtype on every ID-like column so joins downstream do
    not silently fail, and drops the two trailing non-data rows.
    """
    df = pd.read_excel(
        path,
        sheet_name="Sheet0",
        header=HEADER_ROW,
        na_values=MISSING_VALUE_CODES,
        dtype={col: str for col in ID_COLUMNS},
    )
    df = df[df["EID"].notna()].reset_index(drop=True)
    return df


def university_name_from_filename(path: Path) -> str:
    """Derive a readable university name from a source filename.

    e.g. ``QS_World_..._Publications_at_University_of_Sydney.xlsx`` ->
    ``University of Sydney``.
    """
    prefix = "QS_World_University_Rankings_2027_-_Publications_at_"
    return path.stem.removeprefix(prefix).replace("_", " ")


def load_all_universities() -> pd.DataFrame:
    """Read every university export in ``data/`` and concatenate them.

    Adds a ``source_university`` column so each row can be traced back to the
    export it came from. Does **not** de-duplicate — a row here represents one
    university's claim on a publication, and a jointly-authored Go8 paper
    legitimately appears once per contributing university. For any Go8-aggregate
    or cross-university figure, call :func:`deduplicate_by_eid` on the result
    first; per-university figures should use this output as-is.
    """
    frames = []
    for p in sorted(DATA_DIR.glob("*.xlsx")):
        df = load_university_export(p)
        df["source_university"] = university_name_from_filename(p)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def deduplicate_by_eid(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse a multi-university dataframe to one row per unique publication.

    Required before any Go8-aggregate or cross-university benchmarking figure
    (e.g. total distinct Go8 research output, or comparisons in README Analysis
    items 16-17) — without this, 15.1% of rows are duplicates of a publication
    already counted under another university, and every such figure is inflated.

    Do **not** apply this before computing a single university's own output
    figures; a jointly-authored paper legitimately counts toward each
    contributing university's total.
    """
    return df.drop_duplicates(subset="EID", keep="first").reset_index(drop=True)
