"""P8-063: display freshness is independent of the registered Strategy 0 threshold."""
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from desk.ingestion_health import ingestion_health_line, STALE_AFTER_DAYS
from shared.market_time import IST


class DisplayStalenessTest(unittest.TestCase):
    def line(self, today, finish, start=None, current=None):
        start = start or finish
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ingest.log'
            text = f'=== {start} weekly_ingest (finished {finish}) overall=OK steps: sample=OK ===\n  GAPs: 0\n'
            if current:
                text += f'=== {current} weekly_ingest started ===\n'
            path.write_text(text, encoding='utf-8')
            with patch('desk.ingestion_health.LOG_PATH', path), patch('desk.ingestion_health.datetime') as clock:
                clock.now.return_value = datetime.fromisoformat(today).replace(tzinfo=IST)
                return ingestion_health_line(current)

    def test_previous_weekday_is_fresh_and_older_is_stale(self):
        self.assertNotIn('STALE', self.line('2026-10-13T18:00:00', '2026-10-12T22:00:00+05:30'))
        self.assertIn('STALE', self.line('2026-10-13T18:00:00', '2026-10-09T22:00:00+05:30'))
        self.assertEqual(STALE_AFTER_DAYS, 7)

    def test_weekend_and_monday_accept_friday_but_not_thursday(self):
        for today in ('2026-10-10T09:00:00', '2026-10-11T18:00:00', '2026-10-12T18:00:00'):
            with self.subTest(today=today):
                self.assertNotIn('STALE', self.line(today, '2026-10-09T22:00:00+05:30'))
                self.assertIn('STALE', self.line(today, '2026-10-08T22:00:00+05:30'))

    def test_finish_time_and_ist_date_determine_age(self):
        self.assertNotIn('STALE', self.line('2026-10-13T08:00:00',
                         '2026-10-11T23:50:00+00:00', start='2026-10-09T18:00:00+05:30'))

    def test_current_brief_does_not_make_previous_run_fresh(self):
        line = self.line('2026-10-13T18:30:00', '2026-10-09T22:00:00+05:30',
                         current='2026-10-13T18:00:00+05:30')
        self.assertIn('in progress', line)
        self.assertIn('Previous finished run', line)
        self.assertIn('STALE', line)
