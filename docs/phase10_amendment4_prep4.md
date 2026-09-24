# Amendment 4 Prep, Round 4 — Redefine the Horizon, Pass the Commit Rule

Round 3 measured the missing-outcome rate's decay curve properly and found no plateau within 120
sessions — the own-session outcome definition has no clean timing fix because the problem was
never timing. This round diagnosed the real problem (feature-correlated missingness, confirmed
directly), adopted the alternative round 3 named but deferred (a global 90-session horizon with a
staleness cap), and verified it resolves the TRAIN/HOLD-OUT disparity that started the whole
investigation. **The commit rule passed: Amendment 4 is committed this round.**

## Summary (read this first)

**Step 1 — confirmed the selection problem on the OLD definition, before touching anything.**
`scripts/phase10_amendment4_selection_problem.py`: TRAIN missing-outcome rate (buffer≥30 sessions)
by `cap_band` is a clean monotonic gradient — Micro 2.09%, Small 1.84%, Mid 1.46%, Large 1.36%,
Mega 1.20%. Weaker gradients by `volume_ratio_high` (1.50% vs 1.68%) and `delivery_low` (1.75% vs
1.43%, reported as measured — the direction wasn't what I'd have guessed going in). Trading density
tracks the model's own inputs, so missingness is not random.

**Step 2 — relabeled TRAIN and HOLD-OUT under the new definition.** `scripts/
phase8_robustness_relabel_t0.py`'s `compute_t0_relative` now uses the security's last available
close (EQ, extended through `BE`/`BZ`) on or before the 90th GLOBAL trading session after
event_date, market index evaluated at that same observed date, with a 10-session staleness cap
beyond which the outcome is genuinely missing. Verified against hand-built synthetic cases first
(the index-date convention specifically — confirmed the function uses the index level at the
security's own last observed date, not a later target date that would misattribute market drift
the security never had a chance to participate in). Old-vs-new label agreement: **98.73% overall**,
a clean monotonic gradient by cap_band (Micro 96.60% → Mega 99.79%) — near-total agreement for
liquid names, disagreement concentrated in thin ones, exactly as a correctly-targeted fix should
look.

**Step 3 — missing-outcome rate under the new definition, TRAIN vs. HOLD-OUT.** TRAIN 6.838%,
HOLD-OUT 6.661% — a **0.176pp gap**, against the old definition's 1.67% vs. 10.80% (9.1pp). The
elevated 2026 rate that motivated rounds 1-3 was almost entirely a property of the own-session
definition, not genuine 2026-specific attrition. `possible_delisting_or_suspension`: 709 (original)
→ 495 (`P8-012` series-extension alone) → **368** (`P8-012` + `P8-013` together).

**Commit rule: 0.176pp ≤ 2.0pp → PASS.** Amendment 4 is committed as its own commit this round —
see the final hash below.

**Step 4 — refit under the new label, identical specification.** TRAIN n 56,541 (down from round
2's 59,727 under the own-session label — an accepted trade-off: fewer usable rows for a label whose
missingness isn't correlated with the model's own inputs). Coefficients stable across every round
(Amendment 1 → round 2 → round 4); `isolated`'s coefficient remains not distinguishable from zero
(z=+0.71, even more clearly than round 2's z=+1.12) under an entirely independent label definition;
`disclosure_UNKNOWN_COVERAGE` stays at roughly a third of its pre-correction magnitude. FAIR
baseline: 60.27%.

**Step 5 — Phase 8b re-run under the new label.** No feature's direction reverses. Every CI
excludes 0.5 except `asm_gsm_labelled`, unchanged from round 3's finding under the own-session
label — the qualitative conclusions are robust to which of the two label definitions is used, only
their reliability (missingness pattern) differs.

**Step 6 — amendment updated and committed.** §4 rewritten entirely around the global-horizon
definition. Timing: binding evaluation runs no earlier than 10 sessions past the last window
event's own GLOBAL t+90 (~early June 2027, not round 2/3's ~late June 2027 estimate — the new
timing rule is tighter and tied directly to the staleness cap rather than an intuited buffer).
Threshold: **9.8%** (TRAIN's own fully-aged rate, 6.838%, plus the instructed 3-point margin) —
replacing both the original 5% and every provisional round 2/3 figure, which are now superseded,
not merely refined: those were compensating for a definitional problem with a timing adjustment;
this figure is set from a definition that has already removed most of the problem. Re-pinned to
the commit that includes the relabeling code change (pipeline code DID change this round, unlike
round 3).

Two new defect-register entries added and committed separately: `P8-012` (the `BE`/`BZ`
series-move gap, referenced throughout rounds 2-3 but never actually registered — an oversight,
fixed) and `P8-013` (the own-session label's selection bias, this round's headline finding).

---

## 1. The selection problem, confirmed on the OLD definition

`scripts/phase10_amendment4_selection_problem.py`, TRAIN, buffer≥30 sessions (comfortably past any
residual boundary-proximity effect):

| cap_band | n | missing | rate |
|---|---|---|---|
| Micro | 12,142 | 254 | 2.092% |
| Small | 12,139 | 223 | 1.837% |
| Mid | 12,138 | 177 | 1.458% |
| Large | 12,139 | 165 | 1.359% |
| Mega | 12,136 | 145 | 1.195% |

```
volume_ratio_high (>= own band median):  LOW 1.499% (n=30,346)   HIGH 1.677% (n=30,348)
delivery_low (< 13.3333 pooled):  HIGH/NORMAL 1.747% (n=30,794)   LOW 1.425% (n=29,897)
```

`cap_band`'s gradient is clean and monotonic; the other two are weaker and, for `delivery_low`,
in the opposite direction I'd have naively guessed (LOW delivery associates with LOWER missingness,
not higher) — reported exactly as measured, not adjusted to fit an expected story.

