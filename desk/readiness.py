"""Status evidence for starting small and, separately, for later scaling."""
from datetime import date
import json
from pathlib import Path
import re

from desk.process_quality import audit_trade_process
from shared.market_time import market_today


def open_defects(path):
    """Open high/critical and open-but-unclassified defect IDs. An explicit closure marker, added
    without rewriting the entry's history, overrides earlier open wording: `**CLOSED` in the
    summary-table row's status cell, or a line starting `**Status.** Closed` in the entry's section."""
    text = Path(path).read_text(encoding='utf-8')
    high, unknown, closed = set(), set(), set()
    for line in text.splitlines():
        if not re.match(r'\| P\d+-\d+ \|', line):
            continue
        columns = line.split('|')
        if re.search(r'\*\*CLOSED\b', columns[-2]):
            closed.add(columns[1].strip())
        if re.search(r'not fixed|\bopen\b|deferred', columns[-2], re.I) and re.search(r'high|critical', columns[3], re.I):
            high.add(columns[1].strip())
    for section in re.split(r'(?m)^## ', text)[1:]:
        found = re.match(r'(P\d+-\d+)', section)
        if found and re.search(r'(?m)^\*\*Status\.\*\*\s*Closed\b', section):
            closed.add(found[1])
        if not found or not (re.search(r'\(open\)', section.splitlines()[0], re.I)
                             or re.search(r'\*\*Status\.\*\*\s*Open', section, re.I)):
            continue
        severity = re.search(r'\*\*Severity\.\*\*\s*(High|Critical|Medium|Low)', section, re.I)
        if severity and severity[1].lower() in ('high','critical'):
            high.add(found[1])
        elif not severity:
            unknown.add(found[1])
    return sorted(high - closed), sorted(unknown - closed)


