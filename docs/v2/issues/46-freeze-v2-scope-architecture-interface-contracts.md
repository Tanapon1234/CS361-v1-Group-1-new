# [V2] Freeze Scope, Architecture & Interface Contracts

## Implementation Artifacts

ไฟล์ผลลัพธ์สำหรับการ์ดนี้ถูกเตรียมไว้แล้วใน repo:

- `docs/v2/V2_Central_Design.md` — เอกสาร freeze หลักของ V2 scope, architecture, interface contracts, entity baseline, visibility boundary, V1 compatibility และ dependency map
- `docs/v2/README.md` — สารบัญเอกสาร V2 และ link ไปยัง artifacts/issue cards
- `docs/v2/v2-aws-service-architecture.jpg` — ภาพ architecture หลักแบบ AWS service-icon style
- `docs/v2/v2-full-architecture-clean.png` — ภาพ architecture เวอร์ชัน clean/readable สำหรับรายงานหรือ slide
- `docs/v2/v2-full-architecture.png` — ภาพ architecture เวอร์ชันเต็มอีกไฟล์สำหรับใช้แทน/สำรองในเอกสาร

## สรุป

ล็อกขอบเขต สถาปัตยกรรม และสัญญาการทำงานร่วมกันของ V2 ก่อนเริ่มลงมือ implement

การ์ดนี้มีไว้เพื่อให้ทุกคนในทีมเข้าใจตรงกันว่า V2 คืออะไร ไม่ใช่อะไร ใช้สถาปัตยกรรมแบบไหน ใช้ entity และ route ชื่ออะไร และจะรักษา V1 ไม่ให้พังอย่างไร

เมื่อการ์ดนี้เสร็จ ทีม Data, Backend, Cloud, Frontend และ QA/Integration ควรสามารถเริ่มการ์ดถัดไปได้โดยไม่ต้องตีความ scope กันใหม่

## Background

V1 ปัจจุบันเป็นระบบ **Faculty Profile / Public Output** แบบ public read-only

V1 ใช้ flow หลักคือ:

```text
Controlled source snapshot
        ↓
prepare_faculty_data.py
        ↓
public-safe serving JSON
        ↓
S3 private serving/*
        ↓
Lambda read-only API
        ↓
API Gateway
        ↓
Next.js frontend
```

V1 เหมาะกับการแสดงข้อมูลอาจารย์และผลงานบางส่วนที่เปิดเผยต่อสาธารณะได้ แต่ยังไม่ใช่ repository กลางสำหรับจัดเก็บผลงานและภาระงานหลายปี

V2 จะยกระบบจาก public profile viewer ไปเป็น **Managed Multi-year Faculty Output Repository** ที่รองรับข้อมูลหลายประเภท เช่น งานสอน งานวิจัย สิ่งพิมพ์ งานบริการ การดูแลนักศึกษา งานบริหาร หลักฐาน และ provenance

## เป้าหมาย

จัดทำและ freeze baseline ของ V2 ให้ทีมเห็นตรงกันในประเด็นต่อไปนี้:

- ขอบเขต V2
- สิ่งที่ไม่ทำใน V2
- สถาปัตยกรรมหลัก
- service responsibilities
- domain entity หลัก
- API namespace และ route baseline
- frontend route baseline
- admin pilot boundary
- public/internal/restricted visibility boundary
- V1 compatibility rule
- dependency map สำหรับการ์ด #47-#67

## Non-Goals

การ์ดนี้ยังไม่ใช่การ implement ระบบ

ห้ามทำสิ่งต่อไปนี้ใน scope ของการ์ดนี้:

- สร้าง Aurora จริง
- เขียน production database migration
- สร้าง Lambda handler สำหรับ `/api/v2`
- สร้างหน้า frontend `/outputs`
- สร้างหน้า frontend `/admin`
- ตั้งค่า Cognito จริง
- migrate ข้อมูล V1
- implement workload scoring
- เพิ่ม faculty self-service
- เพิ่ม reviewer workflow
- เพิ่ม role-based access control หลาย role

งานเหล่านี้ต้องอยู่ในการ์ดถัดไป

## V2 Product Definition

V2 คือ **Managed Multi-year Faculty Output Repository**

