#!/bin/bash
AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
DATA_PATH="output/KR/data"

# 디렉토리 생성
mkdir -p "${DATA_PATH}"

# company list
COM_LIST_URL="http://comp.fnguide.com/XML/Market/CompanyList.txt"
curl -A "${AGENT}" -L "${COM_LIST_URL}" -o "${DATA_PATH}/stocklist.json"

# Remove BOM (Byte Order Mark) if present
sed -i '1s/^\xEF\xBB\xBF//' "${DATA_PATH}/stocklist.json"
