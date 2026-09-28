# Praman Expert Desk — Phase 1 report (STOP 3, closed)

**Status: CLOSED.** The STOP 3 report below was reviewed; four fixes were required before paper
trading could start (whole-share position sizing, daily ingestion, automatic pending-open
completion, and a test-hygiene cleanup). All four are implemented, tested, and committed --
see "Post-STOP-3 fixes" at the end of this document for what changed and why. The worked examples
and numbers below are updated to reflect the fixes (in particular, Example 1's position size is now
the corrected whole-share figure). Phase 1 is closed; paper trading begins.

## Summary

Phase 1 (the deterministic core) is built, tested, and committed. Two stores exist: Praman
(read-only to the Desk) and the Desk's own append-only journal. Eight gates (G1-G8) run in full on
every assessment — never short-circuited — and a fixed priority mapping derives one of six decision
states: `INSUFFICIENT`, `RESEARCH_REQUIRED`, `WATCH`, `ELIGIBLE`, `VETO`, `EXPIRED`. No LLM, no
network call, no numeric trade score anywhere in the path. Rulebook v1 (capital, risk, liquidity,
surveillance, behavioural limits) and cost config v1 (Zerodha-confirmed transaction costs) are
committed, git-tracked-and-clean, SHA-256-identified, and both load successfully. `desk replay`
reproduces a past decision exactly via TEMP-VIEW shadowing on both stores. Paper execution has two
hindsight guards and never re-assesses an approved decision. The full test suite is 479/479 passing,
0 skipped, including a firewall test proving the Desk never touches outcome-label code. Two
remaining `<FILL>`-type items from earlier reviews are now resolved (capital, brokerage, DP charge);
one rate (GST) and the slippage model remain honestly unconfirmed, as designed. This report is the
STOP 3 checkpoint — nothing further proceeds without your review.

## What Phase 1 built (L0/L1 + minimal L4/L5 only — L2/L3/L6/L7 are later build-order phases)

| Layer | What exists | Files |
|---|---|---|
| L0 (store) | Praman read-only access, Desk's own append-only store | `desk/lib/store.py`, `shared/sqlite_readonly.py`, `desk/lib/schema.py`, `desk/lib/connection.py` |
| L1 (evidence) | Epistemic types, evidence bundle assembly, coverage, provenance | `desk/evidence/types.py`, `desk/evidence/bundle.py`, `desk/evidence/coverage.py` |
| L4 (risk, partial) | Position sizing, stress loss, six risk-related gates | `desk/risk/officer.py`, `desk/gates/checks.py` |
| L5 (decision) | Gate engine, decision states, append-only journal, replay | `desk/gates/engine.py`, `desk/journal/store.py`, `desk/replay.py` |
| — | Paper execution, minimal monitor, ingestion health, CLI | `desk/paper/execution.py`, `desk/paper/open.py`, `desk/monitor.py`, `desk/ingestion_health.py`, `desk/cli.py` |

CLI: `desk rulebook validate\|show`, `assess`, `paper open\|close`, `monitor`, `journal show`,
`replay`, `status` — all present and wired to the tested modules underneath, no extra logic in the
CLI layer itself.

## Design decisions made during review (STOP 1 / STOP 2)

- **Replay uses TEMP VIEW shadowing**, not per-symbol reconstruction or a `read_as_of` parameter —
  verified empirically to preserve query plans/index usage on a real `mode=ro` connection.
  `desk/replay.py` shadows **both** stores (Praman at `praman_watermark`, the Desk's own journal at
  `desk_watermark`), since G6/G7 read the journal and a trade logged after the decision must not
  leak into its replay either.
- **G1 deliberately never reads `logs/weekly_ingest.log`** (mutable, gitignored, outside the
  bitemporal store) — it checks only what the store itself can prove: the date is populated and the
  symbol has no gap the wider market doesn't share. A log-derived quality signal would make replay
  non-reproducible. Named as a real, deferred gap (would need Praman to persist ingestion-quality as
  bitemporal rows).
