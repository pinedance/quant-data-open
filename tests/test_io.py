import pytest
import pandas as pd
from unittest.mock import patch
from core.tIO import fetch_tickers, fetch_prices, download_with_retry

def test_fetch_tickers_raises_runtime_error_on_empty():
    with patch("pandas.read_csv", side_effect=Exception("Simulated network/file error")):
        with pytest.raises(RuntimeError) as excinfo:
            fetch_tickers("https://example.com/invalid_empty.csv")
        assert "티커 목록 로드 실패" in str(excinfo.value)

def test_fetch_tickers_success():
    with patch("pandas.read_csv") as mock_read_csv:
        mock_df = pd.DataFrame({"TICKER": ["AAPL", "MSFT", "AAPL"]})
        mock_read_csv.return_value = mock_df
        tickers = fetch_tickers("https://example.com/tickers.csv")
        assert tickers == ["AAPL", "MSFT"]

def test_fetch_prices_success():
    tickers = ["AAPL", "MSFT"]
    start_date = "2026-01-01"
    old_data = pd.DataFrame()
    
    with patch("core.tIO.get_ticker_data") as mock_get_data:
        idx = pd.date_range("2026-01-01", "2026-01-05")
        mock_get_data.side_effect = [
            pd.Series([100, 101, 102, 103, 104], index=idx, name="AAPL"),
            pd.Series([200, 201, 202, 203, 204], index=idx, name="MSFT")
        ]
        
        df, warning_msg = fetch_prices(tickers, start_date, old_data)
        
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["AAPL", "MSFT"]
        assert warning_msg is None

def test_fetch_prices_warning():
    tickers = ["AAPL", "MSFT", "GOOG"]
    start_date = "2026-01-01"
    old_data = pd.DataFrame()
    
    with patch("core.tIO.get_ticker_data") as mock_get_data:
        idx = pd.date_range("2026-01-01", "2026-01-05")
        mock_get_data.side_effect = [
            pd.Series([100, 101, 102, 103, 104], index=idx, name="AAPL"),
            Exception("Download failed"),
            Exception("Download failed")
        ]
        
        with patch("core.tIO.select_column_by_name", return_value=pd.Series(dtype=float)):
            df, warning_msg = fetch_prices(tickers, start_date, old_data)
            
            assert isinstance(df, pd.DataFrame)
            assert list(df.columns) == ["AAPL"]
            assert warning_msg is not None
            assert "신규 다운로드 성공률 낮음" in warning_msg

def test_download_with_retry_raises_exception_on_failure():
    with patch("core.tIO.yf.Ticker") as mock_ticker:
        mock_ticker.return_value.history.side_effect = Exception("API error")
        with pytest.raises(Exception) as excinfo:
            download_with_retry("INVALID", max_retries=2, delay=0.01)
        assert "다운로드 실패" in str(excinfo.value)

