import unittest
import numpy as np
import empyrical

# A small standalone module to test the logic of max drawdown computation
def manual_max_drawdown(returns):
    n = len(returns)
    if n == 0:
        return 0.0
    cum_ret = np.cumprod(1 + np.array(returns))
    # prepend 1.0 to cumulative returns
    cum_ret = np.insert(cum_ret, 0, 1.0)
    running_max = np.maximum.accumulate(cum_ret)
    drawdowns = (cum_ret - running_max) / running_max
    return np.min(drawdowns) if len(drawdowns) > 0 else 0.0

class TestEvaluateMetrics(unittest.TestCase):
    def test_max_drawdown_matches_empyrical(self):
        cases = [
            [0.05, -0.10, 0.20, -0.05, 0.02],
            [0.10, 0.10, 0.10],
            [-0.10, -0.10, -0.10],
            [0.0, 0.0, 0.0],
            [0.5, -0.5, 0.5, -0.5],
            []
        ]
        for returns in cases:
            with self.subTest(returns=returns):
                arr = np.array(returns)
                expected = empyrical.max_drawdown(arr) if len(arr) > 0 else 0.0
                if np.isnan(expected):
                    expected = 0.0
                actual = manual_max_drawdown(returns)
                self.assertAlmostEqual(actual, expected, places=5)
