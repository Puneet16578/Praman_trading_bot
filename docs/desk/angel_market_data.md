# Angel market data: read-only boundary

## Scope and installation

Optional requirements: requirements-angel.txt, smartapi-python==1.5.5. No nightly
import or step, scheduled job, live store write or credential file is added.
No package was installed during this session. Public package/source/master reads
were approved; authenticated calls are for the user to run in their terminal.
Installation, if needed in that terminal: `python -m pip install -r requirements-angel.txt`.
Do not paste credentials in chat, command arguments, configuration files or fixtures.
Set ANGEL_API_KEY in the terminal's process environment using a private mechanism.
Client ID, PIN and TOTP are getpass prompts; echoed-input fallback is refused.

The seven public methods of desk.angel_market_data.AngelMarketData are login,
logout, profile, quote, candles, stream and download_scrip_master. There is no
SDK handle in the public interface, generic forwarding method or order/account
operation. Private implementation state is not a sandbox against malicious Python;
repository guards and the allowlisted HTTP dispatcher enforce authorized code.

Login reuses a same-day in-memory session. At IST midnight reads/streaming fail
closed and local session state is discarded; the next login prompts again. There
is no refresh-token endpoint. Separate process invocations necessarily log in anew:
no credentials/session state is persisted to enable reuse across processes.
Logout attempts the approved endpoint and clears memory even if that call fails.
Python cannot guarantee byte-level memory zeroization; values are never persisted.

## SDK and transport review

Official source: https://github.com/angel-one/smartapi-python
Published package: https://pypi.org/project/smartapi-python/1.5.5/
Reviewed wheel: smartapi_python-1.5.5-py3-none-any.whl, SHA-256
`32991f413134f773d29a09762660d8a93026c4820bb8881a68ca48be9e45ff7d`.

The pinned SDK performs an unrelated public-IP GET at import and its constructors
create logs. Its error dispatcher includes headers and request parameters in logs.
The wrapper blocks that import-time GET, mutes vendor logging, bypasses the unsafe
constructors, and overrides HTTP dispatch in a private SDK subclass. Official
session, profile, quote, candle methods and feed decoding/subscription framing
are reused. Only five REST routes and their exact verbs are permitted. HTTPS
certificate verification is required, redirects are refused, timeouts bounded,
and all external errors become static messages with suppressed exception context.
Authenticated REST transport also suppresses configured HTTP debug output and
standard logging (the profile URL contains a token), restoring settings on exit.
Websocket trace is disabled before connection. These controls assume this
standalone foreground client, not concurrent unrelated application threads.
The SDK's existing fallback IP headers are retained without an external IP lookup.
Actual account/IP-policy compatibility remains for the user's connection test.

Rate-limit source (official SmartAPI Team table):
https://smartapi.angelone.in/smartapi/forum/topic/4387/changes-in-api-rate-limit/5
Login/logout 1/second; profile 3/second and 1000/hour; quotes 10/second,
500/minute, 5000/hour; candles 3/second, 180/minute, 5000/hour.
The direct documentation page was not readable in this environment; the official
forum table was available. The wrapper uses a conservative 4.1-second spacing
across **all** REST requests, including the profile call inside login and failures,
under 879/hour. No retry bursts. Limits are per process: run one client process
per account; other applications using that account consume the same provider quota.
Public scrip-master downloads also use the spacing and cache in memory for the day.

Stream: one foreground connection and at most 1000 distinct NSE EQ tokens in LTP
mode, no reconnect/helper thread/timer. Finite socket reads and a monotonic deadline
stop even a quiet feed; close runs in finally, including interruption/midnight.
Official 1000 token-mode subscriptions/connection and three connections/client:
https://smartapi.angelone.in/smartapi/forum/topic/1861/user-feedback-websocket-2-0-beta-rollout-python-language/1
Some forum wording says no additional cap; use the explicit quota conservatively.
Actual reliable capacity must be measured (R1 design), not inferred from that cap.

## Identity and point-in-time data

Master source:
https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json
Only exact NSE `SYMBOL-EQ` rows, without an expiry/derivative instrument type, map.
Duplicate conflicting tokens and absent symbols are returned in `unmapped`.
There is no fuzzy/ISIN/name fallback, suffix substitution or guessed token.
SBIN maps to 3045 in the public snapshot read this session.

Read-only comparison with Praman's 2026-10-12 EQ universe: 2696 symbols,
2694 unique matches; unmapped: **CCAVENUE, MOREPENLAB**. The broader historical
identity map has 3341 names and 640 unmapped/ambiguous names; those include delisted
and renamed names and are not the current EQ denominator. No local map was changed.

All read methods require as_of=today in IST. Current endpoints/master cannot
answer historical knowledge queries. Historical one-minute candles retain event
timestamps but have knowledge_date=today and actual recorded_at; current tokens
are not asserted to be a historical identity master. Quotes expose price, bid,
ask, cumulative volume and timestamps only; SDK percentage/net-change fields and
credentials are dropped. Profile returns exchange permissions only, not client ID
or session tokens. No price changes, returns, filing-linked follow-up prices or
outcomes are computed. Future consumers must use the existing outcome firewall;
raw access is not permission to derive forward-window outcomes.

## Verification and remaining limits

Tests mock the SDK/HTTP/feed: import and forbidden-function guard; exact public
surface; deny before network; throttling; getpass/session expiry; sanitized errors;
no constructor logging; exact/ambiguous mapping; candle date checks; TLS/redirect
settings; raw tick filtering and bounded quiet-feed cleanup. No real credentials
or authenticated responses are in fixtures. Values used to exercise redaction are
random synthetic values created only in test memory.

No authenticated Angel endpoint has been called by the agent. Live account access,
permissions, IP restrictions, historical availability and live-feed reliability are
DOCUMENTED, NOT VERIFIED until the user runs scripts/angel_connection_test.py.
Part C is a design only; no live watcher or additional store exists.

## User-terminal connection check (B3)

After installing the optional requirements and privately setting ANGEL_API_KEY,
run `python scripts/angel_connection_test.py` in your own interactive terminal.
It prompts privately, prints one SBIN quote, then raw OHLC prices/timestamps for
2026-09-01 one-minute candles. During regular weekday hours, a fresh exchange
quote (at most 120 seconds old) enables 30 seconds of live SBIN prices, then it
logs out. Otherwise streaming is skipped. No holiday calendar exists: this is
a conservative open-market proxy, not special-session/calendar verification.
Missing/stale exchange timestamps do not imply that the market is open.

Output is prices and timestamps only (apart from necessary hidden-input prompt
labels). Exit code 0 means the requested operations completed; 1 means a failure
or interruption. Raw errors and credentials are never printed. In PowerShell,
inspect `$LASTEXITCODE` after it exits. It writes no store or log file and always
attempts logout. The agent has not run this authenticated connection check.
