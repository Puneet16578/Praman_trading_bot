# Store inventory ? 2026-10-01

Backup archives were copied to a temporary directory before opening. SQLite copies were opened with mode=ro. Original backups remain untouched.

## Current Desk store

Exists: True. Created / modified (IST): 2026-10-01T12:32:14.024530+05:30 / 2026-10-01T22:01:14.379699+05:30

```json
{
  "circuit_bands": 3574,
  "decisions": 0,
  "journal_events": 0,
  "monitor_runs": 0,
  "opportunities": 0,
  "opportunity_executions": 545,
  "opportunity_log": 567,
  "paper_trade_events": 0,
  "sqlite_sequence": 3,
  "theses": 0
}
```

## desk_20260930T162854927700Z.zip

Created / modified (IST): 2026-09-30T21:58:54.944717+05:30 / 2026-09-30T21:58:54.944717+05:30

```json
{
  "decisions": 0,
  "journal_events": 0,
  "monitor_runs": 0,
  "opportunities": 0,
  "paper_trade_events": 0,
  "sqlite_sequence": 0,
  "theses": 0
}
```

## desk_20261001T012818106568Z.zip

Created / modified (IST): 2026-10-01T06:58:18.211465+05:30 / 2026-10-01T06:58:18.227466+05:30

```json
{
  "decisions": 0,
  "journal_events": 0,
  "monitor_runs": 0,
  "opportunities": 0,
  "paper_trade_events": 0,
  "sqlite_sequence": 0,
  "theses": 0
}
```

## praman_20260930T162854927700Z.zip

Created / modified (IST): 2026-09-30T21:59:38.137915+05:30 / 2026-09-30T22:00:16.142762+05:30

```json
{
  "bhavcopy": 4240059,
  "corporate_actions": 975,
  "corporate_announcements": 1022760,
  "sebi_orders": 71,
  "sqlite_sequence": 5,
  "surveillance_flags": 31884
}
```

Normal schema initialization completed; every table row count is unchanged. No database was cleared or replaced.

The scheduled ingestion writer (PID 617260) was stopped before this stable inventory to satisfy the foreground-only session requirement. The earlier inventory while it was running had 566 opportunities and 545 executions; use the stable counts above.
