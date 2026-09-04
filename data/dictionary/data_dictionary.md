# Data Dictionary

> COMP3888_W11_02_P36 · Publication Intelligence & Research Impact Analysis Platform
> Client deliverable #2. This file is the single source of truth for what every column
> in `src/p36/` means, and must stay in sync with the code — see
> `.claude/agents/data-dictionary-sync.md`, which checks this before every pull request.

## Source files

Eight `.xlsx` exports in `data/`, one per Go8 university, each a Scopus/SciVal export
for "QS World University Rankings 2027". Confirmed identical across all eight files
(inspected 2026-08-31):

| Property | Value |
| --- | --- |
| Year range | 2020 to 2024 |
| Subject classification | QS |
| Filtered by | not filtered |
| Types of publications included | All publication types |
| Self-citations | `-` (not filtered — see Data quality notes) |
| Data source | Scopus |
| Sheet name | `Sheet0` |
| Metadata block | Rows 0–18 (0-indexed): key/value export metadata, not data |
| Header row | Row 19 (0-indexed) — 70 columns |
| Data rows | Immediately follow the header row |
| Trailing rows | Exactly 2 non-data rows at the end of every file: one blank separator row, then one Elsevier copyright footer row. Both must be dropped before use (`df["EID"].notna()` is a reliable filter — no genuine data row has a null EID). |

Row counts as exported (before any de-duplication):

| University | Rows |
| --- | --- |
| University of Melbourne | 66,640 |
| The University of Sydney | 60,664 |
| University of New South Wales | 56,316 |
| Monash University | 56,108 |
| University of Queensland | 53,893 |
| Adelaide University | 36,143 |
| University of Western Australia | 29,422 |
| Australian National University | 26,478 |
| **Total (raw, pre-dedup)** | **385,664** |

## Data quality notes

- **Cross-university duplication.** 46,969 distinct publications (EID) appear in more
  than one university's export — 58,399 rows of overlap — because Go8-internal
  collaborations are exported independently by each institution. Deduplicated total:
  **327,265** unique publications. Not deduplicating inflates any Go8-wide aggregate
  by **15.1%**. One EID appears in as many as 7 of the 8 files.
  **This does not mean per-university figures should be deduplicated** — a
  jointly-authored paper legitimately counts toward each contributing university's
  own output. De-duplication is only correct for a *Go8-aggregate* or
  *cross-university benchmarking* figure (see README Analysis items 16–17). Keep both
  code paths distinct; do not silently apply one dedup rule everywhere.
- **Missing-value sentinel.** The source uses the literal string `-` for "not
  applicable / not available", both in per-row cells (e.g. `Volume`, `Pages` for
  non-journal sources) and in the file-level metadata block. `read_excel` does not
  recognise this — pass `na_values=["-"]` (see `p36.config.MISSING_VALUE_CODES`).
- **`Open Access` is ~46% null** (16,663 of 36,145 in the Adelaide file). Not yet
  confirmed whether null means "not open access" or "status unknown" — needs a
  client/team decision before this column is used in any finding.
- **`Year` is not bounded to the declared "2020 to 2024" export window.** 6 rows
  fall in 2013/2014/2019 (negligible — likely corrigenda/reprints), and 429 rows
  fall in 2025/2026 (plausible, not an error — the export's own "Date exported" is
  14 August 2026). Any year-over-year trend must filter to `p36.config.
  MAIN_YEAR_RANGE` first, or the straggler years (as few as 1 row) produce
  nonsensical percentage changes.
- **Field-level analysis drops rows with no field classification.**
  `Quacquarelli Symonds (QS) Subject area field name` is null on 8,015/327,265
  (2.45%) of deduplicated rows; the alternative `ANZSRC FoR (2020) parent name`
  taxonomy is null on 35,124/327,265 (10.7%) — worse, despite being the
  documented fallback option. `p36.analysis.field_analysis.explode_by_field`
  drops these (there is no field to explode into) and prints the count every
  call so it isn't silent — but every field-level total is against that reduced
  denominator, not the true publication count.
