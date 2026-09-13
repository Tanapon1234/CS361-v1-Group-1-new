# [V2] Build Admin Update / Soft Delete API #71

## สรุป

สร้าง Admin API สำหรับดูรายละเอียดแบบ admin, แก้ไข work item, soft delete และ restore work item ใน V2 repository โดยทุก mutation ต้องเขียน Aurora จริงผ่าน transaction และต้องมี audit trail

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #57 แต่ GitHub issue จริงใช้ #71

## Production AWS Requirement

การ์ดนี้ต้องเป็น protected AWS admin API จริง:

```text
Amazon API Gateway
→ Cognito/Admin auth จาก #69
→ Admin Lambda
→ RDS Data API transaction
→ Aurora PostgreSQL Serverless v2
```

`PATCH`, `DELETE`, และ `restore` ต้องแก้ข้อมูลจริงใน Aurora และสร้าง `audit_event` จริงทุกครั้ง ห้ามปิดด้วย mock repository หรือ local fixture เท่านั้น

## Background

หลัง #70 สร้าง work item ได้แล้ว Admin pilot ต้องแก้ข้อมูลที่สร้างผิด, ปิดซ่อน record ที่ไม่ควรแสดง, และ restore record ที่ลบผิดได้โดยไม่ทำลายข้อมูลถาวร

V2 ใช้ soft delete เป็นหลัก:

- `work_item.status = DELETED`
- `work_item.deleted_at = now()`
- public read APIs จาก #66/#67/#68 ต้องไม่แสดง deleted record
- admin detail route ยังสามารถดู deleted record ได้เพื่อ audit/restore

การแก้ไข work item ไม่ใช่ update แค่ `work_item` เพราะหนึ่ง record อาจมี relation หลายชุด:

- `faculty_work_item`
- subtype detail table เช่น `teaching_detail`, `publication_detail`, `service_detail`
- `evidence_reference`
- `audit_event`

ดังนั้นการ์ดนี้ต้องใช้ transaction pattern ต่อจาก #70

## Database Alignment Check

เช็กกับ `database/migrations/001_base.sql`, `database/seeds/001_master_data.sql` และ demo/Aurora dev แล้ว การ์ดนี้ต้องใช้ table/attribute ที่มีอยู่จริง:

- `work_item`: `id`, `category_code`, `work_type_code`, `title`, `description`, `start_date`, `end_date`, `visibility`, `status`, `created_by`, `updated_by`, `created_at`, `updated_at`, `deleted_at`
- `faculty_work_item`: `id`, `faculty_id`, `work_item_id`, `academic_period_id`, `evaluation_period_id`, `role`, `contribution_order`, `contribution_percent`, `contribution_note`, `quantity`, `credits`, `hours`, `source_section_code`
- subtype detail tables:
  - `teaching_detail`
  - `publication_detail`
  - `research_project_detail`
  - `supervision_detail`
  - `service_detail`
  - `administration_detail`
- `evidence_reference`: `id`, `work_item_id`, `reference_type`, `label`, `external_url`, `s3_key`, `mime_type`, `checksum_sha256`, `visibility`
- `audit_event`: `id`, `actor_user_id`, `actor_subject`, `action`, `entity_type`, `entity_id`, `before_json`, `after_json`, `request_id`

มี field กลุ่ม provenance ที่มีอยู่จริงใน schema แต่ไม่ควรเปิดให้ admin client set เองในการ์ดนี้:

- `work_item.source_score`
- `work_item.source_weight`
- `work_item.source_section_code`
- `work_item.import_batch_id`
- `work_item.source_record_id`
- `faculty_work_item.source_section_code`

field กลุ่มนี้เป็นของ import/mapping pipeline จาก workload form หรือ source record เท่านั้น การ์ดนี้ต้อง preserve ค่าเดิมไว้ ไม่ลบทิ้งโดยไม่ตั้งใจ และไม่รับค่าจาก client payload

ตัวอย่าง id/code ที่ต้องใช้ให้ตรงกับฐานข้อมูลจริง:

