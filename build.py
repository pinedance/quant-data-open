#!/usr/bin/env python3
"""
설정 파일 기반 정적 사이트 빌더
config.yaml만 수정하면 새 페이지가 자동으로 생성됩니다
"""

import datetime
import json
import os
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader

from core.config import ConfigManager
from core.cons import (
    MA_LONG_WINDOW as MIN_REQUIRED_DAYS,
    PRICE_EMA_SPAN,
    RECENT_DAYS_COUNT,
)
from core.dashboard_analyzer import DashboardAnalyzer
from core.message import send_telegram_dashboard_summary
from core.tFinance import (
    MOMENTUM_KEYS,
    calculate_daily_average_momentum,
    calculate_daily_momentums,
    calculate_macd,
)
from core.tIO import save_df_as_html_table
from core.tTable import check_nans, post_process_price, resample_monthly

_config = ConfigManager()
BASE_DIR = Path(__file__).resolve().parent

def filter_dashboard_data(data, region):
    if not data:
        return None
    base_dates = data.get("base_dates", {})
    return {
        "base_date": base_dates.get(region, ""),
        "base_dates": base_dates,
        "market_regime": data["market_regime"],
        "trend_breakouts": {
            "up_breakouts":   [e for e in data["trend_breakouts"]["up_breakouts"]   if e["region"] == region],
            "down_breakouts": [e for e in data["trend_breakouts"]["down_breakouts"] if e["region"] == region],
        },
        "monthly_momentum":   [e for e in data["monthly_momentum"]   if e["region"] == region],
        "valuation_extremes": [e for e in data["valuation_extremes"] if e["region"] == region],
        "rsi_extremes":       [e for e in data.get("rsi_extremes", []) if e["region"] == region],
        "macro_rotation":     [e for e in data.get("macro_rotation", []) if e["region"] == region],
        "data_quality_status": [e for e in data["data_quality_status"] if e["region"] == region],
        "last_updated": data["last_updated"],
    }

def check_nans_for_dashboard(df, region, names_dict=None):
    nan_info = check_nans(df)
    dashboard_nan_status = []
    for item in nan_info:
        col = item["column"]
        ticker = col[1:] if (region == "KR" and col.startswith('A')) else col
        name = names_dict.get(ticker, ticker) if names_dict else ticker
        
        dashboard_nan_status.append({
            "column": col,
            "ticker": ticker,
            "name": name,
            "region": region,
            "count": item["count"],
            "range": f"{item['start']} ~ {item['end']}"
        })
    return dashboard_nan_status

def load_json_data(filepath):
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        return json.load(f)

def load_pages_config():
    return {"pages": _config.get_pages()}

def load_paths_config():
    return _config.get_paths()

def get_paths():
    paths = load_paths_config()
    defaults = {
        'templates': 'templates',
        'data': 'output/data',
        'source': 'output',
        'output': 'public',
        'output_subdir': 'dist'
    }
    for key, default in defaults.items():
        if key not in paths:
            paths[key] = default
    return {
        'templates': BASE_DIR / paths['templates'],
        'data': BASE_DIR / paths['data'],
        'source': BASE_DIR / paths['source'],
        'output': BASE_DIR / paths['output'],
        'output_subdir': paths['output_subdir']
    }

def ensure_dir(directory):
    Path(directory).mkdir(parents=True, exist_ok=True)

def convert_tsv_to_html(tsv_path, html_path):
    try:
        df = pd.read_csv(tsv_path, sep='\t', index_col=0, header=0)
        save_df_as_html_table(df, html_path)
        return True
    except Exception as e:
        print(f"⚠️  Error converting {tsv_path.name}: {e}")
        return False

