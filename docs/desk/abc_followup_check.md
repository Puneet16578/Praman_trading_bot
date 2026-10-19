# A/B/C follow-up: input counts and sourcing

19 October 2026. Personal research only. These are counting conventions, not strategy rules. No outcome, post-event price, or forward-window price was read. The store was opened read-only. No download, backfill, rule/configuration change, firewall change, or Strategy 0 change was made.

The completed repaired market and peer tables are in [the sourcing check, section 8](abc_sourcing_check.md#8-event-day-market-and-peer-moves-inputs-only), committed in `b041714`. This report uses that fund-exclusion map, consecutive-session return convention, market-adjusted correlations, 250-session history and 200-pair minimum. It does not revise item 2. Revised 19 October 2026: item 2's session calendar was fixed (P8-093, commit `b72f913`), so item 2's tables and this report's sections 3 and 4 were regenerated; see the note at the start of section 3. The pre-fix tables are kept in the appendix.

## 3. B: successive exclusions from catalogue down events

**Regenerated 19 October 2026 (Claude), after the P8-093 fix.**

**What the fix changed.** Item 2's session calendar now admits only sessions with at least one EQ bar known on their own day, whatever dates a run requests (commit `b72f913`; see section 3i). Before the fix, 13 late-published sessions entered as empty sessions. The market move on the session after each was unknown, and those 192 down events were removed at step 8 as unknown peers.

Tables 3a-3h and section 4 are regenerated. The earlier tables are kept unchanged in the appendix at the end of this report.

**What changed.** In the table, "before → after" marks a change and a single number means unchanged. The lookback is 5 sessions unless stated.

| Year | Market unknown | Peers unknown | Step 1 removed | Step 8 removed | Left: 09:00 next session | Left: 18:00 on D | Left: 23:59 on D | Left: 09:00, lookback 1 | Left: 09:00, lookback 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | 1 → 0 | 2,153 → 2,150 | 1,841 | 230 → 228 | 28 → 30 | 29 → 31 | 29 → 31 | 54 → 56 | 18 → 19 |
| 2021 | 18 → 0 | 197 → 186 | 296 | 54 → 52 | 172 | 183 | 174 | 266 → 268 | 120 → 119 |
| 2022 | 26 → 0 | 404 → 357 | 1,103 → 1,109 | 41 → 36 | 74 → 77 | 82 → 86 | 75 → 78 | 136 → 140 | 45 → 48 |
| 2023 | 14 → 0 | 266 → 249 | 776 | 82 → 80 | 295 → 297 | 311 → 313 | 302 → 304 | 480 → 485 | 181 → 182 |
| 2024 | 133 → 0 | 490 → 369 | 1,077 → 1,195 | 158 → 96 | 178 | 186 | 181 | 313 → 317 | 109 |
| 2025 | 0 | 518 → 516 | 670 | 151 | 268 | 291 | 274 | 493 → 494 | 160 |
| All | 192 → 0 | 4,028 → 3,827 | 5,763 → 5,887 | 716 → 643 | 1,015 → 1,022 | 1,082 → 1,090 | 1,035 → 1,042 | 1,742 → 1,760 | 633 → 637 |

Most of the change is in 2024:

- The 133 events with an unknown market move (109 of them on 23 January 2024) now have one.
- 118 of them fell on days when the market fell more than 2%, so step 1 removes 118 more events and step 8 removes 62 fewer.
- The 2024 end count stays 178.

In 2022, 6 of the 26 such events move to step 1. Elsewhere the end counts change by -1 to +5 events per year, mostly through step 8: the empty sessions no longer shorten peer histories, so fewer peers are UNKNOWN.

3b, 3c, 3g and 3h are unchanged. 3d, 3e and 3f change as above. In 3e, turnover bands differ only in the rows whose counts differ.

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
| 8. Peers share at least half, or peers UNKNOWN | 228 | 54 | 40 | 52 | 2,213 |
| 9. G3 structure window or G5 failure | 24 | 30 | 25 | 30 | 741 |

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
| 8. Peers share at least half, or peers UNKNOWN | 52 | 209 | 110 | 177 | 207 |
| 9. G3 structure window or G5 failure | 37 | 172 | 96 | 147 | 191 |

**2022**

| Step | Removed | Left | Dates left | Symbols left | Removes on its own |
| --- | --- | --- | --- | --- | --- |
| Down events (start) | — | 2,249 | 220 | 1,203 | — |
| 1. Down-market day (market mean below -2%) | 1,109 | 1,140 | 201 | 779 | 1,109 |
| 2. Material filing in window | 284 | 856 | 189 | 643 | 448 |
| 3. Unclear filing in window | 499 | 357 | 148 | 296 | 1,166 |
| 4. Linked SEBI order | 0 | 357 | 148 | 296 | 0 |
| 5. No filing in the 90 days before D | 67 | 290 | 132 | 248 | 147 |
| 6. 2022 results-route gap | 156 | 134 | 65 | 125 | 785 |
| 7. Likely ex-dividend day | 0 | 134 | 65 | 125 | 18 |
| 8. Peers share at least half, or peers UNKNOWN | 36 | 98 | 59 | 90 | 487 |
| 9. G3 structure window or G5 failure | 21 | 77 | 47 | 70 | 401 |

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
| 8. Peers share at least half, or peers UNKNOWN | 80 | 412 | 159 | 351 | 376 |
| 9. G3 structure window or G5 failure | 115 | 297 | 137 | 257 | 446 |

**2024**

| Step | Removed | Left | Dates left | Symbols left | Removes on its own |
| --- | --- | --- | --- | --- | --- |
| Down events (start) | — | 2,456 | 228 | 1,313 | — |
| 1. Down-market day (market mean below -2%) | 1,195 | 1,261 | 212 | 860 | 1,195 |
| 2. Material filing in window | 649 | 612 | 190 | 483 | 996 |
| 3. Unclear filing in window | 276 | 336 | 152 | 287 | 1,542 |
| 4. Linked SEBI order | 0 | 336 | 152 | 287 | 0 |
| 5. No filing in the 90 days before D | 43 | 293 | 140 | 262 | 72 |
| 6. 2022 results-route gap | 0 | 293 | 140 | 262 | 0 |
| 7. Likely ex-dividend day | 6 | 287 | 137 | 257 | 17 |
| 8. Peers share at least half, or peers UNKNOWN | 96 | 191 | 113 | 171 | 585 |
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
| 2020 | 1 | 230 | 150 | 546 | 56 |
| 2020 | 5 | 322 | 234 | 370 | 30 |
| 2020 | 10 | 408 | 247 | 271 | 19 |
| 2021 | 1 | 380 | 126 | 470 | 268 |
| 2021 | 5 | 454 | 191 | 331 | 172 |
| 2021 | 10 | 497 | 227 | 252 | 119 |
| 2022 | 1 | 223 | 378 | 539 | 140 |
| 2022 | 5 | 284 | 499 | 357 | 77 |
| 2022 | 10 | 333 | 553 | 254 | 48 |
| 2023 | 1 | 701 | 255 | 884 | 485 |
| 2023 | 5 | 853 | 385 | 602 | 297 |
| 2023 | 10 | 970 | 434 | 436 | 182 |
| 2024 | 1 | 538 | 212 | 511 | 317 |
| 2024 | 5 | 649 | 276 | 336 | 178 |
| 2024 | 10 | 712 | 316 | 233 | 109 |
| 2025 | 1 | 341 | 697 | 927 | 494 |
| 2025 | 5 | 500 | 903 | 562 | 268 |
| 2025 | 10 | 578 | 999 | 388 | 160 |

### 3e. What is left at the end, by cut-off, lookback, year and turnover band

Turnover bands: quintiles of the 60-session average traded value (close times quantity) across all EQ stocks
with 60 observations on D, Q1 lowest. No event left has an unknown band.

| Cut-off | Lookback | Year | Events | Dates | Symbols | Q1 | Q2 | Q3 | Q4 | Q5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 09:00 next session | 5 | 2020 | 30 | 25 | 30 | 0 | 3 | 11 | 6 | 10 |
| 09:00 next session | 5 | 2021 | 172 | 96 | 147 | 4 | 32 | 35 | 47 | 54 |
| 09:00 next session | 5 | 2022 | 77 | 47 | 70 | 3 | 14 | 14 | 13 | 33 |
| 09:00 next session | 5 | 2023 | 297 | 137 | 257 | 6 | 67 | 66 | 75 | 83 |
| 09:00 next session | 5 | 2024 | 178 | 106 | 162 | 18 | 31 | 38 | 37 | 54 |
| 09:00 next session | 5 | 2025 | 268 | 121 | 232 | 12 | 64 | 72 | 66 | 54 |
| 18:00 on D | 5 | 2020 | 31 | 26 | 31 | 0 | 3 | 11 | 7 | 10 |
| 18:00 on D | 5 | 2021 | 183 | 98 | 156 | 4 | 34 | 36 | 51 | 58 |
| 18:00 on D | 5 | 2022 | 86 | 49 | 78 | 3 | 16 | 18 | 14 | 35 |
| 18:00 on D | 5 | 2023 | 313 | 140 | 270 | 7 | 69 | 74 | 76 | 87 |
| 18:00 on D | 5 | 2024 | 186 | 109 | 170 | 19 | 33 | 40 | 39 | 55 |
| 18:00 on D | 5 | 2025 | 291 | 128 | 251 | 12 | 68 | 75 | 74 | 62 |
| 23:59 on D | 5 | 2020 | 31 | 26 | 31 | 0 | 3 | 11 | 7 | 10 |
| 23:59 on D | 5 | 2021 | 174 | 97 | 148 | 4 | 32 | 35 | 48 | 55 |
| 23:59 on D | 5 | 2022 | 78 | 47 | 71 | 3 | 15 | 14 | 13 | 33 |
| 23:59 on D | 5 | 2023 | 304 | 139 | 263 | 7 | 67 | 69 | 76 | 85 |
| 23:59 on D | 5 | 2024 | 181 | 107 | 165 | 19 | 32 | 38 | 38 | 54 |
| 23:59 on D | 5 | 2025 | 274 | 123 | 235 | 12 | 66 | 72 | 68 | 56 |
| 09:00 next session | 1 | 2020 | 56 | 43 | 55 | 0 | 5 | 16 | 12 | 23 |
| 09:00 next session | 1 | 2021 | 268 | 123 | 217 | 4 | 47 | 54 | 74 | 89 |
| 09:00 next session | 1 | 2022 | 140 | 62 | 125 | 4 | 24 | 23 | 33 | 56 |
| 09:00 next session | 1 | 2023 | 485 | 172 | 395 | 9 | 97 | 108 | 123 | 148 |
| 09:00 next session | 1 | 2024 | 317 | 141 | 271 | 28 | 49 | 66 | 61 | 113 |
| 09:00 next session | 1 | 2025 | 494 | 163 | 407 | 20 | 95 | 132 | 128 | 119 |
| 09:00 next session | 10 | 2020 | 19 | 16 | 19 | 0 | 3 | 6 | 2 | 8 |
| 09:00 next session | 10 | 2021 | 119 | 73 | 100 | 1 | 26 | 25 | 32 | 35 |
| 09:00 next session | 10 | 2022 | 48 | 31 | 47 | 3 | 8 | 8 | 7 | 22 |
| 09:00 next session | 10 | 2023 | 182 | 98 | 163 | 4 | 47 | 42 | 44 | 45 |
| 09:00 next session | 10 | 2024 | 109 | 81 | 102 | 12 | 23 | 26 | 21 | 27 |
| 09:00 next session | 10 | 2025 | 160 | 84 | 148 | 10 | 44 | 39 | 38 | 29 |

### 3f. Unknown and unstable inputs, and the notes that remove nothing (all down events, main setting)

| Year | Down events | Market unknown | Peers unknown | Unstable peer ratio | G3 fail | G3 unknown | G5 fail | G5 unknown | ASM active | GSM unknown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | 2,767 | 0 | 2,150 | 49 | 9 | 0 | 732 | 7 | 147 | 2,767 |
| 2021 | 1,272 | 0 | 186 | 18 | 6 | 0 | 186 | 6 | 116 | 1,272 |
| 2022 | 2,249 | 0 | 357 | 105 | 8 | 0 | 393 | 16 | 116 | 2,249 |
| 2023 | 2,616 | 0 | 249 | 85 | 7 | 0 | 439 | 10 | 138 | 2,616 |
| 2024 | 2,456 | 0 | 369 | 133 | 8 | 0 | 136 | 6 | 169 | 2,456 |
| 2025 | 2,635 | 0 | 516 | 23 | 26 | 0 | 440 | 14 | 96 | 2,625 |

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

Regenerated 19 October 2026 after the P8-093 fix. First pass: one `--years` piece per year. Each piece streams from October 2019 up to its last year, so a piece took from 30 s (2020) to 4 min 36 s (2025). Second pass: pieces for 2020–2022, 2023–2024 and 2025. Per-year digests cover the steps, sensitivities, final counts, diagnostics and dividends (rulebook 4feb5d1f0d1f, cost config 8670e2e48632). They are identical between the two passes for every year. `notes` does not use the calendar, and its output is byte-identical to the pre-fix run. The pre-fix runs are described in the appendix.

- **P8-093 (fixed 19 October 2026).** Before the fix, item 2's session calendar admitted a session if any of its bars was known by the next requested event date. Thirteen sessions whose bars were known one to three days late therefore entered the history as empty sessions. On the session after each, no consecutive return existed and the market move was unknown. That affected 2020 1, 2021 18, 2022 26, 2023 14 and 2024 133 down events, 109 of the 2024 ones on 23 January 2024; those events were removed at step 8 as unknown peers. Now the calendar holds only sessions with at least one EQ bar known on their own day, whatever the requests. Those 13 sessions are left out, like the five known 10 days to over four years later, and the next session's return runs from the last close then known. No down event now has an unknown market move.
- The funnel's own calendar for finding D's previous and next sessions (filing windows, cut-offs, G3/G5) is a fixed list of every stored EQ session up to 10 January 2026. It does not depend on the requests and was not changed. It still contains the 18 late-published sessions as dates; that is a calendar convention, not a price read. The same holds for `notes` and section 4.
- Peers are UNKNOWN for most of 2020 (2,150 of 2,767 events), because the history starts in October 2019 and the main setting needs 200 sessions. Step 8 therefore removes most of 2020 on its own.
- GSM status is UNKNOWN for nearly every event (no stored GSM transition for the stock); ASM is active for 96-169 events a year. Neither removes an event.

### Parsing and interpretation limits

The dividend check uses only the three requested categories and descriptions explicitly mentioning a dividend (or the Dividend category). A record/book-closure date must be attached to that label in the text; an arbitrary meeting date is not substituted. Amounts require a rupee-per-share expression; percentages without an established face value are not converted. The 2% count is limited to matched event/filing pairs whose amount and pre-D EQ close are available. It does not read a later record-date price. Parsed dates are clues, not verified ex-dates. Unparseable descriptions remain visible as a gap. The same previously known filing can be examined in several event years; the per-year filing counts must not be summed as unique releases.

The material/unclear map is the 279-category draft from the sourcing check, used only by this report's script. A category match is not a finding that the filing explains the move. Unclear subcategory counts can overlap across events/windows. The results-route gap, unknown peer history, unknown surveillance status and unlinked orders are limits on an “unexplained” description. ASM/GSM notes do not remove events. Lack of a stored GSM transition is UNKNOWN, including after 2025 began; it is not proof of absence.

Reproduction: `python -B scripts/abc_followup_counts.py funnel [--years 2024]` and `python -B scripts/abc_followup_counts.py notes` print aggregate JSON only. The script imports the existing return/correlation, screening-plan, sizing and G5 functions. Its query wrapper limits bars to D before existing helpers see them. Tests cover an adversarial future-price row, exact filing cut-offs, next-session date-only timing, dividend date labels, ASM mechanism names and closure-bridge timing; and, added on review, the whole funnel (market, peers, turnover, G3/G5) on a store that raises if any bar after D is read, a filing one second after the cut-off that removes nothing while one at the cut-off does, a SEBI order known on D that cannot remove the event, and a one-year run that streams the same sessions as a longer run. No rule, cost setting or pre-registration is changed.

Changed on review (Claude, 19 October): the per-year `--years` option and the separate `notes` part (so a run can be split into foreground pieces), with the stream fix of P8-093; step tables for the 1- and 10-session lookbacks; two extra diagnostic Unclear sub-counts (generic and financial-results clarifications) and the `Outcome of Board Meeting-XBRL` spelling in the board group; the four tests above. None of Codex's nine removal conditions or its listed decisions was changed.

## 4. A: events with company news between the previous close and the open

**Regenerated 19 October 2026 (Claude), after the P8-093 fix.** The market move on D comes from item 2's calendar, so this table changed with it. Before → after:

- Unknown market moves among all events: 638 → 0 (inside the pool, 41 → 0).
- Material filings left out because the market moved over 2% the same way: 361 → 375.
- Pool: 3,402 → 3,388. By year: 2020 up -1, 2021 up -1, 2022 down -2, 2023 up -3, 2024 down -7.
- Events that would join with Board Outcome or Press Release: 1,446 → 1,443.

Events with a Material filing overnight (3,763) and every 2025 row are unchanged. The pre-fix table is in the appendix.

Counting convention only, not a strategy rule. All catalogue events 2020-2025 (`return_1d` above zero is up, below
zero is down). An event is in the pool if the same symbol has a Material news filing (the 279-category draft map)
published from the previous EQ session's close (15:30, inclusive) up to D's open (09:15, exclusive), and the
equal-weight market (item 2's definition) did not move more than 2% the same way on D. A filing at 09:15 or later
never adds an event. Bins: previous evening (15:30 to midnight on the previous session's date), closure bridge (the
calendar days between the two sessions: weekends and holidays) and before the open (00:00 to 09:15 on D); one
event can have filings in several bins. Every stored announcement in the period carries a time on its knowledge
date, so no date-only filing had to be placed (none became known exactly at an open). Events with an unknown
market move cannot be tested against the 2% rule; they stay in the pool and are counted. The market move uses
D's close; nothing after D's close is read.

| Year | Direction | Events | Material filing overnight | Left out: market moved over 2% the same way | Pool | Previous evening | Closure bridge | Before open | Pool dates | Pool symbols | Pool with market unknown | Would join with Board Outcome or Press Release |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | down | 2,767 | 171 | 36 | 135 | 125 | 11 | 2 | 58 | 128 | 0 | 12 |
| 2020 | up | 7,144 | 244 | 20 | 224 | 197 | 24 | 5 | 102 | 203 | 0 | 61 |
| 2021 | down | 1,272 | 246 | 7 | 239 | 192 | 49 | 3 | 85 | 202 | 0 | 23 |
| 2021 | up | 7,691 | 267 | 12 | 255 | 210 | 42 | 4 | 118 | 217 | 0 | 74 |
| 2022 | down | 2,249 | 199 | 58 | 141 | 113 | 26 | 6 | 64 | 130 | 0 | 156 |
| 2022 | up | 7,055 | 243 | 11 | 232 | 187 | 40 | 9 | 112 | 209 | 0 | 212 |
| 2023 | down | 2,616 | 442 | 25 | 417 | 345 | 69 | 3 | 94 | 353 | 0 | 44 |
| 2023 | up | 9,280 | 439 | 5 | 434 | 374 | 58 | 3 | 125 | 371 | 0 | 116 |
| 2024 | down | 2,456 | 432 | 88 | 344 | 301 | 43 | 0 | 89 | 295 | 0 | 32 |
| 2024 | up | 8,135 | 405 | 8 | 397 | 341 | 51 | 7 | 139 | 347 | 0 | 102 |
| 2025 | down | 2,635 | 298 | 78 | 220 | 197 | 24 | 3 | 85 | 205 | 0 | 270 |
| 2025 | up | 7,394 | 377 | 27 | 350 | 304 | 37 | 13 | 147 | 306 | 0 | 341 |

Totals 2020-2025: 3,388 events in the pool; 1,443 more would join if Outcome of Board Meeting and
Press Release filings counted (both stored spellings of each: "Outcome of Board Meeting" and "...-XBRL", "Press
Release" and "Press Release (Revised)"), under the same window and market rule. The joiners' bins:
2020 down 9/1/2, 2020 up 50/5/6, 2021 down 17/4/2, 2021 up 56/12/8, 2022 down 103/52/6, 2022 up 134/70/11, 2023 down 36/2/6, 2023 up 85/20/13, 2024 down 28/3/1, 2024 up 73/18/12, 2025 down 217/54/6, 2025 up 286/45/17 (previous evening / closure bridge / before open).

Unknown market moves among all events: none in any year since the P8-093 fix (638 before: 2020 down 1, 2020 up 78, 2021 down 18, 2021 up 159, 2022 down 26, 2022 up 130, 2023 down 14, 2023 up 20, 2024 down 133, 2024 up 59).

Limits: a Material category is a label from the draft map, not a finding that the filing moved the price; stored
times are taken as IST publication times, which were not verified as first publication; special-session closing
times were not reconstructed (15:30 is used for every session). Reproduction: `python -B scripts/abc_followup_counts.py
clean_pool` (3 min); after the P8-093 fix, two runs gave byte-identical output (sha256 b88b4af8...; f9c4cbb7... before the fix). Tests: the bin edges (15:29:59 and
09:15:00 excluded), a whole run on a store that raises if any bar after D is read, a filing at 09:15:00 that adds
nothing while one at 09:14:59 does, and the same-direction market rule.

## 5. Results coverage from stored announcements (no downloads)

For each quarter ending September 2019 to September 2025: of the EQ symbols with at least one EQ bar in the 75
days after the quarter ends (day 1 is the day after quarter end; fund units excluded by the current ISIN map, as
in item 2), the share with at least one results-bearing filing published in those 75 days. Sources are added
step by step, so each column includes the ones before it: (a) the two legacy tags, Financial Result Updates and
Financial Results Updates; (b) plus Outcome of Board Meeting whose description contains the case-insensitive
phrase "financial result" (the sourcing check's convention); (c) plus Integrated Filing- Financial; (d) plus Copy
of Newspaper Publication and Newspaper Advertisements whose description contains that phrase. The window uses the
stored publication time (every row is timestamped); a filing after day 75 does not count. The denominator uses
the window, not the quarter, because the bar data start on 1 October 2019.

| Quarter end | EQ symbols trading in window | Fund units excluded | Symbols | (a) Legacy tags | (b) + Board outcome | (c) + Integrated Financial | (d) + Newspaper |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-09-30 | 1,578 | 75 | 1,503 | 1,342 (89.3%) | 1,343 (89.4%) | 1,343 (89.4%) | 1,343 (89.4%) |
| 2019-12-31 | 1,623 | 79 | 1,544 | 1,388 (89.9%) | 1,388 (89.9%) | 1,388 (89.9%) | 1,388 (89.9%) |
| 2020-03-31 | 1,611 | 79 | 1,532 | 438 (28.6%) | 438 (28.6%) | 438 (28.6%) | 438 (28.6%) |
| 2020-06-30 | 1,610 | 86 | 1,524 | 1,316 (86.4%) | 1,316 (86.4%) | 1,316 (86.4%) | 1,317 (86.4%) |
| 2020-09-30 | 1,683 | 91 | 1,592 | 1,427 (89.6%) | 1,427 (89.6%) | 1,427 (89.6%) | 1,427 (89.6%) |
| 2020-12-31 | 1,668 | 93 | 1,575 | 1,417 (90.0%) | 1,417 (90.0%) | 1,417 (90.0%) | 1,419 (90.1%) |
| 2021-03-31 | 1,707 | 100 | 1,607 | 911 (56.7%) | 911 (56.7%) | 911 (56.7%) | 914 (56.9%) |
| 2021-06-30 | 1,680 | 104 | 1,576 | 1,425 (90.4%) | 1,425 (90.4%) | 1,425 (90.4%) | 1,425 (90.4%) |
| 2021-09-30 | 1,785 | 110 | 1,675 | 1,512 (90.3%) | 1,512 (90.3%) | 1,512 (90.3%) | 1,512 (90.3%) |
| 2021-12-31 | 1,801 | 123 | 1,678 | 1,530 (91.2%) | 1,530 (91.2%) | 1,530 (91.2%) | 1,531 (91.2%) |
| 2022-03-31 | 1,884 | 139 | 1,745 | 1,581 (90.6%) | 1,584 (90.8%) | 1,584 (90.8%) | 1,586 (90.9%) |
| 2022-06-30 | 1,890 | 141 | 1,749 | 18 (1.0%) | 295 (16.9%) | 295 (16.9%) | 636 (36.4%) |
| 2022-09-30 | 1,933 | 151 | 1,782 | 0 (0.0%) | 281 (15.8%) | 281 (15.8%) | 662 (37.1%) |
| 2022-12-31 | 1,962 | 160 | 1,802 | 1,651 (91.6%) | 1,652 (91.7%) | 1,652 (91.7%) | 1,655 (91.8%) |
| 2023-03-31 | 1,981 | 166 | 1,815 | 1,688 (93.0%) | 1,688 (93.0%) | 1,688 (93.0%) | 1,688 (93.0%) |
| 2023-06-30 | 1,872 | 181 | 1,691 | 1,578 (93.3%) | 1,579 (93.4%) | 1,579 (93.4%) | 1,579 (93.4%) |
| 2023-09-30 | 1,951 | 176 | 1,775 | 1,678 (94.5%) | 1,679 (94.6%) | 1,679 (94.6%) | 1,679 (94.6%) |
| 2023-12-31 | 1,994 | 200 | 1,794 | 1,714 (95.5%) | 1,714 (95.5%) | 1,714 (95.5%) | 1,714 (95.5%) |
| 2024-03-31 | 2,037 | 203 | 1,834 | 1,756 (95.7%) | 1,756 (95.7%) | 1,756 (95.7%) | 1,756 (95.7%) |
| 2024-06-30 | 2,070 | 216 | 1,854 | 1,774 (95.7%) | 1,774 (95.7%) | 1,774 (95.7%) | 1,774 (95.7%) |
| 2024-09-30 | 2,099 | 225 | 1,874 | 1,808 (96.5%) | 1,808 (96.5%) | 1,808 (96.5%) | 1,808 (96.5%) |
| 2024-12-31 | 2,125 | 235 | 1,890 | 1,838 (97.2%) | 1,838 (97.2%) | 1,839 (97.3%) | 1,839 (97.3%) |
| 2025-03-31 | 2,215 | 257 | 1,958 | 0 (0.0%) | 1,159 (59.2%) | 1,207 (61.6%) | 1,321 (67.5%) |
| 2025-06-30 | 2,295 | 275 | 2,020 | 0 (0.0%) | 1,897 (93.9%) | 1,906 (94.4%) | 1,929 (95.5%) |
| 2025-09-30 | 2,448 | 298 | 2,150 | 0 (0.0%) | 2,022 (94.0%) | 2,027 (94.3%) | 2,055 (95.6%) |

What stands out:
- The legacy tags alone cover 86.4-97.2% in the other quarters up to December 2024. They nearly vanish for the June and September 2022
  quarters (18 and 0 symbols), the results-route gap of the sourcing check; board outcomes and newspaper notices
  recover only about 36-37% of symbols there.
- From the March 2025 quarter the legacy tags are gone (the April 2025 route change). Board outcomes carry most
  results afterwards; with all four sources the share is 67.5% for March 2025, 95.5% for June and 95.6% for
  September 2025.
- March 2020 (28.6%) and March 2021 (56.9%) are low in every step. More results may have been published after
  day 75 in those quarters; that was not investigated here, and nothing in this count says why.
- Integrated Filing- Financial adds almost nothing before 2025 (its stored rows begin in January 2025).

Limits: a category or phrase match is evidence that a results-related filing exists, not that it was the first
release of that quarter's results; symbols are matched as strings (renames can split one company); the cache
was not reconciled against a separate results archive. Reproduction: `python -B scripts/abc_followup_counts.py
results_coverage` (under a minute); two runs gave byte-identical output (sha256 b9bc0b9b...). Test: cumulative
steps, exact categories and phrase, day 75 counted and day 76 and the quarter-end day not, fund units excluded,
and a store that raises if any bar after the last window is read.

## 6. Sourcing check for new data (documentation only)

Nothing was downloaded, no data file or API endpoint was opened, and no store was changed. Documentation pages
were opened one at a time with the page reader; every URL is in the ledger at the end of this section, at most 3
pages per site. Codex's pages from earlier today were not recorded, so this ledger starts fresh. **NSE's sites
(nseindia.com, nsearchives.nseindia.com and niftyindices.com) did not answer the reader: all four attempts timed
out after 60 seconds.** They are listed as unreadable and were not worked around, so every NSE-specific timing
claim below is unverified. Two other official sites (indiabudget.gov.in, pib.gov.in) returned HTTP 403 to the
reader. Facts below are marked **read** (from a page in the ledger), **search** (seen only in a search result
snippet of an official document, page not opened) or **unverified** (general knowledge or a secondary report).

**Codex's two findings, re-checked.**
1. "Deal disclosures are meant for same-day release after market hours": **confirmed (read)** in SEBI's circular
   MRD/DoP/SE/Cir-19/05 of 2 September 2005. Block deals: exchanges "shall disseminate the information on block
   deals ... to the general public on the same day, after the market hours"; bulk-deal disclosure under
   SEBI/MRD/SE/Cir-7/2004 (14 January 2004) "shall be continued to be made ... on the same day after the market
   hours". This is the rule, not evidence of when each historical file actually appeared.
2. "F&O ban files apply to the next trade date": **reported by Codex; URL not recorded.** I could not re-check it:
   NSE's surveillance circular NSE/SURV/64402 (4 October 2024), which a search showed names a file of the form
   `fo_secban_DDMMYYYY.csv`, timed out. Which date that file name carries was not established.

### a. Event calendar

- **RBI policy decision days.** The RBI monetary policy page (read) shows the current year's statements, MPC
  resolutions and minutes, archives by financial year back to 2019-20, and a yearly published MPC meeting
  schedule (the 2026-27 schedule was posted on 23 March 2026). It states no announcement time. Format: HTML pages
  with PDF documents. Archive back to October 2019: the year links exist (2019-20 onward); their contents were not
  opened. About 7 archive pages plus one schedule release per year: roughly 15 requests. Store: event_date = the
  decision date; knowledge_date = the statement's release date (time of day not stated; an ASSUMPTION is needed
  for whether it is known during that session); recorded_at = retrieval time.
- **Union Budget days.** indiabudget.gov.in refused the reader (403), so dates are not verified from the official
  page. A PIB snippet (search) dates the 2019-20 budget speech 5 July 2019; the Finance Ministry archive (search)
  lists 2019-20(I), 2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25(I), 2024-25 and 2025-26. The other dates,
  including the interim budget of 1 February 2024, the full budget of 23 July 2024, and the Saturday sessions of
  1 February 2020 and 1 February 2025, are **unverified** here. About 9 speech pages. Store: event_date =
  presentation day; knowledge_date = the same day (the speech is public as delivered; time not verified).
- **2024 general election results day.** ECI press note ECI/PN/113/2024 of 1 June 2024, reproduced by PIB (search;
  the PIB page itself returned 403): counting on "4th June, 2024 (Tuesday) starting 8AM", Sikkim and Arunachal
  Pradesh from 6 AM on 2 June. One document. Store: event_date = 2024-06-04; knowledge_date = the press note's date
  for the schedule, with results arriving during that session.
- **NSE holidays and special sessions.** NSE's holiday page timed out (unreadable). Not verified: format,
  publication time, archive. The store's own sessions give the trading days actually held, but it lacks four
  weekend special sessions (P8-070), so it is not a complete special-session record. Expect one holiday circular a
  year plus one circular per special session (Muhurat, Budget Saturdays, disaster-recovery test sessions):
  roughly 20 documents.
- **F&O expiry dates.** SEBI circular SEBI/HO/MRD/TPD-1/P/CIR/2025/76 of 26 May 2025, "Final Settlement Day (Expiry
  Day) for Equity Derivatives Contracts" (read: title, number and date only; the body is an embedded PDF the reader
  could not show). News reports (unverified) and the NSE June 2025 circular FAOP68589 listed in section 9 of the
  sourcing check (not re-opened today) describe NSE moving from Thursday to Tuesday for contracts expiring on or
  after 1 September 2025. Dated records of each expiry live in NSE's contract files and circulars, not checked
  today. Store: event_date = the contract's expiry date as listed at the time; knowledge_date = the date of the
  record that listed it (expiries are known in advance; holiday shifts need their own circulars).
- **US Fed decision days.** The FOMC calendar (read) gives 2021-2025 meeting dates with statements; the historical
  pages (read) give 2019 and 2020, including the unscheduled meetings of 2 March 2020 (statement released 3 March)
  and 15 March 2020. No page states a release time (the usual 14:00 Eastern release, after India's close, is
  **unverified** here). About 7 year pages. Terms: US government site (not checked). Store: event_date = the
  statement's release date (US); knowledge_date for India = the next Indian session (ASSUMPTION until a release
  time is evidenced).

