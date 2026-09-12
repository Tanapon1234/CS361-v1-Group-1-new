# Database Guide

ไฟล์นี้อธิบาย V2 database สำหรับทีมที่ต้อง implement API, migration, admin CRUD หรือ QA

Database จริงตอนนี้อยู่บน Aurora PostgreSQL และเข้าถึงผ่าน RDS Data API ไม่ใช่ต่อ public database endpoint ตรง

## Database Identity

| Item | Value |
|---|---|
| AWS Region | `ap-southeast-1` |
| Foundation stack | `cs361-v2-aws-foundation-dev` |
| Aurora cluster identifier | `cs361-v2-dev-aurora` |
| Database name | `cs361v2` |
| Access method | RDS Data API |
| Secret location | Secrets Manager, secret name `cs361-v2/dev/aurora/master` |

Do not print, paste, screenshot, or commit the secret value.

## Current Data Counts

ล่าสุดเช็คจาก Aurora ผ่าน RDS Data API:

| Table / Entity | Count |
|---|---:|
| `academic_period` | 5 |
| `evaluation_period` | 3 |
| `work_category` | 6 |
| `work_type` | 26 |
| `faculty` | 3 |
| `work_item` | 18 |
| `faculty_work_item` | 20 |
| `evidence_reference` | 8 |

หมายเหตุ:

- จำนวน `work_category` และ `work_type` ใน Aurora มาจาก master seed จริง จึงมากกว่า fixture subset ในบางจุด
- `work_item`, `faculty_work_item`, subtype details และ evidence มี demo data อยู่แล้วสำหรับทำ #66-#68 ต่อ
- ถ้า Aurora auto-pause อยู่ คำสั่งแรกอาจเจอ `DatabaseResumingException`; รอ 15-30 วินาทีแล้วลองใหม่

## How To View Data Through AWS CLI

ตั้งค่า shell variables จาก CloudFormation outputs:

```bash
DB_CLUSTER_ARN=$(aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-aws-foundation-dev \
  --query "Stacks[0].Outputs[?OutputKey=='DBClusterArn'].OutputValue | [0]" \
  --output text)

DB_SECRET_ARN=$(aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-aws-foundation-dev \
  --query "Stacks[0].Outputs[?OutputKey=='DBSecretArn'].OutputValue | [0]" \
  --output text)

DB_NAME=$(aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-aws-foundation-dev \
  --query "Stacks[0].Outputs[?OutputKey=='DBName'].OutputValue | [0]" \
  --output text)
```

Run SQL:

```bash
aws rds-data execute-statement \
  --region ap-southeast-1 \
  --resource-arn "$DB_CLUSTER_ARN" \
  --secret-arn "$DB_SECRET_ARN" \
  --database "$DB_NAME" \
  --sql "select count(*) from work_item"
```

เช็ค table counts:

```bash
aws rds-data execute-statement \
  --region ap-southeast-1 \
  --resource-arn "$DB_CLUSTER_ARN" \
  --secret-arn "$DB_SECRET_ARN" \
  --database "$DB_NAME" \
  --sql "select
    (select count(*) from faculty) as faculties,
    (select count(*) from work_item) as work_items,
    (select count(*) from faculty_work_item) as faculty_work_items,
    (select count(*) from evidence_reference) as evidence_references"
```

ดูตัวอย่าง public work items:

```bash
aws rds-data execute-statement \
  --region ap-southeast-1 \
  --resource-arn "$DB_CLUSTER_ARN" \
  --secret-arn "$DB_SECRET_ARN" \
  --database "$DB_NAME" \
  --sql "select id, title, category_code, work_type_code, visibility, status from work_item order by id limit 10"
```

ดู faculty:

```bash
aws rds-data execute-statement \
  --region ap-southeast-1 \
  --resource-arn "$DB_CLUSTER_ARN" \
  --secret-arn "$DB_SECRET_ARN" \
  --database "$DB_NAME" \
  --sql "select id, public_slug, name_th, name_en, visibility, status from faculty order by public_slug"
```

## Data Model Groups

V2 schema แบ่งเป็นกลุ่มใหญ่:

1. Faculty profile baseline: `faculty`, `faculty_education`, `faculty_interest`
2. Auth/admin pilot: `app_user`, `app_role`, `app_user_role`, `auth_login_event`
3. Time/master data: `academic_period`, `evaluation_period`, `work_category`, `work_type`
4. Import/provenance: `import_batch`, `source_record`
5. Repository core: `work_item`, `faculty_work_item`
6. Subtype detail: `teaching_detail`, `publication_detail`, `research_project_detail`, `supervision_detail`, `service_detail`, `administration_detail`
7. Evidence/audit: `evidence_reference`, `audit_event`

