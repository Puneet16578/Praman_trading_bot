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
**It is not verified whether Angel accepts `127.0.0.1` in these IP headers.**
No authenticated call has been made; if the account requires a real or
registered IP there, login will fail. The wrapper does not query an
unapproved IP-discovery service or guess a real public address.

## 3. What it prints

On success, after the prompt labels:

```text
<quote timestamp> <SBIN last price>
<completed-session minute timestamp> <open> <high> <low> <close>
...one line per returned minute...
<live exchange timestamp> <SBIN live price>
...live ticks for 30 seconds, if open...
Connection test completed: login, quote, candles, ... and logout.
```

These are format placeholders, not actual prices. The script fetches one day of
ONE_MINUTE candles from 09:15 to 15:30 IST for the latest locally evidenced SBIN EQ
session before today, known by today and within 14 calendar days. It reads the local
Praman store without writing. Missing/stale session evidence stops the test explicitly;
weekdays are not assumed to be trading days. The broker determines which bars are available.

On failure it prints one plain line saying why it stopped, and exits `1`
(P8-071: it used to exit silently). Examples:

```text
Stopped before login: Angel library not installed or incomplete: smartapi-python (not installed: see setup step 1)
Stopped at login: ANGEL_API_KEY is not set in this window: see setup step 2
Stopped at login: login failed: check the client ID, PIN, TOTP and API key; Angel may also refuse the 127.0.0.1 IP headers (not yet verified)
Stopped at quote: HTTP failure (HTTP 503).
Stopped at candles: API rejection.
Stopped at live feed: WebSocket disconnected.
```

No raw error, response, token, header or credential is ever printed, and nothing
is saved to a log or store.

When the market is closed, the quote and historical candles still run; only the
30-second stream is skipped, and the last line says so. The open proxy requires a
weekday, 09:15 <= IST time < 15:30, and an exchange quote timestamp no more than
120 seconds old. Holidays and special sessions are not authoritatively resolved
because the repository has no forward calendar.

Logout is attempted on success, failure or interruption. Live authentication, IP
acceptance and historical availability remain DOCUMENTED, NOT VERIFIED until you
run this check.
