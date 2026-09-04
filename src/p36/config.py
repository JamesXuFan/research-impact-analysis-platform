"""Named constants for the p36 pipeline.

Every threshold, cutoff, and magic number used in analysis code must be defined here,
not hard-coded inline (see .claude/agents/metrics-consistency.md). Where a value is
provisional — awaiting a client answer — it is marked as such below; do not treat a
provisional value as settled anywhere else in the codebase.

Update docs/methodology.md whenever a value here changes meaning, not just when it
changes number.
"""

# --- Missing-value handling -------------------------------------------------

# The source QS exports use "-" as the missing-value sentinel. Pass this to
# pandas.read_excel(na_values=MISSING_VALUE_CODES) on every ingest call.
MISSING_VALUE_CODES = ["-"]

# --- Percentile direction — VERIFIED, not provisional -----------------------
#
# Both `CiteScore percentile (publication year) *` and `Outputs in Top Citation
# Percentiles, per percentile` use the Scopus/SciVal convention where LOWER is
# BETTER: a value of 1 means "top 1%", a value of 100 means bottom. This is the
# opposite of the everyday reading of "percentile" and was confirmed empirically
# (2026-09-02) by checking mean Field-Weighted Citation Impact — unambiguous,
# 1.0 = world average, higher = better — across percentile buckets:
#
#   CiteScore percentile (0,10]   -> mean FWCI 2.50
#   CiteScore percentile (75,100] -> mean FWCI 0.64
#   Top Citation Percentiles (0,1]    -> mean FWCI 13.96
#   Top Citation Percentiles (75,100] -> mean FWCI 0.00
#
# Every threshold below on these two columns is therefore a "<=", never a ">=".
# Get this backwards and every Q1 / highly-cited figure in the project inverts.

# --- Q1 journal definition (direction verified; exact cutoff PROVISIONAL) ---

# A publication is Q1 if its source's CiteScore percentile is <= this value.
# 25 is the standard "top quartile" reading of CiteScore percentile. Client has
# not yet confirmed whether Q1 should instead be based on an SJR quartile
# (`SJR percentile (publication year) *`, same low-is-better direction) —
# the two do not always agree on the same journal.
Q1_CITESCORE_PERCENTILE_MAX = 25  # PROVISIONAL (basis: CiteScore vs SJR)

# --- CiteScore quartile bucketing (PROVISIONAL, same basis as Q1) -----------

# Buckets `CiteScore percentile` into Q1-Q4 tiers for "compare citation
# performance across Q1, Q2, Q3, Q4" (README item 3, sub-questions the binary
# is_q1 flag alone can't answer). Q1's own upper bound (25) is reused as the
# first cut point, so this is consistent with, not an alternative to,
# Q1_CITESCORE_PERCENTILE_MAX above. The same open question (CiteScore vs SJR
# basis) applies to every tier boundary here, not just the Q1 one.
CITESCORE_QUARTILE_BOUNDS = [0, 25, 50, 75, 100]  # PROVISIONAL, same basis as Q1
CITESCORE_QUARTILE_LABELS = ["Q1", "Q2", "Q3", "Q4"]

# Minimum publications a Scopus source (journal) needs within one CiteScore
# quartile before its mean FWCI is reported in an "overperforming within tier"
# comparison (README item 3: "are there journals ... that receive more
# citations than would be expected for that tier?") — below this, a single
# highly-cited paper can make a small source look like an outlier by chance.
# Not from the brief; a sample-size judgment call, flagged like any other
# analysis-design threshold.
OVERPERFORMING_SOURCE_MIN_PUBLICATIONS = 10

# --- Highly-cited / top-decile share (direction verified) -------------------

# A publication counts as "highly cited" / top-decile if
# `Outputs in Top Citation Percentiles, per percentile` <= this value. This
# column is already a per-publication, field/year/type-normalised percentile
# computed by SciVal — do not recompute it from raw Citations.
TOP_DECILE_PERCENTILE_MAX = 10

# A stricter "world-leading" band used where a sub-question asks specifically
# about top-1% performance (e.g. README Analysis item 16).
TOP_1_PERCENT_PERCENTILE_MAX = 1

# --- Citation window (PROVISIONAL — awaiting client confirmation) ----------

# Any year-by-year average-citation trend is expected to show an artificial fall in
# its most recent years because those publications have not had time to accumulate
# citations. Client has not confirmed how many trailing years to exclude, or whether
# to exclude them at all.
CITATION_WINDOW_TRAILING_YEARS_EXCLUDED = 2  # PROVISIONAL

# --- Self-citations (PROVISIONAL — awaiting client confirmation) -----------

# Whether self-citations (author citing their own prior work) are included in citation
# counts. The source export's own metadata field for this ("Self-citations") is "-"
# on all eight files, i.e. no filter was applied at export time — so citation counts
# as they stand include self-citations. That is a fact about what was exported, not
# a team decision about what should be reported; the client has not confirmed whether
# self-citations should be excluded downstream.
EXCLUDE_SELF_CITATIONS = False  # PROVISIONAL

# --- Document type scope (PROVISIONAL — awaiting client confirmation) ------