ระบบต้องรองรับการจัดเก็บและเรียกดูข้อมูลต่อไปนี้อย่างเป็นระบบ:

- ข้อมูลอาจารย์
- งานสอน
- งานวิจัย
- ผลงานตีพิมพ์ / publication
- งานบริการวิชาการ
- การดูแลนักศึกษา / supervision
- งานบริหาร
- หลักฐานหรือเอกสารอ้างอิง
- import/provenance metadata
- ข้อมูลหลายปีการศึกษา
- การค้นหา กรอง และเรียกดูรายละเอียดตามเงื่อนไข

V2 อาจมี Admin pilot สำหรับเพิ่ม แก้ไข และ soft delete ข้อมูลใน repository ได้ แต่ต้องระบุชัดเจนว่าเป็นเพียง **V2+ Admin Repository Management Pilot** ไม่ใช่ V3 Secure Faculty Workspace เต็มรูปแบบ

## V2 In Scope

- รักษา V1 public faculty experience เดิม
- เพิ่ม architecture สำหรับ managed repository
- ใช้ relational domain model
- รองรับหลาย academic year และ semester
- รองรับ search/filter ตาม faculty, year, semester, category, type และ keyword
- รองรับ work item detail
- วางแนว controlled import
- วางแนว provenance
- วางแนว evidence metadata
- กำหนด Public/Internal/Restricted data classification
- กำหนด Admin-only CRUD pilot boundary

## V2 Out of Scope

- Faculty self-service
- Staff workspace
- Reviewer workspace
- Manager dashboard
- Approval workflow
- Submit / reject / return workflow
- Official workload score calculation engine
- Official workload sheet generation
- Annual report generation
- Department aggregation dashboard
- Full evidence upload workflow
- Advanced BI / analytics
- CloudFront เป็น core dependency
- OpenSearch
- RDS Proxy
- ECS / EKS
- Full Infrastructure as Code automation
- Performance/cost before-after optimization

## Architecture ที่ต้อง Freeze

Architecture หลักของ V2:

```text
Next.js / Vercel
        ↓
Amazon API Gateway HTTP API
        ↓
AWS Lambda
        ↓
Amazon RDS Data API
        ↓
Aurora PostgreSQL Serverless v2
```

Supporting services:

- Amazon S3 สำหรับ `landing/`, `archive/`, `evidence/`, `metadata/`, `exports/`, และ public projection
- AWS Secrets Manager สำหรับ database secret
- AWS IAM สำหรับ least privilege ระหว่าง services
- Amazon CloudWatch สำหรับ logs, metrics, alarms
- Amazon Cognito User Pool สำหรับ Admin pilot authentication

CloudFront ให้ถือเป็น optional/deferred service ไม่ใช่ blocker ของ V2

## V1 Compatibility Rule

V1 ต้องไม่พัง

สิ่งต่อไปนี้ต้องยังทำงานได้:

- `/faculties`
- `/faculties/{id}`
- `/api/v1/faculties`
- `/api/v1/faculties/{id}`
- faculty public slug เดิม เช่น `prapaporn-rattanatamrong`

V2 อาจสร้าง public-safe projection จาก Aurora กลับไปเป็นข้อมูลสำหรับ V1 ได้ในอนาคต แต่ contract เดิมของ V1 ต้องไม่ถูกเปลี่ยนแบบ breaking change

## Core Domain Entities ที่ต้อง Freeze

Baseline entity names:

- `faculty`
- `faculty_education`
- `faculty_interest`
- `academic_period`
- `evaluation_period`
- `work_category`
- `work_type`
- `work_item`
- `faculty_work_item`
- `teaching_detail`
- `publication_detail`
- `research_project_detail`
- `supervision_detail`
- `service_detail`
- `administration_detail`
- `evidence_reference`
- `import_batch`
- `source_record`
- `audit_event`

## Modeling Decision สำคัญ

`work_item` เป็นแกนกลางของผลงานหรือภาระงานทุกประเภท

รายละเอียดเฉพาะประเภทงานให้แยกไปอยู่ใน subtype table เช่น:

- `teaching_detail`
- `publication_detail`
- `research_project_detail`
- `supervision_detail`
- `service_detail`
- `administration_detail`

