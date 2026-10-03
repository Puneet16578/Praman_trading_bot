"""Foreground-only preregistered research on disposable read-only database copies."""
from __future__ import annotations
import os
for _name in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[_name] = '1'
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from contextlib import ExitStack

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desk.lib.connection import DESK_DB_PATH
from desk.lib.store import PRODUCTION_DB_PATH, max_recorded_at
from desk.journal.store import desk_watermark
from desk.lib.rulebook import load_active_rulebook
from desk.lib.costs import load_active_cost_config
from desk.outcome_firewall import require_outcome_access
from desk.research_snapshot import SnapshotQueries, memoized_snapshot_histories
from desk.screening_plan import screen_event, execution_observation
from desk.shadow_analysis import tails, summarize, SEED, REPLICATES
from desk.shadow_report import report_markdown
from shared.sqlite_backup import online_backup
from shared.sqlite_readonly import open_readonly
from shared.market_time import market_today
from src.signals.event_catalogue import build_symbol_history
from src.ingestion.nse_market_data.isin_mapping import load_isin_map, build_symbol_groups
from scripts.phase8_robustness_relabel_t0 import compute_t0_relative, load_market_index


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--screen-only-limit', type=int, default=0,
                        help='Inputs-only performance check; never reads labels or writes results.')
    args = parser.parse_args()
    rb, costs = load_active_rulebook(), load_active_cost_config()
    catalogue = ROOT/'data/processed/event_catalogue_loose_zscore_only.csv'
    with catalogue.open(encoding='utf-8') as f:
        source_events = list(csv.DictReader(f))
    events = sorted((r for r in source_events if '2019-10-01' <= r['event_date'] <= '2026-09-15'),
                    key=lambda r: (r['symbol'], r['event_date']))
    if args.screen_only_limit:
        events = events[:args.screen_only_limit]
    for row in events:
        require_outcome_access(row['event_date'])
    groups = build_symbol_groups(load_isin_map(ROOT/'data/raw/nse_symbol_isin_current.json'))
    market_index = load_market_index()
    output_dir = ROOT/'docs/desk'
    raw_path = ROOT/'data/processed/desk_shadow_replay_round2.jsonl'
    provenance = dict(code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                      run_date=market_today().isoformat(), rulebook=rb.model_dump(), costs=costs.model_dump(),
                      seed=SEED, bootstrap_replicates=REPLICATES,
                      catalogue_events=len(source_events), eligible_events=len(events),
                      outside_period_excluded=len(source_events)-len(events), raw_path=raw_path.relative_to(ROOT).as_posix(),
                      label_function='scripts.phase8_robustness_relabel_t0.compute_t0_relative')
    files = [catalogue, ROOT/'data/processed/market_index.csv', ROOT/'data/raw/nse_symbol_isin_current.json',
             ROOT/'scripts/phase8_robustness_relabel_t0.py', ROOT/'src/signals/event_catalogue.py',
             ROOT/'docs/desk/shadow_replay_prereg.md', Path(__file__).resolve()]
    files += sorted((ROOT/'desk').rglob('*.py'))
    provenance['source_hashes'] = {p.relative_to(ROOT).as_posix():sha256(p) for p in files}
    records = []
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='praman_shadow_') as temp, ExitStack() as context:
        snapshots = {}
        for name, source in [('praman',PRODUCTION_DB_PATH), ('desk',DESK_DB_PATH)]:
            target = Path(temp)/(name+'.sqlite')
            online_backup(source, target)
            snapshots[name] = target
        conn, desk = open_readonly(snapshots['praman']), open_readonly(snapshots['desk'])
        try:
            provenance['snapshot_sha256'] = {name:sha256(p) for name,p in snapshots.items()}
            provenance['praman_watermark'] = max_recorded_at(conn)
            provenance['desk_watermark'] = desk_watermark(desk)
            cutoff = market_today().isoformat()
            global_days = [r[0] for r in conn.execute('SELECT DISTINCT event_date FROM bhavcopy WHERE knowledge_date<=? ORDER BY event_date',(cutoff,))]
            provenance['price_cutoff'] = global_days[-1]
            provenance['market_index_cutoff'] = max(market_index)
            cached = SnapshotQueries(conn)
            context.enter_context(memoized_snapshot_histories(cached))
            last_symbol, hist = None, None
            raw = None if args.screen_only_limit else raw_path.open('w',encoding='utf-8',newline='\n')
            try:
                for i, event in enumerate(events, 1):
                    symbol, day = event['symbol'], event['event_date']
                    if symbol != last_symbol:
                        cached.cache.clear()
                        hist = None
                        last_symbol = symbol
                    plan, assessment = screen_event(cached, desk, symbol, day, rb.rulebook, costs.costs)
                    if not args.screen_only_limit:
                        require_outcome_access(day)
                        if hist is None:
                            hist = build_symbol_history(cached,symbol,symbol_group=groups.get(symbol,[symbol]),extend_with_series=('BE','BZ'))
                        label = compute_t0_relative(hist, day, 1 if float(event['return_1d'])>0 else -1, market_index, sorted(market_index))
                        obs = execution_observation(cached,symbol,day,cutoff,plan,rb.rulebook,costs.costs)
                        record = dict(symbol=symbol,event_date=day,state=assessment.state,plan=plan,
                                      gates=assessment.gate_results_json(),evidence_hash=assessment.evidence_bundle.content_hash(),
                                      execution=obs,fill=obs.get('fill_price') if obs else None,label=label,
                                      signed_return_90d=label['signed_return_90d'],collapse=label['collapsed_t0_primary'],
                                      **tails(hist,day,global_days,plan,obs,desk,cutoff))
                        raw.write(json.dumps(record,sort_keys=True)+'\n')
                        records.append(record)
                    if i % 100 == 0 or i == len(events):
                        print(f'Processed {i}/{len(events)} events in {time.monotonic()-started:.1f}s',flush=True)
            finally:
                if raw:
                    raw.close()
        finally:
            conn.close()
            desk.close()
    if args.screen_only_limit:
        return
    provenance['raw_sha256'] = sha256(raw_path)
    summaries = {}
    for period,start,end in [('Primary 2019-2025','2019-10-01','2025-12-31'),('Descriptive 2026','2026-01-01','2026-09-15')]:
        selected = [r for r in records if start<=r['event_date']<=end]
        summaries[period] = {}
        for cohort,rows in [('All candidates',selected),('Filled only',[r for r in selected if r['fill'] is not None])]:
            print(f'Bootstrap: {period}, {cohort}, {len(rows)} events',flush=True)
            summaries[period][cohort] = summarize(rows)
    output = dict(provenance=provenance,results=summaries)
    (output_dir/'shadow_replay_results.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    (output_dir/'shadow_replay_results.md').write_text(report_markdown(provenance,summaries),encoding='utf-8')
    print('Wrote docs/desk/shadow_replay_results.md and .json',flush=True)


if __name__ == '__main__':
    main()
