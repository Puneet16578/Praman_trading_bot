"""Install the durable-store filesystem guard before any discovered tests run."""
import os
import tempfile
import unittest
import sqlite3
from unittest.mock import patch
from pathlib import Path
from shared.store_safety import check_operation, install_guard, protect_connection

install_guard()


class StoreSafetyTest(unittest.TestCase):
    def test_protected_connection_denies_clear_update_and_drop(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'store.sqlite'
            conn = sqlite3.connect(path)
            try:
                conn.execute('CREATE TABLE facts (value TEXT)')
                conn.execute("INSERT INTO facts VALUES ('preserved')")
                with patch('shared.store_safety.PROTECTED', (path.resolve(),)):
                    protect_connection(conn, path)
                for sql in ('DELETE FROM facts', "UPDATE facts SET value='changed'", 'DROP TABLE facts'):
                    with self.assertRaises(sqlite3.DatabaseError):
                        conn.execute(sql)
                self.assertEqual(conn.execute('SELECT * FROM facts').fetchall(), [('preserved',)])
                conn.execute("INSERT INTO facts VALUES ('append')")
            finally:
                conn.close()

    def test_destructive_operations_refused_for_store_and_parent(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'durable.sqlite'
            path.write_bytes(b'preserved')
            for event, args in (
                ('os.remove', (path, -1)),
                ('os.rmdir', (path.parent, -1)),
                ('os.rename', (path, path.with_suffix('.old'), -1, -1)),
                ('os.rename', (path.with_suffix('.new'), path, -1, -1)),
                ('open', (path, 'w', os.O_TRUNC)),
            ):
                with self.subTest(event=event, args=args):
                    with self.assertRaises(PermissionError):
                        check_operation(event, args, (path,))
            check_operation('open', (path, 'r', os.O_RDONLY), (path,))
            check_operation('os.remove', (path.with_suffix('.copy'), -1), (path,))
            self.assertEqual(path.read_bytes(), b'preserved')
