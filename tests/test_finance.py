import pandas as pd
import numpy as np
from core.tFinance import get_price_status, calculate_macd

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
