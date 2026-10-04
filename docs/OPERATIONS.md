# Operations

## Announcement ingestion lapse, ~2026-09-19 to 2026-10-04 (P8-021) — operational deviation, not a pre-registration amendment

**What lapsed.** Amendment 2 §5 of the frozen pre-registration
(`docs/phase10_preregistration_amendment2.md`) requires corporate announcements to be ingested on a
regular weekly schedule through the evaluation window's close (2027-01-15), not as a single
backfill. From about 2026-09-19 — the day after the full-history backfill of 2026-09-18/19 — until
the P8-021 fix (code `8954d4c`, freshness and annotation follow-up 2026-10-04), the nightly
`announcements` step only backfilled symbols with no stored announcement at all, so new
announcements for the ~2,280 already-covered symbols were not ingested. Measured read-only:
2026-08 had 20,897 rows across 2,296 symbols; 2026-09 had 8,847 across 2,065; 2026-10 had 18
across 4. The weekly commitment was therefore not met for roughly the first two and a half weeks of
the forward window, which began 2026-09-16.

**Why the data is recoverable before the June 2027 evaluation.** Each announcement's
`knowledge_date` is its own publication date (`sort_date`), not the fetch date, and re-fetched rows
are skipped by `UNIQUE (symbol, seq_id, knowledge_date)`. A late fetch therefore restores
point-in-time-correct rows. The repair is the nightly `announcements_recent` step
(`scripts/ingest_announcements_recent.py`): a bounded, overlapping refresh of every active equity
with stored rows, first run at the next scheduled ingestion (2026-10-05 18:00 IST, reaching back to
about 2026-09-10), then every night. **Before the June 2027 evaluation, confirm the recovery**:
per-symbol announcement counts from 2026-09-16 onward back in their normal range, and
`data/processed/announcements_refresh_state.json` recording a COMPLETE refresh.

**Why this is not an amendment.** No reference query, scoring rule, success criterion, window or
threshold changes. This records an ingestion failure and its repair, which is exactly what §5's
schedule exists to surface early. The refresh now runs nightly, a strict superset of the weekly
requirement (as with the 2026-09-28 note below).

**Desk effect.** Since the fix the Desk treats the disclosure dimension as UNKNOWN unless the
announcement source is known complete through the day before the decision
(`desk/source_freshness.py`; the assessment becomes INSUFFICIENT, never ELIGIBLE). Desk records
made during the lapse are annotated INCOMPLETE_DISCLOSURE_EVIDENCE, append-only and not
invalidated (`desk/annotations.py`; filter via `opportunity_log_annotated` / `decisions_annotated`).

## Daily ingestion (2026-09-28) — operational change, not a pre-registration amendment

**Ingestion now runs every trading weekday evening instead of weekly.** The pre-registration
(`docs/phase10_preregistration_amendment2.md` §5, "Ingestion schedule — pre-specified") requires
bhavcopy/announcements/ASM-GSM collection "on a regular weekly schedule ... not as a single backfill
attempt" through the evaluation window's close, specifically so an ingestion failure surfaces within
days rather than being discovered four months late. Daily is a strict superset of weekly — it
satisfies that requirement automatically — and changes no reference query, no scoring rule, no
evaluation criterion the pre-registration fixed. Recorded here as the operational note that
provision itself calls for, not as a pre-registration amendment.

**Why now:** the Praman Expert Desk (`docs/desk/DESIGN.md`) needs same-evening data. On a weekly
cadence, `desk assess`'s G1 gate fails most evenings (no bhavcopy row yet for "today"), and a pending
paper-trade entry or an open position's stop can go unchecked for up to a week.

