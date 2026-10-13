# Recorded fill screen - 13 October 2026

Read-only operational audit requested by the user. No prices, symbols, trade
results, P&L, outcome labels or event-to-later-price changes are reported.
Neither engine nor recorded trades were changed.

| Book | Recorded fill rows | Matching EQ bars | Exactly flat OHLC bars |
| --- | ---: | ---: | ---: |
| Manual | 0 | 0 | 0 |
| Strategy 0 | 4 | 4 | 0 |

The exact-flat screen answers **no, zero**: no recorded fill occurred on an
exactly flat daily bar. This is a screen, not a certification that every fill
was executable. In particular it must not be represented as a completed
implementation of the proposal's tick-tolerant lower-limit test.

The full proposal requires the applicable historical band, verified tick size
and exchange reference/absolute lower limit, including corporate-action resets.
The repository does not contain complete authoritative historical tick/limit
data. Therefore **zero confirmed possibly-locked fills; four unresolved under
the full proposed test**, rather than guessing a tick or claiming a definitive
zero under that broader criterion. Today's Angel master is not proof of a
historical session's tick. No new NSE request was made to fill this gap.

Method: open both production databases through shared.sqlite_readonly.open_readonly
(URI mode=ro); select only symbol/event_date for ENTRY_FILLED and EXIT_FILLED,
and count manual OPEN/CLOSE rows, recorded no later than the audit time. For each
fill select the EQ bhavcopy matching its event_date, knowledge_date <= that date,
recorded_at <= audit time, latest knowledge_date/row_id. SQL returns operational
bar predicates only; no stored execution price, strategy detail JSON or
outcome column is loaded. All four matching bars were present and non-flat.

P8-064 remains open. The existing all-day-lock proposal is unchanged; this audit
does not weaken its tolerance to obtain a reassuring answer. A definitive
yes/no for the full proposal remains blocked by the documented source gap.
