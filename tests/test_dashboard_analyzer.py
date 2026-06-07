import numpy as np
import pandas as pd
import pytest

from build import check_nans_for_dashboard
from core.dashboard_analyzer import (
    calculate_average_momentum,
    calculate_ema_crossovers,
    calculate_macd_z,
    calculate_t_sigma,
)


def make_trending_up_series(n=250, daily_return=0.001):
    """Simulate a steadily rising asset (like XLK in a bull run)."""
    prices = [100.0]
    for _ in range(n - 1):
        prices.append(prices[-1] * (1 + daily_return))
    return pd.Series(prices)


def test_t_sigma_trending_up_is_positive():
    """
    A steadily rising asset near its recent high should have positive t_sigma.
    (Regression: old code returned negative because it used the last daily return,
    which is ~0 for a smooth trend, not the price level.)
    """
    series = make_trending_up_series(n=250, daily_return=0.001)
    real_z, raw_z, df_fit, loc_fit, scale_fit = calculate_t_sigma(series)
    assert real_z > 0, f"Expected positive t_sigma for trending-up asset, got {real_z}"
    assert raw_z > 0, f"Expected positive raw_z for trending-up asset, got {raw_z}"


def test_t_sigma_trending_down_is_negative():
    """A falling asset near its recent low should have negative t_sigma."""
    series = make_trending_up_series(n=250, daily_return=-0.001)
    real_z, raw_z, df_fit, loc_fit, scale_fit = calculate_t_sigma(series)
    assert real_z < 0, f"Expected negative t_sigma for falling asset, got {real_z}"


def test_t_sigma_short_series_returns_zeros():
    """Series shorter than window+2 should return all zeros."""
    series = pd.Series([100.0] * 10)
    result = calculate_t_sigma(series)
    assert result == (0.0, 0.0, 0.0, 0.0, 0.0)


def test_t_sigma_returns_five_floats():
    series = make_trending_up_series(n=250)
    result = calculate_t_sigma(series)
    assert len(result) == 5
    assert all(isinstance(v, float) for v in result)

def test_average_momentum_calculation():
    # 13 month EOM prices (last index represents current date in June, e.g. June 5th)
    prices = [100.0] * 13
    prices[-1] = 110.0  # current (June 5)
    prices[-2] = 105.0  # May EOM
    prices[-4] = 100.0  # March EOM
    prices[-7] = 95.0   # Dec EOM
    prices[-13] = 90.0  # June EOM (prev year)
    
    # expected returns: (110/105 - 1), (110/100 - 1), (110/95 - 1), (110/90 - 1)
    ret_1m = 110.0/105.0 - 1
    ret_3m = 110.0/100.0 - 1
    ret_6m = 110.0/95.0 - 1
    ret_12m = 110.0/90.0 - 1
    expected_avg = (ret_1m + ret_3m + ret_6m + ret_12m) / 4
    
    idx = pd.date_range(end='2026-06-05', periods=13, freq='ME')
    # make last index June 5th
    idx_list = list(idx)
    idx_list[-1] = pd.Timestamp('2026-06-05')
    
    df_prices = pd.Series(prices, index=idx_list)
    avg_mom = calculate_average_momentum(df_prices)
    assert np.isclose(avg_mom, expected_avg)

def test_ema_crossovers():
    # Price series where EMA005 crosses above EMA200
    prices = [100.0] * 300
    # Make price shoot up at the end
    prices[-1] = 200.0
    
    price_series = pd.Series(prices)
    status, ema5, ema200 = calculate_ema_crossovers(price_series)
    assert status == "상향 돌파"


# Append to tests/test_dashboard_analyzer.py


def make_mock_daily_prices(length=250, volatility=0.01):
    prices = [100.0]
    np.random.seed(42)
    daily_returns = np.random.normal(0, volatility, length)
    for i in range(1, length):
        prices.append(prices[-1] * (1 + daily_returns[i]))
    return pd.Series(prices)

def test_macd_z_above_mean_is_positive():
    series = pd.Series([1.0] * 12 + [3.0])
    daily_prices = make_mock_daily_prices(250)
    z = calculate_macd_z(series, daily_prices)
    assert z > 0, f"Expected positive macd_z, got {z}"

def test_macd_z_below_mean_is_negative():
    series = pd.Series([2.0] * 12 + [-1.0])
    daily_prices = make_mock_daily_prices(250)
    z = calculate_macd_z(series, daily_prices)
    assert z < 0, f"Expected negative macd_z, got {z}"

def test_macd_z_raises_value_error_on_missing_daily_prices():
    series = pd.Series([1.0] * 13)
    with pytest.raises(ValueError, match="daily_prices is completely missing"):
        calculate_macd_z(series, None)

def test_macd_z_raises_value_error_on_short_daily_prices():
    series = pd.Series([1.0] * 13)
    daily_prices = make_mock_daily_prices(100)
    with pytest.raises(ValueError, match="must contain at least 200 data points"):
        calculate_macd_z(series, daily_prices)

def test_macd_z_raises_value_error_on_empty_hist_series():
    series = pd.Series([], dtype=float)
    daily_prices = make_mock_daily_prices(250)
    with pytest.raises(ValueError, match="hist_series must not be empty"):
        calculate_macd_z(series, daily_prices)

def test_macd_z_is_float():
    series = pd.Series([float(i) for i in range(14)])
    daily_prices = make_mock_daily_prices(250)
    assert isinstance(calculate_macd_z(series, daily_prices), float)

def test_check_nans_for_dashboard():
    dates = pd.date_range("2026-06-01", periods=5)
    df = pd.DataFrame({
        "AAPL": [100.0, np.nan, np.nan, 103.0, 104.0],
        "MSFT": [200.0, 201.0, 202.0, 203.0, 204.0]
    }, index=dates)
    
    names_dict = {"AAPL": "Apple Inc.", "MSFT": "Microsoft Corp."}
    nan_info = check_nans_for_dashboard(df, "US", names_dict)
    assert len(nan_info) == 1
    assert nan_info[0]["column"] == "AAPL"
    assert nan_info[0]["ticker"] == "AAPL"
    assert nan_info[0]["name"] == "Apple Inc."
    assert nan_info[0]["region"] == "US"
    assert nan_info[0]["count"] == 2
    assert nan_info[0]["range"] == "2026-06-02 ~ 2026-06-03"



