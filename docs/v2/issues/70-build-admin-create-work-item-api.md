# [V2] Build Admin Create Work Item API #70

## สรุป

สร้าง `POST /api/v2/admin/work-items` สำหรับให้ Admin pilot เพิ่ม work item ใหม่เข้า V2 repository พร้อม faculty assignment, period, category/type, subtype detail, evidence metadata และ audit event

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #56 แต่ GitHub issue จริงใช้ #70

## Production AWS Requirement

การ์ดนี้ต้องเป็น protected AWS admin API จริง:

```text
Amazon API Gateway
→ Cognito/Admin auth จาก #69
→ Admin Lambda
→ RDS Data API transaction
→ Aurora PostgreSQL Serverless v2
```

ต้องสร้าง record ใน Aurora จริงและมี audit trail จริง ห้ามปิดด้วย mock repository หรือ local fixture เท่านั้น

## Background

V2 ไม่ได้เป็นแค่ public read-only page แต่เป็น repository foundation ที่ Admin pilot สามารถจัดการข้อมูลเบื้องต้นได้

การเพิ่ม work item ต้องไม่ insert เฉพาะ `work_item` อย่างเดียว เพราะข้อมูลหนึ่งรายการต้องมี relation และ metadata ที่สอดคล้องกัน เช่น:

- `faculty_work_item`
- subtype detail table เช่น `teaching_detail`, `publication_detail`, `service_detail`
- `evidence_reference`
- `audit_event`

การ์ดนี้เป็น write path แรกของ V2 admin backend ดังนั้นต้องทำแบบ transaction-safe ตั้งแต่ต้น เพื่อให้ #71 update/delete และ #78 admin form ใช้ pattern ต่อได้

## Database Alignment Check

เช็กกับ `database/migrations/001_base.sql`, `database/seeds/001_master_data.sql` และ demo/Aurora dev แล้ว การ์ดนี้ต้องใช้ table/attribute ที่มีอยู่จริง:

- `work_item`: `id`, `category_code`, `work_type_code`, `title`, `description`, `start_date`, `end_date`, `visibility`, `status`, `created_by`, `updated_by`, `created_at`, `updated_at`
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

field กลุ่มนี้ใช้กับ import/mapping pipeline จาก workload form หรือ source record เท่านั้น ถ้าต้องสร้างจาก admin API ให้ปล่อยเป็น `NULL` หรือให้ backend set ตาม policy ที่ทีมตกลงไว้

ตัวอย่าง id/code ที่ต้องใช้ให้ตรงกับฐานข้อมูลจริง:

- faculty id: `fac_prapaporn-rattanatamrong`
- academic period id: `ap-2567-2`
- evaluation period id: `eval-2567-full-year`
- category/type สำหรับ teaching: `TEACHING` / `LECTURE`
- category/type สำหรับ publication: `RESEARCH` / `PUBLICATION`
- visibility values: `PUBLIC`, `INTERNAL`, `RESTRICTED`

ห้ามใช้ code เก่าใน payload เช่น:

- `TEACHING_LECTURE`
- `ap_2567_2`
- `fac_prapaporn`

## เป้าหมาย

สร้าง create API ที่:

- require authenticated `ADMIN` จาก #69
- รับ payload แบบ structured
- validate category/type/period/faculty/visibility/subtype detail/evidence
- insert หลาย table ใน transaction เดียว
- rollback ทั้งหมดถ้าขั้นตอนใดขั้นตอนหนึ่ง fail
- record `audit_event`
- return created work item summary ที่อ่านกลับผ่าน #66/#68 ได้

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- update/delete/restore
- admin create/edit UI
- evidence file upload
- signed URL generation
- official approval workflow
- import pipeline
- workload scoring
- admin auth setup เอง นอกเหนือจากใช้ guard ของ #69

## Scope

### ต้องทำ

- implement `POST /api/v2/admin/work-items`
- require authenticated `ADMIN`
- validate payload fields:
  - `title`
  - `category_code`
  - `work_type_code`
  - `visibility`
  - `faculty[]`
  - `detail`
  - `evidence[]`
