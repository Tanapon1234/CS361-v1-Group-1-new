#!/usr/bin/env bash
# Deploy the Cognito user pool (infra/v2/cognito.yaml) and create test accounts.
#
#   scripts/deploy-v2-cognito.sh                                  # stack only
#   scripts/deploy-v2-cognito.sh infra/v2/cognito-users.local.csv  # stack + accounts
#
# CSV columns: email,group,password (group empty = plain lecturer). No email is sent; the
# password is set as permanent so demo accounts can sign in right away. Never commit real
# passwords: copy cognito-users.example.csv to a *.local.csv (git-ignored) first.
# Each account still needs a lecturer record with the same email (POST /api/v2/lecturers);
# the backend links them on first sign-in.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGION="${AWS_REGION:-ap-southeast-1}"
PROJECT_NAME="${PROJECT_NAME:-cs361-v2}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
STACK="${COGNITO_STACK:-cs361-v2-cognito-dev}"

aws cloudformation deploy --region "${REGION}" --stack-name "${STACK}" \
  --template-file "${ROOT_DIR}/infra/v2/cognito.yaml" \
  --parameter-overrides ProjectName="${PROJECT_NAME}" Environment="${ENVIRONMENT}"

output() {
  aws cloudformation describe-stacks --region "${REGION}" --stack-name "${STACK}" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue | [0]" --output text
}
POOL_ID="$(output UserPoolId)"
CLIENT_ID="$(output WebClientId)"

if [[ -n "${1:-}" ]]; then
  tail -n +2 "$1" | while IFS=, read -r email group password; do
    [[ -z "${email}" ]] && continue
    if ! aws cognito-idp admin-get-user --region "${REGION}" --user-pool-id "${POOL_ID}" \
      --username "${email}" >/dev/null 2>&1; then
      aws cognito-idp admin-create-user --region "${REGION}" --user-pool-id "${POOL_ID}" \
        --username "${email}" --message-action SUPPRESS \
        --user-attributes Name=email,Value="${email}" Name=email_verified,Value=true >/dev/null
    fi
    aws cognito-idp admin-set-user-password --region "${REGION}" --user-pool-id "${POOL_ID}" \
      --username "${email}" --password "${password}" --permanent
    if [[ -n "${group}" ]]; then
      aws cognito-idp admin-add-user-to-group --region "${REGION}" --user-pool-id "${POOL_ID}" \
        --username "${email}" --group-name "${group}"
    fi
    echo "account ${email} ${group:-lecturer}"
  done
fi

cat <<OUT
COGNITO_REGION=${REGION}
COGNITO_USER_POOL_ID=${POOL_ID}
COGNITO_CLIENT_ID=${CLIENT_ID}
Set these on the backend Lambda (scripts/deploy-v2-backend-api.sh) and in Vercel.
OUT
