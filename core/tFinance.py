import pandas as pd
from core.message import send_telegram_message


#%% DEAL FINANCE DATA
######################################################################

def get_price_status( ticker, _hist ):

    if isinstance( _hist, pd.Series ):
        hist = _hist.to_frame()
    else:
        hist = _hist.copy()
        
    if hist.empty:
        return None
    
    # print( hist )
    # print( hist.columns )
    
    hist.columns = ['Close']

    # 5일 이동평균 및 표준편차 계산
    hist['MA005'] = hist['Close'].rolling(window=5).mean()
    hist['STD005'] = hist['Close'].rolling(window=5).std()
    
    # 200일 이동평균 및 표준편차 계산
    hist['MA200'] = hist['Close'].rolling(window=200).mean()
    hist['STD200'] = hist['Close'].rolling(window=200).std()
    
    # 최근 마지막 데이터 추출
    recent = hist.iloc[-1]
    ma200 = recent['MA200']
    std200 = recent['STD200']
    current_price = recent['MA005']
    
    # 이전 날 데이터 (돌파 판단용)
    prev_data = hist.iloc[-2]
    prev_ma200 = prev_data['MA200']
    prev_price = prev_data['MA005']
    
    # 상태 결정
    sigma = (current_price - ma200) / std200

    if current_price > ma200 and prev_price <= prev_ma200:
        status = "상향 돌파"
    elif current_price > ma200 and prev_price > prev_ma200:
        status = f"상향 지속({sigma:.1f})"
    elif current_price < ma200 and prev_price >= prev_ma200:
        status = "하향 돌파"
    elif current_price < ma200 and prev_price < prev_ma200:
        status = f"하향 지속({sigma:.1f})"
    else:
        status = "중립"
    

    rst = {
        'ticker': ticker,
        'current_price': current_price,
        'ma200': ma200,
        'std200': std200,
        'sigma': sigma,
        'status': status
    }
    
    print(f"{rst['ticker']}: {rst['current_price']:.2f} | MA200: {rst['ma200']:.2f} | 상태: {rst['status']}")
    
    return rst

def process_price_status(etf_tickers, etf_data_raw):
    status_results = []
    for i, hist in enumerate(etf_data_raw):
        try:
            status_data = get_price_status(etf_tickers[i], hist)
            if status_data:
                status_results.append(status_data)
        except Exception as e:
            error_msg = f"Error processing status for {etf_tickers[i]}: {str(e)}"
            send_telegram_message(error_msg)
    return status_results

def calculate_macd(df, fast=12, slow=26, signal=9):
    # Calculate EMA for fast and slow periods
    ema_fast = df.ewm(span=fast).mean()
    ema_slow = df.ewm(span=slow).mean()

    # Calculate MACD line
    macd_line = ema_fast - ema_slow

    # Calculate signal line
    signal_line = macd_line.ewm(span=signal).mean()

    # Calculate MACD histogram
    macd_histogram = macd_line - signal_line

    return macd_line, macd_histogram

