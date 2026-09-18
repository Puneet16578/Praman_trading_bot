"""Guard re-test against REAL ingested data: the event catalogue's vectorized adjustment path
(event_catalogue.py's module docstring explains the algebra) is cross-checked here directly
against actually calling compute_adjustment_factor()/adjusted_close() -- proving the equivalence
empirically on real rows, not just reasoning about it on paper.

Skipped entirely (not faked, not fixture-substituted) if the real store doesn't exist.
"""
from __future__ import annotations
import random
import unittest
from pathlib import Path

from src.bitemporal.connection import get_connection
from src.bitemporal.guard import latest_as_of
from src.config.settings import get_settings
from src.signals.event_catalogue import (
    TRAILING_WINDOW, build_symbol_history, compute_daily_stats, _return,
)
from src.signals.price_adjustment import UnadjustableWindowError, adjusted_close, compute_adjustment_factor

_settings = get_settings()
_DB_EXISTS = Path(_settings.database_path).exists()

@unittest.skipUnless(_DB_EXISTS, f"Real ingested DB not found at {_settings.database_path}.")
class VectorizedAdjustmentMatchesRealFunctionTest(unittest.TestCase):
    """Samples real symbols that actually have BONUS/SPLIT corporate actions, and confirms the
    event catalogue's vectorized return computation agrees EXACTLY with independently calling the
    real, already-trusted compute_adjustment_factor()/adjusted_close() for the same (symbol,
    price_date, as_of)."""

    def setUp(self):
        self.conn = get_connection(_settings.database_path)

    def tearDown(self):
        self.conn.close()

    def test_bajfinance_hand_verified_fixture_matches_both_paths(self):
        """The permanent hand-verified real fixture (docs/phase3_corporate_actions.md): BAJFINANCE's
        2025 bonus (4:1) + split (2:1) on the same ex-date, combined factor 10."""
        hist = build_symbol_history(self.conn, "BAJFINANCE")
        # Pick a real date strictly before the action and one on/after it, from real trading days.
        actions = latest_as_of(self.conn, "corporate_actions", "2099-01-01", symbol="BAJFINANCE")
        bonus_or_split = [a for a in actions if a["action_type"] in ("BONUS", "SPLIT")]
        self.assertTrue(bonus_or_split, "BAJFINANCE must have real BONUS/SPLIT rows in the store.")
        ex_date = bonus_or_split[0]["event_date"]
        before_days = [d for d in hist.trading_days if d < ex_date]
        after_days = [d for d in hist.trading_days if d >= ex_date]
        if not before_days or not after_days:
            self.skipTest("Not enough real trading days around BAJFINANCE's real ex-date in this store.")
        d1, d2 = before_days[-1], after_days[0]

        vectorized = _return(hist, d1, d2, as_of=d2)
        real_adj1 = adjusted_close(self.conn, "BAJFINANCE", d1, as_of=d2)
        real_adj2 = adjusted_close(self.conn, "BAJFINANCE", d2, as_of=d2)
        real_return = real_adj2 / real_adj1 - 1.0
        self.assertAlmostEqual(vectorized, real_return, places=9)

    def test_sampled_real_symbols_with_actions_match_exactly(self):
        """Broader sample: every real symbol with at least one real BONUS/SPLIT action, checked at
        a real (d1, d2=as_of) pair straddling that action, vectorized vs. the real function."""
        all_actions = latest_as_of(self.conn, "corporate_actions", "2099-01-01")
        adjustable = [a for a in all_actions if a["action_type"] in ("BONUS", "SPLIT")]
        symbols = sorted({a["symbol"] for a in adjustable})
        random.Random(42).shuffle(symbols)
        checked = 0
        for symbol in symbols:
            if checked >= 15:
                break
            hist = build_symbol_history(self.conn, symbol)
            if len(hist.trading_days) < 3:
                continue
            symbol_actions = [a for a in adjustable if a["symbol"] == symbol]
            for action in symbol_actions:
                ex_date = action["event_date"]
                before_days = [d for d in hist.trading_days if d < ex_date]
                after_days = [d for d in hist.trading_days if d >= ex_date]
                if not before_days or not after_days:
                    continue
                d1, d2 = before_days[-1], after_days[0]
                try:
                    real_adj1 = adjusted_close(self.conn, symbol, d1, as_of=d2)
                    real_adj2 = adjusted_close(self.conn, symbol, d2, as_of=d2)
                except UnadjustableWindowError:
                    continue  # a demerger also falls in this window -- both paths must agree it's excluded
                except ValueError:
                    continue  # no bhavcopy row visible for one endpoint -- not what this test checks
                real_return = real_adj2 / real_adj1 - 1.0
                vectorized = _return(hist, d1, d2, as_of=d2)
                self.assertIsNotNone(vectorized, f"{symbol}: real function computed a return but vectorized path excluded the window.")
                self.assertAlmostEqual(vectorized, real_return, places=9,
                                        msg=f"{symbol} {d1}->{d2}: vectorized {vectorized} != real {real_return}")
                checked += 1
                break  # one verified window per symbol is enough to move to the next
        self.assertGreater(checked, 0, "Must have checked at least one real symbol/action pair.")
        print(f"\n  [real-data guard] cross-checked {checked} real (symbol, action-window) pairs -- all matched exactly.")

    def test_demerger_window_both_paths_agree_it_is_excluded(self):
        """A real demerger: the real compute_adjustment_factor() raises UnadjustableWindowError;
        the vectorized _return() must return None for the identical window, not silently adjust it."""
        all_actions = latest_as_of(self.conn, "corporate_actions", "2099-01-01")
        demergers = [a for a in all_actions if a["action_type"] == "DEMERGER"]
        self.assertTrue(demergers, "Must have real DEMERGER_EXCLUSION rows in the store (Phase 3).")
        checked = 0
        for action in demergers:
            symbol, ex_date = action["symbol"], action["event_date"]
            hist = build_symbol_history(self.conn, symbol)
            before_days = [d for d in hist.trading_days if d < ex_date]
            after_days = [d for d in hist.trading_days if d >= ex_date]
            if not before_days or not after_days:
                continue
            d1, d2 = before_days[-1], after_days[0]
            with self.assertRaises(UnadjustableWindowError):
                compute_adjustment_factor(self.conn, symbol, d1, as_of=d2)
            vectorized = _return(hist, d1, d2, as_of=d2)
            self.assertIsNone(vectorized, f"{symbol}: real function raised UnadjustableWindowError but vectorized path did not exclude the window.")
            checked += 1
            if checked >= 5:
                break
        self.assertGreater(checked, 0, "Must have checked at least one real demerger window.")

if __name__ == "__main__":
    unittest.main()
