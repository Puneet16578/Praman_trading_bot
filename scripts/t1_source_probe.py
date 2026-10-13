"""T1 sourcing probe, phase 1 (user approval 2026-10-14): at most 64 requests in total, at least 10
seconds apart, never while the nightly runs. Sourcing only: no feature, outcome or store write.

Every request is appended to data/raw/t1_sources/requests.jsonl before it is sent and completed
after: method, URL, parameters, start time, HTTP status, the response's Date and Last-Modified
headers (the publication evidence the user asked to keep), content type and length, ETag, and the
SHA-256 of the saved body (data/raw/t1_sources/<n>_<label>.<ext>). The ledger enforces the budget
and the spacing across invocations. The first HTTP 403 or 429 stops the probe for good.

Run one batch at a time, each well under ten minutes:
    python -B scripts/t1_source_probe.py <batch>
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


BATCHES = dict(js=batch_js, snapshot=batch_snapshot, mirror=batch_mirror)


def main(argv=None) -> int:
    import requests
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1 or argv[0] not in BATCHES:
        print(f"usage: t1_source_probe.py {{{'|'.join(BATCHES)}}}")
        return 2
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