- work item id: `wi-teach-2567-2-cs333`
- faculty id: `fac_prapaporn-rattanatamrong`
- academic period id: `ap-2567-2`
- evaluation period id: `eval-2567-full-year`
- category/type สำหรับ teaching: `TEACHING` / `LECTURE`
- visibility values: `PUBLIC`, `INTERNAL`, `RESTRICTED`
- status values: `ACTIVE`, `DELETED`

ห้ามใช้ code เก่าใน payload เช่น:

- `TEACHING_LECTURE`
- `ap_2567_2`
- `fac_prapaporn`

## เป้าหมาย

สร้าง admin mutation API ที่:

- require authenticated `ADMIN` จาก #69
- ให้ admin ดู detail แบบครบกว่าหน้า public ได้
- PATCH เฉพาะ field ที่ส่งมาโดยไม่เขียนทับ field ที่ไม่ได้ส่ง
- update relation/subtype/evidence แบบ transaction-safe
- soft delete โดยไม่ hard delete
- restore record ที่ถูก soft delete ได้
- record `audit_event` พร้อม before/after snapshot ทุก mutation
- ทำให้ public API ไม่เห็น deleted/internal/restricted record ผิด policy

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- สร้าง admin UI
- สร้าง admin list endpoint ใหม่
- ทำ approval workflow
- ทำ hard delete
- upload/delete binary evidence file ใน S3
- signed URL generation
- full audit viewer
- dynamic RBAC หรือ role management
- import pipeline หรือ workload scoring
- admin auth setup เอง นอกเหนือจากใช้ guard ของ #69

## Scope

### ต้องทำ

- implement `GET /api/v2/admin/work-items/{id}`
- implement `PATCH /api/v2/admin/work-items/{id}`
- implement `DELETE /api/v2/admin/work-items/{id}` เป็น soft delete
- implement `POST /api/v2/admin/work-items/{id}/restore`
- require authenticated `ADMIN` ทุก route
- PATCH ต้องรองรับ:
  - core fields ใน `work_item`
  - replace/upsert `faculty_work_item`
  - replace/upsert subtype detail ที่ตรงกับ `detail.kind`
  - replace/upsert `evidence_reference` metadata
- update metadata:
  - `work_item.updated_at`
  - `work_item.updated_by`
  - `work_item.deleted_at` สำหรับ delete/restore
- insert `audit_event` สำหรับ update, soft delete, restore
- ใช้ RDS Data API transaction:
  - `BeginTransaction`
  - `ExecuteStatement`
  - `CommitTransaction`
  - `RollbackTransaction`
- ใช้ `CS361V2AdminLambdaRole-dev` หรือ role ที่มีสิทธิ์จำกัดตาม #48
- configure API Gateway protected routes สำหรับ admin routes ทั้งหมด
- เพิ่ม CloudWatch logs สำหรับ request id, actor, entity id, action, validation failure, rollback และ success
- เพิ่ม tests สำหรับ admin detail, valid patch, invalid payload, unauthorized, non-admin, not found, soft delete, restore, rollback
- เพิ่ม AWS smoke test ที่ update/soft delete/restore record จริงจาก #70 หรือ demo fixture

### ไม่ต้องทำ

- admin create route เพราะอยู่ในการ์ด #70
- admin UI form เพราะอยู่ในการ์ด #78
- admin integration auth/UI เพราะอยู่ในการ์ด #79
- evidence file upload/delete จริง
- hard delete หรือ purge job

## API Contract

### Admin Detail

```http
GET /api/v2/admin/work-items/{id}
Authorization: Bearer <admin-token>
```

ต้องใช้สำหรับหน้า admin edit form เพื่อโหลดข้อมูลก่อนแก้ไข สามารถ return record ที่เป็น `INTERNAL`, `RESTRICTED` หรือ `DELETED` ได้ ถ้า caller เป็น `ADMIN`

ตัวอย่าง response:

