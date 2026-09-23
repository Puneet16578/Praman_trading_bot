# Phase 10 Pre-registration — Amendment 3

**Dated 2026-09-22. Amends `docs/phase10_preregistration.md` and Amendments 1-2 without editing
any of them, per their own immutability notices. This amendment is not edited after its own commit
either — a future correction is Amendment 4, in a new file.**

## Summary (read this first)

Amendment 2 §5 scheduled bhavcopy, announcements, and ASM/GSM but omitted corporate actions —
without them, a real split/bonus in the window goes unadjusted (a 1:2 split reads as a fabricated
-50% day), a false label the 5%-missing-data rule cannot catch since the row looks complete.
**Fixed: corporate actions added to the weekly schedule** (`fetch_recent`, a narrow-window sibling
of `fetch_all` sharing the same tier/quarantine/demerger-marker logic — only *how much history* is
fetched changes). **A pre-specified check is defined** for scanning forward-window returns for
unadjusted split/bonus shapes, run before the binding evaluation. **Run as a mechanism check against
existing data (inspecting prices, not outcomes — not an interim look), it found something bigger
than expected**: 96 hits, zero explained by an existing action record, a large ETF cluster on shared
dates with near-exact ratios — traced directly (`HDFCNIFETF`, a confirmed real 10:1 unit split
absent from `corporate_actions` entirely). **This project has never captured ETF unit splits, at
any point in its history, not only in the forward window.** Logged as `P8-007`, found and scoped,
not fixed today. Results: `docs/phase10_housekeeping3.md`.

---

## 1. Corporate actions added to the weekly schedule

`src/ingestion/nse_market_data/corporate_actions.py` gained `fetch_recent(lookback_days=60)`, a
narrow-window sibling of the existing `fetch_all(year_from, year_to)`: both now share
`_fetch_corporate_actions_range` (the underlying API call, parametrized by explicit dates instead
of whole years) and `_fetch_announcements_for_actions` (the per-symbol/ex-date announcement-window
loop), factored out so the two entry points do not duplicate logic (CLAUDE.md invariant 1).
`fetch_recent`'s output is written through the exact same `ingest_corporate_actions()` path
`fetch_all` uses — **the same tier logic (announcement-derived knowledge_date, subject-field ratio,
quarantine on disagreement) and the same demerger/capital-reduction exclusion-marker handling apply
automatically**, unchanged, because nothing about ingestion itself changed, only how the input list
of actions is gathered.

`scripts/weekly_ingest.py` gained a fourth step, `corporate_actions`, between `announcements` and
`asm_gsm` (bhavcopy → announcements → corporate actions → ASM/GSM). 60-day lookback, safe to
re-run or overlap for the identical P4-009 duplicate-business-key reason ASM/GSM's own overlap is
safe.

**Live-verified before wiring in** (`fetch_recent(lookback_days=14)`, a quick check, not the full
60-day step): 370 real actions fetched for a real trailing 14-day window, 2 real announcement-window
fetches triggered (the rest were dividends, correctly not bonus/split-eligible). Full suite re-run
after the refactor: 328/328 pass.

## 2. Pre-specified split/bonus shape check

**Procedure, fixed now, before the forward window exists:**

`R = return_1d` (percent) for every catalogued event in the forward window. A hit is any event with
`R` within **±2 percentage points** of one of seven pre-specified shapes — each the raw,
unadjusted one-day return a common split/bonus ratio would produce if its adjustment factor were
missing (a bonus/split of N-for-M yields `1 - M/N`):

| Shape | Ratio | Shape | Ratio |
|---|---|---|---|
| -33.3% | 3-for-2 | -80.0% | 5-for-1 |
| -50.0% | 2-for-1 | -83.3% | 6-for-1 |
| -66.7% | 3-for-1 | -90.0% | 10-for-1 |
| -75.0% | 4-for-1 | | |

For every hit, cross-reference `corporate_actions` for a `BONUS`/`SPLIT` row for that symbol within
a 10-day window of the event date:
- **A matching action exists** but `R` still shows the raw shape → the action IS in the store and
  the adjustment did not apply. A DIFFERENT, more serious problem (an adjustment bug), reported
  distinctly from a missing action, not folded into the same bucket.
