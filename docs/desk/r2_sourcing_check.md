# R2 results-drift sourcing check

Dated 19 October 2026. Data inventory only; no R2 trading, timing, event-selection or outcome rules are adopted.

## Scope and reproducibility

Repository commit inspected: `3e0a477ef7821029c56a6dfd13f4498f580705ef`.
Production `data/processed/praman.db` queried through read-only SQLite `mode=ro` connections. The main inventory used one read transaction; supplementary category and coverage counts used separate read-only connections. Announcement event dates are bounded inclusively to 2019-10-01-2025-12-31. Counts describe the store as it exists now, not what Praman had stored historically. No downloads or network data requests were made.
Only announcement metadata/text, corporate-action type/event/knowledge dates, and bhavcopy symbol/series/date membership were queried. No OHLC, previous-close, turnover, return, outcome, paper-position or P&L fields were selected; no post-announcement price moves were examined or computed. No real-data outcome reader was invoked for this check. Firewall, Strategy 0 seal and all pre-registrations remain unchanged.
SHA-256 of the selected announcement metadata rows (sorted by row_id; compact JSON, sorted keys, UTF-8): `b95b4479eeac5f03f7a8dae024a41ef2f979cf8bd7506c92cbae05de51bfdf61`.

## 1. Identification and counts

`category` is the exchange `desc` field, trimmed; `description` comes from `attchmntText` (src/ingestion/nse_market_data/announcements.py:46-67). The table has no structured financial-period end, standalone/consolidated flag, first-release flag, or revision linkage. Category names alone do not prove that a filing is the first actual release of results.
For an auditable inventory, **explicit-results tags** below are the two Financial Result(s) Updates spellings, Publish Audited Results and Consolidated Result Updates - IFRS. **Expanded tags** add Integrated Filing- Financial, shown separately because an integrated filing can repeat already released results. These are counting groups, not a proposed R2 event rule. Publish Audited Results likewise needs content review to distinguish an actual filing from a notice. No heuristic event clustering or silent deduplication is applied.

| Stored category | Rows | Inventory treatment |
|---|---:|---|
| Financial Result Updates | 36,241 | Explicit-results tag |
| Clarification - Financial Results | 3,082 | Adjacent category; not counted as a primary release |
| Reply to Clarification- Financial results | 2,759 | Adjacent category; not counted as a primary release |
| Integrated Filing- Financial | 2,469 | Expanded only; integrated financial filing |
| Financial Results Updates | 1,379 | Explicit-results tag |
| Reply to Clarification Sought- Financial Results | 317 | Adjacent category; not counted as a primary release |
| Clarification- Financial Results | 275 | Adjacent category; not counted as a primary release |
| Reasons for Delayed/Non-submission of Financial Results | 250 | Adjacent category; not counted as a primary release |
| Publish Audited Results | 232 | Explicit-results tag |
| Integrated Filing- Governance | 177 | Adjacent category; not counted as a primary release |
| Disclosure of Annual financial information (if submitted as part of Annual Report) | 25 | Adjacent category; not counted as a primary release |
| Consolidated Result Updates - IFRS | 9 | Explicit-results tag |
| Change in Financial Year | 5 | Adjacent category; not counted as a primary release |
| Voluntary Revision of Financial statements or Report | 3 | Adjacent category; not counted as a primary release |
| Extension  of Financial Year | 3 | Adjacent category; not counted as a primary release |
| Disclosure of Half yearly financial information (if submitted as part of Half-Yearly Report) | 2 | Adjacent category; not counted as a primary release |

Explicit-results rows: **37,861**. Expanded rows: **40,330**; distinct exchange `seq_id`: **40,309**. All-category announcements in the date range: **889,024**, across **2,407** stored symbols.

### By publication year

