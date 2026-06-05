import pandas as pd
import numpy as np
import scipy.stats as stats
from core.dashboard_analyzer import calculate_t_sigma, calculate_average_momentum, calculate_ema_crossovers

def test_t_sigma_calculation():
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 250)
    
    # Let's manually construct price series from returns
    prices = [100.0]
    for r in returns:
        prices.append(prices[-1] * np.exp(r))
    
    price_series = pd.Series(prices)
    
    # Calculate expected
    log_returns = np.log(price_series / price_series.shift(1)).dropna()
    base_returns = log_returns.iloc[-240:]
    df_fit, loc_fit, scale_fit = stats.t.fit(base_returns)
    current_return = log_returns.iloc[-1]
    t_score = (current_return - loc_fit) / scale_fit
    p_value = stats.t.cdf(t_score, df=df_fit)
    p_value = np.clip(p_value, 0.00001, 0.99999)
    expected_z = stats.norm.ppf(p_value)
    
    real_z, *_ = calculate_t_sigma(price_series)
    assert np.isclose(real_z, expected_z, atol=1e-4)

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
