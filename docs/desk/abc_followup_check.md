# A/B/C follow-up: input counts and sourcing

19 October 2026. Personal research only. These are counting conventions, not strategy rules. No outcome, post-event price, or forward-window price was read. The store was opened read-only. No download, backfill, rule/configuration change, firewall change, or Strategy 0 change was made.

The completed repaired market and peer tables are in [the sourcing check, section 8](abc_sourcing_check.md#8-event-day-market-and-peer-moves-inputs-only), committed in `b041714`. This report uses that fund-exclusion map, consecutive-session return convention, market-adjusted correlations, 250-session history and 200-pair minimum. It does not revise item 2.

## 3. B: successive exclusions from catalogue down events

The starting population is the negative `return_1d` label in the stored catalogue, not a newly recomputed direction. The catalogue has no separately named direction column. The tables count events; distinct symbols are reported as counts only. A remaining event is not proof that no explanation exists.

The main cut-off is 09:00 IST on the next observed EQ session. The two other cut-offs are exactly 18:00:00 and 23:59:00 IST on D. Stored announcement times are assumed IST, as in the R2 check; their first-publication semantics remain unverified. An announcement after the applicable cut-off cannot remove an event. D's prices are the latest prices used at all three cut-offs. The observed EQ calendar includes special/weekend sessions and inherits missing-day limitations. Reading calendar dates to locate the next session does not read that session's prices.

Date-only evidence is handled more narrowly than timestamped evidence. T1 addendum 3(d), lines 298–313, preserves next-session availability except for the stock's own EQ bar. Because it supplies no pre-open availability time, this report uses the next EQ session's 09:15 open for date-only evidence. Thus a date-only item published on D is not assumed known at 09:00 next session. The normal-session 09:15/15:30 clock is a convention; special-session hours have not been reconstructed. This is the research clock, not the P8-084 stored-row decision clock. The current identity map is inherited from item 2 and is not a historically proven identity roster.

The nine steps are: (1) market mean below -2%; (2) draft Material filing; (3) draft Unclear filing; (4) linked SEBI order; (5) no filing in the preceding 90 calendar days, excluding D; (6) the inclusive 13 July–16 December 2022 route gap; (7) parsed dividend record/book-closure date, or the preceding EQ session; (8) peer share at least half, or UNKNOWN peers; (9) G3 structure failure or G5 liquidity failure. Filing windows start at midnight on the fifth prior EQ session. The 1- and 10-session versions change only steps 2–3.

G3 uses the existing 60-own-session structural-break definition and shared action types. G5 uses the existing screening plan (decision close, two-ATR stop), whole-share position sizing with the active costs/risk caps and an empty hypothetical portfolio, and the existing 60-observation turnover/liquidity check. No assessment or decision is persisted. The standard order is therefore a risk-sized order, not a fixed rupee amount. UNKNOWN G3/G5 is counted separately and is not silently converted to FAIL or PASS.

Step 8 retains the separately counted unstable-ratio cases from item 2: when the absolute market-adjusted move is below 1%, the share is not evaluated. These are not reassigned to UNKNOWN peers. Counts left with an unstable ratio or unknown liquidity are disclosed below; they cannot support a claim of a fully screened unexplained pool.

### 3a. Sequential funnel, cut-off 09:00 IST next EQ session, 5-session filing window

Each step removes events still present after the steps above it. "Removes on its own" applies the step alone to all
of that year's down events. Dates and symbols are distinct counts among the events left.

**2020**

| Step | Removed | Left | Dates left | Symbols left | Removes on its own |
| --- | --- | --- | --- | --- | --- |
| Down events (start) | — | 2,767 | 193 | 1,131 | — |
| 1. Down-market day (market mean below -2%) | 1,841 | 926 | 176 | 647 | 1,841 |
| 2. Material filing in window | 322 | 604 | 153 | 461 | 495 |
| 3. Unclear filing in window | 234 | 370 | 125 | 296 | 1,152 |
| 4. Linked SEBI order | 0 | 370 | 125 | 296 | 0 |
| 5. No filing in the 90 days before D | 85 | 285 | 104 | 238 | 233 |
| 6. 2022 results-route gap | 0 | 285 | 104 | 238 | 0 |
| 7. Likely ex-dividend day | 3 | 282 | 104 | 236 | 5 |
| 8. Peers share at least half, or peers UNKNOWN | 230 | 52 | 38 | 50 | 2,215 |
| 9. G3 structure window or G5 failure | 24 | 28 | 23 | 28 | 741 |

**2021**

| Step | Removed | Left | Dates left | Symbols left | Removes on its own |
| --- | --- | --- | --- | --- | --- |
| Down events (start) | — | 1,272 | 210 | 820 | — |
| 1. Down-market day (market mean below -2%) | 296 | 976 | 198 | 667 | 296 |
| 2. Material filing in window | 454 | 522 | 177 | 411 | 501 |
| 3. Unclear filing in window | 191 | 331 | 141 | 272 | 737 |
| 4. Linked SEBI order | 0 | 331 | 141 | 272 | 0 |
| 5. No filing in the 90 days before D | 66 | 265 | 126 | 223 | 92 |
| 6. 2022 results-route gap | 0 | 265 | 126 | 223 | 0 |
| 7. Likely ex-dividend day | 4 | 261 | 123 | 220 | 14 |
| 8. Peers share at least half, or peers UNKNOWN | 54 | 207 | 108 | 174 | 217 |
| 9. G3 structure window or G5 failure | 35 | 172 | 96 | 146 | 191 |

**2022**

| Step | Removed | Left | Dates left | Symbols left | Removes on its own |
| --- | --- | --- | --- | --- | --- |
| Down events (start) | — | 2,249 | 220 | 1,203 | — |
| 1. Down-market day (market mean below -2%) | 1,103 | 1,146 | 202 | 781 | 1,103 |
| 2. Material filing in window | 288 | 858 | 190 | 644 | 448 |
| 3. Unclear filing in window | 501 | 357 | 148 | 296 | 1,166 |
| 4. Linked SEBI order | 0 | 357 | 148 | 296 | 0 |
| 5. No filing in the 90 days before D | 67 | 290 | 132 | 248 | 147 |
| 6. 2022 results-route gap | 156 | 134 | 65 | 125 | 785 |
| 7. Likely ex-dividend day | 0 | 134 | 65 | 125 | 18 |
| 8. Peers share at least half, or peers UNKNOWN | 41 | 93 | 56 | 85 | 533 |
| 9. G3 structure window or G5 failure | 19 | 74 | 45 | 67 | 401 |

**2023**

| Step | Removed | Left | Dates left | Symbols left | Removes on its own |
| --- | --- | --- | --- | --- | --- |
| Down events (start) | — | 2,616 | 228 | 1,373 | — |
| 1. Down-market day (market mean below -2%) | 776 | 1,840 | 222 | 1,129 | 776 |
| 2. Material filing in window | 853 | 987 | 215 | 724 | 912 |
| 3. Unclear filing in window | 385 | 602 | 181 | 478 | 1,417 |
| 4. Linked SEBI order | 0 | 602 | 181 | 478 | 0 |
| 5. No filing in the 90 days before D | 103 | 499 | 170 | 416 | 142 |
| 6. 2022 results-route gap | 0 | 499 | 170 | 416 | 0 |
| 7. Likely ex-dividend day | 7 | 492 | 170 | 414 | 20 |
| 8. Peers share at least half, or peers UNKNOWN | 82 | 410 | 158 | 349 | 388 |
| 9. G3 structure window or G5 failure | 115 | 295 | 136 | 255 | 446 |

**2024**

| Step | Removed | Left | Dates left | Symbols left | Removes on its own |
| --- | --- | --- | --- | --- | --- |
| Down events (start) | — | 2,456 | 228 | 1,313 | — |
| 1. Down-market day (market mean below -2%) | 1,077 | 1,379 | 214 | 922 | 1,077 |
| 2. Material filing in window | 680 | 699 | 192 | 553 | 996 |
| 3. Unclear filing in window | 301 | 398 | 154 | 341 | 1,542 |
| 4. Linked SEBI order | 0 | 398 | 154 | 341 | 0 |
| 5. No filing in the 90 days before D | 43 | 355 | 142 | 316 | 72 |
| 6. 2022 results-route gap | 0 | 355 | 142 | 316 | 0 |
| 7. Likely ex-dividend day | 6 | 349 | 139 | 312 | 17 |
| 8. Peers share at least half, or peers UNKNOWN | 158 | 191 | 113 | 171 | 694 |
| 9. G3 structure window or G5 failure | 13 | 178 | 106 | 162 | 144 |

**2025**

| Step | Removed | Left | Dates left | Symbols left | Removes on its own |
| --- | --- | --- | --- | --- | --- |
| Down events (start) | — | 2,635 | 235 | 1,438 | — |
| 1. Down-market day (market mean below -2%) | 670 | 1,965 | 218 | 1,233 | 670 |
| 2. Material filing in window | 500 | 1,465 | 205 | 1,017 | 724 |
| 3. Unclear filing in window | 903 | 562 | 164 | 450 | 1,711 |
| 4. Linked SEBI order | 0 | 562 | 164 | 450 | 0 |
| 5. No filing in the 90 days before D | 28 | 534 | 162 | 431 | 38 |
| 6. 2022 results-route gap | 0 | 534 | 162 | 431 | 0 |
| 7. Likely ex-dividend day | 8 | 526 | 159 | 425 | 38 |
| 8. Peers share at least half, or peers UNKNOWN | 151 | 375 | 140 | 309 | 540 |
| 9. G3 structure window or G5 failure | 107 | 268 | 121 | 232 | 459 |

### 3b. When the step-2 material filings appeared (all down events, 09:00 cut-off, 5-session window)

Events with at least one material filing in each bin (filings in brackets). Bins: D's close (15:30) to 18:00;
after 18:00 to midnight; the next EQ session's morning up to 09:00; and the closure bridge (calendar days between
D and the next session, i.e. weekends and holidays). Earlier filings in the window are not in these bins.