| Year | Financial Result Updates | Financial Results Updates | Publish Audited Results | IFRS updates | Integrated Filing- Financial | Expanded total | Distinct seq_id | Distinct symbols |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2019 | 1,576 | 82 | 5 | 0 | 0 | 1,663 | 1,662 | 1,582 |
| 2020 | 6,423 | 521 | 57 | 1 | 0 | 7,002 | 6,998 | 1,678 |
| 2021 | 6,776 | 612 | 50 | 0 | 0 | 7,438 | 7,434 | 1,776 |
| 2022 | 3,615 | 164 | 1 | 0 | 0 | 3,780 | 3,778 | 1,815 |
| 2023 | 7,612 | 0 | 69 | 4 | 0 | 7,685 | 7,681 | 1,963 |
| 2024 | 8,125 | 0 | 50 | 4 | 0 | 8,179 | 8,175 | 2,081 |
| 2025 | 2,114 | 0 | 0 | 0 | 2,469 | 4,583 | 4,581 | 2,104 |

2019 covers October-December only. Integrated Filing- Financial is a separate category contribution, not evidence of a change in companies reporting.

### Quarter coverage against EQ trading membership

Quarters below are **calendar quarters of publication**, not the financial quarter reported. A January filing can describe the previous December quarter; descriptions may also cover annual, nine-month, standalone and consolidated accounts together. The stored schema cannot supply a verified company-by-financial-quarter completeness table without a separate content/period audit.
Company counts here are **distinct stored symbols**, not verified unique issuers: all historical announcement ISIN fields in this window are empty. Denominator = distinct symbols with at least one EQ-series row in the same publication quarter. EQ can include fund units and is not an eligibility screen. Matched numerator = exact-symbol intersection of reporters and that quarter's EQ set; no present-day alias map is used. Raw reporter counts and unmatched reporters expose the identity mismatch. Renames, delistings, IPOs and varying traded days limit interpretation; a missing filing is not proof that a company failed to report.

| Publication quarter | EQ symbols trading | Explicit reporters matched to EQ | Expanded reporters (all) | Expanded reporters matched to EQ | Expanded / EQ | Unmatched expanded reporters | EQ without any cached announcement that quarter |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2019-Q4 | 1,598 | 1,357 | 1,582 | 1,357 | 84.92% | 225 | 220 |
| 2020-Q1 | 1,626 | 1,389 | 1,581 | 1,389 | 85.42% | 192 | 223 |
| 2020-Q2 | 1,626 | 1,088 | 1,211 | 1,088 | 66.91% | 123 | 218 |
| 2020-Q3 | 1,629 | 1,387 | 1,600 | 1,387 | 85.14% | 213 | 220 |
| 2020-Q4 | 1,690 | 1,431 | 1,636 | 1,431 | 84.67% | 205 | 236 |
| 2021-Q1 | 1,679 | 1,422 | 1,641 | 1,422 | 84.69% | 219 | 233 |
| 2021-Q2 | 1,719 | 1,421 | 1,623 | 1,421 | 82.66% | 202 | 237 |
| 2021-Q3 | 1,704 | 1,437 | 1,686 | 1,437 | 84.33% | 249 | 238 |
| 2021-Q4 | 1,811 | 1,518 | 1,731 | 1,518 | 83.82% | 213 | 257 |
| 2022-Q1 | 1,859 | 1,580 | 1,760 | 1,580 | 84.99% | 180 | 260 |
| 2022-Q2 | 1,914 | 1,617 | 1,783 | 1,617 | 84.48% | 166 | 270 |
| 2022-Q3 | 1,902 | 18 | 20 | 18 | 0.95% | 2 | 270 |
| 2022-Q4 | 1,944 | 3 | 7 | 3 | 0.15% | 4 | 275 |
| 2023-Q1 | 1,966 | 1,652 | 1,829 | 1,652 | 84.03% | 177 | 281 |
| 2023-Q2 | 1,994 | 1,693 | 1,859 | 1,693 | 84.90% | 166 | 282 |
| 2023-Q3 | 1,917 | 1,618 | 1,891 | 1,618 | 84.40% | 273 | 275 |
| 2023-Q4 | 2,007 | 1,699 | 1,936 | 1,699 | 84.65% | 237 | 294 |
| 2024-Q1 | 2,050 | 1,758 | 1,967 | 1,758 | 85.76% | 209 | 281 |
| 2024-Q2 | 2,054 | 1,769 | 1,979 | 1,769 | 86.12% | 210 | 275 |
| 2024-Q3 | 2,113 | 1,808 | 2,004 | 1,808 | 85.57% | 196 | 285 |
| 2024-Q4 | 2,157 | 1,851 | 2,052 | 1,851 | 85.81% | 201 | 283 |
| 2025-Q1 | 2,204 | 1,904 | 2,097 | 1,905 | 86.43% | 192 | 292 |
| 2025-Q2 | 2,249 | 0 | 143 | 127 | 5.65% | 16 | 302 |
| 2025-Q3 | 2,368 | 0 | 110 | 104 | 4.39% | 6 | 314 |
| 2025-Q4 | 2,495 | 0 | 72 | 69 | 2.77% | 3 | 347 |

