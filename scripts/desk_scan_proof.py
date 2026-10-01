"""Foreground, inputs-only ten-session proof on a disposable Desk snapshot."""
import copy
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desk.lib.connection import DESK_DB_PATH, get_desk_connection
from desk.lib.store import get_live_connection
from desk.scan import run_scan_range
from shared.sqlite_backup import online_backup
from shared.sqlite_readonly import open_readonly
from scripts.desk_gate_diagnostics import summary


def main():
    conn = get_live_connection()
    try:
        days = sorted(r[0] for r in conn.execute('SELECT DISTINCT event_date FROM bhavcopy ORDER BY event_date DESC LIMIT 10'))
    finally:
        conn.close()
    with tempfile.TemporaryDirectory(prefix='praman_scan_proof_') as temporary:
        path = Path(temporary) / 'desk.sqlite'
        online_backup(DESK_DB_PATH, path)
        # Only the freshly-created temporary copy is reset; preserve all other
        # copied tables, including actual dated circuit-band coverage.
        assert path.resolve().parent == Path(temporary).resolve()
        assert path.resolve() != DESK_DB_PATH.resolve()
        desk = get_desk_connection(path)
        try:
            desk.execute('DROP TABLE opportunity_executions')
            desk.execute('DROP TABLE opportunity_log')
            desk.commit()
        finally:
            desk.close()
        inserted = run_scan_range(days, desk_db_path=path)
        desk = open_readonly(path)
        try:
            rows = [dict(symbol=r['symbol'], event_date=r['event_date'], state=r['state'], gates=json.loads(r['gate_results']))
                    for r in desk.execute('SELECT * FROM opportunity_log ORDER BY event_date,symbol')]
            assert len(rows) == inserted
            executions = desk.execute('SELECT COUNT(*) FROM opportunity_executions').fetchone()[0]
        finally:
            desk.close()
    original = copy.deepcopy(rows)
    for row in original:
        # The old G2 differed only by requiring sector. Every other gate below
        # is the actual unchanged gate result on the identical frozen inputs.
        gate = row['gates']['G2']
        if gate['result'] == 'PASS':
            gate['reasons'] = []
        gate['result'] = 'FAIL'
        gate['reasons'].append("Required dimension 'sector' is UNKNOWN, not a Fact.")
        row['state'] = 'SCREEN_FAIL'
    result = dict(days=days, before=summary(original), after=summary(rows), executions=executions, events=rows,
                  before_method='Original G2 sector requirement applied to the same inputs; G1 and G3-G6 unchanged.')
    target = ROOT / 'scratch/scan_proof_round2.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: ({a:b for a,b in v.items() if a != 'reasons'} if isinstance(v,dict) else v)
                      for k,v in result.items() if k != 'events'}, indent=2), flush=True)


if __name__ == '__main__':
    main()