# Observed values in `Publication type` (2026-09-02, deduplicated dataset):
# Article (246,816), Review (34,017), Conference Paper (23,463), Chapter (20,128),
# Book (2,491), Data Paper (285), Retracted (48), Note (9), Editorial (5), Letter (3).
# Client has not confirmed which of these are in scope for publication and citation
# metrics. INCLUDED_DOCUMENT_TYPES = None means "everything, no filter applied yet".
INCLUDED_DOCUMENT_TYPES = None  # PROVISIONAL — None means "not yet decided"

# Whether to drop the 48 rows with Publication type == "Retracted". Defaults to
# excluding them (a retracted paper is not a valid piece of research output to
# report performance on) but this has not been put to the client as a decision —
# treat it as provisional like everything else in this section, and do not present
# it in a finding as an uncontroversial fact.
EXCLUDE_RETRACTED = True  # PROVISIONAL

# --- Fractional counting (PROVISIONAL — awaiting client confirmation) ------

# Whether a publication spanning multiple research fields is counted whole in each
# field (duplicated) or fractionally (split so it sums to 1 across fields). This is
# a live issue, not a theoretical one: on this dataset, a substantial share of rows
# have a pipe-delimited (multi-value) `Quacquarelli Symonds (QS) Subject area field
# name` — e.g. "Natural Sciences| Engineering & Technology". Client has not confirmed.
FRACTIONAL_FIELD_COUNTING = False  # PROVISIONAL

# --- Year range -------------------------------------------------------------

# The export's declared "Year range" metadata is "2020 to 2024" on all 8 files,
# and that is where the bulk of rows sit (63,594-68,202 per year). But `Year`
# is not actually bounded to that range: 6 rows fall in 2013/2014/2019 (likely
# corrigenda/reprints keeping an original publication year — negligible), and
# 429 rows fall in 2025/2026 (plausible, not obviously erroneous, given the
# export's own "Date exported" of 14 August 2026 — these are simply the most
# recent indexed publications, not a data error). Verified 2026-09-02.
#
# Any year-over-year trend (growth rate, publication counts by year) should
# filter to this range first — the straggler years have so few rows that a
# naive groupby-year produces nonsensical percentage changes (a 2019 count of
# 4 makes the 2019->2020 "growth rate" a four-digit percentage, not a real
# trend). Use MAIN_YEAR_RANGE, not the full unfiltered Year column, whenever a
# finding is about a trend over time rather than a single-year total.
MAIN_YEAR_RANGE = (2020, 2024)  # inclusive

# --- International collaboration ---------------------------------------------

# A publication is internationally collaborative if its author affiliations span
# at least this many distinct countries/regions (`Number of Countries/Regions >=
# INTERNATIONAL_COLLABORATION_MIN_COUNTRIES`). A domestic-only Australian paper
# has Number of Countries/Regions == 1 (Australia itself is counted) — verified
# on the data, not provisional. The threshold is named MIN_COUNTRIES and compared
# with >=, not > — a publication with exactly 2 countries (the minimum) already
# counts as international.
INTERNATIONAL_COLLABORATION_MIN_COUNTRIES = 2

# --- Institutional collaboration ---------------------------------------------

# Unlike international collaboration, this is not operationalised as a binary
# threshold — "institutional collaboration" is reported as the mean/distribution
# of `Number of Institutions` directly (e.g. go8_benchmarking.benchmark_summary's
# mean_institutions_per_paper), and as log1p(Number of Institutions) when used as
# a regression predictor (item 14) to reduce right-skew. See docs/methodology.md.

# --- Open access status (PROVISIONAL — awaiting client confirmation) --------

# `Open Access` is ~46% null in the source data. OPEN_ACCESS_NULL_MEANS_NOT_OA
# encodes the working assumption that null means "not open access via any
# recognised route" (Scopus/SciVal convention: this field is populated only when
# an OA route is detected) rather than "status unknown". This has NOT been
# confirmed by the client — see data_dictionary.md, Data quality notes. Any
# is_open_access flag or finding built on this column must carry that caveat.
OPEN_ACCESS_NULL_MEANS_NOT_OA = True  # PROVISIONAL

# --- Growth / trend analysis -------------------------------------------------

# Bucket edges for "how many countries does this publication's collaboration
# span" (used by international_collaboration.impact_by_collaboration_breadth):
# 1 = domestic only, then 2, 3, 4+.
COLLABORATION_BREADTH_BINS = [0, 1, 2, 3]

# Default percentage-point shift used by scenario_analysis.scenario_table when
# the caller doesn't specify one (README Analysis item 17's own examples use 5%).
SCENARIO_DEFAULT_DELTA_PP = 0.05

# --- Scope: which universities, and which one is the client -----------------

# source_university values as produced by p36.ingest.university_name_from_filename.
GO8_UNIVERSITIES = [
    "Adelaide University",
    "Australian National University",
    "Monash University",
    "The University of Sydney",
    "University of Melbourne",
    "University of New South Wales",
    "University of Queensland",
    "University of Western Australia",
]

# The client, and therefore the reference point for every benchmarking figure
# (README Analysis item 16). Peers = GO8_UNIVERSITIES minus this one.
CLIENT_UNIVERSITY = "The University of Sydney"