| Year | Close to 18:00 | After 18:00 | Next morning to 09:00 | Weekend/holiday bridge |
| --- | --- | --- | --- | --- |
| 2020 | 20 (24) | 15 (15) | 3 (3) | 0 (0) |
| 2021 | 13 (13) | 16 (21) | 0 (0) | 2 (2) |
| 2022 | 12 (16) | 23 (34) | 1 (1) | 2 (2) |
| 2023 | 22 (29) | 13 (15) | 2 (2) | 1 (2) |
| 2024 | 26 (29) | 22 (26) | 0 (0) | 3 (3) |
| 2025 | 46 (53) | 39 (45) | 0 (0) | 8 (12) |

### 3c. Unclear filings in the step-3 window, by kind (all down events)

Events with at least one such filing (filings in brackets); one event can appear in several columns. "News and
rumour" is News Verification (both stored spellings), News Clarification and Rumour Verification - Regulation
30(11). Shown separately: the generic Clarification and Reply to Clarification Sought, and the four "Financial
Results" clarification variants.

| Year | News and rumour | Clarification (generic) | Clarification (financial results) | Price movement / Spurt in Volume | Outcome of Board Meeting | SEBI Takeover disclosure |
| --- | --- | --- | --- | --- | --- | --- |
| 2020 | 15 (29) | 37 (59) | 11 (11) | 57 (101) | 224 (232) | 53 (104) |
| 2021 | 10 (13) | 22 (34) | 8 (9) | 41 (72) | 272 (294) | 65 (106) |
| 2022 | 14 (25) | 23 (27) | 15 (19) | 55 (95) | 520 (546) | 32 (70) |
| 2023 | 26 (43) | 8 (10) | 25 (33) | 60 (105) | 528 (584) | 59 (79) |
| 2024 | 37 (59) | 3 (4) | 15 (17) | 54 (89) | 636 (697) | 70 (88) |
| 2025 | 29 (50) | 0 (0) | 27 (27) | 47 (79) | 1,007 (1,386) | 37 (48) |

