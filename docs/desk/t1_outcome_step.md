# T1 outcome step: built on fixtures, not run (18 October 2026)

Built as the pre-registration (docs/desk/t1_market_context_prereg.md) and its addenda define it, in
`desk/t1_outcome/`, and tested on synthetic fixtures only (`tests/test_t1_outcome.py`, 19 tests).
No real outcome was loaded, nothing was run on real data, and there is no entry point that opens a
store: a test checks that the package imports no connection or network code and has no `__main__`.
**Stopped before the development-period run.** The package sits outside `desk/t1/`, so the
feature build's own guard (no outcome name anywhere in `desk/t1/`) still holds.

## What each piece implements

| Piece | Pre-registration text it implements |
| --- | --- |
| `reader.read_adverse20` | "Y=1 if any action-adjusted low in the next 20 GLOBAL market sessions is at or below 80% of decision close. Use the existing adverse20 label definition on a common share basis; all 20 bars required for both outcomes. Structural breaks and missing paths are unavailable, not zero." A test checks every label against the existing definition, `desk/shadow_analysis.py` `tails`, on a fixture with a fall, a split inside the window, a missing bar and a demerger. |
| Firewall and guards in `reader` | "Nothing on or after 2026-09-16 may be evaluated before 2027-06-01; use the shared firewall before loading event outcomes." Every event date goes through `desk.outcome_firewall.evaluate_event`. Added, as you asked: an event on or after the forward start is refused whatever the date today, and a development run refuses any decision date or forward session outside 2019-10-01 to 2024-12-31 and any panel holding a later session, so 2025 is never loaded. There is no hold-out reader. |
| Purge | "Purge development decisions whose 20th forward global session enters 2025; count exclusions." The reader refuses a decision whose 20th session is past 2024-12-31 ("purge the decision first"); the build already labels those sessions `development_purged`. |
| `contrasts.cells` | "For each variant, period, state and quintile report candidates, valid/missing outcomes, date clusters, adverse20 count/rate and risk difference (adverse minus other)." Also "Report risk ratios only as secondary descriptive measures if both rates are nonzero." |
| `contrasts.baseline_weights`, `contrasts.standardized` | "Standardized primary difference = sum of quintile differences weighted by the development baseline candidate shares, fixed for both periods and all draws. If either state lacks valid outcomes in a positive-weight quintile, standardized comparison is unavailable; never renormalize away that quintile." |
| `contrasts.matched_baseline`, `uncertainty.replicate_baseline` | "Compare V1-V3 to V0 on matched available rows and show those rows' baseline rate and coverage." Addendum 1: "A contrast and its matched V0 comparison use the draws of that variant's block length." |
| `contrasts.coverage`, `contrasts.sample_shortfalls` | "coverage at least 80% of eligible stock-days in each evaluated period; at least 100 valid outcomes and 30 distinct dates in EACH state in EACH quintile". |
| `contrasts.spell_count` | Addendum 1: "the result is INCONCLUSIVE unless the adverse state forms at least 5 separate spells among that period's decision dates ... Two runs less than 20 global sessions apart count as one spell ... Sessions whose state is UNKNOWN never separate two runs". Uses the features' `spells`. |
| `uncertainty.period_draws`, `replicate_differences`, `intervals` | "Bootstrap: 2,000 replicates, seed 20261001, resampling complete market-date clusters in MOVING BLOCKS ... Carry every stock-day on each sampled date, including multiplicities and missingness. Reuse draws for all paired contrasts within a period ... Report percentile 95% intervals descriptively and 98.333333% two-sided intervals (Bonferroni family of THREE primary contrasts) ... require at least 1,900 usable draws for a decision." Addendum 1: "V1 and V2 use moving blocks of 60 consecutive global sessions; V3 keeps 20 ... Each block length has its own set of draws from its own generator, seeded 20261001." The draws are the existing `desk/t1/bootstrap.py`. |
| `contrasts.decide` | "Otherwise INCONCLUSIVE, not a passed test or evidence of no association." and "Development success requires standardized risk difference >= 1 percentage point, its family-adjusted interval strictly above zero, and the predicted positive sign in at least four of five quintiles." |

The only change outside the package: the T1 panel now carries the open price (`Panel.open`), which
the existing label checks; the features do not use it.

## Choices the text leaves open (not picked)

Each of the first three is a required argument with no default, so no run can proceed without
your choice; the tests exercise every option.

1. **Coverage numerator** (`coverage(..., numerator=)`): does a stock-day count as covered when its
   variant state is known (`state_known`), or only when its outcome is valid too
   (`state_and_outcome_known`)?
2. **Usable bootstrap draw** (`replicate_differences(..., usable=)`): a replicate is usable when the
   standardised difference can be computed in it (`computable`), or only when every state-quintile
   cell in it also has 100 valid outcomes and 30 distinct dates (`computable_with_sample_minimums`).
3. **Percentile method** (`intervals(..., method=)`): the text says "percentile" intervals but not how
   a percentile falling between two draws is taken. NumPy's methods are offered; the
   pre-registration names "NumPy linear" only for the quintile boundaries.
4. **The bootstrap's dates** (for the run, not yet built): T is every session of the period, or only
   sessions with at least one eligible stock-day. It changes which dates blocks can start on.
5. **The calendar and the late sessions** (docs/desk/t1_coverage_decisions_20261018.md): the outcome
   window is "the next 20 GLOBAL market sessions", so your choices on weekend sessions, 2022-08-08 and
   the five late sessions also define the outcome windows.

Readings I took where the text seemed to settle the point; please confirm or correct:

6. A quintile whose risk difference is exactly zero does not count towards "the predicted positive
   sign in at least four of five quintiles".
7. "Candidate shares" include stock-days whose outcome is missing: the text lists candidates
   separately from valid and missing outcomes.
8. "Matched available rows" for V0 are the rows whose variant state and outcome are both known.
9. Outcome bars are read as stored now (no knowledge cutoff), like the existing label with a far
   cutoff: an outcome is measured after the fact, so a bar that was UNKNOWN as an input (the five
   late sessions) is usable inside an outcome window.
10. A contrast whose standardised difference is unavailable is INCONCLUSIVE.

## Not built (the development run)

Loading the artifact's rows and a panel that ends on 2024-12-31, assembling each variant's rows,
counting purged decisions, writing the tables and the report, and recording input hashes and
commits. That is the development-period run, which waits for your choices above and in the
coverage note.
