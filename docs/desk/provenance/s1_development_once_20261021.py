"""One authorized invocation of the frozen S1 development runner; never retry."""
from pathlib import Path
import sys, json, subprocess, time, traceback
from datetime import datetime, timezone
from contextlib import closing
from collections import Counter

ROOT = Path('D:/Agentic_ai_project/praman')
sys.path.insert(0, str(ROOT))
from desk.s1.report import sha256
from desk.s1 import statistics as S
from desk.s1.inputs import DEV_END, summarize
from desk.s1.evaluation import evaluate_inputs, sensitivity_inputs
from desk.s1.sensitivities import VARIANTS
from desk.s1.reader import RealReader
from desk.t1 import inputs as T
from desk.t1.panel import snapshot_identities
from desk.lib.costs import load_active_cost_config
from desk.lib.rulebook import load_active_rulebook
from shared.sqlite_readonly import open_readonly

ART = ROOT/'data/s1/inputs_complete_20261020_v1.json'
OUT = ROOT/'docs/desk/s1_development_results_20261021.json'
REPORT = OUT.with_suffix('.md')
ATTEMPT = ROOT/'data/s1/development_20261021.attempt.json'
DIGEST = 'c0d88d62719f090d1bde5430e9801ddad57d03715555f37914d2d6c3597bb309'

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()

def save(result):
    temporary = OUT.with_suffix('.json.partial')
    with temporary.open('w',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2,sort_keys=True,allow_nan=False)
    temporary.replace(OUT)

def formatted(value):
    if isinstance(value,float):
        return f'{value:.10g}'
    return json.dumps(value,ensure_ascii=False,sort_keys=True)

