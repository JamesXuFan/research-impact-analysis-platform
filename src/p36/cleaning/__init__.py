"""Cleaning steps applied after ingest: de-duplication, dtype coercion, missing-value
handling. Kept separate from ``metrics/`` so that metric functions can assume clean
input and never re-implement cleaning logic inline.
"""

from p36.cleaning.dtypes import apply_canonical_dtypes

__all__ = ["apply_canonical_dtypes"]
