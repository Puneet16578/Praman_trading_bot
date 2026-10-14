"""User-terminal smoke test: raw SBIN prices/timestamps only, no store writes.

Run: python -B scripts/angel_connection_test.py          (the full test; logs in)
     python -B scripts/angel_connection_test.py --check  (setup only; no login, no credentials read)
Install optional requirements-angel.txt first; set ANGEL_API_KEY privately in the environment.
Client ID/PIN/TOTP are hidden terminal prompts, never arguments.
Exit 0 means the requested steps completed; 1 means failure. Every run ends with one plain line
saying why it stopped (P8-071); no raw error, response or credential is ever printed.
"""
from datetime import date, datetime, time, timedelta
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from desk.angel_market_data import AngelError, AngelMarketData, check_setup, error_details
from shared.market_time import IST
from shared.sqlite_readonly import open_readonly

PRAMAN_DB = Path(__file__).resolve().parents[1] / 'data' / 'processed' / 'praman.db'


def recent_session(as_of, symbol='SBIN'):
    """Use observed EQ sessions, never infer a session from a weekday.

    Only prior dates known by today's as-of are eligible. A 14-calendar-day
    freshness bound fails closed if local ingestion cannot evidence a recent session.
    This is a smoke-test selection policy, not a broker historical-data limit.
    """
    oldest = (date.fromisoformat(as_of) - timedelta(days=14)).isoformat()
    try:
        conn = open_readonly(PRAMAN_DB)
        try:
            row = conn.execute("SELECT MAX(event_date) FROM bhavcopy WHERE symbol = ? AND series = 'EQ' "
                               "AND event_date < ? AND event_date >= ? AND knowledge_date <= ?",
                               (symbol, as_of, oldest, as_of)).fetchone()
        finally:
            conn.close()
    except Exception:
        raise AngelError('Completed-session evidence unavailable in the local NSE store.') from None
    if not row or not row[0]:
        raise AngelError('No recent completed NSE EQ session in the local store.')
    return row[0]

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
    return (f"Feed close: by {summary.get('closed_by')}, code {summary.get('close_code') or 'none'}, reason "
            f"{summary.get('close_reason') or 'none'} ({summary.get('close_reason_bytes', 0)} bytes, text never shown); "
            f"connected {secs('connected_seconds')}; since last message {secs('seconds_since_last_message')}, "
            f"PING sent {secs('seconds_since_ping_sent')}, PONG back {secs('seconds_since_pong_received')}, "
            f"text ping {secs('seconds_since_text_ping_sent')}, text pong {secs('seconds_since_text_pong_received')}; "
            f"frames {summary.get('frames')}")


def _reason(exc):
    if isinstance(exc, KeyboardInterrupt):
        return 'interrupted'
    if isinstance(exc, AngelError):
        message = str(exc)
        if error_details(exc)['category'] in ('access_denied', 'permission_denied'):
            return message + ' Verify app access and registered static IP with Angel support; do not retry in a loop.'
        return PLAIN.get(message, message)
    return f'unexpected error ({type(exc).__name__})'


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
    if argv:
        print('Usage: python -B scripts/angel_connection_test.py [--check]')
        return 1
    missing = [f'{item} ({detail})' for item, ok, detail in check_setup() if not ok]
    if missing:
        print('Stopped before login: Angel library not installed or incomplete: ' + '; '.join(missing))
        return 1
    client = AngelMarketData()
    result, stage, streamed = 0, 'login', False
    candle_day = None
    try:
        client.login()
        day = datetime.now(IST).date().isoformat()
        stage = 'quote'
        quote = client.quote('SBIN', as_of=day)
        print(f"{quote['exchange_timestamp'] or quote['recorded_at']} {quote['price']:.2f}", flush=True)
        stage = 'candles'
        candle_day = date.fromisoformat(recent_session(day)).isoformat()
        for row in client.candles('SBIN', candle_day, as_of=day):
            print(f"{row['timestamp']} {row['open']:.2f} {row['high']:.2f} {row['low']:.2f} {row['close']:.2f}", flush=True)
        if _market_open(datetime.now(IST), quote):
            stage = 'live feed'
            client.stream(['SBIN'], _print_tick, as_of=day, seconds=30)
            streamed = True
        stage = 'logout'
    except (Exception, KeyboardInterrupt) as exc:
        result = 1
        if stage == 'candles' and candle_day is not None:
            print(f'Candle request: NSE SBIN ONE_MINUTE {candle_day} 09:15-15:30 IST; '
                  'completed session evidenced locally.', flush=True)
        print(f'Stopped at {stage}: {_reason(exc)}', flush=True)
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
