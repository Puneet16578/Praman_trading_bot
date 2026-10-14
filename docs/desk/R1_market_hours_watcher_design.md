# R1 market-hours watcher - proposal, 13 October 2026

APPROVED 2026-10-13 with two changes (see the changelog at the end). Only the
capacity probe, `scripts/angel_stream_capacity_test.py`, is built; the watcher, its
tables and any nightly integration wait for the user's review of the probe's
results. No scheduled task. NSE RSS requests need separate approval with a budget.

**Note, 14 October 2026:** R1 must not depend on Angel's historical candles during market
hours; intraday one-minute bars come from the stream. See the changelog's 2026-10-14 entry.

## Lifecycle and sources

The user starts `.\desk live` in a private terminal each trading morning,
preferably by 08:40 IST. It checks master and clean relevant inputs, records HEAD
and input hashes, refuses to start alongside an active nightly, requests the
Part B wrapper's hidden login prompts, and runs until 15:45. No credentials or
tokens enter any log, table or exception report. Only the wrapper imports the SDK.
One broker client process per account; no orders, GTT, account positions,
holdings or funds calls. Books below mean Praman's local paper books only.

At 08:50 it writes `logs/premarket_<date>.txt`. A later launch writes a clearly
LATE report immediately, recording the unobserved interval; it never backdates
detection or claims to have met the deadline. At 15:45 it stops collection,
closes the socket, logs out, writes `logs/live_<date>.txt` and exits. Interruption
does the same best-effort cleanup and marks the report incomplete. A resumed
laptop after 15:45 finalizes immediately. No scheduled launch or wakeup.

| Source | Cadence and use | Coverage limit |
| --- | --- | --- |
| `https://nsearchives.nseindia.com/content/RSS/Online_announcements.xml` | Every 90 seconds | RSS is not an authoritative complete historical archive |
| `https://nsearchives.nseindia.com/content/RSS/Financial_Results.xml` | Every 90 seconds, staggered 30 seconds | Deduplicate overlaps with announcements |
| `https://nsearchives.nseindia.com/content/RSS/Board_Meetings.xml` | Every 90 seconds, staggered 60 seconds | Meeting notices are distinct from subsequent results |
| Existing exchange announcement ingestion source | Startup reconciliation from last finished nightly's coverage watermark to now, into the new watcher store only | Required to cover filings that aged out of RSS; incomplete retrieval is a visible coverage gap |
| Existing NSE surveillance, price-band and corporate-action sources | Startup refresh; reconcile with latest locally known snapshots | Effective dates and publication dates differ; missing fresh evidence means UNKNOWN, not unchanged |
| Angel public master | Once per process/day through wrapper | Exact NSE EQ mapping; list missing/ambiguous symbols |
| Angel FULL quote | Once per newly detected filing; bid, ask, last, cumulative volume | Rate-limited snapshot arrives after detection; record actual delay |
| Angel LTP stream | Continuous during regular market hours | Initial 100 liquid symbols; capacity measured, not assumed |

RSS requests send saved ETag/If-None-Match and Last-Modified/If-Modified-Since.
304 is a successful unchanged check, not a new filing. Bound request duration,
respect Retry-After on 429/503, and record any interval exceeding the intended
cadence. Do not bypass a block or silently swap to an undocumented source.
Persist response hashes and source receipt metadata; redact query parameters
from error records. NSE endpoints have not been requested or verified in this
session. Their use needs the user's network authorization before implementation
testing; the already approved Angel public reads do not cover them.

Reconciliation uses the last finished nightly's actual source coverage, not just
its finish timestamp. The premarket report separately lists every newly known
filing in that interval, surveillance/band/action changes effective today, and
all such filings matching either local book's open symbols as of detection.
Reuse `src.signals.disclosure_classification.classify_category` and retain raw
category; unknown categories remain explicitly UNMAPPED instead of guessing.
Local book reads expose identity/open-state only, not sealed outcome columns.

The repository has no forward trading-holiday calendar. Initially distinguish
weekday eligibility from confirmed open status using fresh exchange timestamps;
show calendar coverage UNKNOWN and do not infer holidays from missing data.
Special sessions require explicit dated exchange-calendar support. Effective
price bands use the preceding report's documented applicability (report D is
for the next session); no guessing across missing sessions or corporate actions.

## Detection, snapshots and observations

Timestamp an RSS receipt immediately when received. Preserve the exchange's
original timestamp, parse status/timezone, first detection time, and processing
time separately. Detection latency is detection minus exchange publication;
negative/unknown values are clock/source anomalies, not clamped to zero.
RSS publication delay is part of that measured latency. Source reconciliation
discoveries retain their later actual detection time.

