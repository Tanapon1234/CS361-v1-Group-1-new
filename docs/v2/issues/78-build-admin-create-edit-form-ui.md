# [V2] Build Admin Create/Edit Form UI #78

## สรุป

สร้างหน้า `/admin/work-items/new` และ `/admin/work-items/{id}` สำหรับ Admin pilot create/edit work item พร้อม form validation, faculty assignment, subtype detail และ evidence metadata โดยต้องใช้ Master Data API และ Admin CRUD APIs จริงบน AWS

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #64 ในเอกสาร design แต่ GitHub issue จริงใช้ #78 เพราะ #64 ปัจจุบันถูกใช้กับ Master Data API แล้ว

## Production AWS Requirement

Admin form ต้องใช้ master data และ admin CRUD APIs ที่ deploy บน AWS จริง:

```text
Frontend admin form
→ Cognito token/session จาก #76
→ API Gateway admin routes
→ Admin Lambda + ADMIN role guard
→ RDS Data API transaction
→ Aurora PostgreSQL Serverless v2
```

form payload/mock submit ใช้ได้เฉพาะ component tests หรือ local UI tests เท่านั้น ไม่ถือว่าเพียงพอสำหรับปิดการ์ดนี้

ต้อง submit จริงไปยัง:

```http
POST  /api/v2/admin/work-items
GET   /api/v2/admin/work-items/{id}
PATCH /api/v2/admin/work-items/{id}
```

พร้อม `Authorization: Bearer <cognito-token>` จาก Cognito admin session จริง

## Background

Admin Create/Update APIs จาก #70 และ #71 ต้องมี form UI ที่ช่วยให้ทีมจัดการ repository ได้จริงในการ demo V2

Form นี้ต้องรองรับข้อมูลหลายหมวดงาน เช่น งานสอน งานตีพิมพ์ โครงการวิจัย การดูแลนักศึกษา งานบริการวิชาการ และงานบริหาร โดยไม่ทำให้ผู้ใช้กรอก category/type/detail ผิด contract

การ์ดนี้ต่อจาก:

- #76: admin login/protected route foundation
- #77: admin work item list และ action paths
- #70: create work item API
- #71: admin detail/update API

และเป็นฐานให้ #79 ทำ admin end-to-end flow ต่อ

## ความเกี่ยวข้องกับโจทย์

โจทย์ V2 ต้องมีแหล่งข้อมูลกลางที่จัดการได้จริง ไม่ใช่แค่แสดงข้อมูล public อย่างเดียว การ์ด #78 คือหน้าที่ admin ใช้เพิ่มและแก้ข้อมูลใน repository ให้ตรงกับ schema กลางของ V2

ถ้าไม่มีการ์ดนี้ ทีมจะมี API หลังบ้านแต่ไม่มี UI สำหรับกรอกข้อมูลจริง ทำให้ demo admin pilot ไม่ครบ

## เป้าหมาย

สร้าง admin form UI ที่:

- เปิด `/admin/work-items/new` สำหรับ create
- เปิด `/admin/work-items/{id}` สำหรับ edit
- ใช้ protected admin route จาก #76
- ใช้ master data options จาก #64
- โหลด existing record จาก admin detail API ของ #71
- validate field หลักก่อน submit
- รองรับ subtype fields ตาม category/type
- รองรับ faculty contributors หลายคน
- รองรับ evidence reference metadata
- map payload ให้ตรงกับ #70/#71
- submit create/update ไป AWS endpoint จริง
- map backend validation errors กลับเข้า form fields
- handle loading, error, dirty form, success, `401`, `403`
- ไม่เปิด secret/token/raw backend error ใน UI

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- evidence file upload เข้า S3
- evidence binary preview/download
- hard delete
- restore flow เต็ม
- role management UI
- official workload scoring
- approval/reviewer workflow
- dynamic custom field builder
- audit event viewer
- user invite/reset password flow

## User Stories

