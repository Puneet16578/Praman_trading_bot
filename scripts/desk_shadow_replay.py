import sys
import csv
import time
import json
import numpy as np
import bisect
from pathlib import Path
from collections import defaultdict
from multiprocessing import Pool
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection
from src.config.settings import get_settings
from src.bitemporal.guard import latest_as_of, read_as_of
from src.signals.price_adjustment import compute_adjustment_factor
from src.signals.event_catalogue import build_symbol_history
from desk.lib.connection import get_desk_connection
from desk.lib.rulebook import load_active_rulebook
from desk.lib.costs import load_active_cost_config
from desk.screening_plan import screen_event, execution_observation
from desk.outcomes import outcome_firewall
from scripts.phase8_robustness_relabel_t0 import compute_t0_relative, load_market_index

# Global init for workers
conn = None
desk_conn = None
rulebook = None
costs = None
market_index = None
global_days = None

def init_worker():
    global conn, desk_conn, rulebook, costs, market_index, global_days
    settings = get_settings()
    conn = get_connection(settings.database_path)
    desk_conn = get_desk_connection()
    rulebook = load_active_rulebook().rulebook
    costs = load_active_cost_config().costs
    market_index = load_market_index()
    global_days = sorted(market_index.keys())

def evaluate_single(row):
    symbol, event_date, direction = row["symbol"], row["event_date"], row["direction"]
    
    # 1. Decision Plan
    plan, assessment = screen_event(conn, desk_conn, symbol, event_date, rulebook, costs)
    state = assessment.state
    gate_results = assessment.gate_results_json()
    
    # Extract veto reasons
    veto_reasons = []
    if state == "SCREEN_FAIL":
        for g, res in gate_results.items():
            if g not in ("G7", "G8") and res["result"] != "PASS":
                veto_reasons.append(g)

    # 2. Outcomes & Tail Metrics
    # Only if NOT in forward window. (We use the firewall for safety, although the input list is filtered)
    try:
        outcome_firewall(event_date)
    except ValueError:
        return {"symbol": symbol, "event_date": event_date, "state": state, "veto": veto_reasons, "fill": None, "forward_window": True}

    # Outcome Label (Amendment 5)
    hist = build_symbol_history(conn, symbol, extend_with_series=("BE", "BZ"))
    outcome_dict = compute_t0_relative(hist, event_date, direction, market_index, global_days)
    label = outcome_dict["collapsed_t0_primary"]
    
    # Execution and 20-day path
    future = conn.execute("SELECT DISTINCT event_date FROM bhavcopy WHERE event_date > ? AND event_date <= '2026-09-15' AND symbol = ? AND series IN ('EQ', 'BE', 'BZ') ORDER BY event_date LIMIT 21", (event_date, symbol)).fetchall()
    future_sessions = [r[0] for r in future]
    
    if not future_sessions:
        return {"symbol": symbol, "event_date": event_date, "state": state, "veto": veto_reasons, "fill": None, "immediate_gap": False, "incomplete_20": True, "label": label, "forward_window": False}
        
    next_session = future_sessions[0]
    obs = execution_observation(conn, symbol, event_date, "2099-01-01", plan, rulebook, costs)
    
    fill = obs["fill_price"] if obs and obs.get("no_fill_reason") == "" else None
    immediate_gap = obs["gap_through"] if obs and obs.get("no_fill_reason") == "" else False
    
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
            rows = latest_as_of(conn, "bhavcopy", "2099-01-01", symbol=symbol, event_date=session)
            rows = [r for r in rows if r["series"] in ("EQ", "BE", "BZ")]
            if not rows: continue
            r = rows[0]
            if not r["low_price"]: continue
            
            from src.signals.price_adjustment import UnadjustableWindowError
            try:
                factor = compute_adjustment_factor(conn, symbol, event_date, session)
            except UnadjustableWindowError:
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
                
            from desk.circuit_bands import band_as_of
            band = band_as_of(desk_conn, symbol, session, report_date=session)
            if band.kind == "FIXED" and band.percent is not None:
                lc_denominator += 1
                limit = round((r["prev_close"] * (1 - band.percent/100)) * 20) / 20.0
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
        "lc_denominator": lc_denominator,
        "label": label,
        "forward_window": False
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
            if "2019-10-01" <= row["event_date"]:
                direction = 1 if float(row["return_1d"]) > 0 else -1
                events.append({"symbol": row["symbol"], "event_date": row["event_date"], "direction": direction})
                
    print(f"Loaded {len(events)} events for shadow replay.")
    
    t0 = time.time()
    results = []
    
    with Pool(processes=os.cpu_count() or 4, initializer=init_worker) as pool:
        for i, res in enumerate(pool.imap_unordered(evaluate_single, events, chunksize=100)):
            results.append(res)
            if (i+1) % 1000 == 0:
                print(f"Processed {i+1}/{len(events)} in {time.time()-t0:.1f}s")
                
    print(f"Done processing in {time.time()-t0:.1f}s.")
    
    out_path = Path(__file__).resolve().parents[1] / "data" / "processed" / "shadow_replay_raw.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f)
        
    print(f"Saved raw results to {out_path}.")
    
    # Simple aggregation for docs/desk/shadow_replay_results.md
    primary = [r for r in results if r["event_date"] <= "2025-12-31"]
    descriptive = [r for r in results if "2026-01-01" <= r["event_date"] <= "2026-09-15"]
    
    def format_results(title, subset):
        passed = [r for r in subset if r["state"] == "SCREEN_PASS" and r.get("fill") is not None]
        md = f"## {title}\n\n"
        md += f"Total catalogued events processed: {len(subset)}\n"
        md += f"SCREEN_PASS with fills: {len(passed)}\n"
        
        adverse_20pct = sum(1 for r in passed if r.get("low_falls_20pct"))
        stop_gap_thrus = sum(1 for r in passed if r.get("stop_gap_through"))
        max_mae = max((r.get("max_adverse_fill", 0) for r in passed), default=0)
        avg_mae = np.mean([r.get("max_adverse_fill", 0) for r in passed]) if passed else 0
        
        locked_days = sum(r.get("locked_lc_days", 0) for r in passed)
        lc_denom = sum(r.get("lc_denominator", 0) for r in passed)
        
        md += f"- **Adverse 20% move within 20 sessions**: {adverse_20pct} ({adverse_20pct/len(passed)*100:.1f}%)\n" if passed else "- Adverse 20% move: N/A\n"
        md += f"- **Stop gap-throughs**: {stop_gap_thrus} ({stop_gap_thrus/len(passed)*100:.1f}%)\n" if passed else "- Stop gap-throughs: N/A\n"
        md += f"- **Max adverse excursion (fill)**: {max_mae*100:.1f}% (Avg: {avg_mae*100:.1f}%)\n"
        md += f"- **Locked lower-circuit days**: {locked_days} / {lc_denom}\n"
        
        md += "\n### Veto Reasons (SCREEN_FAIL)\n"
        vetoes = defaultdict(int)
        for r in subset:
            if r["state"] == "SCREEN_FAIL":
                for v in r["veto"]:
                    vetoes[v] += 1
        for v, c in sorted(vetoes.items(), key=lambda x: -x[1]):
            md += f"- {v}: {c}\n"
        
        # Outcomes based on label
        pos = sum(1 for r in passed if r.get("label") is True)
        neg = sum(1 for r in passed if r.get("label") is False)
        missing = len(passed) - pos - neg
        md += f"\n### Outcomes\n"
        md += f"- **Positive (Collapsed relative)**: {pos}\n"
        md += f"- **Negative (Held relative)**: {neg}\n"
        md += f"- **Missing label**: {missing}\n\n"
        return md
        
    results_md = "# Shadow Replay Results\n\n"
    results_md += format_results("Primary Analysis (2019-10-01 to 2025-12-31)", primary)
    results_md += format_results("Descriptive Analysis (2026-01-01 to 2026-09-15)", descriptive)
    
    # Write to docs
    docs_path = Path(__file__).resolve().parents[1] / "docs" / "desk" / "shadow_replay_results.md"
    with open(docs_path, "w", encoding="utf-8") as f:
        f.write(results_md)
        
    print(f"Wrote {docs_path}")

if __name__ == "__main__":
    main()