## 2. The new definition, implemented and verified

`scripts/phase8_robustness_relabel_t0.py`'s `compute_t0_relative`, redefined:

```
target_date = 90th GLOBAL trading session after event_date (market_index.csv's own calendar)
last_date   = security's own last available close on/before target_date (EQ + BE/BZ, P8-012)
staleness   = (global sessions between last_date and target_date)
if staleness > 10: outcome = MISSING
else: outcome = signed, market-relative return from close(event_date) to close(last_date),
      index evaluated AT last_date (not target_date)
```

Verified via hand-constructed synthetic cases before trusting it against real data:
- No staleness: symbol trades every session — matches the naive expectation exactly.
- Exact-zero staleness: symbol's own last session lands precisely at target_date — identical
  result to the no-staleness case (confirms the boundary condition is handled correctly).
- Beyond-cap: symbol stops 45 sessions before target — correctly returns MISSING with the reason
  stated (`"stale beyond 10-session cap (45 sessions stale)"`).
- **Within-cap, index-date check**: symbol stops 5 sessions before target while the index rises
  sharply in those 5 sessions. Hand-computed expected result (using the index at the symbol's own
  last observed date): `signed_return_90d = 1.0`. The function returns exactly `1.0` — confirming
  it does NOT use the (materially different, wrong) index level at the later target date, which
  would have produced `0.0` instead.

## 3. Real effect

**Old-vs-new label agreement: 98.73% overall** (61,827 both-computable; 61,039 agree), by
`cap_band`:

| cap_band | n | agree | rate |
|---|---|---|---|
| Micro | 11,254 | 10,871 | 96.597% |
| Small | 12,181 | 11,971 | 98.276% |
| Mid | 12,687 | 12,571 | 99.086% |
| Large | 12,786 | 12,734 | 99.593% |
| Mega | 12,919 | 12,892 | 99.791% |

**Missing-outcome rate, new definition:**

```
TRAIN:    n=60,694  missing=4,150  rate=6.838%
HOLD-OUT: n=6,020   missing=401    rate=6.661%
Gap: 0.176pp  ->  COMMIT RULE PASSES (<= 2.0pp)
```

## 4. Refit and Phase 8b re-run under the new label

See the amendment draft §§3, 6 for the full tables (coefficients with SEs across all three
post-correction rounds; Phase 8b AUCs with Hanley-McNeil CIs). Headline: no qualitative conclusion
changes from round 2/3's own-session-label results — the redefinition changes label RELIABILITY
(whose outcomes are missing and why), not the substantive feature findings.

## 5. Amendment updated and committed

`docs/phase10_preregistration_amendment4.md` (fourth revision): §4 rewritten around the
`P8-013` global-horizon definition; §3 refit updated with round-4 numbers and a 3-round coefficient
comparison; §6 Phase 8b table updated; §8 re-pinned to `c4925b6fb4016a942d49bd8d9b4270a977f3ed97`
(pipeline code changed this round, unlike round 3). **Committed as its own commit, per the
passing commit rule — the rule itself was the review, no further approval step.**

**Final commit hash: `7dd939b15ee930e702890876d05b1be2eff0bc42`** — the commit that adds
`docs/phase10_preregistration_amendment4.md` itself. This round's full commit sequence: the
relabel redefinition and diagnostic scripts (`c4925b6`), the `P8-012`/`P8-013` defect register
entries (`fd36f95`), this document (`d10064a`), and the amendment itself (`7dd939b`).

**Amendment 4 is now committed.** The pinned pipeline commit for the forward evaluation is
`c4925b6fb4016a942d49bd8d9b4270a977f3ed97` (stated in the amendment's own §8) — the last commit
that touched pinned pipeline code; `fd36f95`, `d10064a`, and `7dd939b` are documentation-only and
do not change what that pin points to.
