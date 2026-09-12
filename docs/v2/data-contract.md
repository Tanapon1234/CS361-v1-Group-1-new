# V2 Repository Data Contract

เอกสารนี้เป็น data dictionary และ contract ขั้นต้นสำหรับ schema ใน `database/migrations/001_base.sql`

สถานะ: Draft for Issue #47 review

---

## Global Conventions

### IDs

V2 ใช้ `text` primary key เพื่อให้ application/import pipeline สามารถสร้าง stable IDs ได้ เช่น:

- `fac_prapaporn`
- `wi_2025_0001`
- `ap_2567_2`
- `eval_2567_h2`

เหตุผลคือ migration/import ต้อง preserve provenance และอาจต้อง map กลับไปยัง V1 slug หรือ source record key

### Timestamps

ตารางหลักใช้:

- `created_at`
- `updated_at`
- `deleted_at` เฉพาะ table ที่รองรับ soft delete

ฐานข้อมูลตั้งค่า default เป็น `now()` แต่ responsibility การ update `updated_at` ระหว่าง mutation เป็นของ API/import layer ใน V2 baseline

### Visibility

Allowed values:

- `PUBLIC`
- `INTERNAL`
- `RESTRICTED`

Public API ต้องเปิดเฉพาะ `PUBLIC` และต้อง redact field ที่ไม่ public-safe

### Status

Baseline status สำหรับ repository records:

- `ACTIVE`
- `DELETED`

Import/source/audit tables มี status เฉพาะของตัวเอง เช่น `PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`, `WARNING`

---

## Table Dictionary

### `faculty`

ข้อมูลหลักของอาจารย์

| Column | Required | Purpose |
|---|---:|---|
| `id` | yes | stable internal faculty id |
| `public_slug` | yes | slug เดิมจาก V1 สำหรับ preserve public URL |
| `name_th` | no | ชื่อภาษาไทย |
| `name_en` | no | ชื่อภาษาอังกฤษ |
| `academic_position` | no | ตำแหน่งทางวิชาการ |
| `department` | no | สาขา/หน่วยงาน |
| `office_public` | no | ห้องทำงานที่เปิดเผยได้ |
| `phone_public` | no | เบอร์โทรที่เปิดเผยได้ |
| `email_public` | no | email ที่เปิดเผยได้ |
| `profile_image_url` | no | URL รูปโปรไฟล์ |
| `visibility` | yes | public visibility ของ profile |
| `status` | yes | `ACTIVE` หรือ `DELETED` |

Rules:

- `public_slug` unique
- ต้องมีอย่างน้อย `name_th` หรือ `name_en`
- soft delete ใช้ `status = 'DELETED'` และ `deleted_at`

### `faculty_education`

ประวัติการศึกษาของอาจารย์

| Column | Required | Purpose |
|---|---:|---|
| `faculty_id` | yes | อาจารย์เจ้าของประวัติ |
| `degree` | no | ชื่อวุฒิ |
| `field_of_study` | no | สาขาวิชา |
| `institution` | no | สถาบัน |
| `country` | no | ประเทศ |
| `graduation_year` | no | ปีที่จบ |
| `display_order` | yes | ลำดับแสดงผล |

### `faculty_interest`

ความเชี่ยวชาญ, research interest หรือ keyword

| Column | Required | Purpose |
|---|---:|---|
| `faculty_id` | yes | อาจารย์เจ้าของข้อมูล |
| `interest_type` | yes | `RESEARCH_INTEREST`, `EXPERTISE`, `KEYWORD` |
| `value` | yes | ข้อความ interest |
| `visibility` | yes | visibility ของ interest |

Rules:

- unique `(faculty_id, interest_type, value)`

### `academic_period`

ปีการศึกษาและภาคเรียน

