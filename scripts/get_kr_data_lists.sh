AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
TODAY=$(date '+%Y%m%d')
DATA_PATH="output/data"

# 디렉토리 생성
mkdir -p "${DATA_PATH}"

# company list
COM_LIST_URL="http://comp.fnguide.com/XML/Market/CompanyList.txt"
curl -A "${AGENT}" -L "${COM_LIST_URL}" -o "${DATA_PATH}/companylist.json"

# Remove BOM (Byte Order Mark) if present
sed -i '1s/^\xEF\xBB\xBF//' "${DATA_PATH}/companylist.json"

# curl -A "${AGENT}" -L "${COM_LIST_URL}" -o "${DATA_PATH}/${TODAY}_CompanyList.json"
# cp "${DATA_PATH}/${TODAY}_CompanyList.json" "${DATA_PATH}/companylist.json"
