"""Retry pass for circulars that failed in a prior `ingest_asm_gsm_sample.py` run. Re-fetches ONLY
the circulars named in that run's failure list (looked up back against the cached SURV circular
index for subject/knowledge_date/download link -- the failure list itself only records circular
number + reason, not the full record).

The original working theory -- bursty failures meant NSE-side rate limiting -- turned out to be
wrong for 442 of the 490 recorded failures: grouping by normalized cause before writing this
script found 439 ASM failures sharing one real parser gap (abbreviated month names, P4-006), plus
one ESM-typo classification bug (P4-007) and one PDF-rendering-artifact bug (P4-008, 2 GSM
circulars) -- all now fixed in `asm.py`/`gsm.py`. Because the CODE changed since the original
failures were recorded, this script does NOT gate on "was the original reason transient" the way
an unmodified-code retry normally should -- every previously-failed circular gets one fresh
attempt against the fixed parser. `is_transient()` is still used, but only *within* an attempt
loop: if a fresh attempt fails with a reason that still doesn't look transient, retrying the exact
same bytes again with backoff is pointless, so that circular's attempts stop early rather than
burning through MAX_ATTEMPTS uselessly. ASM circulars are also re-checked against
`is_periodic_asm_subject` before any attempt -- P4-007's ESM-typo fix means a circular that
previously failed (wrongly attempted) may now be correctly out of scope and should not be
retried at all.

Idempotency (confirmed by `tests/test_asm_gsm_ingestion.py::IngestAsmCircularTest::test_reingesting_the_same_circular_is_idempotent`
and by `write_facts`'s duplicate-business-key skip) is what makes this safe even though it's
possible (though not expected, given the original run's own accounting) for a "failed" circular to
have partially reached the store already: a repeat write is inserted-and-skipped, not
double-counted.
"""
from __future__ import annotations
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.bitemporal.store import StoreValidationError
from src.config.settings import get_settings
from src.ingestion.nse_market_data.asm import (
    AsmIngestionReport, session_with_cookie as asm_session, fetch_circular_file,
    ingest_asm_circular, is_periodic_asm_subject,
)
from src.ingestion.nse_market_data.gsm import (
    GsmIngestionReport, session_with_cookie as gsm_session, classify_gsm_subject,
    fetch_circular_pdf_text, ingest_gsm_circular,
)

SCRATCH_SEBI = Path(r"C:\Users\VICTUS\AppData\Local\Temp\claude\d--Agentic-ai-project\693aa27b-1dbb-463f-b783-329123a86aff\scratchpad\sebi")
BASE_DELAY = 2.5
MAX_DELAY = 30.0
MAX_ATTEMPTS = 5

TRANSIENT_RE = re.compile(
    r"\b(429|403|5\d\d)\b|timed?\s*out|timeout|connection (aborted|reset|refused)|"
    r"remote end closed connection|max retries exceeded|read timed out", re.I)

def to_iso(yyyymmdd: str) -> str:
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"

def is_transient(reason: str) -> bool:
    return bool(TRANSIENT_RE.search(reason or ""))

def retry_asm(conn, failed_circulars: list[dict], index_by_number: dict[str, dict]) -> tuple[AsmIngestionReport, list[dict]]:
    report = AsmIngestionReport()
    session = asm_session()
    still_failed = []
    skipped_now_out_of_scope = 0
    for f in failed_circulars:
        num = f["circular"].replace("SURV", "")
        c = index_by_number.get(num)
        if c is None:
            still_failed.append({**f, "reason": f["reason"] + " [also: circular number not found in cached index]"})
            continue
        subject = c.get("sub", "") or ""
        if not is_periodic_asm_subject(subject):
            # P4-007: the ESM-typo exclusion fix means a circular that was WRONGLY attempted
            # before (and failed) may now be correctly recognized as out of scope -- not a
            # failure, and must not be retried into the store under the old, buggy classification.
            skipped_now_out_of_scope += 1
            continue
        knowledge_date = to_iso(c["cirDate"])
        last_reason = f["reason"]
        succeeded = False
        for attempt in range(MAX_ATTEMPTS):
            try:
                zip_bytes = fetch_circular_file(session, c["circFilelink"])
                ingest_asm_circular(conn, subject, f["circular"], knowledge_date, zip_bytes, report)
                succeeded = True
                break
            except StoreValidationError:
                raise
            except Exception as exc:
                last_reason = str(exc)
                if not is_transient(last_reason):
                    # fetch succeeded (or failed differently) and the NEW failure is a real
                    # parse/format problem -- retrying identical bytes again will not help.
                    print(f"  [ASM retry] {f['circular']} attempt {attempt + 1} produced a non-transient error, stopping early: {last_reason}")
                    break
                delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
                print(f"  [ASM retry] {f['circular']} attempt {attempt + 1}/{MAX_ATTEMPTS} failed: {last_reason} -- sleeping {delay:.1f}s")
                time.sleep(delay)
        if not succeeded:
            still_failed.append({"circular": f["circular"], "reason": last_reason})
        time.sleep(BASE_DELAY)
    print(f"  [ASM retry] {skipped_now_out_of_scope} of {len(failed_circulars)} now correctly recognized as out-of-scope (ESM etc.), not retried")
    return report, still_failed

