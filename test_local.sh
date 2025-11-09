#!/bin/bash
# Local Test Script
# 전체 데이터 수집 -> 빌드 -> 로컬 서버 실행

# 에러 발생시에도 계속 진행 (실패한 스크립트 추적)
set +e

# 실패한 스크립트 추적
failed_scripts=()

echo "🔍 Checking environment..."

# uv 설치 확인
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "   Install it from: https://github.com/astral-sh/uv"
    exit 1
fi
echo "   ✓ uv found"

# .env 파일 존재 확인
if [ ! -f ".env" ]; then
    echo "   ⚠️  Warning: .env file not found"
    echo "   Some scripts may fail without API keys (e.g., ECOS_KEY)"
else
    echo "   ✓ .env found"
fi

# Python 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed"
    exit 1
fi
echo "   ✓ python3 found"

echo ""
echo "🗑️  Cleaning old directories..."
if [ -d "output" ]; then
    rm -rf output
    echo "   Removed: output/"
fi
if [ -d "public" ]; then
    rm -rf public
    echo "   Removed: public/"
fi

echo ""
echo "📥 Running data collection scripts..."
echo ""

# 실행 순서 명시 (GitHub Actions 워크플로우와 동일)
scripts_order=(
    "scripts/get_data_origin.sh"
    "scripts/get_nv_price.py"
    "scripts/get_yh_price.py"
    "scripts/get_krx_price.py"
    "scripts/get_nv_data.py"
    "scripts/get_yh_data.py"
    "scripts/get_ecos_daily.py"
    "scripts/build_misc.py"
    "scripts/get_data_monthly.py"
    "scripts/get_ecos_monthly.py"
)

for script in "${scripts_order[@]}"; do
    if [ -f "$script" ]; then
        echo "▶️  Executing: $(basename $script)"

        # .sh 파일은 bash로, .py 파일은 uv run으로 실행
        if [[ "$script" == *.sh ]]; then
            bash "$script"
        else
            uv run "$script"
        fi

        # 실행 결과 확인
        if [ $? -ne 0 ]; then
            echo "   ⚠️  Warning: $script failed (continuing...)"
            failed_scripts+=("$(basename $script)")
        else
            echo "   ✓ Completed"
        fi
    else
        echo "   ⚠️  Warning: $script not found (skipping...)"
        failed_scripts+=("$(basename $script) [NOT FOUND]")
    fi
    echo ""
done

echo "🔨 Building the site..."
uv run build.py

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo ""
echo "✅ All tasks completed!"
echo ""

# 실패한 스크립트 요약
if [ ${#failed_scripts[@]} -gt 0 ]; then
    echo "⚠️  Summary of failed scripts:"
    for script in "${failed_scripts[@]}"; do
        echo "   - $script"
    done
    echo ""
    echo "   Note: The site was built with available data."
    echo ""
fi