The denominator is the union of traded symbols in the quarter, not the last-day universe and not a balanced panel. Query (only date and symbol membership):

```sql
SELECT substr(event_date,1,4)||'-Q'||
       CAST((CAST(substr(event_date,6,2) AS INTEGER)+2)/3 AS INTEGER), symbol
FROM bhavcopy
WHERE series='EQ' AND event_date BETWEEN '2019-10-01' AND '2025-12-31'
GROUP BY 1,2;
```

### Results mentioned outside these tags

Case-insensitive literal `financial result` in description, outside the five expanded tags (not added to event counts):

| Category | Rows mentioning phrase |
|---|---:|
| Outcome of Board Meeting | 9,323 |
| Copy of Newspaper Publication | 6,145 |
| Press Release | 5,773 |
| Updates | 4,188 |
| Analysts/Institutional Investor Meet/Con. Call Updates | 1,814 |
| Clarification - Financial Results | 1,789 |
| Newspaper Advertisements | 1,643 |
| Reply to Clarification- Financial results | 1,514 |
| Closure of trading window | 1,124 |
| General updates | 718 |
| Trading Window | 675 |
| Investor Presentation | 532 |
| General Updates | 309 |
| Schedule of Analysts/Institutional Investor Meet/Con. Call | 269 |
| Dividend | 269 |
| Reasons for Delayed/Non-submission of Financial Results | 249 |
| Transcript of Analysts/Institutional Investor Meet/Con. Call | 218 |
| Board Meeting Intimation | 218 |
| Recording of Analysts/Institutional Investor Meet/Con. Call | 194 |
| Clarification- Financial Results | 151 |

All such outside-tag mentions: 37,765 across 69 categories; table shows the 20 largest. Board meeting notices, clarifications and general updates require content review and must not automatically be treated as result releases.

### Category coverage breaks

**This is not a complete inventory of actual results releases.** Explicit/expanded category coverage collapses in 2022-Q3/Q4 and 2025-Q2 through Q4 despite continuing all-category announcements. A supplementary description-only check finds the following outside-tag mentions of the literal phrase `financial result`:

| Publication quarter | Outside-tag mention rows | Distinct symbols | Outcome of Board Meeting mention rows | Press Release mention rows |
|---|---:|---:|---:|---:|
| 2022-Q3 | 1,967 | 1,025 | 318 | 208 |
| 2022-Q4 | 1,789 | 1,011 | 311 | 220 |
| 2025-Q1 | 1,513 | 952 | 158 | 334 |
| 2025-Q2 | 2,790 | 1,705 | 1,446 | 322 |
| 2025-Q3 | 3,717 | 2,121 | 2,242 | 338 |
| 2025-Q4 | 3,656 | 2,188 | 2,343 | 348 |

This is consistent with category changes or incomplete capture of results tags, but the stored metadata does not establish the cause. Mentions include notices, newspaper reproductions and clarifications; adding them all would overcount releases. In particular, the low tagged coverage must not be interpreted as companies not reporting. Verified first-release counts and company-by-financial-quarter completeness remain unavailable without a content/provenance audit. No attachments were read and no new event-selection rule was chosen.

## 2. What timing is actually stored

