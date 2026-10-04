"""Blueprint candidate schema (TRADING_BLUEPRINT.md section 3; session item B3).

Every field is either KNOWN, with a value and its definition, or UNKNOWN, with the reason and the
blueprint phase expected to supply it. An UNKNOWN field never carries a value, so no placeholder
number can be mistaken for an estimate. Contracts are appended to `decision_contracts`, linked to
exactly one Desk decision or one Strategy 0 candidate event; they never feed a gate or sizing.

Blueprint state rule (stated before any Strategy 0 run): the blueprint's ELIGIBLE requires all
research AND deterministic conditions. Research conditions (calibrated probability, expected
value) are UNKNOWN until T4, so no candidate is blueprint-ELIGIBLE yet. VETO when a hard rule
blocks the trade; NO_TRADE when evidence is insufficient or the screen failed; otherwise WATCH.
The Desk's own state is kept beside it, unchanged.

Model estimates (DESIGN.md constitution 3 and 5, amended 2026-10-04): a probability or expected
value may come only from a statistical model or from the user, never from an LLM and never
without a source. Until it passes the T4 calibration gate it is UNVALIDATED: displayed with that
label, display-only, and never able to make a candidate blueprint-ELIGIBLE. KNOWN additionally
requires a reference to the passed validation.
"""
import hashlib
import json
import math
from datetime import datetime, timezone

SCHEMA_VERSION = 1
FIELDS = (
    'symbol', 'direction', 'horizon', 'state', 'calibrated_probability', 'probability_interval',
    'uncertainty_score', 'expected_net_return_after_costs', 'expected_loss_if_wrong', 'expected_value',
    'maximum_adverse_excursion_estimate', 'maximum_favorable_excursion_estimate',
    'historical_analogue_count', 'market_regime', 'sector_regime', 'evidence_completeness',
    'forensic_flags', 'liquidity_state', 'portfolio_incremental_risk', 'invalidations',
    'rejection_reasons', 'model_version', 'rulebook_version', 'data_as_of', 'commit_hash',
)
BLUEPRINT_STATES = ('NO_TRADE', 'WATCH', 'ELIGIBLE', 'VETO')
RESEARCH_UNKNOWN = 'Research conditions (calibrated probability, expected value) are UNKNOWN until T4.'

# Fields later phases supply. Reasons are fixed text so every record says the same thing.
LATER_PHASES = {
    'calibrated_probability': ('T4', 'No calibrated model exists; raw scores are never probabilities.'),
    'probability_interval': ('T4', 'Requires a calibrated probability and an uncertainty method.'),
    'uncertainty_score': ('T4', 'Requires a preregistered uncertainty method over a calibrated model.'),
    'expected_net_return_after_costs': ('T3', 'Requires a baseline alpha model evaluated walk-forward with costs.'),
    'expected_loss_if_wrong': ('T5', 'Requires an empirical loss distribution conditional on failure. The '
                               'deterministic planned loss at the stop is recorded separately; it is not an '
                               'expectation because fills and gaps can exceed it (P8-043).'),
    'expected_value': ('T4', 'EV = P(win) x average win - P(loss) x average loss - costs needs calibrated P(win).'),
    'maximum_adverse_excursion_estimate': ('T5', 'Requires the historical analogue engine.'),
    'maximum_favorable_excursion_estimate': ('T5', 'Requires the historical analogue engine.'),
    'historical_analogue_count': ('T5', 'The historical analogue engine does not exist yet.'),
    'market_regime': ('T1', 'Point-in-time market regime features do not exist yet.'),
    'sector_regime': ('T1', 'Point-in-time sector regime features do not exist yet.'),
    'forensic_flags': ('T5', 'Forensic classifier outputs are not yet joined into Desk candidates.'),
}


MODEL_FIELDS = ('calibrated_probability', 'probability_interval', 'uncertainty_score',
                'expected_net_return_after_costs', 'expected_loss_if_wrong', 'expected_value',
                'maximum_adverse_excursion_estimate', 'maximum_favorable_excursion_estimate')
ALLOWED_SOURCES = ('statistical_model', 'user')
UNVALIDATED_LABEL = 'UNVALIDATED: display-only until it passes the T4 calibration gate.'


