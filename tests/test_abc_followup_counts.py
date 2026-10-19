import sqlite3
import unittest
from datetime import datetime
from unittest.mock import patch

from scripts.abc_followup_counts import BoundedInputs, available_at, steps_for, parse_dividend, asm_active, event_inputs


class FollowupBoundaryTest(unittest.TestCase):
    def test_stream_never_evaluates_a_future_price(self):
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        def forbidden():
            raise AssertionError('Post-D price was accessed')
        conn.create_function('forbidden', 0, forbidden)
        try:
            conn.executescript('''
                CREATE TABLE base(row_id,symbol,event_date,knowledge_date,close_value,series,traded_qty);
                INSERT INTO base VALUES(1,'TEST','2024-01-01','2024-01-01',100,'EQ',1000);
                INSERT INTO base VALUES(2,'TEST','2024-01-02','2024-01-02',101,'EQ',1000);
                INSERT INTO base VALUES(3,'TEST','2024-01-03','2024-01-01',999,'EQ',1000);
                CREATE VIEW bhavcopy AS SELECT *, CASE WHEN event_date>'2024-01-02'
                    THEN forbidden() ELSE close_value END close_price FROM base;
                CREATE TABLE corporate_actions(row_id,symbol,action_type,event_date,knowledge_date,ratio_numerator,ratio_denominator);
            ''')
            with patch('scripts.abc_followup_counts.load_isin_map', return_value={'TEST': 'INE000000001'}):
                records = list(event_inputs(conn, {'2024-01-02': [{'symbol': 'TEST', 'return_1d': -.01}]}, peers=False))
            self.assertEqual(len(records), 1)
            self.assertAlmostEqual(records[0][2]['market'], .01)
        finally:
            conn.close()

    def test_asm_uses_both_stored_mechanisms(self):
        self.assertTrue(asm_active({'ASM_LT': 'I'}))
        self.assertTrue(asm_active({'ASM_ST': 'I'}))
        self.assertFalse(asm_active({'ASM_LT': None, 'GSM': 'I'}))

    def test_bar_ceiling_applies_before_read_even_for_misdated_future_bar(self):
        conn = sqlite3.connect(':memory:')
        try:
            conn.execute('CREATE TABLE bhavcopy(event_date,knowledge_date,close_price)')
            conn.executemany('INSERT INTO bhavcopy VALUES(?,?,?)', [
                ('2024-01-02', '2024-01-02', 100),
                ('2024-01-03', '2024-01-01', 999),
            ])
            bounded = BoundedInputs(conn, '2024-01-02', '2024-01-01')
            self.assertEqual(bounded.execute('SELECT close_price FROM bhavcopy').fetchall(), [(100,)])
            with self.assertRaises(ValueError):
                bounded.execute('DELETE FROM bhavcopy')
        finally:
            conn.close()

    def test_late_filing_cannot_remove_event_at_any_cutoff(self):
        sessions = ['2024-01-01', '2024-01-02', '2024-01-03']
        inputs = dict(market=0, peer_status='KNOWN', peer_share=0, previous_close=100)
        gates = dict(g3=False, g5='PASS')
        for stamp, cutoff in [('2024-01-02 18:00:01', '2024-01-02 18:00:00'),
                              ('2024-01-02 23:59:01', '2024-01-02 23:59:00'),
                              ('2024-01-03 09:00:01', '2024-01-03 09:00:00')]:
            row = dict(seq_id='test', category='Dividend', description='Dividend record date 03-Jan-2024',
                       knowledge_date=stamp[:10], sort_timestamp=stamp)
            for group, step in [('Material news', 1), ('Unclear', 2)]:
                flags, *_ = steps_for([row], '2024-01-02', datetime.fromisoformat(cutoff), sessions,
                                      {'Dividend': group}, inputs, gates, [], [row], 1)
                self.assertFalse(flags[step])
                self.assertFalse(flags[6])
                row_on_time = row | {'sort_timestamp': cutoff, 'knowledge_date': cutoff[:10]}
                flags, *_ = steps_for([row_on_time], '2024-01-02', datetime.fromisoformat(cutoff), sessions,
                                      {'Dividend': group}, inputs, gates, [], [row_on_time], 1)
                self.assertTrue(flags[step])
                self.assertTrue(flags[6])

    def test_date_only_evidence_waits_until_next_open(self):
        row = dict(knowledge_date='2024-01-02', sort_timestamp='2024-01-02')
        self.assertEqual(available_at(row, ['2024-01-02', '2024-01-03']), datetime(2024, 1, 3, 9, 15))

    def test_sensitivity_changes_only_filing_lookbacks(self):
        sessions = [f'2024-01-{i:02d}' for i in range(1, 10)]
        for lookback in (1, 5, 10):
            flags, *_ = steps_for([], '2024-01-08', datetime(2024, 1, 9, 9), sessions, {},
                                  dict(market=0, peer_status='KNOWN', peer_share=0, previous_close=100),
                                  dict(g3=False, g5='PASS'), [{'knowledge_date': '2024-01-03'}], [], lookback)
            self.assertTrue(flags[3])

    def test_weekend_filing_is_closure_bridge_not_next_morning(self):
        row = dict(seq_id='test', category='Material', description='', knowledge_date='2024-01-06',
                   sort_timestamp='2024-01-06 10:00:00')
        _, timing, *_ = steps_for([row], '2024-01-05', datetime(2024, 1, 8, 9),
                                 ['2024-01-04', '2024-01-05', '2024-01-08'], {'Material': 'Material news'},
                                 dict(market=0, peer_status='KNOWN', peer_share=0, previous_close=100),
                                 dict(g3=False, g5='PASS'), [], [], 1)
        self.assertEqual(timing, [0, 0, 0, 1])

    def test_dividend_parser_does_not_confuse_meeting_date_with_record_date(self):
        row = dict(category='Dividend', description='Meeting 01-Jan-2024; record date 15-Jan-2024. Dividend Rs. 3 per share.')
        self.assertEqual(parse_dividend(row), ('2024-01-15', 3.0, 'parsed'))
        self.assertEqual(parse_dividend(row | {'description': 'Meeting on 01-Jan-2024 to consider a dividend'})[0], None)


