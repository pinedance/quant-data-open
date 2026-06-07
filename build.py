#!/usr/bin/env python3
"""
설정 파일 기반 정적 사이트 빌더
config.yaml만 수정하면 새 페이지가 자동으로 생성됩니다
"""

import json
import os
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader

from core.config import ConfigManager
from core.cons import MA_LONG_WINDOW as MIN_REQUIRED_DAYS
from core.dashboard_analyzer import DashboardAnalyzer
from core.message import send_telegram_dashboard_summary
from core.tIO import save_df_as_html_table

_config = ConfigManager()
BASE_DIR = Path(__file__).resolve().parent

def filter_dashboard_data(data, region):
    if not data:
        return None
    return {
        "market_regime": data["market_regime"],
        "trend_breakouts": {
            "up_breakouts":   [e for e in data["trend_breakouts"]["up_breakouts"]   if e["region"] == region],
            "down_breakouts": [e for e in data["trend_breakouts"]["down_breakouts"] if e["region"] == region],
        },
        "monthly_momentum":   [e for e in data["monthly_momentum"]   if e["region"] == region],
        "valuation_extremes": [e for e in data["valuation_extremes"] if e["region"] == region],
        "data_quality_status": [e for e in data["data_quality_status"] if e["region"] == region],
        "last_updated": data["last_updated"],
    }

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

    if template_type == 'table' or template_type == 'dashboard':
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

def process_dist_files(paths):
    source_dir = paths['source']
    output_dir = paths['output'] / paths['output_subdir']
    if not source_dir.exists():
        print(f"⚠️  Source directory not found: {source_dir}")
        return

    converted_count = 0
    failed_count = 0
    tasks = []
    for tsv_file in source_dir.rglob("*.tsv"):
        relative_path = tsv_file.relative_to(source_dir)
        html_path = output_dir / relative_path.with_suffix('.html')
        tasks.append((tsv_file, html_path))

    max_workers = os.cpu_count() or 4
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(convert_tsv_to_html, tsv, html): (tsv, html) for tsv, html in tasks}
        for future in futures:
            tsv_file, html_path = futures[future]
            try:
                if future.result():
                    converted_count += 1
                    print(f"✓ Converted {tsv_file.name} → {html_path.name}")
                else:
                    failed_count += 1
            except Exception as e:
                print(f"❌ Error converting {tsv_file.name}: {e}")
                failed_count += 1
    print(f"   Total: {converted_count} converted, {failed_count} failed")

def load_and_clean_dataset(paths):
    df_us_d = pd.read_csv(paths['source'] / "US/stocks/price/D/raw.tsv", sep='\t', index_col=0, header=0)
    df_us_m = pd.read_csv(paths['source'] / "US/stocks/price/M/raw-eom.tsv", sep='\t', index_col=0, header=0)
    df_us_hist = pd.read_csv(paths['source'] / "US/stocks/signals/MACD/M/raw-eom-histogram.tsv", sep='\t', index_col=0, header=0)
    
    df_kr_d = pd.read_csv(paths['source'] / "KR/stocks/price/D/raw.tsv", sep='\t', index_col=0, header=0)
    df_kr_m = pd.read_csv(paths['source'] / "KR/stocks/price/M/raw-eom.tsv", sep='\t', index_col=0, header=0)
    df_kr_hist = pd.read_csv(paths['source'] / "KR/stocks/signals/MACD/M/raw-eom-histogram.tsv", sep='\t', index_col=0, header=0)

    if len(df_us_d) < MIN_REQUIRED_DAYS or len(df_kr_d) < MIN_REQUIRED_DAYS:
        raise ValueError(f"Total price history is shorter than required window ({MIN_REQUIRED_DAYS} days).")

    clean_us_cols = df_us_d.iloc[-MIN_REQUIRED_DAYS:, :].dropna(axis=1).columns
    us_excluded = df_us_d.columns.difference(clean_us_cols)
    if not us_excluded.empty:
        print(f"⚠️  Excluding US tickers (insufficient/NaN in last {MIN_REQUIRED_DAYS} days): {list(us_excluded)}")
    df_us_d = df_us_d[clean_us_cols]
    df_us_m = df_us_m[clean_us_cols]
    df_us_hist = df_us_hist[clean_us_cols]

    clean_kr_cols = df_kr_d.iloc[-MIN_REQUIRED_DAYS:, :].dropna(axis=1).columns
    kr_excluded = df_kr_d.columns.difference(clean_kr_cols)
    if not kr_excluded.empty:
        clean_names = [c[1:] if c.startswith('A') else c for c in kr_excluded]
        print(f"⚠️  Excluding KR tickers (insufficient/NaN in last {MIN_REQUIRED_DAYS} days): {clean_names}")
    df_kr_d = df_kr_d[clean_kr_cols]
    df_kr_m = df_kr_m[clean_kr_cols]
    df_kr_hist = df_kr_hist[clean_kr_cols]

    return df_us_d, df_us_m, df_us_hist, df_kr_d, df_kr_m, df_kr_hist

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
    df_us_d, df_us_m, df_us_hist, df_kr_d, df_kr_m, df_kr_hist = load_and_clean_dataset(paths)
    
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