- **Both citation-related percentile columns use "lower is better."**
  `CiteScore percentile (publication year) *` and `Outputs in Top Citation
  Percentiles, per percentile` are Scopus/SciVal-convention percentiles where 1 =
  top 1%, 100 = bottom — the opposite of the everyday reading of "percentile."
  Verified against Field-Weighted Citation Impact — see docs/methodology.md,
  "Percentile direction". Every threshold on these two columns is a `<=`.
- **ID-like columns arrive as `float64` on a naive read.** `Source ID` in particular;
  `Institution IDs`, `Scopus Affiliation IDs`, and the four `Scopus Author ID *`
  columns are pipe-delimited and must never be cast to numeric. Force
  `dtype=str` on all of them at read time (see `src/p36/ingest.py`).
- **Pipe-delimited "code" and "ID" columns silently mix `int` and `str` per row.**
  Confirmed on `Scopus Author Ids`: a single-author paper stores this cell as a bare
  Excel number, a multi-author paper stores it as pipe-delimited text, so pandas
  infers a mixed-type `object` column — this reads fine but fails later (e.g. on
  `to_parquet`) with an opaque error, not at ingest time. The same risk applies to
  every "code" column below that can hold one or several pipe-delimited values:
  `Scopus Author Ids`, ASJC code, QS Subject area code, QS Subject code, THE code,
  ANZSRC FoR parent code, ANZSRC FoR code. `Volume`, `Issue`, and `Article number`
  hit the same failure for a different reason — numeric-looking identifiers, not
  actually numbers. All are forced to `dtype=str` in `src/p36/ingest.py:ID_COLUMNS`,
  a list built by auditing the Python type of every value in every column, not just
  trusting the pandas-inferred dtype label — the label alone hides this class of bug.
- **`EID`** (Scopus Electronic ID, e.g. `2-s2.0-85101171240`) is the only reliable
  unique row identifier and the join key for de-duplication. `Source ID` is not
  unique per publication (it identifies the journal/venue, not the paper).

## Raw columns (from the source QS/Scopus exports)

All columns below are `raw` — none are derived yet. "Nulls allowed" reflects what was
observed in the Adelaide file (36,143 real data rows) and is expected to hold across
the other seven exports given their identical structure.

