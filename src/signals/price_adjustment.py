"""Query-time price adjustment. Deliberately NOT a stored column (CLAUDE.md, Phase 3 blocker
note): an adjustment factor is a function of (price_date, as_of) -- it changes every time a new
corporate action becomes knowledge-dated, so storing it would mean either constant rewrites (an
UPDATE, forbidden -- Section 8) or a value that silently goes stale. Computed fresh every call,
from only the corporate_actions rows visible as of the query's own `as_of` (Section 7).
"""
from __future__ import annotations
from datetime import date

from ..bitemporal.guard import latest_as_of
from ..ingestion.nse_market_data.corporate_actions import BONUS, CAPITAL_REDUCTION, DEMERGER, SPLIT

UNADJUSTABLE_ACTION_TYPES = (DEMERGER, CAPITAL_REDUCTION)

class UnadjustableWindowError(ValueError):
    """Raised when a demerger or capital-reduction ex-date falls inside (price_date, as_of] for
    this symbol. Neither has an adjustment factor (CLAUDE.md's scope boundary: NSE discloses no
    ratio for either at announcement time) -- silently ignoring it here would compute a
    confidently wrong adjusted price. The caller must exclude this window, not receive a number.
    """

def factor_for_action(action_type: str, ratio_numerator: float, ratio_denominator: float) -> float:
    """The multiplication factor applied to SHARE COUNT (equivalently, the divisor applied to
    price) for one action. Bonus "N:D" (N new shares per D held) -> (N+D)/D. Split, stored as
    (old_face_value, new_face_value) -> old/new. Two independently-verified real cases:
    BAJFINANCE 2025 bonus 4:1 -> (4+1)/1 = 5; its same-day split 2:1 (Rs 2 -> Re 1) -> 2/1 = 2;
    combined 5*2 = 10, matching the real, publicly known 10x share multiplication that day.
    """
    if action_type == BONUS:
        return (ratio_numerator + ratio_denominator) / ratio_denominator
    if action_type == SPLIT:
        return ratio_numerator / ratio_denominator
    raise ValueError(f"'{action_type}' has no adjustment factor -- only {BONUS!r}/{SPLIT!r} are adjustable.")

def compute_adjustment_factor(conn, symbol: str, price_date: str, as_of: str) -> float:
    """Cumulative factor from every BONUS/SPLIT action for `symbol` with event_date (ex_date) in
    (price_date, as_of] and knowledge_date <= as_of (via `latest_as_of` on corporate_actions --
    Section 7: an action not yet knowledge-dated as of `as_of` must not affect this computation,
    even if its ex_date has already passed in real/calendar time).

    Raises `UnadjustableWindowError` if a DEMERGER ex-date falls in the same range -- never
    silently skipped.
    """
    rows = latest_as_of(conn, "corporate_actions", as_of, symbol=symbol)
    factor = 1.0
    for row in rows:
        if not (price_date < row["event_date"] <= as_of):
            continue
        if row["action_type"] in UNADJUSTABLE_ACTION_TYPES:
            raise UnadjustableWindowError(
                f"{symbol}: a {row['action_type'].lower().replace('_', ' ')} ex-date ({row['event_date']}) "
                f"falls within ({price_date}, {as_of}] -- this window has no adjustment factor and must be "
                "excluded, not adjusted.")
        if row["action_type"] in (BONUS, SPLIT):
            factor *= factor_for_action(row["action_type"], row["ratio_numerator"], row["ratio_denominator"])
    return factor

def adjusted_close(conn, symbol: str, price_date: str, as_of: str, series: str = "EQ") -> float:
    """The as-of adjusted close for `symbol` on `price_date`, expressed in terms comparable to
    `as_of`. Raises `UnadjustableWindowError` per `compute_adjustment_factor` if a demerger falls
    in range; raises `ValueError` if no bhavcopy row exists for the requested (symbol, price_date)
    as of `as_of`.
    """
    price_rows = latest_as_of(conn, "bhavcopy", as_of, symbol=symbol, event_date=price_date, series=series)
    if not price_rows:
        raise ValueError(f"No bhavcopy row for symbol={symbol!r} event_date={price_date!r} series={series!r} visible as of {as_of!r}.")
    raw_close = price_rows[0]["close_price"]
    factor = compute_adjustment_factor(conn, symbol, price_date, as_of)
    return raw_close / factor