### 3d. Lookback sensitivity (steps 2-3 only; the SEBI-order window stays at five sessions)

| Year | Lookback | Step 2 removed | Step 3 removed | Left after step 3 | Left at the end |
| --- | --- | --- | --- | --- | --- |
| 2020 | 1 | 230 | 150 | 546 | 54 |
| 2020 | 5 | 322 | 234 | 370 | 28 |
| 2020 | 10 | 408 | 247 | 271 | 18 |
| 2021 | 1 | 380 | 126 | 470 | 266 |
| 2021 | 5 | 454 | 191 | 331 | 172 |
| 2021 | 10 | 497 | 227 | 252 | 120 |
| 2022 | 1 | 226 | 379 | 541 | 136 |
| 2022 | 5 | 288 | 501 | 357 | 74 |
| 2022 | 10 | 337 | 555 | 254 | 45 |
| 2023 | 1 | 701 | 255 | 884 | 480 |
| 2023 | 5 | 853 | 385 | 602 | 295 |
| 2023 | 10 | 970 | 434 | 436 | 181 |
| 2024 | 1 | 557 | 223 | 599 | 313 |
| 2024 | 5 | 680 | 301 | 398 | 178 |
| 2024 | 10 | 747 | 354 | 278 | 109 |
| 2025 | 1 | 341 | 697 | 927 | 493 |
| 2025 | 5 | 500 | 903 | 562 | 268 |
| 2025 | 10 | 578 | 999 | 388 | 160 |

