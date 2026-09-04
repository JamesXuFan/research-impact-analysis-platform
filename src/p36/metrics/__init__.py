"""The single canonical implementation of every reported metric.

No metric may be recomputed by hand in an analysis module or notebook — import it
from here instead (see .claude/agents/metrics-consistency.md and pandas-safety.md).
Every function's definition must match docs/methodology.md exactly; when they
disagree, methodology.md is not automatically right — it is a client deliverable
that itself needs confirming, but the two must never silently drift apart.
"""

from p36.metrics.metrics import (
    add_derived_flags,
    citations_per_paper,
    citescore_quartile,
    exclude_out_of_scope,
    growth_rate,
    international_collaboration_share,
    mean_fwci,
    period_growth,
    q1_share,
    top_decile_share,
)

__all__ = [
    "add_derived_flags",
    "citations_per_paper",
    "citescore_quartile",
    "exclude_out_of_scope",
    "growth_rate",
    "international_collaboration_share",
    "mean_fwci",
    "period_growth",
    "q1_share",
    "top_decile_share",
]
