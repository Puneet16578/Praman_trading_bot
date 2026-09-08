# Praman — Project Instructions

A forensic classifier for unusual price moves on the NSE. Given a stock that moved sharply,
determine whether the move has an informational basis or carries manipulation-consistent
signatures — and prove the classifier works against SEBI enforcement history, exchange
surveillance flags, and subsequent price behaviour.

This codebase is seeded from InsightForge (a deterministic-first multi-agent investigation
system). Its architectural disciplines carry over unchanged.

## Inherited invariants — non-negotiable

1. **Extend, never fork.** One orchestrator. One checkpoint validator. Never create a parallel
   implementation of an existing class. Enforced by grep, not intention.

2. **Deterministic by default, LLM by permission.** The system must produce complete, grounded
   output with NO language model configured. An LLM may write narrative; a deterministic
   validator re-checks every proposal; any provider failure falls back deterministically.

3. **One authorization enforcement point**, fail-closed. Nothing reaches a tool without passing
   it.

4. **Failure postures are deliberate:** authorization fail-closed, persistence fail-open,
   recovery reads propagate. Do not normalize them.

5. **Banned:** pickle, eval, exec. No TODO/FIXME comments — fix it or document it.

6. **No raw exception text crosses a boundary.**

## Praman-specific invariants — these matter more than any of the above

7. **BITEMPORAL OR NOTHING.** Every record carries an event date (when it happened / the period
   it describes) and a knowledge date (when it became publicly available). Every query filters
   `knowledge_date <= :as_of`. There is no such thing as an unqualified query in this codebase.

   A function that reads data without an as-of parameter is a bug, not a convenience.

8. **Restatements never overwrite.** A revised figure is a NEW ROW with a later knowledge date.
   The original stays. Never UPDATE a fact row.

9. **Labels are knowledge-dated too.** A SEBI order published in 2024 about 2021 activity is
   invisible to a classifier operating as of 2021. Violating this produces a classifier that
   appears to detect manipulation but is reading the future.

10. **Delisted and suspended companies stay in the universe.** A universe of "listed today" has
    deleted every failure, and failures are disproportionately where manipulation ended.

11. **Corporate actions are knowledge-dated.** Adjustment factors were not known before the
    action was announced. An adjusted series built with today's factors is look-ahead bias.

12. **NEVER STATE A CONCLUSION ABOUT MANIPULATION.** Output measured signals and their values.
    "Delivery 11% on 14x average volume; no disclosure in preceding 10 sessions" is a fact.
    "This is a pump" is defamation. ASM/GSM status is reportable because it is a public fact
    from the exchange, not a claim we are making. No buy/sell/hold, no targets, no ratings,
    no ranked "suspicion score" — that is a recommendation with extra steps.

13. **Never report accuracy as a headline metric.** Confirmed manipulation is rare; a classifier
    that always says GROUNDED scores high accuracy and is useless. Report precision, recall,
    precision-at-k, and calibration.

## Evaluation integrity — inherited from InsightForge, still binding

- Expected values are COMPUTED from source data, never authored by a model.
- The benchmark is adversarial toward the system, not supportive of it.
- Never tune the benchmark to raise a score. If a change to scoring is warranted, report the
  before/after impact explicitly.
- Every score is reproducible: committed result file, git sha, fixed inputs.
- Report failures first.

## Data sourcing — decided 2026-09-08

- **NSE market data** (bhavcopy, delivery %, ASM/GSM lists, corporate actions): via `jugaad-data`
  against nseindia.com directly. NSE's own Terms of Use prohibit automated/systematic data
  collection without express written consent; this was a knowing, explicit decision for
  research/personal use, not a silent default. Revisit if this project's scope or audience
  changes (e.g. redistribution, commercial use).
- **Full bhavcopy with delivery %**: `full_bhavcopy_save()` (`sec_bhavdata_full_DDMMYYYY.csv`).
  **Hard project constraint, empirically verified by reading actual file content AND confirming
  the response's own DATE1 column matches the requested date (not just "is this real CSV, not an
  HTML error page" — see P2-001 and P2-003): real, correctly-dated data starts 2019-10-01.**
  Every date checked from 2019-09-27 backward through 2010 returned NSE's HTML error page silently
  saved with a `.csv` extension. **2019-09-30 itself is excluded**: it passes the "is this a real
  CSV" check but the archive silently serves a mislabeled file for that date — its own DATE1
  column reads `27-Jun-2019`, a 95-day anomaly, not the 1-3 day holiday/weekend fallback NSE's
  archive otherwise exhibits (P2-003). 2019-10-01 onward has been confirmed to return content
  whose own DATE1 genuinely matches the requested date (or, for a closed-market date, falls back
  to the nearest prior trading day within a few calendar days — an undocumented but sane archive
  convention ingestion must detect and handle, not assume away).

  **Consequence, stated explicitly so it is visible now and not discovered inside WP-4:** no
  price/volume/delivery data exists in this project for any date before 2019-10-01. A SEBI
  enforcement order concerning activity before that date is unusable as a benchmark label — there
  is no price series to compute signals against for the period it describes. This caps the
  project's confirmed-positive label count to whatever SEBI orders exist for post-2019-10-01
  activity, out of SEBI's full enforcement history. Usable history depth is ~7 years
  (2019-10-01 → today).
- **SEBI enforcement orders**: scraped from `sebi.gov.in/enforcement/orders.html` (public
  regulator records, lowest ToS risk of the four categories). No structured API — listing scrape
  + PDF text extraction. `knowledge_date` = order publication date from the listing page;
  `event_date`/period must be parsed from each order's own text and is flagged `needs_review`
  until a human confirms it — never trusted from regex alone.

## Verification honesty

Never claim a test passed without running it and pasting output. Label anything you could not
verify as DOCUMENTED, NOT VERIFIED. Log every defect you find with an ID, root cause, fix, and
re-verification evidence — including ones you introduced yourself.

## Working procedure

1. Read the relevant source first. Do not act on my description of the code.
2. Write a short plan. **Stop and show me.**
3. Implement only after I approve.
4. Run tests, paste output.
5. Write the phase doc.
6. Propose a commit message; do not commit without asking.

Stop and ask if a task is ambiguous or if what you read contradicts what I described.
