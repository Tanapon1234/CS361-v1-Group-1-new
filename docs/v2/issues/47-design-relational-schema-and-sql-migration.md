# [V2] Design Relational Schema & SQL Migration

## สรุป

ออกแบบ relational schema สำหรับ V2 Faculty Output Repository และเตรียม SQL migration/seed baseline ที่การ์ด backend, import, migration และ frontend ใช้อ้างอิงร่วมกันได้

การ์ดนี้เป็นฐานข้อมูลกลางของ V2 ถ้า schema ยังไม่ชัด งาน API, import, search/filter, admin CRUD และ V1 migration จะเริ่มทำจริงได้ยาก เพราะแต่ละทีมจะไม่รู้ว่าข้อมูลควรอยู่ table ไหน field ไหนเป็น required และความสัมพันธ์ระหว่าง faculty กับ work item ต้องเก็บอย่างไร

## Background

V1 ใช้ S3 serving JSON เป็น runtime data เพราะข้อมูลเป็น public read-only และ query ไม่ซับซ้อน

V2 ต้องรองรับข้อมูลผลงานและภาระงานหลายประเภท หลายปีการศึกษา และมีความสัมพันธ์ระหว่างข้อมูลสูง เช่น:

- อาจารย์หนึ่งคนมีผลงานหลายรายการ
- ผลงานหนึ่งรายการอาจมีอาจารย์หลายคนร่วมกัน
- ผลงานหนึ่งรายการต้องผูกกับ academic period และอาจผูกกับ evaluation period
- ผลงานแต่ละประเภทมี detail ต่างกัน เช่น teaching, publication, supervision, service, administration
- ข้อมูลบางส่วนเป็น public ได้ แต่บางส่วนเป็น internal หรือ restricted
- import ต้อง trace ได้ว่าข้อมูลมาจาก source/batch/record ใด
- admin mutation ต้อง audit ได้

ดังนั้น V2 ต้องใช้ relational repository ที่มี key, constraint, index และ visibility boundary ชัดเจน

## เป้าหมาย

ออกแบบและจัดทำฐาน schema สำหรับ Aurora PostgreSQL ของ V2 ให้พร้อมสำหรับการ์ดถัดไป

ผลลัพธ์ของการ์ดนี้ต้องตอบได้ว่า:

- V2 มี table อะไรบ้าง
- แต่ละ table มีหน้าที่อะไร
- primary key / foreign key / unique constraint คืออะไร
- field ไหน required / optional
- visibility ใช้กับ table ไหน
- soft delete อยู่ตรงไหน
- academic period และ evaluation period แยกกันอย่างไร
- work category และ work type seed อย่างไร
- index ขั้นต้นสำหรับ search/filter คืออะไร
- migration file และ seed file วางไว้ที่ไหน

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- สร้าง Aurora cluster จริง
- เปิด RDS Data API จริง
- เขียน Lambda API
- เขียน import pipeline
- migrate ข้อมูล V1 จริง
- seed demo dataset หลายปีเต็ม
- implement admin CRUD
- implement frontend
- ออกแบบ workload scoring engine
- ทำ official workload sheet/report generation

## Scope

### ต้องทำ

- ออกแบบ ERD สำหรับ V2 repository
- เขียน SQL migration baseline
- เขียน seed master data baseline
- เขียน data dictionary ขั้นต้น
- กำหนด constraints สำคัญ
- กำหนด indexes สำคัญ
- กำหนด visibility/status convention
- กำหนด audit/import/provenance tables
- บันทึก design decision สำคัญที่เกี่ยวกับ schema

### ไม่ต้องทำ

- deploy database จริง
- query database จริงจาก Lambda
- import ข้อมูลจริง
- build API response mapper

## Schema Baseline ที่ต้องออกแบบ

ต้องครอบคลุม table ต่อไปนี้:

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

## Core Modeling Rules

### `faculty`

ใช้เก็บข้อมูลอาจารย์หลัก

ต้องมี:

- stable internal id
- `public_slug` ที่ preserve จาก V1
- ชื่อไทย/อังกฤษ
- academic position
- public contact fields ที่เปิดเผยได้
- public visibility flag
- created/updated timestamps

Rule สำคัญ:

- `public_slug` ต้อง unique
- ห้าม generate slug ใหม่จนทำให้ URL V1 เดิมพัง

### `work_item`

เป็นแกนกลางของผลงานหรือภาระงานทุกประเภท

ต้องรองรับ:

- category
- work type
- title
- description
- date range
- visibility
- status
- source/provenance reference
- source-reported score/weight ถ้าต้องเก็บจากแบบฟอร์ม
- created/updated/deleted timestamps

Rule สำคัญ:

- `visibility` ต้องเป็น `PUBLIC`, `INTERNAL`, หรือ `RESTRICTED`
- `status` ขั้นต่ำใช้ `ACTIVE` และ `DELETED`
- delete จาก admin ต้องเป็น soft delete ไม่ใช่ hard delete
- score/weight ที่มาจากแบบฟอร์มเป็น source-reported value ไม่ใช่ค่าที่ V2 คำนวณรับรองเอง

