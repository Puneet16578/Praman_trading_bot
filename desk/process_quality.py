"""Audit recorded entry and exit evidence, independent of the trade's return."""
import json
from datetime import datetime

from desk.gates.checks import g8_thesis_completeness, PASS
from desk.journal.store import get_decision, get_thesis


def _at_or_before(left, right):
    return datetime.fromisoformat(left) <= datetime.fromisoformat(right)


def audit_trade_process(conn, trade_id):
    events = [dict(r) for r in conn.execute(
        'SELECT * FROM paper_trade_events WHERE trade_id=? ORDER BY event_id', (trade_id,))]
    opened = next((r for r in events if r['event_type'] == 'OPEN'), None)
    closed = next((r for r in events if r['event_type'] == 'CLOSE'), None)
    if opened is None:
        return dict(good=False, thesis_complete_at_entry=False, unlogged_violations=1,
                    g7_override=False, exit_recorded=False, reasons=['Missing entry record.'])
    decision = get_decision(conn, opened['decision_id']) if opened['decision_id'] else None
    thesis = get_thesis(conn, decision['thesis_id']) if decision and decision['thesis_id'] else None
    complete = bool(thesis and g8_thesis_completeness(thesis).result == PASS
                    and thesis.get('sector') and thesis.get('drivers')
                    and _at_or_before(thesis['recorded_at'], opened['recorded_at'])
                    and _at_or_before(decision['recorded_at'], opened['recorded_at'])
                    and thesis['evidence_cutoff'] <= opened['event_date'] <= thesis['horizon'])
    journal = [dict(r) for r in conn.execute(
        'SELECT * FROM journal_events WHERE trade_id=? OR decision_id=? ORDER BY journal_event_id',
        (trade_id, opened['decision_id']))]
    override = bool(decision and decision.get('override_reason')) or any(r['event_type'] == 'G7_OVERRIDE' for r in journal)
    violations = sum(r['event_type'] == 'UNLOGGED_RULE_VIOLATION'
                     or (r['event_type'] == 'RULE_VIOLATION' and json.loads(r['detail']).get('logged') is False)
                     for r in journal)
    if not decision or decision['state'] != 'ELIGIBLE':
        violations += 1
    prior = opened
    for event in events:
        if event['event_type'] != 'ADJUST':
            continue
        widened = event['stop'] < prior['stop'] and not event['reason'].lower().startswith('corporate action:')
        logged = any(r['event_type'] == 'STOP_WIDENED' and (r['reason'] or '').strip()
                     and json.loads(r['detail']).get('event_date') == event['event_date']
                     and _at_or_before(r['recorded_at'], event['recorded_at']) for r in journal)
        if widened and not logged:
            violations += 1
        prior = event
    exit_recorded = False
    if closed and (closed['reason'] or '').strip():
        for row in journal:
            if not _at_or_before(opened['recorded_at'], row['recorded_at']) or not _at_or_before(row['recorded_at'], closed['recorded_at']):
                continue
            detail = json.loads(row['detail'])
            if row['event_type'] in ('MANUAL_CLOSE_REQUEST', 'PAPER_CLOSE_PENDING'):
                reason = row['reason'] or detail.get('reason', '')
                exit_recorded |= bool(reason.strip() and reason == closed['reason'])
            elif row['event_type'] == 'EXIT_TRIGGER':
                exit_recorded |= bool(detail.get('trigger') in ('price', 'time', 'evidence', 'risk', 'portfolio')
                                      and detail.get('event_date') == closed['event_date']
                                      and row['reason'] == closed['reason'])
    reasons = []
    if not complete:
        reasons.append('Thesis was missing, incomplete, expired, or recorded after entry.')
    if violations:
        reasons.append(f'{violations} unlogged rule violation(s).')
    if override:
        reasons.append('G7 override recorded on the decision or trade.')
    if not exit_recorded:
        reasons.append('No matching recorded trigger or reasoned manual-close request before exit.')
    return dict(good=not reasons, thesis_complete_at_entry=complete, unlogged_violations=violations,
                g7_override=override, exit_recorded=exit_recorded, reasons=reasons)