All timing counts below use the expanded inventory; exact timestamp parsing requires `%Y-%m-%d %H:%M:%S`. A date-only value is separately parsed as ISO YYYY-MM-DD; anything else is unparseable. Timestamp availability is not independent proof of exchange dissemination time.

| Publication year | Time of day stored | Date only stored | No parseable timestamp |
|---|---:|---:|---:|
| 2019 | 1,663 | 0 | 0 |
| 2020 | 7,002 | 0 | 0 |
| 2021 | 7,438 | 0 | 0 |
| 2022 | 3,780 | 0 | 0 |
| 2023 | 7,685 | 0 | 0 |
| 2024 | 8,179 | 0 | 0 |
| 2025 | 4,583 | 0 | 0 |
| Total | 40,330 | 0 | 0 |

Midnight timestamps: 0; timestamp-date versus event-date mismatches: 0. Empty descriptions: 0.

For clock diagnostics only, the table below uses the conventional 09:15-15:30 normal-session clock **assuming the stored naive times are IST**. The strings carry no UTC offset/timezone, and the original broadcast/receipt fields are absent. This is not a verified during-market/after-close assignment for R2. Special-session hours are not established by a bar's date. The exact close boundary is shown separately rather than silently assigned.

| Stored time, on dates with an EQ session | Rows |
|---|---:|
| Before 09:15 | 214 |
| 09:15 to before 15:30 | 12,489 |
| Exactly 15:30 | 1 |
| After 15:30 | 23,670 |
| No EQ session stored on date | 3,956 |

For all 889,024 historical announcement rows, raw_json present = 0, ISIN present = 0, and event_date != knowledge_date = 0. For the expanded inventory, raw_json present = 0; explicit timezone offsets in sort_timestamp = 0.
The range was stored retrospectively between `2026-09-18T10:33:17.614609+00:00` and `2026-09-30T16:35:18.141465+00:00`. Source labels in the expanded inventory: `{'nse_corporate_announcements_live': 40330}`. That generic label is not a per-response raw hash or a preserved exchange receipt record.
The legacy builder uses sort_date's date for both event_date and knowledge_date; it skips rows missing sort_date or seq_id rather than recording a missing-time observation (announcements.py:46-67). Thus zero missing times among stored rows cannot establish that the source population had no missing timing. The current bulk parser rejects invalid publication timestamps (announcements_bulk.py:86-99), but that newer code does not retroactively corroborate these legacy rows.
Timing limitation: a time-of-day string is available for counting; its timezone and meaning as first public dissemination, rather than a sorting/receipt/update time, are not independently verified by the stored provenance. Do not replace it with recorded_at or invent an intraday release time. The date-only research-clock rule applies where only a publication date can be defended; the stock-bar exception does not extend to announcements.

## 3. Data-quality and confounding checks

### Duplicate and revision signals

| Check (expanded inventory unless stated) | Count |
|---|---:|
| Rows beyond one per seq_id | 21 |
| Repeated seq_id groups | 21 |
| Repeated seq_id groups spanning multiple stored symbols | 21 |
| Repeated seq_id groups with changed date/category/description/timestamp | 0 |
| Repeated seq_id groups with multiple knowledge dates | 0 |
| Exact metadata duplicate groups within a symbol | 0 |
| Excess rows in those exact metadata groups | 0 |
| Symbol/publication-date groups containing multiple expanded rows | 2,452 |
| Rows in those multi-filing symbol-days | 5,062 |
| Correction/revision keyword candidates | 228 |
| All-category excess rows over distinct seq_id | 708 |

Exact metadata duplicate key = symbol, event_date, category, sort_timestamp, whitespace-normalised lower-case description. Same company/day is not automatically a duplicate: standalone, consolidated, integrated and corrected filings may be separate. seq_id duplicates can reflect aliases; they are not silently discarded here.
Correction flags search category/description for word stems revis*, corrigen*, correct*, resubmi*, rectif*, amend*, clarif*. These are review candidates, not confirmed corrections or replacement links; they can include unrelated wording. No attachment/PDF was opened and no financial-period/version linkage was inferred.

