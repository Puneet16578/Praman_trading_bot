"""T1 rehearsal on the real store, with the outcome replaced by seeded random labels (user decision
2026-10-18). No outcome is read; the real reader is sealed for the whole run.

    python -B scripts/t1_rehearsal.py

Reads Praman's store read-only and the cached T1 inputs, builds the development panel (ending
2024-12-31, weekend sessions left out: approved addendum 3 (b)), computes
the features, and runs the development pipeline on random labels (desk/t1_outcome/rehearsal.py) with
addendum 3's choices (e)-(h). Writes data/t1/rehearsal_<stamp>.json (not committed) and prints a
summary. Never during the nightly. The real development run is a separate step, not built here.
"""
from __future__ import annotations

import ctypes
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from desk.t1 import features as F, inputs                                       # noqa: E402
from desk.t1.panel import load_panel, snapshot_identities                        # noqa: E402
from desk.t1_outcome.rehearsal import REHEARSAL_RATE, REHEARSAL_SEED, outcomes_sealed, rehearse  # noqa: E402
from shared.sqlite_readonly import open_readonly                                 # noqa: E402

PRAMAN_DB = ROOT / "data" / "processed" / "praman.db"
RAW = ROOT / "data" / "raw" / "t1_sources"
ISIN = ROOT / "data" / "raw" / "isin_snapshots"
CHOICES = dict(weekends="exclude", coverage_numerator="state_known", usable="computable_with_sample_minimums",
               method="linear", bootstrap_dates="development sessions after (b), up to the last before the purged ones")


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


@outcomes_sealed()
def main() -> int:
    F.refuse_outside_study(F.DEVELOPMENT_END)
    clock = {"start": time.perf_counter()}
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    index_closes, mismatches = inputs.load(RAW)
    if mismatches:
        raise SystemExit(f"Index close mismatches between sources: {mismatches}")
    snapshots = snapshot_identities(ISIN)
    conn = open_readonly(PRAMAN_DB)
    try:
        panel = load_panel(conn, index_closes, snapshots, end=F.DEVELOPMENT_END, weekends=CHOICES["weekends"])
    finally:
        conn.close()
    clock["loaded"] = time.perf_counter()
    out = F.compute(panel)
    cause = F.exclusion_causes(panel)
    period = F.periods(panel.sessions, panel.forward_sessions)
    bounds = F.quintile_bounds(out["atr_pct"], cause, period)
    clock["features"] = time.perf_counter()
    report = rehearse(panel, out, cause, period, bounds, seed=REHEARSAL_SEED, rate=REHEARSAL_RATE,
                          usable=CHOICES["usable"], method=CHOICES["method"],
                          coverage_numerator=CHOICES["coverage_numerator"])
    clock["rehearsal"] = time.perf_counter()
    report.update(
        kind="t1_rehearsal_random_labels", code_commit=commit, outcomes="none read; random labels",
        source_sha256={str(p.relative_to(ROOT)): __import__('hashlib').sha256(p.read_bytes()).hexdigest()
                       for p in sorted([* (ROOT / 'desk' / 't1').glob('*.py'),
                                        * (ROOT / 'desk' / 't1_outcome').glob('*.py'), Path(__file__)])},
        seed=REHEARSAL_SEED, label_rate=REHEARSAL_RATE, choices=CHOICES, quintile_bounds=bounds,
        timing_assumptions=dict(stock_eq="same-session when stored knowledge date permits; addendum 3",
                                index_vix="D-1; addendum 2", isin="strictly after snapshot date; addendum 3"),
        panel=dict(sessions=len(panel.sessions), symbols=len(panel.symbols), first=panel.sessions[0],
                   last=panel.sessions[-1], store_missing_sessions=panel.store_missing_sessions,
                   weekend_specials_left_out=[d for d in panel.weekend_specials if d <= F.DEVELOPMENT_END]),
        seconds=dict(load=round(clock["loaded"] - clock["start"], 1),
                     features=round(clock["features"] - clock["loaded"], 1),
                     rehearsal=round(clock["rehearsal"] - clock["features"], 1),
                     total=round(clock["rehearsal"] - clock["start"], 1)),
        peak_memory_bytes=peak_memory_bytes())
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = ROOT / "data" / "t1" / f"rehearsal_{stamp}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("seconds", "peak_memory_bytes", "development_sessions",
                                              "eligible_stock_days", "complete_windows")}, indent=1))
    print(f"Report: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