1. As an admin user, I want to open `/admin/work-items/new`, so that I can create a new repository record.
2. As an admin user, I want to open `/admin/work-items/{id}`, so that I can edit an existing work item.
3. As an admin user, I want category/type dropdowns from master data, so that I choose valid values.
4. As an admin user, I want subtype fields to change by category/type, so that I only fill relevant detail fields.
5. As an admin user, I want to add multiple faculty contributors, so that shared work is represented correctly.
6. As an admin user, I want to assign academic/evaluation periods, so that records support multi-year reporting.
7. As an admin user, I want to add evidence metadata, so that references can be tracked without uploading files yet.
8. As an admin user, I want clear validation errors, so that I know exactly which field needs correction.
9. As an admin user, I want dirty form protection, so that I do not accidentally lose edits.
10. As a QA reviewer, I want proof that create/edit hits deployed AWS endpoints, so that the form is production-connected.
11. As a security reviewer, I want the form protected by Cognito admin auth, so that non-admin users cannot mutate data.
12. As a backend developer, I want payload mapping to match #70/#71, so that form changes do not create API drift.

## Scope

### ต้องทำ

- เพิ่ม route `/admin/work-items/new`
- เพิ่ม route `/admin/work-items/{id}`
- protect ทั้งสอง route ด้วย admin auth helper/session จาก #76
- โหลด master data options จาก deployed #64 endpoints:
  - `GET /api/v2/academic-periods`
  - `GET /api/v2/evaluation-periods`
  - `GET /api/v2/work-categories`
  - `GET /api/v2/work-types`
  - `GET /api/v2/faculties`
- create mode:
  - render empty form
  - submit `POST /api/v2/admin/work-items`
- edit mode:
  - load existing value ด้วย `GET /api/v2/admin/work-items/{id}`
  - render existing values
  - submit `PATCH /api/v2/admin/work-items/{id}`
- form fields หลัก:
  - `id` optional เฉพาะ create ถ้าทีมอยากกำหนดเอง
  - `title`
  - `description`
  - `category_code`
  - `work_type_code`
  - `visibility`
  - `start_date`
  - `end_date`
- faculty assignment section:
  - `faculty_id`
  - `academic_period_id`
  - `evaluation_period_id`
  - `role`
  - `contribution_order`
  - `contribution_percent`
  - `contribution_note`
  - `quantity`
  - `credits`
  - `hours`
- subtype detail section:
  - `teaching`
  - `publication`
  - `research_project`
  - `supervision`
  - `service`
  - `administration`
- evidence metadata section:
  - `id` optional
  - `label`
  - `reference_type`
  - `external_url`
  - `s3_key`
  - `mime_type`
  - `checksum_sha256`
  - `visibility`
- client-side validation ที่สอดคล้องกับ backend
- map backend validation errors จาก AWS endpoint กลับเข้า form fields
- loading/error/dirty form/success states
- handle `401/403/400/404/409/500`
- after create/update redirect หรือ show success ตาม UX ที่ทีมเลือก
- เพิ่ม tests/manual QA checklist

### ไม่ต้องทำ

- binary evidence upload
- hard delete
- restore submit
- role management
- mutation integration แบบ full workflow ของ #79
- public repository refresh automation

## Routes

| Route | Mode | Behavior |
|---|---|---|
| `/admin/work-items/new` | create | empty form, submit `POST /api/v2/admin/work-items` |
| `/admin/work-items/{id}` | edit | load existing record, submit `PATCH /api/v2/admin/work-items/{id}` |

ถ้า `id = new` ต้อง route ไป create mode ไม่ใช่ edit mode

## API Endpoints ที่ต้องใช้

### Master Data

```http
GET /api/v2/academic-periods
GET /api/v2/evaluation-periods
GET /api/v2/work-categories
GET /api/v2/work-types
GET /api/v2/faculties
```

### Admin CRUD

```http
POST /api/v2/admin/work-items
GET /api/v2/admin/work-items/{id}
PATCH /api/v2/admin/work-items/{id}
```

ทุก admin request ต้องแนบ:

```http
Authorization: Bearer <cognito-token>
```

## Create Payload Contract

Create form ต้องส่ง payload ให้ตรงกับ #70:

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

## Edit Load Contract

Edit form ต้องโหลด existing data จาก #71:

```http
GET /api/v2/admin/work-items/{id}
```

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

## Edit Submit Contract

PATCH ต้องเป็น partial update ระดับ top-level ตาม #71:

- field ที่ไม่ส่ง ต้องไม่ถูกล้าง
- field ที่ส่ง `null` ให้ล้างค่าเฉพาะ field ที่ backend อนุญาต nullable
- ถ้าส่ง `faculty`, backend ใช้ replace-all strategy สำหรับ `faculty_work_item`
- ถ้าส่ง `detail`, backend upsert subtype detail
- ถ้าส่ง `evidence`, backend ใช้ replace-all strategy สำหรับ `evidence_reference`

