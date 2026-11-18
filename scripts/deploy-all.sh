#!/usr/bin/env bash
# One entrypoint for the whole AWS deployment (V5, #320). It only calls the scripts and
# templates that already exist, in dependency order, and stops at the first failure.
#
#   scripts/deploy-all.sh --dry-run             # print the steps and which inputs are missing; no AWS calls
#   scripts/deploy-all.sh                       # deploy everything (needs AWS credentials)
#   scripts/deploy-all.sh --skip foundation     # re-deploy only what changed (comma separated)
#
# Steps: foundation, migrations, cognito, backend, smoke.
# Inputs (environment variables; none are secrets that belong in git):
#   FOUNDATION_PARAMS   JSON file of ParameterKey/ParameterValue (copy infra/v2/parameters.dev.example.json)
#   COGNITO_USERS_CSV   optional CSV of test accounts for deploy-v2-cognito.sh (git-ignored *.local.csv)
#   AWS_REGION, PROJECT_NAME, ENVIRONMENT, FOUNDATION_STACK   same defaults as the per-step scripts
# The frontend is deployed by Vercel from git, not by this script (see docs/v5-automation.md).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGION="${AWS_REGION:-ap-southeast-1}"
PROJECT_NAME="${PROJECT_NAME:-cs361-v2}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
FOUNDATION_STACK="${FOUNDATION_STACK:-cs361-v2-aws-foundation-dev}"
FOUNDATION_PARAMS="${FOUNDATION_PARAMS:-}"
COGNITO_USERS_CSV="${COGNITO_USERS_CSV:-}"
ALL_STEPS=(foundation migrations cognito backend smoke)

DRY_RUN=false
SKIP=","
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true ;;
    --skip) SKIP=",${2:?--skip needs a comma separated list},"; shift ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

for name in ${SKIP//,/ }; do
  [[ " ${ALL_STEPS[*]} " == *" ${name} "* ]] || { echo "unknown step in --skip: ${name}" >&2; exit 2; }
done

skipped() { [[ "${SKIP}" == *",$1,"* ]]; }
missing=0

# need <description> <condition-result>: report a missing input; in a real run it is fatal
need() {
  if [[ "$2" != "ok" ]]; then
    echo "  MISSING: $1"
    missing=$((missing + 1))
  else
    echo "  ok:      $1"
  fi
}

foundation_args() {
  python3 - "${FOUNDATION_PARAMS}" <<'PY'
import json, sys
for item in json.load(open(sys.argv[1])):
    print(f"{item['ParameterKey']}={item['ParameterValue']}")
PY
}

stack_output() {
  aws cloudformation describe-stacks --region "${REGION}" --stack-name "${FOUNDATION_STACK}" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue | [0]" --output text
}

run_step() {
  case "$1" in
    foundation)
      mapfile -t params < <(foundation_args)
      aws cloudformation deploy --region "${REGION}" --stack-name "${FOUNDATION_STACK}" \
        --template-file "${ROOT_DIR}/infra/v2/aws-foundation.yaml" \
        --capabilities CAPABILITY_NAMED_IAM --parameter-overrides "${params[@]}"
      ;;
    migrations)
      (cd "${ROOT_DIR}/backend" && uv run python -m scripts.apply_migrations \
        --cluster-arn "$(stack_output DBClusterArn)" --secret-arn "$(stack_output DBSecretArn)" \
        --database "$(stack_output DBName)")
      ;;
    cognito)
      "${ROOT_DIR}/scripts/deploy-v2-cognito.sh" ${COGNITO_USERS_CSV:+"${COGNITO_USERS_CSV}"}
      ;;
    backend) "${ROOT_DIR}/scripts/deploy-v2-backend-api.sh" ;;
    smoke) "${ROOT_DIR}/scripts/smoke-v2-backend-api.sh" ;;
  esac
}

describe_step() {
  case "$1" in
    foundation)
      echo "aws cloudformation deploy ${FOUNDATION_STACK}  <- infra/v2/aws-foundation.yaml (Aurora, S3, IAM)"
      need "FOUNDATION_PARAMS points to a JSON parameter file" "$([[ -f "${FOUNDATION_PARAMS}" ]] && echo ok || echo no)"
      ;;
    migrations)
      echo "python -m scripts.apply_migrations via RDS Data API  <- database/migrations/*.sql (only unapplied files run)"
      need "uv installed" "$(command -v uv >/dev/null && echo ok || echo no)"
      ;;
    cognito)
      echo "scripts/deploy-v2-cognito.sh ${COGNITO_USERS_CSV}  <- infra/v2/cognito.yaml"
      ;;
    backend)
      echo "scripts/deploy-v2-backend-api.sh  <- builds the Lambda zip, deploys infra/v2/backend-api.yaml"
      ;;
    smoke)
      echo "scripts/smoke-v2-backend-api.sh  <- read-only GET checks against the deployed API"
      ;;
  esac
}

echo "Region ${REGION}, project ${PROJECT_NAME}, environment ${ENVIRONMENT}"
if ${DRY_RUN}; then
  echo "DRY RUN: no AWS calls"
else
  command -v aws >/dev/null || { echo "aws CLI not found" >&2; exit 1; }
fi

index=0
for step in "${ALL_STEPS[@]}"; do
  index=$((index + 1))
  if skipped "${step}"; then
    echo "[${index}/${#ALL_STEPS[@]}] ${step}: skipped"
    continue
  fi
  echo "[${index}/${#ALL_STEPS[@]}] ${step}"
  if ${DRY_RUN}; then
    describe_step "${step}"
  else
    run_step "${step}"
  fi
done

if ${DRY_RUN}; then
  echo "Frontend: not deployed here; Vercel builds it from git (docs/v5-automation.md)"
  if (( missing > 0 )); then
    echo "${missing} input(s) missing; a real run would fail"
    exit 1
  fi
else
  echo "Deployed. Frontend: set the Vercel variables listed in frontend/README.md."
fi
