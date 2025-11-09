import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot 설정
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    # print( url )
    
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
        if (not status or "지속" in status) and (sigma < sigma_max or sigma > sigma_min):
            return
            
        ticker = data.get('ticker', 'Unknown')
        current_price = data.get('current_price', 0)
        ma200 = data.get('ma200', 0)
        
        message = f"[{ticker}] {status}"
        # message = f"[{ticker}] {status}\n{name}\n현재 가격: {current_price:.2f}\n200일 MA: {ma200:.2f}"

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
