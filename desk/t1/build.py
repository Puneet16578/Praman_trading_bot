"""Build the T1 inputs and features and the coverage and missingness report. No outcome.

Writes one new artifact per build, data/t1/build_<UTC stamp>.sqlite (never overwriting an earlier
one): meta (code commit, input hashes, calendar and knowledge choices), index_closes (with the
knowledge rule), market_daily, stock_daily (every stored EQ stock-day in the study, its
exclusion cause and its features). The report is returned as Markdown.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from desk.t1 import features as F
from desk.t1.inputs import KNOWLEDGE_RULE, SERIES

MARKET_COLUMNS = ("n500_prev", "n500_sma200_prev", "vix_prev", "vix_p80_prev", "v1_adverse", "share_above50",
                  "above50_valid", "net_breadth", "ad_valid", "v2_adverse", "share_above200", "new_high_rate",
                  "new_low_rate", "dispersion", "n50_prev", "n50_sma200_prev", "basket_n", "basket_mean")
STOCK_COLUMNS = ("atr_pct", "rel_ew_1", "rel_ew_5", "rel_ew_20", "rel_ew_60", "v3_negative",
                 "rel_n50_1", "rel_n50_5", "rel_n50_20", "rel_n50_60")
DESCRIPTIVE = ("share_above200", "new_high_rate", "new_low_rate", "dispersion")


def _f(x):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else float(x)


def write_artifact(path: Path, p, out, cause, period, bounds, index_closes, meta) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.executemany("INSERT INTO meta VALUES (?,?)", [(k, json.dumps(v, sort_keys=True)) for k, v in meta.items()])
        conn.execute("CREATE TABLE index_closes (series TEXT, event_date TEXT, close REAL, known_from_session TEXT, "
                     "knowledge_rule TEXT, source_kind TEXT, source_url TEXT, source_sha256 TEXT, "
                     "source_last_modified TEXT, retrieved_at TEXT, PRIMARY KEY(series, event_date))")
        pos = {d: i for i, d in enumerate(p.sessions)}
        rows = []
        for s in SERIES:
            for d, r in sorted(index_closes[s].items()):
                i = pos.get(d)
                nxt = p.sessions[i + 1] if i is not None and i + 1 < len(p.sessions) else None
                rows.append((s, d, r["close"], nxt, KNOWLEDGE_RULE, r["source_kind"], r["source_url"], r["source_sha256"],
                             r["source_last_modified"], r["retrieved_at"]))
        conn.executemany("INSERT INTO index_closes VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
        conn.execute("CREATE TABLE market_daily (session TEXT PRIMARY KEY, period TEXT, "
                     + ", ".join(f"{c} REAL" for c in MARKET_COLUMNS) + ")")
        conn.executemany(f"INSERT INTO market_daily VALUES ({','.join('?' * (2 + len(MARKET_COLUMNS)))})",
                         [(d, period[i], *(_f(out[c][i]) for c in MARKET_COLUMNS)) for i, d in enumerate(p.sessions)])
        conn.execute("CREATE TABLE stock_daily (session TEXT, symbol TEXT, period TEXT, cause TEXT, quintile REAL, "
                     + ", ".join(f"{c} REAL" for c in STOCK_COLUMNS) + ", PRIMARY KEY(session, symbol))")
        q = F.quintile(out["atr_pct"], bounds)
        stored = np.argwhere(~np.isnan(p.raw_close))
        batch = []
        for i, j in stored:
            if period[i] == "outside":
                continue
            elig = cause[i, j] == ""
            batch.append((p.sessions[i], p.symbols[j], period[i], cause[i, j], _f(q[i, j]) if elig else None,
                          *(_f(out[c][i, j]) for c in STOCK_COLUMNS)))
        conn.executemany(f"INSERT INTO stock_daily VALUES ({','.join('?' * (5 + len(STOCK_COLUMNS)))})", batch)
        conn.commit()
    finally:
        conn.close()


def _runs(days: list[str], all_days: list[str]) -> list[tuple[str, str, int]]:
    pos = {d: i for i, d in enumerate(all_days)}
    runs, start, prev = [], None, None
    for d in days:
        i = pos[d]
        if start is not None and i == prev + 1:
            prev = i
            continue
        if start is not None:
            runs.append((all_days[start], all_days[prev], prev - start + 1))
        start = prev = i
    if start is not None:
        runs.append((all_days[start], all_days[prev], prev - start + 1))
    return runs


def report(p, out, cause, period, bounds, index_closes, meta, late_sessions) -> str:
    sessions = p.sessions
    study = [i for i in range(len(sessions)) if period[i] != "outside"]
    years = sorted({sessions[i][:4] for i in study})
    L = []
    L += ["# T1 inputs and features: coverage and missingness (addendum 3)", "",
          "Built from the approved sources; **no outcome was loaded or computed** (no adverse20, no forward price). "
          "This report is for the user's review before any outcome analysis.", "",
          f"Build: `{meta['artifact']}`; code commit `{meta['code_commit']}`; Praman store "
          f"`{meta['praman_db_sha256'][:16]}...`; {len(meta['index_files'])} index source files hashed in the artifact's meta.", ""]
    L += ["## Calendar of global sessions", "",
          f"{len(sessions)} sessions from {sessions[0]} to {sessions[-1]}: before 2019-10-01 the official index's weekday "
          "sessions (stock data start on 2019-10-01); from then the store's sessions plus any weekday index session the "
          "store lacks.", "",
          f"- Weekday sessions in the official index but missing from Praman's store (every stock missing that day): "
          f"{', '.join(p.store_missing_sessions) or 'none'}.",
          f"- Weekend index sessions excluded from inputs and forward windows: {', '.join(p.weekend_specials)}.", ""]
    L += ["## Official index inputs", "",
          f"Knowledge rule: {KNOWLEDGE_RULE}. Source: niftyindices' historical-data endpoint (one response per series and "
          "year), with sessions it lacks taken from the dated Daily Snapshot files.", "",
          "| Series | Year | Calendar sessions | Values | From snapshot files | First | Last | UNKNOWN sessions |",
          "|---|---|---|---|---|---|---|---|"]
    pos = {d: i for i, d in enumerate(sessions)}
    for s in SERIES:
        for y in sorted({d[:4] for d in sessions}):
            cal = [d for d in sessions if d[:4] == y]
            have = [d for d in cal if d in index_closes[s]]
            snap = [d for d in have if index_closes[s][d]["source_kind"] == "daily-snapshot"]
            unknown = [d for d in cal if d not in index_closes[s]]
            L.append(f"| {s} | {y} | {len(cal)} | {len(have)} | {len(snap)} | {have[0] if have else '-'} | "
                     f"{have[-1] if have else '-'} | {', '.join(unknown) or 'none'} |")
    L += ["", "Cross-check against the 16 dated phase 1 files: index closes identical on all 48 series-dates; India VIX "
          "open, high or low differ on 6 dates only by rounding (four decimals in the daily files, two in the history).",
          ""]
    L += ["## Stock bars (Praman store, EQ series)", "",
          "ASSUMPTION (addendum 3): session D's EQ bar is available at the end-of-session decision D "
          "when its stored knowledge date permits. Later-known bars remain unavailable until that date.", "",
          "| Year | Stored stock-days | Known the same day | Known 1-3 days later | Known later |", "|---|---|---|---|---|"]
    stored = ~np.isnan(p.raw_close)
    idx = np.arange(len(sessions))[:, None]
    for y in years:
        rows = np.array([sessions[i][:4] == y and period[i] != "outside" for i in range(len(sessions))])
        sel = stored & rows[:, None]
        lag = (p.known - idx)
        L.append(f"| {y} | {int(sel.sum())} | {int((sel & (lag == 0)).sum())} | {int((sel & (lag >= 1) & (lag <= 3)).sum())} | "
                 f"{int((sel & (lag > 3)).sum())} |")
    L += ["", "Sessions whose bars the store dates as known much later (archive files rewritten after the session); "
          "under the pre-registration's knowledge rule every window containing one is UNKNOWN until that date. "
          "Retained missing inputs under addendum 3:", ""]
    for d, k, n in late_sessions:
        L.append(f"- {d}: {n} bars, known {k}")
    L += [""]
    L += ["## Identity and the primary population", "",
          f"ASSUMPTION (addendum 3): equity identity uses the latest dated ISIN snapshot strictly before the session that lists the symbol "
          f"({', '.join(meta['isin_snapshots'])}); a resolved non-INF ISIN is equity. No stitching across renames. "
          "October 2026 download dates are not used as historical availability.", "",
          f"Development stock-days excluded because no earlier snapshot lists the symbol: "
          f"{int(((period == 'development')[:, None] & (cause == 'identity_unknown')).sum()):,}.", "",
          "| Year | Stock-days | Eligible | Identity unknown | Fund unit | Bar not known by decision | ATR window incomplete | ATR window unadjustable |",
          "|---|---|---|---|---|---|---|---|"]
    for y in years:
        rows = np.array([sessions[i][:4] == y and period[i] != "outside" for i in range(len(sessions))])
        c = Counter(cause[rows][stored[rows]].tolist())
        total = sum(c.values())
        L.append(f"| {y} | {total} | {c['']} | {c['identity_unknown']} | {c['fund_unit']} | {c['bar_not_known_by_decision']} | "
                 f"{c['atr_window_incomplete']} | {c['atr_window_unadjustable']} |")
    L += [""]

    def first_last(mask_days):
        return (mask_days[0], mask_days[-1]) if mask_days else ("-", "-")
    L += ["## Market states (per decision session)", "",
          "| Feature | Year | Adverse | Other | UNKNOWN | First usable | Last usable |", "|---|---|---|---|---|---|---|"]
    for key, label in (("v1_adverse", "V1 market regime"), ("v2_adverse", "V2 weak breadth")):
        for y in years:
            days = [i for i in study if sessions[i][:4] == y]
            v = out[key]
            usable = [sessions[i] for i in days if np.isfinite(v[i])]
            fl = first_last(usable)
            L.append(f"| {label} | {y} | {sum(v[i] == 1 for i in days)} | {sum(v[i] == 0 for i in days)} | "
                     f"{sum(not np.isfinite(v[i]) for i in days)} | {fl[0]} | {fl[1]} |")
    for key, label in (("v1_adverse", "V1"), ("v2_adverse", "V2")):
        unknown = [sessions[i] for i in study if not np.isfinite(out[key][i])]
        L += ["", f"{label} UNKNOWN sessions, as runs: "
              + ("none" if not unknown else "; ".join(f"{a}..{b} ({n})" for a, b, n in _runs(unknown, sessions)))]
    L += ["", "## Stock-level features (eligible stock-days)", "",
          "| Feature | Year | Eligible stock-days | Known | UNKNOWN | First usable | Last usable |", "|---|---|---|---|---|---|---|"]
    elig = (cause == "")
    for key in ("atr_pct", "v3_negative", "rel_ew_1", "rel_ew_5", "rel_ew_60", "rel_n50_1", "rel_n50_20", "rel_n50_60"):
        for y in years:
            rows = np.array([sessions[i][:4] == y and period[i] != "outside" for i in range(len(sessions))])
            sel = elig & rows[:, None]
            known = sel & np.isfinite(out[key])
            dk = [sessions[i] for i in range(len(sessions)) if known[i].any()]
            fl = first_last(dk)
            L.append(f"| {key} | {y} | {int(sel.sum())} | {int(known.sum())} | {int((sel & ~np.isfinite(out[key])).sum())} | "
                     f"{fl[0]} | {fl[1]} |")
    neg = elig & (out["v3_negative"] == 1)
    L += ["", f"V3 split on eligible stock-days: negative {int(neg.sum())}, zero or positive "
          f"{int((elig & (out['v3_negative'] == 0)).sum())}, UNKNOWN {int((elig & ~np.isfinite(out['v3_negative'])).sum())}.", ""]
    L += ["## Descriptive context (no contrast is run on these)", "", "| Feature | Year | Sessions known | UNKNOWN |", "|---|---|---|---|"]
    for key in DESCRIPTIVE + ("n50_sma200_prev",):
        for y in years:
            days = [i for i in study if sessions[i][:4] == y]
            known = sum(np.isfinite(out[key][i]) for i in days)
            L.append(f"| {key} | {y} | {known} | {len(days) - known} |")
    counts = Counter(period[i] for i in study)
    L += ["", "## Periods and volatility quintiles", "",
          f"Decision sessions: development {counts['development']}, development purged (20th forward session in 2025) "
          f"{counts['development_purged']}, hold-out 2025 {counts['holdout_2025']}, hold-out censored (20th forward "
          f"session in 2026) {counts['holdout_censored']}.", "",
          f"Development-only ATR% boundaries (NumPy linear 20/40/60/80 percentiles over "
          f"{int(((period == 'development')[:, None] & elig & np.isfinite(out['atr_pct'])).sum())} eligible development "
          f"stock-days): {', '.join(f'{b:.4f}' for b in bounds)}. Frozen for 2025 and every bootstrap draw.", ""]
    L += ["## Spells of the adverse states (T1 addendum 1)", "",
          "Runs of adverse sessions among the period's decision sessions; runs fewer than 20 known non-adverse sessions "
          "apart merge; UNKNOWN sessions never separate them. At least 5 per period are required.", ""]
    for key, label in (("v1_adverse", "V1"), ("v2_adverse", "V2")):
        for per, name in (("development", "development"), ("holdout_2025", "hold-out 2025")):
            states = [(sessions[i], None if not np.isfinite(out[key][i]) else bool(out[key][i])) for i in study
                      if period[i] == per or (per == "holdout_2025" and period[i] == "holdout_censored")]
            sp = F.spells(states)
            L.append(f"- {label}, {name}: {len(sp)} spell(s)"
                     + (": " + "; ".join(f"{s['first']}..{s['last']} ({s['adverse_sessions']} adverse)" for s in sp) if sp else ""))
    L += ["", "## Fixed coverage rules (addendum 3)", "",
          "1. The sessions known much later (above): retain their stored knowledge dates; no previous-close filling.",
          "2. The weekday session missing from the store (2022-08-08): a Praman data gap; every window across it is UNKNOWN.",
          "3. Every weekend session is excluded from the calendar.",
          "4. Identity is UNKNOWN through the first snapshot date (2019-11-15) and for symbols listed between snapshots until the "
          "session after a snapshot first lists them.", ""]
    return "\n".join(L) + "\n"


def late_known_sessions(praman_conn) -> list[tuple[str, str, int]]:
    return [tuple(r) for r in praman_conn.execute(
        "SELECT event_date, MIN(knowledge_date), COUNT(*) FROM bhavcopy WHERE series='EQ' AND event_date BETWEEN ? AND ? "
        "AND julianday(knowledge_date) - julianday(event_date) > 3 GROUP BY event_date ORDER BY 1",
        (F.STUDY_START, F.DEVELOPMENT_END))]


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
