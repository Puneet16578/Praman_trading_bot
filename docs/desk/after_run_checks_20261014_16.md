# After-run checks, 14 to 16 October 2026 (Part C, read 18 October)

Read-only: logs/weekly_ingest.log, logs/brief_2026-10-14/15/16.txt, the Desk store and the
announcement run folders. No request was made. The user's after-hours Angel run did not happen
(the candle question waits until the IP is registered).

## The three nights

| Night | Started | Finished | Result |
| --- | --- | --- | --- |
| 14 Oct | 19:31:09 IST (not 18:00) | 20:11:06 IST | overall OK; all 14 steps OK |
| 15 Oct | 18:00:01 IST | — | skipped: on battery at 13% (below 30%); no step ran |
| 16 Oct | 20:35:44 IST | — | skipped: on battery at 18% (below 30%); no step ran |

14 Oct steps, all OK: bhavcopy, announcements, isin_map, announcements_recent, corporate_actions,
asm_gsm, bhavcopy_today, circuit_bands, tick_sizes, desk_scan, auto_paper, manual_monitor, brief,
backups. 15 and 16 Oct: no step ran, so none was OK, WARN or FAIL; each wrote the short skip brief.
Consequences for Monday's run: it catches up the data for 15 and 16 Oct; Strategy 0 did not decide
15 or 16 Oct before 09:00 the next weekday, so the next run records those sessions as burn-in gaps.

## Tick sizes (P8-064)

| Session | Master Last-Modified | Fetched | Symbols with a tick | EQ symbols in that day's bhavcopy without one | Changed since the previous night |
| --- | --- | --- | --- | --- | --- |
| 14 Oct | 08:00:07 IST | 19:44 IST | 2,723 | 0 of 2,689 | not applicable (first recording) |
| 15, 16 Oct | — | — | 0 | all (UNKNOWN) | — |

The master is regenerated every morning and only the current copy can be downloaded, so the 15 and
16 Oct ticks stay UNKNOWN for good; the lock rule treats a flat bar on those sessions as possibly
locked.

## Announcements (P8-069)

14 Oct: the bulk refresh (run 20261014T141131312019) was COMPLETE: windows 5-11 Oct and 12-14 Oct,
no failed window, no whole/split mismatch; the open day (14 Oct, 461 filings) was stored without
being certified. Its receipt (through 14 Oct, recorded 14 Oct) certifies through 13 Oct, i.e. D-1:
complete. 1,007 filings inserted, including 13 Oct's, which the PARTIAL 13 Oct night had not stored.
15 and 16 Oct: no refresh ran; the latest certification stays 13 Oct until Monday.

## Price bands (P8-082, P8-083)

The 14 Oct run fetched both lists:

| List dated | NSE Last-Modified | Fetched | Knowledge date stored | Rows |
| --- | --- | --- | --- | --- |
| 13 Oct | 13 Oct 19:00:10 IST | 14 Oct 19:42:49 IST | 14 Oct | 3,570 |
| 14 Oct | 14 Oct 18:22:10 IST | 14 Oct 19:42:51 IST | 14 Oct | 3,570 |

The 13 Oct list appeared at 19:00, after that night's 18:07 request, which confirms the timing
cause. Data health on 14 Oct: "Price bands: OK, list dated 2026-10-14 (3570 rows, published 18:22
IST)". The WARN form never appeared (no brief with the line was written on 15 or 16 Oct). Monday's
run should fetch the lists dated 15, 16 and 19 Oct, each known from 19 Oct.
