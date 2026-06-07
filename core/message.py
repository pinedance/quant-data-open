import json
import math
import os

import requests
from dotenv import load_dotenv

load_dotenv()

from core.cons import MSG_SEPARATOR_WIDTH, SIGMA_THRESHOLD

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("Warning: TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 설정되지 않았습니다. Telegram 알림이 비활성화됩니다.")

def send_telegram_message(message, parse_mode=None, disable_link_preview=True):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    if parse_mode:
        params['parse_mode'] = parse_mode
    if disable_link_preview:
        params['link_preview_options'] = json.dumps({'is_disabled': True})
    
    print()
    print( "--- Send Message" )
    print( message )
    print( "--- --- ---")
    print()
    
    response = requests.post(url, params=params)
    return response.json()

def notice_price_status(data, tickers=None):
    if not data or not isinstance(data, dict):
        return

    try:
        status = data.get('status', '')
        sigma_max, sigma_min = SIGMA_THRESHOLD, -SIGMA_THRESHOLD
        sigma = data.get('sigma', 0)
        if (not status or "지속" in status) and (sigma_min < sigma < sigma_max):
            return

        ticker = data.get('ticker', 'Unknown')
        ma200 = data.get('ma200', 0)

        message = f"[{ticker}] {status}"

        if tickers and f"A{ticker}" in tickers:
            name = tickers[f"A{ticker}"]
            message += f"\n{name}"

        if (sigma > sigma_max) or (sigma < sigma_min):
            message += f"\nSIGMA: {sigma:.1f}"
        else:
            message += f"\nSMA200: {ma200:.2f}"

        send_telegram_message(message)
    except Exception as e:
        send_telegram_message(f"Error in notice_price_status for {data.get('ticker', 'Unknown')}: {str(e)}")


def notice_price_status_batch(status_results, tickers=None):
    sigma_max, sigma_min = SIGMA_THRESHOLD, -SIGMA_THRESHOLD
    up_breakouts = []
    down_breakouts = []
    sigma_highs = []
    sigma_lows = []

    for data in status_results:
        if not data or not isinstance(data, dict):
            continue

        status = data.get('status', '')
        sigma = data.get('sigma', 0)
        ma200 = data.get('ma200', 0)

        if math.isnan(ma200) or math.isnan(sigma):
            continue

        ticker = data.get('ticker', 'Unknown')
        is_up_breakout = "상향 돌파" in status
        is_down_breakout = "하향 돌파" in status
        is_sigma_high = sigma >= sigma_max
        is_sigma_low = sigma <= sigma_min

        if not is_up_breakout and not is_down_breakout and not is_sigma_high and not is_sigma_low:
            continue

        if is_up_breakout:
            up_breakouts.append(data)
        elif is_down_breakout:
            down_breakouts.append(data)
        elif is_sigma_high:
            sigma_highs.append(data)
        elif is_sigma_low:
            sigma_lows.append(data)

    def _format_line(data):
        ticker = data.get('ticker', 'Unknown')
        sigma = data.get('sigma', 0)
        ma200 = data.get('ma200', 0)
        if tickers and f"A{ticker}" in tickers:
            name = tickers[f"A{ticker}"]
            return f"{ticker}  {name}  SMA {ma200:,.0f}  σ {sigma:.1f}"
        return f"[{ticker}]  SMA {ma200:.2f}  σ {sigma:.1f}"

    if not up_breakouts and not down_breakouts and not sigma_highs and not sigma_lows:
        return

    parts = ["📊 가격 상태 알림"]
    if up_breakouts:
        parts.append(f"{'─' * MSG_SEPARATOR_WIDTH}")
        parts.append("▸ 상향 돌파")
        parts.extend(_format_line(d) for d in up_breakouts)
    if down_breakouts:
        parts.append(f"{'─' * MSG_SEPARATOR_WIDTH}")
        parts.append("▸ 하향 돌파")
        parts.extend(_format_line(d) for d in down_breakouts)
    if sigma_highs:
        parts.append(f"{'─' * MSG_SEPARATOR_WIDTH}")
        parts.append(f"▸ Sigma 고  ( σ ≥ {sigma_max} )")
        parts.extend(_format_line(d) for d in sorted(sigma_highs, key=lambda d: d.get('sigma', 0), reverse=True))
    if sigma_lows:
        parts.append(f"{'─' * MSG_SEPARATOR_WIDTH}")
        parts.append(f"▸ Sigma 저  ( σ ≤ {sigma_min} )")
        parts.extend(_format_line(d) for d in sorted(sigma_lows, key=lambda d: d.get('sigma', 0)))

    send_telegram_message("\n".join(parts))


