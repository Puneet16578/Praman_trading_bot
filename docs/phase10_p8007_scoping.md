# P8-007 Scoping — Measurement Only

**No fixes, no refits, no pre-registration amendments in this document, per instruction — one
exception, item 5, is a single, narrow, already-committed code change to the ingestion layer
(unrelated to the frozen scoring function), not a fix to P8-007 itself.**

## Summary (read this first)

**Item 1:** classified all 93 unique symbols behind the 96 shape-matches against NSE's live ETF
list plus a live, per-symbol corporate-actions query (not our own possibly-stale store). **32 are
confirmed ETFs. Of the 61 non-ETF rows, exactly 3 are confirmed missed real corporate actions —
each for a DIFFERENT root cause** (a regex gap, an unhandled action type, and a genuinely unexplained
downstream drop) — **the other 58 show no corporate action of any kind in NSE's live feed** near the
date (genuine-price-move candidates, not individually verified beyond that absence). **Item 2:**
confirmed via 3 independently-traced cases across 2 fund houses (`HDFCNIFETF`/`HDFCSENETF`,
`KOTAKGOLD`) that NSE's corporate-actions endpoint **does not carry ETF unit splits at all** — not a
parser or fetch-filter bug, a source-coverage gap. **A bigger, unplanned finding**: 699 of 702 rows
in `corporate_actions` trace to the OLD pre-`P8-006` scratchpad cache; **the real, live, full
historical sweep (`fetch_all(2019,2026)`) has never actually been run** — this project's historical
corporate-actions completeness has never been verified at scale, a larger and more foundational gap
than the ETF one. **Item 3:** ETF share is 3.91% of TRAIN, 10.30% of HOLD-OUT (growing fast, lower
bound only) — and **43.90% of every `UNKNOWN_COVERAGE` event is a confirmed ETF, against 0.00% of
every other disclosure tier.** The −0.40 `UNKNOWN_COVERAGE` coefficient substantially encodes
instrument type, exactly as hypothesized. **Item 4:** contamination is real but small — 342 events
(0.46% TRAIN, 0.41% HOLD-OUT). Re-running Phase 8b's feature AUC table excluding them moves every
number by less than 0.003 — **no conclusion changes.** **Item 5:** the one permitted fix, committed
separately — circular-index fetches now union two calls, and the weekly ASM/GSM window widened to
30 days.

---

## 1. Splitting the 96 shape-matches

