# [V2] Build Master Data API #64

## สรุป

สร้าง Master Data API สำหรับ V2 เพื่อให้ frontend/API cards ถัดไปใช้ข้อมูลพื้นฐานร่วมกัน เช่น academic periods, evaluation periods, work categories, work types และ faculty options สำหรับ dropdown/filter/search UI

การ์ดนี้เป็น tracer แรกของ V2 read API หลังจากมี schema, AWS foundation, V1 mapping และ demo dataset แล้ว เป้าหมายคือให้ทีมมี endpoint production จริงที่อ่านข้อมูล master/reference จาก Aurora repository ผ่าน AWS runtime ก่อนเริ่ม work item search/detail API

Production runtime ของการ์ดนี้ต้องเป็น:

```text
Amazon API Gateway
→ AWS Lambda query handler
→ Amazon RDS Data API
→ Aurora PostgreSQL Serverless v2
```

Next.js API route หรือ fixture adapter ใช้เป็น local contract prototype/test helper ได้เท่านั้น แต่ไม่ถือว่าเพียงพอสำหรับปิดการ์ดนี้

## Background

V2 ต้องรองรับการค้นหาและกรองข้อมูลผลงาน/ภาระงานตามเงื่อนไข เช่น:

- academic year / semester
- evaluation period
- work category
- work type
- faculty
- visibility

การ์ด Work Item API ถัดไปจะสร้าง API สำหรับ work item list/detail/faculty work items ต่อไป แต่ก่อนถึงจุดนั้น frontend และ backend ต้องมี master data endpoint สำหรับสร้าง filter dropdown และ validate query parameters ให้เป็นชุดเดียวกัน

ข้อมูลอ้างอิงที่มีแล้ว:

- `database/migrations/001_base.sql`
- `database/seeds/001_master_data.sql`
- `data/v2/fixtures/`
- `docs/v2/data-contract.md`
- `docs/v2/demo-dataset.md`
- `docs/v2/V2_Central_Design.md`

## เป้าหมาย

สร้าง read-only API baseline สำหรับ master data ของ V2 ที่:

- ใช้ endpoint ภายใต้ `/api/v2`
- อ่านข้อมูลจาก Aurora V2 repository ผ่าน Lambda + RDS Data API ใน AWS environment จริง
- return response shape ที่ frontend ใช้กับ dropdown/filter ได้ทันที
- enforce visibility และ public-safe fields สำหรับ public route
- รองรับ work type filter ตาม category
- มี tests สำหรับ response shape, sorting, validation และ empty state
- มีเอกสาร contract ให้การ์ด API ถัดไปใช้ต่อ
- มี deployed API Gateway endpoint และ smoke-test evidence จาก CloudWatch/AWS endpoint

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- สร้าง work item list/search API
- สร้าง work item detail API
- สร้าง faculty work items API
- สร้าง admin create/edit/delete API
- สร้าง UI dropdown จริง
- ทำ Cognito admin flow เต็มรูปแบบ
- ทำ cache/CDN optimization ขั้นสูง
- เขียน migration runner หรือ seed runner
- insert fixture data เข้า Aurora ถ้ายังไม่ได้ทำในการ์ดอื่น
- ทำเฉพาะ local fixture/Next.js route โดยไม่มี AWS deploy

## Scope

### ต้องทำ

- implement `GET /api/v2/academic-periods`
- implement `GET /api/v2/evaluation-periods`
- implement `GET /api/v2/work-categories`
- implement `GET /api/v2/work-types`
- implement `GET /api/v2/faculties`
- เพิ่ม response DTO/mapper สำหรับ master data
- เพิ่ม Lambda query handler สำหรับ master data routes
- เพิ่ม repository/data-access layer ที่อ่านจาก Aurora ผ่าน RDS Data API
- configure API Gateway routes ให้ชี้ไปยัง Lambda
- ใช้ IAM role/secret/resource ARN จาก #48 โดยไม่ hardcode secret
- เพิ่ม CloudWatch logging ที่ตรวจสอบ request/error ได้
- fixture adapter ใช้ได้เฉพาะ automated tests/local fallback แต่ production handler ต้อง query Aurora จริง
- เพิ่ม validation สำหรับ query parameters สำคัญ
- เพิ่ม tests สำหรับ endpoint หรือ handler
- เพิ่ม docs contract สำหรับ Master Data API
- เพิ่ม AWS smoke test evidence สำหรับ endpoint ทั้ง 5 ตัว