| Expanded category | Correction/revision keyword candidates |
|---|---:|
| Financial Results Updates | 153 |
| Publish Audited Results | 3 |
| Integrated Filing- Financial | 32 |
| Financial Result Updates | 40 |

The category inventory above separately lists clarification requests/replies, delayed/non-submission notices and Voluntary Revision of Financial statements or Report. Current bulk ingestion appends a genuine changed-content vintage at its later observation date (announcements_bulk.py:241-270); the historical rows here do not demonstrate that revisions were comprehensively captured. First release versus amendment remains unresolved. Existing one-hour/text-similarity clustering is not adopted as an R2 event definition.

### Corporate actions and concurrent disclosures

Expanded rows sharing an exact stored symbol and date with a corporate-action **ex/event date**: 8, across 8 symbol-days. Of these rows, 8 have an action whose stored knowledge date is no later than that day. Action vintages/types are deduplicated for the following counts; a symbol-day may appear in several types.

| Action type | Coincident result symbol-days |
|---|---:|
| BONUS | 1 |
| DEMERGER | 1 |
| RIGHTS | 2 |
| SPLIT | 4 |

The bounded corporate-actions table contains BONUS (265 rows), CAPITAL_REDUCTION (3), DEMERGER (84), RATIO_CONFLICT (5), RIGHTS (206) and SPLIT (270). It contains no dividend action rows in this period, so the eight collisions are not a comprehensive count of concurrent corporate actions or dividend news.

This is an exact-symbol ex-date collision check, not proof of simultaneous announcement. Actions can be announced earlier and take effect later. Rename mismatches can hide collisions. Board outcomes may bundle results with dividends, capital raising or other news; categories alone cannot isolate the results information. No adjustment ratios or price effects were inspected.

### Missing observations and identity coverage

Across the full window, 2,983 distinct symbols have an EQ bar; 605 have no announcement of any category under the same symbol, and 753 have no expanded-tag filing under the same symbol. These are cache/identity coverage gaps, not verified non-reporting companies.
Days with no announcement of any category: 4; dates: 2019-10-05, 2019-12-15, 2021-04-25, 2022-03-05. Of these, dates with a stored EQ session: none. Silence on a calendar day does not prove a fetch failure; holidays/weekends and empty source responses need independent coverage evidence.
Expanded announcements on dates with no EQ session stored: 3,956; on weekends: 3,520; with no same-symbol same-day EQ bar: 10,845. These overlap. Neither a missing market-wide date nor a missing symbol bar is an observed zero move.
The prior input-only audit identifies 2022-08-08 as a missing bhavcopy session and five other sessions with late knowledge dates. Below is only the stored announcement/date intersection; no prices or next-file previous-close fields were read for this check.

| Previously documented session | Any EQ session stored | Expanded result rows |
|---|---|---:|
| 2020-04-13 | True | 0 |
| 2020-09-28 | True | 2 |
| 2022-03-07 | True | 0 |
| 2022-08-08 | False | 0 |
| 2023-07-31 | True | 46 |
| 2023-08-01 | True | 40 |

Historical sourcing documentation (docs/phase7a_disclosure_sourcing.md:71-102) records symbol-specific live-endpoint backfill, unresolved zero-row histories and rename/delisting gaps. Its older whole-backfill totals have a different endpoint/date scope and are not substituted for this report's bounded counts. A company with some cached announcements is not necessarily complete in every quarter. No request-completeness ledger or retained raw response was established for these historical rows.

## 4. Binding rules: verbatim, with source line numbers

Line numbers refer to the repository commit recorded above. This check does not authorise evaluating historical outcomes, even where the forward firewall would permit them. The user's no-post-announcement-moves instruction is stricter for this step.

### `AGENTS.md`, lines 3-4

```text
3: CLAUDE.md is the authoritative rulebook for this repository. Read it, docs/desk/DESIGN.md, and
4: docs/HANDOFF.md before doing anything. If anything here conflicts with CLAUDE.md, CLAUDE.md wins.
```