**What changed, mechanically:** `scripts/weekly_ingest.py` (filename and `logs/weekly_ingest.log`
kept as-is — see that script's own module docstring for why a rename would break more than it fixes)
gained a sixth, final step, `bhavcopy_today`. The five original steps are unchanged, including
`step_bhavcopy`, which deliberately still only requests THROUGH YESTERDAY (correct for the old
Monday-morning cadence, one day behind for a same-day run). `bhavcopy_today` requests TODAY
specifically and retries — up to 6 attempts, 15 minutes apart (90 minutes total) — if NSE has not
published yet, which is a normal possibility right after market close, not an error. If still not
out after the full retry budget, it logs a plain `GAP <today>: ...` line (picked up by the existing
GAP-reporting logic) rather than guessing or fabricating a row. Weekends are skipped locally with no
network call at all.

**Scheduled task — exact PowerShell**, replacing the (per `docs/phase10_housekeeping.md`, never
actually registered) weekly Monday-6AM task:

```powershell
# Remove the old weekly task first, if it was ever actually registered
if (Get-ScheduledTask -TaskName "PramanWeeklyIngest" -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName "PramanWeeklyIngest" -Confirm:$false
}

$Action = New-ScheduledTaskAction `
    -Execute "C:\Users\VICTUS\AppData\Local\Programs\Python\Python313\pythonw.exe" `
    -Argument "scripts\weekly_ingest.py" `
    -WorkingDirectory "D:\Agentic_ai_project\praman"

$Trigger = New-ScheduledTaskTrigger -Weekly `
    -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
    -At 6:00PM

$Settings = New-ScheduledTaskSettingsSet `
    -WakeToRun `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 3) `
    -DontStopOnIdleEnd

Register-ScheduledTask `
    -TaskName "PramanDailyIngest" `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Daily weekday-evening bhavcopy/announcements/ASM-GSM ingestion, incl. same-day bhavcopy with retry, for the Praman Expert Desk" `
    -RunLevel Limited
```

**Confirm registration:**

```powershell
Get-ScheduledTask -TaskName "PramanDailyIngest" | Get-ScheduledTaskInfo
```

`-ExecutionTimeLimit` raised from 2 to 3 hours (the old weekly task's own setting) to comfortably
cover the new step's up-to-90-minute retry budget on top of the other five steps' typical runtime.
`6:00PM` (local machine time) and the 6-attempt/15-minute retry budget are PROPOSED, not measured
against NSE's actual publish-time distribution — real evening-run timestamps, once they exist, are
the right basis to retune either number, not a guess made now.

**Existing task verified 2026-09-30:** `PramanDailyIngest` has `WakeToRun=True`,
`StartWhenAvailable=True`, and `LogonType=Interactive` (no stored password).
No task was created or changed in this check. Interactive logon requires the user
to be logged in; waking the computer does not log the user in.

On 30 September, after that inspection, the user approved changing only the existing
task's executable to `pythonw.exe`. The change was applied and re-read: wake-to-run
and missed-start recovery remain True, logon remains Interactive, and the task is
Ready. The action keeps `scripts\weekly_ingest.py` and its working directory. This
avoids a console window that can be closed accidentally; no password was supplied.
Manual ingestion still uses `python scripts/weekly_ingest.py` in the foreground.

### Durable ingestion progress (Phase A Step 0)

`weekly_ingest.py` appends and flushes a `started` line before any ingestion step,
then a timestamped status after each step, and finally the existing summary.
The run's start timestamp links all these entries. `desk status` reports
`started <time>, never finished` if a start has no matching finish, including when
a later run completed. This means no finish is recorded; the run may still be active.
Logs from before this change cannot reveal interrupted runs that wrote no start.

On Windows the script holds `SetThreadExecutionState(ES_CONTINUOUS |
ES_SYSTEM_REQUIRED)` during work and restores the thread's previous state in
`finally`, including on interruption. Other platforms skip the Windows API.
Failure to acquire the request is reported and leaves an unfinished start;
the script does not silently promise sleep protection. This prevents idle sleep,
not shutdown, manual sleep, or a scheduler time limit.

### Recovery backups (Phase A Step 1)

Configuration: `config/backup_stores.json`. Local destination: `D:\PramanBackups`.
Cloud is **disabled** until the user confirms a working synced folder; no access
to the configured OneDrive destination occurs while disabled. No encryption.

- Desk: one backup per IST calendar day, retain 14 locally (14 in cloud when enabled).
- Praman: one backup per ISO calendar week, retain 8 locally (2 in cloud when enabled).
- The ingestion entry point calls backups after the same-day bhavcopy step, including
  when an earlier ingestion step failed, so an ingestion failure does not prevent
  protecting the journal. The foreground run started before this code change needs
  a separate backup command after it finishes.
- `python scripts/backup_stores.py` creates due backups. Both this tool and the
  milestone snapshot tool use `shared/sqlite_backup.py`: SQLite online backup from
  a read-only source. Neither copies live database files. Copying an already-built
  compressed archive to the optional cloud destination is safe.
- Archives are timestamped ZIP files containing the SQLite snapshot and a JSON
  manifest. The manifest records all user-table row counts, a whole-database SHA-256,
  and a deterministic content SHA-256 for every Desk journal table. Values are read
  from the completed snapshot, so concurrent ingestion cannot skew the baseline.
- Archives publish by a same-directory atomic rename. A temporary restore verifies
  integrity, row counts, journal hashes, and the database hash before any retention
  removal. Re-running within the same period verifies the existing latest archive.
- `desk backup verify` restores the latest archive for each store and enabled
  destination into temporary folders and repeats all checks. It never restores over
  a live store. `desk status` shows last backup and last successful restore times
  from the append-only operational log `logs/backups.jsonl`.

Retention only removes recognized archives directly inside the configured backup
folder. Other files and incomplete archives are not treated as recovery points.

## The design point: two different dates answer two different questions

**`knowledge_date` records when a fact became PUBLIC** — the bitemporal guard's own filter
(`src/bitemporal/guard.py`), what every signal, label, and report is computed as-of. It is a
property of the WORLD: a corporate action's `knowledge_date` is when NSE/the announcement made it
knowable, regardless of which database or which day this project happened to ingest it.

**`recorded_at` records when THIS DATABASE stored the row** — a store-owned column
(`src/bitemporal/store.py`'s `_normalized_values`, stamped `datetime.now(timezone.utc)` at write
time, never writer-supplied). It is a property of THIS INGESTION HISTORY, not of the world: two
different databases, or the same database re-ingested twice, can have the identical
`knowledge_date` for a fact at two completely different `recorded_at` times.

**Consequence for reproducibility:** the as-of guard (and therefore every signal/label/report)
depends only on `knowledge_date` — a promoted, corrected, or newly-ingested row with an OLD
`knowledge_date` is visible to old code exactly as if it had always been there, because the guard
was never told when the row physically arrived in this database. `recorded_at` is the only column
that answers "was this row here yet," and it exists precisely so a question like this one is
answerable at all, not left as "probably, based on when the commit says the code changed."

## Verified before writing this document (not assumed)

- **`recorded_at` is present in all 5 fact tables** (`bhavcopy`, `corporate_actions`,
  `surveillance_flags`, `corporate_announcements`, `sebi_orders` — `src/bitemporal/schema.py`'s
  full `BITEMPORAL_TABLES` registry), `NOT NULL`, and store-owned (excluded from the columns a
  writer must supply — `FactTable.required_columns`).
- **It holds genuine ingestion times, not a copy of `knowledge_date`/`event_date`**: stamped by
  `_now()` inside `_normalized_values`, the single function every write path (`write_fact`/
  `write_facts`) runs through. Cross-checked against git history directly: `bhavcopy`'s earliest
  `recorded_at` (2026-09-08T01:46 UTC) precedes this repo's first commit (2026-09-08 07:38 +0530)
  by minutes, and `corporate_actions`'s earliest `recorded_at` (2026-09-13T04:13 UTC) lands three
  minutes before the commit that introduces corporate-actions ingestion (`7b3952d`, 2026-09-13
  09:46 +0530) — the timestamps track this project's own real ingestion history, not a later bulk
  reload.
- **No fact table has been dropped/rebuilt, and no fact row has ever been updated or deleted, after
  `1c3f655`.** `git log -S"DROP TABLE" --all` finds exactly one commit, `6a89fdb` — the P4-004
  incident, which predates `1c3f655` (Phase 4, long before Phase 8). `git log -S"DELETE FROM"
  --all` and equivalent searches for an `UPDATE ... SQL` statement find none, ever, in this
  repository's history. Every "correction" since (P8-008's promotion, P8-010's ISIN resolution)
  is append-only by construction: `write_fact` rejects a duplicate `(business key, knowledge_date)`
  rather than overwriting it, and `scripts/phase10_amendment4_promote_corporate_actions.py`'s own
  docstring states "no row is deleted or updated" — confirmed directly against the real data, not
  merely trusted from the docstring: `HEG`'s pre-`1c3f655` rows (`recorded_at` 2026-09-13, tier
  `MATCHED_UNCONFIRMED`/`DEMERGER_EXCLUSION`) are untouched; the promotion added a NEW, later-dated
  row (`recorded_at` 2026-09-23, tier `EX_DATE_FALLBACK`, a different `knowledge_date`) alongside
  it, and the post-rename `HEGAM` demerger row is a separate business key entirely (a different
  symbol string), not a rewrite of the `HEG` one.

**Both conditions hold. `data/processed/praman.db` filtered to `recorded_at <=` a commit's own
timestamp is therefore a faithful reconstruction of what that commit's code actually saw** — see
`docs/RESULTS.md`'s reproducibility note for the resulting re-run and its outcome.

## Snapshot rule

**At each milestone** (a pre-registration amendment, a promotion to production, a defect fix that
changes stored data) **and mandatorily immediately before and after the binding forward
evaluation**, snapshot the store to `data/snapshots/<UTC-timestamp>_<label>.sqlite` (gitignored)
using `scripts/snapshot_store.py <label>`.

**Uses SQLite's online backup API from a `mode=ro` source connection, not a raw file copy.** This
store runs in WAL mode (`src/bitemporal/connection.py`); a plain filesystem copy of the `.db` file
alone can miss content still sitting in the `-wal` file that a normal reader would see, silently
producing an incomplete snapshot. `Connection.backup()` copies the database's true logical content
through SQLite itself, correct regardless of journal mode — and the source connection is opened
read-only so the snapshot tool can never itself write to the live store.

Each snapshot's SHA-256 and the git `HEAD` at snapshot time are recorded below. **The evaluation
report, when it is written, must cite the snapshot hash it ran against** — a result with no
recorded snapshot hash does not have a reproducible data state, only a reproducible code state.

## Durable Desk store incident — 2026-10-01 (P8-025)

The prior proof cleared the production Desk store, contrary to append-only policy.
Both `D:\PramanBackups` Desk archives were inspected through read-only temporary
copies and have zero journal rows. Backups remain untouched. The current store's
rows were preserved and normal additive schema initialization changed no counts.
See `docs/desk/store_inventory_round2.md` for every table and file timestamp.
Never clear, replace or recreate either durable store. Proofs use temporary copies.
The scheduled ingestion run was stopped during this review to comply with the
foreground-only requirement; task settings were not changed. It has no completion
summary, so status must report that interruption rather than claim a completed run.

## Snapshots

| Taken (UTC) | Label | File | SHA-256 | Git HEAD |
|---|---|---|---|---|
| 2026-09-25T03:27:52 | `amendment5_frozen` | `data/snapshots/2026-09-25T032745_amendment5_frozen.sqlite` | `069cd86f515883bf274fe42efa904ad3bd912c00b2842f9a181a41aaa3129a79` | `cbb9dda75c8fd1b99428b9e79a60a6c55325e336` |

## Demo store (separate from the snapshot table above -- structurally cutoff-truncated, not a
## point-in-time backup of the full store)

`demo/build_demo_store.py` produces `data/demo/praman_demo.sqlite` (gitignored): a backup-API copy
of production, then every row with `event_date` OR `knowledge_date` after `2026-09-15` deleted from
every fact table, `VACUUM`ed. This is what the Streamlit demo (`demo/`) opens, read-only, and it
never opens production. Re-run whenever you want a fresher demo; the file is fully reproducible
from production + the fixed cutoff, so it is not itself treated as a durable snapshot.

| Built (UTC) | File | SHA-256 | Cutoff | Built from git HEAD |
|---|---|---|---|---|
| 2026-09-25 | `data/demo/praman_demo.sqlite` | `d8bf91bd92ebea2c439e0623b21722c29cfa3e07a92bd13cb4a5431558cce3df` | `2026-09-15` | `4e35329` |

## Pre-existing backup, kept

`data/processed/praman_pre_p8007_promotion_backup_20260923T174335.db` — taken by
`scripts/phase10_amendment4_promote_corporate_actions.py` immediately before that script's own
write, per its docstring ("backed up first"). **Represents the production store's `corporate_actions`
state immediately before the P8-007/P8-008/P8-010 corrections promotion** (702 rows, pre-ISIN-
resolution, pre-full-sweep) — a RAW FILE COPY, not a backup-API snapshot (predates this document's
rule), but adequate for its purpose since it was taken with no concurrent writer running. Kept, not
deleted; not moved into `data/snapshots/` so its original name and the promotion script's own
docstring reference to it stay accurate.

- **SHA-256:** `550a00ea30f5a9722b33f69990b015c3c678b658eba1d9b02142fb804343d9d1`
- **Size:** 1,435,029,504 bytes

## ISIN refresh resilience — operational note, 2026-09-28

This is an operational change, not a pre-registration amendment. A 404 for today's
CM/UDiFF snapshot now produces WARN and retains the existing map and companion
unchanged. Other failures remain ERROR; a 404 with no existing map is ERROR too.
The existing snapshot merge and identity-resolution calculations are unchanged.
No pinned research code or frozen pre-registration document was modified.

`weekly_ingest.py` reports OK / WARN / ERROR, in descending severity ERROR > WARN >
OK. WARN is a completed run with degraded freshness (exit 0); ERROR exits 1.
Warnings are retained in the summary log and shown by `desk status`.

Every successful map build writes `data/raw/nse_symbol_isin_current.meta.json`:
`built_at` with its timezone offset, `map_sha256`, and `snapshot_dates` actually
used. Desk validates the checksum before using its build time. The existing map's
one-time companion uses its file timestamp, `2026-09-23T17:35:56.578734+05:30`,
explicitly labelled `build_time_source=file_mtime`. Its historical snapshot dates
were not recorded: `snapshot_dates=[]`, `snapshot_dates_source=not_recorded`.
The existing map's bytes were unchanged; SHA-256:
`e97da4b5b5450d06c496ba42be1e3db8a5ef85b9a4e02f659a6b0b92a19bcda1`.

Desk age is the count of distinct bhavcopy event dates after the build date in IST,
through the assessment/status date, visible by that knowledge date. G1 fails above
5 trading days and when new-assessment metadata is missing or invalid. Every new
decision records `isin_map_built_at`; replay passes that recorded value directly,
never re-reading the current map or companion. NULL is reserved for legacy
decisions that predate this check; their old G1 behavior remains intact. Replay's
existing exact-code-commit check still applies.

`migrate_decisions_isin_map()` explicitly counts rows, runs `ALTER TABLE decisions
ADD COLUMN isin_map_built_at TEXT` when needed, and checks the unchanged count
inside a savepoint. Real desk migration: **0 rows before, 0 after**. Existing rows
are never backfilled with a guessed build timestamp. The migration also runs
idempotently when opening a Desk database. Tests cover a populated legacy table.

## ISIN history retention repair - 2026-10-03

P8-034: a recent build timestamp did not establish complete identity coverage.
Refresh now retains the existing map as fallback when historical downloads fail,
and merges dated historical observations before today's observations. Recovery
from NSE snapshots restored 32 missing identities and corrected 51 current ISIN
conflicts. All 70,638 catalogue events resolve to non-fund ISINs. The dated audit
and hashes are in docs/desk/isin_recovery_round2.json. Original map and companion
were preserved in scratch/isin_before_recovery*.json; durable stores and backups
were not changed by this repair.

## Test-only timezone dependency (verification)

There are no pytz imports or references in desk/ or src/. Production Desk time
uses shared.market_time. pytz 2026.4 is installed in the test environment alongside
empyrical-reloaded 0.5.12 for the drawdown cross-check; it is not a Desk clock
dependency. No new production timezone dependency was introduced.
