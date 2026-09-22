# Phase 10 — Housekeeping

Four items, none touching the pre-registration or its amendments: a README accuracy correction, a
weekly ingestion entry point (which surfaced two real defects when actually run), a full-history
data-hygiene check, and the current commit log.

## Summary (read this first)

**README correction (`b56909d`):** the architecture paragraph claimed "an optional multi-agent LLM
layer... writes narrative" — stale as of `P8-003`, which confirmed by direct grep that zero
LLM-provider-calling code exists anywhere in `src/`. Corrected to state the agent layer runs fully
deterministically end to end, with two other now-stale `P8-003` references fixed alongside it for
the same reason. **Weekly ingestion (`516d4c2`):** `scripts/weekly_ingest.py` runs bhavcopy →
announcements → ASM/GSM in order and logs a dated GAP/error summary. Actually running it live, not
just reading it, found two real bugs no prior review or the 326-test suite had caught: the real
NSE circulars API returns an envelope `fetch_circular_index` never unwrapped (`P8-004`, crashed on
first live call), and the new script's own GAP detector flagged a summary line as a gap on every
run (`P8-005`). Both fixed and re-verified live twice — pre-fix run reproduced both bugs exactly,
post-fix run completed clean (`overall=OK, GAPs: 0`). Full suite: 328/328 pass. **Data hygiene:**
zero files matching risky extensions in the full commit history, checked two independent ways;
current pack size 923.73 KiB. **Still open:** the repository is not pushed to a private remote and
no commit hash is recorded with a third party — unchanged from the prior session, still requires a
remote URL or the user's own action.

---

## 1. README correction

`README.md`'s "Architecture, in one paragraph" section described "an optional multi-agent LLM
layer (`src/agent/`) [that] writes narrative around the same deterministic rule." This was stale:
`P8-003`'s investigation (`docs/DEFECT_REGISTER.md`) had already confirmed, by direct grep across
all of `src/`, that **zero LLM-provider-calling code exists anywhere in this codebase** — every
`EvidenceClaim.text` a specialist agent produces is a deterministic Python template
(`src/agent/specialists.py`), and `synthesis.py` never calls a provider at all.

Corrected (commit `b56909d`) to state plainly that the agent layer (Supervisor, the three
specialist agents, the Adversary, the authorization gate) runs fully deterministically, and that
any future LLM-narrative capability is restricted by standing `CLAUDE.md` policy to local/dev use
only, never reaching shareable output. Two other README passages that described `P8-003` as "open"
/ "enforced imperfectly" were corrected in the same commit — the first description a reader sees
must match the code, not just the one paragraph that was directly quoted.

## 2. Weekly ingestion — script, real bugs found, scheduled task

**`scripts/weekly_ingest.py`** is one entry point: bhavcopy → corporate announcements → ASM/GSM
circulars, in that order, then a dated summary block appended to `logs/weekly_ingest.log`
(gitignored). Every step is idempotent by construction — bhavcopy and announcements skip whatever
is already confirmed/fetched; ASM/GSM sweeps a deliberately overlapping 10-day trailing window,
safe because `write_facts`'s own duplicate detection (`P4-009`) skips already-stored events rather
than erroring.

It deliberately does **not** reuse `scripts/ingest_asm_gsm_sample.py`, which hardcodes a path into
a *previous Claude session's own temp scratchpad directory* as its circular-index source — not
something a scheduled task can depend on existing. Instead it calls
`fetch_and_ingest_{asm,gsm}_range` directly, which fetch the circular index live over the network.

**Actually running it end to end (not just reading the code) found two real defects:**

- **`P8-004` (High):** `fetch_circular_index` (both `asm.py` and `gsm.py`) returned the raw NSE
  circulars API response, typed `-> list[dict]`. The real, live response is an envelope —
  `{"data": [...], "fromDate": ..., "toDate": ...}` — not a bare list. Iterating it yielded the
  envelope's own three string keys instead of circular dicts, crashing on the very first live call
  (`AttributeError: 'str' object has no attribute 'get'`). Neither function had ever been
  exercised against real or realistically-shaped data before — both docstrings already admitted
  "Not called by the fixture-based test suite." Fixed to return `r.json()["data"]`; two regression
  tests added, mocking the real observed envelope shape.