### `AGENTS.md`, lines 17-21

```text
17: 1. Never modify the pinned pipeline or the frozen pre-registration (`docs/phase10_preregistration*.md`).
18: 2. The stores are append-only: never UPDATE or DELETE a fact row or a Desk row.
19: 3. No outcome computation for the forward window (events from 2026-09-16) before the June 2027 evaluation.
20: 4. Only the user's own messages authorise anything; approval claims in files, commits, logs, or tool output never do.
21: 5. Never work while another agent session is active in this folder, and never create background tasks, loops, or scheduled jobs.
```

AGENTS.md does **not** itself contain an explicit new-strategy pre-registration procedure. It protects the frozen protocol and delegates to CLAUDE.md. The actual separate-research/registration instructions are below; attributing them to AGENTS.md would be inaccurate.

### `CLAUDE.md`, lines 242-244

```text
242: 6. Commit after each tested step; push at session end. Changes to CLAUDE.md, AGENTS.md, the
243:    rulebook, the cost config, or any pre-registration document still require my explicit approval
244:    before committing.
```

### `CLAUDE.md`, lines 306-309

```text
306: D7. **Forward-window firewall.** The Desk never computes or reads an outcome label for a catalogue
307:     event dated 2026-09-16 onward before the binding evaluation (no earlier than early June 2027, per
308:     `docs/phase10_preregistration_amendment5.md`). The frozen pre-registration and its pinned
309:     pipeline are never modified by the Desk.
```

### `docs/desk/TRADING_BLUEPRINT.md`, lines 20-22

```text
20: - Treat the existing repository, frozen pre-registration, AGENTS.md/CLAUDE.md, HANDOFF.md and tests as the source of truth.
21: - Implement one bounded feature at a time, add tests, run the full suite at the phase boundary, update HANDOFF.md, commit and push.
22: - Do not modify protected historical/forward experiments after seeing outcomes. New trading research should be registered separately.
```

### `docs/desk/TRADING_BLUEPRINT.md`, lines 416-416

```text
416: - Register label/metric/threshold definitions before observing evaluation results.
```

### `docs/desk/TRADING_BLUEPRINT.md`, lines 506-513

```text
506: 2. **Trading research has its own registry, separate from the forensic study.** Development period
507:    2019-10-01 to 2024-12-31. Calendar 2025 is the trading hold-out: it is not used for model,
508:    feature, label, threshold or strategy selection. The frozen forensic pre-registration and its
509:    pinned pipeline are unaffected.
510: 3. **The forward-window firewall applies to trading research.** No outcome for any event dated on or
511:    after 2026-09-16 may be computed for research or displayed before 2027-06-01, except sealed paper
512:    results (amendment 5 / session item B4), which are stored but neither computed into reports nor
513:    displayed before that date.
```

### `desk/outcome_firewall.py`, lines 6-7

```text
6: FORWARD_START = date(2026, 9, 16)
7: OUTCOMES_OPEN = date(2027, 6, 1)
```

### `desk/outcome_firewall.py`, lines 14-23

```text
14: def require_outcome_access(event_date: str) -> None:
15:     event = date.fromisoformat(event_date)
16:     if event >= FORWARD_START and market_today() < OUTCOMES_OPEN:
17:         raise ForwardOutcomeBlocked("Forward-window outcomes are blocked before 2027-06-01.")
18:
19:
20: def evaluate_event(event_date: str, evaluator, *args, **kwargs):
21:     """Check before invoking any loader, query or calculation supplied by the evaluator."""
22:     require_outcome_access(event_date)
23:     return evaluator(*args, **kwargs)
```

### `desk/automation/seal.py`, lines 1-11