## Common Column Meanings

Common columns appear in many tables:

- `id` (`text`): stable primary key, example `wi-pub-2024-privacy-edge`
- `created_at` (`timestamptz`): record creation time
- `updated_at` (`timestamptz`): last update time
- `deleted_at` (`timestamptz`): soft-delete timestamp when present
- `status` (`text`): lifecycle state, commonly `ACTIVE`, `DELETED`, `SUSPENDED`
- `visibility` (`text`): public boundary, one of `PUBLIC`, `INTERNAL`, `RESTRICTED`
- `display_order` (`integer`): stable ordering for dropdown/UI
- `source_*`: source/provenance fields used to trace imported data

Public APIs must never expose raw source/provenance, secret, audit, or admin-only fields unless a card explicitly says so.

## Table Dictionary

### `faculty`

Stores faculty profile baseline and V1-compatible public slug.

Attributes:

- `id` (`text`): primary key, example `fac_prapaporn-rattanatamrong`
- `public_slug` (`text`): public route slug from V1, example `prapaporn-rattanatamrong`
- `name_th` (`text`): Thai display name, example `ผศ.ดร.ประภาพร รัตนธำรง`
- `name_en` (`text`): English display name
- `academic_position` (`text`): rank/title, example `ผู้ช่วยศาสตราจารย์`
- `department` (`text`): department, example `Computer Science`
- `office_public` (`text`): office shown publicly if allowed
- `phone_public` (`text`): public phone if allowed
- `email_public` (`text`): public email if allowed; #64 intentionally omits it from dropdown API
- `profile_image_url` (`text`): public image URL
- `profile_image_alt` (`text`): image alt text
- `visibility` (`text`): `PUBLIC`, `INTERNAL`, `RESTRICTED`
- `status` (`text`): `ACTIVE`, `DELETED`
- `created_at`, `updated_at`, `deleted_at`: audit/lifecycle timestamps

Used by: #64, #66, #67, #68, V1 compatibility checks.

### `faculty_education`

Stores education history for each faculty.

Attributes:

- `id` (`text`): education row id
- `faculty_id` (`text`): references `faculty.id`
- `degree` (`text`): degree, example `Ph.D.`
- `field_of_study` (`text`): field, example `Computer Science`
- `institution` (`text`): university/institution
- `country` (`text`): country
- `graduation_year` (`integer`): year, example `2015`
- `display_order` (`integer`): order in profile
- `created_at`, `updated_at`: timestamps

Used by: future faculty detail/profile enrichment, V1/V2 mapping.

### `faculty_interest`

Stores research interests, expertise, and keywords.

Attributes:

- `id` (`text`): interest row id
- `faculty_id` (`text`): references `faculty.id`
- `interest_type` (`text`): `RESEARCH_INTEREST`, `EXPERTISE`, `KEYWORD`
- `value` (`text`): interest text, example `privacy`, `data mining`
- `visibility` (`text`): public boundary for this interest
- `created_at`, `updated_at`: timestamps

Used by: search/filter improvements and V1 mapping.

### `app_user`

Stores admin pilot users mapped from Cognito.

Attributes:

- `id` (`text`): app user id, example `user_admin_001`
- `cognito_sub` (`text`): Cognito user subject, unique
- `email` (`text`): admin email
- `display_name` (`text`): admin display name
- `identity_provider` (`text`): `COGNITO` or `SYSTEM`
- `status` (`text`): `ACTIVE`, `SUSPENDED`, `DELETED`
- `last_login_at` (`timestamptz`): last successful login
- `created_at`, `updated_at`, `deleted_at`: timestamps

Used by: #69 auth, #70-#71 audit.

### `app_role`

Stores role definitions.

Attributes:

- `code` (`text`): role code, example `ADMIN`, `SYSTEM`
- `label` (`text`): human-readable label
- `description` (`text`): role description
- `is_active` (`boolean`): role enabled or not
- `created_at`, `updated_at`: timestamps

Seeded values: `ADMIN`, `SYSTEM`.

### `app_user_role`

Maps users to roles.

Attributes:

- `id` (`text`): assignment id
- `user_id` (`text`): references `app_user.id`
- `role_code` (`text`): references `app_role.code`
- `assigned_by_user_id` (`text`): admin who assigned role
- `assigned_at` (`timestamptz`): assignment time
- `revoked_at` (`timestamptz`): revocation time when removed
- `revoke_reason` (`text`): reason for revocation

Used by: checking active `ADMIN` role in #69.

### `auth_login_event`

Stores auth success/failure events.

