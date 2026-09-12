# V2 Master Data API Evidence

Issue: #64 - Build Master Data API

Date: 2026-09-13

## AWS Deployment

| Item | Value |
|---|---|
| Region | `ap-southeast-1` |
| Foundation stack | `cs361-v2-aws-foundation-dev` |
| API stack | `cs361-v2-master-data-api-dev` |
| API endpoint | `https://n89gqgnqw2.execute-api.ap-southeast-1.amazonaws.com` |
| Lambda function | `cs361-v2-dev-query` |
| CloudWatch log group | `/aws/lambda/cs361-v2-dev-query` |

The Lambda reads Aurora PostgreSQL through RDS Data API using the Query Lambda role from the foundation stack. No database password, secret value, or access key is recorded here.

## API Gateway Routes

Verified deployed routes:

```text
GET /api/v2/academic-periods
GET /api/v2/evaluation-periods
GET /api/v2/work-categories
GET /api/v2/work-types
GET /api/v2/faculties
```

## Aurora Data Readiness

Verified tables exist through RDS Data API:

```text
academic_period
evaluation_period
work_category
work_type
faculty
```

Verified data counts before API smoke test:

```text
academic_periods=5
evaluation_periods=3
active_work_categories=6
active_work_types=26
public_active_faculties=3
```

## Smoke Test

Command:

```bash
AWS_REGION=ap-southeast-1 \
API_STACK=cs361-v2-master-data-api-dev \
scripts/smoke-v2-master-data-api.sh
```

Result:

```text
PASS /api/v2/academic-periods count=5
PASS /api/v2/evaluation-periods count=3
PASS /api/v2/work-categories count=6
PASS /api/v2/work-types count=26
PASS /api/v2/faculties count=3
PASS /api/v2/work-types?category=UNKNOWN returned 400 INVALID_QUERY
```

## Local Verification

Commands:

```bash
python3 -m unittest backend.v2.query.test_master_data

cd frontend
npm run test:v2:master-data
```

Results:

```text
backend.v2.query.test_master_data: Ran 8 tests - OK
frontend test:v2:master-data: 9 tests passed
```
