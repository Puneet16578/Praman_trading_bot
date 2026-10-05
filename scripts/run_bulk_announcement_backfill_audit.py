"""Explicitly authorized, foreground rollout: 30 backfill + 20 audit attempts."""
from datetime import date, datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings
from src.ingestion.nse_market_data.announcements_bulk import CaptureSession
from scripts.ingest_announcements_recent import main as refresh
from scripts.audit_announcement_renames import PLAN, INPUT, file_hash, run_audit
from desk.lib.connection import get_desk_connection
from desk.source_freshness import record_refresh, complete_through
from shared.market_time import market_today


def main():
    if sys.argv[1:] != ['--execute-approved']:
        raise SystemExit('No requests made; explicit --execute-approved is required')
    if market_today() != date(2026,10,5):
        raise SystemExit('This bounded rollout is registered for 2026-10-05 only')
    plan=json.loads(PLAN.read_text(encoding='utf-8'))
    if file_hash(INPUT)!=plan['input_sha256']:
        raise ValueError('Pre-backfill audit baseline hash mismatch')
    output=ROOT/'docs/desk/announcements_bulk_rollout_results.json'
    if output.exists():
        raise SystemExit('Rollout receipt already exists; do not repeat the approved request budget')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    conn=get_connection(get_settings().database_path)
    before={table:conn.execute(f'SELECT count(*) FROM {table}').fetchone()[0]
            for table in ('bhavcopy','corporate_announcements','corporate_actions','surveillance_flags','sebi_orders')}
    init_db(conn)
    after_schema={table:conn.execute(f'SELECT count(*) FROM {table}').fetchone()[0] for table in before}
    if before!=after_schema:
        raise RuntimeError('Additive schema setup changed durable row counts')
    client=CaptureSession(ROOT/'data/raw/announcement_runs'/stamp, {'backfill':30,'audit':20})
    report=dict(started_at=datetime.now(timezone.utc).isoformat(),before=before,after_schema=after_schema)
    try:
        client.get('cookie','https://www.nseindia.com')
        summary=refresh(date(2026,10,5),start_date=date(2026,9,10),conn=conn,client=client)
        report['backfill']=summary
        desk=get_desk_connection()
        try:
            record_refresh(desk,through_date=summary['end_date'],status=summary['status'],
                           failed_symbols=[],summary=summary)
            report['market_complete_through']=complete_through(desk,'__MARKET__')
        finally:
            desk.close()
        report['monthly_counts']=[dict(r) for r in conn.execute(
            "SELECT substr(event_date,1,7) AS month,count(*) AS stored_rows,count(DISTINCT seq_id) AS unique_announcements "
            "FROM corporate_announcements WHERE event_date BETWEEN '2026-09-01' AND '2026-10-05' "
            "AND knowledge_date<='2026-10-05' GROUP BY 1")]
        report['after']={table:conn.execute(f'SELECT count(*) FROM {table}').fetchone()[0] for table in before}
        if report['after']['corporate_announcements']-before['corporate_announcements'] != summary['inserted']:
            raise RuntimeError('Reported insert count does not match durable store delta')
        print('BACKFILL RESULT '+json.dumps(report,sort_keys=True),flush=True)
        report['audit']=run_audit(client)
    finally:
        report['requests']=client.trace
        report['finished_at']=datetime.now(timezone.utc).isoformat()
        output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        client.close()
        conn.close()
    print('ROLLOUT RECEIPT '+str(output),flush=True)
    return 0 if report.get('backfill',{}).get('status')=='COMPLETE' and not report.get('audit',{}).get('failures') else 1


if __name__=='__main__':
    raise SystemExit(main())
