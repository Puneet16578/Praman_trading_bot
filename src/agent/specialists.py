"""The three evidence-gathering specialist agents -- Market Microstructure, Disclosure,
Surveillance. Each `.run()` goes through `mcp.tools.call_tool()` for every fact it needs (the
authorization gate, never bypassed), and emits `EvidenceClaim`s whose text is a plain factual
statement (CLAUDE.md invariant 12: values and raw inputs, never a verdict) and whose `verify`
closure lets the Adversary re-derive the cited number independently.

Claim wording is deliberately terse and numeric -- "Traded quantity was 3.20x the trailing
60-session median," not "trading was suspiciously heavy" -- matching CLAUDE.md's own example of
acceptable output ("Delivery 11% on 14x average volume; no disclosure in preceding 10 sessions").
"""
from __future__ import annotations

from ..classification.event_classifier import CATALOGUE_VOL_THRESHOLD, CATALOGUE_Z_THRESHOLD
from ..mcp.tools import (
    ROLE_DISCLOSURE, ROLE_MARKET_MICROSTRUCTURE, ROLE_SURVEILLANCE,
    call_tool, get_disclosure_window, get_market_microstructure, get_surveillance_status,
    has_announcement_coverage,
)
from ..signals.disclosure_classification import classify_category_safe
from .derivation_check import independent_delivery_percentile, independent_volume_ratio
from .models import AgentTaskResult, EvidenceClaim

DISCLOSURE_WINDOW_SESSIONS = 10

class MarketMicrostructureAgent:
    ROLE = ROLE_MARKET_MICROSTRUCTURE
    ALLOWED_TOOLS = ["get_market_microstructure"]

    def run(self, conn, symbol: str, event_date: str, budget) -> AgentTaskResult:
        try:
            data = call_tool(conn=conn, role=self.ROLE, tool_name="get_market_microstructure",
                              task_allowed_tools=self.ALLOWED_TOOLS, budget=budget,
                              symbol=symbol, event_date=event_date)
        except Exception as exc:
            return AgentTaskResult(role=self.ROLE, status="ERROR", errors=[str(exc)])

        def refetch(field: str):
            return lambda: get_market_microstructure(conn, symbol, event_date)[field]

        claims = []
        if data["volume_ratio"] is not None:
            claims.append(EvidenceClaim(
                claim_id=f"{symbol}:{event_date}:volume_ratio", agent_role=self.ROLE,
                text=f"Traded quantity was {data['volume_ratio']:.2f}x the trailing 60-session median traded quantity.",
                cited_value=data["volume_ratio"], source="bhavcopy, trailing 60-session median traded_qty",
                verify=refetch("volume_ratio"),
                derivation_verify=lambda: independent_volume_ratio(conn, symbol, event_date),
            ))
        if data["delivery_pct"] is not None:
            claims.append(EvidenceClaim(
                claim_id=f"{symbol}:{event_date}:delivery_pct", agent_role=self.ROLE,
                text=f"Delivery percentage was {data['delivery_pct']:.2f}%.",
                cited_value=data["delivery_pct"], source="bhavcopy delivery_pct, event day",
                verify=refetch("delivery_pct"),
            ))
            if data["delivery_pct_percentile_60d"] is not None:
                claims.append(EvidenceClaim(
                    claim_id=f"{symbol}:{event_date}:delivery_pct_percentile_60d", agent_role=self.ROLE,
                    text=(f"Delivery percentage on the event day ranked at the "
                          f"{data['delivery_pct_percentile_60d']:.0f}th percentile of its own trailing 60-session distribution."),
                    cited_value=data["delivery_pct_percentile_60d"], source="bhavcopy delivery_pct, trailing 60-session distribution",
                    verify=refetch("delivery_pct_percentile_60d"),
                    derivation_verify=lambda: independent_delivery_percentile(conn, symbol, event_date),
                ))
        if data["zscore_60d"] is not None:
            claims.append(EvidenceClaim(
                claim_id=f"{symbol}:{event_date}:zscore", agent_role=self.ROLE,
                text=f"The event-day return had a z-score of {data['zscore_60d']:.2f} against its trailing 60-session return distribution.",
                cited_value=data["zscore_60d"], source="bhavcopy, trailing 60-session return distribution",
                verify=refetch("zscore_60d"),
            ))
        if data["return_20d"] is not None:
            claims.append(EvidenceClaim(
                claim_id=f"{symbol}:{event_date}:return_20d", agent_role=self.ROLE,
                text=f"The cumulative return over the 20 sessions from the event was {data['return_20d']:.2%}.",
                cited_value=data["return_20d"], source="bhavcopy, adjusted close, event to event+20 sessions",
                verify=refetch("return_20d"),
            ))
        if data["raw_inputs"] is not None:
            r = data["raw_inputs"]
            claims.append(EvidenceClaim(
                claim_id=f"{symbol}:{event_date}:raw_ohlc", agent_role=self.ROLE,
                text=(f"Raw event-day bhavcopy: open {r['open_price']}, high {r['high_price']}, "
                      f"low {r['low_price']}, close {r['close_price']}, traded quantity {r['traded_qty']}, "
                      f"delivery quantity {r['delivery_qty']}."),
                cited_value=r, source="bhavcopy, event day, raw values",
                verify=refetch("raw_inputs"),
            ))
        if data["zscore_60d"] is not None and data["volume_ratio"] is not None:
            z_ok = abs(data["zscore_60d"]) > CATALOGUE_Z_THRESHOLD
            vol_ok = data["volume_ratio"] > CATALOGUE_VOL_THRESHOLD

            def refetch_membership():
                d = get_market_microstructure(conn, symbol, event_date)
                if d["zscore_60d"] is None or d["volume_ratio"] is None:
                    return None
                return (abs(d["zscore_60d"]) > CATALOGUE_Z_THRESHOLD, d["volume_ratio"] > CATALOGUE_VOL_THRESHOLD)

            claims.append(EvidenceClaim(
                claim_id=f"{symbol}:{event_date}:catalogue_membership", agent_role=self.ROLE,
                text=(f"This project's catalogue requires BOTH |z-score| > {CATALOGUE_Z_THRESHOLD} AND "
                      f"volume_ratio > {CATALOGUE_VOL_THRESHOLD}x, not either alone. This event: |z-score| "
                      f"{abs(data['zscore_60d']):.2f} ({'clears' if z_ok else 'does not clear'} "
                      f"{CATALOGUE_Z_THRESHOLD}); volume_ratio {data['volume_ratio']:.2f}x "
                      f"({'clears' if vol_ok else 'does not clear'} {CATALOGUE_VOL_THRESHOLD}x)."),
                cited_value=(z_ok, vol_ok),
                source="scripts/build_final_event_catalogue.py:is_event() thresholds, applied to this event's own live-recomputed signals",
                verify=refetch_membership,
            ))
        return AgentTaskResult(role=self.ROLE, status="OK", claims=claims, tool_calls=["get_market_microstructure"])

