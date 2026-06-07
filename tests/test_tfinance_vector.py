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

