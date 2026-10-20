#!/usr/bin/env bash
# Smoke test of the deployed FastAPI backend (#201).
#
#   scripts/smoke-v2-backend-api.sh                         # URL from the backend-api stack
#   API_BASE_URL=http://localhost:8000 scripts/smoke-v2-backend-api.sh
#   scripts/smoke-v2-backend-api.sh --save                  # also write evidence/v2/backend-api/
#
# Read-only: only GET requests. Expects the demo data (backend/scripts/seed_workload_demo.py).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGION="${AWS_REGION:-ap-southeast-1}"
API_STACK="${API_STACK:-cs361-v2-backend-api-dev}"

if [[ -z "${API_BASE_URL:-}" ]]; then
  API_BASE_URL="$(aws cloudformation describe-stacks --region "${REGION}" --stack-name "${API_STACK}" \
    --query "Stacks[0].Outputs[?OutputKey=='BackendApiEndpoint'].OutputValue | [0]" --output text)"
fi

run() {
  python3 - "${API_BASE_URL%/}" <<'PY'
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

BASE = sys.argv[1]
failures = 0


def get(path):
    try:
        with urllib.request.urlopen(f"{BASE}{path}", timeout=30) as response:
            return response.status, response.headers.get("content-type", ""), json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, error.headers.get("content-type", ""), json.loads(error.read() or b"null")


def check(name, ok, detail=""):
    global failures
    failures += not ok
    print(f"{'PASS' if ok else 'FAIL'} {name}" + (f"  ({detail})" if detail else ""))


print(f"Backend smoke test {BASE} at {datetime.now(timezone.utc).isoformat(timespec='seconds')}")

status, _, body = get("/health")
check("GET /health", status == 200 and body == {"status": "ok"}, f"{status}")
status, _, body = get("/health/ready")
check("GET /health/ready (database reachable)", status == 200, f"{status} {body}")

status, _, lecturers = get("/api/v2/lecturers?limit=100")
total = lecturers.get("meta", {}).get("total") if status == 200 else None
check("GET /api/v2/lecturers", status == 200 and bool(total), f"{status} total={total}")

for path in ("/api/v2/rubric-versions", "/api/v2/rounds", "/api/v2/departments",
             "/api/v2/publications", "/api/v2/expertise", "/api/v2/research-interests"):
    status, _, body = get(path)
    check(f"GET {path}", status == 200 and "items" in body, f"{status} total={body.get('meta', {}).get('total')}")

main = next((l for l in lecturers.get("items", []) if l["email"] == "rattanat@tu.ac.th"), None)
check("demo lecturer rattanat@tu.ac.th exists", main is not None)
if main:
    work_path = f"/api/v2/lecturers/{main['lecturer_id']}/work?academic_year=2567&category=2"
    status, _, work = get(work_path)
    years = {e["academic_year"] for g in work.get("categories", []) for e in g["entries"]}
    check("GET lecturer work 2567 / category 2 (TC2)",
          status == 200 and work["total"] > 0 and years == {2567}
          and [g["code"] for g in work["categories"]] == ["2"],
          f"{status} total={work.get('total')} years={sorted(years)}")

status, content_type, body = get("/api/v2/lecturers/00000000-0000-0000-0000-000000000000")
check("unknown lecturer is 404 problem+json",
      status == 404 and content_type.startswith("application/problem+json"), f"{status}")
status, _, _ = get("/api/v2/lecturers/00000000-0000-0000-0000-000000000000/work?academic_year=67")
check("invalid academic_year is 422", status == 422, f"{status}")

print(f"{'All checks passed' if not failures else f'{failures} check(s) failed'}")
sys.exit(1 if failures else 0)
PY
}

if [[ "${1:-}" == "--save" ]]; then
  OUT_DIR="${ROOT_DIR}/evidence/v2/backend-api"
  mkdir -p "${OUT_DIR}"
  OUT_FILE="${OUT_DIR}/smoke-$(date +%Y%m%d-%H%M%S).txt"
  run | tee "${OUT_FILE}"
  echo "Saved ${OUT_FILE}"
else
  run
fi
