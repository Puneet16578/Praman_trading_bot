"""Append a pooled historical reference for the requested assessment context."""
import os
for _name in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):
    os.environ[_name]='1'
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from desk.shadow_followup import DateBootstrap, volatility
from desk.volatility_context import BOUNDARIES
from scripts.desk_shadow_followup import load_records,sha256,git
from shared.market_time import market_today


def build_reference(rows,replicates=2000):
    from desk.shadow_followup import check_event
    for row in rows:
        check_event(row)
    selected=[r for r in rows if '2019-10-01'<=r['event_date']<='2025-12-31']
    boot=DateBootstrap(selected,replicates)
    values=np.asarray([volatility(r) for r in selected])
    outcome=np.asarray([np.nan if r['adverse20'] is None else float(r['adverse20']) for r in selected])
    groups=np.searchsorted(BOUNDARIES,values,side='right')+1
    result=dict(boundaries_pct=list(BOUNDARIES),known_on=market_today().isoformat(),
        population='All primary candidates pooled across screening states',
        boundary_convention='User-specified four-decimal frozen primary boundaries; ties go upward.',quintiles=[])
    for q in range(1,6):
        mask=np.isfinite(values)&(groups==q)
        rate,_=boot.mean(outcome,mask)
        result['quintiles'].append(dict(quintile=q,candidates=int(mask.sum()),
            missing_outcomes=int((mask&~np.isfinite(outcome)).sum()),rate=rate))
    return result


def main():
    sources=['scripts/desk_volatility_reference.py','desk/volatility_context.py','tests/test_volatility_context.py']
    for name in sources:
        git('ls-files','--error-unmatch',name)
    if git('diff','HEAD','--',*sources):
        raise ValueError('Commit tested reference implementation first.')
    path=ROOT/'docs/desk/shadow_replay_followup_results.json'
    result=json.loads(path.read_text(encoding='utf-8'))
    base=result['provenance']['original_provenance']
    raw=ROOT/base['raw_path']
    if sha256(raw)!=base['raw_sha256']:
        raise ValueError('Corrected replay hash mismatch.')
    reference=build_reference(load_records(raw))
    reference['provenance']=dict(code_commit=git('rev-parse','HEAD').decode().strip(),
        raw_sha256=base['raw_sha256'],seed=20261001,bootstrap_replicates=2000,
        source_hashes={name:sha256(ROOT/name) for name in sources})
    result['assessment_context']=reference
    path.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    from desk.shadow_followup_report import stat
    lines=['','## Historical volatility context for assessments','',
        'Pooled primary candidate rates, including both screening states. The assessment '
        'uses the user-specified rounded boundaries 3.2975 / 4.0429 / 4.7966 / 5.8627; '
        'the original controlled comparison above retains its exact unrounded boundaries. '
        'This is published retrospective context, never historical gate input.','',
        '| Quintile | Candidates / valid / missing | Adverse20 rate % [95% CI] | Date clusters |',
        '|---|---:|---|---:|']
    for q in reference['quintiles']:
        r=q['rate']
        lines.append(f"| Q{q['quintile']} | {q['candidates']} / {r['n_events']} / {q['missing_outcomes']} | {stat(r,100)} | {r['date_clusters']} |")
    lines+=['','Reference known on '+reference['known_on']+'. Reproduce: `python scripts/desk_volatility_reference.py`.','']
    md=path.with_suffix('.md');body=md.read_text(encoding='utf-8').split('\n## Historical volatility context for assessments')[0]
    md.write_text(body+'\n'.join(lines),encoding='utf-8',newline='\n')
    print(json.dumps(reference,indent=2))


if __name__=='__main__':
    main()