def funnel_store(day_index, filing_stamp, *, sessions=280, after=10, symbols=6):
    """An in-memory store whose bhavcopy is a view: any price or volume of a bar after D raises.
    Every other table uses the real schema (src.bitemporal.schema)."""
    from datetime import date, timedelta
    from src.bitemporal.connection import init_db
    from scripts.abc_followup_counts import draft_map
    days, d = [], date(2023, 1, 2)
    while len(days) < sessions + after:
        if d.weekday() < 5:
            days.append(d.isoformat())
        d += timedelta(days=1)
    event_day = days[day_index]
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    init_db(conn)
    def forbidden():
        raise AssertionError('A bar after D was read')
    conn.create_function('forbidden', 0, forbidden)
    conn.executescript('DROP TABLE bhavcopy; CREATE TABLE base (row_id INTEGER PRIMARY KEY, symbol, event_date, '
                       'knowledge_date, open_v, high_v, low_v, close_v, qty_v, series, recorded_at);')
    columns = ', '.join(f"CASE WHEN event_date > '{event_day}' THEN forbidden() ELSE {src} END AS {name}"
                        for src, name in (('open_v', 'open_price'), ('high_v', 'high_price'), ('low_v', 'low_price'),
                                          ('close_v', 'close_price'), ('close_v', 'prev_close'),
                                          ('qty_v', 'traded_qty'), ('qty_v', 'delivery_qty')))
    conn.execute(f"CREATE VIEW bhavcopy AS SELECT row_id, symbol, event_date, knowledge_date, series, recorded_at, "
                 f"NULL AS delivery_pct, 'fixture' AS source_file, {columns} FROM base")
    import random
    rng = random.Random(3)
    for j in range(symbols):
        price = 100.0
        for i, day in enumerate(days):
            price *= 1 + rng.gauss(0, 0.01) + (-0.06 if (j == 0 and i == day_index) else 0)
            conn.execute('INSERT INTO base (symbol,event_date,knowledge_date,open_v,high_v,low_v,close_v,qty_v,series,recorded_at) '
                         "VALUES (?,?,?,?,?,?,?,?,'EQ',?)", (f'S{j}', day, day, price, price * 1.01, price * 0.99, price,
                                                            100000, day))
    material = next(k for k, v in draft_map().items() if v == 'Material news')
    routine = next(k for k, v in draft_map().items() if v == 'Routine')
    for seq, category, stamp in (('old', routine, days[day_index - 20] + ' 11:00:00'), ('new', material, filing_stamp)):
        conn.execute('INSERT INTO corporate_announcements (symbol,event_date,knowledge_date,seq_id,category,description,'
                     'sort_timestamp,source_file,recorded_at) VALUES (?,?,?,?,?,?,?,?,?)',
                     ('S0', stamp[:10], stamp[:10], seq, category, 'fixture', stamp, 'fixture', stamp[:10]))
    conn.commit()
    return conn, days, event_day


