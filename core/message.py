import os
import math
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("Warning: TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 설정되지 않았습니다. Telegram 알림이 비활성화됩니다.")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    
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
        sigma_max, sigma_min = 1.8, -1.8
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
    sigma_max, sigma_min = 1.8, -1.8
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
        parts.append(f"{'─' * 28}")
        parts.append("▸ 상향 돌파")
        parts.extend(_format_line(d) for d in up_breakouts)
    if down_breakouts:
        parts.append(f"{'─' * 28}")
        parts.append("▸ 하향 돌파")
        parts.extend(_format_line(d) for d in down_breakouts)
    if sigma_highs:
        parts.append(f"{'─' * 28}")
        parts.append(f"▸ Sigma 고  ( σ ≥ {sigma_max} )")
        parts.extend(_format_line(d) for d in sorted(sigma_highs, key=lambda d: d.get('sigma', 0), reverse=True))
    if sigma_lows:
        parts.append(f"{'─' * 28}")
        parts.append(f"▸ Sigma 저  ( σ ≤ {sigma_min} )")
        parts.extend(_format_line(d) for d in sorted(sigma_lows, key=lambda d: d.get('sigma', 0)))

    send_telegram_message("\n".join(parts))
