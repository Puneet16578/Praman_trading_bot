"""desk CLI. Each subcommand is a thin wrapper over the already-tested modules -- no logic lives
here that isn't exercised by tests calling the underlying functions directly."""
from __future__ import annotations
import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from desk.evidence.bundle import assemble_evidence_bundle
from desk.gates.engine import run_assessment
from desk.journal import store as jstore
from desk.lib.connection import get_desk_connection
from desk.lib.costs import load_active_cost_config
from desk.lib.rulebook import load_active_rulebook
from desk.lib.store import get_live_connection, max_recorded_at
from desk.replay import current_git_head, replay_decision


def cmd_rulebook_validate(args):
    try:
        loaded = load_active_rulebook()
        print(f"OK: {loaded.version_file} ({loaded.sha256[:12]}...)")
    except Exception as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        raise SystemExit(1)


def cmd_rulebook_show(args):
    loaded = load_active_rulebook()
    print(json.dumps(loaded.rulebook.model_dump(), indent=2))


def cmd_assess(args):
    praman_conn = get_live_connection()
    desk_conn = get_desk_connection()
    rulebook = load_active_rulebook()
    costs = load_active_cost_config()

    thesis = None
    if args.thesis:
        import yaml
        thesis = yaml.safe_load(Path(args.thesis).read_text(encoding="utf-8"))

    as_of_date = args.as_of or _latest_bhavcopy_date(praman_conn)
    result = run_assessment(
        praman_conn, desk_conn, symbol=args.symbol, as_of_date=as_of_date,
        sector=(thesis or {}).get("sector"), thesis=thesis,
        rulebook=rulebook.rulebook, costs=costs.costs,
    )

    thesis_id = None
    if thesis:
        thesis_id = jstore.record_thesis(desk_conn, symbol=args.symbol, **{
            k: v for k, v in thesis.items() if k in (
                "evidence_cutoff", "hypotheses", "drivers", "catalyst", "horizon",
                "invalidation_conditions", "exit_price", "exit_time", "exit_evidence",
                "exit_risk", "exit_portfolio", "planned_entry", "planned_stop", "planned_target",
                "sector", "stress_loss", "position_size", "portfolio_risk_added", "user_probability",
            )
        })

    decision_id = jstore.record_decision(
        desk_conn, symbol=args.symbol, as_of_date=as_of_date, thesis_id=thesis_id,
        evidence_bundle_hash=result.evidence_bundle.content_hash() if result.evidence_bundle else "n/a",
        gate_results=result.gate_results_json(), state=result.state,
        rulebook_version=rulebook.version_file, rulebook_hash=rulebook.sha256,
        cost_config_version=costs.version_file, cost_config_hash=costs.sha256,
        code_commit=current_git_head(), praman_watermark=max_recorded_at(praman_conn),
        desk_watermark_value=jstore.desk_watermark(desk_conn),
        as_of_is_live=result.as_of_is_live, position_size=result.position_size,
        isin_map_built_at=result.isin_map_built_at,
        stress_loss_inr=result.stress_loss.stress_loss_inr if result.stress_loss else None,
    )

    print(f"decision_id={decision_id} state={result.state}")
    for gate, r in result.gate_results.items():
        print(f"  {gate}: {r.result} {list(r.reasons)}")
    if result.position_size is not None:
        print(f"  position_size={result.position_size:.2f}")
    if result.stress_loss is not None:
        loss = result.stress_loss
        print(f"  circuit_band={loss.circuit_band.label()}")
        print(f"  planned_stop_loss={loss.planned_loss_component_inr:.2f} stress_loss={loss.stress_loss_inr:.2f}")
        locked = f"{loss.locked_circuit_loss_inr:.2f}" if loss.locked_circuit_loss_inr is not None else "N/A"
        print(f"  locked_circuit_loss={locked}; {loss.circuit_band_caveat}")
    else:
        from desk.circuit_bands import band_as_of
        print(f"  circuit_band={band_as_of(desk_conn, args.symbol, as_of_date).label()}")
        print("  planned_stop_loss=N/A stress_loss=N/A locked_circuit_loss=N/A (no sized plan)")

    praman_conn.close()
    desk_conn.close()


def _latest_bhavcopy_date(conn) -> str:
    row = conn.execute("SELECT MAX(event_date) AS d FROM bhavcopy").fetchone()
    return row["d"]


def cmd_status(args):
    desk_conn = get_desk_connection()
    rulebook = load_active_rulebook()
    from desk.gates.engine import _open_risk_used_inr
    from desk.ingestion_health import ingestion_health_line, isin_map_health_line, latest_trading_date_line

    open_risk = _open_risk_used_inr(desk_conn)
    budget = rulebook.rulebook.risk.capital_allocated_inr * rulebook.rulebook.risk.max_open_risk_pct / 100.0
    print(f"Open risk used: {open_risk:.2f} / {budget:.2f}")
    print(f"Open positions: {jstore.open_trade_ids(desk_conn)}")
    print(ingestion_health_line())
    from desk.backups import status_line
    print(status_line())
    praman_conn = get_live_connection()
    try:
        print(latest_trading_date_line(praman_conn))
        print(isin_map_health_line(praman_conn, _latest_bhavcopy_date(praman_conn)))
    finally:
        praman_conn.close()
    desk_conn.close()