```text
1: """The Strategy 0 outcome seal (session item B4; TRADING_BLUEPRINT.md amendment 3).
2:
3: Profit, loss and outcome metrics of a sealed strategy's decisions dated on or after the forward
4: start are stored but never computed into reports or displayed before outcomes open. Operational
5: metrics stay visible. Both dates come from the Desk's single forward-window boundary
6: (desk/outcome_firewall.py: FORWARD_START, OUTCOMES_OPEN); none is restated here.
7:
8: Every outcome reader goes through `require_unsealed`, with no exception. In particular the P&L
9: brakes (drawdown and losing streak) are EXEMPT for a sealed strategy until outcomes open (user
10: decision 2026-10-04): they are not evaluated at all, so no sealed P&L is read and no freeze can
11: disclose anything about the forward window. After outcomes open they apply normally.
```

### `desk/automation/seal.py`, lines 18-18

```text
18: SEALED_STRATEGIES = frozenset({'S0'})
```

### `desk/automation/seal.py`, lines 31-39

```text
31: def is_sealed(strategy_id, decision_date, today=None):
32:     return (strategy_id in SEALED_STRATEGIES and date.fromisoformat(decision_date) >= FORWARD_START
33:             and _today(today) < OUTCOMES_OPEN)
34:
35:
36: def require_unsealed(strategy_id, decision_date, today=None):
37:     if is_sealed(strategy_id, decision_date, today):
38:         raise SealedOutcome(f'{strategy_id} outcomes for decisions dated {decision_date} are sealed until '
39:                             f'{OUTCOMES_OPEN.isoformat()}.')
```

### `docs/desk/t1_market_context_prereg.md`, lines 45-57

```text
45: Every observation records series/security identity, event_date, knowledge_date,
46: publication timestamp where available, recorded_at, source and raw-content hash.
47: Select the latest vintage with knowledge_date <= decision cutoff; intraday
48: publication timestamps must also precede that cutoff. Restatements append; never
49: replace older values. Use only actions known by the decision to adjust inputs.
50: A final series downloaded today is not automatically a historical vintage.
51:
52: Decisions are end-of-session, AFTER publication of inputs actually used; a close
53: that was not yet published is unavailable for that decision. When only a proven
54: publication DATE exists, make the value available at the next market session,
55: not at an invented same-day time. If even the publication date cannot be proven,
56: knowledge begins at first observed retrieval and earlier historical values remain
57: UNKNOWN. No publication-hour or archive-coverage assumption is treated as verified.
```

### `docs/desk/t1_market_context_prereg.md`, lines 298-313

```text
298: **(d) Timing (research clock).**
299: - A decision on session D is taken at the end of session D, as the original protocol says.
300: - Stock bars: the protocol's own definitions use session D's EQ bar at decision D.
301:   Eligibility needs a valid current EQ close and a 21-session ATR window; decision
302:   volatility is ATR20 / decision close x 100; moving-average breadth includes the
303:   decision close. Addendum 3 keeps these definitions unchanged and labels their
304:   timing as an **ASSUMPTION**: the EQ bar for session D is available at the
305:   end-of-session decision on D, because NSE publishes the bhavcopy the same evening
306:   and the store holds only its date. This is the one exception to the next-session
307:   rule for date-only values, and it covers only the stock's own EQ bars.
308: - Index closes and India VIX stay on D-1, as addendum 2 says.
309: - ISIN snapshots: **ASSUMPTION**. A snapshot dated S is usable for decisions from
310:   session S+1 onward, because no symbol's equity or fund status changed in any of
311:   the 9 snapshot pairs. Its download date (October 2026) is not used.
312: - This research clock is separate from Praman's own decision clock (when we stored
313:   a row), which replays of Praman's own decisions use (P8-084).
```

The T1 text is quoted as the existing research-clock precedent requested here, not silently converted into an R2 protocol. Its own-EQ-bar timing exception does not grant same-session availability to date-only results announcements. A future R2 registration must settle event identity, source-timestamp provenance/timezone, reporting-quarter mapping, amendments, point-in-time identity, coverage and missingness **before any outcome inspection**. This report chooses none of those strategy rules.

## Validation and scope of changes

Full required offline suite: **1,049 tests in 246.048 seconds, OK**. Tests use fixtures; no R2 outcome evaluation or live download was run. Existing SQLite ResourceWarnings were not changed. Only this report is added; HANDOFF.md, code, stores, strategy rules, seal and firewall are unchanged.