- insert:
  - `work_item`
  - `faculty_work_item`
  - subtype detail table ที่ตรงกับ `detail.kind`
  - `evidence_reference` rows เมื่อมี
  - `audit_event`
- ใช้ RDS Data API transaction:
  - `BeginTransaction`
  - `ExecuteStatement`
  - `CommitTransaction`
  - `RollbackTransaction`
- ใช้ `CS361V2AdminLambdaRole-dev` หรือ role ที่มีสิทธิ์จำกัดตาม #48
- configure API Gateway protected route สำหรับ `POST /api/v2/admin/work-items`
- เพิ่ม CloudWatch logs สำหรับ request id, actor user, validation failure, transaction rollback และ success
- เพิ่ม tests สำหรับ valid create, invalid payload, unauthorized, non-admin, duplicate/id conflict, transaction rollback
- เพิ่ม AWS smoke test ที่สร้าง record จริงใน Aurora target environment

### ไม่ต้องทำ

- edit existing work item
- soft delete
- restore
- admin UI form
- Cognito setup beyond using guard from #69
- upload ไฟล์ evidence เข้า S3

## API Contract

```http
POST /api/v2/admin/work-items
Authorization: Bearer <admin-token>
Content-Type: application/json
```

### Request Payload Shape

```json
{
  "id": "wi-admin-demo-2567-cs333-lecture",
  "title": "CS333 Software Engineering Lecture",
  "description": "Lecture workload for semester 2/2567",
  "category_code": "TEACHING",
  "work_type_code": "LECTURE",
  "visibility": "INTERNAL",
  "start_date": "2025-01-13",
  "end_date": "2025-05-09",
  "faculty": [
    {
      "faculty_id": "fac_prapaporn-rattanatamrong",
      "academic_period_id": "ap-2567-2",
      "evaluation_period_id": "eval-2567-full-year",
      "role": "INSTRUCTOR",
      "contribution_order": 1,
      "contribution_percent": 100,
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
      "mime_type": "text/html",
      "visibility": "INTERNAL"
    }
  ]
}
```

### Payload Field Notes

| Field | Required | Source / DB target | หมายเหตุ |
|---|---|---|---|
| `id` | optional | `work_item.id` | ถ้าไม่ส่ง server generate stable id |
| `title` | yes | `work_item.title` | ห้ามว่าง |
| `description` | optional | `work_item.description` | summary |
| `category_code` | yes | `work_item.category_code` | ต้องมีใน `work_category` และ active |
| `work_type_code` | yes | `work_item.work_type_code` | ต้องอยู่ใต้ category นั้น |
| `visibility` | yes | `work_item.visibility` | `PUBLIC`, `INTERNAL`, `RESTRICTED` |
| `start_date` | optional | `work_item.start_date` | ISO date |
| `end_date` | optional | `work_item.end_date` | ต้องไม่ก่อน `start_date` |
| `faculty[]` | yes | `faculty_work_item` | อย่างน้อย 1 คน |
| `detail` | yes | subtype table | ต้องตรงกับ `detail.kind` |
| `evidence[]` | optional | `evidence_reference` | metadata/reference เท่านั้น |

### Faculty Payload

```json
{
  "faculty_id": "fac_prapaporn-rattanatamrong",
  "academic_period_id": "ap-2567-2",
  "evaluation_period_id": "eval-2567-full-year",
  "role": "INSTRUCTOR",
  "contribution_order": 1,
  "contribution_percent": 100,
  "contribution_note": "Primary instructor",
  "quantity": 1,
  "credits": 3,
  "hours": 45
}
```

Mapping:

