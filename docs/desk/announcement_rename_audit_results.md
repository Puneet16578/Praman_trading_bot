# P8-046 historical reach: renamed-security announcement audit

Dated 2026-10-05. Report only: no frozen classification, catalogue, label, pre-registration or
research result is changed. Machine-readable results: `announcement_rename_audit_results.json`;
plan, fixed before any fetch: `announcement_rename_audit_plan.json` (seed 20261005; input baseline
hash-checked). Executed in the approved bounded session (`announcements_bulk_rollout_results.json`):
20 audit requests of the 20 approved, all HTTP 200, no failures.

## Population and sample

The audit uses the **195** rename groups (securities whose ISIN maps to more than one symbol) in
the historical Amendment 4 rename log (`logs/amendment4_renames_output.log`, P8-010), not the
current ISIN map's 205. Checked directly: all 195 are still in the current map; the 10 extra
current groups are 7 fund-unit (INF) ETF groups, outside the equity research universe, and 3
equity renames absent from the historical log (TIDEWATER/VEEDOL, KAVDEFENCE/KAVVERITEL,
TIPSINDLTD/TIPSMUSIC), which this audit therefore does not cover. 127 of the 195 have eligible
catalogued events through 2026-09-15, **4,402 events** in total. Twenty securities were drawn
uniformly from the 127, with one eligible event per sampled security, and each request covered that
event's exact ten-session pre-event window from the bulk endpoint.

## Result

| | Count |
|---|---:|
| Sampled securities whose frozen disclosure tier differs from the bulk comparison | **12 of 20** |
| ... of which missing disclosures change the tier (all frozen `UNKNOWN_COVERAGE`) | 10 |
| ... of which only `UNKNOWN_COVERAGE` would become a genuine `NONE` (bulk also empty) | 2 |
| Sampled securities with the same tier and the same stored/bulk counts | 8 |

Every changed case was frozen as `UNKNOWN_COVERAGE`: no announcement was stored under the event's
symbol, while the bulk endpoint returns the security's announcements under its later symbol (for
example MINDAIND -> UNOMINDA, GET&D -> GVT&D, EXCEL -> LANDSMILL). Eight of the ten would become
SUBSTANTIVE. No sampled event with stored announcements had a different tier.

**Estimate of affected catalogued events (of 4,402 in renamed securities):**

- Event-weighted ratio estimate: **about 2,356 events (53.5%)** had their frozen tier affected;
  Horvitz-Thompson estimate about 2,407.
- Restricting to tier changes caused by missing disclosures: **about 1,816 events**.
- Against the whole frozen catalogue (70,638 events) that is roughly 3.3% (2.6% for missing
  disclosures), concentrated entirely in the `UNKNOWN_COVERAGE` tier.
- Descriptively, 211 of 321 further catalogued events whose windows fell inside the sampled
  requests also changed; conservative identification bounds are 211 to 4,292 events.

## Sampling limits

- Only 20 securities, one event each. The event-count weighting assumes the sampled event
  represents its security; within-security variation is unmeasured, so no precise population
  confidence interval is claimed. The binary changed/unchanged rate itself has wide uncertainty
  (12/20).
- The comparison uses today's bulk contents. NSE can revise or remove historical records, so this
  is not proof of what Phase 7's per-symbol fetches received.
- Bulk rows are matched by ISIN. A security whose ISIN changed inside a window (for example after
  a share split) would be undercounted.
- Audit windows had no whole/split completeness check (one request each), unlike the backfill.

## What it means

P8-046's historical reach is material for one feature: a large share of `UNKNOWN_COVERAGE`
assignments in renamed securities reflect the symbol-keyed backfill, not an absence of disclosure.
This is consistent with, and adds scale to, the known instrument/coverage confound in that
coefficient. Nothing frozen is changed; any re-analysis would need its own registration and could
only be a separately labelled secondary comparison to the pinned evaluation.
