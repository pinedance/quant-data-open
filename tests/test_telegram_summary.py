from unittest.mock import patch

from core.message import send_telegram_dashboard_summary


@patch('core.message.send_telegram_message')
def test_telegram_dashboard_summary(mock_send):
    mock_data = {
        "market_regime": {"tip_momentum": 1.2, "status": "Bullish"},
        "trend_breakouts": {"up_breakouts": [], "down_breakouts": []},
        "monthly_momentum": [],
        "valuation_extremes": []
    }
    send_telegram_dashboard_summary(mock_data)
    assert mock_send.called
