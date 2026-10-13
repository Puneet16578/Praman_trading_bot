# Private terminal setup for the Angel connection check

Use your own PowerShell terminal. Do not paste keys, login details or tokens into
chat. If a real key has been shared, revoke/rotate it first. These commands are
instructions for you; the agent has not installed packages or logged in.

## 1. Use the same Python installation as Praman

Verified locally: `python` resolves to the Python313 installation below; the
nightly uses its adjacent `pythonw.exe`. No separate virtual environment is used
by the scheduled task. Install the optional dependencies with that exact Python:

```powershell
Set-Location 'D:\Agentic_ai_project\praman'
$pramanPython = 'C:\Users\VICTUS\AppData\Local\Programs\Python\Python313\python.exe'
& $pramanPython -m pip install -r .\requirements-angel.txt
& $pramanPython -B -c "import importlib.metadata; print(importlib.metadata.version('smartapi-python'))"
```

The version check must print `1.5.5`. Installation requires network and writes
installed packages; the no-file-write claim concerns the connection check, not
package installation. Do not install/update dependencies while the nightly runs.

## 2. Set the API key privately for this terminal only

Do not put a literal key in a command or use `setx`: the former can enter shell
history and the latter persists it in the Windows environment registry. This
hidden prompt sets only the current process environment, inherited by Python:

```powershell
$angelKeyInput = Read-Host 'Angel API key' -AsSecureString
$angelKeyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($angelKeyInput)
try {
    $env:ANGEL_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($angelKeyPointer)
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($angelKeyPointer)
    $angelKeyInput.Dispose()
    Remove-Variable angelKeyInput, angelKeyPointer
}
& $pramanPython -B -c "import os; print(bool(os.environ.get('ANGEL_API_KEY')))"
```

The visibility check prints only `True` or `False`, never the value. It should
print `True`. Keep this same terminal open for the next command.

## 3. Run the connection check

```powershell
& $pramanPython -B .\scripts\angel_connection_test.py
$LASTEXITCODE
Remove-Item Env:\ANGEL_API_KEY
```

Type your client ID, PIN and current TOTP into the three hidden terminal prompts.
`-B` prevents Python bytecode-cache writes, including a fresh wrapper import.
The wrapper avoids SDK log constructors and public-IP/DNS/hardware probes.
It sends both IP headers as `127.0.0.1`, and MAC `00:00:00:00:00:00`.
**It is not verified whether Angel accepts `127.0.0.1` in these IP headers.**
No authenticated call has been made; if the account requires a real or
registered IP there, login will fail. The wrapper does not query an
unapproved IP-discovery service or guess a real public address.

After prompt labels, successful stdout consists only of:

```text
<quote timestamp> <SBIN last price>
<2026-09-01 minute timestamp> <open> <high> <low> <close>
...one line per returned minute...
<live exchange timestamp> <SBIN live price>
...live ticks for 30 seconds, if open...
```

These are format placeholders, not actual prices. The script fetches one day of
ONE_MINUTE candles, 2026-09-01, from 09:15 to 15:30 IST. The broker determines
which minute bars are available. There are no token/header/profile dumps,
credential-bearing exceptions, status banners, saved logs or store writes.

When the market is closed, the quote and historical candles still run; only the
30-second stream is skipped. The open proxy requires a weekday, 09:15 <= IST time
< 15:30, and an exchange quote timestamp no more than 120 seconds old. Missing
or stale timestamps also skip streaming. Holidays and special sessions are not
authoritatively resolved because the repository has no forward calendar.

Logout is attempted on success, failure or interruption. Exit `0` means the
requested operations completed; `1` means failure/interruption, with no raw error
printed. Live authentication, IP acceptance and historical availability remain
DOCUMENTED, NOT VERIFIED until you run this check.
