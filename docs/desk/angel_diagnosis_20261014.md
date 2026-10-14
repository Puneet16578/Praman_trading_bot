# Angel integration diagnosis, 2026-10-14

## Evidence and limits

No authenticated test was run. No credentials were requested, read, stored or printed by this
investigation. SDK/dependency pins, REST allowlist, TLS verification, no-redirect policy, pacing,
and the forward-window firewall remain intact. No strategy or production-store writes.

The initial working tree contained one user edit: the smoke-test date was changed from
2026-09-01 to 2026-10-13. Replaced with session selection rather than reverting its intent.
Baseline: 922 tests in 202.701s, FAILED (failures=2); both smoke-test assertions still expected
2026-09-01. The scheduled ingestion task was checked read-only and was Ready.

### A: Scrip master

Public unauthenticated GET, verified TLS, redirects disabled, complete body decoded in memory:
HTTP 200, 35,325,024 bytes, JSON list, 150,726 records. Running the old record-selection logic
over that response produced zero record exceptions and exactly one unique SBIN-EQ match.
The first sandboxed attempt returned ConnectionError; a permitted public-network check succeeded.
This is evidence of this environment's network boundary, not of the user's earlier failure.

**Original live failure cause unresolved.** The old catch-all discarded the evidence needed to
distinguish timeout, TLS, HTTP, JSON, malformed-record and other failures. Neither endpoint
availability nor a malformed live row can honestly be named as the historical root cause.

**Confirmed code defect, P8-072:** a non-dictionary row or an NSE row with a non-string symbol
aborted the entire master parse. Reproduced offline before the fix. Records are now type-checked;
unusable rows do not crash other mappings. A malformed token for an otherwise eligible identity
blocks that symbol, conflicting tokens remain unmapped, and shared-token identities are rejected.
Tokens must be positive ASCII decimal strings/integers (never bool); exact NSE EQ matching remains.
There is no fallback endpoint, stale disk master, retry, fuzzy match or hardcoded production token.
The in-memory same-day cache remains; failed refresh never becomes today's cache.
GET uses explicit 10-second connect and 60-second read timeouts. These are Requests inactivity
timeouts, not a total transfer wall-clock budget. Full JSON must decode before a map is published.

### B: Candles

The request is NSE, the exact current master token, ONE_MINUTE, a single date formatted
YYYY-MM-DD 09:15 through YYYY-MM-DD 15:30. Angel's documented 30-day maximum for ONE_MINUTE is
the maximum span in one request, not a requirement to choose a date within the last 30 days.
The existing single-day request is within that limit. The existing 4.1-second global request
spacing is below the published candle limits (3/s, 180/min, 5000/h).

Read-only local bhavcopy evidence confirms SBIN EQ traded on 2026-09-01, known by 2026-10-14.
Thus neither the date nor the span establishes the cause of the previous API failure.
**Original live rejection/transport cause unresolved:** its raw response was not retained and
should not now be exposed. Safe HTTP/JSON/structure/API-rejection categories survive the SDK
and login/call boundaries so the next user-run failure can be distinguished.

**Confirmed smoke-test defect, P8-073:** a fixed date becomes stale and a manually updated date
can equal today, which the wrapper deliberately refuses. No reliable forward holiday calendar
exists here. The smoke test now reads the latest stored SBIN EQ session strictly before today,
knowledge_date <= today, at most 14 calendar days old. It does not infer sessions from weekdays
or missing ingestion. Today's store selects 2026-10-13. Missing/stale evidence fails explicitly.
This freshness bound is a local test policy, not a claimed broker restriction. Missing store
sessions can cause selection of an earlier evidenced session; this is not a complete calendar.
Special-session hours are still outside this regular-hours smoke test's scope.

Canonical date formatting is validated before the request; response rows must have six fields.
Empty results fail explicitly. Candle event timestamps stay historical; knowledge_date and
recorded_at describe the current observation. No returns/outcomes are computed.

### C: Streaming

The saved log confirms 7,252 ticks, all 25 symbols, 239.2 of 600 required seconds,
p95 1.5162887 s, p99 1.73216854 s, maximum silence 1.836 s. Latency was below the configured
thresholds; the sole original reason was a generic stream failure. **The exact termination
cause cannot be recovered from that log.** Disconnection, interruption, malformed feed data
and a consumer callback failure remain hypotheses, not findings.