def retry_gsm(conn, failed_circulars: list[dict], index_by_number: dict[str, dict]) -> tuple[GsmIngestionReport, list[dict]]:
    report = GsmIngestionReport()
    session = gsm_session()
    still_failed = []
    for f in failed_circulars:
        num = f["circular"].replace("SURV", "")
        c = index_by_number.get(num)
        if c is None:
            still_failed.append({**f, "reason": f["reason"] + " [also: circular number not found in cached index]"})
            continue
        subject = c.get("sub", "") or ""
        classification = classify_gsm_subject(subject)
        if classification is None:
            continue  # was never a real GSM ingestion candidate; shouldn't be in this list, but skip safely
        action_type, to_stage = classification
        last_reason = f["reason"]
        succeeded = False
        for attempt in range(MAX_ATTEMPTS):
            try:
                pdf_text = fetch_circular_pdf_text(session, c["circFilelink"])
                ok = ingest_gsm_circular(conn, action_type, to_stage, f["circular"], pdf_text, report)
                if not ok:
                    last_reason = "date fields not found in PDF (not a fetch failure -- see parse_gsm_pdf_text reason)"
                    print(f"  [GSM retry] {f['circular']} attempt {attempt + 1} fetched fine but failed to parse, stopping early: {last_reason}")
                    break
                succeeded = True
                break
            except StoreValidationError:
                raise
            except Exception as exc:
                last_reason = str(exc)
                if not is_transient(last_reason):
                    print(f"  [GSM retry] {f['circular']} attempt {attempt + 1} produced a non-transient error, stopping early: {last_reason}")
                    break
                delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
                print(f"  [GSM retry] {f['circular']} attempt {attempt + 1}/{MAX_ATTEMPTS} failed: {last_reason} -- sleeping {delay:.1f}s")
                time.sleep(delay)
        if not succeeded:
            still_failed.append({"circular": f["circular"], "reason": last_reason})
        time.sleep(BASE_DELAY)
    return report, still_failed

def main() -> None:
    prior_report = json.loads((SCRATCH_SEBI / "asm_gsm_ingestion_report.json").read_text(encoding="utf-8"))
    circulars = json.loads((SCRATCH_SEBI / "all_surv_circulars_2019_2026.json").read_text(encoding="utf-8"))
    index_by_number = {c["circNumber"]: c for c in circulars}

    asm_failed_in = prior_report["asm_circulars_failed"]
    gsm_failed_in = prior_report["gsm_circulars_failed"]
    print(f"Retrying {len(asm_failed_in)} ASM + {len(gsm_failed_in)} GSM circulars from the prior run's failure list.")
    print(f"base_delay={BASE_DELAY}s max_delay={MAX_DELAY}s max_attempts={MAX_ATTEMPTS}")

    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    asm_report, asm_still_failed = retry_asm(conn, asm_failed_in, index_by_number)
    gsm_report, gsm_still_failed = retry_gsm(conn, gsm_failed_in, index_by_number)

    print("\n=== RETRY RESULT ===")
    print(f"ASM: {len(asm_failed_in)} retried -> {len(asm_still_failed)} still failing "
          f"({len(asm_failed_in) - len(asm_still_failed)} recovered)")
    print(f"GSM: {len(gsm_failed_in)} retried -> {len(gsm_still_failed)} still failing "
          f"({len(gsm_failed_in) - len(gsm_still_failed)} recovered)")

    print("\n=== ASM STILL-FAILING (after retry, non-transient candidates) ===")
    for f in asm_still_failed:
        print(f"  {f}")
    print("\n=== GSM STILL-FAILING (after retry, non-transient candidates) ===")
    for f in gsm_still_failed:
        print(f"  {f}")

    row = conn.execute("SELECT MIN(event_date), MAX(event_date), COUNT(*) FROM surveillance_flags").fetchone()
    print(f"\n=== STORE STATE AFTER RETRY === min_event_date={row[0]} max_event_date={row[1]} total_rows={row[2]}")

    merged_report = dict(prior_report)
    for key, count in asm_report.event_counts.items():
        merged_report["asm_event_counts"][key] = merged_report["asm_event_counts"].get(key, 0) + count
    for key, count in gsm_report.event_counts.items():
        merged_report["gsm_event_counts"][key] = merged_report["gsm_event_counts"].get(key, 0) + count
    merged_report["asm_circulars_processed"] += asm_report.circulars_processed
    merged_report["gsm_circulars_processed"] += gsm_report.circulars_processed
    merged_report["asm_circulars_failed"] = asm_still_failed
    merged_report["gsm_circulars_failed"] = gsm_still_failed
    merged_report["asm_duplicate_events_skipped"] = merged_report.get("asm_duplicate_events_skipped", 0) + asm_report.duplicate_events_skipped
    merged_report["gsm_duplicate_events_skipped"] = merged_report.get("gsm_duplicate_events_skipped", 0) + gsm_report.duplicate_events_skipped
    merged_report["store_min_event_date"], merged_report["store_max_event_date"], merged_report["store_total_rows"] = row

    out_path = SCRATCH_SEBI / "asm_gsm_ingestion_report_after_retry.json"
    out_path.write_text(json.dumps(merged_report, indent=2), encoding="utf-8")
    print(f"\nMerged post-retry report written to {out_path}")

    conn.close()

if __name__ == "__main__":
    main()