### ไม่ต้องทำ

- work item query/search
- work item detail response
- protected admin write route
- frontend integration
- official authentication/RBAC beyond public-safe read boundary

## API Contract

### `GET /api/v2/academic-periods`

ใช้สำหรับ filter academic year/semester

Query parameters:

| Parameter | Required | Example | Rule |
|---|---:|---|---|
| `year` | no | `2567` | integer academic year |
| `semester` | no | `2` | one of `1`, `2`, `3`, `SUMMER`, `OTHER` |

Response:

```json
{
  "items": [
    {
      "id": "ap-2567-2",
      "academic_year": 2567,
      "semester": "2",
      "label": "2/2567",
      "start_date": "2025-01-01",
      "end_date": "2025-05-31"
    }
  ],
  "meta": {
    "count": 1
  }
}
```

Sorting:

```text
academic_year desc, semester sort desc
```

### `GET /api/v2/evaluation-periods`

ใช้สำหรับรอบประเมินที่แยกจาก academic period

Query parameters:

| Parameter | Required | Example | Rule |
|---|---:|---|---|
| `academic_period_id` | no | `ap-2567-2` | filter optional |

Response item fields:

- `id`
- `code`
- `label`
- `start_date`
- `end_date`
- `academic_period_id`

### `GET /api/v2/work-categories`

ใช้สำหรับ filter หมวดงานหลัก

Query parameters:

| Parameter | Required | Example | Rule |
|---|---:|---|---|
| `active` | no | `true` | default `true` |

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

### `GET /api/v2/work-types`

ใช้สำหรับ filter ประเภทย่อย โดยผูกกับ category

Query parameters:

| Parameter | Required | Example | Rule |
|---|---:|---|---|
| `category` | no | `RESEARCH` | filter by `category_code` |
| `active` | no | `true` | default `true` |

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

- ถ้า `category` ไม่อยู่ใน known `work_category.code` ให้ return `400`
- ถ้าไม่ส่ง `category` ให้ return active work types ทั้งหมด
- output ต้อง sort ตาม `category display_order`, `work_type.display_order`, `code`

### `GET /api/v2/faculties`

ใช้สำหรับ filter faculty dropdown ไม่ใช่ faculty profile detail

Query parameters:

| Parameter | Required | Example | Rule |
|---|---:|---|---|
| `q` | no | `privacy` | optional text search by display name/slug |
| `status` | no | `ACTIVE` | default `ACTIVE` |
| `visibility` | no | `PUBLIC` | public route default `PUBLIC` |

Public-safe response item fields:

- `id`
- `public_slug`
- `name_th`
- `name_en`
- `academic_position`
- `department`
- `profile_image_url`
- `profile_image_alt`

Do not include in this endpoint:

- private/internal notes
- admin-only audit fields
- evidence fields
- restricted workload counts
- raw source/provenance payloads

## Response Envelope

ทุก endpoint ในการ์ดนี้ควรใช้ envelope เดียวกัน:

```json
{
  "items": [],
  "meta": {
    "count": 0
  }
}
```

Error response:

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

## Data Source Rules

Required production path:

```text
API Gateway
→ Query Lambda
→ RDS Data API
→ Aurora PostgreSQL
```

Allowed test/local fallback path:

```text
handler/repository
→ fixture adapter
→ data/v2/fixtures/*.json
```

Rules:

- repository interface ต้องไม่ผูก handler กับ Data API โดยตรง
- mapper ต้องแปลง DB rows เป็น DTO เดียวกับ fixture adapter
- fixture adapter ใช้เพื่อ test และ local development เท่านั้น
- production path ต้องไม่อ่าน fixture files
- Definition of Done ต้องพิสูจน์ด้วย deployed API Gateway URL หรือ documented AWS endpoint จริง

## Security / Visibility Rules

