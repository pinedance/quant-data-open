import math
import pandas as pd
from core.cons import MA_SHORT_WINDOW, MA_LONG_WINDOW

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

    hist['MA005'] = hist['Close'].rolling(window=MA_SHORT_WINDOW).mean()
    hist['STD005'] = hist['Close'].rolling(window=MA_SHORT_WINDOW).std()
    hist['MA200'] = hist['Close'].rolling(window=MA_LONG_WINDOW).mean()
    hist['STD200'] = hist['Close'].rolling(window=MA_LONG_WINDOW).std()

    recent = hist.iloc[-1]
    ma200 = recent['MA200']
    std200 = recent['STD200']
    current_price = recent['MA005']

    prev_data = hist.iloc[-2]
    prev_ma200 = prev_data['MA200']
    prev_price = prev_data['MA005']
 
    if pd.isna(ma200) or pd.isna(std200) or math.isnan(ma200) or math.isnan(std200):
        sigma = 0.0
        status = "데이터부족"
    elif std200 > 0:
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
    else:
        sigma = 0.0
        status = "중립"
    

    rst = {
        'ticker': ticker,
        'current_price': current_price,
        'ma200': ma200,
        'std200': std200,
        'sigma': sigma,
        'status': status
    }
    
    ma_val = rst['ma200']
    ma_str = f"{ma_val:.2f}" if not pd.isna(ma_val) else "0.00"
    print(f"{rst['ticker']}: {rst['current_price']:.2f} | MA200: {ma_str} | 상태: {rst['status']}")
    
    return rst

def process_price_status(etf_tickers, etf_data_raw):
    if len(etf_tickers) != len(etf_data_raw):
        raise ValueError(f"etf_tickers({len(etf_tickers)})와 etf_data_raw({len(etf_data_raw)}) 길이가 다릅니다.")
    status_results = []
    errors = []
    for ticker, hist in zip(etf_tickers, etf_data_raw):
        try:
            status_data = get_price_status(ticker, hist)
            if status_data:
                status_results.append(status_data)
        except Exception as e:
            errors.append(f"Error processing status for {ticker}: {str(e)}")
            
    if errors:
        print("\n".join(errors))
    return status_results

def calculate_macd(df, fast=12, slow=26, signal=9):
    ema_fast = df.ewm(span=fast, adjust=False).mean()
    ema_slow = df.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    macd_histogram = macd_line - signal_line
    return macd_line, macd_histogram

import numpy as np
import scipy.stats as stats

def calculate_average_momentum(prices_df):
    if len(prices_df) < 13:
        return 0.0 if isinstance(prices_df, pd.Series) else pd.Series(0.0, index=prices_df.columns)
    P_curr = prices_df.iloc[-1]
    P_1m = prices_df.iloc[-2]
    P_3m = prices_df.iloc[-4]
    P_6m = prices_df.iloc[-7]
    P_12m = prices_df.iloc[-13]
    
    r1 = (P_curr / P_1m) - 1
    r3 = (P_curr / P_3m) - 1
    r6 = (P_curr / P_6m) - 1
    r12 = (P_curr / P_12m) - 1
    
    return (r1 + r3 + r6 + r12) / 4.0

def calculate_ema_crossovers(prices_df):
    if len(prices_df) < 200:
        raise ValueError("prices_df must contain at least 200 data points.")
    ema5 = prices_df.ewm(span=5, adjust=False).mean()
    ema200 = prices_df.ewm(span=200, adjust=False).mean()
    
    curr_ema5 = ema5.iloc[-1]
    curr_ema200 = ema200.iloc[-1]
    prev_ema5 = ema5.iloc[-2]
    prev_ema200 = ema200.iloc[-2]
    
    up_break = (curr_ema5 > curr_ema200) & (prev_ema5 <= prev_ema200)
    down_break = (curr_ema5 < curr_ema200) & (prev_ema5 >= prev_ema200)
    up_keep = (curr_ema5 > curr_ema200) & ~up_break
    
    return ema5.iloc[-1], ema200.iloc[-1], up_break, down_break, up_keep

def calculate_macd_z(hist_df, daily_prices_df):
    if len(daily_prices_df) < 200:
        raise ValueError("daily_prices_df must contain at least 200 data points.")
    current_macd_hist = hist_df.iloc[-1]
    log_returns = np.log(daily_prices_df / daily_prices_df.shift(1))
    sigma_daily = log_returns.iloc[-200:].std()
    sigma_monthly = sigma_daily * np.sqrt(21)
    current_price = daily_prices_df.iloc[-1]
    scale = current_price * sigma_monthly
    
    return current_macd_hist / (scale + 1e-6)

def calculate_t_sigma(series, window=200):
    if len(series) < window + 2:
        return 0.0, 0.0, 0.0, 0.0, 0.0
    
    log_prices = np.log(series)
    base = log_prices.iloc[-window:]
    
    try:
        df_fit, loc_fit, scale_fit = stats.t.fit(base)
    except Exception:
        return 0.0, 0.0, 0.0, 0.0, 0.0
        
    current = log_prices.iloc[-1]
    t_score = (current - loc_fit) / scale_fit
    p_value = stats.t.cdf(t_score, df=df_fit)
    p_value = np.clip(p_value, 1e-15, 1 - 1e-15)
    real_z = float(stats.norm.ppf(p_value))
    raw_z = float((current - base.mean()) / base.std() if base.std() > 0 else 0.0)
    
    return real_z, raw_z, df_fit, loc_fit, scale_fit