class DisclosureAgent:
    ROLE = ROLE_DISCLOSURE
    ALLOWED_TOOLS = ["has_announcement_coverage", "get_disclosure_window"]

    def run(self, conn, symbol: str, event_date: str, budget) -> AgentTaskResult:
        try:
            coverage = call_tool(conn=conn, role=self.ROLE, tool_name="has_announcement_coverage",
                                  task_allowed_tools=self.ALLOWED_TOOLS, budget=budget, symbol=symbol)
        except Exception as exc:
            return AgentTaskResult(role=self.ROLE, status="ERROR", errors=[str(exc)])

        if not coverage:
            claim = EvidenceClaim(
                claim_id=f"{symbol}:{event_date}:no_coverage", agent_role=self.ROLE,
                text="No cached announcement data exists for this symbol; disclosure coverage could not be checked for this event.",
                cited_value=False, source="corporate_announcements, symbol-level coverage check",
                verify=lambda: has_announcement_coverage(conn, symbol),
            )
            return AgentTaskResult(role=self.ROLE, status="OK", claims=[claim], tool_calls=["has_announcement_coverage"])

        try:
            window = call_tool(conn=conn, role=self.ROLE, tool_name="get_disclosure_window",
                                task_allowed_tools=self.ALLOWED_TOOLS, budget=budget,
                                symbol=symbol, event_date=event_date, window_sessions=DISCLOSURE_WINDOW_SESSIONS)
        except Exception as exc:
            return AgentTaskResult(role=self.ROLE, status="ERROR", errors=[str(exc)])

        def refetch_tier():
            return get_disclosure_window(conn, symbol, event_date, DISCLOSURE_WINDOW_SESSIONS)["tier"]

        claims = []
        for row in window["rows"]:
            row_tier = classify_category_safe(row["category"])
            desc_suffix = f" -- {row['description']}" if row.get("description") else ""
            claims.append(EvidenceClaim(
                claim_id=f"{symbol}:{event_date}:announcement:{row['seq_id']}", agent_role=self.ROLE,
                text=(f"[{row_tier}] '{row['category']}' announcement (seq_id {row['seq_id']}) disclosed "
                      f"{row['event_date']}, before this event{desc_suffix}."),
                cited_value=True, source="corporate_announcements",
                verify=(lambda seq_id=row["seq_id"]: seq_id in {
                    r["seq_id"] for r in get_disclosure_window(conn, symbol, event_date, DISCLOSURE_WINDOW_SESSIONS)["rows"]
                }),
            ))
        if window["rows"]:
            claims.append(EvidenceClaim(
                claim_id=f"{symbol}:{event_date}:attachment_url_unavailable", agent_role=self.ROLE,
                text=("Attachment URLs are not captured by this project's announcement ingestion "
                      "(only category and, when NSE provided one, a short description are stored); "
                      "none can be shown for the disclosures listed above."),
                cited_value=True, source="src/bitemporal/schema.py:CORPORATE_ANNOUNCEMENTS (no attachment-file column)",
                verify=lambda: True,
            ))
        claims.append(EvidenceClaim(
            claim_id=f"{symbol}:{event_date}:disclosure_tier", agent_role=self.ROLE,
            text=(f"Disclosure tier for the {window['window_sessions']}-session pre-event window "
                  f"({window['rows'] and 'starting ' + window['window_start'] or 'no announcements found'}): {window['tier']}."),
            cited_value=window["tier"], source="disclosure_classification.classify_disclosure_window",
            verify=refetch_tier, window_description=f"{window['window_sessions']} sessions",
            canonical_window=f"{DISCLOSURE_WINDOW_SESSIONS} sessions",
        ))
        return AgentTaskResult(role=self.ROLE, status="OK", claims=claims,
                                tool_calls=["has_announcement_coverage", "get_disclosure_window"])

