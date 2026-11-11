import pandas as pd

from core.dashboard_analyzer import DashboardAnalyzer
from core.tFinance import (
    calculate_average_momentum,
    calculate_ema_crossovers,
    calculate_macd_z,
)


def test_average_momentum_vector():
    # 2D DataFrame (13 months EOM)
    prices = pd.DataFrame({
        'A': [100.0] * 12 + [110.0],
        'B': [100.0] * 12 + [90.0]
    })
    result = calculate_average_momentum(prices)
    assert isinstance(result, pd.Series)
    assert result['A'] > 0
    assert result['B'] < 0

def test_ema_crossovers_vector():
    prices = pd.DataFrame({
        'A': [100.0] * 199 + [200.0], # Up breakout
        'B': [100.0] * 200 # Neutral / down keep
    })
    ema5, ema200, up_break, down_break, up_keep = calculate_ema_crossovers(prices)
    assert up_break['A'] == True
    assert up_break['B'] == False

def test_macd_z_vector():
    hist = pd.DataFrame({'A': [1.0], 'B': [-1.0]})
    prices = pd.DataFrame({
        'A': [100.0] * 200,
        'B': [100.0] * 200
    })
    # Add minor price moves to prevent std dev being exactly 0
    prices.iloc[-1] = [101.0, 99.0]
    z = calculate_macd_z(hist, prices)
    assert isinstance(z, pd.Series)
    assert z['A'] > 0
    assert z['B'] < 0

def test_analyzer_constructor():
    df_d = pd.DataFrame({'A': [100.0] * 200})
    df_m = pd.DataFrame({'A': [100.0] * 13})
    df_hist = pd.DataFrame({'A': [1.0]})
    analyzer = DashboardAnalyzer(
        names_dict={'A': 'Test Asset'},
        df_us_d=df_d, df_us_m=df_m, df_us_hist=df_hist,
        df_kr_d=df_d, df_kr_m=df_m, df_kr_hist=df_hist
    )
    assert analyzer.names_dict['A'] == 'Test Asset'


def test_calculate_rsi():
    from core.tFinance import calculate_rsi
    prices = pd.Series([100.0 + i for i in range(20)])
    rsi = calculate_rsi(prices, period=14)
    assert isinstance(rsi, pd.Series)
    assert len(rsi) == 20
    assert rsi.iloc[-1] > 80.0


def test_nan_mid_series_propagates():
    import numpy as np
    from core.tFinance import calculate_daily_average_momentum

    idx = pd.date_range("2024-01-01", "2025-06-30", freq="D")
    df = pd.DataFrame({"TIP": np.linspace(100.0, 120.0, len(idx))}, index=idx)

    nan_date = pd.Timestamp("2025-03-15")
    df.loc[nan_date, "TIP"] = np.nan

    res = calculate_daily_average_momentum(df)
    assert np.isnan(res.loc[nan_date, "TIP"])
    assert np.isnan(res.loc[pd.Timestamp("2025-04-15"), "TIP"])
    assert np.isnan(res.loc[pd.Timestamp("2025-06-15"), "TIP"])
    assert pd.notna(res.loc[pd.Timestamp("2025-04-16"), "TIP"])


def test_daily_average_momentum_holiday_fallback():
    import numpy as np
    from core.tFinance import calculate_daily_average_momentum

    idx = pd.date_range("2024-01-01", "2025-11-05", freq="D")
    # Remove Oct 1 and Oct 2, 2025 to simulate market holidays
    idx = idx.difference(pd.to_datetime(["2025-10-01", "2025-10-02"]))
    prices = pd.Series(100.0, index=idx, name="TIP")
    prices.loc[pd.Timestamp("2025-09-30")] = 80.0
    prices.loc[pd.Timestamp("2025-10-03")] = 120.0
    prices.loc[pd.Timestamp("2025-11-02")] = 100.0

    res = calculate_daily_average_momentum(prices)
    # On 2025-11-02: 1M ago (2025-10-02) is holiday -> falls back to 2025-09-30 (80.0)
    # 3M, 6M, 12M ago are all 100.0 -> r1 = 100/80 - 1 = 0.25, r3=r6=r12=0 -> avg = 0.0625
    assert np.isclose(res.loc[pd.Timestamp("2025-11-02")], 0.0625)


def test_daily_average_momentum_matches_resample_current():
    import numpy as np
    from core.tFinance import calculate_average_momentum, calculate_daily_average_momentum
    from core.tTable import resample_monthly

    idx = pd.date_range("2024-01-01", "2025-09-25", freq="B")
    df = pd.DataFrame({"TIP": np.linspace(100.0, 115.0, len(idx))}, index=idx)

    daily_mom = calculate_daily_average_momentum(df)
    monthly_df = resample_monthly(df, method="current")
    expected_last = calculate_average_momentum(monthly_df).iloc[0]

    assert np.isclose(daily_mom["TIP"].iloc[-1], expected_last)


def test_calculate_daily_momentums_dict_and_13612m():
    import numpy as np
    from core.tFinance import MOMENTUM_KEYS, calculate_daily_momentums

    idx = pd.date_range("2024-01-01", "2025-06-30", freq="D")
    df = pd.DataFrame({"TIP": np.linspace(100.0, 120.0, len(idx))}, index=idx)

    moms = calculate_daily_momentums(df)
    assert tuple(moms.keys()) == MOMENTUM_KEYS
    expected_13612m = (moms["1M"] + moms["3M"] + moms["6M"] + moms["12M"]) / 4.0
    assert np.allclose(moms["13612M"].to_numpy(), expected_13612m.to_numpy(), equal_nan=True)




