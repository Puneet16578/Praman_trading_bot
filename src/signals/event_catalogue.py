"""Phase 5: the event catalogue -- unusual price/volume/delivery moves, defined relative to each
stock's OWN trailing distribution (not a global threshold), computed bitemporally-safe: every
statistic for evaluation day T uses only prices and corporate actions knowable as of T.

Not applicable here -- recorded so a future reader doesn't reapply it incorrectly:
corporate_actions' EX_DATE_FALLBACK confidence tier (src/ingestion/nse_market_data/
corporate_actions.py) exists to protect TIMING-sensitive signals (e.g. "was there unusual activity
before this action's real announcement date") from trusting a knowledge_date that is only a safe
stand-in for PRICE ADJUSTMENT, not a real announcement date. This module never reasons about
corporate-action announcement timing -- it only uses corporate actions for price adjustment (via
the vectorized equivalent of compute_adjustment_factor(), below), which is knowledge-date-filtered
but timing-agnostic: it doesn't matter WHEN within (price_date, as_of] an action was announced,
only THAT it was, by as_of. EX_DATE_FALLBACK rows are therefore safe to use here exactly like any
other tier. This distinction will matter the day a pre-announcement-accumulation signal is built
on top of this catalogue -- THAT signal must use
src/signals/corporate_action_timing.py's timing_reliable_corporate_actions(), not this module's
adjustment path, for its own announcement-timing question.

Vectorization and the knowledge_date <= event_date guard
----------------------------------------------------------
compute_adjustment_factor() (src/signals/price_adjustment.py) is correct but calls latest_as_of()
per (price_date, as_of) pair -- too slow at catalogue scale (millions of (symbol, day) pairs).
This module instead exploits an algebraic identity that holds GIVEN a precondition it checks
explicitly, not assumes: every real corporate-action row satisfies knowledge_date <= event_date
(Phase 3's test_no_real_row_has_knowledge_date_after_event_date passes today, 0 real violations --
but that test's own docstring says the inverse ordering is possible in principle, merely absent in
this dataset). `_assert_ordering_guarantee()` re-checks this directly, per symbol, every time this
module builds a symbol's history, and raises `LateAnnouncedActionError` if it ever fails -- this
module's fast path is valid for the data we have, not as a general invariant, and must never
silently produce a wrong adjusted return from a future late-announced action.

Given that precondition, define cum_factor_up_to(D) = product of factor_for_action(...) for every
BONUS/SPLIT action with event_date <= D (a single per-symbol monotonic step function, T-independent
by construction). Then, for any price_date <= as_of:
    compute_adjustment_factor(price_date, as_of) == cum_factor_up_to(as_of) / cum_factor_up_to(price_date)
and therefore, for ANY two dates D1 <= D2 <= as_of (as_of is always D2 or later here -- every
return this module computes is over a strictly historical window ending at or before the
evaluation day):
    adjusted_close(D2, as_of) / adjusted_close(D1, as_of) == g(D2) / g(D1)
where g(D) = raw_close_as_of(D) * cum_factor_up_to(D) -- the as_of/T term cancels exactly. Every
statistic this module computes is a RETURN (a ratio between two adjusted prices sharing the same
as_of), never an absolute adjusted price level, so this cancellation is all that's needed; no
per-evaluation-day recomputation of the corporate-action adjustment factor is required. This is a
proven algebraic equivalence GIVEN the ordering precondition, not an approximation -- cross-checked
directly against real compute_adjustment_factor()/adjusted_close() calls in
tests/test_event_catalogue_real_data_guard.py, not merely reasoned about on paper.

Structural-break exclusion: a DEMERGER, CAPITAL_REDUCTION, RIGHTS, or RATIO_CONFLICT action has no
trusted adjustment factor by design (CLAUDE.md's scope boundary for the first two; a rights issue's
adjustment depends on premium/theoretical ex-rights price, not the ratio alone; a ratio-conflict
row's own subject/announcement ratios disagree -- see corporate_actions.py's module docstring). Any
return window whose (start, end] spans one of these event_dates is excluded, not silently computed
on raw prices -- mirrored here from compute_adjustment_factor's own UnadjustableWindowError by
checking these event_dates against each window directly (the g(D) fast path only ever folds
BONUS/SPLIT into cum_factor_up_to; STRUCTURAL_BREAK_ACTION_TYPES event_dates are tracked purely as
exclusion boundaries, never given a factor). Kept as one shared "structural break" set rather than
separate parallel ones deliberately: the exclusion criterion is "no ratio trusted enough to adjust
by," not "is specifically a demerger" -- but every row's own `action_type` in `corporate_actions`
still records accurately which action actually happened; only the exclusion-window LOGIC treats
them identically, not their stored labels (docs/phase5_event_catalogue.md Sec.4j). This tuple is
now defined ONCE, in `corporate_actions.py` (P8-009 root-cause fix) -- both this module and
`price_adjustment.py` import the same object rather than each keeping their own copy.

Bhavcopy's own knowledge_date is NOT collapsed the way corporate-action as_of-dependence is:
unlike corporate actions, a bhavcopy row for a given (symbol, event_date) CAN have more than one
real knowledge_date vintage (a value republished/corrected later -- Phase 2's "corrected
republished file" case), and a genuine correction changes the VALUE itself, not just a ratio this
module's algebra could cancel. Every raw close/volume/delivery lookup below therefore resolves to
the latest vintage visible as of the SPECIFIC evaluation day being computed, not a single
precomputed "final" series. Consequence, stated plainly per instruction, not glossed over: an
as-of-T query run a week apart CAN return a (slightly) different trailing distribution for the
same T, if NSE republished a file for a date inside that trailing window in the meantime. That is
correct and intended, not a bug -- see docs/phase5_event_catalogue.md.
"""
from __future__ import annotations
import bisect
import statistics
from dataclasses import dataclass, field

