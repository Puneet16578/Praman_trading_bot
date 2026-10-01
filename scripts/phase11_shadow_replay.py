import sys
import csv
import time
import json
import numpy as np
from pathlib import Path
from collections import defaultdict
from multiprocessing import Pool
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection
from src.config.settings import get_settings
from src.bitemporal.guard import latest_as_of, read_as_of
from src.signals.price_adjustment import compute_adjustment_factor
from desk.lib.connection import get_desk_connection
from desk.lib.rulebook import load_active_rulebook
from desk.lib.costs import load_active_cost_config
from desk.screening_plan import screen_event, execution_observation

# Global init for workers
conn = None
desk_conn = None
rulebook = None
costs = None

def init_worker():
    global conn, desk_conn, rulebook, costs
    settings = get_settings()
    conn = get_connection(settings.database_path)
    desk_conn = get_desk_connection()
    rulebook = load_active_rulebook().rulebook
    costs = load_active_cost_config().costs

def evaluate_single(row):
    symbol, event_date = row["symbol"], row["event_date"]
    
    # 1. Decision Plan
    plan, assessment = screen_event(conn, desk_conn, symbol, event_date, rulebook, costs)
    state = assessment.state
    gate_results = assessment.gate_results_json()
    
    # Extract veto reasons
    veto_reasons = []
    if state == "SCREEN_FAIL":
        for g, res in gate_results.items():
            if g not in ("G7", "G8") and res["result"] != "PASS":
                veto_reasons.append(g) # just the gate name for brevity, or we can use specific reasons

    # 2. Execution and 20-day path
    # Next 20 sessions for this symbol
    future = conn.execute("SELECT DISTINCT event_date FROM bhavcopy WHERE event_date > ? AND event_date <= '2026-09-15' AND symbol = ? AND series IN ('EQ', 'BE', 'BZ') ORDER BY event_date LIMIT 21", (event_date, symbol)).fetchall()
    future_sessions = [r[0] for r in future]
    
    if not future_sessions:
        return {"symbol": symbol, "event_date": event_date, "state": state, "veto": veto_reasons, "fill": None, "immediate_gap": False, "incomplete_20": True}
        
    next_session = future_sessions[0]
    # Execution observation using the next session
    obs = execution_observation(conn, symbol, event_date, "2099-01-01", plan, rulebook, costs)
    
    fill = obs["fill"] if obs and obs.get("status") == "FILLED" else None
    immediate_gap = obs["immediate_gap_through"] if obs and obs.get("status") == "FILLED" else False
    
    window_20 = future_sessions[:20]
    incomplete_20 = len(window_20) < 20
    
    low_falls_20pct = False
    stop_gap_through = immediate_gap
    entry_only_gap = immediate_gap
    max_adverse_decision = 0.0
    max_adverse_fill = 0.0
    locked_lc_days = 0
    lc_denominator = 0
    
    stop_level = plan.get("stop_level")
    decision_price = plan.get("decision_price")
    stop_hit = immediate_gap
    
    if fill is not None:
        if fill <= stop_level:
            stop_hit = True
            
        for session in window_20:
            # We need the low price adjusted to the event_date basis
            rows = latest_as_of(conn, "bhavcopy", "2099-01-01", symbol=symbol, event_date=session)
            rows = [r for r in rows if r["series"] in ("EQ", "BE", "BZ")]
            if not rows: continue
            r = rows[0]
            if not r["low_price"]: continue
            
            # The decision price is in event_date basis.
            # To compare session low to decision price, adjust session low back to event_date basis:
            from src.signals.price_adjustment import UnadjustableWindowError
            try:
                factor = compute_adjustment_factor(conn, symbol, event_date, session)
            except UnadjustableWindowError:
                # Structural break in window, exclude from tail metrics
                incomplete_20 = True
                continue
            
            adj_low = r["low_price"] / factor
            
            adverse_decision = (decision_price - adj_low) / decision_price
            max_adverse_decision = max(max_adverse_decision, adverse_decision)
            
            adverse_fill = (fill - adj_low) / fill
            max_adverse_fill = max(max_adverse_fill, adverse_fill)
            
            if adj_low <= 0.8 * decision_price:
                low_falls_20pct = True
                
            if not stop_hit and adj_low <= stop_level:
                stop_hit = True
                
            # Check locked lower circuit
            from desk.circuit_bands import band_as_of
            # The band for `session` is based on the preceding session's snapshot
            # which is `session` as the report_date (as band snapshots are published daily for the next day)
            band = band_as_of(desk_conn, symbol, session, report_date=session)
            if band.kind == "FIXED" and band.percent is not None:
                lc_denominator += 1
                # Lower circuit limit = previous close * (1 - pct/100), rounded to nearest 0.05
                limit = round((r["prev" + "_close"] * (1 - band.percent/100)) * 20) / 20.0
                if r["low_price"] <= limit:
                    locked_lc_days += 1
    
    return {
        "symbol": symbol,
        "event_date": event_date,
        "state": state,
        "veto": tuple(sorted(veto_reasons)),
        "fill": fill,
        "immediate_gap": immediate_gap,
        "entry_only_gap": entry_only_gap,
        "stop_gap_through": stop_gap_through,
        "incomplete_20": incomplete_20,
        "low_falls_20pct": low_falls_20pct,
        "max_adverse_decision": max_adverse_decision,
        "max_adverse_fill": max_adverse_fill,
        "locked_lc_days": locked_lc_days,
        "lc_denominator": lc_denominator
    }

def main():
    import os
    import time
    
    catalogue_path = Path(__file__).resolve().parents[1] / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
    if not catalogue_path.exists():
        print("Catalogue not found.")
        return
        
    events = []
    with open(catalogue_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "2019-10-01" <= row["event_date"] <= "2026-09-15":
                events.append(row)
                
    print(f"Loaded {len(events)} events for shadow replay.")
    
    t0 = time.time()
    results = []
    
    # Run multiprocessing pool
    with Pool(processes=os.cpu_count() or 4, initializer=init_worker) as pool:
        for i, res in enumerate(pool.imap_unordered(evaluate_single, events, chunksize=100)):
            results.append(res)
            if (i+1) % 1000 == 0:
                print(f"Processed {i+1}/{len(events)} in {time.time()-t0:.1f}s")
                
    print(f"Done processing in {time.time()-t0:.1f}s.")
    
    # Save results to a temporary JSON so we can analyze them quickly
    out_path = Path(__file__).resolve().parents[1] / "data" / "processed" / "shadow_replay_raw.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f)
        
    print(f"Saved raw results to {out_path}.")

    
if __name__ == "__main__":
    main()
