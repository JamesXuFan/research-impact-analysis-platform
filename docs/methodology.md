# Methodology

> COMP3888_W11_02_P36 · Publication Intelligence & Research Impact Analysis Platform

This document is the single source of truth for what each reported metric means. Every
implementation in `src/p36/metrics/metrics.py` must match a definition here exactly. If
you change a definition here, update the corresponding function in the same commit —
`metrics-consistency.md` checks the two stay in sync before every merge.

Items marked **PROVISIONAL** are not yet confirmed by the client. Do not present a
provisional definition as settled in a report, and do not let code silently harden a
provisional choice — the constant it maps to in `src/p36/config.py` is marked the same
way.

## Metrics

### Percentile direction — VERIFIED, not provisional

`CiteScore percentile (publication year) *`, `SJR percentile (publication year) *`,
and `Outputs in Top Citation Percentiles, per percentile` all use the Scopus/SciVal
convention where **lower is better** — a value of 1 means "top 1%", 100 means bottom.
Confirmed 2026-09-02 against Field-Weighted Citation Impact (unambiguous: 1.0 = world
average, higher = better):

| CiteScore percentile bucket | mean FWCI |
| --- | --- |
| (0, 10] | 2.50 |
| (75, 100] | 0.64 |

| Top Citation Percentiles bucket | mean FWCI |
| --- | --- |
| (0, 1] | 13.96 |
| (75, 100] | 0.00 |

Every threshold on these columns is a `<=`. This is the opposite of the everyday
reading of "percentile" — get it backwards and every Q1 and highly-cited figure in
the project inverts.

### Q1 share — direction verified; exact cutoff **PROVISIONAL**

Share of a set's publications whose source has `CiteScore percentile <= 25`.

- **Open question:** should Q1 instead be based on `SJR percentile <= 25`? The two do
  not always agree on the same journal.
- Threshold: `Q1_CITESCORE_PERCENTILE_MAX` in `src/p36/config.py`.

### CiteScore quartile (Q1–Q4) — **PROVISIONAL**, same basis as Q1

`p36.metrics.citescore_quartile` buckets `CiteScore percentile` into four tiers using
`CITESCORE_QUARTILE_BOUNDS = [0, 25, 50, 75, 100]` (Q1's own upper bound reused as the
first cut point — this is not an alternative definition of Q1, it's the same threshold
extended to the other three tiers). Publications with no CiteScore percentile get an
undefined tier (NaN), never a default bucket. Used by
`journal_tier.impact_by_citescore_quartile` (mean FWCI / top-decile share / uncited
share per tier — the item 3 sub-questions the binary `is_q1` flag alone can't answer,
since it collapses Q2–Q4 into one "not Q1" bucket) and `journal_tier.overperforming_sources`.

### Overperforming sources within a tier

`journal_tier.overperforming_sources`: per Scopus source (journal), mean FWCI minus
that source's own CiteScore-quartile mean FWCI — "are there journals/publications
within a tier that receive more citations than would be expected for that tier?"
(README item 3). Restricted to (quartile, source) pairs with at least
`OVERPERFORMING_SOURCE_MIN_PUBLICATIONS` (10) publications, so a single highly-cited
paper can't make a small source look like an outlier. Descriptive only — a source's
gap can reflect genuine editorial quality, a narrow high-citation-culture sub-field,
or a handful of outliers even past the publication floor.

### International collaboration share

Share of publications with `Number of Countries/Regions >=
INTERNATIONAL_COLLABORATION_MIN_COUNTRIES` (i.e. author affiliations span at least
2 countries — a domestic-only Australian paper has `Number of Countries/Regions == 1`,
Australia itself is counted). `>=`, not `>` — the threshold is named "minimum", and a
publication with exactly 2 countries already qualifies.

### Institutional collaboration