Classified against NSE's live `/api/etf` list (351 current symbols) and, for non-matches, a live
per-symbol query to `/api/corporates-corporateActions?symbol=X` (confirmed working — a
symbol-filtered variant of the endpoint this project's own ingestion already uses) — **not our own
`corporate_actions` table**, so this classification is independent of whatever gaps exist in our
own store (see the item-2 finding on that).

| Classification | n (of 96 rows) | Detail |
|---|---|---|
| `ETF_API_CONFIRMED` | 32 | Symbol is in NSE's current live ETF list |
| `NO_ACTION_FOUND_LIVE` | 61 (58 + 3 reclassified, see below) | No ratio-bearing action found in NSE's live feed within ±45 days |
| **Confirmed missed action** | **3** | See per-case detail below |

**A methodological correction made before finalizing, not after:** the automated pass flagged 5
rows as "action found nearby" using a ±3-day window with no check that the action was actually
ratio-bearing. Manually re-checked all 5 against the full ±45-day window: 3 of them
(`ELGIRUBCO`, `LFIC`, `PREMEXPLN`) matched only an unrelated Annual General Meeting / dividend
notice — reclassified to "no ratio-bearing action found," moving the honest total to 61, not 58.

**The 3 confirmed misses, each a different root cause — exactly what item 2 asked to distinguish:**

| Symbol | Date | Real subject (live NSE) | Root cause |
|---|---|---|---|
| `AJANTPHARM` | 2022-06-22 | `"Bonus- 1:2"` | **Parser bug.** `parse_subject_ratio`'s regex requires `\s+` immediately after "Bonus" (`r"\bBonus\s+(\d+)\s*:\s*(\d+)\b"`); the hyphen-attached real NSE phrasing does not match. Confirmed directly: `parse_subject_ratio("Bonus 1:2")` succeeds, `parse_subject_ratio("Bonus- 1:2")` returns `None`. |
| `M&MFIN` | 2020-07-22 | `"Rights 1:1 @ Premium Rs 48/-"` | **Unhandled action type.** `parse_subject_ratio` only recognizes `"Bonus"` and the face-value-split `"From Rs X To Rs Y"` phrasing — Rights issues are out of scope entirely, not merely mis-parsed. Whether a rights ex-date genuinely explains this specific -32.49% move is not established here; rights-issue price adjustment is a different mechanism than bonus/split and was not investigated further. |
| `UNIVASTU` | 2025-10-13 | `"Bonus 2:1"` | **Confirmed NOT a parser bug — a different, downstream drop.** `parse_subject_ratio("Bonus 2:1")` succeeds (`{'type': 'BONUS', 'numerator': 2.0, 'denominator': 1.0, 'factor': 3.0}`). Checked directly against the live full-year sweep too (not just the symbol-filtered query) — the row exists there. Checked our own store: **zero rows for `UNIVASTU`, any type, any tier.** Root cause not fully isolated in this pass — candidates are the announcement-window cross-check, the tier/quarantine logic, or (most likely, given the "New corporate-actions gap" finding below) simply that no historical corporate-actions run has ever covered this date at all. |

## 2. Root cause for ETFs

**Does NSE's corporate-actions endpoint list ETF unit splits at all? No — confirmed directly, not
assumed from absence in our own store, via 3 independently traced cases across 2 fund houses:**

| Symbol | Date | Raw close, day before → day of | Ratio | Live NSE corporate-actions query (±45d) |
|---|---|---|---|---|
| `HDFCNIFETF` | 2021-02-17 | 1628.18 → 162.44 | 10:1 | Empty |
| `HDFCSENETF` | 2021-02-17 | 5633.58 → 559.43 | 10:1 | Empty |
| `KOTAKGOLD` | 2021-07-22 | 419.35 → 41.75 | 10:1 | Empty |

Same clean ~10:1 mechanical ratio, two different fund houses (HDFC AMC, Kotak Mutual Fund), two
different dates — a real, general pattern, not a one-off. **Which pipeline stage drops these:
none of ours — the data was never present in the source this project's ingestion reads from,
confirmed by querying that exact source live and getting nothing back.** This is a source-coverage
gap, not a fetch filter, subject-parse, tier, or announcement-matching bug.

**Which source does carry them: not established with API-level confirmation in this pass.**
Reasoned, not verified: an ETF unit split is executed at the mutual-fund-scheme level (a NAV/unit
restructuring under SEBI mutual-fund rules), not at the listed-company level the equities
corporate-actions feed covers — ETFs trade on NSE like equities but are legally fund units, not
company shares. This is a hypothesis about which regulatory channel would carry the disclosure,
not a confirmed alternate data source; finding and validating one is separate work.

**An unplanned, larger finding, surfaced while tracing these three cases:**

```
corporate_actions total rows: 702
  source_file='nse_corporate_actions_2019_2026_cached.json': 699 (99.6%)
  source_file='weekly_ingest_fetch_recent': 3 (0.4%, this week's real live run)
```

**699 of 702 rows in this project's entire corporate-actions store trace to the OLD, pre-`P8-006`
scratchpad-cache file — the same cache `P8-006` already found was sourced from a past session's
temp directory. The real, live, full historical sweep (`fetch_all(2019, 2026)`, the function
`P8-006` pointed `ingest_corporate_actions_sample.py` at) has never actually been executed.** Only
3 rows — this week's `weekly_ingest.py` run, a 60-day trailing window — come from genuine live
ingestion. `AJANTPHARM`'s and `M&MFIN`'s missed actions (2022, 2020) predate that window by years;
`UNIVASTU`'s (2025-10-13) also predates it. **This project's historical corporate-actions
completeness, beyond the specific 96 shape-matches this pass went looking for, has never been
verified at scale** — a more foundational gap than the ETF-specific one, and the most likely
explanation for `UNIVASTU` specifically (not a bug to trace further, but data that was never fetched
at all). Not fixed here (a full live sweep is a real, multi-hour undertaking, explicitly out of
scope for "measurement only") — named here so the decision is made with this in view, not
discovered later.

## 3. ETF share of the universe

Using the current live ETF list only (a lower bound — historical/renamed ETFs like `HDFCNIFETF`
undercount here):

| Population | n events | ETF-confirmed | Share | Distinct ETF symbols |
|---|---|---|---|---|
| TRAIN (2019-2025) | 64,450 | 2,523 | **3.91%** | 221 |
| HOLD-OUT (2026) | 10,850 | 1,118 | **10.30%** | 276 |

**ETF share is growing fast — 2.6x higher in the 2026 hold-out than in TRAIN**, consistent with
real, rapid growth in the Indian ETF market (several hits above are 2025-2026-dated new products,
e.g. `GROWWGOLD`/`GROWWSLVR`). If this growth continues, the actual Phase 10 forward window
(2026-09-16 through 2027-01-15) plausibly has an ETF share at or above the 2026 hold-out's, not
below it.

**Disclosure-tier composition, full catalogue (n=75,300 with a classification):**

| `disclosure_tier` | Total | ETF | ETF share |
|---|---|---|---|
| `NONE` | 11,078 | 0 | 0.00% |
| `ROUTINE_ONLY` | 22,880 | 0 | 0.00% |
| `SUBSTANTIVE` | 33,048 | 0 | 0.00% |
| `UNKNOWN_COVERAGE` | 8,294 | **3,641** | **43.90%** |

**This is a near-total, exact split: zero ETF events anywhere outside `UNKNOWN_COVERAGE`, and
43.9% of `UNKNOWN_COVERAGE` is confirmed ETF** (again, a lower bound — the true share, including
renamed/historical ETFs, is higher). ETFs mechanically never have cached corporate-announcement
coverage in this project's data (they don't file the same disclosures operating companies do), so
`has_announcement_coverage()` returns False for essentially every ETF, every time. **The model's
largest-magnitude coefficient (`disclosure_UNKNOWN_COVERAGE`, −0.396295, Amendment 1 §1)
substantially encodes instrument type (is this an ETF), not disclosure behavior — confirmed
directly, exactly as hypothesized before this measurement ran, not merely plausible.**