- **No matching action** → investigated directly against the live corporate-actions endpoint for
  that exact symbol/date (not assumed from the shape alone). Confirmed real action → ingest through
  the normal idempotent path, rebuild the affected catalogue rows **at the pinned commit**
  (`a01eda4`, Amendment 2 §2 — this pin governs the FEATURE-COMPUTATION code, which does not change
  by fetching more raw corporate-actions data; ingesting more real data and recomputing features
  from it with the same pinned logic are not in tension), and report every correction made. No
  confirmed action, but a real large move → leave untouched, state so explicitly, per event.
  **A third outcome, found necessary by §3 below and not anticipated when this check was first
  specified: the symbol may be an ETF whose corporate action this project's ingestion cannot
  currently source at all (`P8-007`)** — reported as its own category, not forced into either of
  the other two.

**Inspects prices (`return_1d`), never outcomes (the `relative_t0_primary` label) — not an interim
look**, per the original instruction, and implemented that way: `scripts/
phase10_scan_split_bonus_shapes.py` never reads or computes any outcome label.

## 3. Run as a mechanism check — a real, unanticipated finding

Run against the EXISTING historical catalogue (the forward window does not exist yet; historical
data is not an "outcome" this pre-registration is protecting, so this is a legitimate mechanism
check, the same discipline Amendment 1's top-decile bootstrap validation and Amendment 2's threshold
freezing already used).

**96 events matched a target shape within tolerance. Zero were explained by an existing
`BONUS`/`SPLIT` record — not some, none.** Inspecting the hit list directly rather than assuming
the shape alone proves a defect: a large cluster are ETFs sharing near-identical dates and near-exact
ratios (`HDFCLOWVOL`, `HDFCMID150`, `HDFCMOMENT`, `HDFCNEXT50`, `HDFCNIF100`, `HDFCNIFBAN`,
`HDFCNIFETF`, `HDFCNIFIT`, `HDFCPVTBAN`, `HDFCSENETF`, `HDFCSENSEX` all near -90% on 2023-10-20 or
2024-02-02; `MIDCAPIETF`/`ALPL30IETF`/`FMCGIETF`/`QUAL30IETF`/`NIF100IETF`/`MIDSELIETF` all near
-90% on 2024-05-10) — a pattern of coordination no set of genuinely independent large price moves
would produce.

**One traced fully, not left at the statistical shape:** `HDFCNIFETF`, `series='EQ'` (the same
series equities use — not a series-filtering gap), raw `bhavcopy` close **1628.18 (2021-02-16) ->
162.44 (2021-02-17)**, exactly a 10:1 ratio. Confirmed: this project's `corporate_actions` table has
zero rows for this action, this symbol, this date, or any ETF unit split at all, in the full
history.

**This project's corporate-actions ingestion has never captured ETF unit splits — a finding about
the EXISTING historical catalogue, not only a forward-window risk.** Logged as `P8-007`
(`docs/DEFECT_REGISTER.md`). **Not fixed today**: the remaining 95 hits were not individually traced
(one full trace established the mechanism; tracing 95 more for no new methodological information
was not a good use of this pass's scope), and building real ETF corporate-action ingestion requires
first identifying what disclosure path actually carries this information, since the standard equity
endpoint does not (or not in a recognized shape) — genuine new development. **A scoping question
this raises but does not answer: whether ETFs belong in this project's catalogue at all**, given its
actual purpose (equity manipulation forensics) — left for the project owner to decide, not assumed
here.

**Consequence for the pre-specified check (§2) when it eventually runs on the real forward window:**
expect a nonzero, possibly large, hit count as the norm, not a rare or alarming outcome — and expect
a real share of hits to resolve to "ETF, not currently ingestable" rather than cleanly to "missed
action" or "genuine move." The check's three-way categorization (§2) was updated to reflect this
before being finalized, not after being surprised by it a second time.

---

## What is still not done

Corporate actions are now scheduled weekly and the pre-specified check is fully defined — but ETF
corporate-action ingestion itself is not built, the 95 untraced historical hits are not resolved,
and the forward window does not exist yet for the check to run against for real. Nothing here
evaluates the redesign; nothing here is the binding evaluation.
