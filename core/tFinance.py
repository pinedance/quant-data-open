import pandas as pd
from core.message import send_telegram_message


#%% DEAL FINANCE DATA
######################################################################

def get_price_status(ticker, _hist):
    if isinstance(_hist, pd.Series):
        hist = _hist.to_frame()
    else:
        hist = _hist.copy()

    if hist.empty or len(hist) < 2:
        return None

    if hist.shape[1] != 1:
        raise ValueError(f"[{ticker}] _hist는 1개 컬럼이어야 합니다. (받은 값: {hist.shape[1]}개)")

    hist.columns = ['Close']

    hist['MA005'] = hist['Close'].rolling(window=5).mean()
    hist['STD005'] = hist['Close'].rolling(window=5).std()
    hist['MA200'] = hist['Close'].rolling(window=200).mean()
    hist['STD200'] = hist['Close'].rolling(window=200).std()

    recent = hist.iloc[-1]
    ma200 = recent['MA200']
    std200 = recent['STD200']
    current_price = recent['MA005']

    prev_data = hist.iloc[-2]
    prev_ma200 = prev_data['MA200']
    prev_price = prev_data['MA005']

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
    if len(etf_tickers) != len(etf_data_raw):
        raise ValueError(f"etf_tickers({len(etf_tickers)})와 etf_data_raw({len(etf_data_raw)}) 길이가 다릅니다.")
    status_results = []
    for ticker, hist in zip(etf_tickers, etf_data_raw):
        try:
            status_data = get_price_status(ticker, hist)
            if status_data:
                status_results.append(status_data)
        except Exception as e:
            send_telegram_message(f"Error processing status for {ticker}: {str(e)}")
    return status_results

def calculate_macd(df, fast=12, slow=26, signal=9):
    ema_fast = df.ewm(span=fast).mean()
    ema_slow = df.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    macd_histogram = macd_line - signal_line
    return macd_line, macd_histogram