```json
{
  "id": "wi-teach-2567-2-cs333",
  "title": "CS333 Software Engineering Lecture",
  "description": "Lecture workload for semester 2/2567",
  "category_code": "TEACHING",
  "work_type_code": "LECTURE",
  "visibility": "INTERNAL",
  "status": "ACTIVE",
  "start_date": "2025-01-13",
  "end_date": "2025-05-09",
  "faculty": [
    {
      "id": "fwi-teach-2567-2-cs333-prapaporn",
      "faculty_id": "fac_prapaporn-rattanatamrong",
      "display_name": "ผศ.ดร.ประภาพร รัตนธำรง",
      "academic_period_id": "ap-2567-2",
      "evaluation_period_id": "eval-2567-full-year",
      "role": "INSTRUCTOR",
      "contribution_order": 1,
      "contribution_percent": 100,
      "contribution_note": null,
      "quantity": 1,
      "credits": 3,
      "hours": 45
    }
  ],
  "detail": {
    "kind": "teaching",
    "course_code": "CS333",
    "course_title": "Software Engineering",
    "degree_level": "UNDERGRADUATE",
    "teaching_mode": "LECTURE",
    "section_count": 1,
    "student_count": 45,
    "credits": 3,
    "lecture_hours": 45,
    "lab_hours": 0,
    "workload_hours": 45,
    "reference_label": "Semester 2/2567 teaching assignment"
  },
  "evidence": [
    {
      "id": "ev-admin-demo-2567-cs333-syllabus",
      "label": "Course syllabus",
      "reference_type": "URL",
      "external_url": "https://example.edu/cs361-demo/cs333-syllabus",
      "s3_key": null,
      "mime_type": "text/html",
      "checksum_sha256": null,
      "visibility": "INTERNAL"
    }
  ],
  "created_at": "2026-09-12T00:00:00Z",
  "updated_at": "2026-09-12T00:00:00Z",
  "deleted_at": null
}
```

### Patch Work Item

```http
PATCH /api/v2/admin/work-items/{id}
Authorization: Bearer <admin-token>
Content-Type: application/json
```

PATCH ต้องเป็น partial update ระดับ top-level:

- ถ้าไม่ส่ง field ใดมา ห้ามล้าง field นั้น
- ถ้าส่ง `null` ต้องตีความเป็น "ล้างค่า" เฉพาะ field ที่ schema อนุญาตให้ nullable
- ถ้าส่ง `faculty`, `detail`, หรือ `evidence` ให้ใช้ strategy ตาม section ด้านล่าง

ตัวอย่าง payload สำหรับแก้ core fields + teaching detail:

```json
{
  "title": "CS333 Software Engineering Lecture and Workshop",
  "description": "Updated teaching workload for semester 2/2567",
  "visibility": "INTERNAL",
  "start_date": "2025-01-13",
  "end_date": "2025-05-09",
  "detail": {
    "kind": "teaching",
    "course_code": "CS333",
    "course_title": "Software Engineering",
    "degree_level": "UNDERGRADUATE",
    "teaching_mode": "LECTURE",
    "section_count": 1,
    "student_count": 48,
    "credits": 3,
    "lecture_hours": 45,
    "lab_hours": 6,
    "workload_hours": 51,
    "reference_label": "Updated semester 2/2567 assignment"
  }
}
```

ตัวอย่าง payload สำหรับ replace faculty assignment:

```json
{
  "faculty": [
    {
      "id": "fwi-teach-2567-2-cs333-prapaporn",
      "faculty_id": "fac_prapaporn-rattanatamrong",
      "academic_period_id": "ap-2567-2",
      "evaluation_period_id": "eval-2567-full-year",
      "role": "INSTRUCTOR",
      "contribution_order": 1,
      "contribution_percent": 70,
      "contribution_note": "Primary instructor",
      "quantity": 1,
      "credits": 3,
      "hours": 36
    },
    {
      "faculty_id": "fac_kasidit-chanchio",
      "academic_period_id": "ap-2567-2",
      "evaluation_period_id": "eval-2567-full-year",
      "role": "CO_INSTRUCTOR",
      "contribution_order": 2,
      "contribution_percent": 30,
      "quantity": 1,
      "credits": 3,
      "hours": 15
    }
  ]
}
```

ตัวอย่าง payload สำหรับ replace evidence metadata:

```json
{
  "evidence": [
    {
      "id": "ev-admin-demo-2567-cs333-syllabus",
      "label": "Updated course syllabus",
      "reference_type": "URL",
      "external_url": "https://example.edu/cs361-demo/cs333-syllabus-v2",
      "s3_key": null,
      "mime_type": "text/html",
      "checksum_sha256": null,
      "visibility": "INTERNAL"
    }
  ]
}
```

Success response:

```json
{
  "id": "wi-teach-2567-2-cs333",
  "status": "ACTIVE",
  "visibility": "INTERNAL",
  "message": "updated",
  "updated_at": "2026-09-13T10:30:00Z",
  "links": {
    "admin_detail": "/api/v2/admin/work-items/wi-teach-2567-2-cs333",
    "public_detail": null
  }
}
```

### Soft Delete

```http
DELETE /api/v2/admin/work-items/{id}
Authorization: Bearer <admin-token>
```

Optional body:

```json
{
  "reason": "Duplicate record created during demo import"
}
```

ต้องทำ:

- set `work_item.status = DELETED`
- set `work_item.deleted_at = now()`
- set `work_item.updated_at = now()`
- set `work_item.updated_by = <admin app_user id>`
- preserve child rows ไว้ทั้งหมด
- insert `audit_event.action = WORK_ITEM_SOFT_DELETED`

Response:

```json
{
  "id": "wi-teach-2567-2-cs333",
  "status": "DELETED",
  "message": "soft_deleted",
  "deleted_at": "2026-09-13T10:40:00Z"
}
```

### Restore

```http
POST /api/v2/admin/work-items/{id}/restore
Authorization: Bearer <admin-token>
Content-Type: application/json
```

Optional body:

```json
{
  "reason": "Deleted by mistake during verification"
}
```

ต้องทำ:

- set `work_item.status = ACTIVE`
- set `work_item.deleted_at = NULL`
- set `work_item.updated_at = now()`
- set `work_item.updated_by = <admin app_user id>`
- insert `audit_event.action = WORK_ITEM_RESTORED`

Response:

```json
{
  "id": "wi-teach-2567-2-cs333",
  "status": "ACTIVE",
  "message": "restored",
  "updated_at": "2026-09-13T10:45:00Z"
}
```

### Error Shape

ควร consistent กับ #64/#69/#70:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid update work item payload",
    "details": [
      {
        "field": "faculty[1].faculty_id",
        "message": "faculty_id does not exist"
      }
    ]
  }
}
```

Expected status codes:

| Case | Status |
|---|---:|
| no token | `401` |
| invalid/expired token | `401` |
| valid token without `ADMIN` role | `403` |
| work item not found | `404` |
| invalid payload | `400` |
| unsupported type/detail mapper | `400` |
| conflict เช่น duplicate relation role | `409` |
| success | `200` |

## Update Strategy

### Core `work_item`

PATCH อนุญาตให้แก้:

| Payload field | Target table | Target attribute | Rule |
|---|---|---|---|
| `title` | `work_item` | `title` | required ถ้าส่ง ต้องไม่ empty |
| `description` | `work_item` | `description` | nullable |
| `category_code` | `work_item` | `category_code` | ถ้าส่งต้องส่งคู่กับ `work_type_code` หรือ validate กับค่าเดิม |
| `work_type_code` | `work_item` | `work_type_code` | ต้องอยู่ใต้ category |
| `visibility` | `work_item` | `visibility` | `PUBLIC`, `INTERNAL`, `RESTRICTED` |
| `start_date` | `work_item` | `start_date` | nullable ISO date |
| `end_date` | `work_item` | `end_date` | ต้องไม่ก่อน `start_date` |

PATCH ไม่อนุญาตให้ client set:

- `id`
- `status`
- `deleted_at`
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`
- `source_score`
- `source_weight`
- `source_section_code`
- `import_batch_id`
- `source_record_id`
- audit actor fields

### Faculty Strategy

ถ้า payload ไม่ส่ง `faculty`:

- ไม่แก้ `faculty_work_item`

ถ้าส่ง `faculty`:

