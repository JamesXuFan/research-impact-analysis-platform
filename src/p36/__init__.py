"""p36 — Publication Intelligence & Research Impact Analysis Platform.

Package for COMP3888_W11_02_P36. Structure:

- ``ingest.py``       — load raw QS World University Rankings publication exports.
- ``cleaning/``        — de-duplication, dtype coercion, missing-value handling.
- ``metrics/``         — the single canonical implementation of every reported metric.
- ``config.py``        — named constants for thresholds and cutoffs (no magic numbers
  in analysis code).
"""
