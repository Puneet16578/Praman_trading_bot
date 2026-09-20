"""Phase 7c: the read-only tool registry every specialist agent must go through -- ported from
InsightForge's capability-registry + authorize_tool_call() pattern (src/agent/multi_agent/
authorization.py in the InsightForge tree), adapted rather than imported (CLAUDE.md "extend,
never fork" governs parallel implementations WITHIN a project, not reuse of a foundation across
projects -- this project copies the pattern, not the module).

Every tool here computes its answer FRESH from this project's own bitemporal store or its
directly-derived signal modules (src/signals/*) -- never from a cached report artifact -- so the
Adversary agent's "recompute the cited number and compare" check (adversary.py) is a real
independent re-derivation, not a comparison against the same cached value the claim came from.

Each ToolSpec declares which agent role may call it (`role`) and what kind of evidence it
produces (`evidence_type`) -- authorize_tool_call() below is the single gate every specialist
must pass through before a tool actually runs; CLAUDE.md's "all tool access through the
authorization gate" requirement is enforced here, not by convention.
"""
from __future__ import annotations
import bisect
from dataclasses import dataclass
from typing import Any, Callable

from ..bitemporal.guard import read_as_of
from ..signals.disclosure_classification import classify_disclosure_window
from ..signals.event_catalogue import build_symbol_history, compute_daily_stats
from ..signals.surveillance_state import build_surveillance_timeline, current_surveillance_state

ROLE_MARKET_MICROSTRUCTURE = "MARKET_MICROSTRUCTURE"
ROLE_DISCLOSURE = "DISCLOSURE"
ROLE_SURVEILLANCE = "SURVEILLANCE"
ROLE_ADVERSARY = "ADVERSARY"
ROLE_SYNTHESIS = "SYNTHESIS"
ROLE_SUPERVISOR = "SUPERVISOR"
KNOWN_ROLES = frozenset({
    ROLE_MARKET_MICROSTRUCTURE, ROLE_DISCLOSURE, ROLE_SURVEILLANCE, ROLE_ADVERSARY,
    ROLE_SYNTHESIS, ROLE_SUPERVISOR,
})

DISCLOSURE_WINDOW_SESSIONS = 10  # canonical value -- the Adversary's window check (adversary.py)
                                  # verifies every disclosure claim actually used exactly this,
                                  # never a narrower/wider window chosen to favor a tier.

class RecordNotFoundError(LookupError):
    """Raised by a tool when the record it was asked to fetch does not exist in the store -- the
    Adversary's record-existence check relies on this being a real, catchable failure, not a
    silently returned None that could be mistaken for 'zero'."""

@dataclass(frozen=True)
class ToolSpec:
    name: str
    role: str            # the only agent role authorized to call this tool
    evidence_type: str   # "microstructure" / "disclosure" / "surveillance"
    fn: Callable[..., Any]

def get_market_microstructure(conn, symbol: str, event_date: str) -> dict[str, Any]:
    """Recomputes the event day's Phase 5/6 signal set fresh from bhavcopy via
    build_symbol_history/compute_daily_stats -- not read from a cached catalogue CSV -- plus the
    raw inputs (open/high/low/close/traded_qty/delivery_qty) those signals were built from, per
    the roster requirement that this agent report "values AND raw inputs.\""""
    hist = build_symbol_history(conn, symbol)
    stats = compute_daily_stats(hist)
    match = next((s for s in stats if s.event_date == event_date), None)
    if match is None:
        raise RecordNotFoundError(
            f"No computable daily stat for {symbol} on {event_date} (insufficient trailing "
            f"history, or the date is not a real trading day for this symbol)."
        )
    raw_row = hist.price_row_as_of(event_date, "2099-01-01")
    return {
        "return_1d": match.return_1d, "return_20d": match.return_20d,
        "zscore_60d": match.zscore_60d, "percentile_60d": match.percentile_60d,
        "volume_ratio": match.volume_ratio, "delivery_pct": match.delivery_pct,
        "delivery_pct_percentile_60d": match.delivery_pct_percentile_60d,
        "trailing_return_count": match.trailing_return_count,
        "raw_inputs": {
            "open_price": raw_row["open_price"], "high_price": raw_row["high_price"],
            "low_price": raw_row["low_price"], "close_price": raw_row["close_price"],
            "traded_qty": raw_row["traded_qty"], "delivery_qty": raw_row["delivery_qty"],
        } if raw_row is not None else None,
        "trailing_window_sessions": 60,
    }

