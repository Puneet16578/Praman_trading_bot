"""One entry point for scheduled, unattended ingestion: bhavcopy -> corporate announcements -> ISIN
map refresh -> corporate actions -> ASM/GSM circulars -> TODAY's bhavcopy (with retry), in that
order, then a dated summary block appended to `logs/weekly_ingest.log`.

**Now run daily on trading weekday evenings, not weekly** (Desk Phase 1 post-STOP-3 review,
docs/OPERATIONS.md's "Daily ingestion" section) -- kept this filename/log path rather than renaming,
since `scripts/weekly_ingest.py` and `logs/weekly_ingest.log` are cited by name throughout
docs/DEFECT_REGISTER.md and docs/phase10_*.md's dated, historical accounts of real incidents found
while building it; renaming the file would make those citations point nowhere, for a rename that
changes nothing about what the script does. The cadence changed; the identity of "the ingestion
script that appends to weekly_ingest.log" did not.

The four original steps are UNCHANGED -- `step_bhavcopy` (via `ingest_bhavcopy_full_history.main()`)
still deliberately requests only THROUGH YESTERDAY (see that module's own `end_date` default), which
was correct for a Monday-morning weekly cadence but is now, by itself, one day behind for a same-day
evening run. `step_bhavcopy_today` (new, last in STEPS) closes that gap: it specifically requests
TODAY's date, retrying if NSE has not published it yet by the time this runs (a normal possibility
on an evening run started right after market close), and reports plainly if it is still not out
after the retry budget -- never guessing, never fabricating a placeholder row.

ISIN map (Amendment 4, docs/phase10_preregistration_amendment4.md §1): refreshes
data/raw/nse_symbol_isin_current.json (scripts/build_isin_map.py) before corporate_actions runs,
so P8-010's ISIN-based symbol resolution and the equity-only universe rule both see a current
snapshot for any symbol newly listed or newly renamed this week.

Corporate actions (docs/phase10_preregistration_amendment3.md): without this step, a forward-window
split or bonus goes unadjusted -- a 1:2 split reads as a spurious -50% single-day return, producing
a fabricated catalogue event and a false "underperformed" label for any event whose 90-session
window spans the ex-date. The pre-registration's 5%-missing-data COMPROMISED rule cannot catch this
-- the row is present and looks complete, it is just wrong, the same class of silent-failure this
project's own CLAUDE.md warns adjusted-return code about explicitly.

Idempotent and safe to re-run or run late, by design, inherited from each underlying step:
  - bhavcopy (`scripts/ingest_bhavcopy_full_history.py`) skips every weekday already confirmed in
    the store before making a network call.
  - announcements (`scripts/ingest_announcements_full_history.py`) skips every symbol already
    fetched.
  - corporate actions (`src/ingestion/nse_market_data/corporate_actions.py`'s `fetch_recent`) is
    called over a deliberately overlapping trailing window (`CORPORATE_ACTIONS_LOOKBACK_DAYS`),
    safe for the same P4-009 duplicate-business-key reason as ASM/GSM below -- same tier logic
    (announcement-derived knowledge_date, subject-field ratio, quarantine on disagreement) and the
    same demerger/capital-reduction exclusion-marker handling as the historical ingestion path,
    unchanged, since `fetch_recent` differs from `fetch_all` only in HOW it fetches (a narrow
    window vs. whole calendar years), not in how what it fetches gets written.
  - ASM/GSM (`src/ingestion/nse_market_data/{asm,gsm}.py`'s `fetch_and_ingest_*_range`) is called
    over a deliberately overlapping trailing window (`ASM_GSM_LOOKBACK_DAYS`, not just "since last
    Monday"), safe because `write_facts`'s own duplicate detection (P4-009,
    docs/DEFECT_REGISTER.md) skips an already-stored event rather than erroring or duplicating --
    re-sweeping the same circulars weekly is a deliberate safety margin against a missed run, not
    a bug.
  - bhavcopy_today calls the same `ingest_bhavcopy_date` used above, so it inherits the exact same
    duplicate-write safety -- re-running this whole script a second time the same evening (e.g. a
    manual retry) re-requests today's date harmlessly if it already succeeded.

Deliberately does NOT reuse `scripts/ingest_asm_gsm_sample.py` -- that script hardcodes a path
into a PAST Claude session's own temp scratchpad directory as its circular-index source, which is
ephemeral and not something a scheduled task can depend on existing. This script instead calls
`fetch_and_ingest_asm_range`/`fetch_and_ingest_gsm_range` directly, which fetch the circular index
live over the network for the given date range -- no cached-index dependency at all.

Every step's stdout is captured (not just its exit status) so this script can surface the two
things a human running this unattended actually needs to see without reading the full log every
week: any bhavcopy GAP, and specifically any GAP whose reason names NSE's fallback-window mismatch
shape (P2-003, docs/DEFECT_REGISTER.md -- the archive silently serving a different date's file).
"""
from __future__ import annotations
import contextlib
import io
import re
import sys
import traceback
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))    # this script's own dir (scripts/ has no __init__.py)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # project root, for `src.*` imports

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "logs" / "weekly_ingest.log"
ASM_GSM_LOOKBACK_DAYS = 30  # widened from 10 (P8-007 scoping, docs/phase10_p8007_scoping.md): a
                            # single circular-index call was observed to return an incomplete
                            # result once; fetch_and_ingest_{asm,gsm}_range now union two index
                            # calls internally (fetch_circular_index_union), and this window is
                            # widened as a second, independent layer of the same defense