from ..bitemporal.guard import latest_as_of, read_as_of
from ..ingestion.nse_market_data.corporate_actions import (
    BONUS, SPLIT, STRUCTURAL_BREAK_ACTION_TYPES,
)
from .price_adjustment import factor_for_action

TRAILING_WINDOW = 60      # sessions, for the z-score/percentile reference distribution
CUMULATIVE_WINDOW = 20    # sessions, for the cumulative-return statistic
FAR_FUTURE_AS_OF = "2099-01-01"  # "give me every vintage/row that exists" -- as-of filtering of
                                 # INDIVIDUAL vintages happens in-memory afterward, per evaluation day

class LateAnnouncedActionError(ValueError):
    """Raised when a real corporate-action row violates knowledge_date <= event_date -- this
    module's vectorized adjustment path is valid only under that precondition (see module
    docstring). Never caught and silently worked around: a symbol whose actions violate this must
    be investigated, not quietly given a wrong adjusted return."""

def _assert_ordering_guarantee(actions: list[dict], symbol: str) -> None:
    violations = [a for a in actions if a["knowledge_date"] > a["event_date"]]
    if violations:
        raise LateAnnouncedActionError(
            f"{symbol}: {len(violations)} corporate-action row(s) have knowledge_date > event_date "
            f"-- the event catalogue's vectorized adjustment path (see event_catalogue.py's module "
            f"docstring) is not valid without this guarantee. First offending row: {violations[0]}"
        )

@dataclass
class SymbolHistory:
    """Precomputed, per-symbol state built once from the store (a handful of queries total, not
    per evaluation day). All lookups below are pure in-memory operations -- no further DB access."""
    symbol: str
    trading_days: list[str]                       # chronological, this symbol's own real trading days
    vintages: dict[str, list[tuple[str, dict]]]    # event_date -> [(knowledge_date, bhavcopy row), ...] sorted by knowledge_date
    factor_dates: list[str]                        # sorted event_dates of BONUS/SPLIT actions
    factor_cum: list[float]                        # cumulative product, parallel to factor_dates
    structural_break_dates: list[str]               # sorted event_dates of DEMERGER/CAPITAL_REDUCTION actions

    def price_row_as_of(self, event_date: str, as_of: str) -> dict | None:
        """The latest bhavcopy vintage for `event_date` visible as of `as_of` -- resolves the
        republish/correction case correctly (see module docstring); for the overwhelming majority
        of (symbol, event_date) pairs there is exactly one vintage and this is an O(1) lookup."""
        entries = self.vintages.get(event_date)
        if not entries:
            return None
        result = None
        for knowledge_date, row in entries:
            if knowledge_date <= as_of:
                result = row
            else:
                break  # sorted ascending by knowledge_date -- nothing later can qualify either
        return result

    def cum_factor_up_to(self, event_date: str) -> float:
        idx = bisect.bisect_right(self.factor_dates, event_date)
        return self.factor_cum[idx - 1] if idx > 0 else 1.0

    def structural_break_in_window(self, start_exclusive: str, end_inclusive: str) -> bool:
        lo = bisect.bisect_right(self.structural_break_dates, start_exclusive)
        hi = bisect.bisect_right(self.structural_break_dates, end_inclusive)
        return hi > lo

