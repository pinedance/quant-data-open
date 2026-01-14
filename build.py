#!/usr/bin/env python3
"""
설정 파일 기반 정적 사이트 빌더
config/pages.yaml만 수정하면 새 페이지가 자동으로 생성됩니다
"""

import json
import shutil
import yaml
import pandas as pd
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# 기본 경로
BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"
PAGES_CONFIG = CONFIG_DIR / "pages.yaml"
PATHS_CONFIG = CONFIG_DIR / "paths.yaml"


def load_json_data(filepath):
    """JSON 파일 로드"""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        return json.load(f)


def load_pages_config():
    """페이지 설정 파일 로드"""
    if not PAGES_CONFIG.exists():
        print(f"⚠️  설정 파일이 없습니다: {PAGES_CONFIG}")
        return {"pages": []}

    with open(PAGES_CONFIG, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_paths_config():
    """경로 설정 파일 로드"""
    if not PATHS_CONFIG.exists():
        print(f"⚠️  경로 설정 파일이 없습니다: {PATHS_CONFIG}")
        return {}

    with open(PATHS_CONFIG, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_paths():
    """설정에서 경로 정보 추출"""
    paths = load_paths_config()

    # 기본값 설정
    defaults = {
        'templates': 'templates',
        'data': 'output/data',
        'source': 'output',
        'output': 'public',
        'output_subdir': 'dist'
    }

    # 병합
    for key, default in defaults.items():
        if key not in paths:
            paths[key] = default

    # Path 객체로 변환
    return {
        'templates': BASE_DIR / paths['templates'],
        'data': BASE_DIR / paths['data'],
        'source': BASE_DIR / paths['source'],
        'output': BASE_DIR / paths['output'],
        'output_subdir': paths['output_subdir']
    }


def ensure_dir(directory):
    """디렉토리 생성 (존재하지 않을 경우)"""
    Path(directory).mkdir(parents=True, exist_ok=True)


def convert_tsv_to_html(tsv_path, html_path):
    """TSV 파일을 HTML 테이블로 변환"""
    try:
        df = pd.read_csv(tsv_path, sep='\t', index_col=0, header=0)
        html_table = df.to_html(na_rep='')

        ensure_dir(html_path.parent)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_table)

        return True
    except Exception as e:
        print(f"⚠️  Error converting {tsv_path.name}: {e}")
        return False


def render_page(env, page_config, paths):
    """설정 기반으로 페이지 렌더링"""
    name = page_config['name']
    title = page_config['title']
    data_file = page_config['data_file']
    template_type = page_config.get('template', 'table')
    data_key = page_config.get('data_key')
    columns = page_config.get('columns', [])

    # 데이터 로드
    data_path = paths['data'] / data_file
    if not data_path.exists():
        print(f"⚠️  데이터 파일이 없습니다: {data_path}")
        return

    full_data = load_json_data(data_path)

    # 데이터 키가 지정된 경우 해당 키의 값만 사용
    if data_key:
        data = full_data.get(data_key, [])
    else:
        data = full_data

    # HTML 페이지 생성
    if template_type == 'table':
        template_name = 'generic_table.html.j2'
        layout_name = 'data.html'
        output_path = paths['output'] / paths['output_subdir'] / f'{name}.html'

        page_template = env.get_template(f'pages/{template_name}')
        content = page_template.render(data=data, columns=columns)

        layout_template = env.get_template(f'layouts/{layout_name}')
        html = layout_template.render(content=content, title=title)

        ensure_dir(output_path.parent)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✓ {output_path}")

    # JSON 파일 생성
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
    """TSV 파일을 HTML로 변환하여 output으로 복사"""
    source_dir = paths['source']
    output_dir = paths['output'] / paths['output_subdir']

    if not source_dir.exists():
        print(f"⚠️  Source directory not found: {source_dir}")
        return

    converted_count = 0
    failed_count = 0

    # TSV 파일들을 HTML로 변환
    for tsv_file in source_dir.rglob("*.tsv"):
        relative_path = tsv_file.relative_to(source_dir)
        html_path = output_dir / relative_path.with_suffix('.html')

        if convert_tsv_to_html(tsv_file, html_path):
            converted_count += 1
            print(f"✓ Converted {tsv_file.name} → {html_path.name}")
        else:
            failed_count += 1

    print(f"   Total: {converted_count} converted, {failed_count} failed")


def build():
    """전체 사이트 빌드"""
    print("🔨 Building site with Jinja2...")

    # 설정 파일 로드
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

    # 출력 디렉토리 정리
    if paths['output'].exists():
        shutil.rmtree(paths['output'])
    ensure_dir(paths['output'])

    # Jinja2 환경 설정
    env = Environment(
        loader=FileSystemLoader(paths['templates']),
        autoescape=False
    )

    # 한글을 제대로 표시하기 위한 커스텀 tojson 필터
    def tojson_filter(value):
        return json.dumps(value, ensure_ascii=False, indent=None, separators=(',', ': '))

    env.filters['tojson'] = tojson_filter

    # 설정 기반 페이지 생성
    print("\n📄 Rendering pages from config...")
    for page_config in pages:
        try:
            render_page(env, page_config, paths)
        except Exception as e:
            print(f"❌ Error rendering {page_config.get('name', 'unknown')}: {e}")

    # source 디렉토리의 TSV 파일들을 HTML로 변환
    print(f"\n📋 Converting TSV files from {paths['source']}...")
    process_dist_files(paths)

    print("\n✅ Build completed!")
    print(f"   Output: {paths['output']}")


if __name__ == "__main__":
    build()
