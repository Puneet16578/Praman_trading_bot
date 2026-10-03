"""Exact SELECT memoization for an immutable, read-only research snapshot.

Keys include the entire SQL and parameter tuple (including every as-of cutoff).
The runner clears the cache between symbols. No production connection uses it.
"""
from collections import OrderedDict
from contextlib import contextmanager
import sys


class Rows:
    def __init__(self, rows):
        self.rows = iter(rows)

    def fetchone(self):
        return next(self.rows, None)

    def fetchall(self):
        return list(self.rows)

    def __iter__(self):
        return self.rows


class SnapshotQueries:
    def __init__(self, connection, limit=2048):
        self.connection = connection
        self.limit = limit
        self.cache = OrderedDict()

    def execute(self, sql, parameters=()):
        if not sql.lstrip().upper().startswith('SELECT '):
            raise ValueError('Research snapshot accepts SELECT only.')
        key = (sql, tuple(parameters))
        if key not in self.cache:
            self.cache[key] = tuple(self.connection.execute(sql, parameters).fetchall())
            if len(self.cache) > self.limit:
                self.cache.popitem(last=False)
        self.cache.move_to_end(key)
        return Rows(self.cache[key])


@contextmanager
def memoized_snapshot_histories(connection):
    """Reuse the exact pure history builder on one immutable snapshot.

    Existing consumers import the same function under local aliases. Replace only
    those aliases for this synchronous context, and always restore them. Histories
    contain all vintages; each later price lookup still applies its own cutoff.
    """
    from src.signals.event_catalogue import build_symbol_history
    cache = OrderedDict()
    def cached(conn, symbol, series='EQ', symbol_group=None, extend_with_series=()):
        if conn is not connection:
            return build_symbol_history(conn,symbol,series,symbol_group,extend_with_series)
        key = (symbol,series,tuple(symbol_group or ()),tuple(extend_with_series))
        if key not in cache:
            cache[key] = build_symbol_history(conn,symbol,series,symbol_group,extend_with_series)
            if len(cache)>12:
                cache.popitem(last=False)
        cache.move_to_end(key)
        return cache[key]
    aliases = []
    for module in list(sys.modules.values()):
        if module is not None and getattr(module,'build_symbol_history',None) is build_symbol_history:
            aliases.append(module)
            module.build_symbol_history = cached
    try:
        yield
    finally:
        for module in aliases:
            module.build_symbol_history = build_symbol_history