### 3e. What is left at the end, by cut-off, lookback, year and turnover band

Turnover bands: quintiles of the 60-session average traded value (close times quantity) across all EQ stocks
with 60 observations on D, Q1 lowest. No event left has an unknown band.

| Cut-off | Lookback | Year | Events | Dates | Symbols | Q1 | Q2 | Q3 | Q4 | Q5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 09:00 next session | 5 | 2020 | 28 | 23 | 28 | 0 | 3 | 10 | 6 | 9 |
| 09:00 next session | 5 | 2021 | 172 | 96 | 146 | 4 | 32 | 36 | 47 | 53 |
| 09:00 next session | 5 | 2022 | 74 | 45 | 67 | 2 | 13 | 14 | 12 | 33 |
| 09:00 next session | 5 | 2023 | 295 | 136 | 255 | 6 | 67 | 65 | 75 | 82 |
| 09:00 next session | 5 | 2024 | 178 | 106 | 162 | 18 | 31 | 38 | 37 | 54 |
| 09:00 next session | 5 | 2025 | 268 | 121 | 232 | 12 | 64 | 72 | 66 | 54 |
| 18:00 on D | 5 | 2020 | 29 | 24 | 29 | 0 | 3 | 10 | 7 | 9 |
| 18:00 on D | 5 | 2021 | 183 | 98 | 155 | 4 | 34 | 37 | 51 | 57 |
| 18:00 on D | 5 | 2022 | 82 | 47 | 74 | 2 | 15 | 17 | 13 | 35 |
| 18:00 on D | 5 | 2023 | 311 | 139 | 268 | 7 | 69 | 73 | 76 | 86 |
| 18:00 on D | 5 | 2024 | 186 | 109 | 170 | 19 | 33 | 40 | 39 | 55 |
| 18:00 on D | 5 | 2025 | 291 | 128 | 251 | 12 | 68 | 75 | 74 | 62 |
| 23:59 on D | 5 | 2020 | 29 | 24 | 29 | 0 | 3 | 10 | 7 | 9 |
| 23:59 on D | 5 | 2021 | 174 | 97 | 147 | 4 | 32 | 36 | 48 | 54 |
| 23:59 on D | 5 | 2022 | 75 | 45 | 68 | 2 | 14 | 14 | 12 | 33 |
| 23:59 on D | 5 | 2023 | 302 | 138 | 261 | 7 | 67 | 68 | 76 | 84 |
| 23:59 on D | 5 | 2024 | 181 | 107 | 165 | 19 | 32 | 38 | 38 | 54 |
| 23:59 on D | 5 | 2025 | 274 | 123 | 235 | 12 | 66 | 72 | 68 | 56 |
| 09:00 next session | 1 | 2020 | 54 | 41 | 53 | 0 | 5 | 15 | 12 | 22 |
| 09:00 next session | 1 | 2021 | 266 | 123 | 215 | 4 | 47 | 55 | 72 | 88 |
| 09:00 next session | 1 | 2022 | 136 | 60 | 121 | 3 | 23 | 23 | 32 | 55 |
| 09:00 next session | 1 | 2023 | 480 | 171 | 392 | 9 | 96 | 107 | 122 | 146 |
| 09:00 next session | 1 | 2024 | 313 | 140 | 267 | 28 | 48 | 65 | 61 | 111 |
| 09:00 next session | 1 | 2025 | 493 | 163 | 406 | 20 | 94 | 132 | 128 | 119 |
| 09:00 next session | 10 | 2020 | 18 | 15 | 18 | 0 | 3 | 6 | 2 | 7 |
| 09:00 next session | 10 | 2021 | 120 | 74 | 100 | 1 | 26 | 26 | 32 | 35 |
| 09:00 next session | 10 | 2022 | 45 | 29 | 44 | 2 | 7 | 8 | 6 | 22 |
| 09:00 next session | 10 | 2023 | 181 | 97 | 162 | 4 | 47 | 41 | 44 | 45 |
| 09:00 next session | 10 | 2024 | 109 | 81 | 102 | 12 | 23 | 26 | 21 | 27 |
| 09:00 next session | 10 | 2025 | 160 | 84 | 148 | 10 | 44 | 39 | 38 | 29 |