Attributes:

- `id` (`text`): event id
- `user_id` (`text`): optional reference to `app_user`
- `cognito_sub` (`text`): Cognito subject from token
- `email` (`text`): email from token when available
- `login_status` (`text`): `SUCCESS` or `FAILED`
- `failure_reason` (`text`): reason for failed login/auth
- `ip_address` (`inet`): client IP when captured
- `user_agent` (`text`): request user agent
- `request_id` (`text`): request/correlation id
- `occurred_at` (`timestamptz`): event time

Used by: #69 evidence and security review.

### `academic_period`

Stores academic year/semester periods.

Attributes:

- `id` (`text`): period id, example `ap-2567-2`
- `academic_year` (`integer`): Thai academic year, example `2567`
- `semester` (`text`): `1`, `2`, `3`, `SUMMER`, `OTHER`
- `label` (`text`): display label, example `2/2567`
- `start_date` (`date`): optional start date
- `end_date` (`date`): optional end date
- `created_at`, `updated_at`: timestamps

Used by: #64 filters, #66/#67/#80.

### `evaluation_period`

Stores evaluation windows that can differ from academic periods.

Attributes:

- `id` (`text`): evaluation period id
- `code` (`text`): unique code, example `PPR-2567-2`
- `label` (`text`): display label
- `start_date` (`date`): evaluation start
- `end_date` (`date`): evaluation end
- `academic_period_id` (`text`): optional reference to `academic_period`
- `created_at`, `updated_at`: timestamps

Used by: #64 filters, #66/#67.

### `work_category`

Stores high-level work categories.

Attributes:

- `code` (`text`): category code, example `TEACHING`, `RESEARCH`
- `label_th` (`text`): Thai label, example `งานสอน`
- `label_en` (`text`): English label
- `description` (`text`): category description
- `display_order` (`integer`): dropdown/display order
- `is_active` (`boolean`): whether visible in active lists
- `created_at`, `updated_at`: timestamps

Used by: #64 master data, #66 filtering, #70 validation.

### `work_type`

Stores subtype under each category.

Attributes:

- `code` (`text`): type code, example `PUBLICATION`, `LECTURE`
- `category_code` (`text`): references `work_category.code`
- `label_th` (`text`): Thai label
- `label_en` (`text`): English label
- `description` (`text`): type description
- `default_visibility` (`text`): default `PUBLIC`, `INTERNAL`, or `RESTRICTED`
- `display_order` (`integer`): order within category
- `is_active` (`boolean`): active flag
- `created_at`, `updated_at`: timestamps

Used by: #64 work type endpoint, #66 filters, #70 validation.

### `import_batch`

Stores metadata about a batch import/migration.

Attributes:

- `id` (`text`): batch id
- `source_system` (`text`): source system, example `V1_PUBLIC_FACULTY`
- `source_name` (`text`): source dataset/file name
- `source_version` (`text`): optional source version
- `source_type` (`text`): example `JSON`, `PDF`, `CSV`
- `source_s3_key` (`text`): S3 location of source file if stored
- `source_hash` (`text`): hash for idempotency
- `status` (`text`): `PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`, `WARNING`
- `record_count`, `valid_count`, `warning_count`, `error_count` (`integer`): import counts
- `started_at`, `completed_at` (`timestamptz`): import timing
- `created_by` (`text`): actor/user/system
- `created_at` (`timestamptz`): creation time

Used by: #80 import repeatability and provenance.

### `source_record`

Stores each source row/object and how it maps to target records.

Attributes:

- `id` (`text`): source record id
- `import_batch_id` (`text`): references `import_batch.id`
- `source_system` (`text`): source system
- `source_record_key` (`text`): source object key
- `source_section_code` (`text`): source section, example workload form section `2.3.1`
- `source_hash` (`text`): row/object hash
- `row_number` (`integer`): row number when source is tabular
- `raw_record` (`jsonb`): raw source data for traceability
- `target_entity_type` (`text`): mapped target type, example `work_item`
- `target_entity_id` (`text`): mapped target id
- `status` (`text`): `PENDING`, `IMPORTED`, `SKIPPED`, `WARNING`, `ERROR`
- `error_message` (`text`): import error detail if any
- `created_at` (`timestamptz`): timestamp

Used by: #49/#80 provenance and troubleshooting.

### `work_item`

Central table for one output/workload item.

Attributes:

- `id` (`text`): work item id, example `wi-pub-2024-privacy-edge`
- `category_code` (`text`): references `work_category.code`
- `work_type_code` (`text`): references `work_type.code`
- `title` (`text`): display title
- `description` (`text`): summary/details
- `start_date`, `end_date` (`date`): work period
- `visibility` (`text`): `PUBLIC`, `INTERNAL`, `RESTRICTED`
- `status` (`text`): `ACTIVE`, `DELETED`
- `source_score` (`numeric(12,2)`): score from source form if any
- `source_weight` (`numeric(12,4)`): source weight if any
- `source_section_code` (`text`): workload form source section
- `import_batch_id` (`text`): references `import_batch`
- `source_record_id` (`text`): references `source_record`
- `created_by`, `updated_by` (`text`): actor ids/labels
- `created_at`, `updated_at`, `deleted_at`: timestamps

Used by: #66, #68, #70, #71, #80.

### `faculty_work_item`

Many-to-many join between faculty and work item, including contribution and period.

Attributes:

- `id` (`text`): relation id
- `faculty_id` (`text`): references `faculty.id`
- `work_item_id` (`text`): references `work_item.id`
- `academic_period_id` (`text`): references `academic_period.id`
- `evaluation_period_id` (`text`): references `evaluation_period.id`
- `role` (`text`): role in work item, example `PI`, `Co-author`, `Instructor`
- `contribution_order` (`integer`): order of contributors
- `contribution_percent` (`numeric(5,2)`): contribution percent, example `60.00`
- `contribution_note` (`text`): contribution explanation
- `quantity` (`numeric(12,2)`): quantity from workload source
- `credits` (`numeric(12,2)`): credits if teaching/supervision
- `hours` (`numeric(12,2)`): workload hours
- `source_section_code` (`text`): source form section
- `created_at`, `updated_at`: timestamps

Used by: #66, #67, #68, #70, #71.

### `teaching_detail`

Subtype detail for teaching work items.

Attributes:

- `work_item_id` (`text`): primary key, references `work_item`
- `course_code` (`text`): example `CS333`
- `course_title` (`text`): course title
- `degree_level` (`text`): example `Undergraduate`
- `teaching_mode` (`text`): lecture/lab/seminar mode
- `section_count` (`integer`): number of sections
- `student_count` (`integer`): number of students
- `credits` (`numeric(12,2)`): course credits
- `lecture_hours`, `lab_hours`, `workload_hours` (`numeric(12,2)`): workload hours
- `reference_label` (`text`): source/reference label

Used by: #68 detail API, #70/#71 admin CRUD.

### `publication_detail`

Subtype detail for publication work items.

Attributes:

- `work_item_id` (`text`): primary key, references `work_item`
- `publication_title` (`text`): publication title
- `venue` (`text`): journal/conference
- `publisher` (`text`): publisher
- `publication_year` (`integer`): example `2024`
- `publication_date` (`date`): exact date if known
- `doi` (`text`): DOI
- `isbn`, `issn` (`text`): identifiers
- `quartile` (`text`): `Q1`, `Q2`, `TCI1`, etc.
- `indexing_database` (`text`): example `Scopus`
- `publication_kind` (`text`): journal/proceeding/book chapter etc.
- `external_url` (`text`): public URL

Used by: #68 detail API and publication demos.

### `research_project_detail`

Subtype detail for research project/grant work items.

Attributes:

- `work_item_id` (`text`): primary key, references `work_item`
- `project_title` (`text`): project title
- `funding_source` (`text`): funder
- `funding_type` (`text`): internal/external/grant type
- `budget_amount` (`numeric(14,2)`): budget
- `currency` (`text`): default `THB`
- `project_status` (`text`): ongoing/completed etc.
- `contract_number` (`text`): contract/reference number
- `principal_investigator` (`text`): PI name
- `project_start_date`, `project_end_date` (`date`): project period

Used by: #68 detail API and research filters.

### `supervision_detail`

Subtype detail for supervision/advising work items.

Attributes:

- `work_item_id` (`text`): primary key, references `work_item`
- `supervision_type` (`text`): thesis/senior project/general advisor
- `supervision_role` (`text`): advisor/co-advisor/committee
- `degree_level` (`text`): Bachelor/Master/PhD
- `program_name` (`text`): program
- `course_code` (`text`): course if related
- `student_count` (`integer`): count only, not student names
- `credits` (`numeric(12,2)`): credits if applicable
- `student_identifier_policy` (`text`): `REDACTED`, `INTERNAL_ONLY`, `NOT_STORED`

Used by: #68 detail API and privacy-safe supervision examples.

### `service_detail`

Subtype detail for academic service work items.

Attributes:

- `work_item_id` (`text`): primary key, references `work_item`
- `service_scope` (`text`): internal/external/community/academic service scope
- `organization_name` (`text`): organization served
- `service_role` (`text`): reviewer/speaker/committee/etc.
- `committee_name` (`text`): committee name if any
- `order_reference` (`text`): appointment/order reference
- `service_date`, `service_end_date` (`date`): service period