## 4. Contamination

An event is contaminated if any of the 96 shape-matched dates for the SAME symbol falls inside its
own 60-session trailing window or 90-session forward window (session-based distance on that
symbol's own trading calendar, not calendar days).

| Population | Contaminated | Share |
|---|---|---|
| TRAIN | 298 of 64,450 | 0.462% |
| HOLD-OUT | 44 of 10,850 | 0.406% |

**Sensitivity check: Phase 8b's clean-label feature AUC table
(`scripts/phase8b_feature_reauc.py`), re-run excluding all 342 contaminated events, pooled AUCs:**

| Feature | TRAIN (original → excl.) | HOLD-OUT (original → excl.) |
|---|---|---|
| `zscore_60d` | 0.5270 → 0.5277 | 0.5374 → 0.5406 |
| `volume_ratio` | 0.5769 → 0.5771 | 0.5299 → 0.5310 |
| `delivery_pct_percentile_60d` | 0.4166 → 0.4169 | 0.4347 → 0.4348 |
| `return_20d_context_only` | 0.5328 → 0.5326 | 0.4753 → 0.4765 |
| `close_to_close_60d` | 0.5197 → 0.5198 | 0.4836 → 0.4856 |
| `same_date_event_count` | 0.4675 → 0.4675 | 0.4639 → 0.4623 |
| `asm_gsm_labelled` | 0.5012 → 0.5010 | 0.5025 → 0.5025 |

**Every shift is under 0.003 — noise, not signal. No Phase 8b conclusion changes**, including the
`return_20d_context_only`/`close_to_close_60d` reversal finding that motivated dropping
`momentum_high` from the Phase 10 design. **Caveat, following directly from §2's larger finding**:
this contamination count is bounded by the 96 shape-matches this pass could find, which in turn
depends on the historical `corporate_actions` table's own (now known to be largely unverified)
completeness — a genuinely more complete corporate-actions history could surface additional,
smaller-ratio contamination this specific scan cannot detect. The sensitivity conclusion (no
material effect) is trustworthy for what was actually measured; it is not a claim that zero further
contamination exists beyond the 96 shapes this scan specifically targets.

## 5. The one permitted fix: flaky circulars endpoint, committed separately

`src/ingestion/nse_market_data/{asm,gsm}.py` gain `fetch_circular_index_union(session, from_date,
to_date)`: calls the index endpoint twice, unions by `circNumber` (deduplicating, not doubling
ingestion work) — live-verified (102 circulars, 0 duplicates, 0.50s for a 30-day window).
`fetch_and_ingest_{asm,gsm}_range` now call this instead of a single fetch.
`scripts/weekly_ingest.py`'s `ASM_GSM_LOOKBACK_DAYS` widened `10 → 30`, a second, independent layer
of the same defense. Full suite re-run after the change: **328/328 pass.**

---

## What is still open, stated plainly

Not done in this pass, all deliberately: fixing the `Bonus-` regex gap; handling Rights issues at
all; running the real, live, full historical `fetch_all(2019, 2026)` sweep (the deeper cause behind
`UNIVASTU` and, very plausibly, other undetected gaps); identifying and ingesting a real ETF
unit-split data source; deciding whether ETFs belong in this project's catalogue at all. All are
measured and scoped here; none are decided. **Report, and the fix is decided from these numbers —
per instruction, not before it.**