class FunnelEndToEndTest(unittest.TestCase):
    """The whole funnel (market, peers, turnover, G3/G5, filings) on a store that raises if any
    bar after D is read; and a filing one second after the cut-off removes nothing."""

    def run_funnel(self, stamp_for):
        from scripts import abc_followup_counts as script
        conn, days, event_day = funnel_store(260, 'placeholder')
        conn.close()
        conn, days, event_day = funnel_store(260, stamp_for(days))
        try:
            with patch.object(script, '_events', return_value={event_day: [{'symbol': 'S0', 'return_1d': -0.05}]}), \
                    patch.object(script, 'load_isin_map', return_value={f'S{j}': f'INE00000000{j}' for j in range(6)}):
                return script.funnel(conn, (2024,)), days, event_day
        finally:
            conn.close()

    def test_no_bar_after_d_is_read_and_a_late_filing_removes_nothing(self):
        late, days, event_day = self.run_funnel(lambda days: days[261] + ' 09:00:01')
        on_time, _, _ = self.run_funnel(lambda days: days[261] + ' 09:00:00')
        self.assertTrue(event_day.startswith('2024'))
        step2 = lambda result: next(r for r in result['steps'] if r[0] == 2024 and r[1] == 2)
        self.assertEqual(step2(late)[6], 0)          # standalone removals at step 2: the late filing counts for nothing
        self.assertEqual(step2(on_time)[6], 1)       # exactly at the cut-off it does
        self.assertEqual(next(r for r in late['steps'] if r[0] == 2024 and r[1] == 0)[3], 1)
        for result in (late, on_time):
            diagnostics = result['diagnostics']['2024']
            self.assertEqual(diagnostics.get('market_unknown', 0), 0)
            self.assertEqual(diagnostics.get('peer_unknown', 0), 0)          # the peer path really ran
            self.assertEqual(diagnostics.get('g3_unknown', 0), 0)            # and the G3 and G5 paths
            self.assertEqual(diagnostics.get('g5_unknown', 0), 0)

    def test_the_fixture_really_raises_on_a_bar_after_d(self):
        conn, days, event_day = funnel_store(260, '2024-01-02 09:00:00')
        try:
            self.assertEqual(len(conn.execute('SELECT close_price FROM bhavcopy WHERE event_date<=?', (event_day,)).fetchall()), 6 * 261)
            with self.assertRaises(sqlite3.OperationalError):
                conn.execute('SELECT close_price FROM bhavcopy WHERE event_date>?', (event_day,)).fetchall()
        finally:
            conn.close()

    def test_a_one_year_run_streams_the_same_sessions_as_a_longer_run_despite_a_late_session(self):
        """P8-093: a session whose bars were known late must not enter item 2's calendar, however the
        run is split (before the 2026-10-19 fix it entered once a request reached its knowledge date).
        A one-year run reads the same sessions, in the same order, and reports the same counts for its
        year as a longer run."""
        from scripts import abc_followup_counts as script
        conn, days, event_day = funnel_store(260, '2024-01-02 09:00:01')
        try:
            late = days[250]                                          # a session in December 2023
            conn.execute('UPDATE base SET knowledge_date=? WHERE event_date=?', (days[258], late))
            events = {d: [{'symbol': 'S0', 'return_1d': -0.05}] for d in days[230:261]}
            original = script._bars_for_day
            results, streamed = {}, {}
            for years in ((2023, 2024), (2024,)):
                seen = []
                with patch.object(script, '_events', return_value=events),                         patch.object(script, 'load_isin_map', return_value={f'S{j}': f'INE00000000{j}' for j in range(6)}),                         patch.object(script, '_bars_for_day', side_effect=lambda c, d: seen.append(d) or original(c, d)):
                    results[years] = script.funnel(conn, years)
                streamed[years] = seen
        finally:
            conn.close()
        self.assertNotIn(late, streamed[(2023, 2024)])
        self.assertEqual(streamed[(2024,)], streamed[(2023, 2024)])
        both, one = results[(2023, 2024)], results[(2024,)]
        self.assertEqual([r for r in both['steps'] if r[0] == 2024], one['steps'])
        self.assertEqual(both['diagnostics']['2024'], one['diagnostics']['2024'])
        self.assertEqual([r for r in both['final'] if r[2] == 2024], one['final'])

    def test_a_sebi_order_known_on_d_cannot_remove_the_event(self):
        sessions = ['2024-01-01', '2024-01-02', '2024-01-03']
        inputs = dict(market=0, peer_status='KNOWN', peer_share=0, previous_close=100)
        gates = dict(g3=False, g5='PASS')
        for known, removed in (('2024-01-02', False), ('2024-01-01', True)):
            flags, *_ = steps_for([], '2024-01-02', datetime(2024, 1, 3, 9, 0), sessions, {}, inputs, gates,
                                  [{'order_id': 'x', 'knowledge_date': known}], [], 5)
            self.assertEqual(flags[3], removed)


