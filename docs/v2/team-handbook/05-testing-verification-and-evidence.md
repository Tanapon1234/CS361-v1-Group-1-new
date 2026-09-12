# Testing, Verification, And Evidence Guide

ไฟล์นี้อธิบายวิธีทดสอบและเก็บหลักฐานสำหรับปิดการ์ด V2

หลักสำคัญ: V2 issue card ต้องปิดด้วยหลักฐานจากระบบจริง ไม่ใช่แค่ “โค้ด compile ได้”

## Verification Levels

ใช้ verification 4 ชั้น:

1. Local unit/contract tests
2. Build/static checks
3. AWS deploy/smoke tests
4. Evidence docs/GitHub comment

แต่ละการ์ดไม่จำเป็นต้องมีทุกอย่างเท่ากัน แต่ production API/Admin/UI cards ต้องมี smoke/evidence จาก AWS จริง

## Current Known Good Checks

Backend #64 tests:

```bash
python3 -m unittest backend.v2.query.test_master_data
```

Expected:

```text
Ran 8 tests - OK
```

Frontend local V2 master data contract test:

```bash
cd frontend
npm run test:v2:master-data
```

Expected:

```text
9 tests passed
```

Master Data API AWS smoke:

```bash
AWS_REGION=ap-southeast-1 \
API_STACK=cs361-v2-master-data-api-dev \
scripts/smoke-v2-master-data-api.sh
```

Expected after Aurora is awake:

```text
PASS /api/v2/academic-periods count=5
PASS /api/v2/evaluation-periods count=3
PASS /api/v2/work-categories count=6
PASS /api/v2/work-types count=26
PASS /api/v2/faculties count=3
PASS /api/v2/work-types?category=UNKNOWN returned 400 INVALID_QUERY
```

## What To Test By Card Type

### Public Read API Cards

Examples: #64, #66, #67, #68

Test:

- Lambda/service unit tests
- query validation
- empty result
- invalid query returns standard error shape
- public visibility enforcement
- success response envelope
- deployed API Gateway route
- CloudWatch log exists
- Aurora data is read through RDS Data API

Evidence:

- API endpoint
- Lambda name
- route list
- smoke output
- CloudWatch log group
- sample response with secrets redacted
- commit hash

### Admin API Cards

Examples: #69, #70, #71

Test:

- unauthenticated request returns `401`
- authenticated non-admin returns `403`
- admin success path works
- invalid payload returns `400`
- missing entity returns `404`
- transaction rollback works
- mutation writes Aurora
- `audit_event` inserted

Evidence:

- Cognito resource id/name
- protected API route
- Lambda name
- Aurora verification query result
- CloudWatch logs
- auth/audit table checks

### Frontend Public UI Cards

Examples: #72, #73, #74, #75

Test:

- page opens
- loading state appears appropriately
- filter controls load from real #64 endpoint
- list results load from real #66 endpoint
- detail page loads from real #68 endpoint
- empty/error/404 states work
- URL query state behaves predictably
- restricted/internal records do not appear in public UI

Evidence:

- deployed frontend URL
- API Gateway base URL used
- screenshots if useful
- manual QA matrix
- console/network errors checked

### Admin UI Cards

Examples: #76, #77, #78, #79

Test:

- login page opens
- Cognito login works with admin user
- protected pages redirect unauthenticated users
- admin list loads from protected API
- create/edit form submits to real API
- validation errors map to fields
- soft-delete hides record from public path
- restore works if implemented

Evidence:

- frontend URL
- Cognito user pool/app client names or redacted ids
- admin API route
- smoke/manual QA screenshots
- CloudWatch logs
- Aurora row checks

### Database/Migration Cards

Examples: #80

Test:

- migration can run from clean/reset state
- seed can run repeatably or has documented reset path
- fixture import works
- table counts match expected
- deployed V2 APIs read imported data
- V1 routes still work

Evidence:

- command log
- table counts
- V1 compatibility endpoint results
- smoke matrix
- rollback/reset instructions

## Standard Error Shape

V2 APIs should use:

```json
{
  "error": {
    "code": "INVALID_QUERY",
    "message": "category must be a known work category code",
    "details": {
      "field": "category"
    }
  }
}
```

Unexpected errors should be generic:

```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Unable to load V2 master data"
  }
}
```

Do not leak:

- stack trace
- DB secret
- secret ARN if not needed
- password
- raw SQL with sensitive values
- private S3 key
- internal raw source JSON

## How To Check API Gateway Routes

Get API id from stack:

```bash
API_ID=$(aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-master-data-api-dev \
  --query "Stacks[0].Outputs[?OutputKey=='MasterDataApiId'].OutputValue | [0]" \
  --output text)
```

List routes:

```bash
aws apigatewayv2 get-routes \
  --region ap-southeast-1 \
  --api-id "$API_ID" \
  --query 'Items[].RouteKey' \
  --output table
```

For #64 expected:

```text
GET /api/v2/academic-periods
GET /api/v2/evaluation-periods
GET /api/v2/work-categories
GET /api/v2/work-types
GET /api/v2/faculties
```

## How To Check CloudWatch Logs

List latest streams:

```bash
aws logs describe-log-streams \
  --region ap-southeast-1 \
  --log-group-name /aws/lambda/cs361-v2-dev-query \
  --order-by LastEventTime \
  --descending \
  --max-items 3 \
  --query 'logStreams[].{name:logStreamName,last:lastEventTimestamp}' \
  --output table
```

Get recent events:

```bash
LOG_STREAM=$(aws logs describe-log-streams \
  --region ap-southeast-1 \
  --log-group-name /aws/lambda/cs361-v2-dev-query \
  --order-by LastEventTime \
  --descending \
  --max-items 1 \
  --query 'logStreams[0].logStreamName' \
  --output text)

aws logs get-log-events \
  --region ap-southeast-1 \
  --log-group-name /aws/lambda/cs361-v2-dev-query \
  --log-stream-name "$LOG_STREAM" \
  --limit 20
```

## How To Check DB Counts

Use Data API:

```bash
DB_CLUSTER_ARN=$(aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-aws-foundation-dev \
  --query "Stacks[0].Outputs[?OutputKey=='DBClusterArn'].OutputValue | [0]" \
  --output text)

DB_SECRET_ARN=$(aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-aws-foundation-dev \
  --query "Stacks[0].Outputs[?OutputKey=='DBSecretArn'].OutputValue | [0]" \
  --output text)

DB_NAME=$(aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-aws-foundation-dev \
  --query "Stacks[0].Outputs[?OutputKey=='DBName'].OutputValue | [0]" \
  --output text)

aws rds-data execute-statement \
  --region ap-southeast-1 \
  --resource-arn "$DB_CLUSTER_ARN" \
  --secret-arn "$DB_SECRET_ARN" \
  --database "$DB_NAME" \
  --sql "select
    (select count(*) from faculty) as faculties,
    (select count(*) from work_item) as work_items,
    (select count(*) from faculty_work_item) as faculty_work_items,
    (select count(*) from evidence_reference) as evidence_references"
```

## Known Auto-Pause Behavior

Aurora can auto-pause. If the system has been idle, first request can fail with:

```text
DatabaseResumingException
```

This may appear as API `500`.

How to handle during testing:

1. Record that DB was resuming if it happened
2. Wait 15-30 seconds
3. Retry smoke test
4. Use retry result as pass/fail evidence

For future improvement, a card can add Lambda-level retry/backoff for `DatabaseResumingException`.

## Evidence Folder Pattern

Put evidence under:

```text
evidence/v2/<issue-or-feature>/README.md
```

Examples:

```text
evidence/v2/aws-foundation/README.md
evidence/v2/master-data-api/README.md
```

Evidence should include:

- date
- issue number
- branch/commit
- AWS region
- stack names
- resource names
- commands run
- test output
- known limitations
- no secret values

## GitHub Closing Comment Template

Use this pattern:

````md
อัปเดต Issue #<number> - <title> เสร็จแล้วครับ

สิ่งที่ทำ:
- ...
- ...

AWS/resources:
- Region: `ap-southeast-1`
- Stack: `<stack-name>`
- API endpoint: `<endpoint>`
- Lambda: `<lambda-name>`
- CloudWatch: `<log-group>`

Verification:
```text
<paste smoke/unit test output>
```

Evidence/docs:
- `<docs path>`
- `<evidence path>`

Commit:
`<commit-hash> <commit-message>`

Known notes:
- ไม่มี secret value ถูกเปิดใน docs/repo
- ถ้า Aurora auto-pause อาจต้อง retry หลัง resume

สรุป: การ์ดนี้พร้อมปิดได้ เพราะ <explain why this meets acceptance criteria>.
````

## #64 Evidence Example

````md
อัปเดต Issue #64 - Build Master Data API เสร็จแล้วครับ

สิ่งที่ทำ:
- เพิ่ม Production Master Data API ตาม path จริง: `API Gateway -> Lambda -> RDS Data API -> Aurora`
- เพิ่ม Lambda handler สำหรับ read-only master data
- เพิ่ม CloudFormation stack สำหรับ API Gateway + Query Lambda
- เพิ่ม deploy script และ smoke test script
- อัปเดต docs contract และ evidence

AWS resources:
- Region: `ap-southeast-1`
- API stack: `cs361-v2-master-data-api-dev`
- API endpoint: `https://n89gqgnqw2.execute-api.ap-southeast-1.amazonaws.com`
- Lambda: `cs361-v2-dev-query`
- CloudWatch log group: `/aws/lambda/cs361-v2-dev-query`

Smoke test:
```text
PASS /api/v2/academic-periods count=5
PASS /api/v2/evaluation-periods count=3
PASS /api/v2/work-categories count=6
PASS /api/v2/work-types count=26
PASS /api/v2/faculties count=3
PASS /api/v2/work-types?category=UNKNOWN returned 400 INVALID_QUERY
```

Evidence:
- `docs/v2/issues/64-build-master-data-api.md`
- `docs/v2/master-data-api.md`
- `evidence/v2/master-data-api/README.md`

Commit:
`df03830 feat: deploy V2 master data API`

สรุป: พร้อมปิดได้ เพราะ endpoint ทั้ง 5 ตัว deploy แล้วบน AWS, อ่าน Aurora จริงผ่าน RDS Data API, มี CloudWatch/API smoke evidence และไม่มี secret value เปิดใน docs/repo
````

## Before Closing Any Card

Checklist:

- [ ] Acceptance criteria in issue card are actually satisfied
- [ ] Deployed AWS path tested if required
- [ ] Unit/contract tests pass
- [ ] Smoke test output saved
- [ ] Docs updated
- [ ] Evidence file added/updated
- [ ] Checklist in issue card updated honestly
- [ ] No secrets committed
- [ ] Commit pushed
- [ ] GitHub issue comment includes evidence