def render_page(env, page_config, paths):
    name = page_config['name']
    title = page_config['title']
    data_file = page_config['data_file']
    template_type = page_config.get('template', 'table')
    data_key = page_config.get('data_key')
    columns = page_config.get('columns', [])

    data_path = paths['data'] / data_file
    if not data_path.exists():
        fallback_path = paths['output'] / paths['output_subdir'] / data_file
        if fallback_path.exists():
            data_path = fallback_path
        else:
            print(f"⚠️  데이터 파일이 없습니다: {data_path} (또는 {fallback_path})")
            return

    full_data = load_json_data(data_path)
    if data_key:
        data = full_data.get(data_key, [])
    else:
        data = full_data

    if template_type in ('table', 'dashboard', 'market_regime'):
        template_name = 'generic_table.html.j2' if template_type == 'table' else f'pages/{template_type}.html.j2'
        layout_name = 'data.html'
        output_path = paths['output'] / paths['output_subdir'] / f'{name}.html'

        if template_type == 'table':
            page_template = env.get_template(f'pages/{template_name}')
        else:
            page_template = env.get_template(template_name)
            
        region = page_config.get('region')
        content = page_template.render(data=data, columns=columns, region=region)
        layout_template = env.get_template(f'layouts/{layout_name}')
        html = layout_template.render(content=content, title=title)

        ensure_dir(output_path.parent)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✓ {output_path}")

    json_output_path = paths['output'] / paths['output_subdir'] / f'{name}.json'
    page_template = env.get_template('pages/generic_json.j2')
    json_content = page_template.render(data=data)
    layout_template = env.get_template('layouts/json.html')
    json_output = layout_template.render(content=json_content, title=title)

    ensure_dir(json_output_path.parent)
    with open(json_output_path, 'w', encoding='utf-8') as f:
        f.write(json_output)
    print(f"✓ {json_output_path}")

def save_derived_df_to_html(df, html_path):
    try:
        save_df_as_html_table(df, html_path)
        return True
    except Exception as e:
        print(f"⚠️  Error saving derived {html_path.name}: {e}")
        return False


def compute_region_derived_tables(price_raw: pd.DataFrame, region: str) -> dict[str, pd.DataFrame]:
    price_raw = price_raw.sort_index().astype("float64")
    price_ema3 = price_raw.ewm(span=PRICE_EMA_SPAN).mean()

    price_raw_m_eom = resample_monthly(price_raw, method="eom")
    price_ema3_m_eom = resample_monthly(price_ema3, method="eom")
    price_raw_m_curr = resample_monthly(price_raw, method="current")
    price_ema3_m_curr = resample_monthly(price_ema3, method="current")

    macd_line_raw_curr, macd_hist_raw_curr = calculate_macd(price_raw_m_curr)
    macd_line_ema3_curr, macd_hist_ema3_curr = calculate_macd(price_ema3_m_curr)
    macd_line_raw_eom, macd_hist_raw_eom = calculate_macd(price_raw_m_eom)
    macd_line_ema3_eom, macd_hist_ema3_eom = calculate_macd(price_ema3_m_eom)

    moms_d_raw = calculate_daily_momentums(price_raw)
    moms_d_ema3 = calculate_daily_momentums(price_ema3)

    raw_proc = post_process_price(price_raw)
    ema3_proc = post_process_price(price_ema3)

    tables = {
        f"{region}/stocks/price/D/ema3.html": ema3_proc,
        f"{region}/stocks/price/D/raw-300.html": raw_proc.tail(RECENT_DAYS_COUNT),
        f"{region}/stocks/price/D/ema3-300.html": ema3_proc.tail(RECENT_DAYS_COUNT),
        f"{region}/stocks/price/M/raw-eom.html": post_process_price(price_raw_m_eom),
        f"{region}/stocks/price/M/ema3-eom.html": post_process_price(price_ema3_m_eom),
        f"{region}/stocks/price/M/raw-current.html": post_process_price(price_raw_m_curr),
        f"{region}/stocks/price/M/ema3-current.html": post_process_price(price_ema3_m_curr),
        f"{region}/stocks/signals/MACD/M/raw-current-line.html": post_process_price(macd_line_raw_curr),
        f"{region}/stocks/signals/MACD/M/raw-current-histogram.html": post_process_price(macd_hist_raw_curr),
        f"{region}/stocks/signals/MACD/M/ema3-current-line.html": post_process_price(macd_line_ema3_curr),
        f"{region}/stocks/signals/MACD/M/ema3-current-histogram.html": post_process_price(macd_hist_ema3_curr),
        f"{region}/stocks/signals/MACD/M/raw-eom-line.html": post_process_price(macd_line_raw_eom),
        f"{region}/stocks/signals/MACD/M/raw-eom-histogram.html": post_process_price(macd_hist_raw_eom),
        f"{region}/stocks/signals/MACD/M/ema3-eom-line.html": post_process_price(macd_line_ema3_eom),
        f"{region}/stocks/signals/MACD/M/ema3-eom-histogram.html": post_process_price(macd_hist_ema3_eom),
    }
    for k in MOMENTUM_KEYS:
        tables[f"{region}/stocks/signals/momentum/{k}/D/raw.html"] = post_process_price(moms_d_raw[k])
        tables[f"{region}/stocks/signals/momentum/{k}/D/ema3.html"] = post_process_price(moms_d_ema3[k])

    return tables


