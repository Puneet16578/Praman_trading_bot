"""Readable tables for every registered follow-up comparison and missing group."""
import json


def number(value, scale=1):
    return 'unavailable' if value is None else f'{value * scale:.4f}'


def stat(value, scale=1):
    bounds = value.get('interval95')
    interval = 'unavailable' if bounds is None else ', '.join(number(v, scale) for v in bounds)
    warning = ' SMALL SAMPLE' if value.get('small_sample_warning') else ''
    return f"{number(value.get('estimate'), scale)} [{interval}]; draws={value.get('usable_replicates', 0)}{warning}"


def report_markdown(result):
    lines = ['# Shadow replay follow-up results', '',
             'Registered follow-up to previously known aggregate results. All intervals below are '
             '95% event-date-cluster bootstrap intervals with 2,000 replicates, seed 20261001. '
             'They are descriptive and not adjusted for multiple comparisons.', '',
             '## Limitations and scope', '',
             '- ATR20 ends on the decision date and includes the event bar. Price inputs are shared '
             'with screening and outcomes; quintiles are an incomplete observational control.',
             '- The 2026 period is a spent hold-out, reported descriptively. No forward-window events are read.',
             '- The 90% rule is a fixed research variant. Active rulebook, sizing and journals are unchanged. '
             'At the fill both variants are checked against the original 100% caps.',
             '- Zero-share variants abstain; they are not counted as safe fills. Unknown frozen inputs '
             'are excluded explicitly. Missing locked-circuit scenarios remain missing under the original convention.',
             '- Original raw-opening execution and corporate-action conventions, current identity maps '
             'and empty hypothetical portfolios remain. No independent predictive-edge or readiness claim follows.', '',
             '## Frozen primary volatility boundaries', '',
             'ATR20 / decision price in percent: ' + ', '.join(number(v) for v in result['boundaries_pct']) + '.', '',
             'Ties go to the upper interval. These boundaries are reused for 2026 and filled-only comparisons.', '']
    for period, analysis in result['periods'].items():
        lines += [f'## {period}', '',
                  f"Candidates: {analysis['n']}; missing original 90-session labels: {analysis['missing90']}. "
                  'Labels are retained unchanged; the controlled outcome is the original adverse20 measure.', '']
        for cohort, control in analysis['volatility'].items():
            lines += [f'### Volatility control: {cohort}', '',
                      'Missing volatility by screening state: `' + json.dumps(control['missing_volatility'], sort_keys=True) + '`.', '',
                      '| Quintile | PASS candidates / valid / missing | FAIL candidates / valid / missing | PASS rate % [95% CI] | FAIL rate % [95% CI] | FAIL minus PASS, pp [95% CI] | PASS / FAIL valid dates | Weight |',
                      '|---|---:|---:|---|---|---|---:|---:|']
            for q in control['quintiles']:
                p, f = q['passed'], q['failed']
                lines.append(f"| Q{q['quintile']} | {q['pass_candidates']} / {p['n_events']} / {q['pass_missing']} | "
                             f"{q['fail_candidates']} / {f['n_events']} / {q['fail_missing']} | {stat(p, 100)} | "
                             f"{stat(f, 100)} | {stat(q['difference'], 100)} | {p['date_clusters']} / {f['date_clusters']} | {q['weight']:.4f} |")
            lines += ['', '| Comparison | Estimate and interval, percentage points |', '|---|---|',
                      f"| Unstratified gap, same valid-volatility population | {stat(control['unstratified']['difference'], 100)} |",
                      f"| Standardized gap | {stat(control['standardized'], 100)} |",
                      f"| Attenuation: unstratified minus standardized | {stat(control['attenuation'], 100)} |", '']
        caps = analysis['caps']
        lines += ['### Fill-cap breaches', '',
                  f"Original passes {caps['original_passes']}; original fills {caps['original_fills']}; "
                  f"original NO_FILL {caps['original_no_fill']}; unknown inputs {caps['unknown_inputs']}; "
                  f"variant abstentions {caps['variant_abstentions']}; variant fills {caps['variant_fills']}.", '',
                  f"Original filled passes already exceeding a quantitative cap at the decision: "
                  f"{caps['original_decision_cap_breaches']}. Unknown locked components: {caps['unknown_locked_components']}; "
                  f"unknown historical-gap components: {caps['unknown_gap_components']}.", '',
                  '| Any-cap comparison | Breaches / evaluated fills | Rate % [95% CI] | Valid dates |',
                  '|---|---:|---|---:|']
        for name in ('baseline', 'variant', 'paired_baseline', 'paired_variant'):
            s = caps['any_cap'][name]
            lines.append(f"| {name} | {s.get('breaches', 'see paired rate')} / {s['n_events']} | {stat(s, 100)} | {s['date_clusters']} |")
        lines += ['', 'Paired any-cap difference (variant minus baseline), percentage points: ' +
                  stat(caps['any_cap']['paired_difference_variant_minus_baseline'], 100) + '.', '',
                  'Conditional excess sizes are percentages **over that cap**, among breaches of that cap. '
                  'Zero-inclusive sizes use every evaluable fill. Empty breach groups are unavailable.', '',
                  '| Cap / variant | Breaches / fills | Breach rate % [95% CI] | Conditional median excess % [95% CI] | Conditional p90 excess % [95% CI] | Breach dates | Zero-inclusive median excess % [95% CI] | Zero-inclusive p90 excess % [95% CI] |',
                  '|---|---:|---|---|---|---:|---|---|']
        for name, groups in caps['caps'].items():
            for variant in ('baseline', 'variant'):
                s = groups[variant]
                rate, positive, inclusive = s['rate'], s['conditional_excess_pct'], s['zero_inclusive_excess_pct']
                lines.append(f"| {name} / {variant} | {rate['breaches']} / {rate['n_events']} | {stat(rate, 100)} | "
                             f"{stat(positive['median'])} | {stat(positive['p90'])} | {positive['median']['date_clusters']} | "
                             f"{stat(inclusive['median'])} | {stat(inclusive['p90'])} |")
        lines += ['', '| Cap | Paired rate difference, pp [95% CI] | Conditional median size difference, pp [95% CI] | Conditional p90 size difference, pp [95% CI] |',
                  '|---|---|---|---|']
        for name, groups in caps['caps'].items():
            size = groups['conditional_size_difference_variant_minus_baseline']
            lines.append(f"| {name} | {stat(groups['paired_rate_difference_variant_minus_baseline'], 100)} | "
                         f"{stat(size['median'])} | {stat(size['p90'])} |")
        lines += ['', 'Size differences compare conditional distributions whose membership can change. '
                  'Caps overlap; counts cannot be summed. `per_trade` includes costs, `open_risk` uses '
                  'stress loss, `per_stock` and `per_sector` use position value, `order_adv` uses frozen '
                  'turnover and `exit_days` uses stressed exit capacity.', '']
    lines += ['## Provenance and reproduction', '', '```json', json.dumps(result['provenance'], indent=2), '```', '',
              '`python -u scripts/desk_shadow_followup.py`', '',
              'Full values, sample warnings and usable bootstrap counts: `shadow_replay_followup_results.json`. '
              'Protocol: `shadow_replay_followup_prereg.md`. No gate or the 90% factor was tuned.', '']
    return '\n'.join(lines)
