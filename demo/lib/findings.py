"""Static, committed-result figures for the Findings page. No live query -- every number here is
either PARSED directly from a committed doc (preferred, so the number cannot silently drift from
its source) or, where parsing free prose reliably would be more fragile than the number is worth,
hand-transcribed with an adjacent test (tests/test_demo_findings_figures.py) that re-parses the
same source file and asserts equality -- the P8-009 lesson this project already logged once
(DEFECT_REGISTER.md): two hand-mirrored copies of the same fact silently drift apart if nothing
ever checks them against each other again.
"""
from __future__ import annotations
import re
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_PATH = PROJECT_ROOT / "docs" / "RESULTS.md"
AMENDMENT5_PATH = PROJECT_ROOT / "docs" / "phase10_preregistration_amendment5.md"

_AUC_ROW_RE = re.compile(
    r"^\|\s*`([\w_]+)`\*?\s*\|\s*([\d.]+)\s*\[([\d.]+),\s*([\d.]+)\]\s*\|\s*([\d.]+)\s*\[([\d.]+),\s*([\d.]+)\]\s*\|\s*(.+?)\s*\|\s*$"
)


@lru_cache(maxsize=1)
def parse_final_auc_table() -> list[dict]:
    """Parses the 7-row "final, frozen table" out of docs/RESULTS.md directly -- the exact rows
    this project already committed, not a re-typed copy of them. Source: docs/RESULTS.md, the
    reproducibility-note section (Amendment 5's frozen Phase 8b table)."""
    text = RESULTS_PATH.read_text(encoding="utf-8")
    rows = []
    for line in text.splitlines():
        m = _AUC_ROW_RE.match(line.strip())
        if m:
            feature, train_auc, train_lo, train_hi, ho_auc, ho_lo, ho_hi, excludes = m.groups()
            rows.append({
                "feature": feature,
                "train_auc": float(train_auc), "train_ci": (float(train_lo), float(train_hi)),
                "holdout_auc": float(ho_auc), "holdout_ci": (float(ho_lo), float(ho_hi)),
                "excludes_half": excludes,
            })
    if len(rows) != 7:
        raise RuntimeError(
            f"Expected 7 AUC table rows from {RESULTS_PATH}, parsed {len(rows)} -- "
            "the table's format in RESULTS.md may have changed; update the parser regex, not this count."
        )
    return rows


# Hand-transcribed: prose-embedded figures a generic parser would be fragile against. Each has a
# same-file regex test in tests/test_demo_findings_figures.py asserting it matches RESULTS.md /
# the amendment doc, not merely trusted here.
RETRACTION = {
    "classifier_top_tier_precision_raw": 90.6,
    "classifier_top_tier_precision_clean": 28.6,
    "classifier_top_tier_n_clean": 7,
    "disclosure_alone_precision_raw": 78.7,
    "disclosure_alone_precision_clean": 51.1,
    "source": "docs/RESULTS.md §1",
}

DECOMPOSITION = {
    "raw_lift_pp": 16.4,
    "drift_corrected_lift_pp": 15.9,
    "decoupled_lift_pp_primary": -22.5,
    "decoupled_lift_pp_secondary": 6.7,
    "source": "docs/RESULTS.md §1",
}

FROZEN_PREREGISTRATION = {
    "train_missing_rate_pct": 1.310,
    "holdout_missing_rate_pct": 0.897,
    "gap_pp": 0.413,
    "missing_data_threshold_pct": 4.3,
    "pinned_commit": "afe3e2bd07abe8b602c4119b916f7696a3c12131",
    "evaluation_window": "2026-09-16 through 2027-01-15",
    "earliest_run": "~early June 2027",
    "source": "docs/phase10_preregistration_amendment5.md",
}
