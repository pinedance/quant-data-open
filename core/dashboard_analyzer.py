import datetime
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

from core.tFinance import (
    calculate_average_momentum,
    calculate_t_sigma,
    calculate_rsi,
    calculate_win_rate,
    calculate_win_loss_ratio,
)
from core.tFinance import calculate_ema_crossovers as tf_ema
from core.tFinance import calculate_macd_z as tf_macd_z
from core.cons import RSI_PERIOD, RSI_SIGNAL_PERIOD



def calculate_ema_crossovers(price_series):
    # Wrapper to support both vectorized DataFrame and legacy Series input formats
    if isinstance(price_series, pd.DataFrame):
        return tf_ema(price_series)
    
    if len(price_series) < 200:
        return "중립", 0.0, 0.0
        
    ema5_last, ema200_last, up_break, down_break, up_keep = tf_ema(price_series)
    
    if up_break:
        status = "상향 돌파"
    elif down_break:
        status = "하향 돌파"
    elif up_keep:
        status = "상향 유지"
    else:
        status = "하향 유지"
        
    return status, float(ema5_last), float(ema200_last)

def calculate_macd_z(hist_series, daily_prices):
    if daily_prices is None:
        ticker_name = getattr(hist_series, 'name', 'Unknown')
        raise ValueError(f"Ticker [{ticker_name}] daily_prices is completely missing.")
    if len(hist_series) == 0:
        raise ValueError("hist_series must not be empty.")
    if len(daily_prices) < 200:
        ticker_name = getattr(hist_series, 'name', 'Unknown')
        raise ValueError(f"Ticker [{ticker_name}] daily_prices must contain at least 200 data points for volatility scaling (got {len(daily_prices)}).")
        
    res = tf_macd_z(hist_series, daily_prices)
    if isinstance(res, pd.Series):
        return res
    return float(res)

def _process_t_sigma_single(args):
    ticker, series_d, _ = args
    real_z, raw_z, df_fit, loc_fit, scale_fit = calculate_t_sigma(series_d)
    return ticker, real_z, raw_z, df_fit