- Master data public endpoints ต้อง return เฉพาะ public-safe fields
- `work_category`, `work_type`, `academic_period`, `evaluation_period` ถือเป็น public-safe reference data ใน V2 baseline
- `faculties` endpoint ต้อง default เป็น `visibility = PUBLIC` และ `status = ACTIVE`
- ห้าม expose raw `source_record`, `import_batch`, `audit_event`, `auth_login_event`
- ห้าม expose DB secret, ARN, stack output หรือ S3 private object path ที่ไม่ใช่ placeholder

## Implementation Notes

### Suggested Files

ชื่อไฟล์จริงปรับตามโครงสร้าง backend ที่ทีมเลือกได้ แต่ควรมีส่วนประกอบประมาณนี้:

```text
backend/v2/query/handler.*
backend/v2/query/routes/master-data.*
backend/v2/query/repositories/master-data-repository.*
backend/v2/query/mappers/master-data-mapper.*
backend/v2/query/validation/query-params.*
backend/v2/query/tests/master-data-api.*
docs/v2/master-data-api.md
```

ถ้า repo ยังไม่มี `backend/v2` ให้ scaffold เฉพาะส่วนเล็กที่สุดที่จำเป็นสำหรับ master data routes และอย่าขยายไปถึง work item search/detail

### SQL Shape

ตัวอย่าง query:

```sql
SELECT id, academic_year, semester, label, start_date, end_date
FROM academic_period
ORDER BY academic_year DESC, semester DESC;
```

```sql
SELECT wt.code, wt.category_code, wt.label_th, wt.label_en,
       wt.description, wt.default_visibility, wt.display_order, wt.is_active
FROM work_type wt
JOIN work_category wc ON wc.code = wt.category_code
WHERE wt.is_active = true
ORDER BY wc.display_order ASC, wt.display_order ASC, wt.code ASC;
```

## Test Cases

ต้องมี test อย่างน้อย:

- academic periods endpoint returns items sorted by year/semester
- work categories endpoint returns active categories sorted by display order
- work types endpoint returns all active types when no category is passed
- work types endpoint filters by category
- invalid category returns `400 INVALID_QUERY`
- faculties endpoint returns only public-safe fields
- faculties endpoint preserves V1 `public_slug`
- empty result returns `items: []` and `meta.count = 0`
- fixture adapter and repository mapper return the same DTO shape
- error response does not leak stack trace or secret values

## Expected Deliverables

ต้องมี:

```text
docs/v2/master-data-api.md
```

และ implementation/test/deploy files ตามโครงสร้าง backend ที่ทีมเลือก

เอกสารควรบอก:

- endpoint list
- query parameters
- response examples
- error shape
- visibility rules
- local fixture/dev behavior
- production Data API behavior
- AWS endpoint URL หรือ route mapping
- Lambda name / API Gateway stage / CloudWatch log group ที่ใช้ตรวจสอบ

## Acceptance Criteria

- [ ] `GET /api/v2/academic-periods` ใช้งานได้
- [ ] `GET /api/v2/evaluation-periods` ใช้งานได้
- [ ] `GET /api/v2/work-categories` ใช้งานได้
- [ ] `GET /api/v2/work-types` ใช้งานได้
- [ ] `GET /api/v2/faculties` ใช้งานได้สำหรับ dropdown/filter
- [ ] response envelope เป็นรูปแบบเดียวกันทุก endpoint
- [ ] invalid query parameter return error shape ที่ชัดเจน
- [ ] work type filter by category ใช้งานได้
- [ ] faculties endpoint preserve `public_slug`
- [ ] public-safe fields เท่านั้นที่ถูก expose
- [ ] ไม่ expose source/audit/auth/secret fields
- [ ] มี repository/data-access boundary ไม่ผูก handler กับ SQL ตรงทุกจุด
- [ ] มี mapper จาก DB/fixture row เป็น DTO
- [ ] มี tests สำหรับ success, empty, invalid query และ visibility-safe response
- [ ] มี docs contract สำหรับ master data API
- [ ] endpoint พร้อมให้ Work Item Search API และ Repository Filter UI ใช้ต่อ
- [ ] มี Lambda query handler ที่ deploy แล้ว
- [ ] API Gateway route ทั้ง 5 ตัวชี้ไป Lambda จริง
- [ ] Lambda อ่าน Aurora ผ่าน RDS Data API จริง
- [ ] ใช้ Secrets Manager และ IAM role จาก #48 โดยไม่ hardcode secret
- [ ] CloudWatch log group มี request/error logs สำหรับ endpoint ชุดนี้
- [ ] smoke test ผ่าน deployed AWS endpoint ทั้ง success และ invalid query