One logical filing identity uses exchange ID/GUID where available, otherwise a
documented hash of source identity fields. Revisions are new versions, linked to
the original; repeated receipts remain auditable without repeated snapshots.
At detection enqueue exactly one quote attempt. Record request start, receipt,
exchange quote timestamp and age, bid/ask/last/cumulative volume. Missing token,
timeout, stale quote or throttle delay is recorded as such. Never relabel a later
quote as the price at detection. Never backfill a missing detection snapshot
with candles or a subsequent tick. Four-second global REST spacing means a burst
can queue; the report exposes queue delay and missed snapshots rather than
claiming simultaneous measurements. Batching multiple newly detected identities
is a possible later wrapper extension, not an existing B capability.

Liquidity membership uses trailing turnover known before today's open, with
coverage requirements and deterministic tie-breaking. It is a resource allocation
list, not a recommendation or suspicion score. Every observed tick carries the
exchange timestamp and actual local receipt time. No trade or paper engine runs.

Unusual-observation rules must be predeclared and versioned: compare today's
price or volume with baselines known before today (yesterday's close, a trailing
average of earlier sessions). That is event detection, the same as the nightly
desk scan already does at the close, and it is allowed for every symbol,
including symbols with protected events (firewall rule below). Cause defaults to
UNKNOWN. A filing detected in the same session can be listed beside an
observation as context, never asserted to have caused it; a filing from an
earlier day is never shown beside today's observation, because that pairing is a
change measured from the filing's date.

## Append-only, bitemporal storage

Use a new `data/live/live.sqlite`, owned exclusively by the watcher process.
No writes or schema changes to Praman or Desk stores. WAL and small bounded
transactions apply only to this new database. Existing-store reads are short,
read-only snapshots released before network work; a busy store produces a gap
instead of waiting while holding a lock. All fact tables reject UPDATE/DELETE.
Corrections and run-state changes append linked rows. Every fact has event_date,
knowledge_date and `recorded_at` (real detection/receipt time, UTC); also retain
full event_at/known_at timestamps. Queries require an as-of timestamp and filter
known_at AND recorded_at against it. IST is presentation only. Missing event
time has an explicit status; it is never fabricated from a receipt time.

| New table | Contents |
| --- | --- |
| `live_runs` | Append-only lifecycle records: run ID, start/stop/recovery state, code SHA, configuration hashes, source watermarks |
| `live_source_receipts` | Feed/source, requested/received times, status, validators, payload hash, coverage bounds, sanitized failure code |
| `live_filings` | Identity/version, symbol, exchange publication, first detection, raw category, existing classifier result, receipt reference |
| `live_filing_snapshots` | One attempted detection snapshot per filing version, quote times/age, raw bid/ask/last/volume or failure; never a subsequent-price series |
| `live_minute_bars` | One-minute bars built in memory from the stream: symbol/token, minute start (exchange time), open/high/low/close of the last traded price, tick count, first/last exchange and receipt timestamps, receipt-lag summary; no raw ticks |
| `live_quote_rotation` | The 15-minute FULL quote rotation: slot, symbol, request/receipt times, quote age, bid/ask/last/cumulative volume or failure; skipped/late slots recorded |
| `live_effective_changes` | Surveillance/band/action source, effective date, publication/detection, old/new source references, explicit coverage state |
| `live_observations` | Predeclared observation type, baseline reference, detection measurements, cause UNKNOWN/context references, firewall decision; no outcome fields |
| `live_gaps` | Source/process gap start/end events, reason, clock uncertainty, resolution reference; no rewriting an open gap |
| `live_report_artifacts` | Report kind/version/path/hash, generated time, coverage and completion state |

The canonical tables remain append-only. The two requested log paths are written
once per day. If a restart requires a correction, append a timestamped correction
section and register its new artifact hash; do not erase the first report.

