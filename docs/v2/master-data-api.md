# V2 Master Data API Contract

เอกสารนี้เป็น contract สำหรับ Issue #64 - Build Master Data API

สถานะ: production AWS implementation added for deployment through `backend/v2/query/master_data.py`, `infra/v2/master-data-api.yaml`, and `scripts/deploy-v2-master-data-api.sh`.

หมายเหตุสำคัญ: local fixture implementation ใน `frontend/lib/v2/master-data.mjs` ยังใช้เป็น contract prototype/test helper ได้ แต่ production path ของ Issue #64 คือ `API Gateway -> Lambda -> RDS Data API -> Aurora` และต้อง smoke test ผ่าน AWS endpoint ก่อนปิดการ์ด

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/v2/academic-periods` | academic year/semester filter options |
| `GET /api/v2/evaluation-periods` | evaluation period filter options |
| `GET /api/v2/work-categories` | work category filter options |
| `GET /api/v2/work-types` | work type filter options, optionally filtered by category |
| `GET /api/v2/faculties` | public-safe faculty dropdown/search options |

## Response Envelope

ทุก endpoint ใช้ envelope เดียวกัน:

```json
{
  "items": [],
  "meta": {
    "count": 0
  }
}
```

## Error Shape

Validation errors return:

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

Unexpected server errors return a generic message and must not expose stack traces, ARNs, secrets, S3 private paths, or raw fixture paths.

## `GET /api/v2/academic-periods`

Query parameters:

| Parameter | Required | Example | Rule |
|---|---:|---|---|
| `year` | no | `2567` | 4-digit academic year |
| `semester` | no | `2` | one of `1`, `2`, `3`, `SUMMER`, `OTHER` |

Sorting:

```text
academic_year desc, semester desc
```

Example:

```http
GET /api/v2/academic-periods?year=2567&semester=2
```

## `GET /api/v2/evaluation-periods`

Query parameters:

| Parameter | Required | Example | Rule |
|---|---:|---|---|
| `academic_period_id` | no | `ap-2567-2` | exact match filter |

Response item fields:

- `id`
- `code`
- `label`
- `start_date`
- `end_date`
- `academic_period_id`

## `GET /api/v2/work-categories`

Query parameters:

| Parameter | Required | Example | Rule |
|---|---:|---|---|
| `active` | no | `true` | `true` or `false`, default `true` |

Response item fields:

- `code`
- `label_th`
- `label_en`
- `description`
- `display_order`
- `is_active`

Sorting:

```text
display_order asc, code asc
```

## `GET /api/v2/work-types`

Query parameters:

| Parameter | Required | Example | Rule |
|---|---:|---|---|
| `category` | no | `RESEARCH` | must be a known `work_category.code` |
| `active` | no | `true` | `true` or `false`, default `true` |

Response item fields:

- `code`
- `category_code`
- `label_th`
- `label_en`
- `description`
- `default_visibility`
- `display_order`
- `is_active`

Rules:

- unknown `category` returns `400 INVALID_QUERY`
- no `category` returns all active work types
- output sorts by category display order, work type display order, then code

## `GET /api/v2/faculties`

Query parameters:

| Parameter | Required | Example | Rule |
|---|---:|---|---|
| `q` | no | `prapaporn` | search public slug, Thai/English name, position, department |
| `status` | no | `ACTIVE` | public endpoint supports `ACTIVE` only |
| `visibility` | no | `PUBLIC` | public endpoint supports `PUBLIC` only |

Public-safe response item fields:

- `id`
- `public_slug`
- `name_th`
- `name_en`
- `academic_position`
- `department`
- `profile_image_url`
- `profile_image_alt`

The endpoint intentionally omits email, phone, office, metadata, source/provenance fields, audit fields, evidence fields, and workload counts.

## Data Source Boundary

Local/dev/test behavior:

```text
Next.js route handler
→ frontend/lib/v2/master-data.mjs
→ data/v2/fixtures/*.json
```

Required production behavior from the V2 central design:

```text
Amazon API Gateway HTTP API
→ AWS Lambda query handler
→ RDS Data API
→ Aurora PostgreSQL
```

The DTO shape is intentionally stable so the later Data API repository can replace the fixture adapter without changing frontend filter/dropdown contracts.

## Production AWS Implementation

| File | Purpose |
|---|---|
| `backend/v2/query/master_data.py` | Lambda handler, validation, DTO mapping, Data API repository |
| `infra/v2/master-data-api.yaml` | CloudFormation stack for HTTP API, routes, Lambda function, and API Gateway invoke permission |
| `scripts/deploy-v2-master-data-api.sh` | Packages the Lambda code, uploads it to the V2 S3 bucket, and deploys the API stack |
| `scripts/smoke-v2-master-data-api.sh` | Smoke tests all five deployed endpoints plus invalid category validation |

Default production/deployed names:

| Item | Default |
|---|---|
| API stack | `cs361-v2-master-data-api-dev` |
| Lambda function | `cs361-v2-dev-query` |
| API Gateway | `cs361-v2-dev-master-data-api` |
| CloudWatch log group | `/aws/lambda/cs361-v2-dev-query` |
| Foundation stack dependency | `cs361-v2-aws-foundation-dev` |

The deployment script reads these outputs from the foundation stack:

- `DBClusterArn`
- `DBSecretArn`
- `DBName`
- `QueryLambdaRoleArn`
- `DataBucketName`

No secret value is printed or committed. Only ARNs/resource names are passed as stack parameters.

## Production Deploy

Prerequisites:

- Issue #48 foundation stack exists
- Aurora Data API is enabled
- `database/migrations/001_base.sql` and required seed/demo data have already been applied to Aurora
- AWS CLI is logged in with permission for CloudFormation, Lambda, API Gateway, S3, IAM pass role, RDS Data API, Secrets Manager read, and CloudWatch logs

Deploy command:

```bash
AWS_REGION=ap-southeast-1 \
FOUNDATION_STACK=cs361-v2-aws-foundation-dev \
API_STACK=cs361-v2-master-data-api-dev \
scripts/deploy-v2-master-data-api.sh
```

The script outputs the API endpoint from CloudFormation. Use that endpoint as `API_BASE_URL` for smoke tests and later frontend integration.

## Production Smoke Test

Run against the deployed API:

```bash
AWS_REGION=ap-southeast-1 \
API_STACK=cs361-v2-master-data-api-dev \
scripts/smoke-v2-master-data-api.sh
```

Or pass the endpoint directly:

```bash
API_BASE_URL=https://<api-id>.execute-api.ap-southeast-1.amazonaws.com \
scripts/smoke-v2-master-data-api.sh
```

Expected checks:

- `GET /api/v2/academic-periods` returns `200` with `{ items, meta.count }`
- `GET /api/v2/evaluation-periods` returns `200` with `{ items, meta.count }`
- `GET /api/v2/work-categories` returns `200` with `{ items, meta.count }`
- `GET /api/v2/work-types` returns `200` with `{ items, meta.count }`
- `GET /api/v2/faculties` returns `200` with public-safe fields only
- `GET /api/v2/work-types?category=UNKNOWN` returns `400 INVALID_QUERY`

## Verification

Targeted test command:

```bash
python3 -m unittest backend.v2.query.test_master_data

cd frontend
npm run test:v2:master-data
```

Expected coverage:

- sorted academic periods
- year/semester filters
- active category sorting
- all work type sorting
- work type filter by category
- invalid category error shape
- faculty public-safe fields
- `public_slug` preservation
- empty result envelope
- visibility validation