| Payload field | DB field | Required | Validation |
|---|---|---|---|
| `faculty_id` | `faculty_work_item.faculty_id` | yes | ต้องมีอยู่ใน `faculty` และ status active |
| `academic_period_id` | `faculty_work_item.academic_period_id` | recommended | ต้องมีใน `academic_period` ถ้าส่ง และ admin form ควรส่งเพื่อรองรับหลายปีการศึกษา |
| `evaluation_period_id` | `faculty_work_item.evaluation_period_id` | optional | ต้องมีใน `evaluation_period` ถ้าส่ง |
| `role` | `faculty_work_item.role` | recommended | free text แต่ควรใช้ consistent role code |
| `contribution_order` | `faculty_work_item.contribution_order` | optional | integer >= 1 |
| `contribution_percent` | `faculty_work_item.contribution_percent` | optional | `0-100` |
| `contribution_note` | `faculty_work_item.contribution_note` | optional | admin-only ไม่ควรออก public API |
| `quantity` | `faculty_work_item.quantity` | optional | >= 0 |
| `credits` | `faculty_work_item.credits` | optional | >= 0 |
| `hours` | `faculty_work_item.hours` | optional | >= 0 |

## Detail Payloads

`detail.kind` ต้องสอดคล้องกับ category/type และเลือก insert เพียง subtype table เดียวต่อ work item

### Detail Kind Mapping

| Category / Work type | `detail.kind` | Target table | หมายเหตุ |
|---|---|---|---|
| `TEACHING`: `LECTURE`, `LAB`, `SEMINAR` | `teaching` | `teaching_detail` | ใช้สำหรับภาระงานสอน |
| `RESEARCH`: `PUBLICATION` | `publication` | `publication_detail` | ใช้สำหรับผลงานตีพิมพ์ที่มี title/venue/year/doi |
| `RESEARCH`: `RESEARCH_PROJECT`, `RESEARCH_GRANT` | `research_project` | `research_project_detail` | ใช้สำหรับโครงการ/ทุนวิจัย |
| `SUPERVISION`: `SENIOR_PROJECT`, `COOPERATIVE_EDUCATION`, `THESIS`, `GENERAL_ADVISOR` | `supervision` | `supervision_detail` | ใช้สำหรับการดูแลนักศึกษา |
| `ACADEMIC_SERVICE`: `COMMITTEE`, `ACADEMIC_REVIEWER`, `EDITOR`, `INVITED_SPEAKER`, `EXTERNAL_SERVICE` | `service` | `service_detail` | ใช้สำหรับงานบริการวิชาการ |
| `ADMINISTRATION`: `COURSE_COORDINATOR`, `ADMIN_POSITION`, `PROGRAM_ADMINISTRATION`, `INTERNSHIP_COORDINATOR` | `administration` | `administration_detail` | ใช้สำหรับงานบริหาร |
| `OTHER`: `OTHER_WORKLOAD`, `SPECIAL_SCORE` | `none` หรือ `administration` ตาม policy ทีม | ไม่มี dedicated table | ต้องตกลง mapper ให้ชัดก่อน implement ถ้าทีมต้องรับ type กลุ่มนี้ |

สำหรับ research output อื่นใน master data เช่น `CONFERENCE_PRESENTATION`, `BOOK_OR_CHAPTER`, `PATENT_OR_INVENTION`, `ACADEMIC_AWARD`, `RESEARCH_UTILIZATION` schema ปัจจุบันยังไม่มี dedicated detail table แยก ถ้าจะให้ admin create ผ่าน API นี้ต้องเลือก policy ก่อนว่าใช้ `publication_detail` แบบ generic, สร้าง detail table เพิ่ม, หรือ reject ด้วย `400 UNSUPPORTED_WORK_TYPE` ชั่วคราว

### Teaching Detail

ใช้กับ `TEACHING` type เช่น `LECTURE`, `LAB`, `SEMINAR`

```json
{
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
}
```

### Publication Detail

ใช้กับ `RESEARCH` / `PUBLICATION`

