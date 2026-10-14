"""User-terminal smoke test: raw SBIN prices/timestamps only, no store writes.

Run: python -B scripts/angel_connection_test.py          (the full test; logs in)
     python -B scripts/angel_connection_test.py --candle-date YYYY-MM-DD   (another stored session
                                                          before 2026-09-16; default 2026-09-01)
     python -B scripts/angel_connection_test.py --check  (setup only; no login, no credentials read)
Install optional requirements-angel.txt first; set ANGEL_API_KEY privately in the environment.
Client ID/PIN/TOTP are hidden terminal prompts, never arguments.
Exit 0 means the requested steps completed; 1 means failure. Every run ends with one plain line
saying why it stopped (P8-071); no raw error, response or credential is ever printed.
"""
from datetime import date, datetime, time
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from desk.angel_market_data import AngelError, AngelMarketData, check_setup, error_details
from shared.market_time import IST
from shared.sqlite_readonly import open_readonly

PRAMAN_DB = Path(__file__).resolve().parents[1] / 'data' / 'processed' / 'praman.db'


# The measuring instrument: one fixed, repeatable session before the forward window, which worked
# on 2026-10-14 08:10 (user decision 2026-10-14; it replaces 967729e's "recent session" choice).
CANDLE_DATE = '2026-09-01'


class CandleDateRefused(ValueError):
    pass


def validate_candle_date(text, today):
    """A completed NSE trading session before the forward window: ISO format, before
    desk.outcome_firewall.FORWARD_START, before today, and a stored SBIN EQ session known by today."""
    from desk.outcome_firewall import FORWARD_START
    try:
        day = date.fromisoformat(text)
    except (TypeError, ValueError):
        raise CandleDateRefused('use YYYY-MM-DD') from None
    if text != day.isoformat():
        raise CandleDateRefused('use YYYY-MM-DD')
    if day >= FORWARD_START or text >= today:
        raise CandleDateRefused(f'choose a completed session before {FORWARD_START.isoformat()}')
    try:
        conn = open_readonly(PRAMAN_DB)
        try:
            row = conn.execute("SELECT 1 FROM bhavcopy WHERE symbol='SBIN' AND series='EQ' AND event_date=? "
                               "AND knowledge_date<=? LIMIT 1", (text, today)).fetchone()
        finally:
            conn.close()
    except Exception:
        raise CandleDateRefused('the local store could not be read to confirm the session') from None
    if row is None:
        raise CandleDateRefused(f'{text} is not a stored SBIN trading session')
    return text


def candle_summary(rows, day):
    """One line instead of every bar: count, first and last minute, the day's open/high/low/last
    and the minutes from 09:15 to 15:29 with no bar."""
    minutes = sorted({row['timestamp'][11:16] for row in rows})
    grid = [f'{h:02d}:{m:02d}' for h in range(9, 16) for m in range(60) if '09:15' <= f'{h:02d}:{m:02d}' <= '15:29']
    present = set(minutes)
    missing = [t for t in grid if t not in present]
    ranges, start = [], None
    for i, t in enumerate(missing):
        if start is None:
            start = t
        nxt = missing[i + 1] if i + 1 < len(missing) else None
        if nxt is None or grid.index(nxt) != grid.index(t) + 1:
            ranges.append(start if start == t else f'{start}-{t}')
            start = None
    ordered = sorted(rows, key=lambda r: r['timestamp'])
    gaps = f"{len(missing)} ({', '.join(ranges)})" if missing else 'none'
    return (f"Candles SBIN {day}: {len(rows)} bars, first {minutes[0]}, last {minutes[-1]}; open "
            f"{ordered[0]['open']:.2f}, high {max(r['high'] for r in rows):.2f}, low {min(r['low'] for r in rows):.2f}, "
            f"last {ordered[-1]['close']:.2f}; missing minutes 09:15-15:29: {gaps}")


# The wrapper's errors are fixed, credential-free messages; these say what to do about them.
PLAIN = {
    'Install the pinned optional Angel requirements.': 'Angel library not installed (smartapi-python 1.5.5): see setup step 1',
    'Set ANGEL_API_KEY in the environment.': 'ANGEL_API_KEY is not set in this window: see setup step 2',
    'Login input is required.': 'client ID, PIN and TOTP are all required',
    'Login failed; use a private interactive terminal.': (
        'login failed: check the client ID, PIN, TOTP and API key; Angel may also refuse the 127.0.0.1 '
        'IP headers (not yet verified)'),
}


def _market_open(now, quote):
    # No forward holiday calendar: require regular weekday hours AND a fresh
    # exchange quote. A missing/stale timestamp is not evidence of an open market.
    stamp = quote.get('exchange_timestamp')
    if not stamp or now.weekday() >= 5 or not time(9, 15) <= now.time() < time(15, 30):
        return False
    observed = datetime.fromisoformat(stamp)
    return observed.utcoffset() is not None and 0 <= (now - observed).total_seconds() <= 120


def _print_tick(tick):
    print(f"{tick['timestamp']} {tick['price']:.2f}", flush=True)


