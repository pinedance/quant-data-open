from unittest.mock import patch

from core.message import send_telegram_dashboard_summary


@patch('core.message.send_telegram_message')
def test_telegram_dashboard_summary(mock_send):
    mock_data = {
        "base_dates": {"US": "2026-09-23", "KR": "2026-09-23"},
        "market_regime": {"tip_momentum": 1.2, "status": "Bullish"},
        "trend_breakouts": {"up_breakouts": [], "down_breakouts": []},
        "monthly_momentum": [],
        "valuation_extremes": []
    }
    send_telegram_dashboard_summary(mock_data)
    assert mock_send.called
    sent_msg = mock_send.call_args[0][0]
    assert "📅 <b>Base Date</b>\n  •US: 2026-09-23\n  •KR: 2026-09-23" in sent_msg


@patch('core.message.send_telegram_message')
def test_telegram_dashboard_summary_fallback_base_dates(mock_send):
    mock_data = {
        "market_regime": {"tip_momentum": 1.2, "status": "Bullish"},
        "trend_breakouts": {"up_breakouts": [], "down_breakouts": []},
        "monthly_momentum": [],
        "valuation_extremes": []
    }
    send_telegram_dashboard_summary(mock_data)
    assert mock_send.called
    sent_msg = mock_send.call_args[0][0]
    assert "📅 <b>Base Date</b>\n  •US: N/A\n  •KR: N/A" in sent_msg