def process_dist_files(paths):
    source_dir = paths['source']
    output_dir = paths['output'] / paths['output_subdir']
    if not source_dir.exists():
        print(f"⚠️  Source directory not found: {source_dir}")
        return

    converted_count = 0
    failed_count = 0
    tsv_tasks = []
    for tsv_file in source_dir.rglob("*.tsv"):
        relative_path = tsv_file.relative_to(source_dir)
        html_path = output_dir / relative_path.with_suffix('.html')
        tsv_tasks.append((tsv_file, html_path))

    derived_tasks = []
    for region in ("US", "KR"):
        raw_path = source_dir / f"{region}/stocks/price/D/raw.tsv"
        if raw_path.exists():
            df_raw = pd.read_csv(raw_path, sep='\t', index_col=0, header=0, parse_dates=True).sort_index()
            for rel_html, df_derived in compute_region_derived_tables(df_raw, region).items():
                derived_tasks.append((rel_html, df_derived, output_dir / rel_html))

    max_workers = os.cpu_count() or 4
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for tsv, html in tsv_tasks:
            futures[executor.submit(convert_tsv_to_html, tsv, html)] = (str(tsv.relative_to(source_dir)), html)
        for rel_html, df_derived, html in derived_tasks:
            futures[executor.submit(save_derived_df_to_html, df_derived, html)] = (rel_html, html)

        for future in futures:
            label, html_path = futures[future]
            try:
                if future.result():
                    converted_count += 1
                    print(f"✓ Generated {label} → {html_path.name}")
                else:
                    failed_count += 1
            except Exception as e:
                print(f"❌ Error generating {label}: {e}")
                failed_count += 1
    print(f"   Total: {converted_count} generated, {failed_count} failed")

