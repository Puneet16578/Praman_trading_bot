"""T1 sourcing requests (user approvals of 2026-10-14). Phase 1, the probe: at most 64 requests.
Phase 2, the history downloads: at most 60, in their own ledger. Both: at least 10 seconds apart,
never while the nightly runs. Sourcing only: no feature, outcome or store write.

Every request is appended to data/raw/t1_sources/requests.jsonl before it is sent and completed
after: method, URL, parameters, start time, HTTP status, the response's Date and Last-Modified
headers (the publication evidence the user asked to keep), content type and length, ETag, and the
SHA-256 of the saved body (data/raw/t1_sources/<n>_<label>.<ext>). The ledger enforces the budget
and the spacing across invocations. The first HTTP 403 or 429 stops the probe for good.

Run one batch at a time, each well under ten minutes:
    python -B scripts/t1_source_probe.py [--phase 2] <batch>
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shared.market_time import IST

OUT = ROOT / "data" / "raw" / "t1_sources"
LEDGER = OUT / "requests.jsonl"
BUDGET = 64
PHASES = {1: (OUT, LEDGER, 64), 2: (OUT / "phase2", OUT / "phase2" / "requests.jsonl", 60)}


def use_phase(phase: int) -> None:
    """Point the ledger, output folder and budget at one phase's approval."""
    global OUT, LEDGER, BUDGET
    OUT, LEDGER, BUDGET = PHASES[phase]
SPACING = 10.0                                   # seconds between request starts
NIGHTLY_WINDOW = ((17, 30), (21, 30))            # IST; the nightly's usual hours, kept clear
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/128.0 Safari/537.36", "Accept-Language": "en-US,en;q=0.9"}
KEPT_HEADERS = ("Date", "Last-Modified", "Content-Type", "Content-Length", "ETag")

# Two dates per year, September 2018 (warm-up) to 2025; weekdays chosen before any request.
SAMPLE_DATES = [date(2018, 9, 3), date(2018, 12, 3), date(2019, 2, 4), date(2019, 8, 1), date(2020, 2, 3),
                date(2020, 8, 3), date(2021, 2, 3), date(2021, 8, 3), date(2022, 2, 3), date(2022, 8, 3),
                date(2023, 2, 3), date(2023, 8, 3), date(2024, 2, 5), date(2024, 8, 5), date(2025, 2, 4),
                date(2025, 8, 4)]


class ProbeStopped(RuntimeError):
    pass


def ledger() -> list[dict]:
    if not LEDGER.exists():
        return []
    return [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines() if line.strip()]


def nightly_running() -> bool | None:
    try:
        done = subprocess.run(["schtasks", "/Query", "/TN", "PramanDailyIngest", "/FO", "CSV", "/NH"],
                              capture_output=True, text=True, timeout=30,
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0 or not done.stdout.strip():
        return None
    return "running" in done.stdout.lower()


def check_allowed(now: datetime, entries: list[dict]) -> None:
    """Raise ProbeStopped unless one more request is within the approved limits."""
    if any(e.get("status") in (403, 429) for e in entries):
        raise ProbeStopped("an earlier request was refused (403/429); the probe stays stopped")
    if len(entries) >= BUDGET:
        raise ProbeStopped(f"the {BUDGET}-request budget is used")
    local = now.astimezone(IST)
    (start_h, start_m), (end_h, end_m) = NIGHTLY_WINDOW
    if (start_h, start_m) <= (local.hour, local.minute) < (end_h, end_m):
        raise ProbeStopped("inside the nightly's hours (17:30-21:30 IST)")
    if nightly_running() is not False:
        raise ProbeStopped("the nightly is running or its state could not be read")


def wait_for_spacing(entries: list[dict], sleep=time.sleep, clock=lambda: datetime.now(timezone.utc)) -> None:
    if entries:
        last = datetime.fromisoformat(entries[-1]["started_at"])
        gap = SPACING - (clock() - last).total_seconds()
        if gap > 0:
            sleep(gap + 0.5)


def fetch(session, label: str, method: str, url: str, *, params=None, json_body=None, data=None,
          headers=None, ext="bin", sleep=time.sleep) -> dict:
    """One budgeted, logged request. Returns the ledger entry (with `body` bytes when HTTP 200)."""
    OUT.mkdir(parents=True, exist_ok=True)
    entries = ledger()
    wait_for_spacing(entries, sleep=sleep)
    check_allowed(datetime.now(timezone.utc), entries)
    n = len(entries) + 1
    entry = dict(n=n, label=label, method=method, url=url, params=params, json=json_body,
                 started_at=datetime.now(timezone.utc).isoformat())
    with LEDGER.open("a", encoding="utf-8") as f:              # recorded before it is sent
        f.write(json.dumps(entry, sort_keys=True) + "\n")
    try:
        response = session.request(method, url, params=params, json=json_body, data=data, timeout=40,
                                   allow_redirects=False, headers={**HEADERS, **(headers or {})})
        body = response.content
        path = OUT / f"{n:02d}_{re.sub(r'[^A-Za-z0-9_.-]', '_', label)}.{ext}"
        path.write_bytes(body)
        entry.update(status=response.status_code, headers={k: response.headers.get(k) for k in KEPT_HEADERS},
                     bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), file=path.name)
    except Exception as exc:                                      # no detail beyond the type
        entry.update(status=None, error_type=type(exc).__name__)
        body = None
    entry["seconds"] = round((datetime.now(timezone.utc) - datetime.fromisoformat(entry["started_at"])).total_seconds(), 3)
    lines = LEDGER.read_text(encoding="utf-8").splitlines()
    lines[-1] = json.dumps(entry, sort_keys=True)                  # complete this request's own line
    LEDGER.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{n:02d} {method} {url} -> {entry.get('status')} {entry.get('headers', {}).get('Last-Modified')}", flush=True)
    if entry.get("status") in (403, 429):
        raise ProbeStopped(f"HTTP {entry['status']} from {url}; stopping")
    return entry | dict(body=body if entry.get("status") == 200 else None)