class SurveillanceAgent:
    ROLE = ROLE_SURVEILLANCE
    ALLOWED_TOOLS = ["get_surveillance_status"]

    def run(self, conn, symbol: str, event_date: str, budget) -> AgentTaskResult:
        try:
            data = call_tool(conn=conn, role=self.ROLE, tool_name="get_surveillance_status",
                              task_allowed_tools=self.ALLOWED_TOOLS, budget=budget,
                              symbol=symbol, event_date=event_date)
        except Exception as exc:
            return AgentTaskResult(role=self.ROLE, status="ERROR", errors=[str(exc)])

        def refetch(field: str):
            return lambda: get_surveillance_status(conn, symbol, event_date)[field]

        claims = [
            EvidenceClaim(
                claim_id=f"{symbol}:{event_date}:asm_stage", agent_role=self.ROLE,
                text=f"ASM stage as of the event date: {data['asm_stage_as_of'] or 'not under ASM'}.",
                cited_value=data["asm_stage_as_of"], source="surveillance_flags, current_surveillance_state as-of event_date",
                verify=refetch("asm_stage_as_of"),
            ),
            EvidenceClaim(
                claim_id=f"{symbol}:{event_date}:gsm_stage", agent_role=self.ROLE,
                text=f"GSM stage as of the event date: {data['gsm_stage_as_of'] or 'not under GSM'}.",
                cited_value=data["gsm_stage_as_of"], source="surveillance_flags, current_surveillance_state as-of event_date",
                verify=refetch("gsm_stage_as_of"),
            ),
            EvidenceClaim(
                claim_id=f"{symbol}:{event_date}:lead_time", agent_role=self.ROLE,
                text=f"Lead time to subsequent surveillance flag: {data['subsequent_flag_note']}.",
                cited_value=data["sessions_to_subsequent_flag"],
                source="surveillance_flags, full-history ENTRY timeline (retrospective)",
                verify=refetch("sessions_to_subsequent_flag"),
            ),
        ]
        return AgentTaskResult(role=self.ROLE, status="OK", claims=claims, tool_calls=["get_surveillance_status"])