ตัวอย่าง PATCH core + detail:

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

ตัวอย่าง PATCH faculty replacement:

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

## Form Field Mapping

| Form section | UI field | Payload field | DB target |
|---|---|---|---|
| Core | Work item id | `id` | `work_item.id` |
| Core | Title | `title` | `work_item.title` |
| Core | Description | `description` | `work_item.description` |
| Core | Category | `category_code` | `work_item.category_code` |
| Core | Work type | `work_type_code` | `work_item.work_type_code` |
| Core | Visibility | `visibility` | `work_item.visibility` |
| Core | Start date | `start_date` | `work_item.start_date` |
| Core | End date | `end_date` | `work_item.end_date` |
| Faculty | Faculty | `faculty[].faculty_id` | `faculty_work_item.faculty_id` |
| Faculty | Academic period | `faculty[].academic_period_id` | `faculty_work_item.academic_period_id` |
| Faculty | Evaluation period | `faculty[].evaluation_period_id` | `faculty_work_item.evaluation_period_id` |
| Faculty | Role | `faculty[].role` | `faculty_work_item.role` |
| Faculty | Order | `faculty[].contribution_order` | `faculty_work_item.contribution_order` |
| Faculty | Percent | `faculty[].contribution_percent` | `faculty_work_item.contribution_percent` |
| Faculty | Note | `faculty[].contribution_note` | `faculty_work_item.contribution_note` |
| Faculty | Quantity | `faculty[].quantity` | `faculty_work_item.quantity` |
| Faculty | Credits | `faculty[].credits` | `faculty_work_item.credits` |
| Faculty | Hours | `faculty[].hours` | `faculty_work_item.hours` |
| Detail | Detail kind | `detail.kind` | subtype mapper |
| Evidence | Label | `evidence[].label` | `evidence_reference.label` |
| Evidence | Reference type | `evidence[].reference_type` | `evidence_reference.reference_type` |
| Evidence | External URL | `evidence[].external_url` | `evidence_reference.external_url` |
| Evidence | S3 key | `evidence[].s3_key` | `evidence_reference.s3_key` |
| Evidence | MIME type | `evidence[].mime_type` | `evidence_reference.mime_type` |
| Evidence | Checksum | `evidence[].checksum_sha256` | `evidence_reference.checksum_sha256` |
| Evidence | Visibility | `evidence[].visibility` | `evidence_reference.visibility` |

## Detail Kind / Subtype Fields

เมื่อเลือก `category_code` และ `work_type_code` แล้ว form ต้องเลือก `detail.kind` และแสดง field ที่เกี่ยวข้อง:

| Category / Work type | `detail.kind` | Fields |
|---|---|---|
| `TEACHING`: `LECTURE`, `LAB`, `SEMINAR` | `teaching` | `course_code`, `course_title`, `degree_level`, `teaching_mode`, `section_count`, `student_count`, `credits`, `lecture_hours`, `lab_hours`, `workload_hours`, `reference_label` |
| `RESEARCH`: `PUBLICATION` | `publication` | `publication_title`, `venue`, `publisher`, `publication_year`, `publication_date`, `doi`, `isbn`, `issn`, `quartile`, `indexing_database`, `publication_kind`, `external_url` |
| `RESEARCH`: `RESEARCH_PROJECT`, `RESEARCH_GRANT` | `research_project` | `project_title`, `funding_source`, `funding_type`, `budget_amount`, `currency`, `project_status`, `contract_number`, `principal_investigator`, `project_start_date`, `project_end_date` |
| `SUPERVISION`: `SENIOR_PROJECT`, `COOPERATIVE_EDUCATION`, `THESIS`, `GENERAL_ADVISOR` | `supervision` | `supervision_type`, `supervision_role`, `degree_level`, `program_name`, `course_code`, `student_count`, `credits`, `student_identifier_policy` |
| `ACADEMIC_SERVICE`: `COMMITTEE`, `ACADEMIC_REVIEWER`, `EDITOR`, `INVITED_SPEAKER`, `EXTERNAL_SERVICE` | `service` | `service_scope`, `organization_name`, `service_role`, `committee_name`, `order_reference`, `service_date`, `service_end_date` |
| `ADMINISTRATION`: `COURSE_COORDINATOR`, `ADMIN_POSITION`, `PROGRAM_ADMINISTRATION`, `INTERNSHIP_COORDINATOR` | `administration` | `position_title`, `organization_unit`, `appointment_type`, `appointed_from`, `appointed_to`, `appointment_reference` |