CORPORATE_ACTIONS_LOOKBACK_DAYS = 60  # matches fetch_recent's own default; stated here too so a
                                       # change to one is not silently out of sync with the other

# Daily evening run (Desk Phase 1 post-STOP-3 review): NSE typically publishes the full bhavcopy
# shortly after market close, but "shortly after" is not guaranteed -- retry rather than report a
# false GAP for a file that simply is not out yet. 6 attempts * 15 minutes = 90 minutes of retry
# budget; PROPOSED, not measured against NSE's actual publish-time distribution, stated here so a
# real late-publish pattern can be used to retune it later rather than silently guessed at again.
BHAVCOPY_TODAY_MAX_ATTEMPTS = 6
BHAVCOPY_TODAY_RETRY_DELAY_SECONDS = 15 * 60


def step_bhavcopy() -> None:
    from ingest_bhavcopy_full_history import main as bhavcopy_main
    bhavcopy_main()


def step_announcements() -> None:
    from ingest_announcements_full_history import main as announcements_main
    announcements_main()


def step_isin_map() -> None:
    """Amendment 4 (docs/phase10_preregistration_amendment4.md §1): refreshes
    data/raw/nse_symbol_isin_current.json with a fresh CM/UDiFF snapshot before corporate_actions
    runs, so a symbol newly listed or newly renamed this week resolves (or is correctly counted as
    unresolved) within the week it starts appearing, not discovered after the fact. Must run
    BEFORE step_corporate_actions, which loads this same file."""
    from build_isin_map import main as isin_map_main
    isin_map_main()


def step_corporate_actions() -> None:
    from pathlib import Path
    from src.bitemporal.connection import get_connection, init_db
    from src.config.settings import get_settings
    from src.ingestion.nse_market_data.corporate_actions import fetch_recent, ingest_corporate_actions
    from src.ingestion.nse_market_data.isin_mapping import load_isin_map

    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)
    print(f"[CORP_ACTIONS] sweeping trailing {CORPORATE_ACTIONS_LOOKBACK_DAYS} days")

    actions, announcements_by_key = fetch_recent(lookback_days=CORPORATE_ACTIONS_LOOKBACK_DAYS)
    print(f"[CORP_ACTIONS] fetched {len(actions)} actions, {len(announcements_by_key)} announcement windows")

    # P8-010: resolve a renamed security's action back to whichever symbol was actually trading on
    # its ex_date (this project's OWN bhavcopy symbol), not NSE's live, current-symbol-only report.
    # Missing map file is not fatal -- falls back to the pre-P8-010 behavior (raw symbol as-is), a
    # fresh clone without a built ISIN map must still be able to run this step (P8-006's lesson).
    isin_map_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "nse_symbol_isin_current.json"
    isin_map = load_isin_map(isin_map_path) if isin_map_path.exists() else None
    if isin_map is None:
        print(f"[CORP_ACTIONS] no ISIN map at {isin_map_path} -- symbol resolution skipped "
              f"(run scripts/build_isin_map.py to enable it)")

    report, write_result = ingest_corporate_actions(conn, actions, announcements_by_key,
                                                      source_file="weekly_ingest_fetch_recent", isin_map=isin_map)
    total = sum(report.tier_counts.values())
    print(f"[CORP_ACTIONS] tier_counts={dict(report.tier_counts)} total_rows_built={total}")
    print(f"[CORP_ACTIONS] inserted={write_result.inserted} skipped_duplicate={write_result.skipped_duplicate}")
    print(f"[CORP_ACTIONS] downgraded_to_ex_date_fallback={report.downgraded_count} "
          f"unhandled_action_types={report.unhandled_action_types} quarantined={len(report.quarantined)}")
    for q in report.quarantined:
        print(f"[CORP_ACTIONS] QUARANTINED {q}")

    conn.close()