def known(value, definition):
    return dict(status='KNOWN', value=value, definition=definition)


def unknown(reason, supplied_by):
    return dict(status='UNKNOWN', reason=reason, supplied_by=supplied_by)


def unvalidated(value, *, source, definition, model_version=None):
    """A model or user estimate that has not passed the T4 calibration gate."""
    return dict(status='UNVALIDATED', value=value, source=source, model_version=model_version,
                definition=definition, label=UNVALIDATED_LABEL, display_only=True)


def _check_source(name, entry):
    if entry.get('source') not in ALLOWED_SOURCES:
        raise ValueError(f"{name}: an estimate needs a source in {ALLOWED_SOURCES} (never an LLM, never invented); "
                         f"got {entry.get('source')!r}.")
    if entry['source'] == 'statistical_model' and not entry.get('model_version'):
        raise ValueError(f'{name}: a statistical-model estimate must name its model version.')


def blueprint_state(desk_state, hard_veto):
    if hard_veto:
        return 'VETO'
    if desk_state in ('INSUFFICIENT', 'EXPIRED', 'SCREEN_FAIL'):
        return 'NO_TRADE'
    return 'WATCH'


def build_contract(*, symbol, desk_state, hard_veto, horizon, evidence_completeness, liquidity_state,
                   portfolio_incremental_risk, invalidations, rejection_reasons, model_version,
                   rulebook_version, data_as_of, commit_hash, extra=None, unknown_overrides=None):
    """`horizon`, `evidence_completeness`, `liquidity_state` and `portfolio_incremental_risk` are
    already known(...) / unknown(...) dicts. `unknown_overrides` may replace a later-phase reason."""
    state = blueprint_state(desk_state, hard_veto)
    contract = dict(
        schema_version=SCHEMA_VERSION,
        symbol=known(symbol, 'NSE symbol'),
        direction=known('LONG', 'Cash-equity delivery, LONG only (amendment 1).'),
        horizon=horizon,
        state=known(state, (RESEARCH_UNKNOWN + ' ' if state == 'WATCH' else '') +
                    'Blueprint state; see desk_state for the Desk state.'),
        desk_state=known(desk_state, 'Unchanged Desk or strategy state.'),
        evidence_completeness=evidence_completeness,
        liquidity_state=liquidity_state,
        portfolio_incremental_risk=portfolio_incremental_risk,
        invalidations=known(list(invalidations), 'Conditions that end the position or idea.'),
        rejection_reasons=known(list(rejection_reasons), 'Every reason the candidate is not accepted.'),
        model_version=known(model_version, 'Model used for any estimate in this record.'),
        rulebook_version=known(rulebook_version, 'Active rulebook file.'),
        data_as_of=known(data_as_of, 'Store watermark the record was built from.'),
        commit_hash=known(commit_hash, 'Code commit.'),
    )
    for name, (phase, reason) in LATER_PHASES.items():
        contract[name] = unknown((unknown_overrides or {}).get(name, reason), phase)
    if extra:
        contract['extra'] = extra
    validate_contract(contract)
    return contract


def validate_contract(contract):
    missing = [f for f in FIELDS if f not in contract]
    if missing:
        raise ValueError(f'Contract lacks {missing}.')
    for name in FIELDS:
        entry = contract[name]
        if entry.get('status') == 'UNKNOWN':
            if 'value' in entry or not entry.get('reason') or not entry.get('supplied_by'):
                raise ValueError(f'{name}: UNKNOWN needs a reason and supplier, and no value.')
        elif entry.get('status') in ('KNOWN', 'UNVALIDATED'):
            if 'value' not in entry or not entry.get('definition'):
                raise ValueError(f"{name}: {entry['status']} needs a value and its definition.")
            if _non_finite(entry['value']):
                raise ValueError(f'{name}: non-finite value.')
            if name in MODEL_FIELDS:
                _check_source(name, entry)
                if entry['status'] == 'KNOWN' and not entry.get('validation'):
                    raise ValueError(f'{name}: a KNOWN estimate must reference its passed T4 validation; '
                                     'otherwise it is UNVALIDATED.')
                if entry['status'] == 'UNVALIDATED' and (entry.get('display_only') is not True
                                                         or entry.get('label') != UNVALIDATED_LABEL):
                    raise ValueError(f'{name}: an UNVALIDATED estimate must be labelled and display-only.')
            elif entry['status'] == 'UNVALIDATED':
                raise ValueError(f'{name}: only model estimates can be UNVALIDATED.')
        else:
            raise ValueError(f'{name}: status must be KNOWN, UNVALIDATED or UNKNOWN.')
    if contract['state']['value'] not in BLUEPRINT_STATES:
        raise ValueError('Unknown blueprint state.')
    if contract['state']['value'] == 'ELIGIBLE' and any(
            contract[f]['status'] != 'KNOWN' for f in ('calibrated_probability', 'expected_value')):
        raise ValueError('Blueprint ELIGIBLE requires a validated calibrated probability and expected value.')
    return contract


