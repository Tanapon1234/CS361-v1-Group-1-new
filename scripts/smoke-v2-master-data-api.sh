#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-ap-southeast-1}"
API_STACK="${API_STACK:-cs361-v2-master-data-api-dev}"

if [[ -z "${API_BASE_URL:-}" ]]; then
  API_BASE_URL="$(
    aws cloudformation describe-stacks \
      --region "${REGION}" \
      --stack-name "${API_STACK}" \
      --query "Stacks[0].Outputs[?OutputKey=='MasterDataApiEndpoint'].OutputValue | [0]" \
      --output text
  )"
fi

API_BASE_URL="${API_BASE_URL%/}"

check_json_count() {
  local path="$1"
  python3 - "${API_BASE_URL}" "$path" <<'PY'
import json
import sys
import urllib.request

base_url = sys.argv[1].rstrip("/")
path = sys.argv[2]
url = f"{base_url}{path}"

with urllib.request.urlopen(url, timeout=20) as response:
    body = json.loads(response.read().decode("utf-8"))
    status = response.status

if status != 200:
    raise SystemExit(f"{path}: expected 200, got {status}")
if "items" not in body or "meta" not in body or "count" not in body["meta"]:
    raise SystemExit(f"{path}: response envelope is invalid")
print(f"PASS {path} count={body['meta']['count']}")
PY
}

check_invalid_category() {
  python3 - "${API_BASE_URL}" <<'PY'
import json
import sys
import urllib.error
import urllib.request

url = f"{sys.argv[1].rstrip('/')}/api/v2/work-types?category=UNKNOWN"

try:
    urllib.request.urlopen(url, timeout=20)
except urllib.error.HTTPError as error:
    body = json.loads(error.read().decode("utf-8"))
    if error.code == 400 and body.get("error", {}).get("code") == "INVALID_QUERY":
        print("PASS /api/v2/work-types?category=UNKNOWN returned 400 INVALID_QUERY")
        raise SystemExit(0)
    raise

raise SystemExit("expected invalid category request to fail with 400")
PY
}

check_json_count "/api/v2/academic-periods"
check_json_count "/api/v2/evaluation-periods"
check_json_count "/api/v2/work-categories"
check_json_count "/api/v2/work-types"
check_json_count "/api/v2/faculties"
check_invalid_category
