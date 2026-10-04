"""Structural share-basis test (user request after P8-044; earlier confirmed instance P8-024).

One synthetic 10:1 split between the decision and the exit is driven through every price-handling
path: manual paper open and close, the monitor and its stop, costs and P&L, and Strategy 0's
entry, monitoring and exit. Every recorded price must stay on ONE share basis -- the decision
date's -- and costs and P&L must equal an independent oracle computed from the real post-split
share count at raw prices. Raw evidence fields, explicitly labelled `raw_*`, are excluded.
"""
from datetime import date, datetime, timedelta
import json
from pathlib import Path
import tempfile
import unittest

import yaml

from desk.automation import seal, strategy0
from desk.journal import store as jstore
from desk.lib.connection import get_desk_connection
from desk.lib.costs import load_active_cost_config
from desk.lib.rulebook import DeskRulebook
from desk.monitor import run_monitor
from desk.paper.close import close_approved_trade
from desk.paper.open import open_approved_decision
from desk.risk.officer import compute_position_size, realized_pnl_inr, round_trip_cost_inr
from src.bitemporal.connection import get_connection, init_db
from tests.desk_fixtures import COMPLETE_AXISBANK_THESIS

ROOT = Path(__file__).resolve().parents[1]
SPLIT = 10.0
BAND = (80.0, 130.0)          # every decision-basis price in this scenario lies here
PRICE_KEYS = {'decision_price', 'limit_price', 'stop_level', 'sizing_price', 'price', 'open', 'low', 'stop', 'limit'}


def weekdays(start, n):
    out, d = [], date.fromisoformat(start)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


DAYS = weekdays('2026-08-03', 30)
D, F, S, S2 = DAYS[24], DAYS[25], DAYS[26], DAYS[27]   # decision, fill, split ex-date, stop/exit day
SESSION = {F: (101.5, 103.0, 100.0, 102.0),            # raw, pre-split; limit 100 + 0.5 x 4 = 102
           S: (10.0, 10.2, 9.7, 10.0),                 # raw, post-split: 100 / 97 on the decision basis
           S2: (9.5, 9.6, 9.0, 9.2)}                   # raw: 95 open, 90 low -> a 92 stop is touched


class ShareBasisStructuralTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.praman = get_connection(str(Path(self.temp.name) / 'praman.db'))
        init_db(self.praman)
        self.desk = get_desk_connection(Path(self.temp.name) / 'desk.sqlite')
        self.costs = load_active_cost_config().costs
        raw = yaml.safe_load((ROOT / 'rulebook/desk_rulebook_v3.yaml').read_text(encoding='utf-8'))
        self.rb = DeskRulebook.model_validate(raw)
        self.defects = Path(self.temp.name) / 'defects.md'
        self.defects.write_text('# none open\n', encoding='utf-8')
        for symbol in ('BASISA', 'BASISB', 'BASISC'):
            for day in DAYS[:25]:
                self.bar(symbol, day, 100, 102, 98, 100)          # ATR20 = 4 at the decision
            self.praman.execute('INSERT INTO corporate_actions (symbol,action_type,event_date,knowledge_date,ratio_numerator,'
                                'ratio_denominator,confidence_tier,details,source_file,recorded_at) VALUES (?,?,?,?,?,?,?,?,?,?)',
                                (symbol, 'SPLIT', S, F, SPLIT, 1.0, 'HIGH', 'fixture', 'fixture', F))
        self.praman.commit()

    def tearDown(self):
        self.praman.close()
        self.desk.close()
        self.temp.cleanup()

    def bar(self, symbol, day, o, h, l, c):
        self.praman.execute('INSERT INTO bhavcopy (symbol,event_date,knowledge_date,open_price,high_price,low_price,close_price,'
                            'prev_close,traded_qty,series,source_file,recorded_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                            (symbol, day, day, o, h, l, c, c, 10_000_000, 'EQ', 'fixture', day))
        self.praman.commit()

    def session(self, day):
        for symbol in ('BASISA', 'BASISB', 'BASISC'):
            self.bar(symbol, day, *SESSION[day])

    def manual_decision(self, symbol):
        thesis = dict(COMPLETE_AXISBANK_THESIS, planned_entry=100.0, planned_stop=92.0, planned_target=120.0)
        thesis_id = jstore.record_thesis(self.desk, symbol=symbol, evidence_cutoff=D,
                                         **{k: v for k, v in thesis.items() if k != 'thesis_id'})
        decision_id = jstore.record_decision(
            self.desk, symbol=symbol, as_of_date=D, thesis_id=thesis_id, evidence_bundle_hash='h', gate_results={},
            state='ELIGIBLE', rulebook_version='v3', rulebook_hash='r', cost_config_version='v1', cost_config_hash='c',
            code_commit='c', praman_watermark='w', desk_watermark_value='d', as_of_is_live=True,
            isin_map_built_at='2026-09-01T00:00:00+00:00', position_size=50, stress_loss_inr=1000.0)
        return decision_id, f'{symbol}:{thesis_id}'

    def s0_run(self, day):
        return strategy0.run(self.praman, self.desk, day, rulebook=self.rb, costs=self.costs, rulebook_file='v3',
                             rulebook_hash='r', cost_config_hash='k', code_commit='c', praman_watermark='w',
                             today=day, defect_path=self.defects, isin_status='OK')

    def test_one_share_basis_through_every_price_path(self):
        noon = lambda day: datetime.fromisoformat(day + 'T12:00:00+00:00')
        # Decision day: two manual decisions; Strategy 0 accepts BASISC.
        decision_a, trade_a = self.manual_decision('BASISA')
        decision_b, trade_b = self.manual_decision('BASISB')
        q_screen = int(compute_position_size(100.0, 92.0, self.rb, 0, 0, 0, costs=self.costs))
        plan = dict(decision_price=100.0, atr20=4.0, stop_level=92.0, quantity=q_screen, adv_turnover=1e10,
                    stress=dict(stress_loss_inr=4000.0, floor_component_inr=1.0, worst_gap_component_inr=4000.0,
                                locked_circuit_loss_inr=None))
        self.desk.execute('INSERT INTO opportunity_log(symbol,event_date,knowledge_date,recorded_at,inputs,evidence_bundle_hash,'
                          'gate_results,state,reasons,content_hash,code_commit,praman_watermark,desk_watermark,rulebook_hash,'
                          "cost_config_hash) VALUES('BASISC',?,?,?,?,'h','{}','SCREEN_PASS','[]','h','c','w','d','r','k')",
                          (D, D, D, json.dumps(dict(plan=plan))))
        self.desk.commit()
        self.assertEqual(self.s0_run(D)['accepted'], 1)

        # Fill session (pre-split): both manual entries and Strategy 0's entry fill at 101.5.
        self.session(F)
        for decision_id in (decision_a, decision_b):
            self.assertEqual(open_approved_decision(self.praman, self.desk, decision_id, costs=self.costs,
                                                    cost_config_hash='h', now=noon(D)).price, 101.5)
        self.s0_run(F)

        # Split ex-date: raw prices fall tenfold; nothing may stop out (decision basis 100 / 97 > 92).
        self.session(S)
        report = run_monitor(self.praman, self.desk, S)
        self.assertEqual(report['exits_triggered'], [])
        self.s0_run(S)
        self.assertEqual([e for e in self._s0_events() if e['event_type'] == 'EXIT_FILLED'], [])

        # Manual close of B requested on S fills at S2's open; A and C are stopped on S2 at 92.
        from desk.paper.close import PendingClose
        pending = close_approved_trade(self.praman, self.desk, trade_b, reason='manual', costs=self.costs,
                                       cost_config_hash='h', now=noon(S))
        self.assertIsInstance(pending, PendingClose)                  # S2 not ingested yet
        jstore.record_journal_event(self.desk, event_type='PAPER_CLOSE_PENDING', trade_id=trade_b,
                                    detail={'not_before_date': pending.not_before_date, 'reason': pending.reason})
        self.session(S2)
        report = run_monitor(self.praman, self.desk, S2)
        self.assertEqual([(c['trade_id'], c['status']) for c in report['pending_closes_completed']], [(trade_b, 'FILLED')])
        self.assertEqual([(x['trade_id'], x['reason']) for x in report['exits_triggered']], [(trade_a, 'stop_touch')])
        self.s0_run(S2)

        # 1. Every recorded price is on the decision basis.
        manual = [dict(r) for r in self.desk.execute('SELECT * FROM paper_trade_events ORDER BY event_id')]
        recorded = [(f"{m['trade_id']} {m['event_type']} {k}", m[k]) for m in manual for k in ('price', 'stop', 'target')]
        raw_seen = []
        for e in self._s0_events():
            for k, v in e['detail'].items():
                if k.startswith('raw_') and isinstance(v, (int, float)):
                    raw_seen.append(v)
                elif k in PRICE_KEYS and isinstance(v, (int, float)):
                    recorded.append((f"S0 {e['event_type']} {k}", v))
        off_basis = [(name, v) for name, v in recorded if not BAND[0] <= v <= BAND[1]]
        self.assertEqual(off_basis, [])
        # The scenario really crossed the split: raw evidence is post-split, the factor is applied.
        self.assertTrue(any(v < 20 for v in raw_seen))
        monitored = [e['detail'] for e in self._s0_events() if e['event_type'] == 'MONITORED']
        self.assertEqual([m['factor'] for m in monitored], [SPLIT, SPLIT])
        self.assertGreater(len(recorded), 15)

        # 2. Costs equal the economic costs on the real post-split shares at raw prices.
        opened = {m['trade_id']: m for m in manual if m['event_type'] == 'OPEN'}
        closed = {m['trade_id']: m for m in manual if m['event_type'] == 'CLOSE'}
        raw_exit = {trade_a: 9.2, trade_b: 9.5}                  # stop touch at 92 / S2 open, raw
        for trade in (trade_a, trade_b):
            o, c = opened[trade], closed[trade]
            self.assertAlmostEqual(o['buy_cost_inr'], round_trip_cost_inr(101.5, 50, self.costs, 'buy'))
            self.assertAlmostEqual(c['sell_cost_inr'], round_trip_cost_inr(raw_exit[trade], 50 * SPLIT, self.costs, 'sell'))
            # 3. P&L equals the oracle computed on real shares and raw prices.
            economic = raw_exit[trade] * 50 * SPLIT - 101.5 * 50 - o['buy_cost_inr'] - c['sell_cost_inr']
            pnl = realized_pnl_inr(o['price'], c['price'], o['quantity'], o['buy_cost_inr'], c['sell_cost_inr'])
            self.assertAlmostEqual(pnl, economic, places=6)

        entry = next(e for e in self._s0_events() if e['event_type'] == 'ENTRY_FILLED')['detail']
        exit_ = next(e for e in self._s0_events() if e['event_type'] == 'EXIT_FILLED')['detail']
        self.assertEqual((entry['price'], exit_['price'], exit_['kind']), (101.5, 92.0, 'stop_touch'))
        self.assertEqual(entry['quantity'], exit_['quantity'])                       # one basis, one count
        self.assertAlmostEqual(exit_['sell_cost_inr'], round_trip_cost_inr(9.2, entry['quantity'] * SPLIT, self.costs, 'sell'))
        economic = 9.2 * entry['quantity'] * SPLIT - 101.5 * entry['quantity'] - entry['buy_cost_inr'] - exit_['sell_cost_inr']
        self.assertAlmostEqual(seal.realized_pnl(entry, exit_), economic, places=6)
        self.assertFalse(entry['per_trade_cap_breach_at_fill'])                       # v2 limit sizing

    def _s0_events(self):
        return [dict(r) | dict(detail=json.loads(r['detail']))
                for r in self.desk.execute('SELECT * FROM strategy_paper_events ORDER BY event_id')]


if __name__ == '__main__':
    unittest.main()