Unlike international collaboration, this is **not** a binary threshold metric — it is
reported directly as `Number of Institutions` (its mean, e.g.
`go8_benchmarking.benchmark_summary`'s `mean_institutions_per_paper`), and as
`log1p(Number of Institutions)` when used as a regression predictor (item 14) to
reduce right-skew. If a future finding needs a binary "is multi-institutional" flag
analogous to `is_international`, define it here and in `p36.metrics.add_derived_flags`
first — do not invent one inline in an analysis module.

### Open access status — **PROVISIONAL**

`is_open_access` (`p36.metrics.add_derived_flags`) is `Open Access` non-null. `Open
Access` is ~46% null in the raw source data (~41% in the deduplicated set); the
working assumption is that null means "not open access via any recognised route"
(`p36.config.OPEN_ACCESS_NULL_MEANS_NOT_OA = True`), not "status unknown" — **this has
not been confirmed by the client** (see `data_dictionary.md`, Data quality notes).
Both the item 14 regression coefficient and the item 17 scenario projection on open
access inherit this assumption; state it as a caveat wherever either number is
reported.

### Citations per paper

Mean citations per publication over a given set. **Not** the same figure as the QS
*Citations per Faculty* indicator, which is a raw total citation count, not a per-paper
average — see `.claude/agents/finding-checker.md` for why this distinction matters when
writing findings.

### Top-decile / highly-cited share

Share of publications with `Outputs in Top Citation Percentiles, per percentile <=
TOP_DECILE_PERCENTILE_MAX` (10). This column is already a per-publication,
field/year/document-type-normalised percentile computed by SciVal — **never recompute
it from raw `Citations`**, which would silently drop the field/year normalisation and
reintroduce the cross-field comparison problem below.

Where a sub-question asks about the strictest "world-leading" band specifically
(top 1%, e.g. README Analysis item 16), use `TOP_1_PERCENT_PERCENTILE_MAX` instead.

### Growth rate

Year-over-year change in publication count (`p36.metrics.growth_rate`, a per-year
series). Distinct from citation-based year trends, which are subject to the
citation-window artefact below.

### Total-period growth

**Not the same metric as growth rate above, despite the similar name.**
`p36.metrics.period_growth`: `(count in the last year of a range - count in the
first) / count in the first` — one number summarising a whole span, for "which
field / which university is improving most rapidly" ranking questions (items 6
and 16). A year-over-year series doesn't answer "most rapidly" directly; this
does. Do not call this "growth rate" in a finding — the two are computed
differently and answer different questions.

## Cross-cutting rules

### Citation window artefact — **PROVISIONAL**

Any year-by-year *average citation* trend will show an artificial fall in its most
recent years, because those publications have not had time to accumulate citations.
This is a property of the data, not a real decline. Number of trailing years to
exclude (or whether to exclude them at all): not yet confirmed by client. See
`CITATION_WINDOW_TRAILING_YEARS_EXCLUDED` in `src/p36/config.py`.

### Cross-field / cross-year comparison

Raw citation counts must never be compared across research fields or publication
years without normalisation. Clinical medicine papers can average 5–10× the citations
of mathematics papers — a citation-culture difference, not a quality difference.
Cross-field comparisons require a field-normalised metric or a top-decile share.

### Self-citations — **PROVISIONAL**

Whether self-citations are excluded from citation counts is not yet confirmed by the
client. See `EXCLUDE_SELF_CITATIONS` in `src/p36/config.py`.

### Document type scope — **PROVISIONAL**

Which document types (articles, reviews, conference papers, editorials, ...) count
toward publication and citation totals is not yet confirmed by the client. Observed
`Publication type` values: Article, Review, Conference Paper, Chapter, Book, Data
Paper, Retracted, Note, Editorial, Letter. See `INCLUDED_DOCUMENT_TYPES` in
`src/p36/config.py`.

`EXCLUDE_RETRACTED` (also PROVISIONAL, but defaults to `True`) drops the 48 rows
where `Publication type == "Retracted"` — treated separately from the broader scope
question because the team's working assumption is that a retracted paper should not
count as valid research output, but this has not been put to the client either, so it
must not be presented as a settled fact in any finding.

This scope question (which document types count *at all*) is distinct from whether
document type is a driver *of impact among the types included* — the latter is the
item 14 "Document Type → Citation Impact" fixed-effect analysis above, which assumes
whatever `INCLUDED_DOCUMENT_TYPES`/`EXCLUDE_RETRACTED` scope is currently in force
(retracted excluded, everything else included, as of this writing).

### Multi-field publications — **PROVISIONAL**

Whether a publication spanning multiple research fields is counted whole in each field
or fractionally (split to sum to 1 across fields) is not yet confirmed by the client.
See `FRACTIONAL_FIELD_COUNTING` in `src/p36/config.py`.

