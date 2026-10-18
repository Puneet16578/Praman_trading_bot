# T1 hold-out runner preparation (18 October 2026)

Pre-registration lines 99-101:
> Development volatility quintiles: pooled eligible development stock-days with
> valid ATR percentage, including rows with missing outcomes. NumPy linear 20/40/60/80
> percentiles; freeze for 2025 and bootstrap draws. Ties go to the upper quintile.

Lines 144-145 fix development baseline candidate shares for both periods and all draws.
No pre-registration amendment or feature/threshold/setting change is made.

Changes, all for P8-089:
- `read_guard.py`: explicit 2025 scope; unchanged default 2024 ceiling, restored on exit.
- `provenance.py`: explicit end for file selection and logical SQL hashes, before reads.
- `reader.py`: authorised 2025 decision/window bounds; existing firewall calls unchanged.
- `development.py`: select the evaluated period, require fixed weights for hold-out,
  preserve development defaults, render hold-out disclosures and registered verdict terms.
- `rehearsal.py`: select the period and accept frozen weights, retaining defaults and seed.
- `holdout.py`: verify locked artifacts, load fixed constants, compare the development
  rehearsal, check the 2025 purge and render the rehearsal tables.
- `scripts/t1_holdout.py`: separate rehearsal/evaluation paths, source/input hash checks,
  clean-master gate, pre-outcome manifest, exclusive-create attempt marker and outputs.
- Focused fixture tests cover future-read refusal, SQL/file bounds, weight reuse,
  reader/firewall protection, sealing, rendering, locked-artifact integrity and no retry.
- Defect register and handoff document the limitation and authorised repair.

The development random-label comparison excludes only execution metadata (commit,
source hashes, seconds, peak memory), exactly as the third rehearsal comparison did.
Every saved analytical field must match. Timing and memory are reported separately.

Locked weights and the exact hold-out weights (read, never recomputed):

| Quintile | Locked development | Hold-out | Identical |
|---|---:|---:|---|
| 1 | 0.2 | 0.2 | True |
| 2 | 0.2 | 0.2 | True |
| 3 | 0.2 | 0.2 | True |
| 4 | 0.2 | 0.2 | True |
| 5 | 0.2 | 0.2 | True |

Frozen boundaries: `[3.1605964603389842, 3.9592760180995112, 4.76384909369999, 5.857440286897999]`.

## Development artifact hashes before and after the code change

All four match exactly. Further checks run after each rehearsal and the evaluation.

| Artifact | SHA-256 before | SHA-256 after |
|---|---|---|
| `docs/desk/t1_development_results_20261018.md` | `f8b65100574d19f16026b04722dc5c6c05df84e7a35577e89255c51262439483` | `f8b65100574d19f16026b04722dc5c6c05df84e7a35577e89255c51262439483` |
| `docs/desk/t1_development_manifest_20261018.json` | `3ef3bf6bbfee0f13e67ed15b1e9f935b1b7aed490f219c18b812ef724fa7408b` | `3ef3bf6bbfee0f13e67ed15b1e9f935b1b7aed490f219c18b812ef724fa7408b` |
| `data/t1/development_20261018.json` | `023f1828e1fdc5cce93de987ca83a71c7deedb13ca163021c608e9f9d90579f8` | `023f1828e1fdc5cce93de987ca83a71c7deedb13ca163021c608e9f9d90579f8` |
| `data/t1/development_20261018.started.json` | `1fc5a98286153062d89aa322dc7c16046d72b45a5587029df0ba83c265b2d377` | `1fc5a98286153062d89aa322dc7c16046d72b45a5587029df0ba83c265b2d377` |


## Validation stop

30 focused tests pass. Full suite: 1,049 tests in 231.837 seconds, one failure in
`test_isin_map_operations.IsinRefreshTest.test_summary_health_levels_and_warn_exit_status`.
The isolated test also fails. Its repeated cases use the real clock and one temp log;
after 18:00 IST the retry guard skips later cases. No unrelated fix was made.
No development regression rehearsal, hold-out rehearsal or real evaluation ran.
All four development hashes were rechecked unchanged before stashing the patch.

Resumed after separate clock-test fix 9cc2558. Restored runner full suite: 1,049 tests in 215.789 seconds, OK. P8-089 resolved. No settings or feature changes; both rehearsals still required.
