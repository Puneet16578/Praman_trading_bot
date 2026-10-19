"""Read-only A/B/C input counts. No outcomes, network, store writes, or later bars.

Report conventions only; existing screening/configuration code is imported unchanged.
Run from the repository root. JSON goes to stdout, progress to stderr.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict, deque
from datetime import date, datetime, timedelta
import json
from pathlib import Path
import re
import statistics
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.abc_event_day_context import (
    _events, _calendar, _bars_for_day, _actions_asof, _return,
    _repaired_correlations, CATALOGUE,
)
from shared.sqlite_readonly import open_readonly
from src.ingestion.nse_market_data.isin_mapping import load_isin_map
from src.ingestion.nse_market_data.corporate_actions import STRUCTURAL_BREAK_ACTION_TYPES
from src.bitemporal.guard import latest_as_of
from desk.screening_plan import decision_plan
from desk.gates.engine import _average_daily_volume_and_turnover, ADV_LOOKBACK_SESSIONS
from desk.gates.checks import g5_liquidity
from desk.risk.officer import compute_position_size
from desk.lib.rulebook import load_active_rulebook
from desk.lib.costs import load_active_cost_config

START, END = '2019-10-01', '2025-12-31'
DB = ROOT / 'data/processed/praman.db'
DIV_CATEGORIES = {'Dividend', 'Record Date', 'Book Closure'}
UNCLEAR_GROUPS = {
    'news_queries': {'News Verification', 'News verification', 'News Clarification',
                     'Rumour Verification', 'Rumour Verification - Regulation 30(11)'},
    # Diagnostic only (Claude, 2026-10-19): the store's generic clarification categories, shown
    # separately so either reading of "news and rumour verification and clarification" is visible.
    'clarification_general': {'Clarification', 'Reply to Clarification Sought'},
    'clarification_financial_results': {'Clarification - Financial Results', 'Clarification- Financial Results',
                                        'Reply to Clarification Sought- Financial Results',
                                        'Reply to Clarification- Financial results'},
    'move_queries': {'Price movement', 'Spurt in Volume'},
    'board_outcome': {'Outcome of Board Meeting', 'Outcome of Board Meeting-XBRL'},
    'takeover': {'Disclosure under SEBI Takeover Regulations'},
}
YEARS = tuple(range(2020, 2026))


def draft_map():
    result = {}
    for line in (ROOT / 'docs/desk/abc_sourcing_check.md').read_text(encoding='utf-8').splitlines():
        cells = [c.strip() for c in line.split('|')]
        if len(cells) == 6 and cells[3] in {'Material news', 'Routine', 'Unclear'}:
            result[cells[1]] = cells[3]
    if len(result) != 279:
        raise ValueError('The approved draft inventory must contain 279 categories.')
    return result


def available_at(row, sessions):
    """IST-naive exact timestamps; date-only evidence waits for next EQ open."""
    stamp = row.get('sort_timestamp', '') or ''
    try:
        public = datetime.strptime(stamp, '%Y-%m-%d %H:%M:%S')
        if public.date().isoformat() == row['knowledge_date']:
            return public
    except ValueError:
        pass
    i = bisect_right(sessions, row['knowledge_date'])
    return datetime.fromisoformat(sessions[i] + 'T09:15:00') if i < len(sessions) else datetime.max


def visible_filings(rows, start, cutoff, sessions):
    return [r for r in rows if start <= available_at(r, sessions) <= cutoff]


class BoundedInputs:
    """Apply source-query ceilings before existing screening helpers read rows."""
    def __init__(self, conn, day, date_only_through):
        date.fromisoformat(day)
        date.fromisoformat(date_only_through)
        self.conn, self.day, self.date_only_through = conn, day, date_only_through

    def execute(self, sql, parameters=()):
        if not sql.lstrip().upper().startswith('SELECT'):
            raise ValueError('Input analysis accepts SELECT only.')
        for table in ('bhavcopy', 'corporate_actions', 'surveillance_flags'):
            known = self.day if table == 'bhavcopy' else self.date_only_through
            source = (f"(SELECT * FROM main.{table} WHERE event_date<='{self.day}' "
                      f"AND knowledge_date<='{known}')")
            sql = re.sub(r'\bFROM\s+' + table + r'\b', lambda _: 'FROM ' + source, sql, flags=re.I)
        return self.conn.execute(sql, parameters)


def gate_inputs(conn, symbol, day, previous_session, rulebook, costs):
    bounded = BoundedInputs(conn, day, previous_session)
    rows = sorted(latest_as_of(bounded, 'bhavcopy', day, symbol=symbol, series='EQ'),
                  key=lambda r: r['event_date'])
    g3 = None
    if rows and rows[-1]['event_date'] == day:
        start = rows[max(0, len(rows) - 61)]['event_date']
        actions = latest_as_of(bounded, 'corporate_actions', day, symbol=symbol)
        g3 = any(start < r['event_date'] <= day and r['action_type'] in STRUCTURAL_BREAK_ACTION_TYPES
                 for r in actions)
    _, turnover = _average_daily_volume_and_turnover(bounded, symbol, day, ADV_LOOKBACK_SESSIONS)
    try:
        plan = decision_plan(bounded, symbol, day, stop_multiple=rulebook.screening.stop_multiple)
        quantity = compute_position_size(plan['decision_price'], plan['stop_level'], rulebook, 0, 0, 0, costs=costs)
        g5 = (g5_liquidity(quantity * plan['decision_price'], turnover, rulebook).result
              if quantity > 0 else 'UNKNOWN')
    except ValueError:
        g5 = 'UNKNOWN'
    flags = list(bounded.execute('SELECT * FROM surveillance_flags WHERE symbol=? ORDER BY event_date,knowledge_date,row_id', (symbol,)))
    state = {}
    for flag in flags:
        if flag['action_type'] in ('ENTRY', 'STAGE_CHANGE'):
            state[flag['mechanism']] = flag['to_stage']
        elif flag['action_type'] == 'EXIT':
            state[flag['mechanism']] = None
    return {'g3': g3, 'g5': g5, 'asm': asm_active(state),
            'gsm_unknown': 'GSM' not in state}


def asm_active(state):
    return any(state.get(mechanism) is not None for mechanism in ('ASM_LT', 'ASM_ST'))


def event_inputs(conn, events, *, peers=True, report_years=None):
    """Stream D-bounded inputs, reusing item 2's return/correlation functions.

    `events` drives the calendar requests (item 2's `_calendar`, whose session list depends on the
    requested dates: P8-093), so a per-year run passes every down-event date and reports only
    `report_years`; it then streams exactly as the all-years run does."""
    identities = load_isin_map(ROOT / 'data/raw/nse_symbol_isin_current.json')
    eligible = {s for s, isin in identities.items() if isin and not isin.startswith('INF')}
    previous = {}
    names, columns = [], {}
    rolling = np.empty((0, 0))
    turnovers = defaultdict(lambda: deque(maxlen=60))
    last = ''
    for requested in sorted(events):
        found = False
        for day in _calendar(conn, last, requested):
            bars = _bars_for_day(conn, day)
            actions = _actions_asof(conn, day)
            returns = {}
            prior_closes = {s: p[1] for s, p in previous.items()}
            for symbol, close in bars.items():
                prior = previous.get(symbol)
                ret = _return(prior, day, close, actions.get(symbol, ()))
                if symbol in eligible and prior and prior[0] == last and ret is not None:
                    returns[symbol] = ret
                previous[symbol] = (day, close)
            mean = statistics.fmean(returns.values()) if returns else None
            for symbol in returns:
                if symbol not in columns:
                    columns[symbol] = len(names)
                    names.append(symbol)
            if rolling.shape[1] < len(names):
                rolling = np.pad(rolling, ((0, 0), (0, len(names)-rolling.shape[1])), constant_values=np.nan)
            row = np.full(len(names), np.nan)
            for symbol, ret in returns.items():
                row[columns[symbol]] = ret - mean
            # Turnover bands use all EQ stocks, including funds, as requested.
            seen = set()
            for r in conn.execute("SELECT symbol,close_price,traded_qty FROM bhavcopy WHERE event_date=? "
                                  "AND knowledge_date<=? AND series='EQ' ORDER BY knowledge_date DESC,row_id DESC", (day, day)):
                if r['symbol'] not in seen:
                    turnovers[r['symbol']].append(r['close_price'] * r['traded_qty'])
                    seen.add(r['symbol'])
            if day == requested and report_years is not None and int(day[:4]) not in report_years:
                found = True
            elif day == requested:
                found = True
                averages = {s: statistics.fmean(turnovers[s]) for s in bars if len(turnovers[s]) == 60}
                boundaries = np.quantile(list(averages.values()), [.2, .4, .6, .8]) if averages else []
                for event in events[day]:
                    symbol = event['symbol']
                    share, status = None, 'UNKNOWN'
                    if peers and symbol in returns and mean is not None:
                        selected = _repaired_correlations(rolling[-250:], names, symbol, set(returns), 200)
                        if selected:
                            status = 'KNOWN'
                            residual = returns[symbol] - mean
                            if abs(residual) >= .01:
                                share = (statistics.fmean(returns[p] for _, _, p in selected) - mean) / residual
                            else:
                                status = 'UNSTABLE'
                    yield day, event, {'market': mean, 'peer_status': status, 'peer_share': share,
                                      'previous_close': prior_closes.get(symbol),
                                      'turnover_band': (int(np.searchsorted(boundaries, averages[symbol], side='right')) + 1
                                                        if symbol in averages else 'UNKNOWN')}
            rolling = np.vstack((rolling, row))[-250:]
            last = day
        if not found and (report_years is None or int(requested[:4]) in report_years):
            for event in events[requested]:
                yield requested, event, {'market': None, 'peer_status': 'UNKNOWN', 'peer_share': None,
                                        'previous_close': None, 'turnover_band': 'UNKNOWN'}


DATE_TOKEN = r'(?:\d{4}-\d{2}-\d{2}|\d{1,2}[ /.-](?:\d{1,2}|[A-Za-z]{3,9})[ ,/.-]+\d{4})'


def parse_dividend(row):
    text = row.get('description') or ''
    if 'dividend' not in text.lower() and row['category'] != 'Dividend':
        return None, None, 'not_dividend'
    match = re.search(r'(?:record date|book closure(?: period)?(?: from)?)[^.;\n]{0,90}?(' + DATE_TOKEN + ')', text, re.I)
    record = None
    if match:
        token = re.sub(r'[,/.-]', ' ', match[1])
        token = ' '.join(token.split())
        for fmt in ('%Y %m %d', '%d %m %Y', '%d %b %Y', '%d %B %Y'):
            try:
                record = datetime.strptime(token, fmt).date().isoformat()
                break
            except ValueError:
                pass
    amount = None
    match = re.search(r'(?:dividend\s+(?:of\s+)?(?:Rs\.?|INR)|(?:Rs\.?|INR))\s*([\d,]+(?:\.\d+)?)\s*(?:/-)?\s*(?:per|on each)', text, re.I)
    if match:
        amount = float(match[1].replace(',', ''))
    return record, amount, 'parsed' if record else 'unparsed'


def steps_for(rows, day, cutoff, sessions, mapping, inputs, gates, orders, dividend_rows, lookback):
    index = bisect_left(sessions, day)
    start = datetime.fromisoformat(sessions[max(0, index-lookback)] + 'T00:00:00')
    window = visible_filings(rows, start, cutoff, sessions)
    material = [r for r in window if mapping.get(r['category'], 'Unclear') == 'Material news']
    unclear = [r for r in window if mapping.get(r['category'], 'Unclear') == 'Unclear']
    coverage_start = datetime.fromisoformat(day) - timedelta(days=90)
    covered = visible_filings(rows, coverage_start, min(cutoff, datetime.fromisoformat(day)-timedelta(microseconds=1)), sessions)
    order_start = datetime.fromisoformat(sessions[max(0, index-5)] + 'T00:00:00')
    sebi = any(order_start <= available_at(r, sessions) <= cutoff for r in orders)
    dividend = False
    div_meta = []
    for r in dividend_rows:
        if available_at(r, sessions) > cutoff:
            continue
        record, amount, status = parse_dividend(r)
        match = False
        if record:
            j = bisect_left(sessions, record)
            before = sessions[j-1] if j else None
            match = day in (record, before)
            dividend |= match
        computable = match and amount is not None and inputs['previous_close'] is not None
        div_meta.append((r['seq_id'], status, match, bool(computable and amount >= .02 * inputs['previous_close']),
                         amount is not None, computable))
    flags = [inputs['market'] is not None and inputs['market'] < -.02, bool(material), bool(unclear),
             sebi, not bool(covered), '2022-07-13' <= day <= '2022-12-16', dividend,
             inputs['peer_status'] == 'UNKNOWN' or (inputs['peer_share'] is not None and inputs['peer_share'] >= .5),
             gates['g3'] is True or gates['g5'] == 'FAIL']
    close = datetime.fromisoformat(day + 'T15:30:00')
    evening = datetime.fromisoformat(day + 'T18:00:00')
    midnight = datetime.fromisoformat(day) + timedelta(days=1)
    next_morning = datetime.combine(cutoff.date(), datetime.min.time())
    timing = [sum(close <= available_at(r, sessions) <= evening for r in material),
              sum(evening < available_at(r, sessions) < midnight for r in material),
              sum(next_morning <= available_at(r, sessions) <= cutoff for r in material)
              if cutoff.date() > date.fromisoformat(day) else 0,
              sum(midnight <= available_at(r, sessions) < next_morning for r in material)]
    groups = {name: sum(r['category'] in categories for r in unclear) for name, categories in UNCLEAR_GROUPS.items()}
    return flags, timing, groups, div_meta


def summarize(records, years=YEARS):
    result = []
    for year in years:
        population = [r for r in records if r['day'].startswith(str(year))]
        left = list(population)
        for step in range(10):
            removed = 0
            if step:
                retained = [r for r in left if not r['flags'][step-1]]
                removed, left = len(left)-len(retained), retained
            result.append([year, step, removed, len(left), len({r['day'] for r in left}),
                           len({r['symbol'] for r in left}), sum(r['flags'][step-1] for r in population) if step else 0])
    return result


def funnel(conn, years=YEARS):
    """The B funnel for the given event years. History (returns, peers, turnover) still streams from
    START, so a single-year run gives the same rows as the all-years run (Claude, 2026-10-19: lets a
    run be split into foreground pieces)."""
    years = tuple(sorted(years))
    mapping = draft_map()
    # Every down-event date up to the last requested year drives the stream (P8-093); only the
    # requested years are evaluated and reported.
    stream = {d: [r for r in rows if r['return_1d'] < 0] for d, rows in _events(CATALOGUE).items()
              if int(d[:4]) <= max(years)}
    stream = {d: rows for d, rows in stream.items() if rows}
    events = {d: rows for d, rows in stream.items() if int(d[:4]) in years}
    # Calendar metadata only: no OHLC or volume after D is selected here.
    sessions = [r[0] for r in conn.execute("SELECT DISTINCT event_date FROM bhavcopy WHERE series='EQ' "
                "AND event_date>=? AND event_date<=? AND knowledge_date<=? ORDER BY event_date", (START, '2026-01-10', '2026-01-10'))]
    rb, costs = load_active_rulebook(), load_active_cost_config()
    variants = {(cut, lb): [] for cut, lb in [('09:00', 5), ('18:00', 5), ('23:59', 5), ('09:00', 1), ('09:00', 10)]}
    diagnostics = defaultdict(Counter)
    div_seen = defaultdict(dict)
    last_day = ''
    for day, event, inputs in event_inputs(conn, stream, report_years=set(years)):
        symbol = event['symbol']
        i = bisect_left(sessions, day)
        previous_session = sessions[i-1] if i else START
        nxt = sessions[bisect_right(sessions, day)]
        upper = nxt + ' 09:00:00'
        rows = [dict(r) for r in conn.execute("SELECT seq_id,category,description,sort_timestamp,knowledge_date FROM corporate_announcements "
                    "WHERE symbol=? AND event_date>=? AND event_date<=? AND knowledge_date<=?", (symbol, (date.fromisoformat(day)-timedelta(days=90)).isoformat(), nxt, nxt))]
        dividends = [dict(r) for r in conn.execute("SELECT seq_id,category,description,sort_timestamp,knowledge_date FROM corporate_announcements "
                    "WHERE symbol=? AND category IN ('Dividend','Record Date','Book Closure') AND knowledge_date<=?", (symbol, nxt))]
        orders = [dict(r) for r in conn.execute("SELECT order_id,knowledge_date FROM sebi_orders WHERE symbol=? AND knowledge_date<=?", (symbol, nxt))]
        gates = gate_inputs(conn, symbol, day, previous_session, rb.rulebook, costs.costs)
        year = int(day[:4])
        diagnostics[year].update({'asm_active': int(gates['asm']), 'gsm_unknown': int(gates['gsm_unknown']),
                                  'g3_fail': int(gates['g3'] is True), 'g5_fail': int(gates['g5'] == 'FAIL'),
                                  'g3_unknown': int(gates['g3'] is None), 'g5_unknown': int(gates['g5'] == 'UNKNOWN'),
                                  'peer_unknown': int(inputs['peer_status'] == 'UNKNOWN'),
                                  'peer_share_at_least_half': int(inputs['peer_share'] is not None and inputs['peer_share'] >= .5),
                                  'market_unknown': int(inputs['market'] is None),
                                  'unstable_peer_ratio': int(inputs['peer_status'] == 'UNSTABLE')})
        for (clock, lookback), output in variants.items():
            cutoff = datetime.fromisoformat(upper if clock == '09:00' else day + ' ' + clock + ':00')
            flags, timing, groups, div_meta = steps_for(rows, day, cutoff, sessions, mapping, inputs, gates, orders, dividends, lookback)
            record = {'day': day, 'symbol': symbol, 'flags': flags, 'band': inputs['turnover_band']}
            output.append(record)
            if clock == '09:00' and lookback == 5:
                diagnostics[year].update({f'material_rows_bin_{j}': n for j, n in enumerate(timing)})
                diagnostics[year].update({f'material_events_bin_{j}': int(n > 0) for j, n in enumerate(timing)})
                diagnostics[year].update({f'unclear_rows_{k}': n for k, n in groups.items()})
                diagnostics[year].update({f'unclear_events_{k}': int(n > 0) for k, n in groups.items()})
                for seq, status, match, high, amount_known, computable in div_meta:
                    prior = div_seen[year].get(seq, [status, False, False, False, False])
                    div_seen[year][seq] = [status, prior[1] or match, prior[2] or high,
                                          prior[3] or amount_known, prior[4] or computable]
                if not any(flags):
                    diagnostics[year].update({'final_g3_unknown': int(gates['g3'] is None), 'final_g5_unknown': int(gates['g5'] == 'UNKNOWN'), 'final_unstable_peer_ratio': int(inputs['peer_status'] == 'UNSTABLE')})
        if day != last_day and day.endswith(('-01', '-02', '-03')):
            print('Funnel inputs through ' + day, file=sys.stderr, flush=True)
        last_day = day
    totals = []
    for (clock, lb), records in variants.items():
        for year in years:
            left = [r for r in records if r['day'].startswith(str(year)) and not any(r['flags'])]
            totals.append([clock, lb, year, len(left), len({r['day'] for r in left}), len({r['symbol'] for r in left}),
                           [sum(r['band'] == q for r in left) for q in (1, 2, 3, 4, 5, 'UNKNOWN')]])
    return {'years': list(years),
            'step_columns': ['year', 'step', 'removed', 'left', 'dates_left', 'symbols_left', 'standalone_removed'],
            'steps': summarize(variants[('09:00', 5)], years),
            'steps_lookback_1': summarize(variants[('09:00', 1)], years),
            'steps_lookback_10': summarize(variants[('09:00', 10)], years),
            'final_columns': ['cutoff', 'lookback', 'year', 'events', 'dates', 'symbols', 'turnover_Q1_Q5_unknown'],
            'final': totals, 'diagnostics': {str(k): dict(v) for k, v in diagnostics.items()},
            'dividends': {str(year): dict(Counter(v[0] for v in rows.values())) | {'matched_filings': sum(v[1] for v in rows.values()), 'amount_at_least_2pct': sum(v[2] for v in rows.values()), 'amount_parsed': sum(v[3] for v in rows.values()), 'matched_yield_computable': sum(v[4] for v in rows.values())} for year, rows in div_seen.items()},
            'rulebook_sha256': rb.sha256, 'cost_sha256': costs.sha256}


def notes(conn):
    """Counts outside the per-year funnel: SEBI orders in scope and the 2025 GSM entry-day G5 check."""
    sessions = [r[0] for r in conn.execute("SELECT DISTINCT event_date FROM bhavcopy WHERE series='EQ' "
                "AND event_date>=? AND event_date<=? AND knowledge_date<=? ORDER BY event_date", (START, END, END))]
    rb, costs = load_active_rulebook(), load_active_cost_config()
    order_counts = [dict(r) for r in conn.execute("SELECT substr(knowledge_date,1,4) year,COUNT(*) rows,COUNT(DISTINCT order_id) orders, "
                   "SUM(symbol IS NULL OR symbol='') unlinked FROM sebi_orders WHERE knowledge_date>=? AND knowledge_date<=? GROUP BY 1", (START, END))]
    gsm = []
    for r in conn.execute("SELECT DISTINCT symbol,event_date FROM surveillance_flags WHERE mechanism='GSM' AND action_type='ENTRY' "
                          "AND event_date BETWEEN '2025-01-01' AND '2025-12-31' AND knowledge_date<='2025-12-31' ORDER BY event_date,symbol"):
        day = r['event_date']
        i = bisect_left(sessions, day)
        gates = gate_inputs(conn, r['symbol'], day, sessions[i-1], rb.rulebook, costs.costs)
        gsm.append((r['symbol'], gates['g5']))
    return {'orders': order_counts,
            'gsm_2025': {'entries': len(gsm), 'distinct_stocks': len({s for s, _ in gsm}), 'G5': dict(Counter(g for _, g in gsm)), 'distinct_stocks_by_G5': {g: len({s for s, result in gsm if result == g}) for g in ('PASS', 'FAIL', 'UNKNOWN')}, 'stocks_with_any_G5_pass': len({s for s, g in gsm if g == 'PASS'})},
            'rulebook_sha256': rb.sha256, 'cost_sha256': costs.sha256}


# Item 4 (Claude, 2026-10-19): A's clean pool. Both stored spellings of each extra category count.
EXTRA_A = {'Outcome of Board Meeting', 'Outcome of Board Meeting-XBRL', 'Press Release', 'Press Release (Revised)'}
OVERNIGHT_BINS = ('previous_evening', 'closure_bridge', 'before_open')


def overnight(rows, previous_session, day, sessions):
    """Filings between the previous EQ session's close (15:30, inclusive) and D's open (09:15,
    exclusive), by bin; date-only evidence (known only from the next open) is never placed in a bin
    and is counted separately when it becomes known exactly at D's open."""
    close = datetime.fromisoformat(previous_session + 'T15:30:00')
    after_close_day = datetime.fromisoformat(previous_session) + timedelta(days=1)
    start_of_day = datetime.fromisoformat(day)
    opening = datetime.fromisoformat(day + 'T09:15:00')
    bins = {name: [] for name in OVERNIGHT_BINS}
    date_only_at_open = []
    for r in rows:
        moment = available_at(r, sessions)
        stamp = (r.get('sort_timestamp') or '')
        timestamped = len(stamp) == 19 and stamp[:10] == r['knowledge_date']
        if not timestamped:
            if moment == opening:
                date_only_at_open.append(r)
            continue
        if close <= moment < after_close_day:
            bins['previous_evening'].append(r)
        elif after_close_day <= moment < start_of_day:
            bins['closure_bridge'].append(r)
        elif start_of_day <= moment < opening:
            bins['before_open'].append(r)
    return bins, date_only_at_open


