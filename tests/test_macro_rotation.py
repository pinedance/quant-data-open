import unittest
import numpy as np
import pandas as pd
from core.tFinance import calculate_bollinger_percent_b, calculate_rolling_percentile_rank

class TestMacroRotation(unittest.TestCase):
    def test_calculate_bollinger_percent_b(self):
        series = pd.Series([10.0, 10.0, 10.0, 10.0, 10.0, 20.0, 20.0])
        res = calculate_bollinger_percent_b(series, window=5, num_std=2)
        self.assertTrue(isinstance(res, (pd.Series, pd.DataFrame)))
        self.assertFalse(res.empty)

    def test_calculate_rolling_percentile_rank(self):
        series = pd.Series(list(range(20)))
        res = calculate_rolling_percentile_rank(series, window=12)
        self.assertTrue(isinstance(res, (pd.Series, pd.DataFrame)))
        self.assertAlmostEqual(res.iloc[-1], 1.0, places=4)

if __name__ == '__main__':
    unittest.main()