Used by: #68 detail API and service records.

### `administration_detail`

Subtype detail for administrative roles/work items.

Attributes:

- `work_item_id` (`text`): primary key, references `work_item`
- `position_title` (`text`): position, example course coordinator
- `organization_unit` (`text`): department/program/unit
- `appointment_type` (`text`): appointment type
- `appointed_from`, `appointed_to` (`date`): appointment period
- `appointment_reference` (`text`): reference/order

Used by: #68 detail API and admin work records.

### `evidence_reference`

Stores metadata/reference to evidence. It does not expose private files directly.

Attributes:

- `id` (`text`): evidence id
- `work_item_id` (`text`): references `work_item.id`
- `reference_type` (`text`): `URL`, `S3_OBJECT`, `DOCUMENT_ID`, `TEXT_NOTE`, `OTHER`
- `label` (`text`): display label
- `external_url` (`text`): public/external URL if any
- `s3_key` (`text`): private S3 key if any; never expose private key blindly
- `mime_type` (`text`): file MIME type
- `checksum_sha256` (`text`): checksum if available
- `visibility` (`text`): evidence visibility
- `created_at` (`timestamptz`): timestamp

Used by: #68 detail API and future evidence workflows.

### `audit_event`

Stores audit trail for admin/system mutations.

Attributes:

- `id` (`text`): event id
- `actor_user_id` (`text`): references `app_user.id` when human admin
- `actor_subject` (`text`): Cognito subject or system actor
- `action` (`text`): action, example `CREATE_WORK_ITEM`
- `entity_type` (`text`): target type, example `work_item`
- `entity_id` (`text`): target id
- `before_json` (`jsonb`): state before change
- `after_json` (`jsonb`): state after change
- `request_id` (`text`): API request id
- `occurred_at` (`timestamptz`): timestamp

Used by: #70/#71 admin CRUD and #81 final audit evidence.

## Relationship Map

Important relationships:

- `faculty` 1-to-many `faculty_education`
- `faculty` 1-to-many `faculty_interest`
- `faculty` many-to-many `work_item` through `faculty_work_item`
- `work_category` 1-to-many `work_type`
- `work_item` references `work_type` through `(category_code, work_type_code)`
- `work_item` 1-to-0/1 each subtype detail table
- `work_item` 1-to-many `evidence_reference`
- `import_batch` 1-to-many `source_record`
- `source_record` optionally points to target imported entity
- `app_user` many-to-many `app_role` through `app_user_role`
- `app_user` 1-to-many `auth_login_event` and `audit_event`

## What Public APIs May Return

Public-safe fields:

- faculty id, slug, public names, position, department, profile image fields
- work item title, category/type labels, period labels
- public work item detail fields
- public evidence metadata only when visibility allows it

Public APIs must not return:

- `source_record.raw_record`
- database secret, ARN, S3 private object path
- `audit_event`
- `auth_login_event`
- private admin notes
- `INTERNAL` or `RESTRICTED` rows unless an admin route explicitly allows it

## Which Cards Use Which Tables

| Card | Main Tables |
|---|---|
| #64 Master Data API | `academic_period`, `evaluation_period`, `work_category`, `work_type`, `faculty` |
| #66 Work Item List/Search | `work_item`, `work_type`, `work_category`, `faculty_work_item`, `faculty`, periods |
| #67 Faculty Work Items | `faculty`, `faculty_work_item`, `work_item`, periods |
| #68 Detail API | `work_item`, `faculty_work_item`, subtype details, `evidence_reference` |
| #69 Admin Auth | `app_user`, `app_role`, `app_user_role`, `auth_login_event` |
| #70 Admin Create | `work_item`, `faculty_work_item`, subtype details, `evidence_reference`, `audit_event` |
| #71 Admin Update/Delete | same as #70 plus soft-delete fields |
| #80 Migration/Compatibility | all core data tables plus `import_batch`, `source_record` |

## Database Safety Checklist

Before changing schema:

- Read `database/migrations/001_base.sql`
- Check which issue card owns the change
- Add migration deliberately; do not edit historical SQL silently after teammates depend on it
- Update `docs/v2/erd-table-attribute-guide.md` and this guide if table meaning changes
- Verify RDS Data API query works
- Record evidence without secret values

Before writing admin mutation code:

- Use transactions through RDS Data API
- Validate category/type/faculty/period IDs
- Insert `audit_event`
- Respect `visibility` and `status`
- Add rollback/error tests