ถ้า master data มี work type ที่ schema ยังไม่มี dedicated detail table เช่น research output บางประเภท ให้ form ต้อง disable submit หรือแสดง warning ตาม backend policy ของ #70/#71 เช่น `UNSUPPORTED_WORK_TYPE` ไม่ควรเดา field เอง

## Evidence Metadata Rules

การ์ดนี้รองรับ metadata เท่านั้น ยังไม่ upload binary file

| Field | Rule |
|---|---|
| `reference_type` | `URL`, `S3_OBJECT`, `DOCUMENT_ID`, `TEXT_NOTE`, `OTHER` |
| `external_url` | required เมื่อ `reference_type = URL` |
| `s3_key` | ใช้เฉพาะ metadata ของ object ที่มีอยู่แล้ว ไม่ใช่ signed URL |
| `mime_type` | optional |
| `checksum_sha256` | optional |
| `visibility` | `PUBLIC`, `INTERNAL`, `RESTRICTED` |

ห้ามให้ผู้ใช้กรอกหรือ submit:

- AWS access key/secret key
- signed URL
- Secrets Manager value
- local file path
- raw binary file

## Validation Rules

Client-side validation ควรช่วยจับ error ก่อน submit แต่ backend ยังเป็นแหล่ง truth หลัก

ขั้นต่ำต้อง validate:

- `title` ห้ามว่าง
- `category_code` ต้องเลือก
- `work_type_code` ต้องเลือกและอยู่ใต้ category เดียวกัน
- `visibility` ต้องเป็น `PUBLIC`, `INTERNAL`, `RESTRICTED`
- `end_date` ต้องไม่ก่อน `start_date`
- ต้องมี `faculty[]` อย่างน้อย 1 คน
- `faculty[].faculty_id` ต้องเลือก
- `faculty[].academic_period_id` ควรเลือกเพื่อรองรับหลายปีการศึกษา
- `faculty[].contribution_order` ถ้ามีต้องเป็น integer >= 1
- `faculty[].contribution_percent` ถ้ามีต้องอยู่ในช่วง `0-100`
- ผลรวม contribution percent ถ้าส่งครบทุกคนควรไม่เกิน `100`
- numeric fields เช่น `quantity`, `credits`, `hours`, `student_count`, `budget_amount` ต้องไม่ติดลบ
- `detail.kind` ต้องสอดคล้องกับ category/type
- `publication_year` ถ้ามีต้องอยู่ในช่วง `1900-3000`
- `student_identifier_policy` ต้องเป็น `REDACTED`, `INTERNAL_ONLY`, หรือ `NOT_STORED`
- `reference_type = URL` ต้องมี `external_url`
- evidence visibility ต้องไม่กว้างกว่า work item โดยไม่ตั้งใจ เช่น work item `INTERNAL` ไม่ควรสร้าง evidence `PUBLIC` เว้นแต่ทีมตัดสินใจ explicit

Client ห้าม submit:

- `created_by`
- `updated_by`
- `audit_event.actor_user_id`
- `status`
- `deleted_at`

## Backend Error Mapping