```json
{
  "kind": "publication",
  "publication_title": "Privacy-Preserving Edge Analytics for Smart Campus Workload Signals",
  "venue": "Synthetic Journal of Cloud Education Systems",
  "publisher": "Synthetic Demo Publisher",
  "publication_year": 2024,
  "publication_date": "2024-10-01",
  "doi": "10.0000/cs361.demo.privacy-edge.2024",
  "isbn": null,
  "issn": null,
  "quartile": "Q2",
  "indexing_database": "SYNTHETIC_INDEX",
  "publication_kind": "JOURNAL_ARTICLE",
  "external_url": "https://example.edu/cs361-demo/privacy-edge-analytics"
}
```

### Research Project Detail

ใช้กับ `RESEARCH_PROJECT` หรือ `RESEARCH_GRANT`

```json
{
  "kind": "research_project",
  "project_title": "Privacy Platform Research Project",
  "funding_source": "Synthetic Research Fund",
  "funding_type": "INTERNAL_GRANT",
  "budget_amount": 250000,
  "currency": "THB",
  "project_status": "ACTIVE",
  "contract_number": "SYN-2567-001",
  "principal_investigator": "ผศ.ดร.ประภาพร รัตนธำรง",
  "project_start_date": "2024-06-01",
  "project_end_date": "2025-05-31"
}
```

### Service Detail

ใช้กับ `ACADEMIC_SERVICE` type เช่น `INVITED_SPEAKER`, `COMMITTEE`

```json
{
  "kind": "service",
  "service_scope": "EXTERNAL",
  "organization_name": "Example University",
  "service_role": "INVITED_SPEAKER",
  "committee_name": null,
  "order_reference": null,
  "service_date": "2025-02-15",
  "service_end_date": "2025-02-15"
}
```

### Supervision Detail

ใช้กับ `SUPERVISION` type เช่น `SENIOR_PROJECT`, `THESIS`, `COOPERATIVE_EDUCATION`

```json
{
  "kind": "supervision",
  "supervision_type": "SENIOR_PROJECT",
  "supervision_role": "ADVISOR",
  "degree_level": "UNDERGRADUATE",
  "program_name": "Computer Science",
  "course_code": "CS402",
  "student_count": 3,
  "credits": 3,
  "student_identifier_policy": "REDACTED"
}
```

### Administration Detail

ใช้กับ `ADMINISTRATION` type เช่น `COURSE_COORDINATOR`, `PROGRAM_ADMINISTRATION`

```json
{
  "kind": "administration",
  "position_title": "Course Coordinator",
  "organization_unit": "Computer Science",
  "appointment_type": "COURSE",
  "appointed_from": "2025-01-13",
  "appointed_to": "2025-05-09",
  "appointment_reference": "Semester 2/2567 assignment"
}
```

## Evidence Payload

```json
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
```

Rules:

- `reference_type` ต้องเป็น `URL`, `S3_OBJECT`, `DOCUMENT_ID`, `TEXT_NOTE`, หรือ `OTHER`
- ต้องมี `external_url` หรือ `s3_key` อย่างน้อยหนึ่งค่า ยกเว้น `TEXT_NOTE` / `OTHER`
- การ์ดนี้ยังไม่ upload file เข้า S3
- ถ้าใช้ `S3_OBJECT`, payload ต้องเป็น metadata ของ object ที่มีอยู่แล้วหรือ placeholder ตาม policy ทีม
- ห้ามให้ client ส่ง private AWS credential หรือ signed URL

## Response

Success:

```json
{
  "id": "wi-admin-demo-2567-cs333-lecture",
  "status": "ACTIVE",
  "visibility": "INTERNAL",
  "message": "created",
  "links": {
    "admin_detail": "/api/v2/admin/work-items/wi-admin-demo-2567-cs333-lecture",
    "public_detail": null
  }
}
```

ถ้า `visibility = PUBLIC`, `public_detail` ควรชี้ไปที่ `/api/v2/work-items/{id}` เพื่อ smoke test อ่านกลับผ่าน #68 ได้

