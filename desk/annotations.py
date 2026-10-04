"""Append-only annotations on earlier Desk records (P8-021 addition; user decision 2026-10-04).

Records made while announcement ingestion had lapsed are annotated INCOMPLETE_DISCLOSURE_EVIDENCE,
never invalidated or edited: they are an accurate record of what the system knew at the time, which
is exactly what the "what did I miss?" review needs. Research filters on the annotation through
the `opportunity_log_annotated` and `decisions_annotated` views, or `annotated_ids` below.
"""
from datetime import date, datetime, timedelta, timezone
import json

from desk.lib.schema import INCOMPLETE_DISCLOSURE
from desk.source_freshness import BACKFILL_COMPLETE_THROUGH

LAPSE_FROM = '2026-09-19'   # first day after the 2026-09-18/19 backfill (P8-021 measurement)
_TARGETS = (('opportunity_log', 'opportunity_id', 'event_date'),
            ('opportunities', 'opportunity_id', 'as_of_date'),
            ('decisions', 'decision_id', 'as_of_date'))


def annotate_incomplete_disclosures(desk_conn, *, until: str, since: str = LAPSE_FROM) -> dict:
    """Annotate every opportunity and decision RECORDED in [since, until). Idempotent: a record
    already annotated is skipped (UNIQUE target/annotation). Returns counts per table."""
    now = datetime.now(timezone.utc).isoformat()
    counts = {}
    for table, key, dated in _TARGETS:
        rows = desk_conn.execute(f'SELECT {key} AS id, {dated} AS dated, recorded_at FROM {table} '
                                 'WHERE recorded_at >= ? AND recorded_at < ? ORDER BY 1', (since, until)).fetchall()
        added = 0
        for row in rows:
            window_end = (date.fromisoformat(row['dated']) - timedelta(days=1)).isoformat()
            detail = dict(defect='P8-021', lapse_from=since, annotated_until=until,
                          reason='Recorded while announcement ingestion had lapsed: a "no recent disclosure" '
                                 'reading may reflect missing data. Kept as the accurate record of what the '
                                 'system knew at the time; not invalidated.',
                          record_date=row['dated'], record_recorded_at=row['recorded_at'],
                          disclosure_window_needed_through=window_end,
                          source_complete_through=BACKFILL_COMPLETE_THROUGH,
                          window_extends_past_coverage=window_end > BACKFILL_COMPLETE_THROUGH)
            cursor = desk_conn.execute('INSERT OR IGNORE INTO record_annotations (target_table, target_id, annotation, '
                                       'detail, recorded_at) VALUES (?,?,?,?,?)',
                                       (table, row['id'], INCOMPLETE_DISCLOSURE, json.dumps(detail, sort_keys=True), now))
            added += cursor.rowcount
        counts[table] = dict(in_window=len(rows), newly_annotated=added)
    desk_conn.commit()
    return counts


def annotated_ids(desk_conn, table: str, annotation: str = INCOMPLETE_DISCLOSURE) -> set:
    return {r[0] for r in desk_conn.execute('SELECT target_id FROM record_annotations WHERE target_table=? AND annotation=?',
                                            (table, annotation))}