if __name__ == '__main__':
    unittest.main()


class CleanPoolTest(unittest.TestCase):
    """Item 4: a filing at or after D's open never adds an event; the market rule is same-direction."""

    def test_bins_run_from_the_previous_close_to_just_before_the_open(self):
        from scripts.abc_followup_counts import overnight
        sessions = ['2024-01-04', '2024-01-05', '2024-01-08']
        def row(stamp):
            return dict(seq_id=stamp, category='x', description='', knowledge_date=stamp[:10], sort_timestamp=stamp)
        rows = [row('2024-01-05 15:29:59'), row('2024-01-05 15:30:00'), row('2024-01-06 10:00:00'),
                row('2024-01-08 09:14:59'), row('2024-01-08 09:15:00'), row('2024-01-08 11:00:00')]
        bins, at_open = overnight(rows, '2024-01-05', '2024-01-08', sessions)
        self.assertEqual({k: [r['seq_id'] for r in v] for k, v in bins.items()},
                         {'previous_evening': ['2024-01-05 15:30:00'], 'closure_bridge': ['2024-01-06 10:00:00'],
                          'before_open': ['2024-01-08 09:14:59']})
        self.assertEqual(at_open, [])
        date_only = dict(seq_id='d', category='x', description='', knowledge_date='2024-01-05', sort_timestamp='2024-01-05')
        bins, at_open = overnight([date_only], '2024-01-05', '2024-01-08', sessions)
        self.assertFalse(any(bins.values()))
        self.assertEqual(len(at_open), 1)                 # known only at the open: reported, never joined

    def test_clean_pool_end_to_end_reads_no_bar_after_d_and_ignores_a_filing_at_the_open(self):
        from scripts import abc_followup_counts as script
        from scripts.abc_followup_counts import draft_map
        material = next(k for k, v in draft_map().items() if v == 'Material news')
        results = {}
        for stamp in ('09:14:59', '09:15:00'):
            conn, days, event_day = funnel_store(260, 'placeholder')
            conn.execute('DELETE FROM corporate_announcements')
            conn.execute('INSERT INTO corporate_announcements (symbol,event_date,knowledge_date,seq_id,category,description,'
                         'sort_timestamp,source_file,recorded_at) VALUES (?,?,?,?,?,?,?,?,?)',
                         ('S0', event_day, event_day, 'n', material, 'fixture', f'{event_day} {stamp}', 'fixture', event_day))
            try:
                with patch.object(script, '_events', return_value={event_day: [{'symbol': 'S0', 'return_1d': -0.05}]}), \
                        patch.object(script, 'load_isin_map', return_value={f'S{j}': f'INE00000000{j}' for j in range(6)}):
                    results[stamp] = script.clean_pool(conn, (2024,))['rows'][0]
            finally:
                conn.close()
        self.assertEqual((results['09:14:59']['pool'], results['09:14:59']['pool_before_open']), (1, 1))
        self.assertEqual(results['09:15:00'].get('pool', 0), 0)
        self.assertEqual(results['09:15:00']['events'], 1)

    def test_only_a_same_direction_market_day_is_left_out(self):
        from scripts import abc_followup_counts as script
        from scripts.abc_followup_counts import draft_map
        material = next(k for k, v in draft_map().items() if v == 'Material news')
        conn, days, event_day = funnel_store(260, 'placeholder')
        conn.execute('DELETE FROM corporate_announcements')
        conn.execute('INSERT INTO corporate_announcements (symbol,event_date,knowledge_date,seq_id,category,description,'
                     'sort_timestamp,source_file,recorded_at) VALUES (?,?,?,?,?,?,?,?,?)',
                     ('S0', event_day, event_day, 'n', material, 'fixture', f'{event_day} 08:00:00', 'fixture', event_day))
        try:
            out = {}
            for market, sign in ((0.03, 1), (0.03, -1), (-0.03, -1)):
                fake = lambda conn, events, **kw: iter([(event_day, {'symbol': 'S0', 'return_1d': sign * 0.05},
                                                        {'market': market, 'peer_status': 'UNKNOWN', 'peer_share': None,
                                                         'previous_close': 100, 'turnover_band': 1})])
                with patch.object(script, 'event_inputs', side_effect=fake), \
                        patch.object(script, '_events', return_value={event_day: [{'symbol': 'S0', 'return_1d': sign * 0.05}]}):
                    out[(market, sign)] = script.clean_pool(conn, (2024,))['rows'][0]
        finally:
            conn.close()
        self.assertEqual(out[(0.03, 1)].get('pool', 0), 0)          # up event on a +3% market day: left out
        self.assertEqual(out[(0.03, -1)]['pool'], 1)                # down event on a +3% day: kept
        self.assertEqual(out[(-0.03, -1)].get('pool', 0), 0)        # down event on a -3% day: left out