- ใช้ replace-all strategy ภายใน transaction เพื่อให้ implementation ง่ายและ deterministic
- delete child rows เดิมของ `work_item_id`
- insert rows ใหม่ตาม payload
- generate `faculty_work_item.id` ถ้า client ไม่ส่ง
- preserve provenance fields เฉพาะถ้าทีมมี policy ชัดเจน ไม่อย่างนั้นตั้ง `source_section_code = NULL` สำหรับ admin-created/edited row

Validation:

- ต้องมีอย่างน้อย 1 row
- `faculty_id` ต้องมีอยู่ใน `faculty`
- `academic_period_id` ต้องมีอยู่ใน `academic_period` ถ้าส่ง และ admin form ควรส่งเพื่อรองรับหลายปีการศึกษา
- `evaluation_period_id` ต้องมีอยู่ใน `evaluation_period` ถ้าส่ง
- `contribution_percent` ต้องอยู่ใน `0-100`
- ผลรวม `contribution_percent` ถ้าส่งครบทุกคนควรไม่เกิน `100`
- `quantity`, `credits`, `hours` ต้องไม่ติดลบ
- tuple `faculty_id + work_item_id + role` ต้องไม่ซ้ำ

### Detail Strategy

ถ้า payload ไม่ส่ง `detail`:

- ไม่แก้ subtype detail table

ถ้าส่ง `detail`:

- validate `detail.kind` กับ `category_code` / `work_type_code`
- update/upsert detail table ที่ตรงกับ `detail.kind`
- ถ้าเปลี่ยน type ข้าม kind เช่น `teaching` -> `publication`, ต้องลบ subtype row เดิมทุก table ที่ไม่ใช่ kind ใหม่ใน transaction เดียว
- ถ้า schema ปัจจุบันไม่มี dedicated detail table สำหรับ type นั้น ให้ reject ด้วย `400 UNSUPPORTED_WORK_TYPE` ชั่วคราว หรือทำตาม policy ที่ทีมตกลงไว้ใน #70

Detail kind mapping:

| Category / Work type | `detail.kind` | Target table |
|---|---|---|
| `TEACHING`: `LECTURE`, `LAB`, `SEMINAR` | `teaching` | `teaching_detail` |
| `RESEARCH`: `PUBLICATION` | `publication` | `publication_detail` |
| `RESEARCH`: `RESEARCH_PROJECT`, `RESEARCH_GRANT` | `research_project` | `research_project_detail` |
| `SUPERVISION`: `SENIOR_PROJECT`, `COOPERATIVE_EDUCATION`, `THESIS`, `GENERAL_ADVISOR` | `supervision` | `supervision_detail` |
| `ACADEMIC_SERVICE`: `COMMITTEE`, `ACADEMIC_REVIEWER`, `EDITOR`, `INVITED_SPEAKER`, `EXTERNAL_SERVICE` | `service` | `service_detail` |
| `ADMINISTRATION`: `COURSE_COORDINATOR`, `ADMIN_POSITION`, `PROGRAM_ADMINISTRATION`, `INTERNSHIP_COORDINATOR` | `administration` | `administration_detail` |

### Evidence Strategy

ถ้า payload ไม่ส่ง `evidence`:

- ไม่แก้ `evidence_reference`

ถ้าส่ง `evidence`:

- ใช้ replace-all strategy ภายใน transaction
- delete evidence rows เดิมของ `work_item_id`
- insert rows ใหม่ตาม payload
- generate `evidence_reference.id` ถ้า client ไม่ส่ง

Rules:

- `reference_type` ต้องเป็น `URL`, `S3_OBJECT`, `DOCUMENT_ID`, `TEXT_NOTE`, หรือ `OTHER`
- ต้องมี `external_url` หรือ `s3_key` อย่างน้อยหนึ่งค่า ยกเว้น `TEXT_NOTE` / `OTHER`
- การ์ดนี้ยังไม่ upload/delete file ใน S3
- ถ้าใช้ `S3_OBJECT`, update เฉพาะ metadata/reference ของ object ไม่ใช่ binary file
- ห้ามให้ client ส่ง private AWS credential หรือ signed URL
- public response ของ #68 ยังต้องไม่เปิด `s3_key` หรือ `checksum_sha256` ถ้าเป็นข้อมูล private

## Transaction Plan

### PATCH

ใช้ transaction เดียวต่อ request:

