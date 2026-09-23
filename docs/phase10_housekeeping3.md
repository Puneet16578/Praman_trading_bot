# Phase 10 — Housekeeping 3

Three items, closing this phase per instruction.

## Summary (read this first)

**Item 1:** classified all 9 new circulars, no downloads — **only one was a genuine miss**
(`SURV66480`, GSM Stage II ENTRY, `ORTEL`, 2025-02-04, TRAIN period), ingested via the normal
idempotent path. The other 8 were correctly out-of-scope (CLAUDE.md's excluded mechanisms) or
already ingested by the first weekly run. Wrote `scripts/check_lifecycle_coherence.py` (never
existed in the repo) and caught my own mistake before reporting it: a first pass misapplied ASM's
`ENTRY/STAGE_CHANGE/EXIT` model to GSM, manufacturing a false "115 `double_entry`" — GSM has no
`STAGE_CHANGE` at all, confirmed from a real track. ASM's residual drifted slightly from Phase 4's
baseline (4,271→4,288 tracks), entirely explained by the already-reported weekly run, not today's
one GSM row. ASM status is not a pre-registered input — the frozen model is untouched. **Item 2:**
corporate actions added to the weekly schedule (`fetch_recent`, sharing `fetch_all`'s tier logic).
The pre-specified split/bonus scan, run as a mechanism check, found something much bigger than
expected: **this project has never captured ETF unit splits**, ever — 96 shape-matches, zero
explained, one traced fully (`HDFCNIFETF`, a confirmed real 10:1 split). Logged as `P8-007`, found
and scoped, not fixed. Live run (re-run after a session-boundary interruption killed the first
attempt) completed clean: `overall=OK`, `GAPs: 0`. **Item 3:** "builds it from scratch" corrected to
"designed to, individually verified, never run end-to-end," with an overnight-rebuild-and-diff
recorded as a real, optional future check.

---

## 1. Do any of the 9 new circulars matter?

Classified via `is_periodic_asm_subject`/`is_gsm_subject`/`classify_gsm_subject` directly on the
`sub` field — no downloads:

| Circular | Date | Classification | Verdict |
|---|---|---|---|
| 65532 | 2024-12-11 | "...Encumbrance..." (SEBI SAST Reg. 28(3)) | Correctly out of scope — one of CLAUDE.md's 4 deliberately-excluded mechanisms |
| 66093 | 2025-01-13 | "Applicability of Enhanced Surveillance Measure (ESM)" | Correctly out of scope — excluded mechanism |
| **66480** | **2025-02-04** | **GSM ENTRY, Stage II** | **Genuine miss — ingested this session** |
| 76342 | 2026-09-15 | GSM ENTRY, Stage II | Real, **already ingested** by the first weekly run (confirmed: 1 row in store) |
| 76344 | 2026-09-15 | "Trade for Trade" | Correctly out of scope — denylist category |
| 76345 | 2026-09-15 | ESM | Correctly out of scope — excluded mechanism |
| 76346 | 2026-09-15 | ASM (LT) | Real, **already ingested** (confirmed: 3 rows in store) |
| 76347 | 2026-09-15 | ASM (ST) | Real, **already ingested** (confirmed: 31 rows in store) |
| 76349 | 2026-09-15 | "...ASM...under IBC" | Correctly out of scope — excluded mechanism (IBC) |

**A real, transient inconsistency noted honestly, not smoothed over:** the first attempt at this
classification (a combined script importing both the ASM and GSM classifiers) found only 6 of 9
target circulars in that call's response; two immediately-following, isolated re-fetches of the
identical range each found all 9, consistently. Not investigated further (outside this task's
scope), but recorded — the live NSE circulars endpoint is not perfectly stable call-to-call, at
least occasionally.

**66480 ingested** via `fetch_and_ingest_gsm_range(conn, date(2025,2,1), date(2025,2,7))` — the
normal idempotent path, not a one-off manual insert. Confirmed in the store:
`ORTEL | GSM | ENTRY | to_stage=II | event_date=2025-02-05 | knowledge_date=2025-02-04 |
source_circular=SURV66480`.

**`check_lifecycle_coherence.py` re-run** (written fresh — this script did not previously exist in
the repo; Phase 4's own coherence check lived only in an ad hoc scratchpad script, the same pattern
`P8-006` already found and fixed for the circular-index cache):

| | Phase 4 published baseline | Now |
|---|---|---|
| ASM tracks | 4,271 | 4,288 |
| ASM `exit_no_entry` (not near floor) | 56 | 58 |
| ASM `stage_change_no_entry` (not near floor) | 17 | 17 |
| ASM `double_entry` | 36 | 38 |
| ASM `stage_mismatch` | 12 | 12 |

**The drift is real but not caused by today's addition.** Every number that moved, moved because of
the already-reported first weekly run's own genuine new ASM circulars (`SURV76346`/`76347`, both
dated 2026-09-15, ingested before this task started) — ASM and GSM are structurally separate tracks,
and today's one new row is GSM only. Zero ASM rows were touched this session.

**A real mistake caught before being reported as a finding, not after:** this script's first draft
applied ASM's `ENTRY`/`STAGE_CHANGE`/`EXIT` state machine to GSM too and produced "115
`double_entry`" for GSM. Checked directly rather than trusted: GSM has no `STAGE_CHANGE` action at
all — a real track (`ORTEL`, the very row just ingested) shows 10 `ENTRY` rows to stages
I/II/III/II/III/I/I/III across 2025-02 to 2026-08, zero `STAGE_CHANGE`, zero `EXIT`, `from_stage`
always `NULL`. Every GSM stage move, including moving between two stages a symbol was already in a
GSM relationship for, is a fresh `ENTRY` to the destination — confirmed directly from
`classify_gsm_subject`'s own logic, not assumed. The script was corrected (GSM now only checks
`malformed_symbol` and `exit_no_entry`, the two categories that remain meaningful under its real
model) before this number was written into any document. GSM's own `exit_no_entry` count (35) is
itself expected, not a residual requiring investigation: GSM data starts 2025-01-01 by explicit,
already-documented scope decision (pre-2025 circulars are scanned images), so any symbol that
entered GSM before that floor and exits after it will show exactly this shape — an unbounded
left-censoring window, structurally different from ASM's tight 45-day one, because GSM's floor is a
scope decision with no visibility before it, not a data-availability line with data starting
immediately after.

