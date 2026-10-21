# Disk and nightly backup scope: 21 October 2026

Read-only filesystem/source/log audit. No backup created, restored, deleted or
reconfigured. No archive was opened and no backup file was changed.

`shutil.disk_usage` measurements during the pre-market audit:

| Drive | Free bytes | Free GiB | Total bytes |
|---|---:|---:|---:|
| C: | 42,005,540,864 | 39.12 | 238,519,578,624 |
| D: | 256,043,954,176 | 238.46 | 271,526,653,952 |

Free space is a point-in-time measurement and can change as tests/logs run.

The nightly calls `desk.backups.run_backups` with its default sources:

```python
SOURCES = {"desk": ROOT / "data/desk/desk.sqlite",
           "praman": ROOT / "data/processed/praman.db",
           "logs": logs_dir()}
KINDS = ("desk", "praman", "logs")
DAILY = {"desk", "logs"}  # praman is weekly
```

It does **not** recursively copy `data/`, and **does not back up `data/s1`**.
No exclusion is needed or proposed for the current nightly configuration.
Local destination: `D:/PramanBackups`; retention 14 Desk/log archives and
8 Praman archives. Cloud destination is configured but disabled.

`data/s1` contains two files, not just the completed 570 MB artifact:

| File | Bytes |
|---|---:|
| inputs_20261020_v1.json | 560,353,364 |
| inputs_complete_20261020_v1.json | 569,704,185 |
| Total | 1,130,057,549 |

The original freeze is intentionally preserved. Neither was removed or changed.
Because these ignored research artifacts are outside this backup policy, their
recovery is not guaranteed by the nightly backups. A separate archival policy
would require a separate task; this audit does not change it.

The 20 October backup log records restore checks as OK for Desk, Praman and logs;
the log archive contains 114 files / 2,645,434 uncompressed bytes. The nightly
backup step completed at 23:58:44.672585 IST. These are existing log statements,
not a fresh restore verification. Archive contents were not independently checked.