| Column | Required | Purpose |
|---|---:|---|
| `academic_year` | yes | ปีการศึกษา เช่น 2567 |
| `semester` | yes | `1`, `2`, `3`, `SUMMER`, `OTHER` |
| `label` | yes | label เช่น `2/2567` |
| `start_date` | no | วันที่เริ่มโดยประมาณ |
| `end_date` | no | วันที่สิ้นสุดโดยประมาณ |

Rules:

- unique `(academic_year, semester)`
- ห้าม derive academic year จาก calendar year โดยตรง

### `evaluation_period`

รอบประเมินหรือช่วงเวลาที่รวบรวมงาน

| Column | Required | Purpose |
|---|---:|---|
| `code` | yes | stable code ของรอบประเมิน |
| `label` | yes | label ที่คนอ่านเข้าใจ |
| `start_date` | yes | วันเริ่มรอบ |
| `end_date` | yes | วันจบรอบ |
| `academic_period_id` | no | optional link ไป academic period |

Rules:

- `end_date >= start_date`
- แยกจาก `academic_period`

### `work_category`

หมวดงานหลัก

Seed baseline:

- `TEACHING`
- `RESEARCH`
- `SUPERVISION`
- `ACADEMIC_SERVICE`
- `ADMINISTRATION`
- `OTHER`

### `work_type`

ประเภทงานย่อยภายใต้ `work_category`

ตัวอย่าง:

- `LECTURE`
- `LAB`
- `PUBLICATION`
- `RESEARCH_PROJECT`
- `COMMITTEE`
- `COURSE_COORDINATOR`
- `ACADEMIC_REVIEWER`

Rules:

- `code` unique
- `(category_code, code)` ใช้ enforce ให้ `work_item.category_code` match กับ `work_item.work_type_code`

### `work_item`

แกนกลางของผลงาน/ภาระงานทุกประเภท

| Column | Required | Purpose |
|---|---:|---|
| `category_code` | yes | หมวดงาน |
| `work_type_code` | yes | ประเภทงาน |
| `title` | yes | ชื่อรายการ |
| `description` | no | รายละเอียดทั่วไป |
| `start_date` | no | วันที่เริ่ม |
| `end_date` | no | วันที่สิ้นสุด |
| `visibility` | yes | visibility ของรายการ |
| `status` | yes | `ACTIVE` หรือ `DELETED` |
| `source_score` | no | คะแนนจาก source/form เท่านั้น |
| `source_weight` | no | น้ำหนักจาก source/form เท่านั้น |
| `source_section_code` | no | section code เช่น `2.3.1` |
| `import_batch_id` | no | provenance batch |
| `source_record_id` | no | provenance record |

Rules:

- `source_score` และ `source_weight` ไม่ใช่ scoring engine ที่ระบบรับรองเอง
- soft delete ใช้ `status` และ `deleted_at`
- public API ต้องกรอง `visibility = 'PUBLIC'` และ `status = 'ACTIVE'`

### `faculty_work_item`

ตารางเชื่อมอาจารย์กับ work item

| Column | Required | Purpose |
|---|---:|---|
| `faculty_id` | yes | อาจารย์ที่เกี่ยวข้อง |
| `work_item_id` | yes | work item |
| `academic_period_id` | no | ภาคเรียน/ปีการศึกษา |
| `evaluation_period_id` | no | รอบประเมิน |
| `role` | no | role เช่น author, advisor, committee |
| `contribution_order` | no | ลำดับ contribution |
| `contribution_percent` | no | สัดส่วน 0-100 |
| `quantity` | no | จำนวนเรื่อง/รายการ |
| `credits` | no | หน่วยกิต |
| `hours` | no | ชั่วโมง |
| `source_section_code` | no | section code จาก source |

Rules:

- รองรับ many-to-many
- `contribution_percent` ไม่จำเป็นต้องรวมกันเป็น 100 ถ้า source ไม่ครอบคลุม contributor ทั้งหมด

### Subtype Detail Tables

แต่ละ table ใช้ `work_item_id` เป็น primary key และ foreign key ไปที่ `work_item`

