import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings
from desk.lib.connection import get_desk_connection
from desk.lib.costs import load_active_cost_config
from desk.lib.rulebook import load_active_rulebook
from desk.lib.store import get_live_connection
from desk.screening_plan import screen_event, execution_observation
from desk.opportunity_store import append_opportunity, append_execution
from src.signals.event_catalogue import build_symbol_history, compute_daily_stats
from shared.market_time import market_today

import scripts.build_final_event_catalogue as catalogue

def run_scan(run_date: str = None):
    praman_conn = get_live_connection()
    desk_conn = get_desk_connection()
    
    if not run_date:
        run_date = market_today().isoformat()
    
    rulebook = load_active_rulebook()
    costs = load_active_cost_config()
    
    # We only scan for the given date, so we only need symbols that traded on that date
    symbols = [row[0] for row in praman_conn.execute("SELECT symbol FROM bhavcopy WHERE event_date = ? AND series = 'EQ'", (run_date,)).fetchall()]
    
    from src.ingestion.nse_market_data.isin_mapping import load_isin_map, build_symbol_groups
    ISIN_MAP_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "nse_symbol_isin_current.json"
    isin_map = load_isin_map(ISIN_MAP_PATH) if ISIN_MAP_PATH.exists() else {}
    symbol_groups = build_symbol_groups(isin_map) if isin_map else {}
    
    filtered_symbols = []
    unresolved_isin_count = 0
    for s in symbols:
        isin = isin_map.get(s)
        if not isin or isin.startswith("INF"):
            unresolved_isin_count += 1
            continue
        filtered_symbols.append(s)
        
    import logging
    logger = logging.getLogger("desk.scan")
    if unresolved_isin_count > 0:
        msg = f"Excluded {unresolved_isin_count} symbols without a valid equity ISIN."
        logger.info(msg)
        print(msg)
    
    demerger_windows = catalogue.build_demerger_windows(praman_conn)
    
    # Check execution observations for existing pending opportunities
    pending = desk_conn.execute("SELECT * FROM opportunity_log WHERE opportunity_id NOT IN (SELECT opportunity_id FROM opportunity_executions)").fetchall()
    for p in pending:
        import json
        inputs = json.loads(p["inputs"])
        plan = inputs["plan"]
        obs = execution_observation(praman_conn, p["symbol"], p["event_date"], run_date, plan, rulebook.rulebook, costs.costs)
        if obs is not None:
            append_execution(desk_conn, p["opportunity_id"], obs)
    
    processed_groups = set()
    events_found = 0
    for symbol in filtered_symbols:
        group = tuple(sorted(symbol_groups.get(symbol, [symbol])))
        if group in processed_groups:
            continue
        processed_groups.add(group)
        
        hist = build_symbol_history(praman_conn, symbol, symbol_group=list(group))
        stats = compute_daily_stats(hist)
        
        for s in stats:
            if s.event_date == run_date and catalogue.is_event(s) and not catalogue.in_demerger_window(demerger_windows, s.symbol, s.event_date):
                events_found += 1
                plan, assessment = screen_event(praman_conn, desk_conn, s.symbol, s.event_date, rulebook.rulebook, costs.costs)
                
                from desk.replay import current_git_head
                from desk.lib.store import max_recorded_at
                from desk.journal.store import desk_watermark
                
                provenance = {
                    "code_commit": current_git_head(),
                    "praman_watermark": max_recorded_at(praman_conn),
                    "desk_watermark": desk_watermark(desk_conn),
                    "rulebook_hash": rulebook.sha256,
                    "cost_config_hash": costs.sha256
                }
                append_opportunity(desk_conn, symbol=s.symbol, event_date=s.event_date, plan=plan, assessment=assessment, provenance=provenance)

    praman_conn.close()
    desk_conn.close()
    return events_found