### 3f. Unknown and unstable inputs, and the notes that remove nothing (all down events, main setting)

| Year | Down events | Market unknown | Peers unknown | Unstable peer ratio | G3 fail | G3 unknown | G5 fail | G5 unknown | ASM active | GSM unknown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | 2,767 | 1 | 2,153 | 49 | 9 | 0 | 732 | 7 | 147 | 2,767 |
| 2021 | 1,272 | 18 | 197 | 18 | 6 | 0 | 186 | 6 | 116 | 1,272 |
| 2022 | 2,249 | 26 | 404 | 104 | 8 | 0 | 393 | 16 | 116 | 2,249 |
| 2023 | 2,616 | 14 | 266 | 85 | 7 | 0 | 439 | 10 | 138 | 2,616 |
| 2024 | 2,456 | 133 | 490 | 110 | 8 | 0 | 136 | 6 | 169 | 2,456 |
| 2025 | 2,635 | 0 | 518 | 23 | 26 | 0 | 440 | 14 | 96 | 2,625 |

Among the events left at the end (main setting): G5 unknown 2020 1, 2021 0, 2022 1, 2023 0, 2024 0, 2025 0; G3 unknown 0 in every year; unstable peer ratio 2020 0, 2021 0, 2022 0, 2023 0, 2024 0, 2025 2.

### 3g. Dividend parsing (step 7)

Per event year, distinct Dividend, Record Date and Book Closure filings examined (one filing can be examined in
several years). "Matched" = its parsed record or book-closure date is D or the EQ session before D.

| Year | Not about a dividend | Dividend, date not parsed | Dividend, date parsed | Amount parsed (any) | Matched to an event | Matched with amount and pre-D close | Matched, amount at least 2% |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | 348 | 1,188 | 79 | 170 | 6 | 0 | 0 |
| 2021 | 735 | 1,720 | 388 | 211 | 14 | 0 | 0 |
| 2022 | 1,646 | 3,734 | 1,085 | 884 | 17 | 0 | 0 |
| 2023 | 2,477 | 5,813 | 1,976 | 1,518 | 20 | 0 | 0 |
| 2024 | 2,807 | 7,215 | 2,716 | 1,880 | 17 | 0 | 0 |
| 2025 | 3,608 | 8,325 | 3,737 | 2,289 | 44 | 0 | 0 |

