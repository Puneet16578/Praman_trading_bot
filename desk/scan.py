"""Append nightly screening inputs; a range uses the identical foreground path."""
from pathlib import Path
import json

from desk.lib.connection import get_desk_connection
from desk.lib.costs import load_active_cost_config
from desk.lib.rulebook import load_active_rulebook
from desk.lib.store import get_live_connection, max_recorded_at
from desk.screening_plan import screen_event, execution_observation
from desk.opportunity_store import append_opportunity, append_execution
from desk.journal.store import desk_watermark
from desk.replay import current_git_head
from src.signals.event_catalogue import build_symbol_history, compute_daily_stats
from src.ingestion.nse_market_data.isin_mapping import load_isin_map, build_symbol_groups
from shared.market_time import market_today
from shared.isin_map_metadata import verified_built_at
import scripts.build_final_event_catalogue as catalogue


def catalogue_events(conn, days):
    """Reuse the pinned catalogue functions; build each security history once."""
    wanted = set(days)
    symbols = [r[0] for r in conn.execute(
        "SELECT DISTINCT symbol FROM bhavcopy WHERE event_date>=? AND event_date<=? AND series='EQ' ORDER BY symbol",
        (min(days), max(days)))]
    path = Path(__file__).resolve().parents[1] / 'data/raw/nse_symbol_isin_current.json'
    isin_map = load_isin_map(path)
    groups = build_symbol_groups(isin_map)
    missing = {s for s in symbols if not isin_map.get(s)}
    non_equity = {s for s in symbols if isin_map.get(s, '').startswith('INF')}
    print(f'Identity exclusions: {len(missing)} unresolved, {len(non_equity)} fund symbols.', flush=True)
    windows = catalogue.build_demerger_windows(conn)
    processed, events = set(), []
    for i, symbol in enumerate(symbols, 1):
        if symbol in missing or symbol in non_equity:
            continue
        group = tuple(sorted(groups.get(symbol, [symbol])))
        if group in processed:
            continue
        processed.add(group)
        hist = build_symbol_history(conn, symbol, symbol_group=list(group))
        events.extend(s for s in compute_daily_stats(hist)
                      if s.event_date in wanted and catalogue.is_event(s)
                      and not catalogue.in_demerger_window(windows, s.symbol, s.event_date))
        if i % 100 == 0:
            print(f'Catalogue inputs: {i}/{len(symbols)} symbols', flush=True)
    return sorted(events, key=lambda s: (s.event_date, s.symbol))


def run_scan_range(days, *, desk_db_path=None):
    """Foreground batch; original durable records are never changed or recomputed."""
    conn = get_live_connection()
    desk = get_desk_connection() if desk_db_path is None else get_desk_connection(desk_db_path)
    try:
        rb, costs = load_active_rulebook(), load_active_cost_config()
        built = verified_built_at()
        provenance = dict(code_commit=current_git_head(), praman_watermark=max_recorded_at(conn),
                          rulebook_hash=rb.sha256, cost_config_hash=costs.sha256)
        events = catalogue_events(conn, days)
        inserted = 0
        for i, event in enumerate(events, 1):
            prior = desk.execute('SELECT opportunity_id FROM opportunity_log WHERE symbol=? AND event_date=?',
                                 (event.symbol, event.event_date)).fetchone()
            if prior is not None:
                continue
            plan, assessment = screen_event(conn, desk, event.symbol, event.event_date, rb.rulebook,
                                             costs.costs, isin_map_built_at=built)
            _, created = append_opportunity(desk, symbol=event.symbol, event_date=event.event_date,
                                            plan=plan, assessment=assessment,
                                            provenance=provenance | {'desk_watermark': desk_watermark(desk)})
            inserted += int(created)
            if i % 25 == 0:
                print(f'Screening inputs: {i}/{len(events)}', flush=True)
        pending = desk.execute('SELECT * FROM opportunity_log WHERE opportunity_id NOT IN '
                               '(SELECT opportunity_id FROM opportunity_executions)').fetchall()
        for row in pending:
            plan = json.loads(row['inputs'])['plan']
            observation = execution_observation(conn, row['symbol'], row['event_date'], max(days), plan,
                                                rb.rulebook, costs.costs)
            if observation is not None:
                append_execution(desk, row['opportunity_id'], observation)
        return inserted
    finally:
        desk.close()
        conn.close()


def run_scan(run_date=None):
    return run_scan_range([run_date or market_today().isoformat()])
