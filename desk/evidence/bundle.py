"""Assembles a symbol's evidence bundle, as of a date, through existing Praman functions ONLY --
no new signal computation. Each dimension becomes either a Fact (verified through the real
AdversaryAgent) or an Unknown (with a real uncertainty_category), never a silent None and never a
crash.

Disclosure categories in forward data (checked before writing this, not assumed): `src/signals/
disclosure_classification.py`'s `classify_category_safe()` -- the function `get_disclosure_window`'s
result is built on -- already never raises; an NSE category this project has never seen before
silently defaults to "ROUTINE" (a deliberate, documented Praman design choice: the safer failure
mode for a system that must never overclaim SUBSTANTIVE). That silent default is exactly wrong for
the Desk, which must not let a brand-new, unreviewed category quietly narrow what a report calls
grounded. So the Desk runs its OWN check first, using the STRICT `classify_category()` (which
raises), and treats any unmapped category as an Unknown on the whole disclosures dimension -- never
falling through to Praman's own safe-default tier for that window.
"""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, field, replace
from bisect import bisect_left

from src.agent.adversary import AdversaryAgent
from src.agent.models import EvidenceClaim
from src.bitemporal.guard import read_as_of
from src.mcp.tools import get_disclosure_window, get_surveillance_status
from src.signals.disclosure_classification import classify_category, classify_disclosure_window
from src.signals.event_catalogue import build_symbol_history, compute_daily_stats, TRAILING_WINDOW

from .types import Fact, Unknown

STRUCTURAL_BREAK_LOOKBACK_SESSIONS = 60  # matches the trailing window used elsewhere for z-score/volume_ratio