class ResultsCoverageTest(unittest.TestCase):
    """Item 5: cumulative steps, exact categories and phrase, the 75-day window, funds excluded; no
    bar after a window's last day is read, and a filing after day 75 adds nothing."""

    def test_steps_window_and_universe(self):
        from scripts import abc_followup_counts as script
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        last_window_day = '2025-12-14'                               # the September 2025 quarter's day 75
        def forbidden():
            raise AssertionError('A bar after the last window was read')
        conn.create_function('forbidden', 0, forbidden)
        conn.executescript(f"""
            CREATE TABLE base(symbol, series, event_date, knowledge_date);
            CREATE VIEW bhavcopy AS SELECT CASE WHEN event_date > '{last_window_day}' THEN forbidden() ELSE symbol END symbol,
                series, event_date, knowledge_date FROM base;
            CREATE TABLE corporate_announcements(symbol, category, description, sort_timestamp, knowledge_date);""")
        bars = [('AAA', 'EQ', '2019-10-05'), ('BBB', 'EQ', '2019-10-05'), ('CCC', 'EQ', '2019-10-05'),
                ('DDD', 'EQ', '2019-10-05'), ('EEE', 'EQ', '2019-10-05'), ('FUND', 'EQ', '2019-10-05'),
                ('LATE', 'EQ', '2026-01-05')]
        conn.executemany('INSERT INTO base VALUES (?,?,?,?)', [(s, se, d, d) for s, se, d in bars])
        filings = [('AAA', 'Financial Result Updates', 'x', '2019-10-20 10:00:00'),
                   ('BBB', 'Outcome of Board Meeting', 'Approved the Financial Results for the quarter', '2019-11-10 18:00:00'),
                   ('CCC', 'Outcome of Board Meeting', 'Approved a dividend', '2019-11-10 18:00:00'),
                   ('CCC', 'Integrated Filing- Financial', 'x', '2019-12-14 12:00:00'),            # day 75: counts
                   ('DDD', 'Copy of Newspaper Publication', 'Extract of unaudited financial results', '2019-11-12 09:00:00'),
                   ('EEE', 'Financial Result Updates', 'x', '2019-12-15 09:00:00'),                # day 76: does not
                   ('EEE', 'Financial Result Updates', 'x', '2019-09-30 20:00:00'),                # quarter end: does not
                   ('FUND', 'Financial Result Updates', 'x', '2019-10-20 10:00:00')]
        conn.executemany('INSERT INTO corporate_announcements VALUES (?,?,?,?,?)',
                         [(s, c, d, t, t[:10]) for s, c, d, t in filings])
        try:
            result = script.results_coverage(conn, isin_map={'FUND': 'INF000000001', 'AAA': 'INE000000001'})
        finally:
            conn.close()
        first = result['quarters'][0]
        self.assertEqual(first['quarter_end'], '2019-09-30')
        self.assertEqual((first['eq_symbols'], first['fund_units_excluded'], first['symbols']), (6, 1, 5))
        self.assertEqual([first[k] for k in result['steps']], [1, 2, 3, 4])   # AAA; +BBB; +CCC; +DDD; never EEE
        self.assertEqual(len(result['quarters']), 25)
        self.assertEqual(result['quarters'][-1]['window_last'], last_window_day)