| Column | Type | Definition | Processing rule | Nulls allowed |
| --- | --- | --- | --- | --- |
| Title | str | Publication title | as exported | No |
| Authors | str | Author names, `\|`-delimited, order matches `Scopus Author Ids` | split on `\|` if per-author rows are needed | No |
| Number of Authors | Int64 | Count of authors on the paper | cast `float64` → nullable `Int64` | No |
| Scopus Author Ids | str | Scopus Author IDs, `\|`-delimited, order matches `Authors` | **force `dtype=str` on read** — single-author rows store this as a bare number | No |
| Year | Int64 | Publication year | cast `float64` → nullable `Int64` | No |
| Full date | date | Exact publication date | parse `YYYY-MM-DD` if a date type is needed | No |
| Scopus Source title | str | Journal / conference / book series name | as exported | No |
| Volume | str | Journal volume | `-` → null (non-journal sources); **force `dtype=str`** — mixed int/str per row | Yes |
| Issue | str | Journal issue | `-` → null; **force `dtype=str`** — mixed int/str per row | Yes |
| Pages | str | Page range | `-` → null (e.g. electronic-only articles) | Yes |
| Article number | str | Article number, used when there is no page range | `-` → null; **force `dtype=str`** — mixed float/int/str per row | Yes |
| ISSN | str | Source ISSN, prefixed `ISSN-` | `-` → null (e.g. books) | Yes |
| Source ID | str | Scopus internal source (journal/venue) identifier | **force `dtype=str` on read** — arrives as `float64` otherwise | No |
| Source type | str | e.g. Journal, Conference Proceeding, Book Series | as exported | No |
| Publisher | str | Publisher name | as exported | Yes |
| Language | str | Publication language | as exported | No |
| SNIP (publication year) | float64 | Source Normalized Impact per Paper, in the paper's year | `-` → null | Yes |
| SNIP percentile (publication year) * | float64 | Percentile rank of SNIP | see export footnote: nearest available year used when exact year is missing | Yes |
| CiteScore (publication year) | float64 | CiteScore of the source, in the paper's year | `-` → null | Yes |
| CiteScore percentile (publication year) * | float64 | Percentile rank of CiteScore | see footnote above | Yes |
| SJR (publication year) | float64 | SCImago Journal Rank | `-` → null | Yes |
| SJR percentile (publication year) * | float64 | Percentile rank of SJR | see footnote above | Yes |
| Field-Weighted View Impact | float64 | Views relative to the field/year/type expectation (1.0 = average) | as exported | Yes |
| Views | Int64 | View/download count | as exported | Yes |
| Citations | Int64 | Total citation count | as exported; **0 is a real count, distinct from a missing value** | No |
| Field-Weighted Citation Impact | float64 | FWCI — citations relative to same field/year/document-type average (1.0 = world average) | as exported | Yes |
| Field-Citation Average | float64 | Average citations for comparable publications | as exported | Yes |
| Outputs in Top Citation Percentiles, per percentile | str | Which top-citation percentile bands the paper falls in | as exported | Yes |
| Field-Weighted Outputs in Top Citation Percentiles, per percentile | str | Field-normalised version of the above | as exported | Yes |
| Main patent families | Int64 | Count of patent families citing this publication | as exported | Yes |
| Policy citations | Int64 | Count of citations from policy documents | as exported | Yes |
| Reference | str | Reference count / reference list for the paper | as exported — **TBC: confirm exact semantics before use** | Yes |
| Abstract | str | Publication abstract | as exported | Yes |
| DOI | str | Digital Object Identifier | as exported | Yes |
| Publication type | str | e.g. Article, Review, Conference Paper | as exported — this is the field `INCLUDED_DOCUMENT_TYPES` (config.py) scopes | No |
| Open Access | str | Open access status/colour | **~46% null — meaning not yet confirmed, see Data quality notes** | Yes |
| EID | str | Scopus Electronic ID — the unique, canonical row identifier | **primary key; force `dtype=str`** | No |
| PubMed ID | str | PMID, if indexed in PubMed | force `dtype=str` | Yes |
| Institutions | str | Author affiliation institution names, `\|`-delimited | as exported | Yes |
| Institution IDs | str | Institution IDs matching `Institutions`, `\|`-delimited | **force `dtype=str` on read** | Yes |
| Sector | str | Institution sector (e.g. Higher education, Government, Corporate) | as exported | Yes |
| Number of Institutions | Int64 | Count of distinct co-author institutions | cast to `Int64` | No |
| Scopus Affiliation IDs | str | Scopus affiliation IDs | force `dtype=str` | Yes |
| Scopus Affiliation names | str | Scopus affiliation names | as exported | Yes |
| Scopus Author ID First Author | str | Scopus Author ID of the first-listed author | force `dtype=str` | Yes |
| Scopus Author ID Last Author | str | Scopus Author ID of the last-listed author | force `dtype=str` | Yes |
| Scopus Author ID Corresponding Author | str | Scopus Author ID of the corresponding author | force `dtype=str` | Yes |
| Scopus Author ID Single Author | str | Populated only when there is exactly one author | force `dtype=str`; null for multi-author papers | Yes |
| Country/Region | str | Co-author countries/regions, `\|`-delimited | as exported — drives International Collaboration Analysis | No |
| Number of Countries/Regions | Int64 | Count of distinct co-author countries | cast to `Int64`; **> 1 defines an internationally collaborative paper** | No |
| All Science Journal Classification (ASJC) code | str | Scopus ASJC subject code(s), `\|`-delimited when a paper has more than one | force `dtype=str` — single-classification rows store this as a bare number | Yes |
| All Science Journal Classification (ASJC) field name | str | ASJC subject field name(s) | as exported | Yes |
| Quacquarelli Symonds (QS) Subject area code | str | QS broad subject area code(s) | force `dtype=str` | Yes |
| Quacquarelli Symonds (QS) Subject area field name | str | QS broad subject area name | as exported — candidate field for Faculty/Field Analysis | Yes |
| Quacquarelli Symonds (QS) Subject code | str | QS narrow subject code(s) | force `dtype=str` | Yes |
| Quacquarelli Symonds (QS) Subject field name | str | QS narrow subject field name | as exported | Yes |
| Times Higher Education (THE) code | str | THE subject code(s) | force `dtype=str` | Yes |
| Times Higher Education (THE) field name | str | THE subject field name | as exported | Yes |
| ANZSRC FoR (2020) parent code | str | ANZSRC Field of Research, 2-digit parent code(s) | force `dtype=str` | Yes |
| ANZSRC FoR (2020) parent name | str | ANZSRC FoR parent field name | as exported | Yes |
| ANZSRC FoR (2020) code | str | ANZSRC FoR, 4-digit code(s) | force `dtype=str` | Yes |
| ANZSRC FoR (2020) name | str | ANZSRC FoR field name | as exported | Yes |
| Sustainable Development Goals (2025) | str | UN SDG(s) the paper is mapped to | as exported | Yes |
| Topic Cluster name | str | SciVal Topic Cluster name | as exported | Yes |
| Topic Cluster number | str | SciVal Topic Cluster ID | force `dtype=str` | Yes |
| Topic Cluster Prominence Percentile | float64 | Percentile rank of the Topic Cluster's prominence | as exported | Yes |
| Topic name | str | SciVal Topic name (finer-grained than Topic Cluster) | as exported | Yes |
| Topic number | str | SciVal Topic ID | force `dtype=str` | Yes |
| Topic Prominence Percentile | float64 | Percentile rank of the Topic's prominence | as exported | Yes |
| Publication link to Topic strength | float64 | Strength of this publication's link to its assigned Topic | as exported | Yes |

