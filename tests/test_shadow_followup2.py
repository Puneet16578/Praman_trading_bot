import unittest
from desk.shadow_followup2 import limit_fill, analyze
from tests.desk_fixtures import make_test_rulebook, make_test_costs


class LimitEntryTest(unittest.TestCase):
    def test_late_known_low_uses_replay_knowledge_cutoff(self):
        import sqlite3
        from src.bitemporal.schema import BHAVCOPY
        from scripts.desk_shadow_followup2 import next_session_bar
        conn=sqlite3.connect(':memory:')
        conn.row_factory=sqlite3.Row
        try:
            conn.execute(BHAVCOPY.ddl)
            for known,low in [('2020-01-03',106),('2026-10-03',104)]:
                conn.execute('INSERT INTO bhavcopy (symbol,event_date,knowledge_date,open_price,high_price,low_price,close_price,prev_close,traded_qty,series,source_file,recorded_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                    ('EXAMPLE','2020-01-03',known,110,115,low,112,100,1000,'EQ','fixture',known))
            row=dict(symbol='EXAMPLE',event_date='2020-01-02',state='SCREEN_PASS',execution=dict(fill_date='2020-01-03'))
            bar=next_session_bar(conn,row,dict(run_date='2026-10-04',price_cutoff='2026-10-01'))
            self.assertEqual(bar['low_price'],104)
            self.assertEqual(limit_fill(dict(decision_price=100,atr20=10),bar['open_price'],bar['low_price'])['fill'],105)
        finally:
            conn.close()

    def test_price_cases_and_missing_low(self):
        plan = dict(decision_price=100, atr20=10)
        for opening, low, expected, status in [(103, None, 103, 'FILL_OPEN'),
            (105, 100, 105, 'FILL_OPEN'), (110, 105, 105, 'FILL_LIMIT'),
            (110, 106, None, 'NO_FILL'), (110, None, None, 'UNKNOWN'),
            (None, 100, None, 'UNKNOWN'), (110, 111, None, 'UNKNOWN')]:
            value = limit_fill(plan, opening, low)
            self.assertEqual(value['fill'], expected)
            self.assertEqual(value['status'], status)

    def test_conditional_metrics_and_common_fills(self):
        rows=[]
        for i, (opening, low, adverse) in enumerate([(100,99,False),(130,104,True),(140,120,None)]):
            plan=dict(decision_price=100,atr20=10,quantity=400,stop_level=90)
            rows.append(dict(event_date=f'2020-01-0{i+2}',state='SCREEN_PASS',plan=plan,adverse20=adverse,
                baseline=dict(fill=opening,status='FILL_OPEN'),limit=limit_fill(plan,opening,low)))
        result=analyze(rows,make_test_rulebook(),make_test_costs(),replicates=50)
        self.assertEqual(result['variants']['baseline']['fills'],3)
        self.assertEqual(result['variants']['limit']['fills'],2)
        self.assertEqual(result['variants']['baseline']['breaches'],2)
        self.assertEqual(result['variants']['limit']['breaches'],1)
        self.assertEqual(result['variants']['limit']['conditional_excess_pct']['median']['n_events'],1)
        self.assertEqual(result['variants']['limit']['adverse20_rate']['estimate'],.5)
        self.assertEqual(result['common_fills']['n'],2)
        self.assertEqual(result['common_fills']['adverse20_rate']['difference']['estimate'],0)
        self.assertEqual([r['plan']['quantity'] for r in rows],[400]*3)

    def test_conventions_share_date_draws(self):
        # Identical conventions over several dates: paired draws give an exactly zero interval.
        rows=[]
        for i,(opening,adverse) in enumerate([(100,False),(130,True),(101,True),(125,False)]):
            plan=dict(decision_price=100,atr20=10,quantity=400,stop_level=90)
            fill=dict(fill=opening,status='FILL_OPEN')
            rows.append(dict(event_date=f'2020-01-0{i+2}',state='SCREEN_PASS',plan=plan,adverse20=adverse,
                baseline=fill,limit=dict(fill)))
        result=analyze(rows,make_test_rulebook(),make_test_costs(),replicates=200)
        for key in ('fill_rate','per_trade_breach_rate','adverse20_rate'):
            self.assertEqual(result['differences'][key]['interval95'],[0.0,0.0],key)
            self.assertEqual(result['differences'][key]['estimate'],0)

    def test_no_breaches_are_unavailable_sizes(self):
        row=dict(event_date='2020-01-02',state='SCREEN_PASS',adverse20=False,
            plan=dict(decision_price=100,atr20=10,stop_level=90,quantity=1),
            baseline=dict(fill=100,status='FILL_OPEN'),limit=dict(fill=100,status='FILL_OPEN'))
        result=analyze([row],make_test_rulebook(),make_test_costs(),replicates=10)
        self.assertIsNone(result['variants']['limit']['conditional_excess_pct']['median']['estimate'])

    def test_unknown_bar_is_not_a_safe_fill(self):
        row=dict(event_date='2020-01-02',state='SCREEN_PASS',adverse20=True,
            plan=dict(decision_price=100,atr20=10,stop_level=90,quantity=1),
            baseline=dict(fill=None,status='UNKNOWN'),limit=dict(fill=None,status='UNKNOWN'))
        value=analyze([row],make_test_rulebook(),make_test_costs(),replicates=10)['variants']['limit']
        self.assertEqual(value['fill_rate']['estimate'],0)
        self.assertEqual(value['unknown_inputs'],1)
        self.assertEqual(value['observed_no_touch'],0)
        self.assertIsNone(value['per_trade_breach_rate']['estimate'])
        self.assertIsNone(value['adverse20_rate']['estimate'])

    def test_forward_event_rejected_before_price_access(self):
        from datetime import date
        from unittest.mock import patch
        from desk.outcome_firewall import ForwardOutcomeBlocked
        with patch('desk.outcome_firewall.market_today',return_value=date(2026,10,4)), self.assertRaises(ForwardOutcomeBlocked):
            analyze([dict(event_date='2026-09-16',state='SCREEN_PASS')],make_test_rulebook(),make_test_costs(),replicates=5)