ความสัมพันธ์ระหว่างอาจารย์กับผลงานให้ใช้ `faculty_work_item` เพราะผลงานหนึ่งรายการอาจมีอาจารย์หลายคน และแต่ละคนอาจมี role หรือ contribution ไม่เท่ากัน

## Academic Period vs Evaluation Period

ต้องแยก concept ต่อไปนี้ออกจากกัน:

- `academic_period`
- `evaluation_period`

เหตุผลคือปีการศึกษา เช่น `2/2567` อาจอยู่ในช่วงปีปฏิทิน 2568 ได้ จึงห้าม derive academic year จาก calendar year ของ activity date โดยตรง

## Data Visibility Boundary

Freeze visibility levels ต่อไปนี้:

- `PUBLIC`
- `INTERNAL`
- `RESTRICTED`

Public API และ public projection ต้องเปิดเฉพาะข้อมูลที่ public-safe เท่านั้น

Frontend ซ่อนปุ่มหรือซ่อน field ไม่ถือว่าเป็น security control ต้อง enforce ที่ backend/API

ตัวอย่าง:

- Faculty profile, public expertise, public publication เป็น `PUBLIC`
- Teaching workload และ internal service records ส่วนใหญ่เป็น `INTERNAL`
- Student-identifying supervision data และ sensitive evidence เป็น `RESTRICTED`

## API Namespace ที่ต้อง Freeze

V1 เดิมต้องคงไว้:

```http
GET /api/v1/faculties
GET /api/v1/faculties/{id}
```

V2 read API baseline:

```http
GET /api/v2/academic-periods
GET /api/v2/work-categories
GET /api/v2/work-types
GET /api/v2/faculties

GET /api/v2/work-items
GET /api/v2/work-items/{id}
GET /api/v2/faculties/{faculty_id}/work-items
```

V2 Admin pilot API baseline:

```http
POST   /api/v2/admin/work-items
GET    /api/v2/admin/work-items/{id}
PATCH  /api/v2/admin/work-items/{id}
DELETE /api/v2/admin/work-items/{id}
POST   /api/v2/admin/work-items/{id}/restore
```

`DELETE` หมายถึง soft delete เป็น default

## Frontend Route Baseline

V1 routes เดิมต้องคงไว้:

```text
/faculties
/faculties/{id}
```

V2 repository routes:

```text
/outputs
/outputs/{id}
```

V2 Admin pilot routes:

```text
/admin/login
/admin/work-items
/admin/work-items/new
/admin/work-items/{id}
```

## Admin Pilot Boundary

V2 Admin pilot มี human login role เดียวคือ `ADMIN`

ถ้ามี `SYSTEM` role ใน schema ให้ถือเป็น non-human actor สำหรับ import, projection, migration และ audit event เท่านั้น ไม่ใช่ user ที่ login ผ่านหน้า admin

Admin ทำได้:

- Login
- Browse work items
- Create work item
- Edit work item
- Soft delete work item
- Restore work item ถ้าทีมเลือกทำ
- Assign faculty
- Assign academic period
- Select category/type
- Add subtype detail
- Add evidence reference metadata
- View basic import/audit context ถ้ามี

Admin ยังทำไม่ได้:

- จัดการ role แบบ dynamic
- impersonate faculty
- ให้ faculty แก้ข้อมูลของตัวเอง
- ทำ approval workflow
- submit / reject / return records
- generate official workload sheet
- generate official annual report

## Expected Deliverables

ต้องมีเอกสาร planning/freeze สำหรับให้การ์ดถัดไปใช้อ้างอิงได้

Minimum deliverables:

- `docs/v2/V2_Central_Design.md` หรือเอกสาร baseline ที่เทียบเท่า
- V2 architecture diagram
- V2 in-scope / out-of-scope list
- V2/V3 boundary statement
- API route baseline
- Frontend route baseline
- Entity name baseline
- Visibility boundary
- V1 compatibility rule
- Dependency map สำหรับ issues #47-#67

ถ้าใช้ชื่อไฟล์อื่น ต้อง link ให้ชัดจาก `docs/v2/README.md`

## Acceptance Criteria

