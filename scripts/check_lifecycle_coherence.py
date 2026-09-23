"""Lifecycle-coherence check for surveillance_flags, covering both ASM and GSM tracks.

This script did not previously exist in the committed repo -- docs/phase4_asm_gsm_sourcing.md
describes running "the categorized coherence check" repeatedly during Phase 4 (it is what caught
P4-010 through P4-013), but, like the SURV circular index cache P8-006 fixed, it lived only in an
ad hoc scratchpad script and was never committed. Written here for the first time as a real,
reusable script implementing the same categories that doc's own published table uses, so "re-run
the coherence check" is something a future session (or a scheduled task) can actually do.

Phase 4's own published baseline (docs/phase4_asm_gsm_sourcing.md) is ASM-ONLY: "4,271 real
(symbol, mechanism) tracks and 31,445 ASM events." This script checks GSM tracks too, using the
identical category logic, since nothing about the coherence question (does ENTRY/EXIT/STAGE_CHANGE
alternate sensibly for a given symbol+mechanism track) is ASM-specific.

Categories, matching the Phase 4 table exactly -- ASM ONLY (see the GSM note below for why):
  - malformed_symbol: a stored symbol starting with a footnote/marker character -- must be zero.
  - exit_no_entry: an EXIT with no preceding ENTRY on the same track. Split near-floor (<=45 days
    from 2019-10-01, expected: left-censoring, this project's own data starts then) vs not-near-floor
    (residual).
  - stage_change_no_entry: a STAGE_CHANGE with no preceding ENTRY. Same near/not-near-floor split.
  - double_entry: two ENTRYs with no EXIT between them on the same track.
  - stage_mismatch: a STAGE_CHANGE or EXIT whose from_stage does not match the track's
    currently-open to_stage.

GSM does not share ASM's ENTRY/STAGE_CHANGE/EXIT lifecycle model, confirmed directly by reading
`classify_gsm_subject` (src/ingestion/nse_market_data/gsm.py) and by inspecting a real track
(ORTEL, 10 real ENTRY rows to stages I/II/III/II/III/I/I/III over 2025-02 to 2026-08, zero
STAGE_CHANGE or EXIT rows, zero from_stage values -- every real GSM stage MOVE, including moving
between two stages the symbol was already in a GSM relationship for, is classified as a fresh
ENTRY to the destination stage; GSM has no STAGE_CHANGE action type at all, only ENTRY and EXIT).
Applying the ASM-shaped double_entry/stage_mismatch categories to GSM produces a large, MEANINGLESS
number (a first draft of this script found "115 double_entry" for GSM and this was corrected
before being reported anywhere as a finding, not after) -- it would flag GSM's own normal,
expected behavior as a defect. GSM therefore only gets the two checks that remain meaningful under
its real model: malformed_symbol and exit_no_entry (you cannot exit a GSM relationship you were
never recorded as entering).
"""
from __future__ import annotations
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings

FLOOR = date(2019, 10, 1)
NEAR_FLOOR_DAYS = 45


def _days_from_floor(iso_date: str) -> int:
    y, m, d = (int(x) for x in iso_date.split("-"))
    return (date(y, m, d) - FLOOR).days


