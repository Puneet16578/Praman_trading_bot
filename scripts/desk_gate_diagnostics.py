"""Inputs-only gate audit on temporary Desk copies, with a fixed historical sample."""
import argparse
import csv
import json
import random
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desk.lib.connection import DESK_DB_PATH, get_desk_connection
from desk.lib.store import get_live_connection
from desk.lib.rulebook import load_active_rulebook
from desk.lib.costs import load_active_cost_config
from desk.screening_plan import screen_event
from shared.sqlite_backup import online_backup


def summary(rows):
    first, every, reasons, states = Counter(), Counter(), Counter(), Counter()
    for row in rows:
        states[row['state']] += 1
        gates = row['gates']
        failed = [f'G{i}' for i in range(1, 7) if gates[f'G{i}']['result'] != 'PASS']
        if failed:
            first[failed[0]] += 1
        every.update(failed)
        for gate in failed:
            reasons.update(f'{gate}: {reason}' for reason in gates[gate]['reasons'])
    return dict(n=len(rows), states=dict(states), first=dict(first), every=dict(every), reasons=dict(reasons))


def historical_sample():
    with (ROOT / 'data/processed/event_catalogue_loose_zscore_only.csv').open(encoding='utf-8') as f:
        events = list(csv.DictReader(f))
    rng = random.Random(20261001)
    sample = []
    for year in range(2019, 2026):
        pool = sorted((r for r in events if r['event_date'].startswith(str(year))), key=lambda r: (r['event_date'], r['symbol']))
        sample.extend(rng.sample(pool, min(len(pool), 29 if year < 2023 else 28)))
    selected = {(r['symbol'], r['event_date']) for r in sample}
    remainder = sorted((r for r in events if '2019-01-01' <= r['event_date'] <= '2025-12-31'
                        and (r['symbol'], r['event_date']) not in selected),
                       key=lambda r: (r['event_date'], r['symbol']))
    sample.extend(rng.sample(remainder, 200-len(sample)))
    return sorted(sample, key=lambda r: (r['event_date'], r['symbol']))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rb, costs = load_active_rulebook().rulebook, load_active_cost_config().costs
    conn = get_live_connection()
    records = []
    try:
        with tempfile.TemporaryDirectory(prefix='praman_gates_') as temporary:
            copy = Path(temporary) / 'desk.sqlite'
            online_backup(DESK_DB_PATH, copy)
            desk = get_desk_connection(copy)
            try:
                days = sorted(r[0] for r in conn.execute('SELECT DISTINCT event_date FROM bhavcopy ORDER BY event_date DESC LIMIT 10'))
                stored = [dict(symbol=r['symbol'], event_date=r['event_date'], state=r['state'], gates=json.loads(r['gate_results'])) for r in desk.execute('SELECT * FROM opportunity_log WHERE event_date>=?', (days[0],))]
                for i, row in enumerate(historical_sample(), 1):
                    _, result = screen_event(conn, desk, row['symbol'], row['event_date'], rb, costs)
                    records.append(dict(symbol=row['symbol'], event_date=row['event_date'], state=result.state, gates=result.gate_results_json()))
                    if i % 10 == 0:
                        print(f'Historical inputs: {i}/200', flush=True)
                output = dict(days=days, stored_recent=summary(stored), historical=summary(records), historical_events=records)
                args.output.write_text(json.dumps(output, indent=2), encoding='utf-8')
                print(json.dumps({k: v for k, v in output.items() if k != 'historical_events'}, indent=2), flush=True)
            finally:
                desk.close()
    finally:
        conn.close()


if __name__ == '__main__':
    main()