### Data limitations

The dataset does not include faculty headcount. Any statement about a change in QS
score or QS-style ratio must carry the qualifier "assuming faculty headcount is
unchanged."

### Scope: client and peer set

`CLIENT_UNIVERSITY` = "The University of Sydney" — every Go8/Peer Benchmarking figure
(README Analysis item 16) is relative to this university. `GO8_UNIVERSITIES` in
`src/p36/config.py` lists all 8 `source_university` values found in the data (which is
also the complete Go8); "peers" = that list minus the client. Any cross-university
figure (item 16 or 17) must use the *deduplicated* dataset
(`p36.dataset.load_deduplicated`, or `p36.ingest.deduplicate_by_eid`) — see the
cross-university duplication note in `data/dictionary/data_dictionary.md`. A
per-university figure that stands alone (e.g. Sydney's own Q1 share) may use either
the raw or deduplicated dataset — they agree for any single `source_university`.

## Analysis modules

Each README Analysis item gets a section once its analysis code exists, added in the
same commit as the code — see the per-item docstring in
`src/p36/analysis/<module>.py` for the full question list each one answers.

| README item | Module | Core question |
| --- | --- | --- |
| 3. Journal Tier and Q1 Analysis | `journal_tier.py` | What share of output is in Q1 journals, and how does that vary? |
| 6. Research Field / Faculty Analysis | `field_analysis.py` | Which fields are strongest, which are improving, which are high-volume-low-impact or the reverse? |
| 9. International Collaboration Analysis | `international_collaboration.py` | Are internationally co-authored papers cited more? Does it hold within field and year? |
| 14. Integrated Research Impact Driver Analysis | `impact_drivers.py` | Holding the other factors constant, which of Q1 status, international collaboration, institutional collaboration, open access, and document type is actually associated with impact — and does the item 9 gap survive once the others are controlled for? |
| 16. Go8 / Peer Benchmarking | `go8_benchmarking.py` | How does Sydney compare to Go8 peers on volume, impact, Q1 share, and collaboration? |
| 17. Scenario Analysis | `scenario_analysis.py` | What would mean impact look like under a hypothetical shift in Q1 share, international collaboration, open access, or the uncited share? |

**Headline result so far (2026-09-03, run against the full dataset, model now includes
document-type fixed effects — see below):** the raw international-vs-domestic FWCI gap
is +0.75 (item 9), but shrinks to +0.09 once Q1 status, author count, institution count,
open access, document type, and year are controlled for in the same regression
(item 14) — most of the naive gap is confounding, not an independent collaboration
effect. Q1 status is by far the largest independent driver (+0.97 FWCI). The full
model's R² is 0.019 — these factors together explain very little of the variance in
any single publication's impact, which is itself worth stating plainly rather than
only reporting the coefficients that are statistically significant. Every number here
still needs to go through .claude/agents/finding-checker.md before it appears in a report.

**Document type fixed effects (added 2026-09-03, for README item 14's "Document Type ->
Citation Impact" chain):** `Publication type` is now included in the item 14 model as a
fixed effect (`C(Q('Publication type'))` — the model already includes primary-field fixed
effects the same way). FWCI is already document-type-normalised by SciVal's own
methodology, so a naive expectation is that this term should wash out to ~0 — it does
not: relative to Article (the baseline category statsmodels drops), Conference Paper
(+1.07, p<0.001) and Chapter (+0.76, p<0.001) both run significantly above Article-level
mean FWCI, and Data Paper (-1.27, p<0.001) significantly below. Editorial (n=3), Letter
(n=3), Note (n=9), and Book (n=14) have very wide confidence intervals — those are their
counts in the *regression sample*, not the full dataset. Book has 2,491 publications
overall, but 99.4% have no CiteScore percentile (a journal-level metric that mostly
doesn't apply to books) and are dropped before fitting; Chapter loses 86.1% the same
way, though its remaining 2,746 rows are enough for a tight CI. Read the small-n
document types' coefficients as describing that non-random surviving slice, not
document-type publishing as a whole. Report the significant terms as an actual finding —
FWCI's normalisation does not fully equalise mean impact across document types in this
dataset — not assume they must be near-zero. See `impact_drivers.document_type_summary_table`.
