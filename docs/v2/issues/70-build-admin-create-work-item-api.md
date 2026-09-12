# [V2] Build Admin Create Work Item API #70

## สรุป

สร้าง `POST /api/v2/admin/work-items` สำหรับให้ Admin pilot เพิ่ม work item ใหม่เข้า V2 repository พร้อม faculty assignment, period, category/type, subtype detail, evidence metadata และ audit event

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #56 แต่ GitHub issue จริงใช้ #70

## Production AWS Requirement

การ์ดนี้ต้องเป็น protected AWS admin API จริง:

```text
Amazon API Gateway
→ Cognito/Admin auth
→ Admin Lambda
→ RDS Data API transaction
→ Aurora PostgreSQL Serverless v2
```

ต้องสร้าง record ใน Aurora จริงและมี audit trail จริง ห้ามปิดด้วย mock repository เท่านั้น

## Background

V2 ไม่ได้เป็นแค่ public read-only page แต่เป็น repository foundation ที่ Admin pilot สามารถจัดการข้อมูลเบื้องต้นได้

การเพิ่ม work item ต้องไม่ insert เฉพาะ `work_item` อย่างเดียว เพราะข้อมูลหนึ่งรายการต้องมี relation และ provenance ที่สอดคล้องกัน เช่น:

- `faculty_work_item`
- subtype detail table
- `evidence_reference`
- `audit_event`

## เป้าหมาย

สร้าง create API ที่:

- รับ payload แบบ structured
- validate category/type/period/faculty/visibility
- insert หลาย table ใน transaction
- record audit event
- return created work item id/detail summary
- require Admin auth จาก #69

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- update/delete/restore
- admin create/edit UI
- evidence file upload
- official approval workflow
- import pipeline
- workload scoring

## Scope

### ต้องทำ

- implement `POST /api/v2/admin/work-items`
- require authenticated `ADMIN`
- validate payload fields:
  - title
  - category/type
  - faculty contributors
  - academic/evaluation period
  - visibility
  - subtype detail
  - evidence references
- insert:
  - `work_item`
  - `faculty_work_item`
  - one subtype detail table when provided
  - `evidence_reference` rows when provided
  - `audit_event`
- use transaction through Data API or repository transaction adapter
- configure API Gateway protected route สำหรับ `POST /api/v2/admin/work-items`
- ใช้ RDS Data API transaction (`BeginTransaction`, `ExecuteStatement`, `Commit/Rollback`) หรือ abstraction ที่ทำงานเทียบเท่า
- ใช้ `CS361V2AdminLambdaRole` หรือ role ที่มีสิทธิ์จำกัดตาม #48
- เพิ่ม CloudWatch logs สำหรับ request id, validation failure, transaction rollback และ success
- add idempotency/conflict policy if the implementation supports it
- add tests for valid create, invalid payload, unauthorized, transaction rollback
- เพิ่ม AWS smoke test ที่สร้าง record จริงใน Aurora target environment

### ไม่ต้องทำ

- edit existing work item
- soft delete
- restore
- admin UI form
- Cognito setup beyond using guard from #69

## API Contract

```http
POST /api/v2/admin/work-items
Authorization: Bearer <admin-token>
```

ตัวอย่าง payload:

```json
{
  "title": "CS333 Software Engineering Lecture",
  "description": "Lecture workload for semester 2/2567",
  "category_code": "TEACHING",
  "work_type_code": "TEACHING_LECTURE",
  "visibility": "INTERNAL",
  "academic_period_id": "ap_2567_2",
  "evaluation_period_id": "eval_2567_h2",
  "faculty": [
    {
      "faculty_id": "fac_prapaporn",
      "role": "INSTRUCTOR",
      "contribution_order": 1,
      "contribution_percent": 100
    }
  ],
  "detail": {
    "kind": "teaching",
    "course_code": "CS333",
    "course_name": "Software Engineering",
    "section": "1",
    "credits": 3
  },
  "evidence": [
    {
      "label": "Course syllabus",
      "reference_type": "DOCUMENT_ID",
      "reference_value": "demo-doc-cs333-syllabus",
      "visibility": "INTERNAL"
    }
  ]
}
```

Response:

```json
{
  "id": "wi-generated-id",
  "status": "ACTIVE",
  "message": "created"
}
```

## Validation Rules

- `title` required และต้องไม่เป็น empty string
- `category_code` ต้องมีอยู่และ active
- `work_type_code` ต้องอยู่ใต้ category ที่ส่งมา
- ต้องมี faculty อย่างน้อย 1 คน
- `contribution_percent` ถ้ามีต้องอยู่ในช่วง `0-100`
- visibility ต้องเป็น `PUBLIC`, `INTERNAL`, หรือ `RESTRICTED`
- subtype `detail.kind` ต้องสอดคล้องกับ category/type
- evidence visibility ต้องไม่กว้างกว่า work item โดยไม่ตั้งใจ

## Acceptance Criteria

- [ ] admin create endpoint ใช้งานได้
- [ ] unauthenticated request return `401`
- [ ] non-admin request return `403`
- [ ] valid payload insert record ครบทุก table ที่เกี่ยวข้อง
- [ ] invalid payload return `400` พร้อม details
- [ ] transaction rollback เมื่อ insert ส่วนใดส่วนหนึ่ง fail
- [ ] audit event ถูกสร้างสำหรับ create action
- [ ] created record อ่านกลับผ่าน read/detail API ได้ตาม visibility
- [ ] API Gateway protected route deploy แล้ว
- [ ] Admin Lambda insert เข้า Aurora ผ่าน RDS Data API transaction จริง
- [ ] CloudWatch logs มีหลักฐาน success และ rollback/error path
- [ ] smoke test สร้าง record จริงและอ่านกลับได้

## Review Checklist

Backend:

- [ ] mutation ใช้ transaction
- [ ] validation logic ไม่กระจายซ้ำหลายที่
- [ ] audit event มี actor, action, entity id และ request id
- [ ] production path ไม่อ่าน/เขียน fixture file

Security:

- [ ] route require ADMIN
- [ ] payload ไม่สามารถ set audit actor เองจาก client
- [ ] evidence reference ไม่เปิด secret/private path โดยไม่ตั้งใจ

QA:

- [ ] create teaching/publication/research example ได้อย่างน้อย 2 subtype
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

การ์ดนี้ถือว่าเสร็จเมื่อ Admin สามารถสร้าง work item ใหม่บน AWS endpoint จริงพร้อม relation/subtype/evidence/audit ผ่าน API เดียวแบบ transaction-safe, ข้อมูลถูกเขียนเข้า Aurora จริง, อ่านผลลัพธ์กลับได้ และมี CloudWatch/Aurora smoke evidence
