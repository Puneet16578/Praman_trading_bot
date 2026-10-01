"""Compare full outcome values with Amendment 5 source, on a temporary snapshot."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desk.lib.store import PRODUCTION_DB_PATH
from desk.outcome_firewall import require_outcome_access
from shared.sqlite_backup import online_backup
from shared.sqlite_readonly import open_readonly
from src.ingestion.nse_market_data.isin_mapping import load_isin_map, build_symbol_groups
from src.signals.event_catalogue import build_symbol_history
from scripts.phase8_robustness_relabel_t0 import compute_t0_relative, load_market_index

PIN = 'afe3e2bd07abe8b602c4119b916f7696a3c12131'
SOURCE = 'scripts/phase8_robustness_relabel_t0.py'


def main():
    diff = subprocess.check_output(['git', 'diff', PIN, 'HEAD', '--', SOURCE], cwd=ROOT)
    if diff:
        raise RuntimeError('Pinned label source differs; review before comparing values.')
    source = subprocess.check_output(['git', 'show', f'{PIN}:{SOURCE}'], cwd=ROOT)
    groups = build_symbol_groups(load_isin_map(ROOT / 'data/raw/nse_symbol_isin_current.json'))
    with (ROOT / 'data/processed/event_catalogue_loose_zscore_only.csv').open() as f:
        rows = sorted(csv.DictReader(f), key=lambda r: (r['event_date'], r['symbol']))
    sample = [next(r for r in rows if r['event_date'].startswith(str(year))) for year in (2020, 2021, 2022, 2024, 2025)]
    index = load_market_index()
    values = []
    with tempfile.TemporaryDirectory(prefix='praman_label_check_') as temporary:
        base = Path(temporary)
        pinned_file = base / 'pinned_label.py'
        pinned_file.write_bytes(source)
        spec = importlib.util.spec_from_file_location('pinned_label', pinned_file)
        pinned = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pinned)
        database = base / 'praman.sqlite'
        online_backup(PRODUCTION_DB_PATH, database)
        conn = open_readonly(database)
        try:
            for row in sample:
                symbol, day = row['symbol'], row['event_date']
                require_outcome_access(day)
                hist = build_symbol_history(conn, symbol, symbol_group=groups.get(symbol, [symbol]), extend_with_series=('BE','BZ'))
                direction = 1 if float(row['return_1d']) > 0 else -1
                args = (hist, day, direction, index, sorted(index))
                actual, expected = compute_t0_relative(*args), pinned.compute_t0_relative(*args)
                if actual != expected:
                    raise AssertionError(f'Label value mismatch for {symbol} {day}')
                values.append(dict(symbol=symbol, event_date=day, current=actual, pinned=expected))
        finally:
            conn.close()
    report = dict(pin=PIN, source=SOURCE, function='compute_t0_relative', git_diff='',
                  source_sha256=hashlib.sha256(source).hexdigest(), comparisons=values,
                  qualification='Same temporary data snapshot and identical stitched EQ/BE/BZ histories supplied to both source versions; code-equivalence check, not a claim about the data vintage at the pinned commit.')
    (ROOT / 'docs/desk/label_value_verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
