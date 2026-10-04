"""Audit corrected replay against preserved pre-G6 records and reports."""
import json
from collections import Counter
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from desk.shadow_followup import CAPS, PERIODS, check_event, cap_measurements
from desk.shadow_followup_report import stat
from desk.lib.rulebook import LoadedRulebook
from desk.lib.costs import LoadedCostConfig
from scripts.desk_shadow_followup import sha256,git


def read(name):
    return json.loads((ROOT/'docs/desk'/name).read_text(encoding='utf-8'))


def flip_attribution(x,y,rb,costs):
    """Gates whose result changed and caps over limit at each record's own quantity."""
    gates=sorted(g for g in set(x['gates'])|set(y['gates'])
                 if x['gates'].get(g,{}).get('result')!=y['gates'].get(g,{}).get('result'))
    def over(row):
        try:
            measures=cap_measurements(row['plan'],row['plan']['decision_price'],row['plan']['quantity'],rb,costs)
        except ValueError as exc:
            return ['unmeasurable: '+str(exc)]
        return sorted(cap for cap,v in measures.items() if v['usage']>v['cap'])
    return dict(symbol=x['symbol'],event_date=x['event_date'],direction=x['state']+' -> '+y['state'],
                old_quantity=x['plan']['quantity'],new_quantity=y['plan']['quantity'],changed_gates=gates,
                old_caps_over=over(x),new_caps_over=over(y),
                old_reasons={g:x['gates'][g].get('reasons',[]) for g in gates},
                new_reasons={g:y['gates'][g].get('reasons',[]) for g in gates})


