"""P8-007 triage (user decision 2026-10-04): verify that the equity-only rule and the split-shape
scan mitigate uncaptured ETF unit splits. Read-only: both stores are opened with mode=ro.

Decision rule, fixed before this script was first run:
  MITIGATED if (a) no catalogue event and no Desk opportunity belongs to a fund-unit (INF ISIN) or
  unresolved symbol, and (b) the pre-specified shape scan finds zero fund-unit hits in the
  population the Desk and research actually use. Then P8-007 closes with a residual-risk note.
  Otherwise it is downgraded with the failing check as the reason.
Equity shape hits that remain unexplained are reported as a separate residual (equity
corporate-action coverage), not as P8-007, whose root cause is ETF unit splits.

The shape tolerance and target ratios are the pre-specified ones from
scripts/phase10_scan_split_bonus_shapes.py (via the P8-007 rerun script). Corporate actions are
read as of today (knowledge_date <= as_of), including same-ISIN sibling symbols (P8-010).
"""
import csv
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desk.lib.connection import DESK_DB_PATH
from desk.lib.store import PRODUCTION_DB_PATH
from scripts.phase10_p8007_shape_scan_rerun import (EXCLUSION_TYPES, RATIO_TYPES, TARGET_SHAPES_PCT,
                                                    TOLERANCE_PP, matches_target_shape)
from shared.market_time import market_today
from shared.sqlite_readonly import open_readonly
from src.ingestion.nse_market_data.isin_mapping import build_symbol_groups, load_isin_map

CATALOGUE = ROOT / 'data/processed/event_catalogue_loose_zscore_only.csv'
ISIN_MAP = ROOT / 'data/raw/nse_symbol_isin_current.json'
WINDOW_DAYS = 10


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify(symbol, isin_map):
    isin = isin_map.get(symbol)
    return 'UNRESOLVED' if isin is None else 'FUND_UNIT' if isin.startswith('INF') else 'EQUITY'


def nearby_action(conn, symbols, event_date, types, as_of):
    ev = date.fromisoformat(event_date)
    lo, hi = (ev - timedelta(days=WINDOW_DAYS)).isoformat(), (ev + timedelta(days=WINDOW_DAYS)).isoformat()
    q = (f"SELECT symbol, event_date, action_type, ratio_numerator, ratio_denominator, knowledge_date "
         f"FROM corporate_actions WHERE symbol IN ({','.join('?' * len(symbols))}) "
         f"AND action_type IN ({','.join('?' * len(types))}) AND event_date BETWEEN ? AND ? "
         f"AND knowledge_date <= ? ORDER BY event_date LIMIT 1")
    row = conn.execute(q, (*symbols, *types, lo, hi, as_of)).fetchone()
    return dict(row) if row else None


def main():
    as_of = market_today().isoformat()
    isin_map = load_isin_map(ISIN_MAP)
    groups = build_symbol_groups(isin_map)
    with CATALOGUE.open(encoding='utf-8') as f:
        catalogue = list(csv.DictReader(f))
    store, desk = open_readonly(PRODUCTION_DB_PATH), open_readonly(DESK_DB_PATH)
    try:
        cat_classes = {}
        for row in catalogue:
            cat_classes.setdefault(classify(row['symbol'], isin_map), set()).add(row['symbol'])
        opp_symbols = {r[0] for r in desk.execute('SELECT DISTINCT symbol FROM opportunity_log')}
        opp_classes = {}
        for s in opp_symbols:
            opp_classes.setdefault(classify(s, isin_map), set()).add(s)
        latest = store.execute('SELECT MAX(event_date) FROM bhavcopy WHERE knowledge_date<=?', (as_of,)).fetchone()[0]
        eq_universe = {r[0] for r in store.execute("SELECT DISTINCT symbol FROM bhavcopy WHERE event_date=? AND series='EQ' "
                                                    'AND knowledge_date<=?', (latest, as_of))}
        universe_classes = {}
        for s in eq_universe:
            universe_classes.setdefault(classify(s, isin_map), set()).add(s)

        hits = dict(explained_by_ratio=[], explained_by_exclusion_marker=[], explained_by_sibling=[], unexplained=[])
        fund_unit_hits = 0
        for row in catalogue:
            if row['return_1d'] in ('', 'None'):
                continue
            pct = float(row['return_1d']) * 100
            shape = matches_target_shape(pct)
            if shape is None:
                continue
            if classify(row['symbol'], isin_map) != 'EQUITY':
                fund_unit_hits += 1
                continue
            hit = dict(symbol=row['symbol'], event_date=row['event_date'], return_1d_pct=round(pct, 3), shape_pct=shape)
            own = [row['symbol']]
            siblings = sorted(set(groups.get(row['symbol'], [row['symbol']])) - set(own))
            for bucket, symbols, types in (('explained_by_ratio', own, RATIO_TYPES),
                                           ('explained_by_exclusion_marker', own, EXCLUSION_TYPES),
                                           ('explained_by_sibling', siblings, RATIO_TYPES + EXCLUSION_TYPES)):
                action = nearby_action(store, symbols, row['event_date'], types, as_of) if symbols else None
                if action:
                    hits[bucket].append(hit | dict(action=action))
                    break
            else:
                hits['unexplained'].append(hit)
    finally:
        store.close()
        desk.close()

    counts = lambda d: {k: len(v) for k, v in sorted(d.items())}
    checks = dict(catalogue_has_no_fund_unit_or_unresolved=not cat_classes.get('FUND_UNIT') and not cat_classes.get('UNRESOLVED'),
                  desk_opportunities_have_no_fund_unit_or_unresolved=not opp_classes.get('FUND_UNIT') and not opp_classes.get('UNRESOLVED'),
                  shape_scan_has_no_fund_unit_hits=fund_unit_hits == 0)
    result = dict(
        as_of=as_of, decision='MITIGATED' if all(checks.values()) else 'NOT_MITIGATED', checks=checks,
        catalogue=dict(events=len(catalogue), symbols_by_class=counts(cat_classes)),
        desk_opportunity_log=dict(symbols_by_class=counts(opp_classes)),
        latest_session=latest, eq_universe_on_latest_session=dict(symbols_by_class=counts(universe_classes)),
        shape_scan=dict(target_shapes_pct=TARGET_SHAPES_PCT, tolerance_pp=TOLERANCE_PP, window_days=WINDOW_DAYS,
                        fund_unit_hits=fund_unit_hits, equity_hits=counts(hits),
                        unexplained_by_year=dict(sorted({y: sum(h['event_date'][:4] == y for h in hits['unexplained'])
                                                         for y in {h['event_date'][:4] for h in hits['unexplained']}}.items())),
                        unexplained=hits['unexplained']),
        provenance=dict(catalogue_sha256=sha256(CATALOGUE), isin_map_sha256=sha256(ISIN_MAP),
                        script='scripts/desk_p8007_verification.py', stores='opened read-only (mode=ro)'))
    out = ROOT / 'docs/desk/p8007_verification.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'shape_scan'} |
                     dict(shape_scan={k: v for k, v in result['shape_scan'].items() if k != 'unexplained'}), indent=2))


if __name__ == '__main__':
    main()
