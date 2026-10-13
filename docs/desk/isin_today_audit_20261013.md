# Today's ISIN snapshot: local-log audit, 13 October 2026

Requested window: 13 September through 13 October 2026, before tonight's run.
Source: logs/weekly_ingest.log (read-only); related local logs were searched too.
The available ingestion log starts on 22 September; ISIN attempts first appear on
28 September. Absence before that is not a successful request. No NSE fetch was made.

## Confirmed same-day HTTP 404s

| Date requested | Available timing, IST | Evidence |
|---|---|---|
| 28 September | Within the run 13:53:03-14:22:14; exact request time not recorded | Today's dated URL in the HTTPError traceback, log line 46 |
| 3 October (Saturday) | Between preceding step completion 06:22:38.949684 and ISIN completion 06:22:40.459427 | Explicit today's-404 WARN, line 337; step timing at lines 327-328 |

Eleven distinct runs reached an ISIN attempt: 28 September twice; 30 September;
1, 3, 5, 6, 7, 8, 9 and 12 October. Ten have finish summaries. The 1 October run
has per-step progress but no finish or detailed warning retained.

- 2/11 attempts have a confirmed today's-404 (18.2% of logged attempts, not a
  whole-month availability estimate).
- Seven show today's snapshot succeeded: 30 September; 5-9 and 12 October.
  Their WARNs, where present, name fixed historical snapshots only.
- 28 September's later run failed on DNS; this is not an HTTP 404.
- 1 October is indeterminate: a WARN step at 21:24:21.955615 with no retained cause.
- Of nine weekday-evening attempts, zero confirmed today's-404; seven successes,
  one DNS failure, one indeterminate. Both confirmed 404s were outside the normal
  evening publication window (one pre-close, one Saturday morning).

## Decision

There is no evidence that today's snapshot 404 happens on most nights. Do not add
a late-run retry or suppress the warning on these data. The routine recent WARNs
were historical re-download failures, already addressed by P8-060's cache.
If future completed evening logs show today's-404 recurring, propose one bounded
retry later, before any consumers needing the refreshed identity map, recording
both attempt times and statuses. Never turn an unchanged old map into a new build.
The older historical warning text does not expose HTTP status, so those older
HTTPError entries cannot honestly be counted as 404s; P8-060 now adds that status.

Verification: exact error lines, run boundaries and step times were inspected and
counts independently enumerated from the log's summaries/progress records.
No production store, log, cache or ingestion behavior was changed by this audit.
