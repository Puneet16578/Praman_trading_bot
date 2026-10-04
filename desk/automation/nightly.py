"""Nightly automatic paper run (A1): after ingestion and `desk scan`, with no human step."""
from desk.automation import strategy0
from desk.automation.levels import AutomationRefused
from desk.journal.store import record_journal_event
from desk.lib.connection import get_desk_connection
from desk.lib.costs import load_active_cost_config
from desk.lib.rulebook import load_active_rulebook
from desk.lib.store import get_live_connection, max_recorded_at
from desk.replay import current_git_head
from shared.market_time import market_today


def run_auto_paper(run_date=None, *, desk_db_path=None):
    """A crashed run is journalled as an operational failure (it counts toward the fill-failure
    kill switch) and then re-raised, so the nightly step still reports ERROR. A refusal by the
    automation level is policy, not an engine failure, and is not counted."""
    praman = get_live_connection()
    desk = get_desk_connection() if desk_db_path is None else get_desk_connection(desk_db_path)
    try:
        run_date = run_date or praman.execute('SELECT MAX(event_date) FROM bhavcopy').fetchone()[0]
        try:
            rb, costs = load_active_rulebook(), load_active_cost_config()
            return strategy0.run(praman, desk, run_date, rulebook=rb.rulebook, costs=costs.costs,
                                 rulebook_file=rb.version_file, rulebook_hash=rb.sha256, cost_config_hash=costs.sha256,
                                 code_commit=current_git_head(), praman_watermark=max_recorded_at(praman),
                                 today=market_today().isoformat())
        except AutomationRefused:
            raise
        except Exception as exc:
            desk.rollback()
            record_journal_event(desk, event_type=strategy0.RUN_FAILED_EVENT,
                                 detail=dict(run_date=run_date, error_type=type(exc).__name__))
            raise
    finally:
        desk.close()
        praman.close()