## Existing Local Prototype Evidence

มี local/dev contract prototype แล้วจาก commit `1fdb741`:

- Next.js route handlers under `frontend/app/api/v2/*`
- Fixture-backed repository/mapper/validation in `frontend/lib/v2/master-data.mjs`
- Targeted tests in `frontend/lib/v2/master-data.test.mjs`
- API contract docs in `docs/v2/master-data-api.md`

หลักฐานชุดนี้ช่วยลดความเสี่ยงเรื่อง contract/mapper/test แต่ยังไม่ถือว่าปิดการ์ดนี้ เพราะ production requirement คือ API Gateway + Lambda + RDS Data API + Aurora

## Review Checklist

Data / Database:

- [ ] query สอดคล้องกับ schema จาก #47
- [ ] sort order predictable
- [ ] active/inactive handling ชัดเจน
- [ ] academic period ไม่ derive จาก calendar date ผิดๆ

Backend:

- [ ] handler แยก validation, repository, mapper ชัดเจน
- [ ] error handling ไม่ leak implementation detail
- [ ] response shape stable
- [ ] Lambda handler ใช้ repository/data-access boundary ไม่เขียน SQL กระจาย
- [ ] fixture/dev adapter ไม่ปนกับ production path
- [ ] API Gateway route/stage ถูก document และ test ได้

Frontend:

- [ ] field เพียงพอสำหรับ dropdown/filter UI
- [ ] label ไทย/อังกฤษพร้อมใช้
- [ ] faculty option ใช้ `public_slug` ต่อกับ V1 compatibility ได้
- [ ] endpoint count/empty state ใช้งานง่าย

QA / Integration:

- [ ] smoke test master data endpoint ได้
- [ ] invalid category/semester test ได้
- [ ] visibility-safe response test ได้
- [ ] dataset จาก #50 ใช้เป็น expected baseline ได้
- [ ] smoke test ใช้ AWS endpoint จริง ไม่ใช่ local route อย่างเดียว

Security:

- [ ] ไม่ return secret/config/ARN
- [ ] ไม่ return restricted/internal faculty-only fields ผ่าน public endpoint
- [ ] ไม่ expose source/audit/auth tables
- [ ] Lambda role มีสิทธิ์เท่าที่จำเป็นต่อ Data API/Secrets เท่านั้น

Tech Lead:

- [ ] scope ไม่ล้ำไป Work Item Search/Detail API
- [ ] API contract พร้อมให้ frontend/API cards ถัดไปใช้
- [ ] implementation ไม่ผูกกับ fixture format มากเกินไป

## Dependencies

Blocked by:

- #46 Freeze V2 Scope, Architecture & Interface Contracts
- #47 Design Relational Schema & SQL Migration
- #48 Provision Aurora / Data API / Secret / IAM
- #50 Prepare Multi-Year Demo Dataset

Blocks:

- #66 Build Work Item List/Search/Filter API
- #67 Build Faculty Work Items API
- #72 Build Repository Page Shell & Filter UI
- #73 Build Repository Result List & Pagination UI

Related:

- #49 Define V1 to V2 Data Mapping
- #68 Build Work Item Detail API
- #80 Execute Migration & Preserve V1 Compatibility
- #81 Final Integration / Deploy / Demo Docs

## Suggested Labels

- `v2`
- `backend`
- `api`
- `master-data`
- `ready-for-review`

## Suggested Owner

Backend Developer

Reviewers:

- Tech Lead
- Data Developer
- Frontend Developer
- QA / Integration

## Estimate

0.5-1 day

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อ V2 มี Master Data API ที่ deploy บน AWS จริงผ่าน API Gateway + Lambda + RDS Data API + Aurora และ return academic periods, evaluation periods, work categories, work types และ faculty options ได้ด้วย response shape ที่ stable, ทดสอบได้, public-safe, มี CloudWatch/API smoke evidence และพร้อมให้ Work Item API กับ frontend filter UI ใช้ต่อโดยไม่ต้องเดา contract เอง