def clean_pool(conn, years=YEARS):
    """Item 4: up and down catalogue events with a same-symbol filing between the previous EQ close
    and D's open, leaving out days whose equal-weight market moved more than 2% the same way.
    Prices through D's close only (the market move on D); filings after D's open never count."""
    years = tuple(sorted(years))
    mapping = draft_map()
    stream = {d: rows for d, rows in _events(CATALOGUE).items() if int(d[:4]) <= max(years) and rows}
    sessions = [r[0] for r in conn.execute("SELECT DISTINCT event_date FROM bhavcopy WHERE series='EQ' "
                "AND event_date>=? AND event_date<=? AND knowledge_date<=? ORDER BY event_date", (START, END, END))]
    table = defaultdict(Counter)
    left = defaultdict(lambda: defaultdict(set))
    for day, event, inputs in event_inputs(conn, stream, peers=False, report_years=set(years)):
        if event['return_1d'] == 0:
            continue
        direction = 'up' if event['return_1d'] > 0 else 'down'
        key = (int(day[:4]), direction)
        counts = table[key]
        counts['events'] += 1
        i = bisect_left(sessions, day)
        if i == 0:
            counts['no_previous_session'] += 1
            continue
        previous_session = sessions[i - 1]
        rows = [dict(r) for r in conn.execute(
            "SELECT seq_id,category,description,sort_timestamp,knowledge_date FROM corporate_announcements "
            "WHERE symbol=? AND event_date>=? AND event_date<=? AND knowledge_date<=?",
            (event['symbol'], previous_session, day, day))]
        material = [r for r in rows if mapping.get(r['category'], 'Unclear') == 'Material news']
        extra = [r for r in rows if r['category'] in EXTRA_A]
        bins, at_open = overnight(material, previous_session, day, sessions)
        extra_bins, _ = overnight(extra, previous_session, day, sessions)
        has_material = any(bins.values())
        has_extra = any(extra_bins.values())
        market = inputs['market']
        same_way = market is not None and ((direction == 'up' and market > .02) or (direction == 'down' and market < -.02))
        counts['market_unknown'] += market is None
        counts['same_direction_market_day'] += same_way
        counts['material_overnight'] += has_material
        counts['date_only_known_at_open'] += bool(at_open)
        if same_way:
            counts['material_overnight_left_out_by_market'] += has_material
            continue
        if has_material:
            counts['pool'] += 1
            counts['pool_market_unknown'] += market is None
            for name in OVERNIGHT_BINS:
                counts[f'pool_{name}'] += bool(bins[name])
            left[key]['dates'].add(day)
            left[key]['symbols'].add(event['symbol'])
        elif has_extra:
            counts['would_join_with_board_outcome_or_press_release'] += 1
            for name in OVERNIGHT_BINS:
                counts[f'join_{name}'] += bool(extra_bins[name])
    result = []
    for (year, direction), counts in sorted(table.items()):
        result.append(dict(year=year, direction=direction, **counts,
                           pool_dates=len(left[(year, direction)]['dates']),
                           pool_symbols=len(left[(year, direction)]['symbols'])))
    return {'years': list(years), 'rows': result}