def build_symbol_history(conn, symbol: str, series: str = "EQ", symbol_group: list[str] | None = None) -> SymbolHistory:
    """`symbol_group` (Amendment 4 prep item 5, optional, default None = just `[symbol]`, IDENTICAL
    to before -- fully backward compatible) stitches every symbol string known to share this
    security's ISIN into one continuous history. Without it, a company rename (this project's own
    bhavcopy/corporate_actions tables are keyed by symbol STRING, not ISIN) makes the pre-rename
    symbol's own trading history end abruptly and the post-rename symbol's begin from nothing --
    exactly the shape that starves a forward-looking label of the real trading days it needs
    (measured: docs/phase10_amendment4_prep.md item 3, ~0.52% of fully-elapsed catalogued events).
    Safe to concatenate without a merge/tie-break step because a real rename's member date ranges
    never overlap (confirmed directly: scripts/phase10_amendment4_isin_renames.py found all 195
    detected renames strictly chronologically contiguous, never concurrent). Caller resolves
    `symbol_group` via `src/ingestion/nse_market_data/isin_mapping.py`'s `build_symbol_groups` --
    this module stays decoupled from the ISIN-mapping mechanism itself, accepting only plain data."""
    symbols = symbol_group or [symbol]

    raw_rows = []
    for s in symbols:
        raw_rows.extend(read_as_of(conn, "bhavcopy", FAR_FUTURE_AS_OF, symbol=s, series=series))
    vintages: dict[str, list[tuple[str, dict]]] = {}
    for row in raw_rows:
        vintages.setdefault(row["event_date"], []).append((row["knowledge_date"], row))
    for entries in vintages.values():
        entries.sort(key=lambda kv: kv[0])
    trading_days = sorted(vintages.keys())

    actions = []
    for s in symbols:
        actions.extend(latest_as_of(conn, "corporate_actions", FAR_FUTURE_AS_OF, symbol=s))
    _assert_ordering_guarantee(actions, symbol)

    adjustable = sorted((a for a in actions if a["action_type"] in (BONUS, SPLIT)), key=lambda a: a["event_date"])
    factor_dates: list[str] = []
    factor_cum: list[float] = []
    running = 1.0
    for a in adjustable:
        running *= factor_for_action(a["action_type"], a["ratio_numerator"], a["ratio_denominator"])
        factor_dates.append(a["event_date"])
        factor_cum.append(running)

    structural_break_dates = sorted(a["event_date"] for a in actions if a["action_type"] in STRUCTURAL_BREAK_ACTION_TYPES)

    return SymbolHistory(symbol=symbol, trading_days=trading_days, vintages=vintages,
                          factor_dates=factor_dates, factor_cum=factor_cum,
                          structural_break_dates=structural_break_dates)

def _return(hist: SymbolHistory, d1: str, d2: str, as_of: str) -> float | None:
    """Adjusted return from d1 to d2 (d1 < d2 <= as_of), or None if a demerger or capital
    reduction falls in (d1, d2] or either date's price isn't visible as of `as_of`."""
    if hist.structural_break_in_window(d1, d2):
        return None
    row1 = hist.price_row_as_of(d1, as_of)
    row2 = hist.price_row_as_of(d2, as_of)
    if row1 is None or row2 is None:
        return None
    g1 = row1["close_price"] * hist.cum_factor_up_to(d1)
    g2 = row2["close_price"] * hist.cum_factor_up_to(d2)
    if g1 == 0:
        return None
    return g2 / g1 - 1.0

