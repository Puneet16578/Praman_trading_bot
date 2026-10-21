# S1 development sensitivities wrapper - 21 October 2026

Implementation and synthetic validation only. No real sensitivity or check-only
invocation was run by the agent. This is not the full protocol results report.

`research_runs/s1_development_sensitivities.py` calls the frozen S1 evaluator only
for the eight registered variants, in the supplied order, at both horizons. It
has no primary or 2025 option. Frozen `desk/s1` and `scripts/s1_*` are unchanged
from b539e7e. Primary results and their provenance wrapper remain unchanged.

The input artifact SHA-256 is checked before parsing. Preflight also checks the
locked primary, frozen S1 code, rulebook/cost hashes, applicable manifest files,
cached development index payloads and dated ISIN snapshots, and bootstrap
settings. No download is performed. Source changes must be committed; previously
completed, untracked sensitivity JSONs and recognisable publication partials with
an existing attempt marker are the only permitted tree differences.
HEAD must match the local origin/master reference; the wrapper does not fetch.

The reader ends at 2024-12-31. Read-only SQLite handles expose only rows with
event and knowledge dates no later than that boundary and `recorded_at` strictly
before 2026-10-21 08:35:49 IST. Temporary views implement this recording cutoff;
the adapter routes the frozen helper's explicit main-table queries to those
views. A SQLite authorizer denies direct main-table bypasses and unreviewed
tables. Schema and timestamp validation selects recording metadata only. Each
source handle holds a read transaction. No persistent store is modified.

`--check-only` performs input/hash, destination and source-metadata checks, loads
the frozen development inputs, and exits with real readers sealed. It creates no
attempt marker or result and does not instantiate an outcome reader. Production
data compatibility and execution time remain unverified in this session; tests
used synthetic inputs/databases only.

## Commands

Run from your own PowerShell window after confirming the nightly and its retries
have finished, within the permitted time window. Fetch and align master first.

```powershell
Set-Location D:\Agentic_ai_project\praman
python -u -B .\research_runs\s1_development_sensitivities.py --check-only --variants cutoff_0900 cutoff_2359 lookback_1 lookback_10 peer_overlap_120 include_unstable omit_crowded_dates exit_slippage_040
```

Replace the placeholder with an IST date and time:

```powershell
python -u -B .\research_runs\s1_development_sensitivities.py --variants cutoff_0900 cutoff_2359 lookback_1 lookback_10 peer_overlap_120 include_unstable omit_crowded_dates exit_slippage_040 --no-start-after "YYYY-MM-DD HH:MM"
```

The deadline prevents a new variant from starting after that time. It does not
interrupt one already running. Set it early enough for the last variant to
finish and for results to be committed or stashed before 17:40. The primary took
approximately 3.5 hours; eight similarly sized variants suggest roughly 28 hours,
not a guarantee. Recording-cutoff overhead has not been measured on real data.
The all-eight command may therefore stop at the deadline with variants remaining.

## Outputs and interruption handling

- Completed files: `docs/desk/s1_development_results_20261021_sensitivity_<variant>.json`.
  Each records start/end UTC timestamps, hashes, cutoff, variant, bootstrap settings,
  results for both horizons, input counts, descriptive breakdowns and coverage audits.
  Saves are atomic and never overwrite an existing result.
- Initial marker: `data/s1/sensitivity_attempts/<variant>.attempt.json`.
  An OS lock prevents simultaneous execution of the same variant, including when
  an explicit rerun flag is supplied. Locks release on process death.
- On a caught failure, a corresponding `.attempt.failure.json` records the type
  and end time. The batch stops; later variants do not start. A hard kill may
  leave only a marker and/or `.partial` file. A partial file is not a result;
  a recognised partial with its attempt marker is preserved during explicit rerun.
- After a stop, check terminal output, completed JSONs and markers. Request only
  unfinished variants, preserving the registered order. Completed variants are
  refused, not silently recomputed or overwritten. All eight remain required
  regardless of the primary result.
- A marker without a completed result requires the explicit `--rerun-interrupted`
  flag. First establish that no instance is still running and review any failure.
  The original marker stays; a uniquely named rerun marker and output metadata
  record the rerun and original marker hash. There is no automatic retry.
- Run `--check-only` on the remaining list first, adding `--rerun-interrupted`
  there too when an interrupted attempt is intentionally being retried.

The attempt/lock/failure files are under ignored `data/s1`. Completed JSONs under
`docs/desk` and the wrapper under `research_runs` do not match the nightly's current
dirty-input guard. That does not waive the clean-tree or no-work time rules.
Do not remove markers or rename results to bypass refusal checks.

## Validation

Synthetic tests cover strict recording time (including timezone equivalence and
microseconds), date ceilings, forbidden direct reads, metadata-only setup, the
frozen reader against synthetic databases, all eight variants through the frozen
evaluator, hash/code failure checks, check-only isolation, ordered execution,
start deadlines, atomic no-overwrite saves, OS locking and explicit interrupted
reruns. Full-suite evidence is recorded in the implementation commit message.