# Item 5 (Claude, 2026-10-19): results coverage from stored announcements only. The legacy tags and
# the case-insensitive literal "financial result" follow docs/desk/abc_sourcing_check.md (line 470)
# and docs/desk/r2_sourcing_check.md.
RESULT_STEPS = (
    ('a_legacy_tags', "category IN ('Financial Result Updates','Financial Results Updates')"),
    ('b_plus_board_outcome', "category='Outcome of Board Meeting' AND lower(description) LIKE '%financial result%'"),
    ('c_plus_integrated_financial', "category='Integrated Filing- Financial'"),
    ('d_plus_newspaper', "category IN ('Copy of Newspaper Publication','Newspaper Advertisements') "
                         "AND lower(description) LIKE '%financial result%'"),
)
RESULT_WINDOW_DAYS = 75


def quarter_ends(first='2019-09-30', last='2025-09-30'):
    ends, year, month = [], int(first[:4]), int(first[5:7])
    while f'{year}-{month:02d}' <= last[:7]:
        day = {3: 31, 6: 30, 9: 30, 12: 31}[month]
        ends.append(f'{year}-{month:02d}-{day:02d}')
        month += 3
        if month > 12:
            month, year = 3, year + 1
    return ends


def results_coverage(conn, isin_map=None):
    """Per quarter: of the EQ symbols with an EQ bar in the 75 days after quarter end (fund units
    excluded by the current ISIN map, as in item 2), how many have a results-bearing filing published
    in that window, adding sources step by step. Bars are read only for symbol presence inside each
    window; nothing after a window's last day is read for that quarter."""
    identities = isin_map if isin_map is not None else load_isin_map(ROOT / 'data/raw/nse_symbol_isin_current.json')
    funds = {s for s, isin in identities.items() if isin and isin.startswith('INF')}
    rows = []
    for end in quarter_ends():
        first = (date.fromisoformat(end) + timedelta(days=1)).isoformat()
        last = (date.fromisoformat(end) + timedelta(days=RESULT_WINDOW_DAYS)).isoformat()
        trading = {r[0] for r in conn.execute("SELECT DISTINCT symbol FROM bhavcopy WHERE series='EQ' AND event_date>=? "
                                             "AND event_date<=? AND knowledge_date<=?", (first, last, last))}
        universe = trading - funds
        covered, row = set(), dict(quarter_end=end, window_last=last, eq_symbols=len(trading),
                                  fund_units_excluded=len(trading & funds), symbols=len(universe))
        for name, condition in RESULT_STEPS:
            covered |= {r[0] for r in conn.execute(
                f"SELECT DISTINCT symbol FROM corporate_announcements WHERE {condition} AND substr(sort_timestamp,1,10)>=? "
                f"AND substr(sort_timestamp,1,10)<=? AND knowledge_date<=?", (first, last, last))} & universe
            row[name] = len(covered)
        rows.append(row)
    return {'window_days': RESULT_WINDOW_DAYS, 'steps': [n for n, _ in RESULT_STEPS], 'quarters': rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('section', choices=['funnel', 'notes', 'clean_pool', 'results_coverage'])
    parser.add_argument('--years', help='Comma-separated event years for funnel (default 2020-2025).')
    args = parser.parse_args()
    years = tuple(int(y) for y in args.years.split(',')) if args.years else YEARS
    if not set(years) <= set(YEARS):
        parser.error('years must be within 2020-2025')
    conn = open_readonly(DB)
    try:
        result = (funnel(conn, years) if args.section == 'funnel' else notes(conn) if args.section == 'notes'
                  else clean_pool(conn, years) if args.section == 'clean_pool' else results_coverage(conn))
        print(json.dumps(result, sort_keys=True, indent=2))
    finally:
        conn.close()


if __name__ == '__main__':
    main()