The zero in the last column is not evidence that the dividends were small: across all such filings from October
2019 to 2025, only 6 of 5,604 with a parsed record date also have a parsed amount (a typical miss is "Dividend of Rs.
4.50/- (@ 225%) per share", where the bracket sits between the amount and "per"). No matched filing had an amount.

### 3h. SEBI orders and the 2025 GSM entry check

SEBI orders in scope: 71 orders (71 rows) known in 2020, 71 without a symbol. None is linked to a stock, so step 4 removes nothing; no link was inferred from company names.

GSM entries in 2025: 94 entry checks for 23 distinct stocks. G5 on the entry day: PASS 1, FAIL 18, UNKNOWN 75 (stocks with at least one pass: 1). The 75 UNKNOWN checks have no usable screening plan, which is not a liquidity pass: 39 had no bar at all on the entry day, 34 traded only in the trade-for-trade BE (22) or BZ (12) series, and 2 had an EQ bar but fewer than the 21 sessions the plan needs.

### 3i. Reproduction and limits found while finishing the count

First run: `python -B scripts/abc_followup_counts.py funnel` (all years, 9 min 12 s) and `... notes`. Second run: one
`--years` piece per year (26 s to 4 min 34 s each) and `notes` again. Per-year digests of the steps, sensitivities,
final counts, diagnostics and dividends (rulebook 4feb5d1f0d1f, cost config 8670e2e48632)
are identical between the two runs for every year, and the two `notes` outputs are byte-identical.

- **P8-093.** Item 2's session calendar admits a session only if its bars are known by the next requested event date.
  Thirteen sessions whose bars were known one to three days late (weekend specials and a few weekdays) therefore enter
  the history as empty sessions, and five sessions known months later are skipped. Item 2's tables and this funnel's
  full run admit the same thirteen. A per-year piece first disagreed with the full run for 2024 (one more admitted
  session, 1 Aug 2023), so pieces now request the same dates as the full run. One effect stays in both item 2 and these
  tables: on the session after each admitted empty session no consecutive return exists, so the market move is unknown
  (2020 1, 2021 18, 2022 26, 2023 14, 2024 133 events; 109 of the 2024 ones on 23 Jan 2024, after Saturday 20 Jan) and
  those events are removed at step 8 as unknown peers. Changing that would change item 2, which was out of scope.
- Peers are UNKNOWN for most of 2020 (2,153 of 2,767 events) because the history starts in October 2019 and the main
  setting needs 200 sessions; step 8 therefore removes most of 2020 on its own.
- GSM status is UNKNOWN for nearly every event (no stored GSM transition for the stock); ASM is active for 96-169 events
  a year. Neither removes an event.

### Parsing and interpretation limits

The dividend check uses only the three requested categories and descriptions explicitly mentioning a dividend (or the Dividend category). A record/book-closure date must be attached to that label in the text; an arbitrary meeting date is not substituted. Amounts require a rupee-per-share expression; percentages without an established face value are not converted. The 2% count is limited to matched event/filing pairs whose amount and pre-D EQ close are available. It does not read a later record-date price. Parsed dates are clues, not verified ex-dates. Unparseable descriptions remain visible as a gap. The same previously known filing can be examined in several event years; the per-year filing counts must not be summed as unique releases.

The material/unclear map is the 279-category draft from the sourcing check, used only by this report's script. A category match is not a finding that the filing explains the move. Unclear subcategory counts can overlap across events/windows. The results-route gap, unknown peer history, unknown surveillance status and unlinked orders are limits on an “unexplained” description. ASM/GSM notes do not remove events. Lack of a stored GSM transition is UNKNOWN, including after 2025 began; it is not proof of absence.

Reproduction: `python -B scripts/abc_followup_counts.py funnel [--years 2024]` and `python -B scripts/abc_followup_counts.py notes` print aggregate JSON only. The script imports the existing return/correlation, screening-plan, sizing and G5 functions. Its query wrapper limits bars to D before existing helpers see them. Tests cover an adversarial future-price row, exact filing cut-offs, next-session date-only timing, dividend date labels, ASM mechanism names and closure-bridge timing; and, added on review, the whole funnel (market, peers, turnover, G3/G5) on a store that raises if any bar after D is read, a filing one second after the cut-off that removes nothing while one at the cut-off does, a SEBI order known on D that cannot remove the event, and a one-year run that streams the same sessions as a longer run. No rule, cost setting or pre-registration is changed.

Changed on review (Claude, 19 October): the per-year `--years` option and the separate `notes` part (so a run can be split into foreground pieces), with the stream fix of P8-093; step tables for the 1- and 10-session lookbacks; two extra diagnostic Unclear sub-counts (generic and financial-results clarifications) and the `Outcome of Board Meeting-XBRL` spelling in the board group; the four tests above. None of Codex's nine removal conditions or its listed decisions was changed.