Error shape ควร consistent กับ #64/#66/#69 เช่น:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid create work item payload",
    "details": [
      {
        "field": "work_type_code",
        "message": "work_type_code must belong to category_code"
      }
    ]
  }
}
```

## Transaction Plan

ใช้ transaction เดียวต่อ request:

1. Verify admin context จาก #69
2. Validate master data:
   - category active
   - work type active และอยู่ใต้ category
   - faculty ids มีอยู่จริง
   - academic/evaluation periods มีอยู่จริง
3. Generate ids สำหรับ work item, faculty_work_item, evidence, audit event ถ้า client ไม่ส่ง
4. Insert `work_item`
5. Insert subtype detail table ตาม `detail.kind`
6. Insert `faculty_work_item` rows
7. Insert `evidence_reference` rows
8. Insert `audit_event`
9. Commit transaction
10. Return created summary

ถ้าขั้นตอนใด fail ต้อง rollback และไม่เหลือ partial rows

## Data Source / Table Mapping

| Payload/Derived field | Target table | Target attribute |
|---|---|---|
| `id` | `work_item` | `id` |
| `category_code` | `work_item` | `category_code` |
| `work_type_code` | `work_item` | `work_type_code` |
| `title` | `work_item` | `title` |
| `description` | `work_item` | `description` |
| `start_date` | `work_item` | `start_date` |
| `end_date` | `work_item` | `end_date` |
| `visibility` | `work_item` | `visibility` |
| server default | `work_item` | `status = ACTIVE` |
| admin context | `work_item` | `created_by`, `updated_by` |
| `faculty[].*` | `faculty_work_item` | relation fields |
| `detail.kind = teaching` | `teaching_detail` | teaching columns |
| `detail.kind = publication` | `publication_detail` | publication columns |
| `detail.kind = research_project` | `research_project_detail` | research columns |
| `detail.kind = supervision` | `supervision_detail` | supervision columns |
| `detail.kind = service` | `service_detail` | service columns |
| `detail.kind = administration` | `administration_detail` | administration columns |
| `evidence[]` | `evidence_reference` | evidence columns |
| admin context + payload snapshot | `audit_event` | `actor_user_id`, `actor_subject`, `action`, `entity_type`, `entity_id`, `after_json`, `request_id` |

## Validation Rules

- `title` required และต้องไม่เป็น empty string
- `category_code` ต้องมีอยู่และ `is_active = true`
- `work_type_code` ต้องมีอยู่, active และอยู่ใต้ `category_code`
- `visibility` ต้องเป็น `PUBLIC`, `INTERNAL`, หรือ `RESTRICTED`
- `end_date` ต้องไม่ก่อน `start_date`
- ต้องมี `faculty[]` อย่างน้อย 1 คน
- `faculty[].faculty_id` ต้องมีอยู่ใน `faculty`
- `faculty[].contribution_percent` ถ้ามีต้องอยู่ในช่วง `0-100`
- ผลรวม contribution percent ถ้าส่งครบทุกคนควรไม่เกิน `100`
- numeric fields เช่น `quantity`, `credits`, `hours`, `student_count`, `budget_amount` ต้องไม่ติดลบ
- `detail.kind` ต้องสอดคล้องกับ category/type
- `publication_year` ถ้ามีต้องอยู่ในช่วง `1900-3000`
- `quartile` ถ้ามีต้องอยู่ใน allowed values ของ schema
- `student_identifier_policy` ต้องเป็น `REDACTED`, `INTERNAL_ONLY`, หรือ `NOT_STORED`
- evidence visibility ต้องไม่กว้างกว่า work item โดยไม่ตั้งใจ เช่น work item `INTERNAL` ไม่ควรสร้าง evidence `PUBLIC` เว้นแต่ทีมตัดสินใจ explicit
- client ห้าม set `created_by`, `updated_by`, `audit_event.actor_user_id`, `status`, `deleted_at`

## Audit Event

ต้อง insert `audit_event` หลัง create สำเร็จใน transaction เดียวกัน:

```json
{
  "action": "WORK_ITEM_CREATE",
  "entity_type": "work_item",
  "entity_id": "wi-admin-demo-2567-cs333-lecture",
  "before_json": null,
  "after_json": {
    "id": "wi-admin-demo-2567-cs333-lecture",
    "category_code": "TEACHING",
    "work_type_code": "LECTURE",
    "visibility": "INTERNAL",
    "faculty_count": 1,
    "evidence_count": 1
  },
  "request_id": "<api-gateway-request-id>"
}
```

`actor_user_id` และ `actor_subject` ต้องมาจาก admin guard ของ #69 ไม่ใช่จาก client payload

## Smoke Test Baseline

ควรมี smoke test ใน AWS จริงอย่างน้อย:

- no token -> `401`
- valid Cognito but no admin role -> `403`
- invalid payload เช่น `work_type_code = TEACHING_LECTURE` -> `400`
- valid teaching payload -> `201`
- query Aurora แล้วเจอ rows ใน:
  - `work_item`
  - `faculty_work_item`
  - `teaching_detail`
  - `evidence_reference`
  - `audit_event`
- ถ้า create เป็น `PUBLIC`, อ่านกลับผ่าน `GET /api/v2/work-items/{id}` ได้
- ถ้า create เป็น `INTERNAL`, public detail ต้องไม่เปิด แต่ admin detail ของ #71 ควรอ่านได้เมื่อทำต่อ

## Acceptance Criteria

- [ ] admin create endpoint ใช้งานได้บน AWS จริง
- [ ] unauthenticated request return `401`
- [ ] non-admin request return `403`
- [ ] valid payload insert record ครบทุก table ที่เกี่ยวข้อง
- [ ] invalid payload return `400` พร้อม field-level details
- [ ] transaction rollback เมื่อ insert ส่วนใดส่วนหนึ่ง fail
- [ ] `audit_event` ถูกสร้างสำหรับ create action
- [ ] created record อ่านกลับผ่าน public detail ได้เมื่อ `visibility = PUBLIC`
- [ ] internal/restricted record ไม่เปิดผ่าน public detail
- [ ] API Gateway protected route deploy แล้ว
- [ ] Admin Lambda insert เข้า Aurora ผ่าน RDS Data API transaction จริง
- [ ] CloudWatch logs มีหลักฐาน success และ rollback/error path
- [ ] smoke test สร้าง record จริงและตรวจ DB ได้

## Review Checklist

Backend:

- [ ] mutation ใช้ transaction
- [ ] validation logic ไม่กระจายซ้ำหลายที่
- [ ] subtype mapper ใช้ field ที่ตรงกับ schema จริง
- [ ] audit event มี actor, action, entity id และ request id
- [ ] production path ไม่อ่าน/เขียน fixture file

Security:

- [ ] route require `ADMIN`
- [ ] payload ไม่สามารถ set audit actor เองจาก client
- [ ] payload ไม่สามารถ set `status = DELETED` หรือ source/provenance field เอง
- [ ] evidence reference ไม่เปิด secret/private path โดยไม่ตั้งใจ

QA:

- [ ] create teaching payload ผ่าน
- [ ] create publication payload ผ่าน หรือมี test mapper publication
- [ ] invalid category/type pair fail
- [ ] rollback test ผ่าน

## Dependencies

Blocked by:

- #64 Build Master Data API
- #69 Configure Admin Authentication

Blocks:

- #71 Build Admin Update / Soft Delete API
- #78 Build Admin Create/Edit Form UI
- #79 Integrate Admin UI with Auth & CRUD API

Related:

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

1-1.5 days

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อ Admin สามารถสร้าง work item ใหม่บน AWS endpoint จริงผ่าน Cognito-protected API พร้อม relation/subtype/evidence/audit ใน transaction เดียว, ข้อมูลถูกเขียนเข้า Aurora จริง, rollback ทำงานเมื่อ error, อ่านผลลัพธ์กลับได้ตาม visibility rule และมี CloudWatch/Aurora smoke evidence สำหรับปิดการ์ด