def step_asm_gsm() -> None:
    from src.bitemporal.connection import get_connection, init_db
    from src.config.settings import get_settings
    from src.ingestion.nse_market_data.asm import fetch_and_ingest_asm_range
    from src.ingestion.nse_market_data.gsm import fetch_and_ingest_gsm_range

    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)
    to_date = date.today()
    from_date = to_date - timedelta(days=ASM_GSM_LOOKBACK_DAYS)
    print(f"[ASM/GSM] sweeping {from_date.isoformat()} .. {to_date.isoformat()} "
          f"({ASM_GSM_LOOKBACK_DAYS}-day lookback)")

    asm_report = fetch_and_ingest_asm_range(conn, from_date, to_date)
    print(f"[ASM] circulars_processed={asm_report.circulars_processed} "
          f"skipped_not_periodic={asm_report.circulars_skipped_not_periodic} "
          f"failed={len(asm_report.circulars_failed)} event_counts={asm_report.event_counts}")
    for f in asm_report.circulars_failed:
        print(f"[ASM] FAILED {f['circular']}: {f['reason']}")

    gsm_report = fetch_and_ingest_gsm_range(conn, from_date, to_date)
    print(f"[GSM] circulars_processed={gsm_report.circulars_processed} "
          f"skipped_not_transition={gsm_report.circulars_skipped_not_transition} "
          f"failed={len(gsm_report.circulars_failed)} event_counts={gsm_report.event_counts}")
    for f in gsm_report.circulars_failed:
        print(f"[GSM] FAILED {f['circular']}: {f['reason']}")

    conn.close()


def step_bhavcopy_today() -> None:
    """Requests TODAY's bhavcopy specifically -- `step_bhavcopy` above deliberately stops at
    yesterday (see `ingest_bhavcopy_full_history.main`'s own `end_date` default), so on a same-day
    evening run this is the step that actually closes today's gap. Retries if NSE has not published
    yet: `ingest_bhavcopy_date` classifies "not out yet" the same way it classifies a holiday
    fallback -- the archive keeps serving the PRIOR trading day's file until the real one exists
    (P2-003) -- so a request for today whose `actual_event_date` comes back EARLIER than today means
    "not published yet, or today is not a trading day," not a distinguishable error. This function
    cannot tell those two apart any more than the underlying fetch can (no invented holiday
    calendar) -- it retries either way and reports plainly if today's file still is not out after
    the full retry budget, leaving the ambiguity visible rather than guessing at it.

    Weekends are the one case this DOES resolve locally, cheaply, without a network call at all --
    skipped outright rather than spending the full retry budget on a request nothing will ever
    publish."""
    from src.bitemporal.connection import get_connection, init_db
    from src.config.settings import get_settings
    from src.ingestion.nse_market_data.bhavcopy import ingest_bhavcopy_date

    today = date.today()
    if today.weekday() >= 5:  # Sat=5, Sun=6
        print(f"[BHAVCOPY_TODAY] {today.isoformat()} is a weekend -- skipped, no request made.")
        return

    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)
    try:
        for attempt in range(1, BHAVCOPY_TODAY_MAX_ATTEMPTS + 1):
            outcome = ingest_bhavcopy_date(conn, today)
            if outcome.status == "ingested" and outcome.actual_event_date == today.isoformat():
                print(f"[BHAVCOPY_TODAY] {today.isoformat()} ingested on attempt {attempt}/"
                      f"{BHAVCOPY_TODAY_MAX_ATTEMPTS} ({outcome.rows_inserted} rows).")
                return
            if outcome.status == "ingested":
                detail = (f"archive still serving {outcome.actual_event_date} for a "
                           f"{today.isoformat()} request -- not published yet, or not a trading day")
            else:
                detail = outcome.reason
            print(f"[BHAVCOPY_TODAY] attempt {attempt}/{BHAVCOPY_TODAY_MAX_ATTEMPTS}: {detail}")
            if attempt < BHAVCOPY_TODAY_MAX_ATTEMPTS:
                time.sleep(BHAVCOPY_TODAY_RETRY_DELAY_SECONDS)

        total_minutes = BHAVCOPY_TODAY_MAX_ATTEMPTS * BHAVCOPY_TODAY_RETRY_DELAY_SECONDS // 60
        print(f"GAP {today.isoformat()}: still not published after {BHAVCOPY_TODAY_MAX_ATTEMPTS} "
              f"attempts over {total_minutes} minutes -- may be a holiday not reflected in the plain "
              f"weekday check, or NSE is later than usual today. Re-run this script, or wait for "
              f"tomorrow's run, which will pick it up via the normal through-yesterday catch-up step.")
    finally:
        conn.close()