## Derived columns (computed by src/p36/)

All added by `p36.metrics.add_derived_flags` (`src/p36/metrics/metrics.py`) — the
single place these are computed; no analysis module recomputes them.

| Column | Type | Definition | Source | Processing rule | Nulls allowed |
| --- | --- | --- | --- | --- | --- |
| is_retracted | bool | `Publication type == "Retracted"` | derived | direct comparison | No |
| is_q1 | boolean (nullable) | Source is Q1: `CiteScore percentile <= Q1_CITESCORE_PERCENTILE_MAX` (25). **PROVISIONAL** — see methodology.md | derived | `<=` comparison; `pd.NA` where CiteScore percentile is null (Q1 status undefined, not false) | Yes — when source has no CiteScore percentile |
| is_top_decile | bool | `Outputs in Top Citation Percentiles <= TOP_DECILE_PERCENTILE_MAX` (10) | derived | `<=` comparison; column has no nulls | No |
| is_top_1_percent | bool | `Outputs in Top Citation Percentiles <= TOP_1_PERCENT_PERCENTILE_MAX` (1) | derived | `<=` comparison | No |
| is_international | bool | `Number of Countries/Regions >= INTERNATIONAL_COLLABORATION_MIN_COUNTRIES` (2) | derived | `>=` comparison | No |
| is_multi_institution | bool | `Number of Institutions >= INSTITUTIONAL_COLLABORATION_MIN_INSTITUTIONS` (2) | derived | `>=` comparison | No |
| is_uncited | bool | `Citations == 0` | derived | direct comparison | No |
| is_open_access | bool | `Open Access` is non-null. **PROVISIONAL** — assumes null means "not open access", not "status unknown"; see methodology.md, Open access status | derived | `.notna()` | No |
