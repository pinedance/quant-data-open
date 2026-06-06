import os
import math
import json
import datetime
import numpy as np
import pandas as pd
import scipy.stats as stats
import requests
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

# Module-level constants
T_SIGMA_WINDOW = 200    # EMA200과 통일 — "EMA200 기준선 대비 현재가 몇 sigma?"
MACD_Z_WINDOW  = 12     # 12개월 rolling z-score

def calculate_t_sigma(price_series, window=T_SIGMA_WINDOW):
    if len(price_series) < window + 2:
        return 0.0, 0.0, 0.0, 0.0, 0.0

    # Use log-price levels (not returns) — Bollinger Band principle + heavy-tail T
    log_prices = np.log(price_series)
    base = log_prices.iloc[-window:]          # 200-day window of log-price levels

    try:
        df_fit, loc_fit, scale_fit = stats.t.fit(base)   # MLE: loc ≈ 200-day mean
    except Exception as e:
        print(f"Error fitting stats.t: {e}")
        return 0.0, 0.0, 0.0, 0.0, 0.0

    current = log_prices.iloc[-1]
    t_score = (current - loc_fit) / scale_fit            # sigma above 200-day center
    p_value = stats.t.cdf(t_score, df=df_fit)
    p_value = np.clip(p_value, 1e-15, 1 - 1e-15)
    real_z  = float(stats.norm.ppf(p_value))             # convert to standard normal sigma

    raw_z = float(
        (current - base.mean()) / base.std()
        if base.std() > 0 else 0.0
    )
    return real_z, raw_z, float(df_fit), float(loc_fit), float(scale_fit)

def calculate_macd_z(hist_series, window=MACD_Z_WINDOW):
    """
    Z-score of current MACD histogram vs its own trailing window.
    Normalizes price-unit differences → cross-ticker comparison possible.

    Args:
        hist_series: pd.Series of monthly MACD histogram values (oldest first)
        window: rolling window in months (default MACD_Z_WINDOW=12)
    Returns:
        float: z-score. Positive = momentum stronger than recent history.
    """
    if len(hist_series) < window + 1:
        return 0.0
    base = hist_series.iloc[-window:]
    current = hist_series.iloc[-1]
    std = base.std()
    if std == 0:
        return 0.0
    return float((current - base.mean()) / std)

def calculate_average_momentum(price_series):
    # assumes the series is resampled to monthly EOM prices, with last index representing current date
    if len(price_series) < 13:
        return 0.0
    P_curr = price_series.iloc[-1]
    P_1m = price_series.iloc[-2]
    P_3m = price_series.iloc[-4]
    P_6m = price_series.iloc[-7]
    P_12m = price_series.iloc[-13]
    
    r1 = (P_curr / P_1m) - 1 if P_1m > 0 else 0.0
    r3 = (P_curr / P_3m) - 1 if P_3m > 0 else 0.0
    r6 = (P_curr / P_6m) - 1 if P_6m > 0 else 0.0
    r12 = (P_curr / P_12m) - 1 if P_12m > 0 else 0.0
    
    return float((r1 + r3 + r6 + r12) / 4)

def calculate_ema_crossovers(price_series):
    if len(price_series) < 200:
        return "중립", 0.0, 0.0
    ema005 = price_series.ewm(span=5, adjust=False).mean()
    ema200 = price_series.ewm(span=200, adjust=False).mean()
    
    curr_ema005 = ema005.iloc[-1]
    curr_ema200 = ema200.iloc[-1]
    prev_ema005 = ema005.iloc[-2]
    prev_ema200 = ema200.iloc[-2]
    
    if curr_ema005 > curr_ema200 and prev_ema005 <= prev_ema200:
        status = "상향 돌파"
    elif curr_ema005 < curr_ema200 and prev_ema005 >= prev_ema200:
        status = "하향 돌파"
    elif curr_ema005 > curr_ema200:
        status = "상향 유지"
    else:
        status = "하향 유지"
        
    return status, float(curr_ema005), float(curr_ema200)