def cmd_paper_open(args):
    """Executes the ALREADY-APPROVED decision exactly as persisted -- never re-assesses (integrity
    fix b). See desk/paper/open.py for the two hindsight guards (integrity fix a). A PENDING result
    is logged as a PAPER_OPEN_PENDING journal event (decision_id, the frozen not_before_date) so
    `desk monitor` can complete the fill automatically later (Fix 2c, post-STOP-3 review) without
    requiring the human to remember to re-run this command."""
    from desk.paper.open import PaperOpenRefused, PendingOpen, open_approved_decision

    praman_conn = get_live_connection()
    desk_conn = get_desk_connection()
    try:
        loaded_costs = load_active_cost_config()
        result = open_approved_decision(praman_conn, desk_conn, args.decision_id,
                                         costs=loaded_costs.costs, cost_config_hash=loaded_costs.sha256)
        if isinstance(result, PendingOpen):
            jstore.record_journal_event(
                desk_conn, event_type="PAPER_OPEN_PENDING", decision_id=args.decision_id,
                detail={"not_before_date": result.not_before_date},
            )
            print(f"PENDING: no session with data yet after {result.not_before_date} -- "
                  f"`desk monitor` will complete this automatically once it is ingested "
                  f"(or re-run `desk paper open {args.decision_id}` manually).")
        else:
            print(f"opened at {result.price} on {result.event_date}")
    except PaperOpenRefused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        raise SystemExit(1)
    finally:
        praman_conn.close()
        desk_conn.close()


def cmd_paper_close(args):
    """Mirrors desk/paper/open.py's anti-hindsight design: no --price or --event-date -- both were
    the exact same hindsight loophole already closed for entries (they let any exit price be
    recorded on any past date). The exit fills at the store's own real (raw, never cost-adjusted)
    price for the first session strictly after this command's own recorded_at; the real round-trip
    sell-side cost from the active cost config is recorded in its own field -- see
    desk/paper/close.py. A PENDING result logs a PAPER_CLOSE_PENDING journal event so `desk monitor`
    completes it automatically, exactly like a pending open."""
    from desk.paper.close import PaperCloseRefused, PendingClose, close_approved_trade

    praman_conn = get_live_connection()
    desk_conn = get_desk_connection()
    try:
        loaded_costs = load_active_cost_config()
        result = close_approved_trade(praman_conn, desk_conn, args.trade_id, reason=args.reason,
                                       costs=loaded_costs.costs, cost_config_hash=loaded_costs.sha256)
        if isinstance(result, PendingClose):
            jstore.record_journal_event(
                desk_conn, event_type="PAPER_CLOSE_PENDING", trade_id=args.trade_id,
                detail={"not_before_date": result.not_before_date, "reason": result.reason},
            )
            print(f"PENDING: no session with data yet after {result.not_before_date} -- "
                  f"`desk monitor` will complete this automatically once it is ingested.")
        else:
            print(f"closed at {result.price:.2f} on {result.event_date}")
    except PaperCloseRefused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        raise SystemExit(1)
    finally:
        praman_conn.close()
        desk_conn.close()


def cmd_monitor(args):
    from desk.monitor import run_monitor

    praman_conn = get_live_connection()
    desk_conn = get_desk_connection()
    run_date = args.date or _latest_bhavcopy_date(praman_conn)
    report = run_monitor(praman_conn, desk_conn, run_date)
    print(json.dumps(report, indent=2, default=str))
    praman_conn.close()
    desk_conn.close()


def cmd_journal_show(args):
    desk_conn = get_desk_connection()
    events = desk_conn.execute("SELECT * FROM paper_trade_events WHERE trade_id = ? ORDER BY event_id", (args.trade_id,)).fetchall()
    for e in events:
        print(dict(e))
    desk_conn.close()