1. Verify admin context จาก #69
2. Load current work item + child rows เป็น `before_json`
3. ถ้าไม่พบ record ให้ return `404`
4. Validate payload กับ current state และ master data
5. Update `work_item` เฉพาะ field ที่ส่งมา
6. ถ้ามี `detail`, upsert subtype detail และลบ subtype row เก่าที่ไม่ตรง kind
7. ถ้ามี `faculty`, replace `faculty_work_item`
8. ถ้ามี `evidence`, replace `evidence_reference`
9. Set `updated_at` และ `updated_by`
10. Load updated state เป็น `after_json`
11. Insert `audit_event.action = WORK_ITEM_UPDATED`
12. Commit transaction
13. Return updated summary

ถ้าขั้นตอนใด fail ต้อง rollback และไม่เหลือ partial update

### DELETE

ใช้ transaction เดียว:

1. Verify admin context
2. Load current state เป็น `before_json`
3. ถ้าไม่พบ record ให้ return `404`
4. ถ้า already `DELETED`, return success แบบ idempotent หรือ `409` ตาม policy ทีม แต่ต้องไม่ hard delete
5. Update `status = DELETED`, `deleted_at = now()`, `updated_at = now()`, `updated_by`
6. Insert `audit_event.action = WORK_ITEM_SOFT_DELETED`
7. Commit transaction

### RESTORE

ใช้ transaction เดียว:

1. Verify admin context
2. Load current state เป็น `before_json`
3. ถ้าไม่พบ record ให้ return `404`
4. ถ้า already `ACTIVE`, return success แบบ idempotent หรือ `409` ตาม policy ทีม
5. Update `status = ACTIVE`, `deleted_at = NULL`, `updated_at = now()`, `updated_by`
6. Insert `audit_event.action = WORK_ITEM_RESTORED`
7. Commit transaction

## Audit Event

ทุก mutation ต้อง insert `audit_event` ใน transaction เดียวกันกับ data change:

```json
{
  "action": "WORK_ITEM_UPDATED",
  "entity_type": "work_item",
  "entity_id": "wi-teach-2567-2-cs333",
  "before_json": {
    "title": "CS333 Software Engineering Lecture",
    "visibility": "INTERNAL",
    "status": "ACTIVE",
    "faculty_count": 1,
    "evidence_count": 1
  },
  "after_json": {
    "title": "CS333 Software Engineering Lecture and Workshop",
    "visibility": "INTERNAL",
    "status": "ACTIVE",
    "faculty_count": 1,
    "evidence_count": 1
  },
  "request_id": "<api-gateway-request-id>"
}
```

`actor_user_id` และ `actor_subject` ต้องมาจาก admin guard ของ #69 ไม่ใช่จาก client payload

Action names:

- `WORK_ITEM_UPDATED`
- `WORK_ITEM_SOFT_DELETED`
- `WORK_ITEM_RESTORED`

## Public API Impact

หลังทำการ์ดนี้ ต้อง verify ร่วมกับ #66/#67/#68:

- deleted record ต้องไม่อยู่ใน `GET /api/v2/work-items`
- deleted record ต้องไม่อยู่ใน `GET /api/v2/faculties/{facultyId}/work-items`
- deleted record ต้องไม่เปิดผ่าน `GET /api/v2/work-items/{id}`
- internal/restricted record ต้องไม่ถูกเปิด public เพราะ admin เปลี่ยน visibility ผิด logic
- admin detail ยังดู deleted record ได้
- restore แล้ว public API กลับมาเห็น record ได้เฉพาะเมื่อ `visibility = PUBLIC`

## Smoke Test Baseline

ควรมี smoke test ใน AWS จริงอย่างน้อย:

- no token -> `401`
- valid Cognito but no admin role -> `403`
- admin GET detail ของ active record -> `200`
- PATCH title/description/visibility -> `200`
- PATCH invalid `work_type_code = TEACHING_LECTURE` -> `400`
- PATCH invalid faculty id -> `400`
- PATCH detail แล้ว query Aurora เห็น update ใน subtype table
- DELETE -> `200`, query Aurora แล้ว `status = DELETED`, `deleted_at IS NOT NULL`
- หลัง DELETE public detail/list ไม่เห็น record
- RESTORE -> `200`, query Aurora แล้ว `status = ACTIVE`, `deleted_at IS NULL`
- `audit_event` มี action update/delete/restore พร้อม actor/request id
- CloudWatch มี logs ของ success และ rollback/error path

