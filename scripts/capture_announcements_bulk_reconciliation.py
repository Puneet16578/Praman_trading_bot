"""Eight-request evidence capture; explicit --fetch only, never production ingestion."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/processed/announcements_bulk_reconcile_20261005'
ENDPOINT = 'https://www.nseindia.com/api/corporate-announcements'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true', help='Requires explicit network approval')
    args = parser.parse_args()
    if not args.fetch:
        parser.error('No requests made: --fetch and user approval are required')
    OUT.mkdir(exist_ok=False)
    week = dict(index='equities', from_date='07-09-2026', to_date='13-09-2026')
    calls = [
        ('cookie', 'https://www.nseindia.com', None),
        ('bulk_week', ENDPOINT, week),
        ('bulk_first', ENDPOINT, week | dict(to_date='10-09-2026')),
        ('bulk_last', ENDPOINT, week | dict(from_date='11-09-2026')),
        *[(symbol, ENDPOINT, week | dict(symbol=symbol))
          for symbol in ('HEG', 'SANGINITA', 'HMT', 'MELSTAR')],
    ]
    trace = []
    report = dict(week=['2026-09-07', '2026-09-13'], requests=trace, status='INCOMPLETE')
    with requests.Session() as session:
        session.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
        try:
            for label, url, params in calls:
                if len(trace) >= 8:
                    raise RuntimeError('Eight-request probe budget exhausted')
                item = dict(label=label, params=params)
                trace.append(item)
                started = time.monotonic()
                response = session.get(url, params=params, timeout=25, allow_redirects=False)
                item.update(status=response.status_code, seconds=round(time.monotonic()-started, 3),
                            sha256=hashlib.sha256(response.content).hexdigest())
                (OUT / (label+'.response')).write_bytes(response.content)
                if response.status_code != 200:
                    raise RuntimeError('Non-200 response; no retry')
                if label != 'cookie':
                    payload = response.json()
                    if not isinstance(payload, list):
                        raise ValueError('Expected announcement list')
                    item['rows'] = len(payload)
                print(json.dumps(item), flush=True)
                (OUT/'requests.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
            report['status'] = 'COMPLETE'
        except Exception as exc:
            report['error_type'] = type(exc).__name__
        finally:
            (OUT/'requests.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return 0 if report['status'] == 'COMPLETE' else 1


if __name__ == '__main__':
    raise SystemExit(main())