Raw ticks are not stored. The watcher folds each tick into its symbol's current
one-minute bar in memory and writes the bar once the minute has closed (a tick
for a later minute, or the minute's end plus a short grace on the local clock).
A tick arriving for a minute already written is counted as late in the next bar
and in `live_gaps`; a written bar is never rewritten. Stored alongside the bars:
the filing snapshots and the 15-minute quote rotation. Raw ticks exist only in
the capacity probe, in its own file, to measure capacity and storage. Bound
in-memory work; on saturation record dropped counts and intervals explicitly.
Once `live.sqlite` exists, it is added to the nightly backups with restore
verification against its own manifest, as the logs folder is; that is a separate
change to `desk/backups.py` with its own tests.

## Forward-window firewall

Reuse `desk/outcome_firewall.py` as the single date-policy authority:
events on/after 2026-09-16 are protected while market_today() < 2027-06-01.
Check BEFORE any outcome query or calculation, not only in rendering. Do not
modify the frozen pipeline/pre-registration or create another calendar boundary.

The firewall line (user decision, 2026-10-13):
- Allowed for every symbol: comparing today's price or volume with baselines
  known before today (yesterday's close, a trailing average). That is event
  detection, as the nightly desk scan already does at the close.
- Never compute, store or display a change measured from an earlier event's or
  filing's date (a post-filing return, best or worst later price, event-window
  volume, P&L, an outcome label), and never join live observations to catalogue
  events dated on or after 2026-09-16.
- The firewall also covers research reads of `data/live/live.sqlite`: no query
  may join it to those events before 2027-06-01. The watcher's own query layer
  enforces it, and any research reader must go through the same guard.

Snapshot receipt lag is an operational latency, not a price change. No
retrospective recomputation or causal relabelling of recorded observations.
Do not open access merely because a synthetic as-of query is dated in 2027;
the actual market clock controls the existing firewall.

Required implementation tests (not implemented by this design-only task):

1. Both sides of the firewall line: a same-day flag (today against yesterday's
   close or a trailing average) works for a symbol with a protected catalogue
   event; any change anchored on an event's or filing's date, and any join of
   `live.sqlite` to a catalogue event dated on or after 2026-09-16 before
   2027-06-01, fails before a loader or evaluator is called.
2. Boundary dates 2026-09-15/16 and actual dates 2027-05-31/06-01, with UTC/IST
   rollover and forged future as-of. Existing firewall remains authoritative.
3. Source/category corrections and late arrivals cannot create an event-anchored
   change or join; raw observations remain correctly timestamped.
4. Every query is as-of filtered; a restart cannot backdate detections, duplicate
   a snapshot or overwrite a fact. UPDATE/DELETE attempts fail.
5. Inject sleep, clock jumps, network disconnect, queue overflow, 429, malformed
   RSS, stale quote, unmatched symbols and early nightly start: gaps are visible,
   finalization bounded, credentials absent, both existing stores unchanged.
6. Dirty/untracked runtime input, non-master HEAD or changed code after startup
   prevents/ends collection. Architecture tests retain Part B's SDK/order bans.

## Reliable streaming limit and foreground concurrency

`scripts/angel_stream_capacity_test.py` (built 2026-10-13; run by the user after
the connection test passes) is the only place raw ticks are kept, in its own
file under `data/live/probe/`. The user runs it manually during a liquid part of
a trading day with a clean tree on master and their login. Probe 25, 50, 100, 200, 300, 500, 750, then at most 1000 tokens,
one connection at a time, ten minutes per tier, ending no later than 15:45.
Stop escalation on failed tiers, disconnect, growing queue or missing heartbeat.
No outcomes, trades, account calls or nightly writes. Record raw receipt metrics:
subscription acceptance, per-token coverage, exchange-to-receipt latency,
disconnects, queue occupancy/drop count, CPU, memory and disk throughput.
Normal lack of trading is distinct from a feed gap: compare liquid sentinel
symbols, heartbeat and sequence evidence; do not promise every symbol ticks.

Initial operational pass targets: no unexplained disconnect or dropped tick,
bounded queue with no sustained growth, p95 receipt lag under 2 seconds and p99
under 5 seconds where exchange timestamps are valid. These are proposed quality
targets, not observed performance. Run more than one market period/day before
choosing capacity; default to 100, then at most 80% of the smallest repeatably
passing maximum. Never exceed the explicit provider cap while measuring.

Official forum specifies 1000 token-mode subscriptions per connection and three
connections per client:
https://smartapi.angelone.in/smartapi/forum/topic/1861/user-feedback-websocket-2-0-beta-rollout-python-language/1
Forum reports about a few hundred versus no additional cap do not establish
laptop/account reliability. The current wrapper permits one LTP connection.
It does not yet expose streaming volume; initially rotate FULL snapshots over
the default 100 symbols every 15 minutes (400 requests/hour), with new filing
snapshots taking priority and the wrapper's global budget always binding. Record
skipped/late rotation slots. Volume observations then have a 15-minute target
cadence, not tick precision; increasing the universe cannot increase that load
without a new measured budget. Quote-mode streaming would require a reviewed extension
to that same allowed market-feed capability and tests, not a second SDK import.

The current B wrapper's bounded stream call is foreground and blocking. R1 needs
one foreground event loop that services RSS, quote queues, socket reads and disk
writes with bounded work per iteration. Refactor private transport into cooperative
steps behind the same seven public capabilities during R1 implementation; do not
silently add threads or use 30-second reconnect cycles as a polling mechanism.
This is an explicit dependency of R1, not a feature already delivered by B.

## Laptop and nightly isolation

Reuse the nightly's Windows sleep-prevention approach (`_prevent_sleep`), factored
into a shared helper only in the separately approved R1 implementation. Restore
the OS setting on exit. Record foreground heartbeat, wall/monotonic clock changes
and resume evidence; sleep prevention cannot guarantee power/network availability.
Any unexplained heartbeat gap is logged as such, not silently classified as sleep.

Before start and periodically while running, inspect nightly task/process state
read-only; stop immediately if it becomes active, or if verification fails. Never
write task settings. Hard stop 15:45 leaves over two hours before the 18:00 nightly.
Use separate OS processes and separate writable databases, no shared write lock.
Code and dependency hashes are recorded and checked; changes cause safe shutdown.
Reuse the nightly dirty-input/master guard for both commands, extending its input
coverage for the optional Angel requirements in R1, with tests. B itself does not
alter that guard or the nightly. No edits or suite execution during either run.

## Requested log formats

Illustrative placeholders only, not observations from today's market:

```text
PREMARKET <date> generated <08:50 IST> run=<id> code=<sha>
Coverage: last finished nightly <time/status>; reconciled through <time>
Calendar/source coverage: <complete/UNKNOWN and reason>; launch <on time/LATE>
Filings since watermark: <count>; category mapping gaps: <count>
<symbol> exchange=<timestamp> seen=<timestamp> category=<raw> class=<existing class>
  Local books: <manual/Strategy 0/neither>; document=<exchange link>
Effective today: <surveillance change / circuit band / corporate action + sources>
Unmapped Angel symbols: <list>; stale/missing sources: <list>
Forward firewall: active; same-day flags only; no event-anchored changes or joins
```

```text
LIVE <date> stopped <15:45 IST> run=<id> code=<sha> status=<complete/incomplete>
Observed interval <start/end>; feeds checked <counts>; 304 <counts>; errors <counts>
New filings <count>; revisions <count>; unmapped categories <count>
<symbol> exchange=<time> detected=<time> latency=<seconds or UNKNOWN>
  snapshot received=<time> exchange=<time> age=<seconds> queue=<seconds>
  bid=<raw> ask=<raw> last=<raw> volume_so_far=<raw or unavailable>
Observations: <raw/unusual type if permitted> detected=<time> cause=UNKNOWN
Stream: <subscribed count>, <coverage>, receipt-lag p50/p95/max=<values>
Filing latency: p50/p95/max=<values>; unparseable/negative timestamps=<count>
Gaps: <start/end, source, reason, uncertainty, dropped count>
Firewall: <suppressed count/reasons>; no post-filing price changes or outcomes
Logout: <completed/failed>; report/table reconciliation: <counts/hash>
```

## Changelog

**2026-10-13 — approved with two changes (user decision in their message of
2026-10-13).**
- Firewall line. Before: all derived move and volume comparisons were suppressed
  for symbols with protected events, and for the whole universe when event
  coverage was uncertain. After: same-day comparisons with baselines known before
  today are allowed for every symbol; changes measured from an earlier event's or
  filing's date, and joins of live observations (including research reads of
  `live.sqlite`) to catalogue events dated on or after 2026-09-16 before
  2027-06-01, are never computed, stored or displayed. Tests cover both sides.
