"""Freeze registered one-change population variants; no outcome reads."""
from bisect import bisect_left, bisect_right
from datetime import datetime
from desk.s1 import inputs as S

VARIANTS = ("cutoff_0900", "cutoff_2359", "lookback_1", "lookback_10", "peer_overlap_120",
            "include_unstable", "omit_crowded_dates", "exit_slippage_040")


def enrich(conn, artifact, snapshots, progress=lambda _: None):
    """Add independent variant reasons to an in-memory copy of frozen inputs.

    Preserve primary records, plans, calendars and tercile boundaries exactly.
    Future queries select filing metadata only, never a future bar price.
    """
    records = {(r["day"], r["symbol"]): r for r in artifact["records"]}
    events = {}
    for r in records.values():
        events.setdefault(r["day"], []).append({"symbol": r["symbol"]})
    observed, mapping = artifact["calendars"]["observed"], artifact["meta"]["category_map"]
    for day, event, alternate in S.stream_context(conn, events, snapshots, minimum_overlap=120):
        symbol = event["symbol"]
        r = records[day, symbol]
        j = bisect_right(observed, day)
        nxt = observed[j] if j < len(observed) else None
        # At the final period boundary a next-session filing cutoff cannot be
        # reconstructed; its scheduled exits are already censored.
        upper = nxt or day
        rows = [dict(x) for x in conn.execute(
            "SELECT seq_id,category,description,sort_timestamp,knowledge_date FROM corporate_announcements "
            "WHERE symbol=? AND event_date<=? AND knowledge_date<=?", (symbol, upper, upper))]
        dividends = [x for x in rows if x["category"] in S.A.DIV_CATEGORIES]
        orders = [dict(x) for x in conn.execute(
            "SELECT order_id,knowledge_date FROM sebi_orders WHERE symbol=? AND knowledge_date<=?", (symbol, upper))]
        variants = {}
        for name, cutoff, lb, context in (
            ("cutoff_0900", upper+"T09:00:00", 5, r),
            ("cutoff_2359", day+"T23:59:00", 5, r),
            ("lookback_1", day+"T18:00:00", 1, r),
            ("lookback_10", day+"T18:00:00", 10, r),
            ("peer_overlap_120", day+"T18:00:00", 5, alternate)):
            flags, *_ = S.A.steps_for(rows, day, datetime.fromisoformat(cutoff), observed, mapping, context,
                                      r["gates"], orders, dividends, lb)
            variants[name] = {g: S.reasons(flags, context, r["gates"], r["limit_g5"], day, nxt, g)
                              for g in S.GROUPS}
        r["sensitivity_exclusions"] = variants
        progress(day)
    artifact["meta"]["sensitivity_variants"] = list(VARIANTS)
    return artifact