def send_telegram_dashboard_summary(data):
    
    regime = data["market_regime"]
    sign = "+" if regime["tip_momentum"] > 0 else ""
    market_season_line = f"🌤️ <b>Market Regime</b>: TIP Mom ({sign}{regime['tip_momentum']:.1f}%)"
    
    def get_ticker_link(ticker, region):
        if region == "KR":
            return f'<a href="https://finance.naver.com/item/main.naver?code={ticker}">{ticker}</a>'
        else:
            return f'<a href="https://finance.yahoo.com/quote/{ticker}">{ticker}</a>'

    def format_tickers(entries):
        kr_ticks = [get_ticker_link(e['ticker'], 'KR') for e in entries if e["region"] == "KR"]
        us_ticks = [get_ticker_link(e['ticker'], 'US') for e in entries if e["region"] == "US"]
        
        lines = []
        if us_ticks:
            prefix = "  🇺🇸 "
            if len(us_ticks) > 5:
                prefix += ", ".join(us_ticks[:5]) + f" (외 {len(us_ticks) - 5}개)"
            else:
                prefix += ", ".join(us_ticks)
            lines.append(prefix)
        else:
            lines.append("  🇺🇸 None")
            
        if kr_ticks:
            prefix = "  🇰🇷 "
            if len(kr_ticks) > 5:
                prefix += ", ".join(kr_ticks[:5]) + f" (외 {len(kr_ticks) - 5}개)"
            else:
                prefix += ", ".join(kr_ticks)
            lines.append(prefix)
        else:
            lines.append("  🇰🇷 None")
            
        return "\n".join(lines)
    
    def format_extremes(entries):
        kr_parts = [f"{get_ticker_link(e['ticker'], 'KR')}({e['t_sigma']})" for e in entries if e["region"] == "KR"]
        us_parts = [f"{get_ticker_link(e['ticker'], 'US')}({e['t_sigma']})" for e in entries if e["region"] == "US"]
        
        lines = []
        if us_parts:
            prefix = "  🇺🇸 "
            if len(us_parts) > 5:
                prefix += ", ".join(us_parts[:5]) + f" (외 {len(us_parts) - 5}개)"
            else:
                prefix += ", ".join(us_parts)
            lines.append(prefix)
        else:
            lines.append("  🇺🇸 None")
            
        if kr_parts:
            prefix = "  🇰🇷 "
            if len(kr_parts) > 5:
                prefix += ", ".join(kr_parts[:5]) + f" (외 {len(kr_parts) - 5}개)"
            else:
                prefix += ", ".join(kr_parts)
            lines.append(prefix)
        else:
            lines.append("  🇰🇷 None")
            
        return "\n".join(lines)

    up_ticks = data["trend_breakouts"]["up_breakouts"]
    down_ticks = data["trend_breakouts"]["down_breakouts"]
    overheated = [e for e in data["valuation_extremes"] if e["t_sigma"] > 2.5]
    depressed = [e for e in data["valuation_extremes"] if e["t_sigma"] < -2.5]
    
    BASE = "https://pinedance.github.io/quant-data-open/dist"
    link_line = (
        f"🔗 <a href=\"{BASE}/US/dashboard.html\">🇺🇸 US Dashboard</a> | "
        f"<a href=\"{BASE}/KR/dashboard.html\">🇰🇷 KR Dashboard</a>"
    )
    
    parts = [
        "<b>📊 [Quant Dashboard] 일간 업데이트</b>",
        "",
        market_season_line,
        "──────────────────",
        "📈 <b>EMA200 상향 돌파</b>",
        format_tickers(up_ticks),
        "",
        "📉 <b>EMA200 하향 돌파</b>",
        format_tickers(down_ticks),
        "",
        "🔥 <b>과열 (T-Sigma &gt; 2.5)</b>",
        format_extremes(overheated),
        "",
        "❄️ <b>침체 (T-Sigma &lt; -2.5)</b>",
        format_extremes(depressed),
        "──────────────────",
        link_line
    ]
    
    msg = "\n".join(parts)
    send_telegram_message(msg, parse_mode='HTML')