- **Disclosure categories default to UNKNOWN, never Praman's own silent ROUTINE default**, for any
  category the Desk's own strict classifier doesn't recognize (`desk/evidence/bundle.py:_disclosures`).
- **Config integrity**: `git ls-files --error-unmatch` (tracked) AND `git diff --quiet HEAD --`
  (clean) together — either alone has a gap (untracked files pass a bare `git diff`). Hashing is
  CRLF-normalized (`.gitattributes` also forces `eol=lf` on `rulebook/*` and `config/*`) so the same
  content hashes identically regardless of `core.autocrlf`.
- **`max_asm_stage` is rejected at rulebook LOAD time** if non-null (`desk/lib/rulebook.py`'s
  `field_validator`) — stage-ordering logic doesn't exist in Phase 1, so this can't be silently
  loosened; it fails before any assessment can start, not mid-assessment.
- **No gate short-circuiting**: `run_assessment` computes all eight gates unconditionally, then a
  pure function (`_derive_state`) applies the priority mapping. A VETOed or INSUFFICIENT decision
  still carries every gate's result (tested explicitly).
- **Paper opens have two hindsight guards**: (1) a decision can only be opened if it was a *live*
  assessment (`as_of_is_live`), never an explicit historical `--as-of`; (2) staleness is WALL-CLOCK
  calendar days since assessment, and the fill can only land on a session strictly after the
  calendar date `paper open` itself runs on — resolving a real paradox where comparing to the
  store's own latest date made the required D+1/D+2 test scenario impossible to satisfy.
- **`paper open` never re-assesses** — it executes the exact persisted `position_size` and the
  linked thesis's `planned_stop`/`planned_target`, confirmed by mutating the store between assess
  and open and checking the opened trade is unaffected.
- **Two schema additions** made during STOP 2 review: `risk.stress_loss_floor_pct_of_position`
  (replacing a hardcoded rupee floor) and `liquidity.participation_pct_of_stressed_volume` (so
  days-to-exit assumes you only take a share of stressed volume, not all of it).
- **Ingestion health is reported, never gates**: `desk status` prints a plain staleness line from
  the mutable log, entirely outside any decision record.

## Rulebook v1 and cost config v1 — now committed

- `capital_allocated_inr: 500000` — your own confirmed figure, not a suggestion.
- Every other rulebook limit: proposed with a one-line reason, reviewed, approved (`rulebook/desk_rulebook_v1.yaml`).
- Cost config: **six of eight rate blocks CONFIRMED** against Zerodha's official charges page
  (checked 2026-09-27) — brokerage (₹0/order), depository charge (₹15.34/scrip/sell day,
  GST-inclusive), STT (0.1% both legs), NSE transaction charges (0.00307% per leg — corrected from
  an earlier draft's 0.00297%), SEBI fee (0.0001%/leg), stamp duty (0.015% buy-side only).
- `gst` (18%, statutory rather than broker-specific) stays `TO_VERIFY`.
- `slippage_by_liquidity_bucket` is marked `ASSUMPTION` — a new status added to the schema,
  distinct from `TO_VERIFY`, for a modelling estimate with no published rate to ever check it
  against.
- `tests/test_desk_cost_round_trip.py` checks the real, committed config against an independently
  hand-written calculation for a ₹50,000 delivery trade: **₹126.58 round trip** (₹59.37 buy leg +
  ₹67.21 sell leg), including an explicit check that the GST-inclusive DP charge is never taxed
  twice.

## Remaining UNKNOWNs (honest, by design — not hidden)

**Evidence dimensions never ingested in Phase 1** (typed `Unknown`, never guessed): `fundamentals`,
`bid_ask_spread`, `circuit_band`. `required_evidence_dimensions` in the rulebook deliberately
excludes these so G2 doesn't fail on every single assessment.

**Cost/model uncertainty, explicitly labeled:**
- `gst` rate (18%) — `TO_VERIFY`, not broker-specific.
- Slippage by liquidity bucket — `ASSUMPTION`, can only be replaced once real paper-trade fills
  exist to measure it from (Desk phase 9, the evaluator).
- Stress loss's `circuit_band_caveat`: does not account for a circuit-locked exit becoming
  impossible (`desk/risk/officer.py`).

**Named, deliberate Phase 1 gaps:**
- **Staleness is calendar-day, not trading-session-aware** (`desk/paper/open.py`) — a Friday
  decision opened Monday would read as 3 days stale though zero sessions elapsed. Fixing this needs
  a reliable "what is today's session, if any" source Phase 1 doesn't have (Praman's ingestion is
  nightly batch, not live).