def check_nans_for_df(df, region):
    nan_info = []
    n_nan = df.isna().sum().sum()
    if n_nan > 0:
        for col in df.columns:
            nan_series = df[col].isna()
            if nan_series.sum() > 0:
                nan_indices = nan_series[nan_series].index
                start_index = nan_indices[0]
                end_index = nan_indices[-1]
                # convert timestamps to string
                if hasattr(start_index, 'strftime'):
                    start_index = start_index.strftime("%Y-%m-%d")
                if hasattr(end_index, 'strftime'):
                    end_index = end_index.strftime("%Y-%m-%d")
                nan_info.append({
                    "column": col,
                    "region": region,
                    "count": int(nan_series.sum()),
                    "range": f"{start_index} ~ {end_index}"
                })
    return nan_info

def _process_single_ticker(args):
    ticker, series_d, series_m, region, name = args
    real_z, raw_z, df_fit, loc, scale = calculate_t_sigma(series_d)
    avg_mom = calculate_average_momentum(series_m)
    status, ema5, ema200 = calculate_ema_crossovers(series_d)
    
    return {
        "ticker": ticker,
        "name": name,
        "region": region,
        "t_sigma": round(real_z, 2),
        "raw_z": round(raw_z, 2),
        "df": round(df_fit, 2),
        "avg_mom": round(avg_mom * 100, 2),
        "ema005": round(ema5, 2),
        "ema200": round(ema200, 2),
        "status": status
    }