def ddmmyyyy(d: date) -> str:
    return d.strftime("%d%m%Y")


def batch_js(session):
    fetch(session, "historicalData_js", "GET", "https://liveindexsa.niftyindices.com/assets/js/historicalData.js", ext="js")


def batch_snapshot(session, dates=SAMPLE_DATES):
    for d in dates:
        fetch(session, f"snapshot_{d.isoformat()}", "GET",
              f"https://www.niftyindices.com/Daily_Snapshot/ind_close_all_{ddmmyyyy(d)}.csv", ext="csv")


def batch_mirror(session, dates=SAMPLE_DATES[:8]):
    for d in dates:
        fetch(session, f"nse_mirror_{d.isoformat()}", "GET",
              f"https://nsearchives.nseindia.com/content/indices/ind_close_all_{ddmmyyyy(d)}.csv", ext="csv")


def batch_components_js(session):
    fetch(session, "IISLComponet_js", "GET", "https://liveindexsa.niftyindices.com/assets/js/IISLComponet.js", ext="js")


# Phase 2: niftyindices' own historical-data endpoints (found in IISLComponet.js), at most one year
# per request, dates as the form sends them ("dd-Mon-yyyy").
HISTORY_URL = "https://www.niftyindices.com/BackPage/getHistoricaldatatabletoString"
VIX_URL = "https://www.niftyindices.com/BackPage/BindHistoricalIndiaVixData"
FORM_HEADERS = {"Content-Type": "application/json; charset=utf-8", "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://www.niftyindices.com", "Referer": "https://www.niftyindices.com/reports/historical-data"}
YEAR_WINDOWS = [(date(2018, 9, 1), date(2018, 12, 31))] + [(date(y, 1, 1), date(y, 12, 31)) for y in range(2019, 2026)]


def form_date(d: date) -> str:
    return d.strftime("%d-%b-%Y")


def batch_history(session, indices=("NIFTY 50", "NIFTY 500"), windows=YEAR_WINDOWS):
    for index in indices:
        for start, end in windows:
            cinfo = (f"{{'name':'{index}','startDate':'{form_date(start)}','endDate':'{form_date(end)}',"
                     f"'indexName':'{index}'}}")
            fetch(session, f"history_{index.replace(' ', '')}_{start.isoformat()}_{end.isoformat()}", "POST",
                  HISTORY_URL, json_body=dict(cinfo=cinfo), headers=FORM_HEADERS, ext="json")


def batch_history_first(session):
    batch_history(session, indices=("NIFTY 50",), windows=YEAR_WINDOWS[:1])


def batch_history_rest(session):
    batch_history(session, indices=("NIFTY 50",), windows=YEAR_WINDOWS[1:])
    batch_history(session, indices=("NIFTY 500",))


def batch_vix(session, windows=YEAR_WINDOWS):
    for start, end in windows:
        body = f"{{'name':'India Vix','startDate':'{form_date(start)}','endDate':'{form_date(end)}'}}"
        fetch(session, f"vix_{start.isoformat()}_{end.isoformat()}", "POST", VIX_URL, data=body.encode(),
              headers=FORM_HEADERS, ext="json")


def batch_vix_history_first(session):
    """The VIX form's own endpoint is gone (all 8 requests redirected to a 404 page); India VIX is
    in the index list, so the index-history endpoint is tried once first."""
    batch_history(session, indices=("INDIA VIX",), windows=YEAR_WINDOWS[:1])


def batch_vix_history_rest(session):
    batch_history(session, indices=("INDIA VIX",), windows=YEAR_WINDOWS[1:])


VIX_GAP_DATES = [date(2021, 4, 26), date(2021, 4, 28), date(2022, 9, 26), date(2022, 9, 27), date(2022, 9, 30),
                 date(2022, 10, 3), date(2022, 11, 1), date(2022, 11, 2)]


def batch_vix_gaps(session):
    """The 8 sessions the India VIX history lacks, from the dated Daily Snapshot files."""
    batch_snapshot(session, dates=VIX_GAP_DATES)


BATCHES = dict(js=batch_js, snapshot=batch_snapshot, mirror=batch_mirror, components_js=batch_components_js,
               history_first=batch_history_first, history_rest=batch_history_rest, vix=batch_vix,
               vix_history_first=batch_vix_history_first, vix_history_rest=batch_vix_history_rest,
               vix_gaps=batch_vix_gaps)
PHASE_2_BATCHES = {"components_js", "history_first", "history_rest", "vix", "vix_history_first", "vix_history_rest",
                   "vix_gaps"}


def main(argv=None) -> int:
    import requests
    argv = sys.argv[1:] if argv is None else argv
    phase = 1
    if argv[:1] == ["--phase"] and len(argv) >= 2:
        phase, argv = int(argv[1]), argv[2:]
    if len(argv) != 1 or argv[0] not in BATCHES or (argv[0] in PHASE_2_BATCHES) != (phase == 2):
        print(f"usage: t1_source_probe.py [--phase 2] {{{'|'.join(BATCHES)}}}")
        return 2
    use_phase(phase)
    session = requests.Session()
    try:
        BATCHES[argv[0]](session)
    except ProbeStopped as exc:
        print(f"Stopped: {exc}.")
        return 1
    finally:
        session.close()
    print(f"Requests used: {len(ledger())} of {BUDGET}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