- **No background resolver for `PENDING` paper opens** — if the next session's data isn't ingested
  yet, `paper open` returns PENDING and must be re-run manually; a monitor-integrated auto-retry is
  deferred.
- **`max_asm_stage` stage-ordering logic doesn't exist** — any ASM stage vetoes; a graded tolerance
  needs a later phase.
- **`get_disclosure_window` (pinned Praman code) still builds its own internal EQ-only history**
  regardless of the Desk's own `extend_with_series` fix — a real, disclosed limitation of reused
  pinned code, moot for outcomes since G4 already vetoes trade-for-trade series outright.
- **G1 excludes any mutable-log-derived ingestion-quality signal by design** (reproducibility), so a
  real ingestion problem not yet visible in the store itself won't be caught by G1 — only by the
  separate, non-gating `desk status` ingestion health line.
- **No correlation/portfolio-level risk beyond per-stock and per-sector caps** — a full six-layer
  risk officer, market/sector context engines (L2), thesis graph and red team (L3), "what changed"
  monitoring and edge/drift tracking (L6), and the learning loop (L7) are later build-order phases,
  not built yet.
- **`paper_to_live_criteria` is unevaluated** — no paper trades exist yet to check it against.
- **`inference_rules.thresholds` is an empty registry** — no inference rules are defined in Phase 1;
  it exists only so a later `Inference` claim has something real to validate a `rule_id` against.

## Test output (real, this run)

```
$ python -m unittest discover -s tests -p "test_*.py"
...
Ran 479 tests in 96.596s

OK
```

No skips, no failures, no errors — includes `test_desk_no_outcome_labels.py` (the firewall test:
greps every file under `desk/` for forbidden outcome-label imports/literals, and independently
re-confirms outcome-label computation is still confined to the three known scripts, none under
`src/`), the append-only trigger tests, the rulebook/cost integrity tests (git-tracked-and-clean,
CRLF-hash-stability, the real config now loading and matching approved values), the epistemic-type
tests, one test per decision state on the real examples below, the risk-budget/BAJFINANCE-split
tests, the real gap-through-stop fill test, the five no-hindsight/no-reassessment paper-open tests,
and the replay-after-append test.

## Two worked examples, real data

Both run against the real production Praman store, the committed rulebook (`desk_rulebook_v1.yaml`,
sha256 `65338bca2157c59e…`) and the committed cost config (`costs_india_delivery_v1.yaml`, sha256
`8670e2e48632cabf…`), via `run_assessment` directly (the same code path `desk assess` uses) against
a throwaway scratch journal so this report doesn't write permanent entries into the real append-only
journal before you've reviewed it.

### Example 1 — ELIGIBLE: AXISBANK, as of 2021-10-27, with a complete thesis

```
state = ELIGIBLE
as_of_is_live = False   (a historical --as-of date, not "today" — expected for a backtest-style demo)
  G1: PASS  []
  G2: PASS  []
  G3: PASS  []
  G4: PASS  []
  G5: PASS  []
  G6: PASS  []
  G7: PASS  []
  G8: PASS  []
  position_size = 66 shares          <- whole shares (Fix 1, see "Post-STOP-3 fixes" below);
                                         raw/capped sizing works out to 66.6667, floored to 66
  stress_loss_inr = 4950.00
    planned_loss_component_inr = 3422.04
    worst_gap_component_inr   = 1662.47
    floor_component_inr       = 4950.00   <- the binding component here (10% of 66 x Rs 750)
    caveat: Circuit bands are UNKNOWN in Phase 1 -- this figure does not account for
            a circuit-locked exit becoming impossible.
  evidence_bundle.content_hash() = efed2042de8d64cd4286feb7d2f8e4a9c4ebf402b0a7ff343a8b6c14dba89800
```