@dataclass
class EvidenceBundle:
    symbol: str
    as_of_date: str
    price: Fact | Unknown
    volume: Fact | Unknown
    delivery: Fact | Unknown
    disclosures: Fact | Unknown
    surveillance: Fact | Unknown
    corporate_actions: Fact | Unknown
    sector: Fact | Unknown
    fundamentals: Unknown = field(default_factory=lambda: Unknown("fundamentals", "epistemic", "Not ingested in Phase 1."))
    bid_ask_spread: Unknown = field(default_factory=lambda: Unknown("bid_ask_spread", "epistemic", "Not ingested in Phase 1."))
    circuit_band: Unknown = field(default_factory=lambda: Unknown("circuit_band", "epistemic", "Price-band data not ingested until a later phase."))

    def dimensions(self) -> dict[str, Fact | Unknown]:
        return {
            "price": self.price, "volume": self.volume, "delivery": self.delivery,
            "disclosures": self.disclosures, "surveillance": self.surveillance,
            "corporate_actions": self.corporate_actions, "sector": self.sector,
            "fundamentals": self.fundamentals, "bid_ask_spread": self.bid_ask_spread,
            "circuit_band": self.circuit_band,
        }

    def content_hash(self) -> str:
        """SHA-256 over each dimension's meaningful content (claim id/text/cited_value/source for a
        Fact; dimension/category/detail for an Unknown) -- deliberately not the EvidenceClaim's own
        `verify` closure (unhashable, and irrelevant to what a replay needs to confirm matched)."""
        parts = {}
        for name, evidence in sorted(self.dimensions().items()):
            if isinstance(evidence, Fact):
                c = evidence.claim
                parts[name] = {"kind": "Fact", "claim_id": c.claim_id, "text": c.text,
                                "cited_value": c.cited_value, "source": c.source}
            else:
                parts[name] = {"kind": "Unknown", "dimension": evidence.dimension,
                                "uncertainty_category": evidence.uncertainty_category, "detail": evidence.detail}
        canonical = json.dumps(parts, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _verify_and_wrap(claim: EvidenceClaim, unknown_on_reject: Unknown) -> Fact | Unknown:
    accepted, _findings = AdversaryAgent().verify([claim])
    if claim.claim_id not in {c.claim_id for c in accepted}:
        return unknown_on_reject
    return Fact(claim=claim)


def daily_stat_at(hist, as_of_date):
    """Call the unchanged catalogue statistic on its exact required 62-date window.

    Keep vintages, action prefixes and structural breaks intact. Verification calls
    recompute independently; no evidence value is cached or accepted on trust.
    """
    i = bisect_left(hist.trading_days, as_of_date)
    if i >= len(hist.trading_days) or hist.trading_days[i] != as_of_date:
        return None
    window = replace(hist, trading_days=hist.trading_days[max(0, i-TRAILING_WINDOW-1):i+1])
    return next((s for s in compute_daily_stats(window) if s.event_date == as_of_date), None)


def _price_volume_delivery(conn, symbol: str, as_of_date: str, hist) -> tuple[Fact | Unknown, Fact | Unknown, Fact | Unknown]:
    match = daily_stat_at(hist, as_of_date)
    if match is None:
        gap = Unknown("price", "measurement", f"No computable daily stat for {symbol} on {as_of_date}.")
        return gap, gap, gap

    def refetch(field_name: str):
        return lambda: getattr(daily_stat_at(hist, as_of_date), field_name)

    if match.return_1d is None:
        # A structural break (e.g. a demerger) inside the window compute_daily_stats needs makes
        # return_1d uncomputable -- real, observed on RELIANCE/2023-07-20. Unknown, not a crash.
        price: Fact | Unknown = Unknown("price", "measurement", f"return_1d not computable for {symbol} on {as_of_date} (likely a structural break in the trailing window).")
    else:
        price_claim = EvidenceClaim(
            claim_id=f"{symbol}:{as_of_date}:desk_return_1d", agent_role="DESK",
            text=f"1-session return on {as_of_date} was {match.return_1d:.2%}.",
            cited_value=match.return_1d, source="bhavcopy, adjusted close, event day",
            verify=refetch("return_1d"),
        )
        price = _verify_and_wrap(price_claim, Unknown("price", "measurement", "Adversary rejected the recomputed return_1d."))

    if match.volume_ratio is None:
        volume = Unknown("volume", "measurement", "volume_ratio not computable (insufficient trailing history).")
    else:
        volume_claim = EvidenceClaim(
            claim_id=f"{symbol}:{as_of_date}:desk_volume_ratio", agent_role="DESK",
            text=f"Traded quantity was {match.volume_ratio:.2f}x the trailing 60-session median.",
            cited_value=match.volume_ratio, source="bhavcopy, trailing 60-session median traded_qty",
            verify=refetch("volume_ratio"),
        )
        volume = _verify_and_wrap(volume_claim, Unknown("volume", "measurement", "Adversary rejected the recomputed volume_ratio."))

    if match.delivery_pct is None:
        delivery = Unknown("delivery", "measurement", "delivery_pct not reported for this row.")
    else:
        delivery_claim = EvidenceClaim(
            claim_id=f"{symbol}:{as_of_date}:desk_delivery_pct", agent_role="DESK",
            text=f"Delivery percentage was {match.delivery_pct:.2f}%.",
            cited_value=match.delivery_pct, source="bhavcopy delivery_pct, event day",
            verify=refetch("delivery_pct"),
        )
        delivery = _verify_and_wrap(delivery_claim, Unknown("delivery", "measurement", "Adversary rejected the recomputed delivery_pct."))

    return price, volume, delivery


def _disclosures(conn, symbol: str, as_of_date: str, source_complete_through: str | None = None) -> Fact | Unknown:
    """Missing data never reads as "no disclosure" (P8-021): a stale announcement source, a symbol
    with no announcement coverage at all, or too little history to check the window is UNKNOWN."""
    from desk.source_freshness import BACKFILL_COMPLETE_THROUGH, STALENESS_LIMIT_DAYS, required_through
    through = source_complete_through or BACKFILL_COMPLETE_THROUGH
    needed = required_through(as_of_date)
    if through < needed:
        return Unknown("disclosures", "measurement",
                       f"Announcement source known complete only through {through}; this window needs {needed} "
                       f"(staleness limit {STALENESS_LIMIT_DAYS} days). Missing announcements are not 'no disclosure'.")
    try:
        window = get_disclosure_window(conn, symbol, as_of_date)
    except Exception as exc:  # e.g. RecordNotFoundError if as_of_date isn't a real trading day
        return Unknown("disclosures", "execution", f"Could not fetch disclosure window: {exc}")
    if window.get("coverage") != "checked":
        return Unknown("disclosures", "measurement",
                       f"Disclosure window not checked ({window.get('coverage')}); its NONE tier is not evidence.")
    covered = conn.execute("SELECT 1 FROM corporate_announcements WHERE symbol=? AND knowledge_date<=? LIMIT 1",
                           (symbol, as_of_date)).fetchone()
    if covered is None:
        return Unknown("disclosures", "measurement",
                       "No announcement has ever been stored for this symbol as of the decision: coverage is "
                       "unknown, so an empty window is not 'no disclosure'.")

    unmapped = sorted({row["category"] for row in window["rows"] if _is_unmapped(row["category"])})
    if unmapped:
        return Unknown(
            "disclosures", "epistemic",
            f"Unmapped disclosure categor{'y' if len(unmapped) == 1 else 'ies'} encountered: "
            f"{unmapped} -- classify_disclosure_window() would silently default these to ROUTINE; "
            "the Desk treats an unreviewed category as UNKNOWN instead, never a silent default.",
        )

    def refetch_tier():
        return classify_disclosure_window(get_disclosure_window(conn, symbol, as_of_date)["rows"])

    tier_claim = EvidenceClaim(
        claim_id=f"{symbol}:{as_of_date}:desk_disclosure_tier", agent_role="DESK",
        text=f"Disclosure tier for the {window['window_sessions']}-session pre-event window: {refetch_tier()}.",
        cited_value=refetch_tier(), source="corporate_announcements via disclosure_classification.classify_disclosure_window",
        verify=refetch_tier,
    )
    return _verify_and_wrap(tier_claim, Unknown("disclosures", "measurement", "Adversary rejected the recomputed disclosure tier."))


def _is_unmapped(category: str) -> bool:
    try:
        classify_category(category)
        return False
    except ValueError:
        return True


def _surveillance(conn, symbol: str, as_of_date: str) -> Fact | Unknown:
    try:
        status = get_surveillance_status(conn, symbol, as_of_date)
    except Exception as exc:
        return Unknown("surveillance", "execution", f"Could not fetch surveillance status: {exc}")

    def refetch(field_name: str):
        return lambda: get_surveillance_status(conn, symbol, as_of_date)[field_name]

    claim = EvidenceClaim(
        claim_id=f"{symbol}:{as_of_date}:desk_surveillance", agent_role="DESK",
        text=f"ASM stage as of {as_of_date}: {status['asm_stage_as_of'] or 'not under ASM'}; "
             f"GSM stage: {status['gsm_stage_as_of'] or 'not under GSM'}.",
        cited_value=(status["asm_stage_as_of"], status["gsm_stage_as_of"]),
        source="surveillance_flags, current_surveillance_state as-of the assessment date",
        verify=lambda: (refetch("asm_stage_as_of")(), refetch("gsm_stage_as_of")()),
    )
    return _verify_and_wrap(claim, Unknown("surveillance", "measurement", "Adversary rejected the recomputed surveillance status."))


def _corporate_actions_and_structural_breaks(conn, symbol: str, as_of_date: str, hist) -> Fact | Unknown:
    idx = None
    try:
        idx = hist.trading_days.index(as_of_date)
    except ValueError:
        return Unknown("corporate_actions", "measurement", f"{as_of_date} is not in {symbol}'s own trading calendar.")

    start_idx = max(0, idx - STRUCTURAL_BREAK_LOOKBACK_SESSIONS)
    start_exclusive = hist.trading_days[start_idx]
    has_break = hist.structural_break_in_window(start_exclusive, as_of_date)

    actions = read_as_of(conn, "corporate_actions", as_of_date, symbol=symbol)
    recent_actions = [a for a in actions if start_exclusive < a["event_date"] <= as_of_date]

    claim = EvidenceClaim(
        claim_id=f"{symbol}:{as_of_date}:desk_structural_break", agent_role="DESK",
        text=(f"Structural break in the trailing {STRUCTURAL_BREAK_LOOKBACK_SESSIONS}-session window: {has_break}. "
              f"Corporate action(s) in that window: {[a['action_type'] for a in recent_actions] or 'none'}."),
        cited_value=has_break,
        source="corporate_actions, event_catalogue.structural_break_in_window",
        verify=lambda: hist.structural_break_in_window(start_exclusive, as_of_date),
    )
    return _verify_and_wrap(claim, Unknown("corporate_actions", "measurement", "Adversary rejected the recomputed structural-break check."))


def assemble_evidence_bundle(conn, symbol: str, as_of_date: str, sector: str | None, *,
                             disclosure_source_complete_through: str | None = None) -> EvidenceBundle:
    """`sector` is user-supplied in Phase 1 (item 5) -- typed as a Fact sourced from the user's own
    input if given, an Unknown otherwise. Never inferred or guessed.

    `extend_with_series=("BE","BZ")` -- without it, a stock currently in trade-for-trade settlement
    has no EQ row on `as_of_date` at all, so its OWN trading day is invisible to build_symbol_history
    and every price/volume/delivery dimension comes back Unknown -- not because the data doesn't
    exist, but because the default EQ-only history silently treats an actively-trading,
    surveillance-flagged stock as if it had gone dark (exactly the P8-012 finding from Praman's own
    research, re-discovered here independently: a real BE-series stock, ZEELEARN/2026-08-31,
    produced INSUFFICIENT instead of the expected VETO before this fix, for precisely this reason).
    G4 still independently detects and excludes the BE/BZ series itself via its own direct bhavcopy
    query -- this fix only restores the OTHER dimensions' visibility, it does not weaken G4.

    `disclosure_source_complete_through` is the announcement-source freshness watermark the caller
    read from its Desk connection (desk/source_freshness.py); omitted, only the backfill baseline
    applies, so a later decision's disclosures are UNKNOWN rather than silently "none" (P8-021).
    """
    hist = build_symbol_history(conn, symbol, extend_with_series=("BE", "BZ"))

    price, volume, delivery = _price_volume_delivery(conn, symbol, as_of_date, hist)
    disclosures = _disclosures(conn, symbol, as_of_date, disclosure_source_complete_through)
    surveillance = _surveillance(conn, symbol, as_of_date)
    corporate_actions = _corporate_actions_and_structural_breaks(conn, symbol, as_of_date, hist)

    if sector:
        sector_claim = EvidenceClaim(
            claim_id=f"{symbol}:{as_of_date}:desk_sector", agent_role="DESK",
            text=f"Sector (user-supplied): {sector}.", cited_value=sector,
            source="user input, Phase 1 (no independent sector data source ingested)", verify=None,
        )
        sector_evidence: Fact | Unknown = Fact(claim=sector_claim)
    else:
        sector_evidence = Unknown("sector", "epistemic", "No sector supplied by the user.")

    return EvidenceBundle(
        symbol=symbol, as_of_date=as_of_date, price=price, volume=volume, delivery=delivery,
        disclosures=disclosures, surveillance=surveillance, corporate_actions=corporate_actions,
        sector=sector_evidence,
    )