STEPS = [
    ("bhavcopy", step_bhavcopy),
    ("announcements", step_announcements),
    ("isin_map", step_isin_map),
    ("corporate_actions", step_corporate_actions),
    ("asm_gsm", step_asm_gsm),
    ("bhavcopy_today", step_bhavcopy_today),
]


def _run_capturing(label: str, fn) -> dict:
    buf = io.StringIO()
    status, error_text = "OK", ""
    try:
        with contextlib.redirect_stdout(buf):
            fn()
    except Exception:
        status, error_text = "ERROR", traceback.format_exc()
    return {"label": label, "status": status, "output": buf.getvalue(), "error": error_text}


_GAP_LINE_RE = re.compile(r"^GAP \d{4}-\d{2}-\d{2}:")


def _extract_gaps_and_mismatches(output: str) -> tuple[list[str], list[str]]:
    """A real per-date bhavcopy GAP line looks like 'GAP 2026-09-16: <reason>' (see
    ingest_bhavcopy_full_history.py's own print format) -- 'reason' names the fallback-window
    mismatch shape verbatim when that's what happened (bhavcopy.py's DateIngestionOutcome.reason,
    P2-003's exact wording), so a case-insensitive substring check on top of the date-anchored
    regex is sufficient and does not duplicate the classification logic that already lives in
    src/.

    Anchored on a trailing date, NOT a bare 'GAP ' prefix (P8-005, docs/DEFECT_REGISTER.md): the
    same script also prints an unconditional SUMMARY line, 'GAP (confirmed trading day, this
    request failed): 0', on every run regardless of whether any gap occurred -- a bare prefix
    match flagged that summary line as a gap every single week, including weeks with zero real
    gaps, caught only by actually running this script end to end rather than by inspection."""
    gaps, mismatches = [], []
    for line in output.splitlines():
        stripped = line.strip()
        if _GAP_LINE_RE.match(stripped):
            gaps.append(stripped)
            if "fallback window" in stripped.lower():
                mismatches.append(stripped)
    return gaps, mismatches


def main() -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    started = datetime.now().isoformat(timespec="seconds")

    results = [_run_capturing(label, fn) for label, fn in STEPS]

    all_gaps: list[str] = []
    all_mismatches: list[str] = []
    for r in results:
        gaps, mismatches = _extract_gaps_and_mismatches(r["output"])
        all_gaps.extend(f"[{r['label']}] {g}" for g in gaps)
        all_mismatches.extend(f"[{r['label']}] {m}" for m in mismatches)

    overall_status = "OK" if all(r["status"] == "OK" for r in results) else "ERROR"
    step_summary = ", ".join(f"{r['label']}={r['status']}" for r in results)
    finished = datetime.now().isoformat(timespec="seconds")

    lines = [f"=== {started} weekly_ingest (finished {finished}) overall={overall_status} steps: {step_summary} ==="]
    lines.append(f"  GAPs: {len(all_gaps)}" + ("" if not all_gaps else " --"))
    lines.extend(f"    {g}" for g in all_gaps)
    if all_mismatches:
        lines.append(f"  P2-003-SHAPED DATE MISMATCHES: {len(all_mismatches)} --")
        lines.extend(f"    {m}" for m in all_mismatches)
    for r in results:
        if r["status"] == "ERROR":
            lines.append(f"  [{r['label']}] EXCEPTION:")
            lines.extend(f"    {ln}" for ln in r["error"].splitlines())

    block = "\n".join(lines) + "\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(block)

    print(block)
    return 0 if overall_status == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
