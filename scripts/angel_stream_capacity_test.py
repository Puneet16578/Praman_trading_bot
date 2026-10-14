"""Angel market-feed capacity probe for R1 (user decision 2026-10-13). User-run, never scheduled.

Run in your own terminal during market hours, after scripts/angel_connection_test.py passes:
    python -B scripts/angel_stream_capacity_test.py
Same private ANGEL_API_KEY setup as the connection check; client ID, PIN and TOTP are the
wrapper's hidden prompts. It refuses to start unless master is checked out with a clean tree and
the nightly is not running.

Tiers of 25, 50, 100, 200, 300, 500, 750 and at most 1000 symbols, one connection at a time, ten
minutes each, every tier ending by 15:30 IST. Symbols are ranked by average daily turnover over
the 20 sessions known before today (data/processed/praman.db, read-only). Escalation stops at the
first failed tier. Raw ticks are kept only here, in data/live/probe/; the summary in logs/ holds
receipt metrics only, never prices. No orders, account calls, outcomes or store writes.

Pass targets (docs/desk/R1_market_hours_watcher_design.md; proposed, not observed): the feed
stays up, every liquid sentinel ticks, no 30-second silence across all symbols, receipt lag p95
under 2 s and p99 under 5 s where exchange timestamps are valid, and no growing lag. Each
symbol's first tick after subscribing (the feed's snapshot, possibly minutes old) is counted but
kept out of the lag statistics; negative lags are counted as clock anomalies, never clamped.
One run is one market period: choose a capacity only after repeat runs on different days.
"""
from __future__ import annotations

import ctypes
import json
import sqlite3
import subprocess
import sys
import time as clock
from datetime import datetime, time, timedelta
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from desk.angel_market_data import AngelError, AngelMarketData, error_details
from scripts.weekly_ingest import NIGHTLY_BRANCH, _prevent_sleep, head_branch, uncommitted_nightly_inputs
from shared.log_paths import logs_dir
from shared.market_time import IST
from shared.sqlite_readonly import open_readonly

TIERS = (25, 50, 100, 200, 300, 500, 750, 1000)   # never above the provider's 1000 per connection
TIER_SECONDS = 600
SENTINEL_COUNT = 10                                # the most liquid symbols; each must tick
MARKET_OPEN, MARKET_CLOSE = time(9, 15), time(15, 30)
EARLIEST_START = time(9, 20)                       # after the opening minutes
QUOTE_MAX_AGE = 120                                # seconds; a fresh quote confirms the market is open
TURNOVER_SESSIONS, MIN_SESSIONS = 20, 18
P95_LIMIT, P99_LIMIT = 2.0, 5.0                    # seconds of receipt lag
MAX_SILENCE = 30.0                                 # seconds with no tick from any symbol
DRIFT_WINDOW, DRIFT_LIMIT = 120.0, 2.0             # last vs first two minutes of p95 lag
FLUSH_TICKS, FLUSH_SECONDS = 2000, 1.0
PRAMAN_DB = ROOT / "data" / "processed" / "praman.db"
PROBE_DIR = ROOT / "data" / "live" / "probe"
NIGHTLY_TASK = "PramanDailyIngest"


def now_ist() -> datetime:
    return datetime.now(IST)


def liquid_symbols(conn, today: str, limit: int = TIERS[-1]) -> list[str]:
    """EQ symbols by average close x traded quantity over the 20 global sessions before `today`,
    using only rows knowledge-dated before today (the latest such vintage of each bar), present on
    at least 18 of them. Ties by symbol. A resource list, not a recommendation."""
    rows = conn.execute("""
        WITH sessions AS (SELECT DISTINCT event_date FROM bhavcopy
                          WHERE series = 'EQ' AND event_date < :today AND knowledge_date < :today
                          ORDER BY event_date DESC LIMIT :n),
        bars AS (SELECT b.symbol, b.event_date, b.close_price * b.traded_qty AS turnover,
                        ROW_NUMBER() OVER (PARTITION BY b.symbol, b.event_date
                                           ORDER BY b.knowledge_date DESC, b.row_id DESC) AS vintage
                 FROM bhavcopy b JOIN sessions s ON s.event_date = b.event_date
                 WHERE b.series = 'EQ' AND b.knowledge_date < :today)
        SELECT symbol, AVG(turnover) AS average, COUNT(*) AS present FROM bars
        WHERE vintage = 1 AND turnover IS NOT NULL GROUP BY symbol HAVING present >= :minimum
        ORDER BY average DESC, symbol ASC LIMIT :limit""",
        dict(today=today, n=TURNOVER_SESSIONS, minimum=MIN_SESSIONS, limit=limit)).fetchall()
    return [r[0] for r in rows]