The installed websocket-client implementation of recv() already answers genuine PING frames.
A mock using real ABNF control frames confirmed automatic PONG and an empty-string return on
CLOSE. It is incorrect to claim that the prior wrapper failed to answer every control PING.

**Confirmed diagnostic/bounding defect, P8-074:** recv() discarded frame identity, and its
internal control-frame loop could defer the wrapper's heartbeat/deadline checks on a continuously
busy control-only connection. recv_data(control_frame=True) exposes control frames while retaining
the library's automatic PONG. CLOSE and connection-closed exceptions now have a fixed category;
control PING/PONG never enter the binary tick decoder. Text/binary application `pong` remains
accepted. The existing text `ping` heartbeat is unchanged (every 10 seconds), with receive
timeouts of at most one second and no reconnect loop. Parsing, callback and interruption errors
are separated, and sockets are closed in finally. Consumer exception text is never propagated.
The duration deadline starts after subscription so setup time does not shorten the requested feed.
Synchronous callbacks must return; there is no worker to preempt a blocking callback. Fragmented
data-frame assembly remains delegated to websocket-client.

**Confirmed capacity-check defect, P8-075:** the evaluator did not independently reject an early
clean stream return. The run now passes its required duration to evaluation. Summaries and terminal
output retain only safe failure metadata, not close reasons, payloads or exception messages.
`--only-25` limits an explicitly user-started probe to the 25-symbol tier; the default tier sequence
is unchanged. Exit 0 still means the probe ran, not that a tier passed: inspect its PASS/FAIL result.

## Tests and next steps

New mocked regressions were first run against the original wrapper: five tests produced nine
errors, exposing malformed-row aborts and absent categories. Focused tests cover HTTP errors and
redirect refusal, timeout/TLS/network failure, invalid JSON/shape, exact and ambiguous mapping,
no stale fallback, candle parameters and date/response validation, observed-session selection,
real WebSocket control frames, bounded control-only feeds, callback failure, interruption,
closure, and safe persisted diagnostics. Existing no-write/no-secret and architecture tests remain.
During test development ANGEL-TEST-01 used a Mock without a list-valued `pending`; corrected the
fixture to `Mock(pending=[])` and reran it successfully. No production behavior was changed for it.

Final full suite: `python -B -m unittest discover -s tests -p "test_*.py"`
reported `Ran 936 tests in 187.616s`, `OK`, exit 0. Existing SQLite ResourceWarnings
also appeared in the baseline and are outside this change. Offline setup check passed.
Mock success does not establish live
login, account entitlement, quote/candle availability, or ten-minute stream reliability.

Run privately from D:\Agentic_ai_project\praman:

```powershell
python -u -B scripts\angel_connection_test.py
```

Only after that succeeds, and on explicit user initiation during a confirmed open market:

```powershell
python -u -B scripts\angel_stream_capacity_test.py --only-25
```

Do not run either authenticated test through an agent without separate approval for that test.
Credentials belong only in hidden prompts in the user's private interactive terminal.

## Files changed

- `desk/angel_market_data.py`: guarded master parsing, fixed diagnostic categories, canonical
  candle requests/response shape checks, explicit WebSocket frame handling and cleanup.
- `scripts/angel_connection_test.py`: recent completed-session selection from the read-only store.
- `scripts/angel_stream_capacity_test.py`: safe summary metadata, duration check and --only-25.
- `tests/test_angel_diagnostics.py`: new transport, mapping, calendar, candle and stream regressions.
- `tests/test_angel_connection_test.py`, `tests/test_angel_market_data.py`,
  `tests/test_angel_side_effects.py`, `tests/test_angel_stream_capacity_test.py`: updated smoke/frame
  fixtures and end-to-end mocked probe checks.
- `docs/desk/angel_diagnosis_20261014.md`, `docs/desk/angel_connection_setup.md`,
  `docs/desk/angel_market_data.md`, `docs/DEFECT_REGISTER.md`, `docs/HANDOFF.md`: findings,
  user commands, limitations and verification record.

## Primary references

- [Angel historical API and limits](https://smartapi.angelone.in/docs)
- [websocket-client control-frame behavior](https://websocket-client.readthedocs.io/en/latest/core.html)
- Installed smartapi-python 1.5.5 and websocket-client source inspected locally; no upgrade.
