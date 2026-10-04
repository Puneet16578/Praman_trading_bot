# Follow-up 2 review: fixed 0.5 × ATR20 entry limit

Dated 2026-10-04. Interpretation of `shadow_replay_followup2_results.md` / `.json`
(produced by `python -u scripts/desk_shadow_followup2.py` at `47272e2`, protocol
`cb89f96`, 26 s). Research only: the active rulebook and the paper entry
convention are unchanged. This document recommends; it applies nothing.

## Provenance checked

- Raw replay SHA-256 `9a71fcf3…` = corrected G6 replay; base results hash, all
  six source hashes and the execution-evidence hash (`16b6d228…`) match.
- Store snapshot SHA-256 `8f0608c7…` is identical to the corrected replay's
  snapshot, so both runs saw the same data.
- Production store opened only through `mode=ro` for the online backup; its
  SHA-256 (`ecb36311…`), size and mtime are identical before and after. The
  temporary copy (`praman_limit_*`) was removed; none remains. SQLite's WAL
  sidecar files (`-wal` 0 bytes, `-shm`) appeared because the store is in WAL
  mode; a read-only connection cannot remove them. Nothing was written.
- Every baseline opening matched its frozen replay fill (the runner aborts on
  any mismatch in either direction).

## What it shows (primary 2019-2025, 45,770 corrected passes)

| | Baseline (next open) | Limit (decision + 0.5 ATR20) | Limit − baseline [95% CI] |
|---|---|---|---|
| Fill rate | 99.98% | 97.10% | −2.88 pp [−3.20, −2.61] |
| Per-trade cap breach rate at the fill | 30.38% | 27.47% | −2.91 pp [−3.14, −2.70] |
| Conditional excess, median (% of cap) | 11.50 | 9.60 | −1.90 [−2.16, −1.66] |
| Conditional excess, p90 (% of cap) | 40.67 | 24.08 | −16.59 [−18.21, −15.33] |
| Adverse20 among fills | 10.01% | 10.15% | +0.14 pp [+0.09, +0.20] |

Common-fill sensitivity (44,443 events filled under both): breach rate
−1.28 pp [−1.41, −1.17]; adverse20 identical by construction. The 2026
descriptive sample (7,142 passes) points the same way on every statistic:
breach −2.50 pp [−3.48, −1.76], fill rate 97.62%.

Reading it plainly:

1. **The limit helps, modestly.** The at-fill breach rate falls by about a
   tenth in relative terms (30.4% to 27.5%), and the worst breaches shrink sharply: the p90 excess falls from ~41% to
   ~24% of the cap, because the limit bounds how far above the decision price
   an entry can be.
2. **It does not solve the problem.** With the limit, 27.5% of fills still
   exceed the per-trade planned-loss cap. The cause is unchanged: quantity is
   sized at the decision price, and the next session typically opens higher,
   while the stop stays where it was.
3. **About 3% of trades are missed** (1,320 untouched limits in 2019-2025).
   Missed events are slightly better than average: adverse20 among limit fills
   is 0.14 pp higher, a small but statistically clear adverse selection.
4. Unknown inputs (7 primary, 2 descriptive) are identical across conventions
   and too few to matter.

Limits of the evidence, as registered: daily bars cannot establish intraday
order, queue position or tradability; touching the limit on the session low
does not guarantee a fill at the limit; circuit bands remain partly unknown;
the 2026 sample is a spent descriptive hold-out.

## Recommendation for the manual paper-trading convention (not applied)

**Recommend switching to the limit entry**: a day limit order at decision
price + 0.5 × ATR20, cancelled if unfilled that session, with quantity
unchanged. The breach reduction is consistent across periods with intervals
entirely below zero, the fill rate stays above 97%, and it removes the worst
gap-up entries. The cost is ~3% missed trades with a small adverse-selection
penalty, which is acceptable for a convention whose purpose is risk discipline.

Two caveats should travel with the switch:

- It is an incremental improvement. Treat the remaining ~27% at-fill breach
  rate as an open risk-control gap, not as solved.
- A materially stronger option was not tested and must not be assumed:
  **sizing the quantity against the limit price instead of the decision
  price.** Any fill at or below the limit would then have planned loss within
  the cap by construction, at the price of smaller positions. That is a
  different protocol (it changes quantities), so it would need its own
  preregistration before being measured or adopted.

The B4 entry-policy rule, stated before these results were seen (use the
limit if the paired breach-rate difference's 95% interval lies entirely below
zero and the fill rate is at least 60%), is evaluated and recorded with the
Strategy 0 registration in Part B.
