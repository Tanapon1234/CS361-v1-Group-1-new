#!/usr/bin/env bash
# Verify the V1 -> V2 full faculty migration (Issue #105) landed in Aurora
# correctly. Compares counts against docs/v2/v1-to-v2-mapping.md baseline:
#   faculty=22 education=65 research_interest=78 expertise=17 publications=7
set -euo pipefail

AWS_REGION="${AWS_REGION:-ap-southeast-1}"
DB_CLUSTER_ARN="${DB_CLUSTER_ARN:?Set DB_CLUSTER_ARN from the CloudFormation output.}"
DB_SECRET_ARN="${DB_SECRET_ARN:?Set DB_SECRET_ARN from the CloudFormation output.}"
DB_NAME="${DB_NAME:?Set DB_NAME from the CloudFormation output.}"

run_sql() {
  aws rds-data execute-statement \
    --region "$AWS_REGION" \
    --resource-arn "$DB_CLUSTER_ARN" \
    --secret-arn "$DB_SECRET_ARN" \
    --database "$DB_NAME" \
    --sql "$1" \
    --output table
}

echo "== import_batch row for this migration =="
run_sql "SELECT id, status, record_count, valid_count, error_count FROM import_batch WHERE id = 'imp_v1_public_faculty_full';"

echo
echo "== Row counts from this import batch =="
run_sql "
SELECT 'faculty' AS table_name, COUNT(*)::int AS row_count
  FROM faculty WHERE id LIKE 'fac_%'
UNION ALL
SELECT 'faculty_education', COUNT(*)::int FROM faculty_education fe
  JOIN faculty f ON f.id = fe.faculty_id WHERE f.id LIKE 'fac_%'
UNION ALL
SELECT 'faculty_interest (research)', COUNT(*)::int FROM faculty_interest
  WHERE interest_type = 'RESEARCH_INTEREST' AND faculty_id LIKE 'fac_%'
UNION ALL
SELECT 'faculty_interest (expertise)', COUNT(*)::int FROM faculty_interest
  WHERE interest_type = 'EXPERTISE' AND faculty_id LIKE 'fac_%'
UNION ALL
SELECT 'work_item (from this batch)', COUNT(*)::int FROM work_item
  WHERE import_batch_id = 'imp_v1_public_faculty_full'
UNION ALL
SELECT 'publication_detail (from this batch)', COUNT(*)::int FROM publication_detail pd
  JOIN work_item wi ON wi.id = pd.work_item_id WHERE wi.import_batch_id = 'imp_v1_public_faculty_full'
UNION ALL
SELECT 'faculty_work_item (from this batch)', COUNT(*)::int FROM faculty_work_item fwi
  JOIN work_item wi ON wi.id = fwi.work_item_id WHERE wi.import_batch_id = 'imp_v1_public_faculty_full'
UNION ALL
SELECT 'source_record (from this batch)', COUNT(*)::int FROM source_record
  WHERE import_batch_id = 'imp_v1_public_faculty_full'
ORDER BY table_name;
"

echo
echo "Expected baseline (docs/v2/v1-to-v2-mapping.md): faculty=22 education=65 research_interest=78 expertise=17 publications=7"

echo
echo "== Public slug spot-check =="
run_sql "
SELECT id, public_slug, name_th, status, visibility
FROM faculty
WHERE public_slug IN ('prapaporn-rattanatamrong', 'kasidit-chanchio', 'denduang-pradubsuwun')
ORDER BY public_slug;
"

echo
echo "== V1 compatibility: every faculty is PUBLIC/ACTIVE =="
run_sql "
SELECT visibility, status, COUNT(*)::int AS count
FROM faculty
WHERE id LIKE 'fac_%'
GROUP BY visibility, status
ORDER BY visibility, status;
"

echo
echo "Verification complete."
