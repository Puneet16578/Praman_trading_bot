import numpy as np

from desk.lib.connection import get_desk_connection
from desk.outcome_firewall import require_outcome_access
from desk.process_quality import audit_trade_process

def evaluate(month: str = None):
    desk_conn = get_desk_connection()
    try:
        return _evaluate_connection(desk_conn, month)
    finally:
        desk_conn.close()


def _evaluate_connection(desk_conn, month=None):
    
    # 1. Opportunity counts by state
    if month:
        rows = desk_conn.execute("SELECT state, COUNT(*) FROM opportunity_log WHERE event_date LIKE ? GROUP BY state", (f"{month}%",)).fetchall()
        print(f"=== Opportunity Counts for {month} ===")
    else:
        rows = desk_conn.execute("SELECT state, COUNT(*) FROM opportunity_log GROUP BY state").fetchall()
        print("=== Opportunity Counts (All Time) ===")
    
    for state, count in rows:
        print(f"{state}: {count}")
    print()
    
    # 2. Paper trades evaluation
    print("=== Paper Trades Evaluation ===")
    
    # Fetch all closed paper trades
    q = """
    SELECT o.trade_id, o.event_date as open_date, o.price as open_price, o.quantity as qty, o.buy_cost_inr, 
           c.event_date as close_date, c.price as close_price, c.sell_cost_inr, c.reason
    FROM paper_trade_events o
    JOIN paper_trade_events c ON o.trade_id = c.trade_id
    WHERE o.event_type = 'OPEN' AND c.event_type = 'CLOSE'
    """
    # Check the entry date before fetching any corresponding exit price.
    valid_trades = []
    entries = desk_conn.execute("SELECT trade_id,event_date FROM paper_trade_events WHERE event_type='OPEN' "
                                "AND (? IS NULL OR event_date LIKE ?)", (month, f'{month}%')).fetchall()
    for entry in entries:
        try:
            require_outcome_access(entry['event_date'])
        except ValueError:
            continue
        valid_trades.extend(desk_conn.execute(q + ' AND o.trade_id=? ORDER BY c.event_date,c.event_id',
                                              (entry['trade_id'],)).fetchall())
    valid_trades.sort(key=lambda r: (r['close_date'], r['trade_id']))
            
    n = len(valid_trades)
    print(f"Count (n): {n}")
    if n < 30:
        print("WARNING: Small sample size (n < 30). Metrics may not be statistically significant.")
        
    if n == 0:
        return
        
    gross_returns = []
    net_returns = []
    wins = []
    losses = []
    process_good = 0
    process_bad = 0
    
    quadrants = {
        "Deserved Success (Good Process, Good Outcome)": 0,
        "Dumb Luck (Bad Process, Good Outcome)": 0,
        "Bad Luck (Good Process, Bad Outcome)": 0,
        "Poetic Justice (Bad Process, Bad Outcome)": 0
    }
    
    
    # Load market index
    market_index = {}
    try:
        import csv
        from pathlib import Path
        index_path = Path(__file__).resolve().parents[1] / "data" / "processed" / "market_index.csv"
        with open(index_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                market_index[row["date"]] = float(row["index_level"])
    except:
        pass

    rel_returns = []
    
    for t in valid_trades:
        gross_pnl = (t["close_price"] - t["open_price"]) * t["qty"]
        gross_inv = t["open_price"] * t["qty"]
        gross_ret = gross_pnl / gross_inv if gross_inv else 0
        
        net_pnl = gross_pnl - (t["buy_cost_inr"] or 0) - (t["sell_cost_inr"] or 0)
        net_ret = net_pnl / gross_inv if gross_inv else 0
        
        # Relative to market index
        idx_open = market_index.get(t["open_date"])
        idx_close = market_index.get(t["close_date"])
        if idx_open and idx_close and idx_open > 0:
            market_ret = (idx_close - idx_open) / idx_open
            rel_returns.append(net_ret - market_ret)
        
        gross_returns.append(gross_ret)
        net_returns.append(net_ret)
        
        if net_ret > 0:
            wins.append(net_ret)
        elif net_ret < 0:
            losses.append(net_ret)
            
        # Process check
        is_good_process = audit_trade_process(desk_conn, t['trade_id'])['good']
        
        if is_good_process:
            process_good += 1
            if net_ret > 0:
                quadrants["Deserved Success (Good Process, Good Outcome)"] += 1
            else:
                quadrants["Bad Luck (Good Process, Bad Outcome)"] += 1
        else:
            process_bad += 1
            if net_ret > 0:
                quadrants["Dumb Luck (Bad Process, Good Outcome)"] += 1
            else:
                quadrants["Poetic Justice (Bad Process, Bad Outcome)"] += 1

    net_returns_arr = np.array(net_returns)
    total_gross = np.sum(gross_returns)
    total_net = np.sum(net_returns)
    avg_win = np.mean(wins) if wins else 0
    avg_loss = np.mean(losses) if losses else 0
    
    # Expectancy = (Win % * Avg Win) - (Loss % * |Avg Loss|)
    win_rate = len(wins) / n
    loss_rate = len(losses) / n
    expectancy = (win_rate * avg_win) - (loss_rate * abs(avg_loss))
    
    # Max Drawdown (manual calculation)
    max_dd = 0.0
    if n > 0:
        # returns to cumulative product
        cum_ret = np.cumprod(1 + net_returns_arr)
        cum_ret = np.insert(cum_ret, 0, 1.0)
        running_max = np.maximum.accumulate(cum_ret)
        drawdowns = (cum_ret - running_max) / running_max
        max_dd = np.min(drawdowns) if len(drawdowns) > 0 else 0.0
    
    avg_rel_ret = np.mean(rel_returns) if rel_returns else 0
    
    print(f"Gross Return (sum): {total_gross*100:.2f}%")
    print(f"Net Return (sum): {total_net*100:.2f}%")
    print(f"Return vs Market Index (avg net diff): {avg_rel_ret*100:.2f}%")
    print(f"Average Win: {avg_win*100:.2f}%")
    print(f"Average Loss: {avg_loss*100:.2f}%")
    print(f"Expectancy: {expectancy*100:.2f}% per trade")
    print(f"Max Drawdown: {max_dd*100:.2f}%")
    
    print(f"\nRules Followed (Good Process): {process_good}")
    print(f"Overrides (Bad Process): {process_bad}")
    
    print("\nProcess-by-Outcome Quadrants:")
    for k, v in quadrants.items():
        print(f"  {k}: {v}")
