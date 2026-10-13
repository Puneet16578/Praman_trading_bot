"""User-terminal smoke test: raw SBIN prices/timestamps only, no store writes.

Run: python scripts/angel_connection_test.py
Install optional requirements-angel.txt first; set ANGEL_API_KEY privately in the
environment. Client ID/PIN/TOTP are hidden terminal prompts, never arguments.
Exit 0 means requested calls completed; 1 means failure (no raw error is printed).
"""
from datetime import datetime, time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from desk.angel_market_data import AngelMarketData
from shared.market_time import IST


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


def main():
    client = AngelMarketData()
    result = 0
    try:
        client.login()
        day = datetime.now(IST).date().isoformat()
        quote = client.quote('SBIN', as_of=day)
        print(f"{quote['exchange_timestamp'] or quote['recorded_at']} {quote['price']:.2f}", flush=True)
        for row in client.candles('SBIN', '2026-09-01', as_of=day):
            print(f"{row['timestamp']} {row['open']:.2f} {row['high']:.2f} {row['low']:.2f} {row['close']:.2f}", flush=True)
        if _market_open(datetime.now(IST), quote):
            client.stream(['SBIN'], _print_tick, as_of=day, seconds=30)
    except (Exception, KeyboardInterrupt):
        result = 1
    finally:
        try:
            client.logout()
        except Exception:
            result = 1
    return result


if __name__ == '__main__':
    raise SystemExit(main())
