#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-ap-southeast-1}"
DB_CLUSTER_ARN="${DB_CLUSTER_ARN:?Set DB_CLUSTER_ARN from the CloudFormation output.}"
DB_SECRET_ARN="${DB_SECRET_ARN:?Set DB_SECRET_ARN from the CloudFormation output.}"
DB_NAME="${DB_NAME:?Set DB_NAME from the CloudFormation output.}"

if ! command -v aws >/dev/null 2>&1; then
  echo "ERROR: aws CLI was not found. Install AWS CLI v2 and configure credentials first." >&2
  exit 1
fi

echo "Checking AWS caller identity..."
aws sts get-caller-identity \
  --region "$AWS_REGION" \
  --query '{Account:Account,Arn:Arn}' \
  --output table

echo
echo "Running SELECT 1 through RDS Data API..."
aws rds-data execute-statement \
  --region "$AWS_REGION" \
  --resource-arn "$DB_CLUSTER_ARN" \
  --secret-arn "$DB_SECRET_ARN" \
  --database "$DB_NAME" \
  --sql "SELECT 1 AS ok;" \
  --query 'records[0][0].longValue' \
  --output text

echo
echo "Running identity checks through RDS Data API..."
aws rds-data execute-statement \
  --region "$AWS_REGION" \
  --resource-arn "$DB_CLUSTER_ARN" \
  --secret-arn "$DB_SECRET_ARN" \
  --database "$DB_NAME" \
  --sql "SELECT current_database() AS database_name, current_user AS user_name;" \
  --output table

echo
echo "V2 AWS foundation Data API verification completed."