All eight gates pass on real evidence: a real trading day with no gap (G1); price, volume,
delivery, disclosures, surveillance, corporate-actions and (user-supplied) sector all present as
Facts (G2); no structural break in the trailing 60 sessions (G3); not under ASM/GSM and not
trade-for-trade (G4); the order size clears both the ADV and days-to-exit liquidity checks (G5); the
stress loss (₹4,950, the 10%-of-position floor, exceeding both the planned-loss and worst-historical-
gap components) fits the open-risk/per-stock/per-sector budgets (G6); no behavioural brakes tripped
(G7); the thesis supplies every required field (G8). Note that the floor — not the historical gap or
planned loss — binds here, which is exactly why the rulebook's percentage-of-position floor exists
rather than relying on planned loss alone.

### Example 2 — VETO: CAPTRUST, as of 2026-08-05, no thesis

```
state = VETO
as_of_is_live = False
  G1: PASS     []
  G2: PASS     []
  G3: PASS     []
  G4: FAIL     ['CAPTRUST is under ASM (stage I) as of 2026-08-05; rulebook tolerates no ASM stage.']
  G5: UNKNOWN  ['No thesis supplied.']
  G6: UNKNOWN  ['No thesis supplied.']
  G7: PASS     []
  G8: FAIL     ['No thesis supplied.']
  evidence_bundle.content_hash() = ba3104116094f4a1dab95ccede7b64b6e6668db23e744f53e26ecb2ab59f33f3
```

CAPTRUST is a real, verified ASM (Additional Surveillance Measure) stage-I stock as of this date.
G4 fails on that fact alone — the rulebook's `max_asm_stage: null` tolerates no ASM stage at all —
and VETO outranks every other state in the priority mapping regardless of what G5/G6/G8 show. Note
that **all eight gates still ran and are recorded** (the no-short-circuit guarantee): G5/G6 report
UNKNOWN rather than being silently skipped, because no thesis was supplied to size a candidate
trade against, and G8 independently fails for the same reason. A real BE-series (trade-for-trade)
stock was tried first for this example and rejected as the wrong example — it produced INSUFFICIENT
instead of VETO due to a pinned-Praman-code limitation in `get_disclosure_window`'s own internal
history construction (documented above); CAPTRUST was substituted as a cleaner, unambiguous VETO
case.

## Commits, in order

```
339557e Add the Praman Expert Desk design brief and its constitution to CLAUDE.md
6844d64 Desk Phase 1: the deterministic core
c30f3a0 Desk Phase 1, STOP 2 fixes: no-hindsight paper opens, persisted decisions, no gate short-circuit
69070fe Desk cost schema: add ASSUMPTION status; test real round-trip cost
79e317c Rulebook v1: approved risk/liquidity/behavioural limits, STOP 2
59f4717 Cost config v1: six rates confirmed against Zerodha, GST-inclusive DP charge
810b756 Desk tests: real rulebook/cost config now load successfully
```

## Post-STOP-3 fixes (before Phase 1 close)

Your STOP 3 review confirmed both worked examples and accepted every open UNKNOWN, with one bug and
three required changes before paper trading starts.

**Fix 1 — whole shares.** NSE trades in whole shares; `compute_position_size` (`desk/risk/officer.py`)
now floors to a whole share AFTER every risk/liquidity cap is applied, so every downstream figure
(planned loss, stress loss, G5's order value, G6's capital-at-stock addition) automatically uses the
same final integer quantity. If the floored size is 0 -- a single share already exceeds the tightest
cap -- `desk/gates/engine.py` now reports this as a stated G6 FAIL rather than a silent size-zero
PASS, which VETOes via the existing priority mapping. AXISBANK's ELIGIBLE example above is corrected
to 66 shares (was 66.6667); a new test (`tests/test_desk_states_real_data.py::test_single_share_
exceeding_the_per_stock_cap_is_vetoed`, plus two pure unit tests in `test_desk_risk.py`) confirms a
high-priced thesis where even one share exceeds the per-stock cap is VETOed with a stated reason.