def render(result):
    lines=['# S1 locked development evaluation — 21 October 2026','',
           f"Status: **{result['status']}**. One invocation; no 2025 evaluation or rehearsal.",'',
           'Development period: 2019-10-01 through 2024-12-31. Registered horizons h=1 and h=3.',
           f"Code commit: `{result['meta']['code_commit']}`. Input SHA-256: `{DIGEST}`.",
           'The companion JSON is the complete locked result: every trade record, input/exclusion cell,',
           'breakdown, sensitivity, audit count, interval and provenance field. Returns below are',
           'decimal fractions (0.0025 = 0.25%); no winning horizon is selected.','',
           '## Preflight and inference','',
           'Fetched origin; clean master aligned. desk/s1 and scripts/s1_* unchanged since b539e7e.',
           'Artifact, active rulebook/cost and development index/ISIN payload hashes verified.',
           'Corrected rehearsal check passed: overall FAIL / NOT SHOWN at both horizons.',
           'Synthetic seed 20261020 controlled rehearsal randomness; bootstrap seed remains 20261001.',
           'Development reader end is 2024-12-31. Synthetic probes reject 2025 requests before SQL.',
           'Scheduled exits after the period are purged before occupancy or price reads. Delayed exits',
           'are censored at the same boundary; no next-period price is requested.','',
           'Frozen path: evaluation.evaluate_inputs -> statistics.evaluate -> t1.bootstrap.block_draws.',
           '```python',
           'FAMILY = (("a", 1), ("b", 1), ("a", 3), ("b", 3))',
           'SEED, DRAWS, BLOCK, MIN_USABLE = 20261001, 2000, 20, 1900',
           'weights = multiplicities(block_draws(len(dates), BLOCK, DRAWS, SEED), len(dates))',
           'np.quantile(usable, [.00625, .99375], method="linear")',
           '```',
           'Moving blocks of 20 consecutive weekday dates, uniform valid starts with replacement,',
           'ceil(T/20) blocks truncated to T. Complete date clusters share paired draws; empty dates',
           'remain and scheduled-purged dates are removed. Type-7 98.75% family intervals; 95% descriptive.',
           'Minimums: 100 valid trades and 30 distinct original dates per required group, missing rate',
           '<=5%, and >=1900 usable draws per test. Test (a) needs unexplained only; (b) needs both.',
           'Tests (a)/(b) require estimates >=0.0025 and family lower bounds >0. Consistency (c)',
           'requires at least three positive 2021–2024 years, each with >=30 valid unexplained trades.',
           'Overall PASS requires (a) and (c); (b) is reported separately. Sensitivities never decide it.','',
           '## Provenance and limitations','',
           f"Rulebook hash: `{result['meta']['rulebook_sha256']}`.",
           f"Cost hash: `{result['meta']['cost_config_sha256']}`.",
           'Stores were opened read-only; hashes before/after are in JSON. Live-store hashes can differ',
           'from the input freeze because the normal nightly appended data after that freeze.',
           'No population was rebuilt. Configured costs and frozen quantities apply; primary exit',
           'slippage is 0.15%, sensitivity 0.40%; limit-entry slippage is zero.',
           'Selection, ATR, market/peer measures and returns share prices and anchors. Filing coverage',
           'and liquidity filters select a non-random population; group differences are not causal.',
           'Dated identity/same-day bhavcopy availability and announcement publication timing remain',
           'assumptions. Catalogue identity stitching, weekday special-session/daily-bar ambiguity,',
           'weekend sessions within holds, absent historical GSM and configured costs remain limitations.',
           'No dividends are credited. Dividend diagnostics use parsed record/book-closure evidence,',
           'not a complete ex-dividend calendar; absent evidence is UNKNOWN.',
           'Benchmark members are fixed from D-known identities, using fill open to actual exit-session',
           'open. Intraday stop exits therefore have a benchmark endpoint mismatch. Missing members',
           'are counted, not imputed. Missing outcomes are never replaced with zero.',
           'The 2025 period is partly exposed by earlier research but is not evaluated here.',
           'Shared date-only firewall defect P8-094 remains open; this reader has a hard development end.','']
    if result.get('error'):
        lines += ['## Stopped','',json.dumps(result['error'],sort_keys=True),'No repair or rerun.','']
    for name, data in result['results'].items():
        lines += [f'## {name}','',f"Exit slippage: {data['slippage']}; synthetic: {data['synthetic']}.",'']
        for test in data['tests']:
            h=test['horizon']
            lines += [f'### Horizon {h}','',
                      f"**S1 {test['verdict']}; label {test['label']}.**",'']
            if test['label_statement']:
                lines += [test['label_statement'],'']
            lines += ['| Test | Estimate | Family 98.75% interval | Descriptive 95% | Usable draws | State |',
                      '|---|---:|---|---|---:|---|']
            for key in ('a','b'):
                t=test[key]
                lines.append(f"| {key} | {formatted(t['estimate'])} | {formatted(t['family_interval'])} | {formatted(t['descriptive_95'])} | {t['usable_draws']} | {t['state']} |")
            lines += ['',f"Consistency (c): **{test['c']['state']}**.",'',
                      '| Year | Valid unexplained trades | Mean net return | Qualifying positive |',
                      '|---|---:|---:|---|']
            for year,c in test['c']['cells'].items():
                lines.append(f"| {year} | {c['n']} | {formatted(c['mean'])} | {c['positive']} |")
            lines += ['',f"Bootstrap calendar dates: {test['calendar_dates']}. Unusable-draw reasons (overlapping):",'```json',
                      json.dumps(test['unusable_reasons'],indent=2,sort_keys=True),'```','',
                      '| Measure | Unexplained | Explained |','|---|---|---|']
            u,e=test['groups']['unexplained'],test['groups']['explained']
            for key in u:
                lines.append(f'| {key} | {formatted(u[key])} | {formatted(e[key])} |')
            lines += ['', 'Coverage/overlap audit (multiple reasons may apply to one hold):','```json',
                      json.dumps(data['audit'][str(h)],indent=2,sort_keys=True),'```','']
        lines += ['### Inputs before fills and actual position exclusions','',
                  'Scheduled overlap is a count, not a bound: delayed exits add exclusions; early stops remove them.',
                  '| Year | Group | h | Retained | Inputs eligible | Dates | Scheduled overlap |',
                  '|---|---|---:|---:|---:|---:|---:|']
        for c in data['input_cells']:
            lines.append(f"| {c['year']} | {c['group']} | {c['horizon']} | {c['retained']} | {c['inputs_eligible']} | {c['distinct_dates']} | {c['scheduled_overlap_count']} |")
        lines += ['', 'All standalone exclusion reasons and exact overlaps are retained in JSON input_cells.',
                  'Frozen development terciles: '+formatted(result['meta']['tercile_boundaries'])+'.','',
                  '### Descriptive breakdowns','',
                  'Complete measures for every breakdown cell are in JSON. Below: counts and mean returns.', '']
        for group, dimensions in data['breakdowns'].items():
            lines += [f'#### {group}','', '| Dimension | Cell | Valid | Dates | Mean | Missing rate |',
                      '|---|---|---:|---:|---:|---:|']
            for dimension,cells in dimensions.items():
                for key,c in cells.items():
                    lines.append(f"| {dimension} | {key} | {c['valid']} | {c['distinct_dates']} | {formatted(c['mean'])} | {formatted(c['missing_rate'])} |")
            lines.append('')
    lines += ['## Lock and next step','',
              'One development invocation only. No tuning, repair-and-rerun or 2025 invocation.',
              'The full-suite evidence and locking commit identify this result; the commit message records',
              'the final suite. 2025 rehearsal and evaluation require separate user approval.','']
    REPORT.write_text('\n'.join(lines),encoding='utf-8')