def check_mechanism(rows: list[dict], mechanism_label: str, model: str) -> dict:
    """model="asm_lifecycle": full ENTRY/STAGE_CHANGE/EXIT state machine (Phase 4's categories).
    model="gsm_entries": GSM's real model -- ENTRY can repeat freely (each is a real move to a
    different stage; GSM has no STAGE_CHANGE action at all), only EXIT-without-a-prior-open-ENTRY
    and malformed symbols are meaningful checks."""
    tracks: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in rows:
        tracks[(r["symbol"], r["mechanism"])].append(r)

    malformed_symbol = 0
    exit_no_entry_near = exit_no_entry_far = 0
    stage_change_no_entry_near = stage_change_no_entry_far = 0
    double_entry = 0
    stage_mismatch = 0
    residual_detail: list[str] = []

    for (symbol, mechanism), events in tracks.items():
        if symbol[:1] in ("*", "#", "^"):
            malformed_symbol += 1
        events_sorted = sorted(events, key=lambda r: (r["event_date"], r["recorded_at"]))

        is_open = False
        open_stage: str | None = None
        for e in events_sorted:
            action = e["action_type"]
            near_floor = _days_from_floor(e["event_date"]) <= NEAR_FLOOR_DAYS
            if action == "ENTRY":
                if model == "asm_lifecycle" and is_open:
                    double_entry += 1
                    residual_detail.append(f"double_entry {mechanism_label}:{symbol} at {e['event_date']} ({e['source_circular']})")
                is_open, open_stage = True, e["to_stage"]
            elif action == "EXIT":
                if not is_open:
                    if near_floor:
                        exit_no_entry_near += 1
                    else:
                        exit_no_entry_far += 1
                        residual_detail.append(f"exit_no_entry {mechanism_label}:{symbol} at {e['event_date']} ({e['source_circular']})")
                elif model == "asm_lifecycle" and e.get("from_stage") not in (None, open_stage):
                    stage_mismatch += 1
                    residual_detail.append(f"stage_mismatch(exit) {mechanism_label}:{symbol} at {e['event_date']} ({e['source_circular']})")
                is_open, open_stage = False, None
            elif action == "STAGE_CHANGE":
                if model != "asm_lifecycle":
                    continue  # not a real category under this mechanism's model
                if not is_open:
                    if near_floor:
                        stage_change_no_entry_near += 1
                    else:
                        stage_change_no_entry_far += 1
                        residual_detail.append(f"stage_change_no_entry {mechanism_label}:{symbol} at {e['event_date']} ({e['source_circular']})")
                elif e.get("from_stage") not in (None, open_stage):
                    stage_mismatch += 1
                    residual_detail.append(f"stage_mismatch(stage_change) {mechanism_label}:{symbol} at {e['event_date']} ({e['source_circular']})")
                is_open, open_stage = True, e["to_stage"]

    return {
        "n_tracks": len(tracks), "n_events": len(rows), "malformed_symbol": malformed_symbol,
        "exit_no_entry_near_floor": exit_no_entry_near, "exit_no_entry_not_near_floor": exit_no_entry_far,
        "stage_change_no_entry_near_floor": stage_change_no_entry_near,
        "stage_change_no_entry_not_near_floor": stage_change_no_entry_far,
        "double_entry": double_entry, "stage_mismatch": stage_mismatch,
        "residual_detail": residual_detail,
    }


def main() -> None:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    all_rows = [dict(r) for r in conn.execute(
        "SELECT symbol, mechanism, action_type, from_stage, to_stage, event_date, source_circular, recorded_at "
        "FROM surveillance_flags"
    ).fetchall()]
    conn.close()

    asm_rows = [r for r in all_rows if r["mechanism"] in ("ASM_LT", "ASM_ST")]
    gsm_rows = [r for r in all_rows if r["mechanism"] == "GSM"]
    print(f"Total surveillance_flags rows: {len(all_rows)} (ASM: {len(asm_rows)}, GSM: {len(gsm_rows)})")

    for label, rows, model in (("ASM (LT+ST combined)", asm_rows, "asm_lifecycle"), ("GSM", gsm_rows, "gsm_entries")):
        result = check_mechanism(rows, label, model)
        print(f"\n=== {label} (model={model}) ===")
        print(f"  tracks: {result['n_tracks']}  events: {result['n_events']}")
        print(f"  malformed_symbol: {result['malformed_symbol']} (must be 0)")
        print(f"  exit_no_entry, near floor (<=45d, expected): {result['exit_no_entry_near_floor']}")
        print(f"  exit_no_entry, NOT near floor (residual): {result['exit_no_entry_not_near_floor']}")
        if model == "asm_lifecycle":
            print(f"  stage_change_no_entry, near floor (expected): {result['stage_change_no_entry_near_floor']}")
            print(f"  stage_change_no_entry, NOT near floor (residual): {result['stage_change_no_entry_not_near_floor']}")
            print(f"  double_entry (residual): {result['double_entry']}")
            print(f"  stage_mismatch (residual): {result['stage_mismatch']}")
        else:
            print(f"  (double_entry/stage_change/stage_mismatch not meaningful under GSM's real model -- see module docstring)")
        if result["residual_detail"]:
            print(f"  -- residual detail ({len(result['residual_detail'])}) --")
            for d in result["residual_detail"][:50]:
                print(f"    {d}")


if __name__ == "__main__":
    main()