def load_and_clean_dataset(paths):
    df_us_raw_dt = pd.read_csv(
        paths['source'] / "US/stocks/price/D/raw.tsv", sep='\t', index_col=0, header=0, parse_dates=True
    ).sort_index()
    df_kr_raw_dt = pd.read_csv(
        paths['source'] / "KR/stocks/price/D/raw.tsv", sep='\t', index_col=0, header=0, parse_dates=True
    ).sort_index()

    if len(df_us_raw_dt) < MIN_REQUIRED_DAYS or len(df_kr_raw_dt) < MIN_REQUIRED_DAYS:
        raise ValueError(f"Total price history is shorter than required window ({MIN_REQUIRED_DAYS} days).")

    us_m_eom_dt = resample_monthly(df_us_raw_dt, method='eom')
    _, us_hist_eom_dt = calculate_macd(us_m_eom_dt)
    kr_m_eom_dt = resample_monthly(df_kr_raw_dt, method='eom')
    _, kr_hist_eom_dt = calculate_macd(kr_m_eom_dt)

    df_us_d = post_process_price(df_us_raw_dt)
    df_us_m = post_process_price(us_m_eom_dt)
    df_us_hist = post_process_price(us_hist_eom_dt)

    df_kr_d = post_process_price(df_kr_raw_dt)
    df_kr_m = post_process_price(kr_m_eom_dt)
    df_kr_hist = post_process_price(kr_hist_eom_dt)

    df_us_d_raw = df_us_d.copy()
    df_kr_d_raw = df_kr_d.copy()

    # Filter out tickers with insufficient valid history (< MIN_REQUIRED_DAYS non-null points)
    valid_us_counts = df_us_d.notna().sum()
    clean_us_cols = valid_us_counts[valid_us_counts >= MIN_REQUIRED_DAYS].index
    us_excluded = df_us_d.columns.difference(clean_us_cols)
    if not us_excluded.empty:
        print(f"⚠️  Excluding US tickers (insufficient history < {MIN_REQUIRED_DAYS} days): {list(us_excluded)}")
    df_us_d = df_us_d[clean_us_cols].ffill().bfill()
    df_us_m = df_us_m[clean_us_cols].ffill().bfill()
    df_us_hist = df_us_hist[clean_us_cols].ffill().bfill()

    valid_kr_counts = df_kr_d.notna().sum()
    clean_kr_cols = valid_kr_counts[valid_kr_counts >= MIN_REQUIRED_DAYS].index
    kr_excluded = df_kr_d.columns.difference(clean_kr_cols)
    if not kr_excluded.empty:
        clean_names = [c[1:] if c.startswith('A') else c for c in kr_excluded]
        print(f"⚠️  Excluding KR tickers (insufficient history < {MIN_REQUIRED_DAYS} days): {clean_names}")
    df_kr_d = df_kr_d[clean_kr_cols].ffill().bfill()
    df_kr_m = df_kr_m[clean_kr_cols].ffill().bfill()
    df_kr_hist = df_kr_hist[clean_kr_cols].ffill().bfill()

    return df_us_d, df_us_m, df_us_hist, df_kr_d, df_kr_m, df_kr_hist, df_us_d_raw, df_kr_d_raw


def _format_momentum_series(mom_series: pd.Series) -> dict:
    valid_series = mom_series.dropna()
    if valid_series.empty:
        return {"tip_momentum": 0.0, "status": "Bearish", "series": []}

    pct_series = (valid_series * 100.0).round(2)
    last_val = float(pct_series.iloc[-1])
    dates = valid_series.index.strftime("%Y-%m-%d").tolist()
    values = pct_series.tolist()

    return {
        "tip_momentum": last_val,
        "status": "Bullish" if last_val > 0 else "Bearish",
        "series": [{"date": d, "momentum": v} for d, v in zip(dates, values)],
    }


def _serialize_momentum_series(prices_df: pd.DataFrame, ticker: str = "TIP") -> dict:
    if ticker not in prices_df.columns:
        return {"tip_momentum": 0.0, "status": "Bearish", "series": []}

    mom_series = calculate_daily_average_momentum(prices_df[[ticker]])[ticker]
    return _format_momentum_series(mom_series)


def build_market_regime_data(paths: dict) -> dict:
    price_path = paths['source'] / "US/stocks/price/D/raw.tsv"
    df_raw = pd.read_csv(price_path, sep='\t', index_col=0, header=0, parse_dates=True).sort_index()
    df_ema3 = df_raw.ewm(span=PRICE_EMA_SPAN).mean()
    base_date = df_raw.index[-1].strftime("%Y-%m-%d") if not df_raw.empty else ""

    raw_data = _serialize_momentum_series(df_raw, "TIP")
    ema3_data = _serialize_momentum_series(df_ema3, "TIP")

    payload = {
        "base_date": base_date,
        "ticker": "TIP",
        "raw": raw_data,
        "ema3": ema3_data,
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    us_dir = paths['output'] / paths['output_subdir'] / "US"
    ensure_dir(us_dir)
    out_path = us_dir / "market-regime.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved US market regime data -> {out_path}")
    return payload