class DashboardAnalyzer:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.data_dir = self.root_dir / "output"
        
    def _load_names(self):
        names = {}
        
        # 1. KR names from output/KR/data/stocklist.json
        # Strip 'A' prefix from ticker keys to match the analyzer's clean ticker lookup key
        kr_path = self.root_dir / "output/KR/data/stocklist.json"
        if kr_path.exists():
            try:
                with open(kr_path, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)
                if "Co" in data:
                    for item in data["Co"]:
                        cd = item["cd"]
                        clean_cd = cd[1:] if cd.startswith('A') else cd
                        names[clean_cd] = item["nm"]
            except Exception as e:
                print(f"Error loading KR stocklist: {e}")

        # 2. US names from output/US/data/stocklist.json
        us_path = self.root_dir / "output/US/data/stocklist.json"
        if us_path.exists():
            try:
                with open(us_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if "Co" in data:
                    for item in data["Co"]:
                        names[item["cd"]] = item["nm"]
            except Exception as e:
                print(f"Error loading US stocklist: {e}")

        return names

    def analyze(self):
        names_dict = self._load_names()
        
        # Paths
        us_daily_path = self.data_dir / "US/stocks/price/D/raw.tsv"
        kr_daily_path = self.data_dir / "KR/stocks/price/D/raw.tsv"
        
        us_monthly_path = self.data_dir / "US/stocks/price/M/raw-eom.tsv"
        kr_monthly_path = self.data_dir / "KR/stocks/price/M/raw-eom.tsv"
        
        us_macd_hist_path = self.data_dir / "US/stocks/signals/MACD/M/raw-eom-histogram.tsv"
        kr_macd_hist_path = self.data_dir / "KR/stocks/signals/MACD/M/raw-eom-histogram.tsv"
        
        # 1. Market Season (TIP Momentum)
        tip_momentum = 0.0
        if us_monthly_path.exists():
            df_us_m = pd.read_csv(us_monthly_path, sep='\t', index_col=0, header=0)
            if 'TIP' in df_us_m.columns:
                tip_momentum = calculate_average_momentum(df_us_m['TIP'])
                
        # 2. Process All Tickers for Z-Score and EMA Breakouts
        ticker_stats = []
        up_breakouts = []
        down_breakouts = []
        nan_status = []
        tasks = []
        
        # Process US tickers
        if us_daily_path.exists() and us_monthly_path.exists():
            df_us_d = pd.read_csv(us_daily_path, sep='\t', index_col=0, header=0)
            df_us_m = pd.read_csv(us_monthly_path, sep='\t', index_col=0, header=0)
            
            # Check NaNs
            nan_status.extend(check_nans_for_df(df_us_d, "US"))
            
            for ticker in df_us_d.columns:
                series_d = df_us_d[ticker].dropna()
                series_m = df_us_m[ticker].dropna()
                name = names_dict.get(ticker, ticker)
                tasks.append((ticker, series_d, series_m, "US", name))

        # Process KR tickers
        if kr_daily_path.exists() and kr_monthly_path.exists():
            df_kr_d = pd.read_csv(kr_daily_path, sep='\t', index_col=0, header=0)
            df_kr_m = pd.read_csv(kr_monthly_path, sep='\t', index_col=0, header=0)
            
            # Check NaNs
            nan_status.extend(check_nans_for_df(df_kr_d, "KR"))
            
            for col in df_kr_d.columns:
                ticker = col[1:] if col.startswith('A') else col
                series_d = df_kr_d[col].dropna()
                series_m = df_kr_m[col].dropna()
                name = names_dict.get(ticker, ticker)
                tasks.append((ticker, series_d, series_m, "KR", name))

        # Run tasks in parallel to speed up scipy.stats.t.fit MLE calculation
        if tasks:
            max_workers = os.cpu_count() or 4
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                results = list(executor.map(_process_single_ticker, tasks))
            
            for stat_entry in results:
                ticker_stats.append(stat_entry)
                status = stat_entry["status"]
                if status == "상향 돌파":
                    up_breakouts.append(stat_entry)
                elif status == "하향 돌파":
                    down_breakouts.append(stat_entry)

        # 3. Monthly MACD Histogram > 0 list
        macd_positive = []
        macd_z_lookup    = {}   # ticker -> macd_z   (all tickers, for scatter join)
        macd_hist_lookup = {}   # ticker -> macd_hist (raw last value)

        # Process US EOM MACD
        if us_macd_hist_path.exists():
            df_us_hist = pd.read_csv(us_macd_hist_path, sep='\t', index_col=0, header=0)
            if not df_us_hist.empty:
                last_row = df_us_hist.iloc[-1]
                for ticker in df_us_hist.columns:
                    hist_series = df_us_hist[ticker].dropna()
                    val = last_row.get(ticker, float('nan'))
                    if pd.isna(val):
                        continue
                    z = calculate_macd_z(hist_series)
                    macd_z_lookup[ticker]    = round(z, 2)
                    macd_hist_lookup[ticker] = round(float(val), 2)
                    if val > 0:
                        macd_positive.append({
                            "ticker": ticker,
                            "name": names_dict.get(ticker, ticker),
                            "region": "US",
                            "macd_hist": round(float(val), 2),
                            "macd_z": round(z, 2),
                        })

        # Process KR EOM MACD
        if kr_macd_hist_path.exists():
            df_kr_hist = pd.read_csv(kr_macd_hist_path, sep='\t', index_col=0, header=0)
            if not df_kr_hist.empty:
                last_row = df_kr_hist.iloc[-1]
                for col in df_kr_hist.columns:
                    ticker = col[1:] if col.startswith('A') else col
                    hist_series = df_kr_hist[col].dropna()
                    val = last_row.get(col, float('nan'))
                    if pd.isna(val):
                        continue
                    z = calculate_macd_z(hist_series)
                    macd_z_lookup[ticker]    = round(z, 2)
                    macd_hist_lookup[ticker] = round(float(val), 2)
                    if val > 0:
                        macd_positive.append({
                            "ticker": ticker,
                            "name": names_dict.get(ticker, ticker),
                            "region": "KR",
                            "macd_hist": round(float(val), 2),
                            "macd_z": round(z, 2),
                        })

        # Sort valuation extremes by T-Sigma descending
        ticker_stats.sort(key=lambda x: x["t_sigma"], reverse=True)
        
        for entry in ticker_stats:
            t = entry["ticker"]
            entry["macd_z"]    = macd_z_lookup.get(t, 0.0)
            entry["macd_hist"] = macd_hist_lookup.get(t, 0.0)
        
        # Structure final dashboard JSON data
        dashboard_data = {
            "market_regime": {
                "tip_momentum": round(tip_momentum * 100, 2),
                "status": "Bullish" if tip_momentum > 0 else "Bearish"
            },
            "trend_breakouts": {
                "up_breakouts": up_breakouts,
                "down_breakouts": down_breakouts
            },
            "monthly_momentum": macd_positive,
            "valuation_extremes": ticker_stats,
            "data_quality_status": nan_status,
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return dashboard_data