def nightly_running() -> bool | None:
    """The scheduled task's state, read-only (schtasks /Query). None if it cannot be read."""
    try:
        done = subprocess.run(["schtasks", "/Query", "/TN", NIGHTLY_TASK, "/FO", "CSV", "/NH"],
                              capture_output=True, text=True, timeout=30,
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0 or not done.stdout.strip():
        return None
    return "running" in done.stdout.lower()


def preflight() -> list[str]:
    """Reasons not to start; empty means go. Checked before any login."""
    reasons = []
    branch = head_branch()
    if branch != NIGHTLY_BRANCH:
        reasons.append(f"HEAD is not {NIGHTLY_BRANCH} ({'unreadable' if branch is None else branch})")
    dirty = uncommitted_nightly_inputs()
    if dirty is None or dirty:
        reasons.append("the working tree could not be checked" if dirty is None
                       else f"uncommitted changes: {', '.join(dirty[:5])}")
    running = nightly_running()
    if running is not False:
        reasons.append("the nightly is running" if running else "the nightly's state could not be read")
    return reasons


def market_open(now: datetime, quote: dict) -> bool:
    """Weekday regular hours AND a fresh exchange quote; no holiday calendar exists."""
    stamp = quote.get("exchange_timestamp")
    if not stamp or now.weekday() >= 5 or not MARKET_OPEN <= now.time() < MARKET_CLOSE:
        return False
    observed = datetime.fromisoformat(stamp)
    return observed.utcoffset() is not None and 0 <= (now - observed).total_seconds() <= QUOTE_MAX_AGE


def percentile(values: list[float], q: float) -> float | None:
    """Linear interpolation between closest ranks (NumPy's default); None for no values."""
    if not values:
        return None
    ordered = sorted(values)
    k = (len(ordered) - 1) * q / 100
    low, high = int(k), min(int(k) + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (k - low)


def peak_memory_bytes() -> int | None:
    if sys.platform != "win32":
        return None

    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
    counters = Counters()
    counters.cb = ctypes.sizeof(Counters)
    kernel32, psapi = ctypes.windll.kernel32, ctypes.windll.psapi
    kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    ok = psapi.GetProcessMemoryInfo(ctypes.c_void_p(kernel32.GetCurrentProcess()), ctypes.byref(counters), counters.cb)
    return int(counters.PeakWorkingSetSize) if ok else None


class TickStore:
    """The probe's own raw tick file; insert-only, flushed in batches."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.execute("CREATE TABLE IF NOT EXISTS ticks (tier INTEGER NOT NULL, symbol TEXT NOT NULL, "
                          "exchange_ts TEXT NOT NULL, price REAL, recorded_at TEXT NOT NULL)")
        self.conn.commit()
        self.pending = []

    def add(self, row):
        self.pending.append(row)

    def flush(self):
        if self.pending:
            self.conn.executemany("INSERT INTO ticks VALUES (?, ?, ?, ?, ?)", self.pending)
            self.conn.commit()
            self.pending = []

    def size(self) -> int:
        return self.path.stat().st_size if self.path.exists() else 0

    def close(self):
        self.flush()
        self.conn.close()


class TierStats:
    """Receipt metrics for one tier, from each tick's exchange time and the wrapper's receipt time."""

    def __init__(self, tier: int, symbols: list[str], store: TickStore, started: datetime):
        self.tier, self.symbols, self.store, self.started = tier, symbols, store, started
        self.counts = dict.fromkeys(symbols, 0)
        self.lags, self.lag_at = [], []          # valid (non-negative) lags and their receipt offsets
        self.negative = self.unparsed = self.ticks = self.initial = 0
        self.last_receipt, self.max_silence = started, 0.0
        self.last_flush = started
        self.feed_error = False
        self.feed_diagnostic = None

    def on_tick(self, tick: dict):
        received = datetime.fromisoformat(tick["recorded_at"])
        self.ticks += 1
        first = not self.counts.get(tick["symbol"])
        self.counts[tick["symbol"]] = self.counts.get(tick["symbol"], 0) + 1
        self.max_silence = max(self.max_silence, (received - self.last_receipt).total_seconds())
        self.last_receipt = received
        try:
            lag = (received - datetime.fromisoformat(tick["timestamp"])).total_seconds()
        except (TypeError, ValueError):
            self.unparsed += 1
        else:
            if first:
                # The feed's snapshot on subscribing carries the last update's time, which can be
                # minutes old for a quiet symbol: counted, but kept out of the lag statistics.
                self.initial += 1
            elif lag < 0:
                self.negative += 1                # a clock or source anomaly, never clamped to zero
            else:
                self.lags.append(lag)
                self.lag_at.append((received - self.started).total_seconds())
        self.store.add((self.tier, tick["symbol"], str(tick["timestamp"]), tick.get("price"), tick["recorded_at"]))
        if len(self.store.pending) >= FLUSH_TICKS or (received - self.last_flush).total_seconds() >= FLUSH_SECONDS:
            self.store.flush()
            self.last_flush = received

    def finish(self, ended: datetime):
        self.max_silence = max(self.max_silence, (ended - self.last_receipt).total_seconds())
        self.ended = ended
        self.store.flush()


def evaluate(stats: TierStats, sentinels: list[str], required_seconds=None) -> dict:
    """Metrics and PASS/FAIL against the proposed targets; no prices."""
    duration = (stats.ended - stats.started).total_seconds()
    first = [lag for lag, at in zip(stats.lags, stats.lag_at) if at <= DRIFT_WINDOW]
    last = [lag for lag, at in zip(stats.lags, stats.lag_at) if at >= duration - DRIFT_WINDOW]
    p95_first, p95_last = percentile(first, 95), percentile(last, 95)
    drift = None if p95_first is None or p95_last is None else p95_last - p95_first
    watched = [s for s in sentinels if s in stats.counts]
    result = dict(
        tier=stats.tier, subscribed=len(stats.symbols), started=stats.started.isoformat(),
        ended=stats.ended.isoformat(), seconds=round(duration, 1), ticks=stats.ticks,
        symbols_ticking=sum(1 for n in stats.counts.values() if n), sentinels=len(watched),
        sentinels_ticking=sum(1 for s in watched if stats.counts[s]),
        lag_p50=percentile(stats.lags, 50), lag_p95=percentile(stats.lags, 95),
        lag_p99=percentile(stats.lags, 99), lag_max=max(stats.lags) if stats.lags else None,
        initial_snapshots=stats.initial, negative_lags=stats.negative, unparsed_timestamps=stats.unparsed,
        max_silence=round(stats.max_silence, 3), lag_drift=drift, feed_stopped=stats.feed_error,
        feed_diagnostic=stats.feed_diagnostic)
    reasons = []
    if stats.feed_error:
        reasons.append("the feed stopped, failed or was interrupted")
    if required_seconds is not None and duration < required_seconds:
        reasons.append('the feed did not complete the required duration')
    if not stats.ticks:
        reasons.append("no ticks received")
    if result["sentinels_ticking"] < len(watched):
        reasons.append(f"{len(watched) - result['sentinels_ticking']} liquid sentinel(s) never ticked")
    if stats.max_silence > MAX_SILENCE:
        reasons.append(f"no tick from any symbol for {stats.max_silence:.1f} s")
    if result["lag_p95"] is not None and result["lag_p95"] > P95_LIMIT:
        reasons.append(f"receipt lag p95 {result['lag_p95']:.2f} s above {P95_LIMIT} s")
    if result["lag_p99"] is not None and result["lag_p99"] > P99_LIMIT:
        reasons.append(f"receipt lag p99 {result['lag_p99']:.2f} s above {P99_LIMIT} s")
    if drift is not None and drift > DRIFT_LIMIT:
        reasons.append(f"receipt lag grew by {drift:.2f} s over the tier")
    result.update(outcome="FAIL" if reasons else "PASS", reasons=reasons)
    return result


def _fmt(value, digits=2):
    return "n/a" if value is None else f"{value:.{digits}f}"


def tier_line(r: dict) -> str:
    return (f"Tier {r['tier']}: {r['outcome']} | ticks {r['ticks']} | symbols ticking "
            f"{r['symbols_ticking']}/{r['subscribed']} | sentinels {r['sentinels_ticking']}/{r['sentinels']} | "
            f"receipt lag p50/p95/p99/max {_fmt(r['lag_p50'])}/{_fmt(r['lag_p95'])}/{_fmt(r['lag_p99'])}/"
            f"{_fmt(r['lag_max'])} s | max silence {_fmt(r['max_silence'], 1)} s | lag drift {_fmt(r['lag_drift'])} s"
            + (f" | feed category: {r['feed_diagnostic']['category']}" if r.get('feed_diagnostic') else '')
            + (f" | {'; '.join(r['reasons'])}" if r["reasons"] else ""))


def run(client=None, *, now=now_ist, tiers=None) -> int:
    """0: the probe ran (tiers may have failed); 1: failure or interruption; 2: refused to start."""
    reasons = preflight()
    if reasons:
        print("Not started: " + "; ".join(reasons) + ".")
        return 2
    started = now()
    day = started.date().isoformat()
    if started.weekday() >= 5 or not EARLIEST_START <= started.time() < MARKET_CLOSE:
        print(f"Not started: run between {EARLIEST_START:%H:%M} and {MARKET_CLOSE:%H:%M} IST on a trading day.")
        return 2
    conn = open_readonly(PRAMAN_DB)
    try:
        ranked = liquid_symbols(conn, day)
    finally:
        conn.close()                                     # released before any network work
    client = client or AngelMarketData()
    summary = dict(kind="angel_stream_capacity_probe", started=started.isoformat(), tiers=[],
                   tier_seconds=TIER_SECONDS, targets=dict(p95=P95_LIMIT, p99=P99_LIMIT, max_silence=MAX_SILENCE,
                                                           drift=DRIFT_LIMIT), ranked=len(ranked))
    stamp = started.strftime("%Y%m%d_%H%M%S")
    store = TickStore(PROBE_DIR / f"capacity_{stamp}.sqlite")
    result = 0
    try:
        with _prevent_sleep():
            client.login()
            mapped = client.download_scrip_master(ranked, as_of=day)
            symbols = [s for s in ranked if s in mapped["mapped"]]
            sentinels = symbols[:SENTINEL_COUNT]
            summary.update(mapped=len(symbols), unmapped=mapped["unmapped"], sentinel_symbols=sentinels)
            if not sentinels or not market_open(now(), client.quote(sentinels[0], as_of=day)):
                summary["stopped"] = "market not confirmed open (no fresh exchange quote)"
                return result
            for tier in (TIERS if tiers is None else tiers):
                begin = now()
                if tier > len(symbols):
                    summary["stopped"] = f"only {len(symbols)} mapped liquid symbols for tier {tier}"
                    break
                if begin + timedelta(seconds=TIER_SECONDS) > datetime.combine(begin.date(), MARKET_CLOSE, tzinfo=IST):
                    summary["stopped"] = f"tier {tier} could not finish by {MARKET_CLOSE:%H:%M}"
                    break
                if nightly_running() is not False:
                    summary["stopped"] = "the nightly started or its state could not be read"
                    break
                stats = TierStats(tier, symbols[:tier], store, begin)
                before = store.size()
                cpu = clock.process_time()
                try:
                    client.stream(symbols[:tier], stats.on_tick, as_of=day, seconds=TIER_SECONDS)
                except AngelError as exc:
                    stats.feed_error = True
                    stats.feed_diagnostic = error_details(exc)
                stats.finish(now())
                outcome = evaluate(stats, sentinels, required_seconds=TIER_SECONDS)
                outcome.update(cpu_seconds=round(clock.process_time() - cpu, 3),
                               bytes_written=store.size() - before, peak_memory_bytes=peak_memory_bytes())
                summary["tiers"].append(outcome)
                print(tier_line(outcome), flush=True)
                if outcome["outcome"] != "PASS":
                    summary["stopped"] = f"tier {tier} failed"
                    break
            else:
                summary["stopped"] = "all tiers ran"
    except (Exception, KeyboardInterrupt):
        result = 1
        summary["stopped"] = "failed or interrupted (no detail is printed)"
    finally:
        try:
            client.logout()
        except Exception:
            result = 1
        store.close()
        passing = [t["tier"] for t in summary["tiers"] if t["outcome"] == "PASS"]
        summary.update(ended=now().isoformat(), largest_passing_tier=max(passing) if passing else None,
                       tick_file=str(store.path))
        out = logs_dir() / f"angel_capacity_{stamp}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, indent=1, sort_keys=True), encoding="utf-8")
        print(f"Stopped: {summary.get('stopped')}. Largest passing tier today: "
              f"{summary['largest_passing_tier']} (one run; choose capacity only after repeat runs).")
        print(f"Summary: {out}")
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only-25', action='store_true', help='Run only the 25-symbol, 600-second tier.')
    args = parser.parse_args()
    raise SystemExit(run(tiers=(25,) if args.only_25 else None))