def main():
    old,new=read('shadow_replay_results_pre_g6.json'),read('shadow_replay_results.json')
    oldf,newf=read('shadow_replay_followup_results_pre_g6.json'),read('shadow_replay_followup_results.json')
    for key in ('praman_watermark','desk_watermark','rulebook','costs','eligible_events','catalogue_events','price_cutoff','market_index_cutoff'):
        if old['provenance'][key]!=new['provenance'][key]:
            raise AssertionError('Original/corrected input differs: '+key)
    if oldf['boundaries_pct']!=newf['boundaries_pct']:
        raise AssertionError('Frozen exact primary quintile boundaries changed.')
    rb=LoadedRulebook.model_validate(new['provenance']['rulebook']).rulebook
    costs=LoadedCostConfig.model_validate(new['provenance']['costs']).costs
    paths=[ROOT/'data/processed/desk_shadow_replay_pre_g6.jsonl',ROOT/new['provenance']['raw_path']]
    if sha256(paths[0])!=old['provenance']['raw_sha256'] or sha256(paths[1])!=new['provenance']['raw_sha256']:
        raise AssertionError('Raw artifact hash mismatch.')
    audit={name:dict(transitions=Counter(),quantity_changes=0,old_decision_caps=Counter(),
        new_decision_caps=Counter(),old_filled_decision_caps=Counter(),new_filled_decision_caps=Counter(),
        corrected_passes=0,unchanged_labels=0,unchanged_adverse20=0,quantity_decreases=0,quantity_increases=0,
        flip_causes=Counter(),flips=[]) for name,_,_ in PERIODS}
    from itertools import zip_longest
    with paths[0].open(encoding='utf-8') as a,paths[1].open(encoding='utf-8') as b:
        for left,right in zip_longest(a,b):
            if left is None or right is None:
                raise AssertionError('Raw record counts differ.')
            x,y=json.loads(left),json.loads(right)
            check_event(x);check_event(y)
            if (x['symbol'],x['event_date'])!=(y['symbol'],y['event_date']):
                raise AssertionError('Raw identity order differs.')
            name=next(name for name,start,end in PERIODS if start<=x['event_date']<=end)
            out=audit[name]
            out['transitions'][x['state']+' -> '+y['state']]+=1
            out['quantity_changes']+=x['plan']['quantity']!=y['plan']['quantity']
            out['quantity_decreases']+=y['plan']['quantity']<x['plan']['quantity']
            out['quantity_increases']+=y['plan']['quantity']>x['plan']['quantity']
            if x['state']!=y['state']:
                flip=flip_attribution(x,y,rb,costs)
                out['flips'].append(flip)
                out['flip_causes'][f"{flip['direction']}; gates {'+'.join(flip['changed_gates'])}; "
                                   f"caps over at old quantity {'+'.join(flip['old_caps_over']) or 'none'}; "
                                   f"at new quantity {'+'.join(flip['new_caps_over']) or 'none'}"]+=1
            for key in ('label','adverse20'):
                if x[key]!=y[key]:
                    raise AssertionError('Unaffected event outcome changed: '+key)
            out['unchanged_labels']+=1;out['unchanged_adverse20']+=1
            for prefix,row in [('old',x),('new',y)]:
                if row['state']!='SCREEN_PASS':
                    continue
                measures=cap_measurements(row['plan'],row['plan']['decision_price'],row['plan']['quantity'],rb,costs)
                for cap,value in measures.items():
                    if value['usage']>value['cap']:
                        out[prefix+'_decision_caps'][cap]+=1
                        if row['fill'] is not None:
                            out[prefix+'_filled_decision_caps'][cap]+=1
                if prefix=='new':
                    out['corrected_passes']+=1
                    if any(v['usage']>v['cap'] for v in measures.values()):
                        raise AssertionError('Corrected pass exceeds a decision cap.')
    output=dict(audit=audit,provenance=dict(code_commit=git('rev-parse','HEAD').decode().strip(),
        old_raw_sha256=sha256(paths[0]),new_raw_sha256=sha256(paths[1]),
        preregistration_addendum_commit='cb89f96',repair_commit='7801550'))
    lines=['# G6 correction: old and new results','',
        'The rulebook defines planned loss including buy and sell costs. The follow-up '
        'used that definition correctly. Original sizing divided its budget by gross stop '
        'distance and G6 omitted the per-trade check. Corrected sizing uses the same cost '
        'function as the gate and follow-up, with whole-share search. G6 independently '
        'rejects a cost-inclusive excess. No cap, rulebook or paper entry convention changed.','',
        'Preregistration addenda were committed at `cb89f96`, before the correction (`7801550`) '
        'and the complete reruns. Original results remain in `*_pre_g6.md/.json` and the '
        'preserved raw artifact. Quantities and potentially screening states change; outcomes '
        'and frozen volatility boundaries are independently checked unchanged.','']
    for name,_,_ in PERIODS:
        a=audit[name]
        lines += [f'## {name}: decision-cap audit','',
            f"State transitions: `{dict(a['transitions'])}`. Quantity changes: {a['quantity_changes']}. "
            f"Corrected passes checked: {a['corrected_passes']}. Unchanged full labels/adverse20: "
            f"{a['unchanged_labels']} / {a['unchanged_adverse20']}. Quantity decreases / increases: "
            f"{a['quantity_decreases']} / {a['quantity_increases']}.",'',
            f"Net SCREEN_PASS change: {a['transitions']['SCREEN_FAIL -> SCREEN_PASS']-a['transitions']['SCREEN_PASS -> SCREEN_FAIL']:+d} "
            f"({a['transitions']['SCREEN_FAIL -> SCREEN_PASS']} FAIL->PASS, {a['transitions']['SCREEN_PASS -> SCREEN_FAIL']} PASS->FAIL). "
            'Each flip is attributed by the gates whose result changed and the caps over limit at the '
            "record's own frozen quantity (per-event detail in the JSON companion):",'',
            '| Flip cause | Events |','|---|---:|']
        for cause,count in sorted(a['flip_causes'].items()):
            lines.append(f'| {cause} | {count} |')
        lines += ['',
            '| Cap | Old all passes | Old filled passes | New all passes | New filled passes |',
            '|---|---:|---:|---:|---:|']
        for cap in CAPS:
            lines.append(f"| {cap} | {a['old_decision_caps'][cap]} | {a['old_filled_decision_caps'][cap]} | {a['new_decision_caps'][cap]} | {a['new_filled_decision_caps'][cap]} |")
        for cohort in ('All candidates','Filled only'):
            lines += ['',f'### Original replay: {cohort}','',
                '| State / statistic | Old [95% CI] | New [95% CI] | Old / new valid N |','|---|---|---|---:|']
            for state in ('SCREEN_PASS','SCREEN_FAIL'):
                x,y=old['results'][name][cohort][state],new['results'][name][cohort][state]
                lines.append(f"| {state} candidates / NO_FILL | {x['n']} / {x['no_fill']} | {y['n']} / {y['no_fill']} | - |")
                for metric in x['metrics']:
                    left,right=x['metrics'][metric],y['metrics'][metric]
                    lines.append(f"| {state} {metric}, % | {stat(left,100)} | {stat(right,100)} | {left['n_events']} / {right['n_events']} |")
            x,y=oldf['periods'][name]['volatility'][cohort],newf['periods'][name]['volatility'][cohort]
            lines += ['',f'### First follow-up volatility: {cohort}','',
                '| Statistic | Old, pp [95% CI] | New, pp [95% CI] |','|---|---|---|']
            for label,left,right in [('Unstratified gap',x['unstratified']['difference'],y['unstratified']['difference']),
                ('Standardized gap',x['standardized'],y['standardized']),('Attenuation',x['attenuation'],y['attenuation'])]:
                lines.append(f'| {label} | {stat(left,100)} | {stat(right,100)} |')
            for left,right in zip(x['quintiles'],y['quintiles']):
                lines.append(f"| Q{left['quintile']} FAIL minus PASS | {stat(left['difference'],100)} | {stat(right['difference'],100)} |")
        x,y=oldf['periods'][name]['caps'],newf['periods'][name]['caps']
        lines += ['', '### First follow-up cap breaches at fills','',
            '| Cap / sizing | Old rate % [CI] | New rate % [CI] | Old median / p90 excess % [CI] | New median / p90 excess % [CI] |',
            '|---|---|---|---|---|']
        for variant in ('baseline','variant'):
            lines.append(f"| Any / {variant} | {stat(x['any_cap'][variant],100)} | {stat(y['any_cap'][variant],100)} | - | - |")
            for cap in CAPS:
                left,right=x['caps'][cap][variant],y['caps'][cap][variant]
                lq,rq=left['conditional_excess_pct'],right['conditional_excess_pct']
                lines.append(f"| {cap} / {variant} | {stat(left['rate'],100)} | {stat(right['rate'],100)} | {stat(lq['median'])} / {stat(lq['p90'])} | {stat(rq['median'])} / {stat(rq['p90'])} |")
        lines+=['']
    lines += ['## Verification scope','',
        'The real-assessment regression checks an ELIGIBLE decision with a binding per-trade '
        'budget, and real SCREEN_PASS decisions, against all six caps. The full replay asserts '
        'the same invariant for every corrected pass. This does not remove the separately '
        'documented approximation of existing portfolio risk or the missing historical band '
        'data. All prior research limitations remain. Full original gate-group statistics '
        'and all first-follow-up per-statistic denominators remain in each old/new JSON report.','',
        'Reproduce: `python scripts/desk_g6_comparison.py`.','']
    (ROOT/'docs/desk/g6_correction_comparison.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8',newline='\n')
    (ROOT/'docs/desk/g6_correction_comparison.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    print(json.dumps(output,indent=2))


if __name__=='__main__':
    main()