@dataclass
class DailyStat:
    """The `_demerger_excluded` field names below are retained as-is (not renamed to
    `_structural_break_excluded`) even though they now also fire for CAPITAL_REDUCTION windows --
    these are internal field names with no independent existing consumers outside this module's own
    build scripts, so the cost of a rename is real (every script/test touching these fields) for a
    purely cosmetic gain; the field's actual behavior (§ module docstring, "structural-break
    exclusion") is what's accurate, not its name. See docs/phase5_event_catalogue.md Sec.4j for
    this scoping decision recorded explicitly rather than left implicit."""
    symbol: str
    event_date: str
    close_price_raw: float
    return_1d: float | None
    return_1d_demerger_excluded: bool
    return_20d: float | None
    return_20d_demerger_excluded: bool
    zscore_60d: float | None
    percentile_60d: float | None          # 0..100, rank of return_1d within the trailing distribution
    trailing_return_count: int            # how many of the up-to-60 trailing 1-day returns were usable
    traded_qty: int
    volume_ratio: float | None            # traded_qty(T) / trailing median traded_qty
    delivery_pct: float | None
    delivery_pct_percentile_60d: float | None

def _percentile_rank(value: float, population: list[float]) -> float:
    """% of the population strictly below `value`, plus half the ties -- the conventional
    definition, avoids a value tied with itself always reading exactly 100."""
    below = sum(1 for v in population if v < value)
    tied = sum(1 for v in population if v == value)
    return 100.0 * (below + 0.5 * tied) / len(population)

def compute_daily_stats(hist: SymbolHistory) -> list[DailyStat]:
    """One DailyStat per trading day this symbol has, from the (TRAILING_WINDOW + 1)-th real
    trading day onward (earlier days don't have a full trailing window and are not emitted at
    all, rather than emitted with a misleadingly partial z-score/percentile)."""
    days = hist.trading_days
    out: list[DailyStat] = []

    for i in range(TRAILING_WINDOW + 1, len(days)):
        today = days[i]
        as_of = today  # the single as-of-T perspective for every lookup this iteration needs

        today_row = hist.price_row_as_of(today, as_of)
        if today_row is None:
            continue

        r1 = _return(hist, days[i - 1], today, as_of)
        r1_excluded = r1 is None and hist.structural_break_in_window(days[i - 1], today)

        r20 = None
        r20_excluded = False
        if i - CUMULATIVE_WINDOW >= 0:
            r20 = _return(hist, days[i - CUMULATIVE_WINDOW], today, as_of)
            r20_excluded = r20 is None and hist.structural_break_in_window(days[i - CUMULATIVE_WINDOW], today)

        trailing_returns = []
        for k in range(i - TRAILING_WINDOW, i):
            r = _return(hist, days[k - 1], days[k], as_of)
            if r is not None:
                trailing_returns.append(r)

        zscore = percentile = None
        if r1 is not None and len(trailing_returns) >= 2:
            mean = statistics.fmean(trailing_returns)
            stdev = statistics.pstdev(trailing_returns)
            if stdev > 0:
                zscore = (r1 - mean) / stdev
            percentile = _percentile_rank(r1, trailing_returns)

        trailing_qty = []
        for k in range(i - TRAILING_WINDOW, i):
            row = hist.price_row_as_of(days[k], as_of)
            if row is not None:
                trailing_qty.append(row["traded_qty"])
        volume_ratio = None
        if trailing_qty:
            median_qty = statistics.median(trailing_qty)
            if median_qty > 0:
                volume_ratio = today_row["traded_qty"] / median_qty

        trailing_delivery = []
        for k in range(i - TRAILING_WINDOW, i):
            row = hist.price_row_as_of(days[k], as_of)
            if row is not None and row["delivery_pct"] is not None:
                trailing_delivery.append(row["delivery_pct"])
        delivery_percentile = None
        if today_row["delivery_pct"] is not None and trailing_delivery:
            delivery_percentile = _percentile_rank(today_row["delivery_pct"], trailing_delivery)

        out.append(DailyStat(
            symbol=today_row["symbol"], event_date=today, close_price_raw=today_row["close_price"],
            return_1d=r1, return_1d_demerger_excluded=r1_excluded,
            return_20d=r20, return_20d_demerger_excluded=r20_excluded,
            zscore_60d=zscore, percentile_60d=percentile, trailing_return_count=len(trailing_returns),
            traded_qty=today_row["traded_qty"], volume_ratio=volume_ratio,
            delivery_pct=today_row["delivery_pct"], delivery_pct_percentile_60d=delivery_percentile,
        ))
    return out