### b. Bulk and block deals

Published by the exchanges under SEBI's 2004 and 2005 circulars (read): same day, after market hours; block-deal
fields named include scrip, client name, quantity bought/sold and traded price. A search result describes an
October 2025 revision of the block-deal framework (minimum Rs 25 crore, two windows): **unverified**. NSE's report
pages, file format, daily publication time and archive depth were not verified (NSE unreadable). Rough count, from
the daily cadence: 2 lists x about 1,560 sessions = about 3,100 daily requests, or far fewer if NSE's report allows
date ranges (not verified). Store: event_date = deal date; knowledge_date = deal date by the SEBI rule (an
ASSUMPTION per file unless the file's Last-Modified is kept as evidence); recorded_at = retrieval. Use: a large
holder selling as a label for a B drop; a large buyer as news for A.

### c. F&O ban list, open interest and F&O membership

Search results (unverified, mostly broker pages) describe the ban as open interest above 95% of the market-wide
position limit, lifted below 80%, published each evening; NSE's own documents timed out. Daily files would be about
1,560 per series (ban list, open interest), plus F&O membership by date from the contract files: about 3,000-4,700
requests in all. Store: event_date = the trade date each file applies to (not established; see Codex finding 2);
knowledge_date = file publication, evidenced by Last-Modified; recorded_at = retrieval.

### d. Index changes

- **NSE indices.** Search results show NSE Indices press releases per review as PDFs named by date (for example
  `ind_prs23082024.pdf`, `ind_prs10082026.pdf`); a search summary says the August 2026 release made changes
  effective after the close of 29 September 2026. The PDF timed out (unreadable), so announcement times and
  archive depth are unverified. About 2 semi-annual reviews a year plus ad hoc replacements: roughly 30-60
  documents for 2019-2025. Store as two rows: the announcement (event_date = release date) and the change
  (event_date = effective date), both with knowledge_date = the release date.
- **MSCI.** The index-review page (read) only links to regional review pages. MSCI's terms of use (read) grant a
  limited, revocable licence and prohibit derived works (2(d)(ii)), redistribution (2(d)(iv)) and the use of
  "unauthorized bots, scrapers, crawlers, AI agents" (2(d)(viii)). No further msci.com page was opened. MSCI
  changes should come only from public press releases entered by hand, and even then the terms limit reuse.
- **FTSE Russell.** The ground rules' legal notice (search) says use and distribution of LSEG data requires a
  licence; the ground-rules PDF could not be read. Review schedule and announcement timing are unverified.

### e. Dividend ex-dates from NSE corporate actions

Would replace step 7's text parsing (section 3g: only 6 of 5,604 record-date filings had a parsed amount). NSE's
corporate-actions pages were not reachable, so format, fields (ex-date, record date, purpose, amount), publication
timing and archive depth are unverified. If a date-range report exists, about 75 monthly requests; per symbol,
about 2,700. Store: event_date = ex-date; knowledge_date = the action's announcement or broadcast date, if the
source carries one (evidence to be checked); recorded_at = retrieval.

### f. FII/DII daily flows (lowest priority)

Search results (unverified): NSE posts provisional FII/DII cash-market figures after the close each trading day;
NSDL's FPI report gives depository-confirmed daily figures (SEBI's statistics page, per a snippet, dates the daily
series to 1 June 2014); NSDL has begun daily DII reporting (date not found). These are data pages and were not
opened. About 75 monthly or 1,560 daily requests. Store: event_date = trade date; knowledge_date = publication
(provisional same evening; confirmed later), each vintage kept; recorded_at = retrieval.

