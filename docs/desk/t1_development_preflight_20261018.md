# T1 development evaluation: stopped before outcome access (18 October 2026)

Started on clean master at `9dea1e8b785b4c4aeb0c044e8774478c3210ea7d`.
No evaluation was attempted. No result was seen, no result file was created, and
no real-outcome computation was performed. The once-only evaluation remains pending.

## The 350-stock-day reconciliation

The additional 2,153 identity-unknown stock-days were previously classified as:

| Previous category | Stock-days |
|---|---:|
| Eligible | 1,803 |
| Fund unit | 183 |
| ATR window incomplete | 166 |
| ATR window unadjustable | 1 |
| Total | 2,153 |

The other 350 were already excluded. `features.exclusion_causes` assigns identity
before fund/ATR exclusions; delaying snapshot availability changes their reported
category without changing their inclusion. This is not a population-count bug.
The 186,581 identity-exclusion figure is an exclusion-category count, not a count
of rows otherwise proven eligible: some rows also fail other eligibility conditions.

Verified with a read-only, input-only audit: hash-checked only ISIN CSVs dated
through 2024, found newly listed symbols on each snapshot date, and checked their
same-day EQ presence/knowledge, fund status and 21-session ATR-window completeness
and structural breaks. SQL event dates were bounded through 2024; no later ISIN
file contents or index series were loaded. No price or outcome values were printed.
The counted total equals the observed increase exactly.

## Blocking read-isolation defect

P8-087: the existing panel loader queries 40 session dates after its requested end;
the index and identity loaders open later source files before the panel is trimmed.
The outcome guard does not prevent these earlier reads. This conflicts with the
user's no-2025-read requirement. Found through source inspection, before invoking
these loaders or building a real evaluation runner. No code, setting or threshold
was changed, and no workaround or retry was attempted.

No run manifest or input-hash set is presented as an evaluation record because
there was no evaluation. The source commit above identifies the stopped preflight.
No PASS/FAIL/INCONCLUSIVE verdict exists. The 2025 hold-out remains PARTIALLY
EXPOSED under the protocol, and no hold-out evaluation was started.

P8-088 separately records the requested low-priority SQLite ResourceWarnings.
No tests were rerun during this stopped preflight; code is unchanged from the
previous passing full suite. The nightly task was checked read-only: Ready.