class ResultsCoverageCovidWindowTest(unittest.TestCase):
    """Item 3 recheck: the March 2020 and March 2021 quarters with a 125-day window beside the 75-day
    one. Day 125 counts and day 126 does not; the denominator uses the same window; no bar after the
    last 125-day window is read; other quarters are not counted."""

    def test_two_quarters_two_windows(self):
        from scripts import abc_followup_counts as script
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        last_window_day = '2021-08-03'                               # 2021-03-31 + 125 days
        def forbidden():
            raise AssertionError('A bar after the last 125-day window was read')
        conn.create_function('forbidden', 0, forbidden)
        conn.executescript(f"""
            CREATE TABLE base(symbol, series, event_date, knowledge_date);
            CREATE VIEW bhavcopy AS SELECT CASE WHEN event_date > '{last_window_day}' THEN forbidden() ELSE symbol END symbol,
                series, event_date, knowledge_date FROM base;
            CREATE TABLE corporate_announcements(symbol, category, description, sort_timestamp, knowledge_date);""")
        bars = [('EARLY', '2020-04-10'), ('LATE', '2020-04-10'), ('EDGE', '2020-04-10'), ('MISS', '2020-04-10'),
                ('NEWCO', '2020-07-20'),                              # trades only after day 75 (2020-06-14)
                ('A21', '2021-04-05'), ('B21', '2021-04-05')]
        conn.executemany('INSERT INTO base VALUES (?,?,?,?)', [(s, 'EQ', d, d) for s, d in bars])
        filings = [('EARLY', '2020-05-20 10:00:00'),                  # day 50
                   ('LATE', '2020-07-15 18:00:00'),                   # day 106
                   ('EDGE', '2020-08-03 23:00:00'),                   # day 125: counts
                   ('MISS', '2020-08-04 09:00:00'),                   # day 126: does not
                   ('NEWCO', '2020-07-25 12:00:00'),
                   ('A21', '2021-06-29 17:00:00'),                    # day 90
                   ('B21', '2021-08-03 12:00:00')]                    # day 125
        conn.executemany('INSERT INTO corporate_announcements VALUES (?,?,?,?,?)',
                         [(s, 'Financial Result Updates', 'x', t, t[:10]) for s, t in filings])
        try:
            result = script.results_coverage_covid(conn, isin_map={})
        finally:
            conn.close()
        self.assertEqual(sorted(result), ['125', '75'])
        for days, expected in (('75', [(4, 1), (2, 0)]), ('125', [(5, 4), (2, 2)])):
            block = result[days]
            self.assertEqual(block['window_days'], int(days))
            self.assertEqual([q['quarter_end'] for q in block['quarters']], ['2020-03-31', '2021-03-31'])
            self.assertEqual([(q['symbols'], q['d_plus_newspaper']) for q in block['quarters']], expected)
        self.assertEqual(result['125']['quarters'][1]['window_last'], last_window_day)
        # LATE, EDGE and NEWCO only after 30 June 2020; B21 only after 30 June 2021 (A21 on 29 June).
        self.assertEqual([q['covered_only_after_next_quarter_end'] for q in result['125']['quarters']], [3, 1])
