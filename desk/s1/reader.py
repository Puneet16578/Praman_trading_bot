"""The sole S1 real-outcome read surface. No CLI grants evaluation permission."""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass

from desk import outcome_firewall
from desk.paper.execution import basis_factor
from desk.paper.locks import lock_state
from desk.s1.inputs import START, END, DEV_END, eligible_at
from scripts.abc_followup_counts import BoundedInputs
from scripts import abc_event_day_context as C
from src.signals.price_adjustment import UnadjustableWindowError

_sealed = ContextVar("s1_real_outcomes_sealed", default=False)


class OutcomeReadRefused(RuntimeError):
    pass


@contextmanager
def seal_real_reads():
    token = _sealed.set(True)
    try:
        yield
    finally:
        _sealed.reset(token)


def check(event, day, end, authorized):
    # Called before every query, including helper calls. Hard ceiling survives
    # the shared firewall's calendar opening; S1 has no forward experiment.
    if _sealed.get() or not authorized:
        raise OutcomeReadRefused("Real S1 outcomes are sealed.")
    if end not in (DEV_END, END) or not START <= event <= end or not START <= day <= end:
        raise OutcomeReadRefused("S1 read outside its period boundary.")
    if (event <= DEV_END) != (end == DEV_END):
        raise OutcomeReadRefused("Event and evaluation period differ.")
    outcome_firewall.require_outcome_access(event)


@dataclass(frozen=True)
class Bar:
    opening: float
    high: float
    low: float
    close: float
    factor: float = 1.
    blocks_buy: bool = False
    blocks_sell: bool = False
    upper: float | None = None
    unadjustable: bool = False
    dividend: bool = False


class RealReader:
    """Only construct with authorization after the user's separate evaluation
    approval. Store handles must already be read-only. Rehearsal seals even a
    previously-created instance and any previously-imported method alias.
    """
    def __init__(self, conn, desk_conn, end, *, authorized=False, snapshots=()):
        self.conn, self.desk_conn, self.end = conn, desk_conn, end
        self.authorized, self.snapshots = authorized, snapshots

    def bar(self, event, symbol, day):
        check(event, day, self.end, self.authorized)
        bounded = BoundedInputs(self.conn, day, day)
        try:
            factor = basis_factor(bounded, symbol, event, day)
        except UnadjustableWindowError:
            return Bar(0, 0, 0, 0, unadjustable=True)
        rows = list(bounded.execute(
            "SELECT * FROM bhavcopy WHERE symbol=? AND event_date=? AND knowledge_date<=? "
            "AND series IN ('EQ','BE','BZ') ORDER BY CASE series WHEN 'EQ' THEN 0 WHEN 'BE' THEN 1 ELSE 2 END,"
            "knowledge_date DESC,row_id DESC", (symbol, day, day)))
        if not rows:
            return None
        raw = dict(rows[0])
        lock = lock_state(bounded, self.desk_conn, symbol, day, raw, day)
        dividend = bounded.execute(
            "SELECT 1 FROM corporate_actions WHERE symbol=? AND event_date=? AND action_type='DIVIDEND' "
            "AND knowledge_date<=? LIMIT 1", (symbol, day, day)).fetchone() is not None
        return Bar(*(raw[k]*factor if raw[k] is not None else float("nan")
                     for k in ("open_price", "high_price", "low_price", "close_price")),
                   factor=factor, blocks_buy=lock.blocks_buy, blocks_sell=lock.blocks_sell,
                   upper=None if lock.limits.upper is None else lock.limits.upper*factor, dividend=dividend)

    def market_members(self, event):
        check(event, event, self.end, self.authorized)
        sessions = C._calendar(self.conn, "", event)
        if len(sessions) < 2 or sessions[-1] != event:
            return []
        previous = sessions[-2]
        before, now = C._bars_for_day(self.conn, previous), C._bars_for_day(self.conn, event)
        actions = C._actions_asof(self.conn, event)
        eligible = eligible_at(self.snapshots, event)
        return sorted(s for s in eligible & before.keys() & now.keys()
                      if C._return((previous, before[s]), event, now[s], actions.get(s, ())) is not None)

    def benchmark_open(self, event, symbol, day, fill_day):
        check(event, day, self.end, self.authorized)
        bounded = BoundedInputs(self.conn, day, day)
        row = bounded.execute(
            "SELECT open_price FROM bhavcopy WHERE symbol=? AND event_date=? AND series='EQ' "
            "AND knowledge_date<=? ORDER BY knowledge_date DESC,row_id DESC LIMIT 1", (symbol, day, day)).fetchone()
        if row is None:
            return None
        try:
            factor = basis_factor(bounded, symbol, fill_day, day)
        except UnadjustableWindowError:
            return None
        return row[0]*factor if row[0] is not None else None
