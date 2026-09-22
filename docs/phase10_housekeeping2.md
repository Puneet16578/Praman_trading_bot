# Phase 10 — Housekeeping 2: the reproducibility gap `P8-004` exposed

## Summary (read this first)

`P8-004`'s fix prompted a direct question: did the ORIGINAL historical ASM/GSM ingestion have the
same fragility? It did, worse — a call that was never live at all. **Three scripts**
(`ingest_asm_gsm_sample.py`, `retry_asm_gsm_failures.py`, `ingest_corporate_actions_sample.py`)
hardcoded paths into a *past Claude session's own temp scratchpad*, so a fresh clone could not
rebuild `surveillance_flags`/`corporate_actions` at all, contradicting the README's "builds it from
scratch" claim. Logged as `P8-006` (Critical), fixed in all three by delegating to each domain's
live-network function instead (`fetch_and_ingest_{asm,gsm}_range`, `P8-004`-fixed; `fetch_all` for
corporate actions) — also removing a duplicated sweep implementation (CLAUDE.md invariant 1).
`git grep` for the literal temp-path prefix across `scripts/` now returns zero matches.
**Verified without re-downloading circulars:** a live fetch of the full 2019-10-01..2026-09-15
index returned 7,945 circulars in 0.8s — a strict superset of the old 7,936-row cache, 9 net new, 0
lost. The full historical re-ingestion and the corporate-actions sweep were deliberately NOT re-run
(redundant or genuinely multi-hour); stated precisely which pieces were and weren't live-verified.
**`weekly_ingest.py`'s exit code was already correct** — confirmed by this session's own real
evidence (pre-fix run: "failed with exit code 1"; post-fix run: "exit code 0") — no change needed.

---

## 1. The fix

Three scripts, one shape of bug, one shape of fix — delegate to the live-network function each
domain already has, in place of a scratchpad-cached JSON file:

| Script | Was reading from | Now calls |
|---|---|---|
| `scripts/ingest_asm_gsm_sample.py` | `SCRATCH_SEBI/all_surv_circulars_2019_2026.json` | `fetch_and_ingest_asm_range` / `fetch_and_ingest_gsm_range` directly |
| `scripts/retry_asm_gsm_failures.py` | same, plus a prior scratchpad report | `fetch_circular_index` live, `data/raw/asm_gsm_ingestion_report.json` for the prior report |
| `scripts/ingest_corporate_actions_sample.py` | `SCRATCH_CACHE/{actions_2019_2026,announcements}.json` | `fetch_all(year_from, year_to)` directly |

`ingest_asm_gsm_sample.py`'s own `run_asm`/`run_gsm` functions — a second, independent
implementation of the exact sweep logic already living in `fetch_and_ingest_{asm,gsm}_range` — were
deleted, not kept alongside the fix. `ingest_corporate_actions_sample.py`'s `rekey_announcements()`
bridging function was deleted too: `fetch_all()` already returns `announcements_by_key` in the
final key format `ingest_corporate_actions()` expects, so the bridge was solving a problem the live
path doesn't have.

All three scripts' report/log output that used to write back into the scratchpad now writes to
`data/raw/` (already gitignored, stable across sessions) instead.

**Confirmed by grep, not assumed from having fixed the three files known about going in:**

```
$ grep -rn "C:\\Users\\VICTUS\\AppData\\Local\\Temp" scripts/
(zero matches)
```

## 2. Verification, without re-downloading circulars

**Live fetch, full historical range, one call:**

```
fetch_circular_index(session, date(2019,10,1), date(2026,9,15))
-> 7,945 circulars in 0.8s
-> date range actually covered: 2019-10-01 .. 2026-09-15 (confirmed from the response's own dates)
```

**Compared directly against the old scratchpad cache** (still present on disk, used here only for
this one-time comparison, not as an ongoing dependency):

| | count |
|---|---|
| Old cache | 7,936 |
| Live fetch | 7,945 |
| In old but missing from live | **0** |
| In live but not in old (net new) | **9** |

**The live fetch is a strict superset — every circular the old cache ever had is still there.** Of
the 9 new: 6 have circular numbers clustered near the range's end (76342, 76344–76347, 76349) —
consistent with real circulars published after the old cache was captured, still falling inside the
same nominal 2019–2026 window. 3 (65532, 66093, 66480) do not fit that pattern — older-numbered,
not near the boundary. **Not investigated further; reported as an open, small, unexplained
discrepancy rather than assumed to be recency and left at that.**

## 3. What was NOT re-verified, and why — stated precisely

- **The full ASM/GSM historical ingestion (`ingest_asm_gsm_sample.py` end to end) was not re-run.**
  The store already holds this history from the original ingestion; a full re-run would mostly
  re-discover already-handled duplicates (`write_facts`'s duplicate-business-key skip, already
  covered by `test_reingesting_the_same_circular_is_idempotent`) at the cost of thousands of
  redundant real network calls. The function it now calls (`fetch_and_ingest_asm_range`/
  `..._gsm_range`) is independently already live-verified this session, via `weekly_ingest.py`'s
  successful second run.
- **The full corporate-actions sweep (`fetch_all`, 7 years + one announcement fetch per
  symbol/ex-date pair, potentially thousands of calls) was not run.** Only
  `fetch_corporate_actions_year` was spot-checked live (2026, 1,819 rows, correct bare-list shape —
  this endpoint does not have the SURV-circulars envelope problem `P8-004` found). The script's own
  docstring says so explicitly: DOCUMENTED, NOT VERIFIED at full historical scale.
- **`retry_asm_gsm_failures.py` was not run live** — there is currently no failure-list report to
  retry against, because nothing has failed. Syntax-checked and import-verified only.

All three scripts: `python -m py_compile` plus a real `importlib` load (not merely a parse check)
confirm each still defines and can execute `main()`.

## 4. `weekly_ingest.py`'s exit code — already correct, no change needed

Checked directly (`grep -n "sys.exit\|return 0\|return 1" scripts/weekly_ingest.py`) rather than
assumed: `main()` already returns `0 if overall_status == "OK" else 1`, and
`sys.exit(main())` already propagates it. This was not merely read from the code — this session
already has real, independent confirmation from the two live runs `docs/phase10_housekeeping.md`
reported: the pre-fix run's own background-task completion notice read *"failed with exit code
1"*; the post-fix run's read *"completed (exit code 0)"*. A Windows Scheduled Task's
`LastTaskResult` will show a non-zero result on a real failure without anyone opening the log.

## 5. Defect logged

**`P8-006`** (Critical), `docs/DEFECT_REGISTER.md` — full root cause, fix, and re-verification
detail there; summarized above.

---

Phase closed, per instruction.
