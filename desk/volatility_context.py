"""Sourced retrospective context, kept outside evidence dimensions and gate inputs."""
from bisect import bisect_right
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path

from desk.evidence.types import Fact, Unknown
from src.agent.models import EvidenceClaim
from src.bitemporal.guard import latest_as_of
from src.signals.price_adjustment import compute_adjustment_factor, UnadjustableWindowError

BOUNDARIES = (3.2975, 4.0429, 4.7966, 5.8627)
SOURCE = Path(__file__).resolve().parents[1]/'docs/desk/shadow_replay_followup_results.json'


@dataclass(frozen=True)
class VolatilityContext:
    atr20: float | None
    decision_price: float | None
    atr20_pct: float | None
    quintile: int | None
    historical_rate: Fact | Unknown
    decision_as_of: str
    source_sha256: str | None = None
    reference_known_on: str | None = None

    @property
    def retrospective(self):
        """True when the reference was published after the decision it annotates."""
        return self.reference_known_on is not None and self.decision_as_of < self.reference_known_on

    def to_record(self):
        value = self.historical_rate
        historical = (dict(type='FACT', claim_id=value.claim.claim_id, source=value.claim.source,
                           text=value.claim.text, **value.claim.cited_value)
                      if isinstance(value, Fact) else
                      dict(type='UNKNOWN', detail=value.detail, uncertainty_category=value.uncertainty_category))
        return dict(atr20=self.atr20, decision_price=self.decision_price, atr20_pct=self.atr20_pct,
                    quintile=self.quintile, boundaries_pct=list(BOUNDARIES), historical_rate=historical,
                    decision_as_of=self.decision_as_of, reference_known_on=self.reference_known_on,
                    source_sha256=self.source_sha256, informational_only=True, retrospective=self.retrospective,
                    temporal_scope='Retrospective published context; excluded from historical decision evidence and all gates.')

    def display(self):
        prefix = ('ATR20 context: unavailable' if self.atr20_pct is None else
                  f'ATR20={self.atr20:.4f}; {self.atr20_pct:.4f}% of decision price; Q{self.quintile}')
        if isinstance(self.historical_rate, Unknown):
            return prefix+'; historical rate UNKNOWN: '+self.historical_rate.detail
        data = self.historical_rate.claim.cited_value
        lo, hi = data['interval95']
        return (prefix+f"; FACT: 2019-2025 pooled adverse20 rate {100*data['estimate']:.2f}% "
                f"[95% CI {100*lo:.2f}%, {100*hi:.2f}%]; source=shadow_replay_followup_results; "
                f"reference known {self.reference_known_on}; "
                f"{'RETROSPECTIVE (published after this decision); ' if self.retrospective else ''}information only")


def atr20_and_close(conn, symbol, as_of):
    rows = sorted((r for r in latest_as_of(conn, 'bhavcopy', as_of, symbol=symbol, series='EQ')
                   if r['event_date'] <= as_of), key=lambda r:r['event_date'])[-21:]
    if len(rows) != 21 or rows[-1]['event_date'] != as_of:
        raise ValueError('ATR20 requires 21 visible EQ sessions ending at the decision.')
    adjusted=[]
    for row in rows:
        factor=compute_adjustment_factor(conn,symbol,row['event_date'],as_of)
        values=[row[name]/factor for name in ('high_price','low_price','close_price')]
        if not all(math.isfinite(v) and v>0 for v in values) or values[0]<values[1]:
            raise ValueError('Invalid adjusted OHLC in ATR20 window.')
        adjusted.append(values)
    ranges=[max(high-low,abs(high-adjusted[i-1][2]),abs(low-adjusted[i-1][2]))
            for i,(high,low,_) in enumerate(adjusted) if i]
    return sum(ranges)/20, adjusted[-1][2]


def context_from_values(atr, price, as_of, *, source=SOURCE):
    if not all(isinstance(v,(float,int)) and math.isfinite(v) for v in (atr,price)) or atr<0 or price<=0:
        return unavailable(as_of,'Decision ATR20 or price is unavailable.')
    pct=100*atr/price
    quintile=bisect_right(BOUNDARIES,pct)+1
    try:
        raw=source.read_bytes()
        ref=json.loads(raw)['assessment_context']
        if ref['boundaries_pct'] != list(BOUNDARIES):
            raise ValueError('Historical reference boundaries differ from the frozen assessment boundaries.')
        rate=ref['quintiles'][quintile-1]
        if rate['quintile'] != quintile or rate['rate']['estimate'] is None:
            raise ValueError('Historical quintile reference is unavailable.')
        values=dict(rate['rate'], period='2019-10-01 through 2025-12-31',
                    population='All candidates pooled across SCREEN_PASS and SCREEN_FAIL', quintile=quintile)
        digest=hashlib.sha256(raw).hexdigest()
        fact=Fact(EvidenceClaim(claim_id=f'historical_volatility_q{quintile}',agent_role='desk_context',
            text='Observed historical frequency of a 20% adverse move within 20 global sessions from decision price.',
            cited_value=values,source=f'docs/desk/shadow_replay_followup_results.json#assessment_context; sha256={digest}'))
        return VolatilityContext(atr,price,pct,quintile,fact,as_of,digest,ref['known_on'])
    except (OSError,KeyError,ValueError,IndexError) as exc:
        return VolatilityContext(atr,price,pct,quintile,
            Unknown('volatility_context','measurement',str(exc)),as_of)


def unavailable(as_of,detail):
    return VolatilityContext(None,None,None,None,Unknown('volatility_context','measurement',detail),as_of)


def assessment_context(conn,symbol,as_of,decision_price=None):
    try:
        atr,close=atr20_and_close(conn,symbol,as_of)
        return context_from_values(atr,close if decision_price is None else decision_price,as_of)
    except (ValueError,UnadjustableWindowError) as exc:
        return unavailable(as_of,str(exc))
    except Exception as exc:
        # Information only: a lookup failure must never abort an already-recorded decision.
        return unavailable(as_of,f'Context lookup failed ({type(exc).__name__}): {exc}')


def record_context(desk_conn,context,*,symbol,decision_id=None,opportunity_id=None):
    """Append publication-dated context separately from historical decision inputs."""
    if (decision_id is None)==(opportunity_id is None):
        raise ValueError('Context must link to exactly one decision or opportunity.')
    from desk.journal.store import record_journal_event
    record_journal_event(desk_conn,event_type='VOLATILITY_CONTEXT',decision_id=decision_id,
        detail=dict(symbol=symbol,opportunity_id=opportunity_id,context=context.to_record()))