### `faculty_work_item`

ใช้เชื่อม faculty กับ work item แบบ many-to-many

ต้องรองรับ:

- faculty id
- work item id
- academic period id
- evaluation period id
- role
- contribution percent
- quantity / credits / hours
- source section code

Rule สำคัญ:

- publication/work item หนึ่งรายการอาจมี faculty หลายคน
- contribution percent ไม่จำเป็นต้อง sum = 100 เสมอ ถ้า source ไม่ได้ครอบคลุม contributor ทั้งหมด

### Subtype Detail Tables

ใช้เก็บรายละเอียดเฉพาะประเภทงาน

ต้องมีอย่างน้อย:

- `teaching_detail`
- `publication_detail`
- `research_project_detail`
- `supervision_detail`
- `service_detail`
- `administration_detail`

Rule สำคัญ:

- แต่ละ subtype table ใช้ `work_item_id` เป็น primary key และ foreign key ไปที่ `work_item`
- ห้าม copy โครงสร้างแบบฟอร์มภาระงาน 1:1 เป็น schema
- form section code เก็บเป็น metadata ได้ แต่ domain model ต้องเป็นกลาง

### `academic_period` และ `evaluation_period`

ต้องแยกกัน

ตัวอย่าง:

```text
academic_period = 2/2567
evaluation_period = 1 มกราคม 2568 - 30 มิถุนายน 2568
```

Rule สำคัญ:

- ห้าม derive academic year จาก calendar year ของ activity date โดยตรง
- `academic_period` ต้อง unique ตาม `academic_year + semester`

### `evidence_reference`

ใช้เก็บ metadata ของหลักฐาน

ต้องรองรับ:

- work item id
- reference type
- reference label
- external URL
- S3 key ถ้ามี
- mime type/checksum ถ้ามี
- visibility

Rule สำคัญ:

- public API ห้าม expose internal S3 key โดยตรง
- restricted evidence ต้องไม่หลุดไป public projection

### `import_batch` และ `source_record`

ใช้เก็บ import/provenance

ต้องรองรับ:

- source type/name/version
- S3 source key
- import status
- record count / valid count / warning count / error count
- source hash
- source record key
- target entity reference

Rule สำคัญ:

- ต้องออกแบบให้ import ซ้ำไฟล์เดิมแล้วไม่เกิด duplicate
- ใช้ `source_system + source_record_key + source_hash` เป็นฐานของ idempotency

### `audit_event`

ใช้เก็บประวัติ admin/import mutation

ต้องรองรับ:

- actor subject
- action
- entity type
- entity id
- before JSON
- after JSON
- occurred at

Rule สำคัญ:

- audit table ห้ามเปิดให้ public API

## Required Constraints

อย่างน้อยต้องมี:

- primary key ทุก table
- foreign key ระหว่าง table หลัก
- unique `faculty.public_slug`
- unique `academic_period(academic_year, semester)`
- unique `faculty_interest(faculty_id, interest_type, value)`
- duplicate protection สำหรับ DOI ถ้ามีใน `publication_detail`
- check constraint สำหรับ `work_item.visibility`
- check constraint หรือ convention สำหรับ `work_item.status`
- constraint สำหรับ contribution percent ให้อยู่ในช่วง 0-100 ถ้ามีค่า

## Required Indexes

อย่างน้อยต้องออกแบบ index สำหรับ:

- filter by faculty
- filter by academic period
- filter by category
- filter by work type
- filter by visibility
- filter by status / exclude deleted
- date range
- publication year
- DOI lookup
- source record idempotency lookup

ตัวอย่าง index ที่ควรพิจารณา:

```sql
CREATE INDEX idx_fwi_faculty ON faculty_work_item(faculty_id);
CREATE INDEX idx_fwi_academic_period ON faculty_work_item(academic_period_id);
CREATE INDEX idx_work_item_category ON work_item(category_code);
CREATE INDEX idx_work_item_type ON work_item(work_type_id);
CREATE INDEX idx_work_item_visibility ON work_item(visibility);
CREATE INDEX idx_work_item_status ON work_item(status);
CREATE INDEX idx_work_item_dates ON work_item(start_date, end_date);
CREATE INDEX idx_publication_year ON publication_detail(publication_year);
```

## Seed Master Data

ต้องมี seed baseline สำหรับ `work_category`

ขั้นต่ำ:

- `TEACHING`
- `RESEARCH`
- `SUPERVISION`
- `ACADEMIC_SERVICE`
- `ADMINISTRATION`
- `OTHER`

ต้องมี seed baseline สำหรับ `work_type` อย่างน้อยให้ครอบคลุม:

- `LECTURE`
- `LAB`
- `SEMINAR`
- `SENIOR_PROJECT`
- `COOPERATIVE_EDUCATION`
- `THESIS`
- `PUBLICATION`
- `RESEARCH_PROJECT`
- `RESEARCH_GRANT`
- `COMMITTEE`
- `COURSE_COORDINATOR`
- `ACADEMIC_REVIEWER`
- `EDITOR`
- `INVITED_SPEAKER`

## Expected Files

สร้างหรือเตรียมไฟล์อย่างน้อย:

```text
docs/v2/erd.md
docs/v2/data-contract.md
docs/v2/schema-decisions.md
database/migrations/001_base.sql
database/seeds/001_master_data.sql
database/README.md
```

ถ้าเลือกชื่อไฟล์ต่างจากนี้ ต้องระบุเหตุผลและ link จาก `docs/v2/README.md`

## Acceptance Criteria

- [ ] มี ERD ของ V2 repository
- [ ] มี data dictionary ขั้นต้น
- [ ] มี SQL migration baseline
- [ ] มี seed master data baseline
- [ ] table หลักครบตาม schema baseline
- [ ] `faculty.public_slug` ถูกออกแบบให้ preserve V1 slug ได้
- [ ] `work_item` เป็น central entity ของ work/output ทุกประเภท
- [ ] subtype detail tables แยกจาก `work_item`
- [ ] `faculty_work_item` รองรับ many-to-many relationship
- [ ] `academic_period` และ `evaluation_period` แยกกันชัดเจน
- [ ] มี visibility model `PUBLIC`, `INTERNAL`, `RESTRICTED`
- [ ] มี status model ขั้นต่ำ `ACTIVE`, `DELETED`
- [ ] soft delete ถูกออกแบบผ่าน `deleted_at` และ/หรือ `status`
- [ ] มี constraints สำคัญครบ
- [ ] มี indexes สำหรับ search/filter ขั้นต้น
- [ ] มี duplicate/idempotency strategy สำหรับ import
- [ ] มี duplicate strategy สำหรับ publication DOI/title
- [ ] มี evidence metadata model
- [ ] มี audit event model
- [ ] ไม่มี table ที่ copy โครงสร้างแบบฟอร์มภาระงานแบบ 1:1 โดยไม่ผ่าน domain model
- [ ] เอกสารอธิบายว่า source-reported score/weight ไม่ใช่ scoring engine ของ V2
- [ ] migration SQL สามารถ review ได้โดยไม่ต้อง deploy จริง

## Review Checklist

Data / Database:

- [ ] schema สอดคล้องกับ V2 domain
- [ ] constraints ครอบคลุมข้อมูลสำคัญ
- [ ] index strategy รองรับ query หลัก
- [ ] ไม่มีการผูก schema กับแบบฟอร์มภาระงานมากเกินไป

Backend:

- [ ] schema รองรับ Master Data API
- [ ] schema รองรับ Work Item Search API
- [ ] schema รองรับ Faculty Work Items API
- [ ] schema รองรับ Work Item Detail API
- [ ] schema รองรับ Admin Create/Edit/Soft Delete API

Cloud / AWS:

- [ ] SQL เหมาะกับ Aurora PostgreSQL
- [ ] ไม่มี dependency ที่ขัดกับ RDS Data API
- [ ] migration/seed แยกไฟล์ชัดเจน

Frontend:

- [ ] schema มี master data พอสำหรับ filter dropdown
- [ ] category/type/period/faculty query ใช้ทำ UI ได้
- [ ] detail model เพียงพอสำหรับหน้า `/outputs/{id}`

QA / Integration:

- [ ] acceptance queries ของ V2 สามารถทดสอบจาก schema นี้ได้
- [ ] public/internal/restricted leakage สามารถทดสอบได้
- [ ] V1 slug compatibility สามารถทดสอบได้

## Dependencies

Blocked by:

- #46 Freeze V2 Scope, Architecture & Interface Contracts

Blocks:

- #48 Provision Aurora / Data API / Secret / IAM
- #49 Define V1 to V2 Data Mapping
- #50 Prepare Multi-Year Demo Dataset
- #51 Build Master Data API
- #52 Build Work Item List/Search/Filter API
- #53 Build Faculty Work Items API
- #54 Build Work Item Detail API
- #56 Build Admin Create Work Item API
- #57 Build Admin Update / Soft Delete API
- #66 Execute Migration & Preserve V1 Compatibility

## Suggested Labels

- `v2`
- `database`
- `schema`
- `migration`
- `blocking`
- `ready-for-review`

## Suggested Owner

Data / Database Developer

Reviewers:

- Tech Lead
- Backend Developer
- Cloud Developer
- QA / Integration

## Estimate

1-1.5 days

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อทีมมี schema, migration baseline, seed baseline และ data contract ที่เพียงพอให้ backend, cloud, import, migration และ frontend เริ่มงานต่อได้โดยไม่ต้องเดา table, field, relationship หรือ visibility rules เอง