**ASM status is not a pre-registered input** (`docs/phase10_preregistration.md` §Features and
directions lists `delivery_pct_percentile_60d`, `volume_ratio`, `same_date_event_count`,
`disclosure_tier` — no ASM/GSM feature) — **the frozen scoring function and thresholds are untouched
by anything in this section**, stated explicitly per instruction.

## 2. Amendment 3 — forward corporate actions

Full detail: `docs/phase10_preregistration_amendment3.md`. Summary: corporate actions added to the
weekly schedule via a new `fetch_recent()` function sharing `fetch_all()`'s tier/quarantine/
demerger-marker logic (only the fetch window narrows, not how ingestion itself works); the
pre-specified split/bonus shape scan (`scripts/phase10_scan_split_bonus_shapes.py`) is fully defined
and was run as a mechanism check against historical data (prices, not outcomes — not an interim
look), surfacing `P8-007`: **this project has never captured ETF unit splits**, confirmed directly
for `HDFCNIFETF` (a real 10:1 split, 2021-02-16→17, absent from `corporate_actions` entirely) out of
96 total shape-matches, none explained by an existing action record. Found and scoped, not fixed —
a real, separate ingestion gap this pass does not attempt to close.

**The weekly schedule change, run live once, as instructed.** First attempt was killed by an
unrelated session boundary before completing (no log entry was written — `main()` only appends
after every step finishes, success or failure, so an absent entry means the run genuinely did not
finish, not that it succeeded silently). Re-run cleanly on 2026-09-23, real output, persisted in
`logs/weekly_ingest.log` (gitignored) and pasted here verbatim:

```
=== 2026-09-23T11:38:56 weekly_ingest (finished 2026-09-23T12:02:21) overall=OK
steps: bhavcopy=OK, announcements=OK, corporate_actions=OK, asm_gsm=OK ===
  GAPs: 0
```

The new `corporate_actions` step ran cleanly alongside the three already-verified ones, `overall=OK`,
zero gaps — the four-step schedule works end to end for real, not only as individually-tested
pieces.

## 3. README precision

`README.md`'s Setup section claimed "running the ingestion scripts under `scripts/` builds it from
scratch" with no qualification. Corrected: the scripts are DESIGNED for a fresh-clone rebuild, and
`P8-006` fixed the three that structurally could not have done one; every constituent live-network
function has been individually verified against the real API this session (§1 above,
`docs/phase10_housekeeping.md`/`housekeeping2.md`); **a full, unattended, end-to-end rebuild from an
empty database has never actually been run.** Recorded, per instruction, as a real, optional future
check rather than done now: an overnight rebuild into a separate database, diffed row-for-row
against the current store, would turn this from a designed claim into a verified one.

---

## Defects logged this session

`P8-007` (Critical, found not fixed) — ETF unit splits uncaptured. Full detail:
`docs/DEFECT_REGISTER.md`.

Phase closed, per instruction.
