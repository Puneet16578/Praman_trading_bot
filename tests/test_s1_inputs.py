import sqlite3
import unittest
from contextlib import closing
from datetime import datetime
from unittest.mock import patch

from desk.s1 import inputs as S
from desk.s1.report import timing_audit


class S1InputsTest(unittest.TestCase):
    def test_snapshot_strict_timing_and_carry(self):
        snapshots = [("2020-01-01", {"A": "INE1", "F": "INF1"}),
                     ("2020-01-03", {"B": "INE2"})]
        self.assertEqual(S.eligible_at(snapshots, "2020-01-01"), set())
        self.assertEqual(S.eligible_at(snapshots, "2020-01-03"), {"A"})
        self.assertEqual(S.eligible_at(snapshots, "2020-01-06"), {"A", "B"})

    def test_stream_never_reads_post_D_even_if_misdated_known(self):
        with closing(sqlite3.connect(":memory:")) as c:
            c.row_factory = sqlite3.Row
            def forbidden():
                raise AssertionError("post-D price")
            c.create_function("forbidden", 0, forbidden)
            c.executescript("""
                CREATE TABLE base(row_id,symbol,event_date,knowledge_date,close_value,series,traded_qty);
                INSERT INTO base VALUES(1,'A','2024-01-01','2024-01-01',100,'EQ',1000);
                INSERT INTO base VALUES(2,'A','2024-01-02','2024-01-02',90,'EQ',1000);
                INSERT INTO base VALUES(3,'A','2024-01-03','2024-01-01',999,'EQ',1000);
                CREATE VIEW bhavcopy AS SELECT *,CASE WHEN event_date>'2024-01-02'
                    THEN forbidden() ELSE close_value END close_price FROM base;
                CREATE TABLE corporate_actions(row_id,symbol,action_type,event_date,knowledge_date,ratio_numerator,ratio_denominator);
            """)
            rows = list(S.stream_context(c, {"2024-01-02": [{"symbol": "A"}]},
                                         [("2023-12-29", {"A": "INE1"})]))
            self.assertAlmostEqual(rows[0][2]["market"], -.1)

    def test_explained_reverses_material_and_waives_unclear(self):
        inputs = dict(peer_status="KNOWN", eligible=True)
        gates = dict(g3=False, g5="PASS", asm=False)
        flags = [False]*9
        flags[1:3] = [True, True]
        self.assertEqual(S.reasons(flags, inputs, gates, "PASS", "2024-01-05", "2024-01-08", "explained"), [])
        got = S.reasons(flags, inputs, gates, "UNKNOWN", "2024-01-05", "2024-01-06", "unexplained")
        self.assertEqual(set(got), {"material", "unclear", "limit_g5_unknown", "next_session_weekend"})

    def test_one_second_late_filing(self):
        day = "2024-01-02"
        row = dict(seq_id="1", category="X", description="", knowledge_date=day,
                   sort_timestamp=day+" 18:00:01")
        flags, *_ = S.A.steps_for([row], day, datetime.fromisoformat(day+"T18:00:00"),
            ["2024-01-01", day, "2024-01-03"], {"X": "Material news"},
            dict(market=0, peer_status="KNOWN", peer_share=0, previous_close=100),
            dict(g3=False, g5="PASS"), [], [], 5)
        self.assertFalse(flags[1])

    def test_terciles_only_development_and_overlap_not_position_filter(self):
        rows = []
        for day, z, exit_day in [("2024-01-01", 1, "2024-01-04"), ("2024-01-02", 3, "2024-01-05"),
                                 ("2025-01-02", 999, "2025-01-07")]:
            rows.append(dict(day=day, symbol="A", zscore_60d=z, turnover_band=1,
                exclusions={"unexplained": [], "explained": ["no_material"]},
                scheduled_exits={"1": exit_day, "3": exit_day}))
        out = S.summarize(rows)
        self.assertAlmostEqual(out["tercile_boundaries"][0], 1+2/3)
        cell = next(c for c in out["cells"] if c["year"] == 2024 and c["group"] == "unexplained" and c["horizon"] == 1)
        self.assertEqual((cell["inputs_eligible"], cell["scheduled_overlap_count"]), (2, 1))

    def test_metadata_is_not_publication_proof(self):
        result = timing_audit(["=== 2024-01-01T18:00:00+05:30 weekly_ingest step=bhavcopy_today "
                               "status=OK completed=2024-01-01T18:01:00+05:30 ==="], ["2024-01-01"])
        self.assertEqual(result["availability_unknown"], 1)
        self.assertEqual(result["study_dates_with_step_metadata"], 1)
