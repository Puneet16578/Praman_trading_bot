# Private terminal setup for the Angel connection check

Use your own PowerShell terminal. Do not paste keys, login details or tokens into
chat. If a real key has been shared, revoke/rotate it first. The agent has never
logged in or read a key.

## 1. The Angel library (installed 2026-10-14)

The nightly's Python, `C:\Users\VICTUS\AppData\Local\Programs\Python\Python313\python.exe`
(3.13.6; the scheduled task runs the `pythonw.exe` beside it), now has the pinned
library: `smartapi-python` 1.5.5 (wheel SHA-256 `32991f41...45ff7d`, the reviewed
one) and `logzero` 1.7.0 (`23eb1f71...08769d`). A `pip --dry-run` first showed these
two as the only changes, both new; its other needs (`websocket-client` 1.8.0,
`requests` 2.32.4, `six` 1.17.0, `python-dateutil` 2.9.0.post0) were already
installed and unchanged. They were installed hash-checked with `--no-deps`.
`requirements-angel.txt` pins these exact versions. Do not install or update
packages while the nightly runs.

## 2. The lines to type, in order

Each line on its own. The key goes in through a hidden prompt, lives only in this
window's environment (never `setx`, never typed on a command line), and is
removed at the end.

```powershell
Set-Location 'D:\Agentic_ai_project\praman'
$pramanPython = 'C:\Users\VICTUS\AppData\Local\Programs\Python\Python313\python.exe'
& $pramanPython -B .\scripts\angel_connection_test.py --check
$angelKeyInput = Read-Host 'Angel API key' -AsSecureString
$angelKeyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($angelKeyInput)
$env:ANGEL_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($angelKeyPointer)
[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($angelKeyPointer); $angelKeyInput.Dispose(); Remove-Variable angelKeyInput, angelKeyPointer
& $pramanPython -B .\scripts\angel_connection_test.py
Remove-Item Env:\ANGEL_API_KEY
```

`--check` confirms the setup without logging in and without reading the key; it
must end "Setup ready for the connection test." The full test then asks for your
client ID, PIN and current TOTP in three hidden prompts.

`-B` prevents Python bytecode-cache writes. The wrapper avoids the SDK's log
constructors and its public-IP, DNS and hardware probes. It sends both IP headers
as `127.0.0.1`, and MAC `00:00:00:00:00:00`.
On 2026-10-14 the candles worked at 08:10 (for 2026-09-01) and returned HTTP 403 at 11:22
(for 2026-10-13), with login and quote working both times. The cause is not known. Angel's
Moderator_3 wrote on the forum on 7 Oct 2026 that "Static IP is required to access any
smartAPI" (topics 5679 and 5671); the wrapper does not discover or guess an address. See the
[historical 403 investigation](angel_candle_403_20261014.md) for the differences between the
two runs and what the next runs would show.

## 3. What it prints

On success, after the prompt labels:

```text
<quote timestamp> <SBIN last price>
Candles SBIN 2026-09-01: <bars> bars, first <HH:MM>, last <HH:MM>; open <o>, high <h>, low <l>, last <c>; missing minutes 09:15-15:29: <none | count (ranges)>
<live exchange timestamp> <SBIN live price>
...live ticks for 30 seconds, if open...
Connection test completed: login, quote, candles, ... and logout.
```

These are format placeholders, not actual prices. The script fetches one day of
ONE_MINUTE candles from 09:15 to 15:30 IST for the fixed session **2026-09-01** (one request,
no retry) and prints one summary line, not every bar. To ask for another day:

```powershell
python -u -B scripts\angel_connection_test.py --candle-date 2026-09-15
```

It accepts only a completed session before 2026-09-16 (the forward window's start) that the
local store holds for SBIN EQ; it reads the store without writing. Anything else stops before
login: `Stopped before login: --candle-date refused: <why>`. The broker decides which bars exist;
"missing minutes" lists the minutes from 09:15 to 15:29 with no bar.

On failure it prints a plain stop line and exits `1` (P8-071: it used to exit silently).
A candle failure prints the request and whether the market was open at that moment. Examples:

```text
Stopped before login: Angel library not installed or incomplete: smartapi-python (not installed: see setup step 1)
Stopped at login: ANGEL_API_KEY is not set in this window: see setup step 2
Stopped at login: login failed: check the client ID, PIN, TOTP and API key; Angel may also refuse the 127.0.0.1 IP headers (not yet verified)
Stopped at quote: HTTP failure (HTTP 503).
Candle request: NSE SBIN ONE_MINUTE 2026-09-01 09:15-15:30 IST, one request, no retry.
Stopped at candles: RATE_LIMITED (Angel's "exceeding access rate" reply) (HTTP 403). Market open at that moment: yes (weekday 09:15-15:30 IST with a fresh quote).
Stopped at candles: Access denied; cause unclassified (HTTP 403). Market open at that moment: no (weekday 09:15-15:30 IST with a fresh quote); see docs/desk/angel_candle_403_20261014.md
Stopped at live feed: WebSocket disconnected.
Feed close: by <server|client|connection_lost>, code <n|none>, reason <kind> (<n> bytes, text never shown); connected <s>; since last message <s>, PING sent <s>, PONG back <s>, text ping <s>, text pong <s>; frames {...}
```

RATE_LIMITED means the reply was exactly Angel's throttling phrase; the reply itself is never
printed. No raw error, response, token, header or credential is ever printed, and nothing
is saved to a log or store.

When the market is closed, the quote and historical candles still run; only the
30-second stream is skipped, and the last line says so. The open proxy requires a
weekday, 09:15 <= IST time < 15:30, and an exchange quote timestamp no more than
120 seconds old. Holidays and special sessions are not authoritatively resolved
because the repository has no forward calendar.

Logout is attempted on success, failure or interruption. The user has confirmed a
successful login/quote; historical access remains unresolved. No authenticated test
has been run by the agent. Do not proceed to capacity testing until candles succeed.
