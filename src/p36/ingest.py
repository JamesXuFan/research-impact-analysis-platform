from pathlib import Path

import pandas as pd

from p36.config import MISSING_VALUE_CODES

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

HEADER_ROW = 19

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
    prefix = "QS_World_University_Rankings_2027_-_Publications_at_"
    return path.stem.removeprefix(prefix).replace("_", " ")

def load_all_universities() -> pd.DataFrame:
    frames = []
    for p in sorted(DATA_DIR.glob("*.xlsx")):
        df = load_university_export(p)
        df["source_university"] = university_name_from_filename(p)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)

def deduplicate_by_eid(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates(subset="EID", keep="first").reset_index(drop=True)
