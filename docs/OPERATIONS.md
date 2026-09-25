# Operations — store snapshots

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