class DashboardAnalyzer:
    def __init__(self, names_dict, df_us_d, df_us_m, df_us_hist, df_kr_d, df_kr_m, df_kr_hist):
        self.names_dict = names_dict or self._load_names()
        self.df_us_d = df_us_d
        self.df_us_m = df_us_m
        self.df_us_hist = df_us_hist
        self.df_kr_d = df_kr_d
        self.df_kr_m = df_kr_m
        self.df_kr_hist = df_kr_hist

    def _load_names(self):
        names = {}
        # Dynamic fallback loading
        root_dir = Path(__file__).parent.parent
        kr_path = root_dir / "output/KR/data/stocklist.json"
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

        us_path = root_dir / "output/US/data/stocklist.json"
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
        # 1. Market Season
        tip_momentum = 0.0
        if 'TIP' in self.df_us_m.columns:
            tip_momentum = calculate_average_momentum(self.df_us_m[['TIP']]).iloc[0]

        # Compute US/KR metric vectors
        us_metrics = (
            calculate_average_momentum(self.df_us_m),
            *calculate_ema_crossovers(self.df_us_d),
            calculate_macd_z(self.df_us_hist, self.df_us_d),
            calculate_win_rate(self.df_us_d, 240),
            calculate_win_loss_ratio(self.df_us_d, 240)
        )
        kr_metrics = (
            calculate_average_momentum(self.df_kr_m),
            *calculate_ema_crossovers(self.df_kr_d),
            calculate_macd_z(self.df_kr_hist, self.df_kr_d),
            calculate_win_rate(self.df_kr_d, 240),
            calculate_win_loss_ratio(self.df_kr_d, 240)
        )

        # Build multiprocessing tasks for T-Sigma fitting
        tasks = []
        for ticker in self.df_us_d.columns:
            tasks.append((ticker, self.df_us_d[ticker].dropna(), "US"))
        for col in self.df_kr_d.columns:
            ticker = col[1:] if col.startswith('A') else col
            tasks.append((ticker, self.df_kr_d[col].dropna(), "KR"))

        t_sigma_results = {}
        if tasks:
            max_workers = os.cpu_count() or 4
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                results = list(executor.map(_process_t_sigma_single, tasks))
            for ticker, real_z, raw_z, df_fit in results:
                t_sigma_results[ticker] = (real_z, raw_z, df_fit)

        # Assemble
        ticker_stats = []
        up_breakouts = []
        down_breakouts = []
        macd_positive = []

        def assemble_results(df_d, df_hist, metrics, region):
            avg_mom, ema5_last, ema200_last, up_break, down_break, up_keep, macd_z, win_rates, win_loss_ratios = metrics
            last_hist = df_hist.iloc[-1]

            for col in df_d.columns:
                ticker = col[1:] if (region == "KR" and col.startswith('A')) else col
                name = self.names_dict.get(ticker, ticker)
                real_z, raw_z, df_fit = t_sigma_results.get(ticker, (0.0, 0.0, 0.0))

                if up_break[col]:
                    status = "상향 돌파"
                elif down_break[col]:
                    status = "하향 돌파"
                elif up_keep[col]:
                    status = "상향 유지"
                else:
                    status = "하향 유지"

                stat_entry = {
                    "ticker": ticker,
                    "name": name,
                    "region": region,
                    "t_sigma": round(real_z, 2),
                    "raw_z": round(raw_z, 2),
                    "df": round(df_fit, 2),
                    "avg_mom": round(avg_mom[col] * 100, 2),
                    "ema005": round(ema5_last[col], 2),
                    "ema200": round(ema200_last[col], 2),
                    "status": status,
                    "macd_z": round(macd_z[col], 2),
                    "macd_hist": round(float(last_hist[col]), 2),
                    "win_rate": round(float(win_rates[col]), 4),
                    "win_loss_ratio": round(float(win_loss_ratios[col]), 4)
                }
                ticker_stats.append(stat_entry)
                
                if status == "상향 돌파":
                    up_breakouts.append(stat_entry)
                elif status == "하향 돌파":
                    down_breakouts.append(stat_entry)

                if last_hist[col] > 0:
                    macd_positive.append({
                        "ticker": ticker,
                        "name": name,
                        "region": region,
                        "macd_hist": round(float(last_hist[col]), 2),
                        "macd_z": round(macd_z[col], 2),
                    })

        assemble_results(self.df_us_d, self.df_us_hist, us_metrics, "US")
        assemble_results(self.df_kr_d, self.df_kr_hist, kr_metrics, "KR")

        ticker_stats.sort(key=lambda x: x["t_sigma"], reverse=True)

        rsi_extremes = []
        def calculate_rsi_metrics(df_d, df_m, region):
            for col in df_d.columns:
                ticker = col[1:] if (region == "KR" and col.startswith('A')) else col
                name = self.names_dict.get(ticker, ticker)
                m_series = df_m[col].dropna()
                d_series = df_d[col].dropna()
                if m_series.empty or d_series.empty:
                    continue
                last_m_date = pd.to_datetime(m_series.index[-1])
                last_d_date = pd.to_datetime(d_series.index[-1])
                if last_d_date > last_m_date:
                    appended_val = pd.Series([d_series.iloc[-1]], index=[d_series.index[-1]])
                    merged_series = pd.concat([m_series, appended_val])
                else:
                    merged_series = m_series

                rsi_series = calculate_rsi(merged_series, period=RSI_PERIOD)
                rsi_signal_series = rsi_series.ewm(span=RSI_SIGNAL_PERIOD, adjust=False).mean()
                val_rsi = float(rsi_series.iloc[-1])
                val_rsi_signal = float(rsi_signal_series.iloc[-1])
                rsi_extremes.append({
                    "ticker": ticker,
                    "name": name,
                    "region": region,
                    "rsi": round(val_rsi, 2),
                    "rsi_signal": round(val_rsi_signal, 2),
                    "rsi_diff": round(val_rsi - val_rsi_signal, 2)
                })

        calculate_rsi_metrics(self.df_us_d, self.df_us_m, "US")
        calculate_rsi_metrics(self.df_kr_d, self.df_kr_m, "KR")
        rsi_extremes.sort(key=lambda x: x["rsi"], reverse=True)

        return {
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
            "rsi_extremes": rsi_extremes,
            "data_quality_status": [],
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
