#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGION="${AWS_REGION:-ap-southeast-1}"
PROJECT_NAME="${PROJECT_NAME:-cs361-v2}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
FOUNDATION_STACK="${FOUNDATION_STACK:-cs361-v2-aws-foundation-dev}"
API_STACK="${API_STACK:-cs361-v2-master-data-api-dev}"
ARTIFACT_PREFIX="${ARTIFACT_PREFIX:-lambda-artifacts/v2-query}"
BUILD_DIR="${ROOT_DIR}/build/v2/query-api"
ZIP_FILE="${BUILD_DIR}/query-api.zip"
GIT_REVISION="$(git -C "${ROOT_DIR}" rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)"

export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/tmp/codex-pycache}"

stack_output() {
  local key="$1"
  aws cloudformation describe-stacks \
    --region "${REGION}" \
    --stack-name "${FOUNDATION_STACK}" \
    --query "Stacks[0].Outputs[?OutputKey=='${key}'].OutputValue | [0]" \
    --output text
}

DB_CLUSTER_ARN="${DB_CLUSTER_ARN:-$(stack_output DBClusterArn)}"
DB_SECRET_ARN="${DB_SECRET_ARN:-$(stack_output DBSecretArn)}"
DB_NAME="${DB_NAME:-$(stack_output DBName)}"
QUERY_LAMBDA_ROLE_ARN="${QUERY_LAMBDA_ROLE_ARN:-$(stack_output QueryLambdaRoleArn)}"
CODE_S3_BUCKET="${CODE_S3_BUCKET:-$(stack_output DataBucketName)}"
CODE_S3_KEY="${CODE_S3_KEY:-${ARTIFACT_PREFIX}/${PROJECT_NAME}-${ENVIRONMENT}-query-${GIT_REVISION}.zip}"

mkdir -p "${BUILD_DIR}"

python3 -m compileall -q "${ROOT_DIR}/backend/v2/query"
python3 - "${ROOT_DIR}" "${ZIP_FILE}" <<'PY'
import pathlib
import sys
import zipfile

root = pathlib.Path(sys.argv[1])
zip_path = pathlib.Path(sys.argv[2])
source_dir = root / "backend" / "v2" / "query"

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as package:
    for path in source_dir.glob("*.py"):
        if path.name.startswith("test_") or path.name == "__init__.py":
            continue
        package.write(path, path.name)
PY

aws s3 cp "${ZIP_FILE}" "s3://${CODE_S3_BUCKET}/${CODE_S3_KEY}" --region "${REGION}"

aws cloudformation deploy \
  --region "${REGION}" \
  --stack-name "${API_STACK}" \
  --template-file "${ROOT_DIR}/infra/v2/master-data-api.yaml" \
  --parameter-overrides \
    ProjectName="${PROJECT_NAME}" \
    Environment="${ENVIRONMENT}" \
    CodeS3Bucket="${CODE_S3_BUCKET}" \
    CodeS3Key="${CODE_S3_KEY}" \
    DBClusterArn="${DB_CLUSTER_ARN}" \
    DBSecretArn="${DB_SECRET_ARN}" \
    DBName="${DB_NAME}" \
    QueryLambdaRoleArn="${QUERY_LAMBDA_ROLE_ARN}" \
  --capabilities CAPABILITY_NAMED_IAM

aws cloudformation describe-stacks \
  --region "${REGION}" \
  --stack-name "${API_STACK}" \
  --query 'Stacks[0].Outputs' \
  --output table
