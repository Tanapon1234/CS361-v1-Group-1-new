# V2 Master Data API Contract

เอกสารนี้เป็น contract สำหรับ Issue #64 - Build Master Data API

สถานะ: implemented for local/dev through the V2 fixture adapter in `frontend/lib/v2/master-data.mjs`

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
→ frontend/lib/v2/master-data.cjs
→ data/v2/fixtures/*.json
```

Production target behavior from the V2 central design:

```text
API Gateway / V2 API route
→ Query service/repository
→ RDS Data API
→ Aurora PostgreSQL
```

The DTO shape is intentionally stable so the later Data API repository can replace the fixture adapter without changing frontend filter/dropdown contracts.

## Verification

Targeted test command:

```bash
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
