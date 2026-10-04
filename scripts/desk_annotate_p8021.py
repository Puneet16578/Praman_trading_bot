"""One-time, idempotent P8-021 annotation of Desk records made while announcement ingestion had
lapsed (2026-09-19 until the freshness fix). Appends to record_annotations only; never edits a record.

    python scripts/desk_annotate_p8021.py --until <ISO timestamp of the fix deployment>
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desk.annotations import annotate_incomplete_disclosures
from desk.lib.connection import get_desk_connection


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--until', required=True, help='Records recorded at or after this are not annotated')
    args = parser.parse_args(argv)
    conn = get_desk_connection()
    try:
        print(json.dumps(annotate_incomplete_disclosures(conn, until=args.until), indent=2))
    finally:
        conn.close()


if __name__ == '__main__':
    main()