**Fix 2 — daily data for daily paper trading.**
- **(a) Ingestion is now daily on trading weekdays, not weekly.** `scripts/weekly_ingest.py` (kept
  its name -- see its own module docstring) gained a sixth step, `bhavcopy_today`, which requests
  TODAY specifically (the original steps deliberately stop at yesterday) and retries up to 6 times,
  15 minutes apart, if NSE hasn't published yet. Exact PowerShell to register the new weekday-evening
  scheduled task, and to confirm registration, is in `docs/OPERATIONS.md`'s "Daily ingestion"
  section -- **not yet actually registered**, per that section, exactly as before for the same
  reason (registering a persistent scheduled task is the user's action to take).
- **(b) Recorded in `docs/OPERATIONS.md`** as an operational note, citing the pre-registration's own
  weekly-minimum requirement (`docs/phase10_preregistration_amendment2.md` §5) that daily satisfies
  as a strict superset -- explicitly not a pre-registration amendment, since no reference query or
  evaluation criterion changes.
- **(c) `desk monitor` now completes pending paper entries automatically.** `desk paper open`
  returning PENDING now logs a `PAPER_OPEN_PENDING` journal event with the fill target date FROZEN
  at that moment; `desk monitor` (`desk/monitor.py:complete_pending_paper_opens`) finds any such
  still-open entry and retries at that SAME frozen date (`desk/paper/open.py:resume_pending_open`),
  never a freshly-recomputed "now" -- waiting for ingestion to catch up must not silently push the
  target fill session forward. This is not a new autonomous decision: the human already approved
  opening this exact decision when `paper open` was first run. Tested end-to-end with real AXISBANK
  data (`tests/test_desk_monitor_pending_opens.py`): open on D with D+1 deliberately absent from the
  store, confirm still-pending with no fill, then a real write_fact of D+1's own real row, then
  confirm `desk monitor` fills at D+1's real open with no further action.
- **(d) New `desk evening` command.** Refuses outright if today's data isn't in the store yet (an
  honest refusal, including on a genuine weekend/holiday, since this command keeps no invented
  holiday calendar to tell that apart from a late ingestion); otherwise runs the monitor and prints
  what changed, pending/filled/refused opens, exits, and open positions. New assessments
  (`desk assess`) remain a separate, manual step.

**Small — test hygiene.** The rulebook/cost-config integrity tests were creating scratch git
repositories under `data/desk/_test_scratch_repos` (a path inside the project tree). Both that test
class and the CRLF/LF hash-stability test now use the OS's own temp directory
(`tempfile.mkdtemp()`), cleaned up in `tearDown`/`finally` exactly as before -- nothing under the
project tree is created or left behind.

**Full suite after all four fixes: 484/484 passing, 0 skipped** (479 + 2 whole-share tests + 2
per-stock-cap VETO tests, counted once each under `DecisionStateRealDataTest` and once under its
`AllGatesRunEveryTimeTest` subclass, per that file's existing pattern + 1 pending-open test):

```
$ python -m unittest discover -s tests -p "test_*.py"
...
Ran 484 tests in 136.378s

OK
```

**Commits, in order** (appended to the list above):

```
f0474a1 Fix 1 (post-STOP-3 review): whole-share position sizing
d87e5f3 Fix 2a/2b (post-STOP-3 review): daily ingestion for daily paper trading
a5e2cdb Fix 2c/2d (post-STOP-3 review): desk monitor auto-completes pending opens
c9849e1 Small (post-STOP-3 review): scratch git repos use the OS temp dir
```

## Phase 1 is closed

Paper trading begins. `desk assess` for a new idea, `desk paper open` to act on an ELIGIBLE decision,
and `desk evening` as the one daily routine command are the three you'll use going forward; `desk
status`, `desk journal show`, and `desk replay` remain available for review and audit at any time.