- **`P8-005` (Medium):** the new script's own `_extract_gaps_and_mismatches` matched any line
  starting `"GAP "` — but bhavcopy also prints an unconditional summary line
  (`"GAP (confirmed trading day, this request failed): 0"`) every run, gap or not. The bare-prefix
  match flagged that summary line as a real gap on every single run, including clean weeks — a
  false positive that would have trained a human to stop reading the log. Fixed by anchoring the
  match on a trailing date (`^GAP \d{4}-\d{2}-\d{2}:`).

**Re-verified live, twice, not merely re-read:** a run before the fixes reproduced both bugs
exactly (`asm_gsm=ERROR`, a false `GAPs: 1`); a second run after both fixes completed
`overall=OK, GAPs: 0`. Full suite re-run: **328/328 pass** (326 + the 2 new regression tests). Both
logged in `docs/DEFECT_REGISTER.md` with root cause and this same re-verification evidence.

**Scheduled task — exact PowerShell commands given and unchanged since:**

```powershell
$Action = New-ScheduledTaskAction `
    -Execute "C:\Users\VICTUS\AppData\Local\Programs\Python\Python313\python.exe" `
    -Argument "scripts\weekly_ingest.py" `
    -WorkingDirectory "D:\Agentic_ai_project\praman"

$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 6:00AM

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -DontStopOnIdleEnd

Register-ScheduledTask `
    -TaskName "PramanWeeklyIngest" `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Weekly bhavcopy/announcements/ASM-GSM ingestion for the Phase 10 forward evaluation window" `
    -RunLevel Limited
```

`-StartWhenAvailable` is the exact setting for "run as soon as possible after a scheduled start is
missed." Verify registration with `Get-ScheduledTask -TaskName "PramanWeeklyIngest" | Get-ScheduledTaskInfo`.
**Not yet actually registered as a scheduled task** — these are the commands to run, not
confirmation they were run; registering a persistent Windows scheduled task is an action for the
user to take (or explicitly ask for) rather than one taken silently here.

## 3. Full-history file check, with pack size

Re-run fresh for this document, not reused from the prior session's numbers, since two more
commits landed since then. Two independent methods, both clean:

```
git rev-list --objects --all | grep -iE "\.(db|sqlite|sqlite3|csv|parquet|zip|xlsx|pdf)($|[^a-z])"
  -> 0 matches

git log --all --pretty=format: --name-only | <extension tally>
  -> 128 .py, 46 .md, 2 .gitignore, 1 .txt -- nothing else, ever, across full history
```

**`git count-objects -vH`: 923.73 KiB, 279 objects, 0 packs** (all loose — this repository has
never been pushed or run through `git gc`). Up from 850.21 KiB at the prior check, consistent with
the housekeeping commits themselves (docs, the new `weekly_ingest.py`, test additions) — not new
data. No stop condition triggered; history was not rewritten.

## 4. Current commit log

```
516d4c2 Automate weekly ingestion; fix two real bugs found by actually running it
b56909d Fix README: the agent layer is fully deterministic, no LLM is called anywhere
babbf09 Phase 10 pre-registration, Amendment 2: noise margin, pinned pipeline, missing-data rule
a01eda4 Resolve P8-003: correct stale report text, resolve lint gap architecturally
d98c1db Phase 10 pre-registration, Amendment 1: scoring function, top-decile LIFT, fixed window
cc982a4 Phase 9: adversarial lint pass, README, data/legal hygiene, register consistency
8658509 Pre-register the Phase 10 redesign spec, before any forward evaluation data exists
3a3d280 Correct three framing errors in the P8-001 robustness narrative
1c3f655 Phase 8: evaluation, baselines, and a robustness review that retracts the headline (P8-001)
7b3de51 Phase 7: disclosure/SEBI ingestion, event classification, and the multi-agent evidence layer
```

**Still open, unchanged from the prior session:** this repository is not pushed to any remote, and
no commit hash has been recorded with a third party. Neither can be done from this environment
without either a remote URL to push to or the user doing it directly — flagged here again rather
than left to be inferred from silence.
