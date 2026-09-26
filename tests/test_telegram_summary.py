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
    assert "<b>📊 [Quant Data] Dashboard Summary</b>" in sent_msg
    assert ' 🇺🇸 2026-09-23 | <a href="https://pinedance.github.io/quant-data-open/dist/US/dashboard.html">Dashboard</a>' in sent_msg
    assert ' 🇰🇷 2026-09-23 | <a href="https://pinedance.github.io/quant-data-open/dist/KR/dashboard.html">Dashboard</a>' in sent_msg
    assert "🌤️ <b>Market Regime</b>\n •TIP Mom: +1.2%" in sent_msg


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
    assert ' 🇺🇸 N/A | <a href="https://pinedance.github.io/quant-data-open/dist/US/dashboard.html">Dashboard</a>' in sent_msg
    assert ' 🇰🇷 N/A | <a href="https://pinedance.github.io/quant-data-open/dist/KR/dashboard.html">Dashboard</a>' in sent_msg


@patch('core.message.send_telegram_message')
def test_telegram_dashboard_summary_with_data_quality_status(mock_send):
    mock_data = {
        "base_dates": {"US": "2026-09-23", "KR": "2026-09-23"},
        "market_regime": {"tip_momentum": 1.2, "status": "Bullish"},
        "trend_breakouts": {"up_breakouts": [], "down_breakouts": []},
        "monthly_momentum": [],
        "valuation_extremes": [],
        "data_quality_status": [
            {"region": "US", "ticker": "SPY", "count": 2, "range": "2026-09-22 ~ 2026-09-23"},
            {"region": "US", "ticker": "QQQ", "count": 1, "range": "2026-09-23 ~ 2026-09-23"},
            {"region": "KR", "ticker": "005930", "count": 3, "range": "2026-09-21 ~ 2026-09-23"},
        ]
    }
    send_telegram_dashboard_summary(mock_data)
    assert mock_send.called
    sent_msg = mock_send.call_args[0][0]
    assert "⚠️ <b>NaN data</b>" in sent_msg
    assert " 🇺🇸 2 종목 (3일)" in sent_msg
    assert " 🇰🇷 1 종목 (3일)" in sent_msg


@patch('core.message.send_telegram_message')
def test_telegram_dashboard_summary_without_data_quality_status(mock_send):
    mock_data = {
        "base_dates": {"US": "2026-09-23", "KR": "2026-09-23"},
        "market_regime": {"tip_momentum": 1.2, "status": "Bullish"},
        "trend_breakouts": {"up_breakouts": [], "down_breakouts": []},
        "monthly_momentum": [],
        "valuation_extremes": [],
        "data_quality_status": []
    }
    send_telegram_dashboard_summary(mock_data)
    assert mock_send.called
    sent_msg = mock_send.call_args[0][0]
    assert "⚠️ <b>NaN data</b>" not in sent_msg