def _non_finite(value):
    if isinstance(value, float):
        return not math.isfinite(value)
    if isinstance(value, dict):
        return any(_non_finite(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return any(_non_finite(v) for v in value)
    return False


def canonical(contract):
    return json.dumps(contract, sort_keys=True, separators=(',', ':'), allow_nan=False)


def record_contract(conn, contract, *, decision_id=None, strategy_event_id=None):
    if (decision_id is None) == (strategy_event_id is None):
        raise ValueError('A contract links to exactly one decision or strategy event.')
    validate_contract(contract)
    text = canonical(contract)
    conn.execute('INSERT INTO decision_contracts (decision_id,strategy_event_id,contract,content_hash,recorded_at) '
                 'VALUES (?,?,?,?,?)', (decision_id, strategy_event_id, text,
                                        hashlib.sha256(text.encode('utf-8')).hexdigest(),
                                        datetime.now(timezone.utc).isoformat()))


def assessment_contract(result, *, symbol, thesis, rulebook_version, data_as_of, commit_hash):
    """Contract for a `desk assess` decision, from the stored assessment result."""
    from desk.evidence.coverage import compute_coverage
    gates = result.gate_results_json()
    if result.evidence_bundle is not None:
        coverage = compute_coverage(result.evidence_bundle)
        total = len(coverage.present) + len(coverage.unknown)
        evidence = known(dict(present=list(coverage.present), unknown=list(coverage.unknown),
                              fraction_present=(len(coverage.present) / total) if total else None),
                         'Evidence dimensions present versus UNKNOWN in the decision bundle.')
    else:
        evidence = unknown('No evidence bundle was assembled for this decision.', 'T0')
    g5 = gates.get('G5')
    liquidity = (known(dict(result=g5['result'], reasons=g5['reasons']), 'G5 liquidity gate result.')
                 if g5 else unknown('G5 was not evaluated.', 'T0'))
    risk = (known(dict(stress_loss_inr=result.stress_loss.stress_loss_inr,
                       planned_loss_at_stop_inr=result.stress_loss.planned_loss_component_inr),
                  'Cost-inclusive stress and planned loss added to the portfolio (G6 inputs).')
            if result.stress_loss is not None else unknown('No sized plan; incremental risk not computed.', 'T0'))
    reasons = [f'{g}: {r}' for g, v in gates.items() if v['result'] != 'PASS' for r in (v['reasons'] or [v['result']])]
    horizon = (unknown(f"Thesis horizon {thesis.get('horizon')!r} is not one of the 1/3/5/10-session horizons; "
                       'registered trading horizons arrive with T2 labels.', 'T2')
               if thesis else unknown('No thesis supplied.', 'T2'))
    return build_contract(
        symbol=symbol, desk_state=result.state, hard_veto=result.state == 'VETO', horizon=horizon,
        evidence_completeness=evidence, liquidity_state=liquidity, portfolio_incremental_risk=risk,
        invalidations=list((thesis or {}).get('invalidation_conditions') or []), rejection_reasons=reasons,
        model_version='NONE: deterministic gates; no model', rulebook_version=rulebook_version,
        data_as_of=data_as_of, commit_hash=commit_hash)