def audit(data):
    result={}
    for h in (1,3):
        result[str(h)]={}
        for g in ('unexplained','explained'):
            rows=[r for r in data['records'] if r['horizon']==h and r['group']==g]
            overlaps=Counter()
            for r in rows:
                if r.get('filled'):
                    flags=[k for k in ('missing_sessions','circuit_delays','dividend_sessions','dividend_unknown_sessions') if r.get(k)]
                    overlaps['+'.join(flags) or 'none']+=1
            result[str(h)][g]=dict(filled=sum(bool(r.get('filled')) for r in rows),
                benchmark_member_observations=sum(r.get('benchmark',{}).get('members',0) for r in rows),
                benchmark_missing_member_observations=sum(r.get('benchmark',{}).get('missing',0) for r in rows),
                hold_reason_overlaps=dict(overlaps))
    return result

def main():
    if any(p.exists() for p in (OUT,REPORT,ATTEMPT)):
        raise RuntimeError('Existing attempt/result; no rerun permitted.')
    assert git('branch','--show-current')=='master' and not git('status','--porcelain')
    assert git('rev-parse','HEAD')==git('rev-parse','origin/master')
    assert not git('diff','b539e7e','--','desk/s1','scripts/s1_*')
    assert sha256(ART)==DIGEST
    a=json.loads(ART.read_text(encoding='utf-8'))
    a['records']=[r for r in a['records'] if r['day']<=DEV_END]
    rb,cc=load_active_rulebook(),load_active_cost_config()
    assert rb.sha256==a['meta']['rulebook_sha256'] and cc.sha256==a['meta']['cost_config_sha256']
    assert (S.SEED,S.DRAWS,S.BLOCK,S.MIN_USABLE)==(20261001,2000,20,1900)
    indices,mismatches=T.load(ROOT/'data/raw/t1_sources',end=DEV_END)
    assert not mismatches
    snapshots=snapshot_identities(ROOT/'data/raw/isin_snapshots',end=DEV_END)
    stores=[ROOT/'data/processed/praman.db',ROOT/'data/desk/desk.sqlite']
    before={str(p.relative_to(ROOT)):sha256(p) for p in stores}
    result=dict(status='STARTED',results={},meta=dict(code_commit=git('rev-parse','HEAD'),
        input_sha256=DIGEST,input_artifact=str(ART),input_meta=a['meta'],
        rulebook_sha256=rb.sha256,cost_config_sha256=cc.sha256,
        store_hashes_before=before,tercile_boundaries=a['summary']['tercile_boundaries'],
        started_utc=datetime.now(timezone.utc).isoformat(),
        invocation_source=Path(__file__).read_text(encoding='utf-8')))
    with ATTEMPT.open('x',encoding='utf-8') as f:
        json.dump(dict(started_utc=result['meta']['started_utc'],input_sha256=DIGEST),f)
    save(result)
    start=time.perf_counter()
    try:
        with closing(open_readonly(stores[0])) as conn,closing(open_readonly(stores[1])) as desk:
            reader=RealReader(conn,desk,DEV_END,authorized=True,snapshots=snapshots,index_closes=indices)
            for name in ('primary',*VARIANTS):
                print('START '+name,flush=True)
                inputs=a if name in ('primary','exit_slippage_040') else sensitivity_inputs(a,name)
                cells=[c for c in summarize(inputs['records'])['cells'] if c['year']<=2024]
                data=evaluate_inputs(inputs,reader,cc.costs,period='development',
                    slippage=.004 if name=='exit_slippage_040' else .0015)
                data['input_cells']=cells
                data['audit']=audit(data)
                result['results'][name]=data
                save(result)
                print('COMPLETE '+name+f' elapsed={time.perf_counter()-start:.1f}s',flush=True)
        after={str(p.relative_to(ROOT)):sha256(p) for p in stores}
        result['meta']['store_hashes_after']=after
        assert before==after,'Store changed during evaluation'
        result['status']='COMPLETE_LOCKED'
        result['meta']['elapsed_seconds']=time.perf_counter()-start
        save(result)
        render(result)
        print('COMPLETE_LOCKED; reports written',flush=True)
    except BaseException as exc:
        result['status']='ABORTED_NO_RERUN'
        result['error']=dict(type=type(exc).__name__,frames=[dict(file=x.filename,line=x.lineno,function=x.name)
            for x in traceback.extract_tb(exc.__traceback__)])
        save(result)
        render(result)
        print('ABORTED_NO_RERUN '+type(exc).__name__,flush=True)
        return 1
    return 0

if __name__=='__main__':
    sys.exit(main())
