# 13 October 2026 follow-ups and read-only market data

## A1 - manual time exits

The manual book now follows Strategy 0's order timing: standing stops are checked
across missed sessions, while time exits require an order at the recovery run and
fill only at the following session open. The append-only journal preserves the
order and its session delay; the brief shows pending orders and their delay.
Repeated monitoring cannot replace the frozen order date. The live manual book
has zero trade events, verified read-only; no live journal was changed.

Regression coverage: missed horizon, next-open fill, on-time order followed by
missed runs, stop precedence, gap-through, and duplicate-run safety.


## A2 - same-day bhavcopy wait and calendar limitation (P8-062)

The step now skips without opening a database, requesting a file or sleeping when
it is a weekend, the run started before 15:30 IST, or the run started on another
calendar date. It uses the original run-start timestamp, not the time this late
step happens to execute. At/after close, a same-date weekday run retains retries.

Both this step and Strategy 0's 09:00 cutoff use weekdays. Searches of src/, desk/,
shared/ and scripts/ found observed bar calendars but no forward holiday calendar.
Weekdays are therefore retained: a weekday holiday may still exhaust the wait;
the cutoff may reject on a holiday earlier than strictly necessary. Neither an
absent bar nor an ingestion gap is evidence that a day was a holiday.

Targeted regression: 19 tests in 2.861s, OK (retry and ingestion-progress modules).


## A3 - display freshness (P8-063)

The brief and desk status share ingestion_health_line. Its last *finished* run is
now STALE if its IST finish date predates the previous weekday. Friday stays fresh
through Monday; it is stale on Tuesday. An in-progress run cannot refresh it.
Strategy 0 retains STALE_AFTER_DAYS = 7 and its registered version unchanged.
The previous-weekday proxy has the same holiday limitation as A2: no forward
holiday calendar is stored, and an absent bar is not evidence of a holiday.
A holiday can therefore yield a conservative false STALE. This display never gates
or sizes trades. Tests include UTC/IST and finish-vs-start boundary cases.
Targeted: 35 tests in 1.049s, OK. Full-suite result is in HANDOFF.md.
