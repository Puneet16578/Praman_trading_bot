"""Render every registered comparison, including missing and reversed results."""
import json


def report_markdown(provenance, summaries):
    lines = ['# Desk shadow replay results', '',
             'This is reconstructed, observational research, not evidence that either live-trading gate is met.', '',
             '## Limitations and missingness', '',
             'Current identity mappings reconstruct historical membership. Historical map freshness is unavailable. '
             'Candidates use an empty hypothetical portfolio. Fixed-band history is sparse; unknown bands are never zero. '
             'Labels and screening share price inputs and the event close; ATR stops mechanically affect stop outcomes. '
             'The 2026 period is descriptive only. Intervals are unadjusted for multiple comparisons.', '',
             'All tails use 20 global sessions; incomplete price windows are missing for 20-session statistics. '
             'Entry gaps use the first global session when observed, even if the rest of the window is missing. '
             'Adjusted paths use a constant share basis. Execution records retain the identical nightly raw-open, '
             'frozen-quantity convention; entry action dates can therefore differ from adjusted tail gaps. '
             'Circuit locks require all daily OHLC at the tick-rounded lower limit, using the previous market session report. '
             'This is only a daily-data proxy.', '',
             'Reason groups describe the same semantic check with numeric values and symbols removed; exact reasons remain in the raw artifact. '
             'Gate/reason groups overlap and are not additive or independent. Each cohort resamples event-date clusters '
             '2,000 times with seed 20261001. The all-candidate cohort is primary; filled-only is a selection-conditioned sensitivity.', '',
             '## Provenance', '', '```json', json.dumps(provenance, indent=2), '```', '']
    for period, cohorts in summaries.items():
        lines += [f'## {period}', '']
        for cohort, groups in cohorts.items():
            lines += [f'### {cohort}', '', '| Group | Events | Dates | NO_FILL | Zero size | Invalid | Incomplete 20 | Missing 90 | Band covered / unknown | Warning |',
                      '|---|---:|---:|---:|---:|---:|---:|---:|---:|---|']
            for name, row in groups.items():
                lines.append(f"| {name} | {row['n']} | {row['date_clusters']} | {row['no_fill']} | {row['zero_size']} | {row['invalid_plan']} | {row['incomplete20']} | {row['missing90']} | {row['band_covered']} / {row['band_unknown']} | {'small sample' if row['small_sample_warning'] else ''} |")
            lines += ['', '| Group / statistic | Estimate | n events / denominator | Missing events | 95% interval (usable draws) | Difference vs PASS | Difference 95% interval (usable draws) |', '|---|---:|---:|---:|---|---:|---|']
            def number(v):
                return 'unavailable' if v is None else f'{v:.6f}'
            def interval(s):
                return ('unavailable' if s.get('interval95') is None else ', '.join(number(v) for v in s['interval95'])) + f" ({s.get('usable_replicates',0)})"
            for name, row in groups.items():
                for metric, stat in row['metrics'].items():
                    diff = stat.get('difference_vs_pass', {})
                    warning = ' [small sample]' if stat['small_sample_warning'] else ''
                    lines.append(f"| {name} / {metric}{warning} | {number(stat['estimate'])} | {stat['n_events']} / {stat['denominator']:g} | {stat['missing_events']} | {interval(stat)} | {number(diff.get('estimate'))} | {interval(diff)} |")
            lines += ['']
    lines += ['## Reproduce', '', '`python -u scripts/desk_shadow_replay.py`', '',
              'Full denominators, missingness reasons and confidence intervals: `shadow_replay_results.json`. '
              'Event-level plans, evidence hashes, gates, execution records and labels: the raw artifact named in provenance. '
              'Rates and returns above are fractions; MAE is a nonnegative loss fraction. '
              'The signed 90-session mean is direction-aware market-relative return, not long-trade profit.', '']
    return '\n'.join(lines)