- [ ] เขียน V2 product definition แล้ว
- [ ] ทีม review และ approve V2 product definition แล้ว
- [ ] ระบุ V2 in-scope ชัดเจน
- [ ] ระบุ V2 out-of-scope ชัดเจน
- [ ] ระบุ V2+ Admin pilot boundary ชัดเจน
- [ ] ระบุชัดว่า Admin pilot ไม่ใช่ V3 Secure Faculty Workspace เต็มรูปแบบ
- [ ] เอกสาร target architecture พร้อมแล้ว
- [ ] เอกสาร AWS service responsibilities พร้อมแล้ว
- [ ] freeze core entity names แล้ว
- [ ] บันทึก modeling decision ของ `work_item` และ `faculty_work_item` แล้ว
- [ ] บันทึกว่า `academic_period` และ `evaluation_period` เป็นคนละ concept แล้ว
- [ ] บันทึก visibility values `PUBLIC`, `INTERNAL`, `RESTRICTED` แล้ว
- [ ] บันทึก public API visibility rule แล้ว
- [ ] บันทึก V1 compatibility rule แล้ว
- [ ] ระบุว่าต้อง preserve V1 public slug เดิม
- [ ] ระบุว่า `/api/v1` ห้าม breaking change
- [ ] approve V2 API namespace `/api/v2` แล้ว
- [ ] approve frontend route baseline แล้ว
- [ ] approve admin API route baseline แล้ว
- [ ] ระบุ deferred services แล้ว เช่น CloudFront, OpenSearch, RDS Proxy, ECS/EKS
- [ ] บันทึก issue dependency map สำหรับงาน V2 ที่เหลือแล้ว
- [ ] มี team review/sign-off section พร้อมสถานะ

## Review Checklist

Architecture / Tech Lead:

- [ ] Architecture เหมาะกับ V2
- [ ] V1 compatibility ได้รับการป้องกัน
- [ ] V2/V3 boundary ชัดเจน

Data / Database:

- [ ] Entity names ใช้ได้
- [ ] Multi-year model ชัดเจน
- [ ] แบบฟอร์มภาระงานจะถูก map เข้า domain model ไม่ใช่ copy schema 1:1

Backend:

- [ ] API namespace และ routes implement ได้
- [ ] Query/Admin responsibility split ชัดเจน
- [ ] Error/security expectations ชัดเจน

Cloud / AWS:

- [ ] Service choices เหมาะกับ target region
- [ ] IAM/Secrets/Data API direction ใช้ได้
- [ ] Deferred services เหมาะสม

Frontend:

- [ ] Route baseline ใช้ได้
- [ ] Repository UI และ Admin UI boundary ชัดเจน
- [ ] V1 frontend compatibility ได้รับการป้องกัน

QA / Integration:

- [ ] Definition of Done ตรวจสอบได้
- [ ] Security boundaries ทดสอบได้
- [ ] การ์ดถัดไปสามารถ verify แยกกันได้

## Dependencies

Blocked by:

- ไม่มี

Blocks:

- #47 Design Relational Schema & SQL Migration
- #48 Provision Aurora / Data API / Secret / IAM
- #49 Define V1 to V2 Data Mapping
- #50 Prepare Multi-Year Demo Dataset
- #51 Build Master Data API
- #52 Build Work Item List/Search/Filter API
- #53 Build Faculty Work Items API
- #54 Build Work Item Detail API
- #55 Configure Admin Authentication
- #56 Build Admin Create Work Item API
- #57 Build Admin Update / Soft Delete API
- #58 Build Repository Page Shell & Filter UI
- #59 Build Repository Result List & Pagination UI
- #60 Build Work Item Detail UI
- #61 Integrate Repository UI with Real API
- #62 Build Admin Login UI
- #63 Build Admin Work Item List UI
- #64 Build Admin Create/Edit Form UI
- #65 Integrate Admin UI with Auth & CRUD API
- #66 Execute Migration & Preserve V1 Compatibility
- #67 Final Integration / Deploy / Demo Docs

## Suggested Labels

- `v2`
- `architecture`
- `planning`
- `blocking`
- `ready-for-review`

## Suggested Owner

Tech Lead โดยมี Data, Backend, Cloud, Frontend และ QA/Integration ช่วย review

## Estimate

0.5-1 day

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อทีมสามารถเริ่ม #47-#67 ได้โดยไม่ต้องถกซ้ำเรื่อง scope, architecture, public/private boundary, V1 compatibility rule, route names หรือ core entity vocabulary ของ V2
