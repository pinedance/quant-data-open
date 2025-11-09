#!/usr/bin/env python3
"""
중앙화된 경로 관리
모든 스크립트에서 이 모듈을 import하여 일관된 경로 사용
"""

from pathlib import Path

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).parent.parent

# 데이터 출력 경로
OUTPUT_ROOT = PROJECT_ROOT / "output"
OUTPUT_DATA = OUTPUT_ROOT / "data"

# 서브 디렉토리
OUTPUT_NV = OUTPUT_ROOT / "NV"
OUTPUT_YH = OUTPUT_ROOT / "YH"
OUTPUT_KRX = OUTPUT_ROOT / "KRX"
OUTPUT_ECOS = OUTPUT_ROOT / "ECOS"
OUTPUT_M = OUTPUT_ROOT / "M"

# 빌드 결과 경로
PUBLIC_ROOT = PROJECT_ROOT / "public"
PUBLIC_DIST = PUBLIC_ROOT / "dist"


def ensure_output_dirs():
    """
    필요한 모든 출력 디렉토리를 생성
    스크립트 실행 전에 호출하면 안전
    """
    dirs = [
        OUTPUT_ROOT,
        OUTPUT_DATA,
        OUTPUT_NV,
        OUTPUT_YH,
        OUTPUT_KRX,
        OUTPUT_ECOS,
        OUTPUT_M,
    ]

    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)


def get_data_path(filename):
    """
    데이터 파일 경로 반환
    예: get_data_path("companylist.json") -> output/data/companylist.json
    """
    return OUTPUT_DATA / filename


def get_output_path(subdir, filename):
    """
    서브디렉토리의 출력 파일 경로 반환
    예: get_output_path("NV", "etf-price-selected.html")
    """
    base_path = OUTPUT_ROOT / subdir
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path / filename


if __name__ == "__main__":
    # 테스트: 모든 디렉토리 생성
    ensure_output_dirs()
    print("✓ All output directories created")
    print(f"  OUTPUT_ROOT: {OUTPUT_ROOT}")
    print(f"  OUTPUT_DATA: {OUTPUT_DATA}")
    print(f"  OUTPUT_NV: {OUTPUT_NV}")
    print(f"  OUTPUT_YH: {OUTPUT_YH}")
    print(f"  OUTPUT_KRX: {OUTPUT_KRX}")
    print(f"  OUTPUT_ECOS: {OUTPUT_ECOS}")
    print(f"  OUTPUT_M: {OUTPUT_M}")
