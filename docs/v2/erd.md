# V2 Repository ERD

เอกสารนี้เป็น ERD baseline สำหรับ Issue #47 - Design Relational Schema & SQL Migration

เป้าหมายของ ERD นี้คือทำให้ทีมเห็นความสัมพันธ์หลักของ V2 repository ก่อนเริ่มทำ API, import, migration และ UI โดยไม่ copy โครงสร้างแบบฟอร์มภาระงาน 1:1 เข้ามาเป็น schema

---

## ERD Overview

```mermaid
erDiagram
  faculty ||--o{ faculty_education : has
  faculty ||--o{ faculty_interest : has
  faculty ||--o{ faculty_work_item : contributes

  academic_period ||--o{ evaluation_period : may_group
  academic_period ||--o{ faculty_work_item : classifies
  evaluation_period ||--o{ faculty_work_item : evaluates

  work_category ||--o{ work_type : contains
  work_category ||--o{ work_item : classifies
  work_type ||--o{ work_item : specifies

  work_item ||--o{ faculty_work_item : has_contributors
  work_item ||--o{ evidence_reference : has_evidence
  work_item ||--|| teaching_detail : optional_detail
  work_item ||--|| publication_detail : optional_detail
  work_item ||--|| research_project_detail : optional_detail
  work_item ||--|| supervision_detail : optional_detail
  work_item ||--|| service_detail : optional_detail
  work_item ||--|| administration_detail : optional_detail

  import_batch ||--o{ source_record : contains
  import_batch ||--o{ work_item : imported
  source_record ||--o{ work_item : produced

  faculty {
    text id PK
    text public_slug UK
    text name_th
    text name_en
    text academic_position
    text visibility
    text status
    timestamptz created_at
    timestamptz updated_at
    timestamptz deleted_at
  }

  faculty_education {
    text id PK
    text faculty_id FK
    text degree
    text field_of_study
    text institution
    text country
    integer graduation_year
    integer display_order
  }

  faculty_interest {
    text id PK
    text faculty_id FK
    text interest_type
    text value
    text visibility
  }

  academic_period {
    text id PK
    integer academic_year
    text semester
    text label
    date start_date
    date end_date
  }

  evaluation_period {
    text id PK
    text code UK
    text label
    date start_date
    date end_date
    text academic_period_id FK
  }

  work_category {
    text code PK
    text label_th
    text label_en
    integer display_order
    boolean is_active
  }

  work_type {
    text code PK
    text category_code FK
    text label_th
    text label_en
    text default_visibility
    integer display_order
    boolean is_active
  }

  work_item {
    text id PK
    text category_code FK
    text work_type_code FK
    text title
    text description
    date start_date
    date end_date
    text visibility
    text status
    numeric source_score
    numeric source_weight
    text source_section_code
    text import_batch_id FK
    text source_record_id FK
    timestamptz created_at
    timestamptz updated_at
    timestamptz deleted_at
  }

  faculty_work_item {
    text id PK
    text faculty_id FK
    text work_item_id FK
    text academic_period_id FK
    text evaluation_period_id FK
    text role
    integer contribution_order
    numeric contribution_percent
    numeric quantity
    numeric credits
    numeric hours
    text source_section_code
  }

  teaching_detail {
    text work_item_id PK,FK
    text course_code
    text course_title
    text degree_level
    text teaching_mode
    numeric credits
    numeric lecture_hours
    numeric lab_hours
    integer student_count
  }

  publication_detail {
    text work_item_id PK,FK
    text publication_title
    text venue
    integer publication_year
    text doi
    text quartile
    text indexing_database
    text external_url
  }

  research_project_detail {
    text work_item_id PK,FK
    text project_title
    text funding_source
    text funding_type
    numeric budget_amount
    text project_status
  }

  supervision_detail {
    text work_item_id PK,FK
    text supervision_type
    text supervision_role
    text degree_level
    text program_name
    integer student_count
  }

  service_detail {
    text work_item_id PK,FK
    text service_scope
    text organization_name
    text service_role
    text committee_name
  }

  administration_detail {
    text work_item_id PK,FK
    text position_title
    text organization_unit
    text appointment_type
    date appointed_from
    date appointed_to
  }

  evidence_reference {
    text id PK
    text work_item_id FK
    text reference_type
    text label
    text external_url
    text s3_key
    text checksum_sha256
    text visibility
  }

  import_batch {
    text id PK
    text source_system
    text source_name
    text source_hash
    text status
    integer record_count
    integer valid_count
    integer warning_count
    integer error_count
  }

  source_record {
    text id PK
    text import_batch_id FK
    text source_system
    text source_record_key
    text source_hash
    jsonb raw_record
    text target_entity_type
    text target_entity_id
    text status
  }

  audit_event {
    text id PK
    text actor_subject
    text action
    text entity_type
    text entity_id
    jsonb before_json
    jsonb after_json
    timestamptz occurred_at
  }
```

---

## Key Relationship Rules

- `work_item` เป็นแกนกลางของผลงานและภาระงานทุกประเภท
- subtype detail tables ใช้ `work_item_id` เป็นทั้ง primary key และ foreign key
- `faculty_work_item` รองรับ many-to-many ระหว่าง faculty กับ work item
- `academic_period` และ `evaluation_period` แยกกันเพื่อรองรับกรณีปีการศึกษาไม่ตรงกับปีปฏิทิน
- `work_category` และ `work_type` เป็น master data สำหรับ filter, API response และ UI dropdown
- `source_record` และ `import_batch` ทำให้ import ตรวจสอบย้อนกลับและทำ idempotency ได้
- `audit_event` เก็บ mutation history สำหรับ admin/import ไม่เปิดผ่าน public API

---

## Visibility Boundary

ตารางที่มี `visibility` โดยตรง:

- `faculty`
- `faculty_interest`
- `work_item`
- `work_type` ผ่าน `default_visibility`
- `evidence_reference`

Public API ต้องกรองข้อมูลที่ `visibility = 'PUBLIC'` และต้องไม่ expose `s3_key`, restricted evidence หรือ audit/import raw data โดยตรง

