"""`desk brief`: the daily decision desk (TRADING_BLUEPRINT.md section 13; session item B5).

Shows only fields that exist today. Model-dependent lines are printed as UNKNOWN with the phase
that will supply them, never as numbers. NO TRADE is a normal outcome. Strategy 0 shows
operational metrics only (seal); the user's manual paper book is shown in full.
"""
import json
from pathlib import Path

from desk.automation import kill_switches, strategy0
from desk.outcome_firewall import OUTCOMES_OPEN

ROOT = Path(__file__).resolve().parents[1]


def _accepted(desk_conn, run_date):
    rows = desk_conn.execute("SELECT * FROM strategy_paper_events WHERE strategy_id='S0' AND event_type='CANDIDATE_ACCEPTED' "
                             'AND decision_date=? ORDER BY symbol', (run_date,)).fetchall()
    return [dict(r) | dict(detail=json.loads(r['detail'])) for r in rows]


def build_brief(praman_conn, desk_conn, run_date, *, rulebook, health_lines=()):
    universe = praman_conn.execute("SELECT COUNT(DISTINCT symbol) FROM bhavcopy WHERE event_date=? AND series='EQ'",
                                   (run_date,)).fetchone()[0]
    screened = dict(desk_conn.execute('SELECT state, COUNT(*) FROM opportunity_log WHERE event_date=? GROUP BY state',
                                      (run_date,)).fetchall())
    run = strategy0.latest_operational(desk_conn, run_date)
    ops = run['operational'] if run else None
    lines = [f'PRAMAN - DAILY DECISION DESK  {run_date}',
             f'Automation level: {rulebook.automation_level} (paper only; no orders are created)',
             '',
             f'Universe scanned: {universe:,} (EQ symbols with a stored session)',
             f"Candidates: {sum(screened.values())} (catalogue events screened by desk scan)",
             f"Passed evidence/data checks: {screened.get('SCREEN_PASS', 0)}",
             'High-confidence model candidates: UNKNOWN (no calibrated model until T4)']
    if ops is None:
        lines += ['Passed risk/portfolio/execution checks: UNKNOWN (Strategy 0 has not run for this date)']
    else:
        order = ops.get('candidate_order') or {}
        lines += [f"Passed risk/portfolio/execution checks: {ops['accepted']} (Strategy 0 paper burn-in)",
                  f"Strategy 0 version {run['strategy_version']}; candidate order "
                  + (f"{order['method']}, seed {order['seed'][:16]} (from the decision date)" if order.get('seed')
                     else order.get('method', 'not recorded')),
                  f"Opened (entry fills settled today): {ops['entries_filled']}; no fill {ops['entries_no_fill']}; "
                  f"fill failures {ops['entries_failed']}; cancelled {ops['entries_cancelled']}; "
                  f"per-trade cap breaches at fill {ops['cap_breaches_at_fill']}",
                  'Rejected by reason: ' + (', '.join(f'{k} {v}' for k, v in sorted(ops['rejected'].items())) or 'none')]
    lines += ['']
    accepted = _accepted(desk_conn, run_date)
    for c in accepted:
        d = c['detail']
        execution = (f"limit order at {d['limit_price']:.2f} for the next session" if d.get('limit_price') is not None
                     else 'next-session open')
        lines += [f"Candidate {c['symbol']}",
                  '  Direction: LONG',
                  '  Calibrated P(profitable): UNKNOWN (T4)',
                  '  Uncertainty: UNKNOWN (T4)',
                  '  Expected net return: UNKNOWN (T3)',
                  '  Expected loss if wrong: UNKNOWN (T5)',
                  '  Expected value: UNKNOWN (T4)',
                  '  Historical analogues: UNKNOWN (T5)',
                  '  Market: UNKNOWN (T1)',
                  '  Sector: UNKNOWN (T1)',
                  '  Evidence: required dimensions present (G2 PASS)',
                  f"  Risk: PASS (stop {d['stop_level']:.2f}; quantity {d['quantity']}; stress loss Rs {d['stress_loss_inr']:,.2f})",
                  f"  Portfolio: PASS (open risk before Rs {d['budget_used_before_inr']:,.2f} of Rs {d['budget_inr']:,.2f})",
                  f'  Execution: {execution}',
                  '  Final state: WATCH (research conditions UNKNOWN until T4; accepted only as a paper burn-in)']
    if ops is not None and not accepted:
        lines += ['NO TRADE - no candidate passed every check today. This is a normal outcome.']
    lines += ['', 'Kill switches:'] + kill_switches.display_lines(desk_conn, 'S0')
    budget = rulebook.risk.capital_allocated_inr * rulebook.risk.max_open_risk_pct / 100
    from desk.gates.engine import _open_risk_used_inr
    from desk.journal.store import open_trade_ids
    manual_risk = _open_risk_used_inr(desk_conn)
    lines += ['', 'Open risk (stress loss):',
              (f"  Strategy 0: Rs {ops['open_risk_inr']:,.2f} of Rs {ops['open_risk_budget_inr']:,.2f} "
               f"({ops['positions_holding']} positions open, pending or exiting)") if ops else '  Strategy 0: no run',
              f'  Manual (strategy_id=manual): Rs {manual_risk:,.2f} of Rs {budget:,.2f}; open trades {open_trade_ids(desk_conn)}',
              '',
              f'Strategy 0 profit/loss and outcome metrics: SEALED until {OUTCOMES_OPEN.isoformat()}. '
              'Only operational metrics are shown.']
    if health_lines:
        lines += ['', 'Data health:'] + [f'  {h}' for h in health_lines]
    return '\n'.join(lines) + '\n'


def health_lines(praman_conn, run_date):
    from desk.ingestion_health import ingestion_health_line, isin_map_health_line, latest_trading_date_line
    return [ingestion_health_line(), latest_trading_date_line(praman_conn), isin_map_health_line(praman_conn, run_date)]


def write_brief(run_date=None, *, out_dir=ROOT/'logs'):
    from desk.lib.connection import get_desk_connection
    from desk.lib.rulebook import load_active_rulebook
    from desk.lib.store import get_live_connection
    praman, desk = get_live_connection(), get_desk_connection()
    try:
        run_date = run_date or praman.execute('SELECT MAX(event_date) FROM bhavcopy').fetchone()[0]
        text = build_brief(praman, desk, run_date, rulebook=load_active_rulebook().rulebook,
                           health_lines=health_lines(praman, run_date))
    finally:
        desk.close()
        praman.close()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f'brief_{run_date}.txt'
    path.write_text(text, encoding='utf-8', newline='\n')
    return path, text