def cmd_evening(args):
    """Fix 2d (post-STOP-3 review): the one daily command for the evening routine. Refuses outright
    if today's data isn't in the store yet (no partial/best-effort run against yesterday's data
    silently passed off as today's) -- run ingestion first, or wait for the scheduled daily ingest,
    then re-run this. On a genuine weekend/holiday this will also refuse, correctly: there is no
    today's data to check for a day the market never traded, and this command does not maintain its
    own holiday calendar to distinguish that from a late ingestion (see scripts/weekly_ingest.py's
    step_bhavcopy_today for the same honestly-stated ambiguity). New assessments (`desk assess`)
    stay a separate, manual step -- this command only monitors and completes what was already
    approved."""
    from desk.monitor import run_monitor

    praman_conn = get_live_connection()
    desk_conn = get_desk_connection()
    try:
        from shared.market_time import market_today
        today = market_today().isoformat()
        latest = _latest_bhavcopy_date(praman_conn)
        if latest != today:
            print(f"REFUSED: today's data ({today}) is not yet in the store (latest ingested: "
                  f"{latest}). Run ingestion first (scripts/weekly_ingest.py, or wait for the "
                  f"scheduled daily run), then re-run `desk evening`.", file=sys.stderr)
            raise SystemExit(1)

        report = run_monitor(praman_conn, desk_conn, today)

        print(f"=== desk evening: {today} ===")
        print(f"What changed: {report.get('what_changed')}")

        pending_opens = report.get("pending_opens_completed", [])
        opens_filled = [p for p in pending_opens if p["status"] == "FILLED"]
        opens_refused = [p for p in pending_opens if p["status"] == "REFUSED"]
        opens_still_pending = len(pending_opens) - len(opens_filled) - len(opens_refused)
        print(f"Pending opens: {len(opens_filled)} filled, {len(opens_refused)} refused, {opens_still_pending} still pending")
        for f in opens_filled:
            print(f"  FILLED decision {f['decision_id']}: {f['event_date']} @ {f['price']:.2f}")
        for r in opens_refused:
            print(f"  REFUSED decision {r['decision_id']}: {r['detail']}")

        pending_closes = report.get("pending_closes_completed", [])
        closes_filled = [c for c in pending_closes if c["status"] == "FILLED"]
        closes_refused = [c for c in pending_closes if c["status"] == "REFUSED"]
        closes_still_pending = len(pending_closes) - len(closes_filled) - len(closes_refused)
        print(f"Pending closes: {len(closes_filled)} filled, {len(closes_refused)} refused, {closes_still_pending} still pending")
        for f in closes_filled:
            print(f"  CLOSED {f['trade_id']}: {f['event_date']} @ {f['price']:.2f}")
        for r in closes_refused:
            print(f"  REFUSED close {r['trade_id']}: {r['detail']}")

        exits = report.get("exits_triggered", [])
        print(f"Exits triggered: {len(exits)}")
        for e in exits:
            print(f"  EXIT {e['trade_id']}: {e['reason']} @ {e['price']}")

        print(f"Open positions: {list(report.get('positions', {}).keys())}")
    finally:
        praman_conn.close()
        desk_conn.close()


def cmd_replay(args):
    result = replay_decision(args.decision_id)
    print(f"decision {result.decision_id}: matched={result.matched}")
    if not result.matched:
        for line in result.diff:
            print(f"  MISMATCH: {line}")
        raise SystemExit(1)


def cmd_backup_verify(args):
    from desk.backups import verify_latest
    try:
        for report in verify_latest():
            print(json.dumps(report, sort_keys=True))
    except Exception as exc:
        print(f"REFUSED: restore verification failed ({type(exc).__name__})", file=sys.stderr)
        raise SystemExit(1)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="desk")
    sub = parser.add_subparsers(dest="command", required=True)

    backup = sub.add_parser("backup")
    backup_sub = backup.add_subparsers(dest="backup_command", required=True)
    backup_sub.add_parser("verify").set_defaults(func=cmd_backup_verify)

    p = sub.add_parser("rulebook")
    rb_sub = p.add_subparsers(dest="rulebook_command", required=True)
    rb_sub.add_parser("validate").set_defaults(func=cmd_rulebook_validate)
    rb_sub.add_parser("show").set_defaults(func=cmd_rulebook_show)

    p = sub.add_parser("assess")
    p.add_argument("symbol")
    p.add_argument("--thesis")
    p.add_argument("--as-of")
    p.set_defaults(func=cmd_assess)

    p = sub.add_parser("status")
    p.set_defaults(func=cmd_status)

    paper = sub.add_parser("paper")
    paper_sub = paper.add_subparsers(dest="paper_command", required=True)
    po = paper_sub.add_parser("open")
    po.add_argument("decision_id", type=int)
    po.set_defaults(func=cmd_paper_open)
    pc = paper_sub.add_parser("close")
    pc.add_argument("trade_id")
    pc.add_argument("--reason", required=True)
    pc.set_defaults(func=cmd_paper_close)

    p = sub.add_parser("monitor")
    p.add_argument("--date")
    p.set_defaults(func=cmd_monitor)

    p = sub.add_parser("evening")
    p.set_defaults(func=cmd_evening)

    j = sub.add_parser("journal")
    j_sub = j.add_subparsers(dest="journal_command", required=True)
    js = j_sub.add_parser("show")
    js.add_argument("trade_id")
    js.set_defaults(func=cmd_journal_show)

    p = sub.add_parser("replay")
    p.add_argument("decision_id", type=int)
    p.set_defaults(func=cmd_replay)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
