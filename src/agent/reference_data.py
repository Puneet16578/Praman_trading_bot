"""Catalogue-relative reference constants/lookups the live agent layer needs but cannot cheaply
recompute per single-event report -- cap-band quintile assignment and same-date co-movement count
are properties of the WHOLE catalogue for a given year/day, not of one symbol in isolation (see
scripts/build_event_classifications.py, which computes them once, in bulk, from every catalogued
event). Recomputing them per report would mean reloading and re-deriving the full catalogue's
turnover quintiles and cross-sectional clustering on every call -- expensive and duplicative of
work a batch script already did correctly.

Loaded lazily, once per process, from the versioned artifacts those batch scripts persist:
data/processed/classification_thresholds.json (the approved band momentum medians + the isolated
co-movement threshold, docs/phase7b_classification_design.md) and
data/processed/event_classifications.csv (cap_band + same_date_event_count per event, indexed by
(symbol, event_date)). Every value this module returns carries that provenance explicitly in the
report -- never presented as a live per-event computation, because it isn't one. Contrast with
mcp/tools.py's tools, which DO recompute fresh from the bitemporal store per call -- that
distinction is the point: only genuinely catalogue-wide statistics are read from a cached
artifact, everything else in this agent layer is live.
"""
from __future__ import annotations
import csv
import json
from functools import lru_cache
from pathlib import Path

from ..classification.event_classifier import ClassificationThresholds

ROOT = Path(__file__).resolve().parents[2]
THRESHOLDS_PATH = ROOT / "data" / "processed" / "classification_thresholds.json"
CLASSIFICATIONS_PATH = ROOT / "data" / "processed" / "event_classifications.csv"

CATALOGUE_REFERENCE_SOURCE = (
    "data/processed/event_classifications.csv (scripts/build_event_classifications.py -- "
    "catalogue-relative, not live-recomputed per report)"
)

@lru_cache(maxsize=1)
def load_thresholds() -> ClassificationThresholds:
    with open(THRESHOLDS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return ClassificationThresholds(
        band_median_abs_return_20d=data["band_median_abs_return_20d"],
        isolated_comovement_threshold=data["isolated_comovement_threshold"],
    )

@lru_cache(maxsize=1)
def _load_catalogue_reference() -> dict[tuple[str, str], dict]:
    out = {}
    with open(CLASSIFICATIONS_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[(row["symbol"], row["event_date"])] = row
    return out

def lookup_catalogue_reference(symbol: str, event_date: str) -> dict | None:
    """cap_band + same_date_event_count for this event, sourced from the last batch run of
    scripts/build_event_classifications.py -- None if this (symbol, event_date) was never
    catalogued (e.g. a query for an event outside the Phase 5 catalogue's own criteria)."""
    row = _load_catalogue_reference().get((symbol, event_date))
    if row is None:
        return None
    same_date = row["same_date_event_count"]
    return {
        "cap_band": row["cap_band"] or None,
        "same_date_event_count": int(same_date) if same_date not in ("", "None") else None,
        "source": CATALOGUE_REFERENCE_SOURCE,
    }
