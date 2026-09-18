"""Real-data ASM/GSM ingestion. Reuses the cached SURV circular index built during Phase 4 source
evaluation (this session's scratchpad, 7,936 rows, zero re-fetch of the index itself) but makes
real network calls to download each individual circular's ZIP (ASM) or PDF (GSM) -- those were
never bulk-cached, only a handful of samples were. Writes to the same real DB as
scripts/ingest_bhavcopy_sample.py / scripts/ingest_corporate_actions_sample.py.

ASM: full range, 2019-10-01 (the project's hard floor) through the latest cached circular.
GSM: 2025-01-01 onward only -- see docs/phase4_asm_gsm_sourcing.md for the scope decision
(pre-2025 GSM circulars are scanned images with no extractable text; this project declines to OCR
them).
"""
from __future__ import annotations
import json
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
    fetch_circular_pdf_text, ingest_gsm_circular, is_gsm_subject,
)

SCRATCH_SEBI = Path(r"C:\Users\VICTUS\AppData\Local\Temp\claude\d--Agentic-ai-project\693aa27b-1dbb-463f-b783-329123a86aff\scratchpad\sebi")
GSM_FLOOR = "20250101"
DELAY_SECONDS = 0.3

def to_iso(yyyymmdd: str) -> str:
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"

def run_asm(conn, circulars: list[dict]) -> AsmIngestionReport:
    report = AsmIngestionReport()
    periodic = [c for c in circulars if is_periodic_asm_subject(c.get("sub") or "")]
    print(f"[ASM] {len(periodic)} periodic circulars to fetch (of {len(circulars)} total cached SURV circulars).")
    session = asm_session()
    for i, c in enumerate(periodic):
        subject = c.get("sub", "") or ""
        source_circular = "SURV" + str(c["circNumber"])
        knowledge_date = to_iso(c["cirDate"])
        if c.get("fileExt") != "zip":
            report.circulars_failed.append({"circular": source_circular, "reason": f"unexpected fileExt={c.get('fileExt')!r}, not a zip"})
            continue
        try:
            zip_bytes = fetch_circular_file(session, c["circFilelink"])
            ingest_asm_circular(conn, subject, source_circular, knowledge_date, zip_bytes, report)
        except StoreValidationError:
            raise
        except Exception as exc:
            report.circulars_failed.append({"circular": source_circular, "reason": str(exc)})
        if (i + 1) % 200 == 0:
            print(f"[ASM] ...{i + 1}/{len(periodic)} processed, {report.circulars_processed} ok, {len(report.circulars_failed)} failed so far")
        time.sleep(DELAY_SECONDS)
    return report

def run_gsm(conn, circulars: list[dict]) -> GsmIngestionReport:
    report = GsmIngestionReport()
    candidates = [c for c in circulars if c.get("cirDate", "") >= GSM_FLOOR and is_gsm_subject(c.get("sub") or "")]
    print(f"[GSM] {len(candidates)} GSM-subject circulars from {GSM_FLOOR} onward to classify.")
    session = gsm_session()
    for i, c in enumerate(candidates):
        subject = c.get("sub", "") or ""
        source_circular = "SURV" + str(c["circNumber"])
        classification = classify_gsm_subject(subject)
        if classification is None:
            report.circulars_skipped_not_transition += 1
            continue
        action_type, to_stage = classification
        try:
            pdf_text = fetch_circular_pdf_text(session, c["circFilelink"])
            ingest_gsm_circular(conn, action_type, to_stage, source_circular, pdf_text, report)
        except StoreValidationError:
            raise
        except Exception as exc:
            report.circulars_failed.append({"circular": source_circular, "reason": str(exc)})
        if (i + 1) % 50 == 0:
            print(f"[GSM] ...{i + 1}/{len(candidates)} processed")
        time.sleep(DELAY_SECONDS)
    return report

def main() -> None:
    circulars = json.loads((SCRATCH_SEBI / "all_surv_circulars_2019_2026.json").read_text(encoding="utf-8"))
    print(f"Loaded {len(circulars)} cached SURV circular index rows (zero network calls for the index itself).")

    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    asm_report = run_asm(conn, circulars)
    gsm_report = run_gsm(conn, circulars)

    print("\n=== ASM EVENT COUNTS ===")
    for key, count in sorted(asm_report.event_counts.items()):
        print(f"  {key}: {count}")
    print(f"  circulars_processed: {asm_report.circulars_processed}")
    print(f"  circulars_failed: {len(asm_report.circulars_failed)}")
    print(f"  unparsed_section_titles: {len(asm_report.unparsed_section_titles)}")
    print(f"  duplicate_events_skipped: {asm_report.duplicate_events_skipped}")

    print("\n=== GSM EVENT COUNTS ===")
    for key, count in sorted(gsm_report.event_counts.items()):
        print(f"  {key}: {count}")
    print(f"  circulars_processed: {gsm_report.circulars_processed}")
    print(f"  circulars_skipped_not_transition: {gsm_report.circulars_skipped_not_transition}")
    print(f"  circulars_failed: {len(gsm_report.circulars_failed)}")
    print(f"  duplicate_events_skipped: {gsm_report.duplicate_events_skipped}")

    print("\n=== ASM CIRCULAR FAILURES (first 30) ===")
    for f in asm_report.circulars_failed[:30]:
        print(f"  {f}")

    print("\n=== GSM CIRCULAR FAILURES (first 30) ===")
    for f in gsm_report.circulars_failed[:30]:
        print(f"  {f}")

    print("\n=== ASM UNPARSED SECTION TITLES (distinct, first 30) ===")
    seen_titles = {}
    for u in asm_report.unparsed_section_titles:
        seen_titles[u["title"]] = seen_titles.get(u["title"], 0) + 1
    for title, count in sorted(seen_titles.items(), key=lambda kv: -kv[1])[:30]:
        print(f"  ({count}x) {title}")

    row = conn.execute("SELECT MIN(event_date), MAX(event_date), COUNT(*) FROM surveillance_flags").fetchone()
    print(f"\n=== FINAL STORE STATE === min_event_date={row[0]} max_event_date={row[1]} total_rows={row[2]}")

    out_path = SCRATCH_SEBI / "asm_gsm_ingestion_report.json"
    out_path.write_text(json.dumps({
        "asm_event_counts": asm_report.event_counts,
        "asm_circulars_processed": asm_report.circulars_processed,
        "asm_circulars_failed": asm_report.circulars_failed,
        "asm_unparsed_titles_distinct": seen_titles,
        "asm_duplicate_events_skipped": asm_report.duplicate_events_skipped,
        "gsm_event_counts": gsm_report.event_counts,
        "gsm_circulars_processed": gsm_report.circulars_processed,
        "gsm_circulars_skipped_not_transition": gsm_report.circulars_skipped_not_transition,
        "gsm_circulars_failed": gsm_report.circulars_failed,
        "gsm_duplicate_events_skipped": gsm_report.duplicate_events_skipped,
        "store_min_event_date": row[0], "store_max_event_date": row[1], "store_total_rows": row[2],
    }, indent=2), encoding="utf-8")
    print(f"\nFull report written to {out_path}")

    conn.close()

if __name__ == "__main__":
    main()
