#!/usr/bin/env bash
# Real invoke against the deployed Lambda + real S3 serving/* objects.
# Required before closing the task: at least List + Detail.
#
# Usage:
#   FUNCTION_NAME=cs361-faculty-api-dev FACULTY_ID=eng ./scripts/smoke_test.sh
set -euo pipefail

FUNCTION_NAME="${FUNCTION_NAME:?set FUNCTION_NAME}"
FACULTY_ID="${FACULTY_ID:-eng}"
REGION="${AWS_REGION:-ap-southeast-1}"
EVENTS_DIR="$(dirname "$0")/../lambda/events"
OUT_DIR="$(mktemp -d)"

invoke() {
  local label="$1" payload="$2" expected="$3"
  echo "--- ${label} (expect HTTP ${expected})"
  aws lambda invoke \
    --region "$REGION" \
    --function-name "$FUNCTION_NAME" \
    --cli-binary-format raw-in-base64-out \
    --payload "$payload" \
    "$OUT_DIR/${label}.json" >/dev/null
  python3 -c "
import json,sys
r=json.load(open('$OUT_DIR/${label}.json'))
status=r.get('statusCode')
print('status:', status)
print('body  :', r.get('body','')[:400])
sys.exit(0 if status == $expected else 1)
"
}

# 1. List
invoke list "$(cat "$EVENTS_DIR/list.json")" 200

# 2. Detail
DETAIL_PAYLOAD=$(python3 -c "
import json
e=json.load(open('$EVENTS_DIR/detail.json'))
e['path']='/api/v1/faculties/$FACULTY_ID'
e['pathParameters']={'id':'$FACULTY_ID'}
print(json.dumps(e))
")
invoke detail "$DETAIL_PAYLOAD" 200

# 3. Unknown faculty -> 404
NOT_FOUND_PAYLOAD=$(python3 -c "
import json
e=json.load(open('$EVENTS_DIR/detail.json'))
e['path']='/api/v1/faculties/definitely-not-a-faculty'
e['pathParameters']={'id':'definitely-not-a-faculty'}
print(json.dumps(e))
")
invoke not_found "$NOT_FOUND_PAYLOAD" 404

# 4. Invalid id -> 400
invoke invalid_id "$(cat "$EVENTS_DIR/detail-invalid.json")" 400

# 5. Unsupported method -> 405
invoke method_not_allowed "$(cat "$EVENTS_DIR/method-not-allowed.json")" 405

echo
echo "All smoke checks passed. Raw responses: $OUT_DIR"