### Summary

| Dataset | Use for A | Use for B | Use for C | Label or signal | Known before B's entry? | History back to Oct 2019? |
| --- | --- | --- | --- | --- | --- | --- |
| a. RBI policy days | tag macro-day moves so they are not credited to company news | tag macro-day drops so they are not called unexplained | tag results days that coincide | label | yes, if announced during or before D's session (time not stated on the page) | archive years from 2019-20 exist (contents not opened) |
| a. Union Budget days (incl. 2024 interim and full, Saturday sessions) | as above | as above | as above | label | yes (speech on D) | 2019-20 onward listed (search); dates unverified, site refused the reader |
| a. 2024 election results day | as above | as above | as above | label | yes (counting from 08:00 on D, per the ECI note seen in search) | single event |
| a. NSE holidays and special sessions | session calendar | session calendar; closure bridges | session calendar | label | yes (published in advance; unverified) | not verified (NSE unreadable); store sessions incomplete (P8-070) |
| a. F&O expiry dates | tag expiry-day moves | tag expiry-day drops | tag | label | yes (known when contracts list) | not verified; rule change dated by SEBI 2025/76 (read) |
| a. US Fed decision days | context | tag the next Indian session | context | label | yes for D+1 09:00, if released after India's close (time unverified) | yes, 2019 and 2020 pages read |
| b. Bulk and block deals | a large buyer as news | a large holder selling explains a drop | context | signal (A), label (B) | yes by rule (same day after market hours, read); per-file time unverified | not verified (NSE unreadable) |
| c. F&O ban list | forced-unwinding context | short build-up or unwinding explains a move | context | label | not established (Codex's "next trade date" not re-checked) | not verified |
| c. Open interest, F&O membership by date | context | context | context | label | end of day (unverified) | not verified |
| d. NSE index changes | announcement is news | deletion-day selling explains a drop | tag | signal (A), label (B) | yes (announcement precedes effective date; times unverified) | press releases exist by date (search); depth unverified |
| d. MSCI / FTSE changes | announcement is news | deletion selling | tag | label | yes by announcement | MSCI terms forbid automated collection; FTSE data needs a licence |
| e. Dividend ex-dates | context | replaces step 7 parsing | results often carry dividends | label | yes (announced before ex-date; unverified) | not verified (NSE unreadable) |
| f. FII/DII flows | market context | market context | context | label | provisional same evening (unverified) | NSDL daily FPI from 2014 per a SEBI snippet (unverified) |

What verifying the rest would take: reading the NSE and NSE Indices documentation pages from a client they answer
(they time out for this reader), the Union Budget archive (403 here), and the embedded SEBI 2025 circular PDF; then a
download budget for any dataset chosen. None of that was done.

### URL ledger (19 October 2026, in order)

| Time (IST) | Site | URL | Result |
| --- | --- | --- | --- |
| 11:26:29 | nseindia.com | https://www.nseindia.com/resources/exchange-communication-holidays | UNREADABLE (timeout after 60 s) |
| 11:26:41 | indiabudget.gov.in | https://www.indiabudget.gov.in/bspeech.php | UNREADABLE (HTTP 403 to this reader) |
| 11:27:00 | federalreserve.gov | https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm | READ: 2021-2025 meeting dates with statements; no release time stated; 2019-2020 not on page |
| 11:27:17 | federalreserve.gov | https://www.federalreserve.gov/monetarypolicy/fomc_historical_year.htm | READ: per-year links incl. 2019 and 2020; no timing statement |
| 11:27:37 | rbi.org.in | https://www.rbi.org.in/Scripts/Annualpolicy.aspx | READ: Mar-Oct 2026 entries only; archives by fiscal year 2019-20 onward as links; annual MPC meeting schedule published (2026-27 posted 23 Mar 2026); no announcement time stated |
| 11:28:22 | (web search) | query: SEBI bulk/block deal disclosure same day | search results only, not a page read |
| 11:28:22 | (web search) | query: SEBI 2025 expiry day Tuesday/Thursday | search results only, not a page read |
| 11:28:22 | (web search) | query: NSE F&O ban MWPL next trading day | search results only, not a page read |
| 11:28:22 | (web search) | query: niftyindices semi-annual review press release | search results only, not a page read |
| 11:28:22 | (web search) | query: MSCI quarterly index review India | search results only, not a page read |
| 11:28:22 | (web search) | query: NSDL FPI daily / NSE FII-DII | search results only, not a page read |
| 11:28:41 | sebi.gov.in | https://www.sebi.gov.in/legal/circulars/sep-2005/guidelines-for-execution-of-block-deals-on-the-stock-exchanges_8382.html | READ: MRD/DoP/SE/Cir-19/05, 2 Sep 2005: block deals disseminated 'on the same day, after the market hours'; bulk deals continued same day after market hours (SEBI/MRD/SE/Cir-7/2004, 14 Jan 2004) |
| 11:30:09 | nseindia.com (nsearchives) | https://nsearchives.nseindia.com/content/circulars/SURV64402.pdf | UNREADABLE (timeout after 60 s) |
| 11:31:19 | nseindia.com | https://www.nseindia.com/static/resources/faqs | UNREADABLE (timeout after 60 s); no further NSE pages attempted |
| 11:32:32 | niftyindices.com | https://niftyindices.com/Press_Release/ind_prs23082024.pdf | UNREADABLE (timeout after 60 s) |
| 11:32:58 | (web search) | query: SEBI May 26 2025 expiry day circular (sebi.gov.in only) | search results only |
| 11:32:58 | sebi.gov.in | https://www.sebi.gov.in/legal/circulars/may-2025/final-settlement-day-expiry-day-for-equity-derivatives-contracts_94189.html | PARTLY READ: title, SEBI/HO/MRD/TPD-1/P/CIR/2025/76, 26 May 2025; body (embedded PDF) not visible to the reader |
| 11:33:12 | msci.com | https://www.msci.com/index-review | READ: only links to region-specific review pages; no timing or archive statement; footer links Terms of use (/legal/terms-of-use); '(c) 2026 MSCI Inc. All rights reserved.' |
| 11:33:38 | msci.com | https://www.msci.com/legal/terms-of-use | READ: limited revocable licence; no derived works (2(d)(ii)); no redistribution (2(d)(iv)); no 'unauthorized bots, scrapers, crawlers, AI agents' (2(d)(viii)). No further msci.com pages opened. |
| 11:33:58 | (web search) | query: LSEG FTSE Russell terms / India reviews (lseg.com only) | search results only; ground-rules legal notice: use and distribution of LSEG data requires a licence |
| 11:34:27 | lseg.com | https://www.lseg.com/content/dam/ftse-russell/en_us/documents/ground-rules/ftse-global-equity-index-series-ground-rules.pdf | UNREADABLE (PDF text not extracted by the reader; no PDF tool installed; not worked around) |
| 11:34:49 | federalreserve.gov | https://www.federalreserve.gov/monetarypolicy/fomchistorical2020.htm | READ: 2020 incl. unscheduled 2 Mar (statement released 3 Mar) and 15 Mar; notation votes; no release times |
| 11:35:07 | (web search) | query: ECI 2024 counting date (eci.gov.in, pib.gov.in) | search results only |
| 11:35:07 | (web search) | query: Union Budget dates 2019-2025 (pib.gov.in, indiabudget.gov.in, finmin.gov.in) | search results only; PIB snippet: budget 2019-20 presented 5 July 2019; others not confirmed |
| 11:35:30 | pib.gov.in | https://www.pib.gov.in/PressReleasePage.aspx?PRID=2022466 | UNREADABLE (HTTP 403) |

Pages opened per site: federalreserve.gov 3, indiabudget.gov.in 1, lseg.com 1, msci.com 2, niftyindices.com 1, nseindia.com 3, pib.gov.in 1, rbi.org.in 1, sebi.gov.in 2. Searches are listed for transparency; they are not page reads.

## Appendix. Section 3 and 4 tables before the P8-093 fix (superseded 19 October 2026)

Kept unchanged for comparison; use the tables in sections 3 and 4. These were generated on 19 October 2026 before item 2's calendar was fixed (commit `b72f913`). Headings are prefixed "Before the fix".

#### Before the fix: 3a. Sequential funnel, cut-off 09:00 IST next EQ session, 5-session filing window

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

#### Before the fix: 3b. When the step-2 material filings appeared (all down events, 09:00 cut-off, 5-session window)

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

#### Before the fix: 3c. Unclear filings in the step-3 window, by kind (all down events)

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

#### Before the fix: 3d. Lookback sensitivity (steps 2-3 only; the SEBI-order window stays at five sessions)

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

#### Before the fix: 3e. What is left at the end, by cut-off, lookback, year and turnover band

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

#### Before the fix: 3f. Unknown and unstable inputs, and the notes that remove nothing (all down events, main setting)

| Year | Down events | Market unknown | Peers unknown | Unstable peer ratio | G3 fail | G3 unknown | G5 fail | G5 unknown | ASM active | GSM unknown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | 2,767 | 1 | 2,153 | 49 | 9 | 0 | 732 | 7 | 147 | 2,767 |
| 2021 | 1,272 | 18 | 197 | 18 | 6 | 0 | 186 | 6 | 116 | 1,272 |
| 2022 | 2,249 | 26 | 404 | 104 | 8 | 0 | 393 | 16 | 116 | 2,249 |
| 2023 | 2,616 | 14 | 266 | 85 | 7 | 0 | 439 | 10 | 138 | 2,616 |
| 2024 | 2,456 | 133 | 490 | 110 | 8 | 0 | 136 | 6 | 169 | 2,456 |
| 2025 | 2,635 | 0 | 518 | 23 | 26 | 0 | 440 | 14 | 96 | 2,625 |

Among the events left at the end (main setting): G5 unknown 2020 1, 2021 0, 2022 1, 2023 0, 2024 0, 2025 0; G3 unknown 0 in every year; unstable peer ratio 2020 0, 2021 0, 2022 0, 2023 0, 2024 0, 2025 2.

#### Before the fix: 3g. Dividend parsing (step 7)

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

#### Before the fix: 3h. SEBI orders and the 2025 GSM entry check

SEBI orders in scope: 71 orders (71 rows) known in 2020, 71 without a symbol. None is linked to a stock, so step 4 removes nothing; no link was inferred from company names.

GSM entries in 2025: 94 entry checks for 23 distinct stocks. G5 on the entry day: PASS 1, FAIL 18, UNKNOWN 75 (stocks with at least one pass: 1). The 75 UNKNOWN checks have no usable screening plan, which is not a liquidity pass: 39 had no bar at all on the entry day, 34 traded only in the trade-for-trade BE (22) or BZ (12) series, and 2 had an EQ bar but fewer than the 21 sessions the plan needs.

#### Before the fix: 3i. Reproduction and limits

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

#### Before the fix: section 4 table

| Year | Direction | Events | Material filing overnight | Left out: market moved over 2% the same way | Pool | Previous evening | Closure bridge | Before open | Pool dates | Pool symbols | Pool with market unknown | Would join with Board Outcome or Press Release |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | down | 2,767 | 171 | 36 | 135 | 125 | 11 | 2 | 58 | 128 | 0 | 12 |
| 2020 | up | 7,144 | 244 | 19 | 225 | 198 | 24 | 5 | 103 | 204 | 1 | 61 |
| 2021 | down | 1,272 | 246 | 7 | 239 | 192 | 49 | 3 | 85 | 202 | 4 | 23 |
| 2021 | up | 7,691 | 267 | 11 | 256 | 210 | 43 | 4 | 119 | 218 | 1 | 74 |
| 2022 | down | 2,249 | 199 | 56 | 143 | 115 | 26 | 7 | 65 | 132 | 2 | 156 |
| 2022 | up | 7,055 | 243 | 11 | 232 | 187 | 40 | 9 | 112 | 209 | 2 | 212 |
| 2023 | down | 2,616 | 442 | 25 | 417 | 345 | 69 | 3 | 94 | 353 | 3 | 44 |
| 2023 | up | 9,280 | 439 | 2 | 437 | 376 | 59 | 3 | 126 | 372 | 3 | 116 |
| 2024 | down | 2,456 | 432 | 81 | 351 | 303 | 48 | 0 | 90 | 297 | 15 | 35 |
| 2024 | up | 8,135 | 405 | 8 | 397 | 341 | 51 | 7 | 139 | 347 | 10 | 102 |
| 2025 | down | 2,635 | 298 | 78 | 220 | 197 | 24 | 3 | 85 | 205 | 0 | 270 |
| 2025 | up | 7,394 | 377 | 27 | 350 | 304 | 37 | 13 | 147 | 306 | 0 | 341 |

Totals 2020-2025: 3,402 events in the pool; 1,446 more would join if Outcome of Board Meeting and
Press Release filings counted (both stored spellings of each: "Outcome of Board Meeting" and "...-XBRL", "Press
Release" and "Press Release (Revised)"), under the same window and market rule. The joiners' bins:
2020 down 9/1/2, 2020 up 50/5/6, 2021 down 17/4/2, 2021 up 56/12/8, 2022 down 103/52/6, 2022 up 134/70/11, 2023 down 36/2/6, 2023 up 85/20/13, 2024 down 29/5/1, 2024 up 73/18/12, 2025 down 217/54/6, 2025 up 286/45/17 (previous evening / closure bridge / before open).

Unknown market moves among all events: 2020 down 1, 2020 up 78, 2021 down 18, 2021 up 159, 2022 down 26, 2022 up 130, 2023 down 14, 2023 up 20, 2024 down 133, 2024 up 59, 2025 down 0, 2025 up 0. Most of the down-side ones are the P8-093 sessions (section 3i).
