"""One-time, idempotent P8-069 note on the records decided for 2026-10-13 (user decision
2026-10-14). That night's announcement refresh failed its whole/split check on one filing
published during the refresh, so the receipt was PARTIAL and every candidate's disclosures were
UNKNOWN. Appends INCOMPLETE_DISCLOSURE_EVIDENCE annotations and a Strategy 0 run note; never edits
or re-decides a record.

    python -B scripts/desk_annotate_p8069.py
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desk.annotations import annotate_day_incomplete_disclosures
from desk.lib.connection import get_desk_connection

DAY = '2026-10-13'
REASON = ('Decided with incomplete disclosure data because of P8-069: the announcement refresh failed its '
          'whole/split check on one filing published during the refresh, so the receipt was PARTIAL and '
          'disclosures were UNKNOWN. Kept as the accurate record of what the system knew; not re-decided.')
EVIDENCE = dict(receipt_status='PARTIAL', failed_window='2026-10-12..2026-10-13',
                capture='data/raw/announcement_runs/20261013T123643127766')


def main(conn=None):
    own = conn is None
    conn = conn or get_desk_connection()
    try:
        counts = annotate_day_incomplete_disclosures(conn, day=DAY, defect='P8-069', reason=REASON, evidence=EVIDENCE)
        print(json.dumps(counts, indent=2))
        return counts
    finally:
        if own:
            conn.close()


if __name__ == '__main__':
    main()