def gate_progress(conn, rulebook, *, today=None, defect_path=None):
    if rulebook.operational_gate is None or rulebook.edge_confidence_gate is None:
        return {'operational_gate': {'status':'UNAVAILABLE', 'checks':{}},
                'edge_confidence_gate': {'status':'UNAVAILABLE', 'checks':{}}}
    today = today or market_today()
    op, edge = rulebook.operational_gate, rulebook.edge_confidence_gate
    events = [dict(r) for r in conn.execute('SELECT * FROM paper_trade_events ORDER BY event_date,event_id')]
    opens = [r for r in events if r['event_type']=='OPEN' and r['event_date'] <= today.isoformat()]
    closed = [r for r in events if r['event_type']=='CLOSE' and r['event_date'] <= today.isoformat()]
    days = max(0, (today-date.fromisoformat(min(r['event_date'] for r in opens))).days) if opens else 0
    audits = {r['trade_id']:audit_trade_process(conn,r['trade_id']) for r in opens}
    journal = [dict(r) for r in conn.execute('SELECT * FROM journal_events')]
    explicit = sum(r['event_type']=='UNLOGGED_RULE_VIOLATION' or
                   (r['event_type']=='RULE_VIOLATION' and json.loads(r['detail']).get('logged') is False) for r in journal)
    # Explicit events are already included in each linked trade audit. Global or
    # orphaned violation records must also prevent a falsely clean gate.
    linked_explicit = sum(r['event_type']=='UNLOGGED_RULE_VIOLATION' or
                         (r['event_type']=='RULE_VIOLATION' and json.loads(r['detail']).get('logged') is False)
                         for r in journal if r['trade_id'] in audits or r['decision_id'] in {e['decision_id'] for e in opens})
    violations = explicit + max(0, sum(a['unlogged_violations'] for a in audits.values())-linked_explicit)
    risks, breaches, unknown_risk = {}, 0, 0
    budget = rulebook.risk.capital_allocated_inr * rulebook.risk.max_open_risk_pct/100
    for row in events:
        if row['event_date'] > today.isoformat():
            continue
        if row['event_type']=='OPEN':
            decision = conn.execute('SELECT stress_loss_inr FROM decisions WHERE decision_id=?',(row['decision_id'],)).fetchone()
            if decision is None or decision[0] is None:
                unknown_risk += 1
            else:
                risks[row['trade_id']] = decision[0]
        elif row['event_type']=='ADJUST':
            # An adjustment without a recorded updated stress estimate cannot
            # prove that the historic budget stayed intact.
            unknown_risk += 1
        elif row['event_type']=='CLOSE':
            risks.pop(row['trade_id'],None)
        breaches += sum(risks.values()) > budget
    breaches += sum(r['event_type']=='OPEN_RISK_BUDGET_BREACH' for r in journal)
    high, unclassified = open_defects(defect_path or Path(__file__).resolve().parents[1]/'docs/DEFECT_REGISTER.md')
    recorded_exits = sum(audits.get(r['trade_id'],{}).get('exit_recorded',False) for r in closed)
    def check(value, required, passed):
        return dict(value=value, required=required, passed=bool(passed))
    checks = {
        'calendar_days':check(days,op.min_calendar_days,days>=op.min_calendar_days),
        'closed_paper_trades':check(len(closed),op.min_closed_paper_trades,len(closed)>=op.min_closed_paper_trades),
        'unlogged_rule_violations':check(violations,op.max_unlogged_rule_violations,violations<=op.max_unlogged_rule_violations),
        'open_risk_budget_breaches':check(breaches,op.max_open_risk_budget_breaches,breaches<=op.max_open_risk_budget_breaches and unknown_risk==0),
        'recorded_exits':check(recorded_exits,len(closed),not op.require_recorded_exit_on_every_trade or recorded_exits==len(closed)),
        'open_high_severity_defects':check(high,op.max_open_high_severity_defects,len(high)<=op.max_open_high_severity_defects and not unclassified),
    }
    count = conn.execute('SELECT COUNT(*) FROM opportunity_log').fetchone()[0]
    regimes = set()
    for row in conn.execute('SELECT inputs FROM opportunity_log'):
        regime = json.loads(row[0]).get('market_regime')
        if isinstance(regime,str) and regime.strip():
            regimes.add(regime)
    edge_checks = {
        'logged_opportunities':check(count,edge.min_logged_opportunities,count>=edge.min_logged_opportunities),
        'distinct_market_regimes':check(sorted(regimes),edge.min_distinct_market_regimes,len(regimes)>=edge.min_distinct_market_regimes),
        'out_of_sample_evaluation':check('NOT_EVALUABLE',True,False),
        'positive_expectancy_after_costs':check('NOT_EVALUABLE',True,False),
        'bootstrap_lower_bound':check('NOT_EVALUABLE',f'{edge.bootstrap_confidence_level:.0%} lower bound > {edge.bootstrap_lower_bound_must_exceed}',False),
        'equal_weighted_market_comparison':check('NOT_EVALUABLE',True,False),
        'neighbouring_parameter_stability':check('NOT_EVALUABLE',True,False),
    }
    return dict(operational_gate=dict(status='PASS' if all(c['passed'] for c in checks.values()) else 'NOT_MET',
                checks=checks, unknown_risk_records=unknown_risk, unclassified_open_defects=unclassified),
                edge_confidence_gate=dict(status='NOT_EVALUABLE',checks=edge_checks))


def print_gate_progress(conn, rulebook):
    for name, gate in gate_progress(conn,rulebook).items():
        print(f"{name}: {gate['status']}")
        for name, check in gate['checks'].items():
            print(f"  {name}: {check['value']} (required {check['required']}; {'met' if check['passed'] else 'not met'})")
        if gate.get('unknown_risk_records'):
            print(f"  Unverified risk records: {gate['unknown_risk_records']}")
        if gate.get('unclassified_open_defects'):
            print(f"  Open defects awaiting severity review: {gate['unclassified_open_defects']}")
