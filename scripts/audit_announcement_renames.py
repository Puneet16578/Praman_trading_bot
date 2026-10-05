"""Read-only P8-046 audit. Inputs/tiers only; never rebuilds frozen artifacts."""
import bisect
from collections import defaultdict
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import random
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shared.sqlite_readonly import open_readonly
from src.config.settings import get_settings
from src.ingestion.nse_market_data.announcements_bulk import fetch_window, stable_id
from src.signals.disclosure_classification import classify_disclosure_window

PLAN = ROOT/'docs/desk/announcement_rename_audit_plan.json'
INPUT = ROOT/'data/processed/announcement_rename_audit_input_20261005.json'
RESULT = ROOT/'docs/desk/announcement_rename_audit_results.json'
SEED = 20261005
CUTOFF = '2026-09-15'


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare():
    import pandas as pd
    log = ROOT/'logs/amendment4_renames_output.log'
    text = log.read_text(encoding='utf-8').split('=== Orphaned actions')[0]
    groups = {}
    for line in text.splitlines():
        match = re.match(r'^  (IN[A-Z0-9]{10}): (.*)$', line)
        if match:
            groups[match[1]] = re.findall(r'(\S+) \[', match[2])
    if len(groups) != 195:
        raise ValueError('Historical 195-security frame could not be reconstructed')
    by_symbol = {s: i for i, symbols in groups.items() for s in symbols}
    catalogue = ROOT/'data/processed/event_catalogue_loose_zscore_only.csv'
    classifications = ROOT/'data/processed/event_classifications.csv'
    # Load no forward-outcome columns from the classification artifact.
    events = pd.read_csv(catalogue, usecols=['symbol','event_date'], dtype=str).to_dict('records')
    frozen = pd.read_csv(classifications, usecols=['symbol','event_date','disclosure_tier'], dtype=str)
    tiers = {(r.symbol,r.event_date):r.disclosure_tier for r in frozen.itertuples() if r.event_date<=CUTOFF}
    events = [r for r in events if r['symbol'] in by_symbol and r['event_date']<=CUTOFF]
    conn = open_readonly(get_settings().database_path)
    try:
        days, stored = {}, {}
        for isin, symbols in groups.items():
            placeholders = ','.join('?' for _ in symbols)
            days[isin] = [r[0] for r in conn.execute('SELECT DISTINCT event_date FROM bhavcopy WHERE symbol IN ('+
                placeholders+") AND series='EQ' AND knowledge_date<=? ORDER BY event_date", (*symbols,CUTOFF))]
            for symbol in symbols:
                stored[symbol] = [dict(r) for r in conn.execute('SELECT symbol,seq_id,event_date,knowledge_date,category '
                    'FROM corporate_announcements WHERE symbol=? AND knowledge_date<=?',(symbol,CUTOFF))]
        framed = []
        for event in events:
            isin = by_symbol[event['symbol']]
            index = bisect.bisect_left(days[isin],event['event_date'])
            if index < 10:
                continue
            event = dict(event,isin=isin,start=days[isin][index-10],
                         end=(date.fromisoformat(event['event_date'])-timedelta(days=1)).isoformat(),
                         frozen_tier=tiers.get((event['symbol'],event['event_date'])))
            framed.append(event)
        by_isin = defaultdict(list)
        for event in framed:
            by_isin[event['isin']].append(event)
        rng = random.Random(SEED)
        chosen = rng.sample(sorted(by_isin),20)
        sample = [dict(rng.choice(sorted(by_isin[i],key=lambda e:(e['event_date'],e['symbol']))),
                       security_events=len(by_isin[i]),symbols=groups[i]) for i in chosen]
        inputs = dict(groups=groups,events=framed,stored=stored)
        INPUT.write_text(json.dumps(inputs,sort_keys=True)+'\n',encoding='utf-8')
        plan = dict(seed=SEED,cutoff=CUTOFF,security_population=195,securities_with_eligible_events=len(by_isin),
                    catalogue_events=len(events),eligible_events=len(framed),excluded_short_history=len(events)-len(framed),
                    sample=sample,input_sha256=file_hash(INPUT),source_hashes={str(p.relative_to(ROOT)):file_hash(p)
                    for p in (log,catalogue,classifications)},
                    method='Uniform sample of 20 securities with eligible events, then one uniform event per security. '
                           'Twenty bulk window calls reuse the backfill session. No resampling after responses. '
                           'Point estimate is the security-event-count-weighted changed-tier fraction times eligible events '
                           '(Hajek ratio). Report raw Horvitz-Thompson estimate too. Remaining sampled-window observations '
                           'are descriptive only. Identification bounds show the unobserved uncertainty; no precise population CI. '
                           'Any failed sampled window suppresses the point estimate. Counts compare the frozen tier and '
                           'the pre-backfill store with current bulk contents, not trading outcomes.')
        PLAN.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({k:v for k,v in plan.items() if k not in ('sample','source_hashes')},indent=2))
    finally:
        conn.close()
    return plan