def get_disclosure_window(conn, symbol: str, event_date: str, window_sessions: int = DISCLOSURE_WINDOW_SESSIONS) -> dict[str, Any]:
    """Every corporate_announcements row for `symbol` in the `window_sessions` real trading
    sessions strictly before `event_date` (as-of `event_date` -- a restated/corrected row known
    only later must not leak backward), plus the resulting SUBSTANTIVE/ROUTINE_ONLY/NONE tier.
    `window_sessions` defaults to the canonical 10 -- a caller passing anything else is exactly
    what the Adversary's cherry-pick/window check exists to catch."""
    hist = build_symbol_history(conn, symbol)
    days = hist.trading_days
    idx = bisect.bisect_left(days, event_date)
    if idx >= len(days) or days[idx] != event_date:
        raise RecordNotFoundError(f"{event_date} is not a real trading day for {symbol}.")
    if idx < window_sessions:
        return {"rows": [], "tier": "NONE", "window_sessions": window_sessions,
                "window_start": None, "coverage": "insufficient_history"}

    window_start = days[idx - window_sessions]
    ann_rows = read_as_of(conn, "corporate_announcements", event_date, symbol=symbol)
    window_rows = sorted(
        (r for r in ann_rows if window_start <= r["event_date"] < event_date),
        key=lambda r: r["event_date"],
    )
    tier = classify_disclosure_window([{"category": r["category"]} for r in window_rows])
    return {
        "rows": [{"event_date": r["event_date"], "category": r["category"], "seq_id": r["seq_id"],
                  "description": r["description"]}
                 for r in window_rows],
        "tier": tier, "window_sessions": window_sessions, "window_start": window_start,
        "coverage": "checked",
    }

def has_announcement_coverage(conn, symbol: str) -> bool:
    row = conn.execute("SELECT 1 FROM corporate_announcements WHERE symbol=? LIMIT 1", (symbol,)).fetchone()
    return row is not None

def get_surveillance_status(conn, symbol: str, event_date: str) -> dict[str, Any]:
    """ASM/GSM stage as-of event_date (bitemporally correct, current_surveillance_state) plus the
    lead time to any subsequent flag if not already flagged (retrospective, SurveillanceTimeline --
    src/signals/surveillance_state.py -- see that module's docstring for why full/later knowledge
    is the correct convention for the second half of this answer and not the first)."""
    from ..classification.event_classifier import sessions_to_subsequent_flag

    state = current_surveillance_state(conn, symbol, event_date)
    asm_stage = state.get("ASM_LT") or state.get("ASM_ST")
    gsm_stage = state.get("GSM")
    hist = build_symbol_history(conn, symbol)
    timeline = build_surveillance_timeline(conn, symbol)
    gap, note = sessions_to_subsequent_flag(
        timeline=timeline, event_date=event_date, trading_days=hist.trading_days,
        asm_stage_as_of=asm_stage, gsm_stage_as_of=gsm_stage,
    )
    return {
        "asm_stage_as_of": asm_stage, "gsm_stage_as_of": gsm_stage,
        "full_state_as_of": state, "sessions_to_subsequent_flag": gap,
        "subsequent_flag_note": note,
    }

TOOL_REGISTRY: dict[str, ToolSpec] = {
    "get_market_microstructure": ToolSpec("get_market_microstructure", ROLE_MARKET_MICROSTRUCTURE, "microstructure", get_market_microstructure),
    "get_disclosure_window": ToolSpec("get_disclosure_window", ROLE_DISCLOSURE, "disclosure", get_disclosure_window),
    "has_announcement_coverage": ToolSpec("has_announcement_coverage", ROLE_DISCLOSURE, "disclosure", has_announcement_coverage),
    "get_surveillance_status": ToolSpec("get_surveillance_status", ROLE_SURVEILLANCE, "surveillance", get_surveillance_status),
}

@dataclass
class AuthorizationResult:
    allowed: bool
    reason: str

def authorize_tool_call(*, role: str, tool_name: str, task_allowed_tools: list[str], budget) -> AuthorizationResult:
    """Fail-closed authorization gate every specialist agent's tool call passes through --
    ported from InsightForge's authorize_tool_call() (role x tool x task-allowlist x budget), with
    the evidence-type-compatibility check dropped (this project has no separate capability-
    compatibility registry to check against; each tool declares exactly one evidence_type and
    exactly one authorized role, so that check would be redundant with the role check here)."""
    spec = TOOL_REGISTRY.get(tool_name)
    if spec is None:
        return AuthorizationResult(False, f"'{tool_name}' is not a registered tool.")
    if spec.role != role:
        return AuthorizationResult(False, f"Role '{role}' is not authorized to call '{tool_name}' (reserved for '{spec.role}').")
    if task_allowed_tools and tool_name not in task_allowed_tools:
        return AuthorizationResult(False, f"'{tool_name}' is not among the tools authorized for this specific task.")
    if not budget.can_call_tool(role):
        return AuthorizationResult(False, "Tool-call budget exhausted (global or per-agent).")
    return AuthorizationResult(True, "authorized")

def call_tool(*, conn, role: str, tool_name: str, task_allowed_tools: list[str], budget, **kwargs) -> Any:
    """The only path a specialist agent may use to invoke a tool -- raises PermissionError on any
    authorization failure rather than silently skipping the call, so a bug that bypasses
    authorize_tool_call() cannot happen by omission."""
    auth = authorize_tool_call(role=role, tool_name=tool_name, task_allowed_tools=task_allowed_tools, budget=budget)
    if not auth.allowed:
        raise PermissionError(auth.reason)
    budget.register_tool_call(role)
    return TOOL_REGISTRY[tool_name].fn(conn, **kwargs)
