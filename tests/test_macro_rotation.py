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

    def test_dashboard_analyzer_macro_rotation(self):
        from core.dashboard_analyzer import DashboardAnalyzer
        dates = pd.date_range("2020-01-01", periods=25, freq="M")
        df_us_m = pd.DataFrame({
            "SPY": np.linspace(100, 200, 25),
            "QQQ": np.linspace(200, 300, 25)
        }, index=dates)
        df_us_d = pd.DataFrame({"SPY": np.linspace(100, 200, 250), "QQQ": np.linspace(200, 300, 250)}, index=pd.date_range("2020-01-01", periods=250))
        df_us_hist = df_us_d.copy()
        
        analyzer = DashboardAnalyzer(
            names_dict={"SPY": "S&P 500", "QQQ": "Nasdaq 100"},
            df_us_d=df_us_d, df_us_m=df_us_m, df_us_hist=df_us_hist,
            df_kr_d=df_us_d, df_kr_m=df_us_m, df_kr_hist=df_us_hist
        )
        data = analyzer.analyze()
        self.assertIn("macro_rotation", data)
        self.assertGreater(len(data["macro_rotation"]), 0)
        entry = data["macro_rotation"][0]
        self.assertIn("x", entry)
        self.assertIn("y", entry)
        self.assertIn("prev_x", entry)
        self.assertIn("prev_y", entry)

if __name__ == '__main__':
    unittest.main()