def build():
    print("🔨 Building site with Jinja2...")
    no_message = "--no-message" in sys.argv

    print("\n📋 Loading configuration...")
    paths = get_paths()
    pages_config = load_pages_config()
    pages = pages_config.get('pages', [])

    if not pages:
        print("⚠️  설정된 페이지가 없습니다")
        return

    print(f"   Found {len(pages)} page(s) to generate")
    print(f"   Templates: {paths['templates']}")
    print(f"   Data: {paths['data']}")
    print(f"   Source: {paths['source']}")
    print(f"   Output: {paths['output']}")

    if paths['output'].exists():
        shutil.rmtree(paths['output'])
    ensure_dir(paths['output'])

    print("\n📊 Running Quant Dashboard analysis...")
    
    # Preprocess/Filter data
    df_us_d, df_us_m, df_us_hist, df_kr_d, df_kr_m, df_kr_hist, df_us_d_raw, df_kr_d_raw = load_and_clean_dataset(paths)
    
    # Inject filtered data
    analyzer = DashboardAnalyzer(
        names_dict={}, # Filled dynamically or handled inside
        df_us_d=df_us_d,
        df_us_m=df_us_m,
        df_us_hist=df_us_hist,
        df_kr_d=df_kr_d,
        df_kr_m=df_kr_m,
        df_kr_hist=df_kr_hist
    )
    
    try:
        dashboard_data = analyzer.analyze()
        if dashboard_data:
            nan_status = []
            nan_status.extend(check_nans_for_dashboard(df_us_d_raw, "US", analyzer.names_dict))
            nan_status.extend(check_nans_for_dashboard(df_kr_d_raw, "KR", analyzer.names_dict))
            dashboard_data["data_quality_status"] = nan_status

        for region in ["US", "KR"]:
            filtered_data = filter_dashboard_data(dashboard_data, region)
            region_dir = paths['output'] / paths['output_subdir'] / region
            ensure_dir(region_dir)
            json_output_path = region_dir / 'dashboard.json'
            with open(json_output_path, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, f, ensure_ascii=False, indent=2)
            print(f"✓ Saved {region} dashboard data -> {json_output_path}")
    except Exception as e:
        print(f"❌ Error during dashboard analysis: {e}")
        dashboard_data = None

    try:
        build_market_regime_data(paths)
    except Exception as e:
        print(f"❌ Error building market regime data: {e}")

    env = Environment(
        loader=FileSystemLoader(paths['templates']),
        autoescape=False
    )

    def tojson_filter(value):
        return json.dumps(value, ensure_ascii=False, indent=None, separators=(',', ': '))
    env.filters['tojson'] = tojson_filter

    print("\n📄 Rendering pages from config...")
    for page_config in pages:
        try:
            render_page(env, page_config, paths)
        except Exception as e:
            print(f"❌ Error rendering {page_config.get('name', 'unknown')}: {e}")

    print(f"\n📋 Converting TSV files from {paths['source']}...")
    process_dist_files(paths)

    if dashboard_data and not no_message:
        try:
            print("\n📬 Sending Telegram dashboard summary...")
            send_telegram_dashboard_summary(dashboard_data)
            print("✓ Telegram dashboard summary sent.")
        except Exception as e:
            print(f"❌ Failed to send Telegram dashboard summary: {e}")

    print("\n✅ Build completed!")
    print(f"   Output: {paths['output']}")

if __name__ == "__main__":
    build()