def feed_close_line(summary):
    """One line from the wrapper's close summary: numbers and fixed words only."""
    def secs(key):
        value = summary.get(key)
        return 'never' if value is None else f'{value:.1f}s'
    stopped = ''
    if summary.get('closed_by') == 'client' and summary.get('stopped_because'):
        size = summary.get('stopped_message_bytes')
        stopped = (f" (we stopped it: {summary['stopped_because']}"
                   + (f", {size} bytes, text never shown" if size is not None else '') + ')')
    return (f"Feed close: by {summary.get('closed_by')}{stopped}, code {summary.get('close_code') or 'none'}, reason "
            f"{summary.get('close_reason') or 'none'} ({summary.get('close_reason_bytes', 0)} bytes, text never shown); "
            f"connected {secs('connected_seconds')}; since last message {secs('seconds_since_last_message')}, "
            f"PING sent {secs('seconds_since_ping_sent')}, PONG back {secs('seconds_since_pong_received')}, "
            f"text ping {secs('seconds_since_text_ping_sent')}, text pong {secs('seconds_since_text_pong_received')}; "
            f"frames {summary.get('frames')}")


# An unexplained denial names no suspect; the evidence so far is in the 403 note (user, 2026-10-14).
NOTE_403 = 'see docs/desk/angel_candle_403_20261014.md'


def stop_reason(exc):
    """The fixed, credential-free reason for a stop; also used by the capacity probe (P8-081)."""
    if isinstance(exc, KeyboardInterrupt):
        return 'interrupted'
    if isinstance(exc, AngelError):
        message = str(exc)
        return PLAIN.get(message, message)
    return f'unexpected error ({type(exc).__name__})'


def reply_shape_line(exc):
    """An unexplained denial's shape (kind, bytes, Angel-pattern error code), never its text."""
    shape = error_details(exc).get('reply') if isinstance(exc, AngelError) else None
    if not shape:
        return None
    size = 'length unknown' if shape.get('bytes') is None else f"{shape['bytes']} bytes"
    code = f"error code {shape['error_code']}" if shape.get('error_code') else 'no Angel error code'
    return f"Reply: {shape.get('kind')}, {size}, {code} (text never shown)."


def _with_note(line, exc):
    if isinstance(exc, AngelError) and error_details(exc)['category'] in ('access_denied', 'permission_denied'):
        return line.rstrip('.') + '; ' + NOTE_403
    return line


def check():
    """Setup only: one line per item, then a verdict. Never reads ANGEL_API_KEY."""
    results = check_setup()
    for item, ok, detail in results:
        print(f"{'OK     ' if ok else 'MISSING'} {item}: {detail}")
    print('NOTE    ANGEL_API_KEY: not checked here (the check never reads credentials); the full test reports it')
    ready = all(ok for _, ok, _ in results)
    print('Setup ready for the connection test.' if ready else 'Setup incomplete: fix the MISSING items above.')
    return 0 if ready else 1


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv == ['--check']:
        return check()
    candle_day = CANDLE_DATE
    if len(argv) == 2 and argv[0] == '--candle-date':
        try:
            candle_day = validate_candle_date(argv[1], datetime.now(IST).date().isoformat())
        except CandleDateRefused as exc:
            print(f'Stopped before login: --candle-date refused: {exc}')
            return 1
    elif argv:
        print('Usage: python -B scripts/angel_connection_test.py [--check | --candle-date YYYY-MM-DD]')
        return 1
    missing = [f'{item} ({detail})' for item, ok, detail in check_setup() if not ok]
    if missing:
        print('Stopped before login: Angel library not installed or incomplete: ' + '; '.join(missing))
        return 1
    client = AngelMarketData()
    result, stage, streamed, quote = 0, 'login', False, None
    try:
        client.login()
        day = datetime.now(IST).date().isoformat()
        stage = 'quote'
        quote = client.quote('SBIN', as_of=day)
        print(f"{quote['exchange_timestamp'] or quote['recorded_at']} {quote['price']:.2f}", flush=True)
        stage = 'candles'
        print(candle_summary(client.candles('SBIN', candle_day, as_of=day), candle_day), flush=True)
        if _market_open(datetime.now(IST), quote):
            stage = 'live feed'
            client.stream(['SBIN'], _print_tick, as_of=day, seconds=30)
            streamed = True
        stage = 'logout'
    except (Exception, KeyboardInterrupt) as exc:
        result = 1
        if reply_shape_line(exc):
            print(reply_shape_line(exc), flush=True)
        if stage == 'candles':
            print(f'Candle request: NSE SBIN ONE_MINUTE {candle_day} 09:15-15:30 IST, one request, no retry.', flush=True)
            opened = quote is not None and _market_open(datetime.now(IST), quote)
            reason = stop_reason(exc)
            print(_with_note(f'Stopped at candles: {reason}{" " if reason.endswith(".") else ". "}Market open at '
                             f'that moment: {"yes" if opened else "no"} (weekday 09:15-15:30 IST with a fresh quote).',
                             exc), flush=True)
        else:
            print(_with_note(f'Stopped at {stage}: {stop_reason(exc)}', exc), flush=True)
        stream_summary = error_details(exc).get('stream') if isinstance(exc, AngelError) else None
        if stage == 'live feed' and stream_summary:
            print(feed_close_line(stream_summary), flush=True)
    finally:
        try:
            client.logout()
        except Exception:
            result = 1
            print('Logout failed; local credentials were cleared anyway.', flush=True)
    if result == 0:
        print('Connection test completed: login, quote, candles'
              + (', 30 seconds of live feed' if streamed else ' (live feed skipped: market closed or quote not fresh)')
              + ' and logout.', flush=True)
    return result


if __name__ == '__main__':
    raise SystemExit(main())
