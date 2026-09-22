"""Real-data ASM/GSM full-historical ingestion.

P8-006 (docs/DEFECT_REGISTER.md): this script used to load its SURV circular index from a cached
JSON file inside a PAST Claude session's own temp scratchpad directory -- ephemeral, deletable by
Windows at any time, and unavailable to a fresh clone entirely. It also duplicated
`fetch_and_ingest_asm_range`/`fetch_and_ingest_gsm_range`'s own sweep logic in a second,
independent `run_asm`/`run_gsm` implementation (CLAUDE.md invariant 1: "never create a parallel
implementation of an existing class/function"). Both problems are fixed the same way: this script
now calls those two shared, already-tested functions directly, which fetch the circular index live
over the network (confirmed against the real API: 7,945 circulars for the full 2019-10-01 ..
2026-09-15 range, in under a second, a strict superset of the old 7,936-row cache -- see
docs/phase10_housekeeping2.md for the full comparison).

ASM: full range, 2019-10-01 (the project's hard floor) through today.
GSM: 2025-01-01 onward only -- see docs/phase4_asm_gsm_sourcing.md for the scope decision
(pre-2025 GSM circulars are scanned images with no extractable text; this project declines to OCR
them).
"""
from __future__ import annotations
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings
from src.ingestion.nse_market_data.asm import fetch_and_ingest_asm_range
from src.ingestion.nse_market_data.gsm import fetch_and_ingest_gsm_range

ASM_START = date(2019, 10, 1)
GSM_START = date(2025, 1, 1)

REPORT_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "asm_gsm_ingestion_report.json"


def main() -> None:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    today = date.today()
    print(f"[ASM] sweeping {ASM_START.isoformat()} .. {today.isoformat()} (live network fetch, no cache)")
    asm_report = fetch_and_ingest_asm_range(conn, ASM_START, today)

    print(f"[GSM] sweeping {GSM_START.isoformat()} .. {today.isoformat()} (live network fetch, no cache)")
    gsm_report = fetch_and_ingest_gsm_range(conn, GSM_START, today)

    print("\n=== ASM EVENT COUNTS ===")
    for key, count in sorted(asm_report.event_counts.items()):
        print(f"  {key}: {count}")
    print(f"  circulars_processed: {asm_report.circulars_processed}")
    print(f"  circulars_skipped_not_periodic: {asm_report.circulars_skipped_not_periodic}")
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

    seen_titles: dict[str, int] = {}
    for u in asm_report.unparsed_section_titles:
        seen_titles[u["title"]] = seen_titles.get(u["title"], 0) + 1
    print("\n=== ASM UNPARSED SECTION TITLES (distinct, first 30) ===")
    for title, count in sorted(seen_titles.items(), key=lambda kv: -kv[1])[:30]:
        print(f"  ({count}x) {title}")

    row = conn.execute("SELECT MIN(event_date), MAX(event_date), COUNT(*) FROM surveillance_flags").fetchone()
    print(f"\n=== FINAL STORE STATE === min_event_date={row[0]} max_event_date={row[1]} total_rows={row[2]}")

    # Written under data/raw/ (gitignored, stable across sessions) -- NOT a past session's temp
    # scratchpad (P8-006). This is run OUTPUT, not raw source data, but data/raw/ is this
    # project's existing convention for "real artifacts too dynamic/large for git."
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps({
        "asm_event_counts": asm_report.event_counts,
        "asm_circulars_processed": asm_report.circulars_processed,
        "asm_circulars_skipped_not_periodic": asm_report.circulars_skipped_not_periodic,
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
    print(f"\nFull report written to {REPORT_PATH}")

    conn.close()


if __name__ == "__main__":
    main()