- Storage. Before: every tick stored in `live_market_ticks`. After: one-minute
  bars built in memory and stored, plus the filing snapshots and the 15-minute
  quote rotation; raw ticks only in the capacity probe. `live.sqlite` joins the
  nightly backups, with restore verification, once it exists.
- Approved as proposed: the isolated store, the cooperative single-loop wrapper
  refactor and the startup reconciliation.
- Built now: only `scripts/angel_stream_capacity_test.py`, with offline tests.
  The watcher waits for the user's review of the probe's results. NSE RSS
  requests need the user's approval with a stated budget when reached.

**2026-10-14 — note (user decision in their message of 2026-10-14). Design only;
nothing is built.**
- Observed today: Angel refused getCandleData during market hours twice, each time on a
  single request: 11:22 IST (HTTP 403, reply not examined by that code) and 15:21 IST
  (HTTP 403, confirmed RATE_LIMITED, Angel's "exceeding access rate" reply), both for SBIN
  ONE_MINUTE. Login, quote and the live feed worked in the same runs; the 25-symbol feed
  tier passed for 600 seconds at 15:04-15:14. Every run came from a public IP that is not
  the one registered with Angel.
- So R1 must not depend on historical candles during market hours. Intraday one-minute
  bars come from the stream (built in memory, as approved on 2026-10-13); candle requests
  run only outside market hours.
- Still being tested: whether candles are reliable outside market hours, and whether the
  unregistered IP plays a part. Evidence: docs/desk/angel_candle_403_20261014.md.