## Acceptance Criteria

- [ ] admin detail endpoint return record ได้รวม internal/restricted/deleted ตามสิทธิ์ admin
- [ ] PATCH update core fields ได้โดยไม่ล้าง field ที่ไม่ได้ส่ง
- [ ] PATCH replace faculty assignment ได้ใน transaction
- [ ] PATCH upsert subtype detail ได้ตรงกับ schema จริง
- [ ] PATCH replace evidence metadata ได้โดยไม่จัดการ binary file
- [ ] invalid payload return `400` พร้อม field-level details
- [ ] unsupported detail/type return `400`
- [ ] DELETE ทำ soft delete ไม่ hard delete
- [ ] restore ทำงานและ clear `deleted_at`
- [ ] public API ไม่แสดง deleted record
- [ ] mutation ทุกครั้งมี `audit_event`
- [ ] unauthorized return `401`
- [ ] non-admin return `403`
- [ ] not found return `404`
- [ ] transaction rollback เมื่อ update child table fail
- [ ] API Gateway protected routes deploy แล้ว
- [ ] Lambda update/soft delete/restore Aurora ผ่าน RDS Data API transaction จริง
- [ ] CloudWatch logs มีหลักฐาน action/audit/rollback path
- [ ] smoke test บน AWS endpoint ผ่านครบ update, soft delete และ restore

## Review Checklist

Backend:

- [ ] patch logic ไม่เขียนทับ field ที่ไม่ได้ส่งมาโดยไม่ตั้งใจ
- [ ] relation/detail/evidence update ใช้ transaction
- [ ] subtype mapper ใช้ field ที่ตรงกับ schema จริง
- [ ] updated/deleted metadata ถูกต้อง
- [ ] audit event มี before/after, actor, action, entity id และ request id
- [ ] production path ไม่อ่าน/เขียน fixture file

Security:

- [ ] route ทั้งหมด require `ADMIN`
- [ ] payload ไม่สามารถ set audit actor เองจาก client
- [ ] payload ไม่สามารถ hard delete หรือ set status เอง
- [ ] admin response ไม่เปิด secret ที่ไม่จำเป็น
- [ ] evidence reference ไม่เปิด private S3 path/signed URL โดยไม่ตั้งใจ

QA:

- [ ] สร้างจาก #70 แล้ว update/delete/restore ต่อได้
- [ ] deleted record หายจาก public list/detail
- [ ] restore แล้วกลับมาอ่านได้ตาม visibility rule
- [ ] rollback test ผ่าน

## Dependencies

Blocked by:

- #69 Configure Admin Authentication
- #70 Build Admin Create Work Item API

Blocks:

- #77 Build Admin Work Item List UI
- #78 Build Admin Create/Edit Form UI
- #79 Integrate Admin UI with Auth & CRUD API

Related:

- #66 Build Work Item List/Search/Filter API
- #67 Build Faculty Work Items API
- #68 Build Work Item Detail API
- #80 Execute Migration & Preserve V1 Compatibility
- #81 Final Integration, Deploy, Demo & Docs

## Suggested Labels

- `v2`
- `backend`
- `admin`
- `api`
- `ready-for-agent`

## Suggested Owner

Backend Developer

Reviewers:

- Tech Lead
- Security Reviewer
- Data Developer
- QA / Integration

## Estimate

1.5-2 days

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อ Admin สามารถดูรายละเอียดแบบ admin, PATCH แก้ข้อมูล, soft delete และ restore work item ผ่าน AWS endpoint จริงได้อย่างปลอดภัย, mutation เขียน Aurora ผ่าน RDS Data API transaction, มี `audit_event`/CloudWatch/Aurora smoke evidence ครบ และ public API ไม่เห็น record ที่ถูกลบหรือข้อมูลที่ไม่ควรเปิดเผย
