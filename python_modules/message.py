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

def notice_price_status( data, tickers=None ):
    try:
        # '상향 지속'이 아닌 경우 알림 전송
        if not "지속" in data['status']:
            if tickers:
                name = tickers.get( f"A{data['ticker']}", "Unknown")
                message = f"[{data['ticker']}] {data['status']}\n{name}\n현재 가격: {data['current_price']:.2f}\n200일 MA: {data['ma200']:.2f}"
            else:
                message = f"[{data['ticker']}] {data['status']}\n현재 가격: {data['current_price']:.2f}\n200일 MA: {data['ma200']:.2f}"
            send_telegram_message(message)
    except Exception as e:
        print(f"{ticker} 처리 중 오류 발생: {str(e)}")