def compare_event(event, raw, inputs):
    first,last = event['start'],event['end']
    bulk = {stable_id(r):r for r in raw if r.get('sm_isin')==event['isin'] and first<=r['sort_date'][:10]<=last}
    direct = {r['seq_id']:r for r in inputs['stored'][event['symbol']]
              if first<=r['event_date']<=last and r['knowledge_date']<=event['event_date']}
    sibling = {r['seq_id']:r for s in inputs['groups'][event['isin']] for r in inputs['stored'][s]
               if first<=r['event_date']<=last and r['knowledge_date']<=event['event_date']}
    bulk_tier = classify_disclosure_window([dict(category=(r.get('desc') or '').strip()) for r in bulk.values()])
    stored_tier = classify_disclosure_window(list(direct.values()))
    missing_ids = sorted(set(bulk)-set(direct))
    return dict(**event,stored_count=len(direct),sibling_count=len(sibling),bulk_count=len(bulk),
                stored_tier=stored_tier,bulk_tier=bulk_tier,
                changed_frozen_tier=bulk_tier!=event['frozen_tier'] if event['frozen_tier'] else None,
                changed_stored_tier=bulk_tier!=stored_tier,
                coverage_only_resolution=event['frozen_tier']=='UNKNOWN_COVERAGE' and not bulk,
                missing_disclosure_tier_change=bool(missing_ids) and bulk_tier!=stored_tier,
                missing_from_direct=missing_ids,missing_from_entire_group=sorted(set(bulk)-set(sibling)),
                already_stored_under_sibling=sorted(set(missing_ids)&set(sibling)),
                stored_absent_from_bulk=sorted(set(direct)-set(bulk)),
                response_symbols=sorted({r['symbol'] for r in bulk.values()}))


def run_audit(client):
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    if file_hash(INPUT)!=plan['input_sha256']:
        raise ValueError('Audit baseline changed after sample selection')
    inputs=json.loads(INPUT.read_text(encoding='utf-8'))
    primary,observed,failures=[],{},[]
    for case in plan['sample']:
        try:
            raw=fetch_window(client,date.fromisoformat(case['start']),date.fromisoformat(case['end']),component='audit',label='audit')
            primary.append(compare_event(case,raw,inputs))
            for event in inputs['events']:
                if case['start']<=event['start'] and event['end']<=case['end']:
                    observed[(event['symbol'],event['event_date'])]=compare_event(event,raw,inputs)
        except Exception as exc:
            failures.append(dict(isin=case['isin'],error_type=type(exc).__name__))
        print(f"Audit windows completed: {len(primary)}, failed: {len(failures)}",flush=True)
    known=[r for r in observed.values() if r['changed_frozen_tier'] is not None]
    changed=sum(r['changed_frozen_tier'] for r in known)
    result=dict(plan_sha256=file_hash(PLAN),primary=primary,failures=failures,
                observed_events=len(known),observed_changed_tiers=changed,
                observed_unchanged_tiers=len(known)-changed,descriptive_events=list(observed.values()),
                eligible_events=plan['eligible_events'],population_securities=195,
                conservative_identification_bounds=[changed,plan['eligible_events']-(len(known)-changed)],
                request_count=sum(r['component']=='audit' for r in client.trace))
    if len(primary)==20 and all(r['changed_frozen_tier'] is not None for r in primary):
        weighted=sum(r['security_events']*r['changed_frozen_tier'] for r in primary)
        fraction=weighted/sum(r['security_events'] for r in primary)
        result.update(sample_changed_tiers=sum(r['changed_frozen_tier'] for r in primary),
                      estimated_fraction=fraction,estimated_events=fraction*plan['eligible_events'],
                      horvitz_thompson_events=plan['securities_with_eligible_events']/20*weighted,
                      sample_missing_disclosure_tier_changes=sum(r['missing_disclosure_tier_change'] for r in primary),
                      estimated_missing_disclosure_tier_changes=plan['eligible_events']*
                        sum(r['security_events']*r['missing_disclosure_tier_change'] for r in primary)/
                        sum(r['security_events'] for r in primary))
    else:
        result['estimated_events']=None
    RESULT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    if sys.argv[1:]!=['--prepare']:
        raise SystemExit('Use --prepare for the read-only baseline; network execution uses the bounded session runner.')
    prepare()