ต้อง map validation error จาก backend กลับเข้า form field:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid work item payload",
    "details": [
      {
        "field": "faculty[1].faculty_id",
        "message": "faculty_id does not exist"
      },
      {
        "field": "work_type_code",
        "message": "work_type_code must belong to category_code"
      }
    ]
  }
}
```

กติกา UI:

- field-level error ต้องแสดงใกล้ field นั้น
- form-level error ใช้สำหรับ error ที่ map field ไม่ได้
- `401` ให้ redirect login หรือ clear session ตาม #76
- `403` ให้แสดง no-permission state
- `404` ใน edit mode ให้แสดง not found/admin-safe state
- `409` ให้แสดง conflict message และแนะนำ reload
- `500` ให้แสดง retry โดยไม่โชว์ stack trace

## State Handling

### Create Mode

- โหลด master data options
- render empty form
- disable submit จน required fields ผ่านขั้นต่ำ
- submit แล้วแสดง saving state
- success แล้ว redirect ไป `/admin/work-items/{id}` หรือ `/admin/work-items` ตาม UX ที่ทีมเลือก

### Edit Mode

- โหลด master data options
- โหลด existing record จาก `GET /api/v2/admin/work-items/{id}`
- render values เดิม
- track dirty state
- ถ้าออกจากหน้าโดยยังไม่ save ให้เตือนผู้ใช้
- submit เฉพาะ payload ที่ต้องการแก้ หรือ payload normalized ตาม strategy ที่ทีมเลือก
- success แล้ว refresh data หรือแสดง saved state

### Loading / Error

- loading master data แยกจาก loading record
- master data fail ต้องแสดง retry
- edit record fail `404` ต้องแสดง not found
- auth fail `401/403` ตาม #76

## Suggested Frontend Files

ปรับตาม pattern repo ได้ แต่ควรมี responsibility ประมาณนี้:

```text
frontend/app/admin/work-items/new/page.tsx
frontend/app/admin/work-items/[id]/page.tsx
frontend/components/admin/work-item-form.tsx
frontend/components/admin/work-item-core-fields.tsx
frontend/components/admin/work-item-faculty-section.tsx
frontend/components/admin/work-item-detail-section.tsx
frontend/components/admin/work-item-evidence-section.tsx
frontend/lib/admin-api/work-items-client.ts
frontend/lib/admin-form/work-item-payload.ts
frontend/lib/admin-form/work-item-validation.ts
```

ควรแยก payload mapper ออกจาก UI component เพื่อให้ #79 reuse ได้ง่าย

## UX Requirements

- category/type เปลี่ยนแล้ว subtype fields ต้องชัดเจน
- ถ้าเปลี่ยน category/type แล้ว detail เดิมไม่ตรง ต้องเตือนก่อนล้าง subtype fields
- faculty contributor rows เพิ่ม/ลบ/เรียงได้
- contribution order ควร auto-fill ตามลำดับแต่แก้ได้
- form ไม่ควรทำให้ผู้ใช้คิดว่ากำลังสร้าง official report
- validation error ต้องบอก field ที่ต้องแก้
- edit mode ต้องโหลด existing values จาก deployed API จริง
- save button ต้องมี loading state
- cancel/back ควรพากลับ `/admin/work-items`
- mobile/desktop ต้องใช้งานได้ ไม่ล้นจอจนแก้ฟอร์มไม่ได้

## QA / Smoke Test Checklist

ต้องทดสอบกับ Cognito admin user และ AWS endpoints จริง:

- เปิด `/admin/work-items/new` แบบไม่ login แล้ว redirect `/admin/login`
- login admin แล้วเปิด `/admin/work-items/new` ได้
- master data dropdown โหลดจาก deployed #64 endpoints จริง
- create teaching work item แล้ว `POST /api/v2/admin/work-items` สำเร็จ
- create response ได้ `id`, `status`, `visibility`, links
- เปิด `/admin/work-items/{id}` แล้วโหลด existing values จาก `GET /api/v2/admin/work-items/{id}`
- edit title/description/visibility แล้ว `PATCH /api/v2/admin/work-items/{id}` สำเร็จ
- faculty contributor เพิ่ม/แก้/ลบ row ได้และ payload ถูก
- subtype detail เปลี่ยนตาม category/type
- evidence metadata submit ได้โดยไม่ upload file
- backend validation error map เข้า form fields
- no token ได้ `401`
- non-admin token ได้ `403` ถ้าทดสอบได้
- public `/outputs` เห็น created record เฉพาะเมื่อ `visibility = PUBLIC` และ `status = ACTIVE`
- public `/outputs` ไม่เห็น `INTERNAL`, `RESTRICTED`, หรือ deleted records
- CloudWatch logs มี create/update request
- Aurora มี row ใน `work_item`, `faculty_work_item`, subtype detail, `evidence_reference`, `audit_event`

## QA Evidence ที่ต้องแนบตอนปิดการ์ด

ควรมี:

- screenshot create form
- screenshot edit form loaded with existing values
- screenshot subtype fields ตอนเลือก teaching/publication/service อย่างน้อย 1-2 แบบ
- Network tab/log ของ master data endpoints
- Network tab/log ของ `POST /api/v2/admin/work-items`
- Network tab/log ของ `GET /api/v2/admin/work-items/{id}`
- Network tab/log ของ `PATCH /api/v2/admin/work-items/{id}`
- screenshot validation error
- screenshot success state หรือ redirect หลัง save
- SQL/Aurora หรือ API evidence ว่า record ถูกสร้าง/แก้จริง
- CloudWatch log note ของ create/update
- note ว่าไม่แนบ raw token/password/secret

ห้ามแนบ:

- raw JWT token
- password
- Cognito temporary password
- AWS access key/secret key
- Secrets Manager secret value

## Acceptance Criteria

- [ ] `/admin/work-items/new` เปิดได้เฉพาะ admin
- [ ] `/admin/work-items/{id}` เปิดได้เฉพาะ admin
- [ ] form แสดง field หลักครบ
- [ ] category/type options ใช้ master data contract จาก AWS จริง
- [ ] subtype fields เปลี่ยนตาม category/type
- [ ] faculty contributors รองรับหลายคน
- [ ] faculty rows เพิ่ม/ลบ/เรียงได้
- [ ] evidence metadata section ทำงานได้
- [ ] validation error ชัดเจน
- [ ] form payload shape ตรงกับ #70/#71
- [ ] create form submit ไป deployed #70 API จริง
- [ ] edit form load existing value จาก deployed #71 admin detail จริง
- [ ] edit form submit ไป deployed #71 PATCH API จริง
- [ ] backend validation error จาก AWS endpoint map เข้า form ได้
- [ ] handle `401/403/400/404/409/500` ได้เหมาะสม
- [ ] frontend ไม่ submit `created_by`, `updated_by`, `status`, `deleted_at`
- [ ] ไม่มี token/secret/password ใน source, console, docs หรือ evidence
- [ ] มี QA evidence สำหรับ create/edit happy path และ validation error

## Review Checklist

Frontend:

- [ ] form state ไม่ซับซ้อนเกินดูแล
- [ ] payload mapper แยกจาก UI component
- [ ] validation แยกพอให้ test ได้
- [ ] optional fields ไม่ทำให้ submit payload สกปรก
- [ ] dirty state ทำงาน
- [ ] category/type change ไม่ล้างข้อมูลโดยไม่เตือน
- [ ] mobile/desktop ไม่ล้นจนใช้งานไม่ได้

Backend/API:

- [ ] payload shape match create/update API
- [ ] validation rules ไม่ขัดกับ backend
- [ ] `POST`, `GET admin detail`, `PATCH` ใช้ Cognito token จริง
- [ ] API response เพียงพอให้ UI redirect/refresh state
- [ ] CORS/env ใช้กับ deployed frontend ได้

Security:

- [ ] protected route ทำงานจริง
- [ ] non-admin user เข้า form ไม่ได้
- [ ] ไม่ log token/password
- [ ] evidence metadata ไม่ส่ง signed URL หรือ AWS credential
- [ ] public route ไม่เห็น internal/restricted/deleted โดยไม่ตั้งใจ

QA:

- [ ] test create happy path
- [ ] test edit happy path
- [ ] test validation error
- [ ] test unauthorized/forbidden
- [ ] test subtype อย่างน้อย teaching และ publication/service
- [ ] test กับ Cognito admin user และ AWS endpoint จริง

## Dependencies

Blocked by:

- #64 Build Master Data API
- #70 Build Admin Create Work Item API
- #71 Build Admin Update / Soft Delete API
- #76 Build Admin Login UI
- #77 Build Admin Work Item List UI

Blocks:

- #79 Integrate Admin UI with Auth & CRUD API

Related:

- #68 Build Work Item Detail API
- #69 Configure Admin Authentication
- #81 Final Integration / Deploy / Demo Docs

## Suggested Labels

- `v2`
- `frontend`
- `admin`
- `form`
- `api`
- `ready-for-agent`

## Suggested Owner

Frontend Developer

Reviewers:

- Tech Lead
- Backend Developer
- Security Reviewer
- QA / Integration

## Estimate

1-1.5 days

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อ Admin มี create/edit form ที่ protected ด้วย Cognito จริง ใช้ deployed Master Data/Admin APIs จริง สร้างและแก้ข้อมูลใน Aurora ผ่าน AWS endpoint ได้ครบ core/faculty/subtype/evidence metadata พร้อม validation, backend error mapping, dirty state, QA evidence และไม่เปิดเผย token/secret หรือทำให้ public routes เห็นข้อมูลที่ไม่ควรเห็น
