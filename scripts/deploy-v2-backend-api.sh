#!/usr/bin/env bash
# Package backend/ for AWS Lambda and deploy infra/v2/backend-api.yaml.
#
#   scripts/deploy-v2-backend-api.sh --build-only   # just build build/v2/backend-api/backend-api.zip
#   scripts/deploy-v2-backend-api.sh                # build, upload, deploy (needs AWS credentials)
#
# Network and database values are looked up from the Aurora cluster of the foundation stack;
# set any of them in the environment to override (see the variables below).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGION="${AWS_REGION:-ap-southeast-1}"
PROJECT_NAME="${PROJECT_NAME:-cs361-v2}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
FOUNDATION_STACK="${FOUNDATION_STACK:-cs361-v2-aws-foundation-dev}"
API_STACK="${API_STACK:-cs361-v2-backend-api-dev}"
BUILD_DIR="${ROOT_DIR}/build/v2/backend-api"
ZIP_FILE="${BUILD_DIR}/backend-api.zip"
GIT_REVISION="$(git -C "${ROOT_DIR}" rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)"

build() {
  rm -rf "${BUILD_DIR}/package"
  mkdir -p "${BUILD_DIR}/package"
  (cd "${ROOT_DIR}/backend" && uv export --no-dev --no-hashes --no-emit-project --format requirements-txt \
    > "${BUILD_DIR}/requirements.txt")
  # Linux wheels for the Lambda runtime (python3.12, x86_64), whatever machine builds this
  uv pip install --quiet --target "${BUILD_DIR}/package" \
    --python-platform x86_64-manylinux2014 --python-version 3.12 --only-binary :all: \
    -r "${BUILD_DIR}/requirements.txt"
  cp -R "${ROOT_DIR}/backend/app" "${BUILD_DIR}/package/app"
  find "${BUILD_DIR}/package" -name "__pycache__" -type d -prune -exec rm -rf {} +
  rm -f "${ZIP_FILE}"
  (cd "${BUILD_DIR}/package" && zip -qr9 "${ZIP_FILE}" .)
  echo "Built ${ZIP_FILE} ($(du -h "${ZIP_FILE}" | cut -f1) zipped, $(du -sh "${BUILD_DIR}/package" | cut -f1) unzipped; Lambda limit 250M)"
}

stack_output() {
  aws cloudformation describe-stacks --region "${REGION}" --stack-name "${FOUNDATION_STACK}" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue | [0]" --output text
}

build
if [[ "${1:-}" == "--build-only" ]]; then
  exit 0
fi

DB_CLUSTER_ID="${DB_CLUSTER_ID:-$(stack_output DBClusterIdentifier)}"
DB_SECRET_ARN="${DB_SECRET_ARN:-$(stack_output DBSecretArn)}"
DB_NAME="${DB_NAME:-$(stack_output DBName)}"
DATA_BUCKET_NAME="${DATA_BUCKET_NAME:-$(stack_output DataBucketName)}"
CODE_S3_BUCKET="${CODE_S3_BUCKET:-${DATA_BUCKET_NAME}}"
CODE_S3_KEY="${CODE_S3_KEY:-lambda-artifacts/v2-backend/${PROJECT_NAME}-${ENVIRONMENT}-backend-${GIT_REVISION}.zip}"

cluster() {
  aws rds describe-db-clusters --region "${REGION}" --db-cluster-identifier "${DB_CLUSTER_ID}" \
    --query "DBClusters[0].$1" --output text
}
DB_HOST="${DB_HOST:-$(cluster Endpoint)}"
DB_SECURITY_GROUP_ID="${DB_SECURITY_GROUP_ID:-$(cluster 'VpcSecurityGroups[0].VpcSecurityGroupId')}"
DB_SUBNET_GROUP="$(cluster DBSubnetGroup)"
VPC_ID="${VPC_ID:-$(aws rds describe-db-subnet-groups --region "${REGION}" \
  --db-subnet-group-name "${DB_SUBNET_GROUP}" --query 'DBSubnetGroups[0].VpcId' --output text)}"
PRIVATE_SUBNET_IDS="${PRIVATE_SUBNET_IDS:-$(aws rds describe-db-subnet-groups --region "${REGION}" \
  --db-subnet-group-name "${DB_SUBNET_GROUP}" --query 'DBSubnetGroups[0].Subnets[].SubnetIdentifier' \
  --output text | tr '\t' ',')}"
PRIVATE_ROUTE_TABLE_IDS="${PRIVATE_ROUTE_TABLE_IDS:-$(aws ec2 describe-route-tables --region "${REGION}" \
  --filters "Name=association.subnet-id,Values=${PRIVATE_SUBNET_IDS}" \
  --query 'RouteTables[].RouteTableId' --output text | tr '\t' ',')}"
CORS_ALLOW_ORIGINS="${CORS_ALLOW_ORIGINS:-[\"http://localhost:3000\"]}"
CREATE_VPC_ENDPOINTS="${CREATE_VPC_ENDPOINTS:-true}"
DEV_AUTH_HEADER_ENABLED="${DEV_AUTH_HEADER_ENABLED:-true}"

aws s3 cp "${ZIP_FILE}" "s3://${CODE_S3_BUCKET}/${CODE_S3_KEY}" --region "${REGION}"

aws cloudformation deploy \
  --region "${REGION}" \
  --stack-name "${API_STACK}" \
  --template-file "${ROOT_DIR}/infra/v2/backend-api.yaml" \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    ProjectName="${PROJECT_NAME}" \
    Environment="${ENVIRONMENT}" \
    CodeS3Bucket="${CODE_S3_BUCKET}" \
    CodeS3Key="${CODE_S3_KEY}" \
    VpcId="${VPC_ID}" \
    PrivateSubnetIds="${PRIVATE_SUBNET_IDS}" \
    PrivateRouteTableIds="${PRIVATE_ROUTE_TABLE_IDS}" \
    DBSecurityGroupId="${DB_SECURITY_GROUP_ID}" \
    DBHost="${DB_HOST}" \
    DBName="${DB_NAME}" \
    DBSecretArn="${DB_SECRET_ARN}" \
    DataBucketName="${DATA_BUCKET_NAME}" \
    CorsAllowOrigins="${CORS_ALLOW_ORIGINS}" \
    CreateVpcEndpoints="${CREATE_VPC_ENDPOINTS}" \
    DevAuthHeaderEnabled="${DEV_AUTH_HEADER_ENABLED}"

ENDPOINT="$(aws cloudformation describe-stacks --region "${REGION}" --stack-name "${API_STACK}" \
  --query "Stacks[0].Outputs[?OutputKey=='BackendApiEndpoint'].OutputValue | [0]" --output text)"
echo "Backend API: ${ENDPOINT}"
curl -fsS "${ENDPOINT}/health/ready" && echo