| Table | Purpose |
|---|---|
| `teaching_detail` | รายละเอียดงานสอน เช่น course, credits, hours, student count |
| `publication_detail` | รายละเอียดสิ่งพิมพ์ เช่น DOI, venue, year, quartile |
| `research_project_detail` | รายละเอียดโครงการวิจัยและทุน |
| `supervision_detail` | รายละเอียดการดูแลนักศึกษาแบบไม่จำเป็นต้องเปิด student identity |
| `service_detail` | งานบริการ คณะกรรมการ วิทยากร reviewer editor |
| `administration_detail` | งานบริหารและตำแหน่ง |

### `evidence_reference`

metadata ของหลักฐาน

| Column | Required | Purpose |
|---|---:|---|
| `work_item_id` | yes | work item ที่อ้างถึง |
| `reference_type` | yes | `URL`, `S3_OBJECT`, `DOCUMENT_ID`, `TEXT_NOTE`, `OTHER` |
| `label` | yes | label สำหรับคนอ่าน |
| `external_url` | no | URL ภายนอกถ้ามี |
| `s3_key` | no | private S3 key ถ้ามี |
| `mime_type` | no | mime type |
| `checksum_sha256` | no | checksum |
| `visibility` | yes | visibility ของหลักฐาน |

Rules:

- public API ห้าม expose `s3_key` โดยตรง
- restricted evidence ต้องไม่หลุดไป public projection

### `import_batch`

metadata ของรอบ import

ใช้เก็บ source name, source hash, S3 key, status และ counts เพื่อให้ตรวจสอบย้อนหลังได้

### `source_record`

source row/record ที่ถูกนำเข้า

Rules:

- unique `(source_system, source_record_key, source_hash)` เพื่อ idempotency
- `raw_record` เก็บเป็น `jsonb`
- `target_entity_type` และ `target_entity_id` ช่วย trace ไปยัง entity ที่สร้างขึ้น

### `audit_event`

ประวัติ mutation จาก admin/import/projection

Rules:

- ไม่เปิดผ่าน public API
- ใช้ `before_json` และ `after_json` เพื่อ review การเปลี่ยนแปลงย้อนหลัง

---

## Query Contract Baseline

### Work Item Search

ต้องรองรับ filter ขั้นต้น:

- faculty
- academic period
- evaluation period
- category
- work type
- visibility
- status
- date range
- keyword/title

Required supporting indexes อยู่ใน `database/migrations/001_base.sql`

### Public Repository Query

Baseline predicate:

```sql
WHERE wi.status = 'ACTIVE'
  AND wi.visibility = 'PUBLIC'
```

### Faculty Work Items Query

Baseline join:

```sql
FROM faculty_work_item fwi
JOIN work_item wi ON wi.id = fwi.work_item_id
JOIN faculty f ON f.id = fwi.faculty_id
```

### V1 Compatibility Query

Faculty public page ต้องหา faculty ด้วย:

```sql
WHERE faculty.public_slug = :slug
  AND faculty.status = 'ACTIVE'
```

---

## Acceptance Queries for Review

ตัวอย่าง query ที่ reviewer ใช้ตรวจ schema ได้โดยไม่ deploy application:

```sql
-- public-safe work item list
SELECT wi.id, wi.title, wi.category_code, wi.work_type_code
FROM work_item wi
WHERE wi.status = 'ACTIVE'
  AND wi.visibility = 'PUBLIC'
ORDER BY wi.updated_at DESC;

-- faculty work items by slug
SELECT f.public_slug, wi.id, wi.title, fwi.role
FROM faculty f
JOIN faculty_work_item fwi ON fwi.faculty_id = f.id
JOIN work_item wi ON wi.id = fwi.work_item_id
WHERE f.public_slug = :public_slug
  AND wi.status = 'ACTIVE';

-- source idempotency lookup
SELECT id, target_entity_type, target_entity_id
FROM source_record
WHERE source_system = :source_system
  AND source_record_key = :source_record_key
  AND source_hash = :source_hash;
```

