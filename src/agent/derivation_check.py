"""Tier 2 of the Adversary's number-verification: DERIVATION, not just TRANSCRIPTION.

TRANSCRIPTION (the `verify` closures on EvidenceClaim, unchanged from the original design) re-runs
the SAME derivation function (src/mcp/tools.py) the specialist agent already called, and confirms
the claim's cited_value still matches that function's output. This proves the claim was copied
faithfully -- it does NOT prove the function's own formula is correct, because a bug inside that
shared function returns the identical wrong number on both calls and passes every time. This is
exactly the gap InsightForge's own EvidenceValidator.validate_claim() left open (it checks that
evidence of the right TYPE exists, never that a cited number is arithmetically correct -- confirmed
by direct reading during Phase 7 planning) and exactly the gap a follow-up review named directly:
checking volume_ratio against the same value it came from proves transcription, not correctness.

DERIVATION closes that gap for a random, seeded, reproducible subset of claims: recompute the
value from raw bhavcopy rows via a SEPARATE, independently-written code path -- plain SQL against
`bhavcopy` directly, never build_symbol_history/compute_daily_stats -- and compare to the cited
value within a stated numeric tolerance. A disagreement here means the SHARED formula itself is
wrong, not that a specialist agent mistyped something.

Sampling is deterministic and reproducible (not wall-clock random, so the determinism test --
running the identical event twice must produce byte-identical output -- still holds): a claim's
inclusion is a pure function of its own claim_id via SHA-256, salted with a fixed version string.
Re-running the exact same report always samples the exact same claims.

Scope, stated honestly rather than silently narrowed (CLAUDE.md verification-honesty: never claim
untested coverage): DERIVATION is implemented for `volume_ratio` and `delivery_pct_percentile_60d`
-- both computable from raw bhavcopy quantities/percentages alone, no corporate-action price
adjustment required. `return_20d` and `zscore_60d` need an ADJUSTED return series (corporate-action
factor accumulation, src/signals/price_adjustment.py); an independent second implementation of
that machinery is materially larger and is NOT attempted here. Those two claim types report
DERIVATION as NOT_APPLICABLE and remain TRANSCRIPTION-only until a second adjustment
implementation exists.
"""
from __future__ import annotations
import hashlib
import statistics

DERIVATION_SAMPLE_RATE = 0.20
DERIVATION_SAMPLE_SALT = "praman-phase7c-derivation-sample-v1"
DERIVATION_TOLERANCE = 1e-9  # relative -- both paths read the same raw column values and use the
                             # same well-tested stdlib primitives (statistics.median), so an
                             # honest formula match should be numerically exact; this tolerance
                             # only absorbs incidental floating-point reordering, not a real bug.
TRAILING_WINDOW = 60

def is_sampled_for_derivation(claim_id: str) -> bool:
    """Deterministic ~DERIVATION_SAMPLE_RATE selection, seeded by claim_id -- reproducible across
    runs and processes (no reliance on Python's randomized string hash() or wall-clock random)."""
    digest = hashlib.sha256(f"{DERIVATION_SAMPLE_SALT}:{claim_id}".encode()).hexdigest()
    frac = int(digest[:8], 16) / 0xFFFFFFFF
    return frac < DERIVATION_SAMPLE_RATE

def _trading_days_up_to(conn, symbol: str, event_date: str, n: int) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT event_date FROM bhavcopy WHERE symbol=? AND event_date<=? AND series='EQ' "
        "ORDER BY event_date DESC LIMIT ?",
        (symbol, event_date, n),
    ).fetchall()
    return [r[0] for r in rows][::-1]  # chronological order

def _latest_visible_row(conn, symbol: str, event_date: str, as_of: str):
    """The latest bhavcopy vintage for (symbol, event_date) visible as of `as_of` -- plain SQL,
    deliberately not SymbolHistory.price_row_as_of (see module docstring: independence is the
    point)."""
    return conn.execute(
        "SELECT traded_qty, delivery_pct FROM bhavcopy WHERE symbol=? AND event_date=? AND series='EQ' "
        "AND knowledge_date<=? ORDER BY knowledge_date DESC LIMIT 1",
        (symbol, event_date, as_of),
    ).fetchone()

def independent_volume_ratio(conn, symbol: str, event_date: str) -> float | None:
    """Independent second implementation of volume_ratio: trailing 60-session median traded_qty,
    ratio against the event day's own traded_qty. Returns None under the same conditions the
    primary implementation would (insufficient trailing history, zero median, missing row) --
    those are agreement, not disagreement, so they must never be reported as a derivation FAIL."""
    days = _trading_days_up_to(conn, symbol, event_date, n=TRAILING_WINDOW + 1)
    if not days or days[-1] != event_date or len(days) < TRAILING_WINDOW + 1:
        return None
    trailing_days = days[:-1]
    trailing_qty = []
    for d in trailing_days:
        row = _latest_visible_row(conn, symbol, d, event_date)
        if row is not None:
            trailing_qty.append(row[0])
    if not trailing_qty:
        return None
    median_qty = statistics.median(trailing_qty)
    if median_qty == 0:
        return None
    today_row = _latest_visible_row(conn, symbol, event_date, event_date)
    if today_row is None:
        return None
    return today_row[0] / median_qty

def independent_delivery_percentile(conn, symbol: str, event_date: str) -> float | None:
    """Independent second implementation of delivery_pct_percentile_60d: rank of the event day's
    delivery_pct within its own trailing 60-session distribution (below + half-ties convention,
    matching src/signals/event_catalogue.py's `_percentile_rank` -- reimplemented here rather than
    imported, since importing the function under test would defeat the point of a second,
    independent path)."""
    days = _trading_days_up_to(conn, symbol, event_date, n=TRAILING_WINDOW + 1)
    if not days or days[-1] != event_date or len(days) < TRAILING_WINDOW + 1:
        return None
    trailing_days = days[:-1]
    trailing_delivery = []
    for d in trailing_days:
        row = _latest_visible_row(conn, symbol, d, event_date)
        if row is not None and row[1] is not None:
            trailing_delivery.append(row[1])
    today_row = _latest_visible_row(conn, symbol, event_date, event_date)
    if today_row is None or today_row[1] is None or not trailing_delivery:
        return None
    value = today_row[1]
    below = sum(1 for v in trailing_delivery if v < value)
    tied = sum(1 for v in trailing_delivery if v == value)
    return 100.0 * (below + 0.5 * tied) / len(trailing_delivery)

def values_agree(cited, independent, tolerance: float = DERIVATION_TOLERANCE) -> bool:
    if cited is None or independent is None:
        return cited == independent
    if not isinstance(cited, (int, float)) or not isinstance(independent, (int, float)):
        return cited == independent
    if cited == independent == 0:
        return True
    denom = max(abs(cited), abs(independent), 1e-12)
    return abs(cited - independent) / denom <= tolerance
