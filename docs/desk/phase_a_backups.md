# Phase A — local backup recovery proof

Verified 2026-09-30. Cloud is disabled by user instruction until they confirm a
working synced folder. No encryption. Configuration: `config/backup_stores.json`.

## First production archives

Local folder: `D:\PramanBackups` (outside the repository).

| Archive | Compressed bytes |
|---|---:|
| `desk_20260930T162854927700Z.zip` | 3,793 |
| `praman_20260930T162854927700Z.zip` | 329,916,828 |

Both archives were produced by `python scripts/backup_stores.py`, exit code 0.
Each contains an online SQLite backup from a read-only source, plus the manifest
computed from that snapshot. No live database file was copied.

Backups ran during the supervised foreground ingestion. The bhavcopy catch-up had
completed through 2026-09-29; the same-day step had not run yet. This is a recovery
snapshot of that point, not a claim that the September 30 ingestion was complete.

## Restored and checked

The backup command restored each archive before recording success. Then
`python desk/cli.py backup verify` independently restored both latest archives into
temporary folders and exited 0. Both returned `integrity_check: ok`, matching
whole-database SHA-256 values and the following row counts:

| Praman table | Rows |
|---|---:|
| bhavcopy | 4,240,059 |
| corporate_actions | 975 |
| corporate_announcements | 1,022,760 |
| sebi_orders | 71 |
| surveillance_flags | 31,884 |

Desk tables `decisions`, `journal_events`, `monitor_runs`, `opportunities`,
`paper_trade_events`, and `theses` each had zero rows. Each table's content hash
matched its backup-time manifest. Because the production journal is empty, the
tests also restore committed WAL rows from a populated journal and reject a
changed journal value even when row counts and the whole-file hash match.

## Retention and integration

- Daily Desk: retain 14 locally; 14 in cloud when enabled.
- Weekly Praman: retain 8 locally; 2 in cloud when enabled.
- No cloud directory was accessed or created by the backup command.
- Restore verification runs before retention removes old recognized archives.
- The existing ingestion entry point now ends with `backups`, after
  `bhavcopy_today`. No new scheduled task was created.
- `desk status` reports last backup and successful restore times for both stores.

## Tests

Ten backup tests passed. The full suite after the backup implementation reported:

```text
Ran 552 tests in 115.065s
OK
```

Tests include read-only source enforcement, committed WAL recovery, restore count
and content mismatch detection, failed-write atomicity, cadence, exact local/cloud
retention, disabled cloud behavior, and refusal of repository backup destinations.
