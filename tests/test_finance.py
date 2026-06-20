import pandas as pd
import pytest

from core.tFinance import calculate_macd, get_price_status, process_price_status


def test_calculate_macd():
    # Create a simple upward series
    prices = pd.Series([10.0 + i for i in range(50)])
    macd_line, macd_hist = calculate_macd(prices, fast=12, slow=26, signal=9)
    assert len(macd_line) == 50
    assert len(macd_hist) == 50
    assert not macd_line.isna().all()


def test_get_price_status_insufficient_data():
    # If history is less than MA_LONG_WINDOW (200), it should be handled gracefully as "데이터부족"
    prices = pd.Series([100.0] * 50)
    rst = get_price_status("TEST", prices)
    assert rst is not None
    assert rst['status'] == "데이터부족"
    assert rst['sigma'] == 0.0


def test_get_price_status_flat_price():
    # 250 elements of identical prices (std is 0.0) -> division by zero safeguard
    prices = pd.Series([100.0] * 250)
    rst = get_price_status("TEST", prices)
    assert rst is not None
    assert rst['status'] == "중립"
    assert rst['sigma'] == 0.0


def test_get_price_status_sufficient_data():
    # 250 elements of constant price, then rising
    prices = pd.Series([100.0] * 249 + [120.0])
    rst = get_price_status("TEST", prices)
    assert rst is not None
    assert rst['status'] in ["상향 돌파", "중립", "상향 지속(3.5)", "상향 지속(2.5)"] or "상향" in rst['status']


def test_process_price_status(capsys):
    # 1. Normal flow
    prices1 = pd.Series([100.0] * 250)
    prices2 = pd.Series([100.0] * 50)
    tickers = ["TEST1", "TEST2"]
    data = [prices1, prices2]
    
    results = process_price_status(tickers, data)
    assert len(results) == 2
    assert results[0]['ticker'] == "TEST1"
    assert results[1]['ticker'] == "TEST2"

    # 2. Length mismatch
    with pytest.raises(ValueError, match="길이가 다릅니다"):
        process_price_status(["TEST1"], [prices1, prices2])

    # 3. Processing error handling (e.g. invalid history structure)
    bad_df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
    results2 = process_price_status(["TEST_BAD"], [bad_df])
    assert len(results2) == 0
    captured = capsys.readouterr()
    assert "Error processing status for TEST_BAD" in captured.out


def test_calculate_win_rate_and_ratio():
    from core.tFinance import calculate_win_rate, calculate_win_loss_ratio
    
    # 250 rows of alternating returns
    prices = pd.DataFrame({
        'A': [100.0 * (1.01 ** i) for i in range(250)], # positive returns only (Win rate should be 1.0)
        'B': [100.0 if i % 2 == 0 else 99.0 for i in range(250)] # alternating (Gain = 1.01%, Loss = 1.0%)
    })
    
    win_rates = calculate_win_rate(prices, lookback=240)
    ratios = calculate_win_loss_ratio(prices, lookback=240)
    
    assert len(win_rates) == 2
    assert len(ratios) == 2
    assert win_rates['A'] == 1.0
    assert win_rates['B'] > 0.4
    assert ratios['A'] == 1.0  # fallback when no loss days

