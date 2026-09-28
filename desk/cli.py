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
        stress_loss_inr=result.stress_loss.stress_loss_inr if result.stress_loss else None,
    )

    print(f"decision_id={decision_id} state={result.state}")
    for gate, r in result.gate_results.items():
        print(f"  {gate}: {r.result} {list(r.reasons)}")
    if result.position_size is not None:
        print(f"  position_size={result.position_size:.2f} stress_loss={result.stress_loss.stress_loss_inr:.2f}")

    praman_conn.close()
    desk_conn.close()


def _latest_bhavcopy_date(conn) -> str:
    row = conn.execute("SELECT MAX(event_date) AS d FROM bhavcopy").fetchone()
    return row["d"]


def cmd_status(args):
    desk_conn = get_desk_connection()
    rulebook = load_active_rulebook()
    from desk.gates.engine import _open_risk_used_inr
    from desk.ingestion_health import ingestion_health_line

    open_risk = _open_risk_used_inr(desk_conn)
    budget = rulebook.rulebook.risk.capital_allocated_inr * rulebook.rulebook.risk.max_open_risk_pct / 100.0
    print(f"Open risk used: {open_risk:.2f} / {budget:.2f}")
    print(f"Open positions: {jstore.open_trade_ids(desk_conn)}")
    print(ingestion_health_line())
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
        result = open_approved_decision(praman_conn, desk_conn, args.decision_id)
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
    desk_conn = get_desk_connection()
    jstore.close_paper_trade(desk_conn, trade_id=args.trade_id, event_date=args.event_date,
                              price=args.price, reason=args.reason)
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
        today = date.today().isoformat()
        latest = _latest_bhavcopy_date(praman_conn)
        if latest != today:
            print(f"REFUSED: today's data ({today}) is not yet in the store (latest ingested: "
                  f"{latest}). Run ingestion first (scripts/weekly_ingest.py, or wait for the "
                  f"scheduled daily run), then re-run `desk evening`.", file=sys.stderr)
            raise SystemExit(1)

        report = run_monitor(praman_conn, desk_conn, today)

        print(f"=== desk evening: {today} ===")
        print(f"What changed: {report.get('what_changed')}")

        pending = report.get("pending_opens_completed", [])
        filled = [p for p in pending if p["status"] == "FILLED"]
        refused = [p for p in pending if p["status"] == "REFUSED"]
        still_pending = len(pending) - len(filled) - len(refused)
        print(f"Pending opens: {len(filled)} filled, {len(refused)} refused, {still_pending} still pending")
        for f in filled:
            print(f"  FILLED decision {f['decision_id']}: {f['event_date']} @ {f['price']:.2f}")
        for r in refused:
            print(f"  REFUSED decision {r['decision_id']}: {r['detail']}")

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


def main(argv=None):
    parser = argparse.ArgumentParser(prog="desk")
    sub = parser.add_subparsers(dest="command", required=True)

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
    pc.add_argument("--event-date", dest="event_date", required=True)
    pc.add_argument("--price", type=float, required=True)
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
