# [V2] Build Work Item Detail API #68

## สรุป

สร้าง `GET /api/v2/work-items/{id}` สำหรับเรียกดูรายละเอียด work item รายการเดียว โดยอ่านจาก Aurora จริงผ่าน `API Gateway -> Lambda -> RDS Data API -> Aurora` และ return ข้อมูล public-safe สำหรับหน้า detail ของ V2 repository

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #54 แต่ GitHub issue จริงใช้ #68

## Production AWS Requirement

การ์ดนี้ต้อง deploy เป็น production read API จริง:

```text
Amazon API Gateway
→ AWS Lambda query handler
→ Amazon RDS Data API
→ Aurora PostgreSQL Serverless v2
```

fixture/mock ใช้ได้เฉพาะ unit test หรือ local contract test เท่านั้น ไม่ถือว่าเพียงพอสำหรับปิดการ์ดนี้

## Background

#66 แสดง list/search/filter แบบสรุป และ #67 แสดง list เฉพาะอาจารย์หนึ่งคน แต่ V2 ยังต้องมีหน้า detail เพื่อให้ผู้ใช้กดจาก list แล้วเห็นข้อมูลของผลงาน/ภาระงานรายการเดียวอย่างครบถ้วน เช่น publication metadata, รายชื่ออาจารย์ที่เกี่ยวข้อง, ปีการศึกษา, evidence metadata และรายละเอียดตามประเภทงาน

เพราะรายละเอียดแต่ละชนิดงานไม่เหมือนกัน schema จึงแยก subtype detail tables:

- `teaching_detail`
- `publication_detail`
- `research_project_detail`
- `supervision_detail`
- `service_detail`
- `administration_detail`

การ์ดนี้คือ backend contract สำหรับหน้า `/outputs/{id}` หรือ work item detail drawer/card ที่ frontend จะทำต่อใน #74/#75

## Database Alignment Check

เช็กกับไฟล์ `database/migrations/001_base.sql`, `database/seeds/001_master_data.sql`, `data/v2/fixtures/` และ Aurora dev แล้ว การ์ดนี้ต้องใช้ table/attribute ที่มีอยู่จริงดังนี้:

- `work_item`: `id`, `category_code`, `work_type_code`, `title`, `description`, `start_date`, `end_date`, `visibility`, `status`, `created_at`, `updated_at`
- `work_category`: `code`, `label_th`, `label_en`, `description`, `display_order`, `is_active`
- `work_type`: `code`, `category_code`, `label_th`, `label_en`, `description`, `default_visibility`, `display_order`, `is_active`
- `faculty_work_item`: `id`, `faculty_id`, `work_item_id`, `academic_period_id`, `evaluation_period_id`, `role`, `contribution_order`, `contribution_percent`, `contribution_note`, `quantity`, `credits`, `hours`, `source_section_code`
- `faculty`: `id`, `public_slug`, `name_th`, `name_en`, `academic_position`, `department`, `profile_image_url`, `profile_image_alt`, `visibility`, `status`
- `academic_period`: `id`, `academic_year`, `semester`, `label`, `start_date`, `end_date`
- `evaluation_period`: `id`, `code`, `label`, `start_date`, `end_date`, `academic_period_id`
- `publication_detail`: `work_item_id`, `publication_title`, `venue`, `publisher`, `publication_year`, `publication_date`, `doi`, `isbn`, `issn`, `quartile`, `indexing_database`, `publication_kind`, `external_url`
- `teaching_detail`: `work_item_id`, `course_code`, `course_title`, `degree_level`, `teaching_mode`, `section_count`, `student_count`, `credits`, `lecture_hours`, `lab_hours`, `workload_hours`, `reference_label`
- `research_project_detail`: `work_item_id`, `project_title`, `funding_source`, `funding_type`, `budget_amount`, `currency`, `project_status`, `contract_number`, `principal_investigator`, `project_start_date`, `project_end_date`
- `supervision_detail`: `work_item_id`, `supervision_type`, `supervision_role`, `degree_level`, `program_name`, `course_code`, `student_count`, `credits`, `student_identifier_policy`
- `service_detail`: `work_item_id`, `service_scope`, `organization_name`, `service_role`, `committee_name`, `order_reference`, `service_date`, `service_end_date`
- `administration_detail`: `work_item_id`, `position_title`, `organization_unit`, `appointment_type`, `appointed_from`, `appointed_to`, `appointment_reference`
- `evidence_reference`: `id`, `work_item_id`, `reference_type`, `label`, `external_url`, `s3_key`, `mime_type`, `checksum_sha256`, `visibility`, `created_at`

Aurora dev live check วันที่ 2026-09-13 มี detail/evidence rows ดังนี้:

| Table | Row count |
|---|---:|
| `teaching_detail` | 4 |
| `publication_detail` | 3 |
| `research_project_detail` | 3 |
| `supervision_detail` | 3 |
| `service_detail` | 3 |
| `administration_detail` | 2 |
| `evidence_reference` | 8 |

ตัวอย่าง id/code ที่ต้องใช้ให้ตรงกับฐานข้อมูลจริง:

- public work item id: `wi-pub-2024-privacy-edge`
- category/type: `RESEARCH` / `PUBLICATION`
- faculty ids: `fac_prapaporn-rattanatamrong`, `fac_kasidit-chanchio`
- faculty slugs: `prapaporn-rattanatamrong`, `kasidit-chanchio`
- academic period id/label: `ap-2567-1` / `1/2567`
- evaluation period id/code: `eval-2567-full-year` / `EVAL-2567`
- public evidence id: `ev-pub-2024-demo-url`

ข้อควรระวัง:

- ห้ามใช้ id เก่าแบบ `fac_prapaporn` หรือ `ap_2567_2` เพราะไม่ตรงกับ schema/demo data ปัจจุบัน
- `work_item.source_score`, `source_weight`, `source_section_code`, `import_batch_id`, `source_record_id` เป็น provenance/internal fields ไม่ควรออก public response
- `evidence_reference.s3_key` และ `checksum_sha256` ไม่ควรออก public response แม้ evidence row เป็น `PUBLIC` เพราะอาจเป็น private storage path หรือ integrity metadata
- `INTERNAL` / `RESTRICTED` work items ต้องตอบ public-safe `404` ใน public route

## เป้าหมาย

สร้าง Detail API ที่:

- ดึง core work item จาก `work_item`
- แนบ category/type label จาก master tables
- แนบ faculty contributors จาก `faculty_work_item` + `faculty`
- แนบ academic/evaluation periods จาก relation ใน `faculty_work_item`
- แนบ subtype detail ตามชนิดงานจริง
- แนบ evidence metadata เฉพาะที่ public-safe
- enforce visibility ที่ backend
- ใช้ response shape stable ต่อ frontend detail page

## User Stories

1. As a public visitor, I want to open one public work item detail, so that I can understand the output beyond the summary list.
2. As a public visitor, I want to see the category/type labels in Thai, so that I can understand what kind of work it is.
3. As a public visitor, I want to see all public-safe faculty contributors and their roles, so that I understand who participated in the work.
4. As a public visitor, I want to see publication metadata when the item is a publication, so that I can verify venue, DOI, year, and external link.
5. As a public visitor, I want to see only public evidence references, so that private documents or storage keys are not exposed.
6. As a frontend developer, I want a stable detail response shape with `detail.kind`, so that the UI can render different work types without guessing the subtype table.
7. As a QA reviewer, I want predictable 404 behavior for missing/internal/restricted items, so that public access rules are easy to test.
8. As a backend developer, I want SQL/Data API baselines, so that I can compare implementation output with Aurora rows directly.

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- เปิด evidence file download
- ทำ signed URL สำหรับ S3 object
- ทำ admin detail response ที่เห็น restricted/internal fields
- ทำ create/edit/delete
- ทำ frontend route `/outputs/{id}`
- ทำ official workload report rendering
- ทำ score calculation หรือ workload summary

## Scope

### ต้องทำ

- implement `GET /api/v2/work-items/{id}`
- route ต้องรับ `id` เป็น `work_item.id`
- read จาก Aurora ผ่าน RDS Data API จริง
- join core row จาก `work_item`, `work_category`, `work_type`
- join contributors จาก `faculty_work_item`, `faculty`, `academic_period`, `evaluation_period`
- query subtype detail table ตาม `category_code` / `work_type_code`
- query public-safe evidence metadata จาก `evidence_reference`
- return `detail.kind` ตาม subtype ที่พบ
- enforce public route ด้วย `work_item.status = ACTIVE` และ `work_item.visibility = PUBLIC`
- omit/redact fields ที่ไม่ public-safe
- เพิ่ม Lambda route/handler สำหรับ `GET /api/v2/work-items/{id}`
- configure API Gateway route/stage สำหรับ endpoint นี้
- เพิ่ม CloudWatch logs สำหรับ request id, work item id, visibility decision, subtype decision และ errors
- เพิ่ม tests สำหรับ public detail, missing id, internal/restricted id, evidence visibility, contributors ordering และ subtype mapping
- เพิ่ม AWS smoke test ผ่าน deployed endpoint จริง

### ไม่ต้องทำ

- subtype mutation
- admin-only visibility expansion
- evidence upload/download
- frontend rendering
- search/list pagination

## API Contract

```http
GET /api/v2/work-items/{id}
```

ตัวอย่าง:

```text
/api/v2/work-items/wi-pub-2024-privacy-edge
```

ตัวอย่าง response จาก public data จริงของ `wi-pub-2024-privacy-edge`:

```json
{
  "id": "wi-pub-2024-privacy-edge",
  "title": "Privacy-Preserving Edge Analytics for Smart Campus Workload Signals",
  "description": "Synthetic publication used for keyword search demo. Keyword: privacy.",
  "category": {
    "code": "RESEARCH",
    "label_th": "งานวิชาการ/วิจัย",
    "label_en": "Research and Academic Output"
  },
  "type": {
    "code": "PUBLICATION",
    "label_th": "ผลงานตีพิมพ์",
    "label_en": "Publication"
  },
  "visibility": "PUBLIC",
  "start_date": "2024-10-01",
  "end_date": "2024-10-01",
  "academic_periods": [
    {
      "id": "ap-2567-1",
      "label": "1/2567",
      "academic_year": 2567,
      "semester": "1"
    }
  ],
  "evaluation_periods": [
    {
      "id": "eval-2567-full-year",
      "code": "EVAL-2567",
      "label": "Evaluation 2567"
    }
  ],
  "faculty": [
    {
      "id": "fac_prapaporn-rattanatamrong",
      "display_name": "ผศ.ดร.ประภาพร รัตนธำรง",
      "slug": "prapaporn-rattanatamrong",
      "role": "CORRESPONDING_AUTHOR",
      "contribution_order": 1,
      "contribution_percent": 60,
      "academic_period": {
        "id": "ap-2567-1",
        "label": "1/2567"
      },
      "evaluation_period": {
        "id": "eval-2567-full-year",
        "code": "EVAL-2567",
        "label": "Evaluation 2567"
      }
    },
    {
      "id": "fac_kasidit-chanchio",
      "display_name": "ผศ.ดร.กษิดิศ ชาญเชี่ยว",
      "slug": "kasidit-chanchio",
      "role": "AUTHOR",
      "contribution_order": 2,
      "contribution_percent": 40,
      "academic_period": {
        "id": "ap-2567-1",
        "label": "1/2567"
      },
      "evaluation_period": {
        "id": "eval-2567-full-year",
        "code": "EVAL-2567",
        "label": "Evaluation 2567"
      }
    }
  ],
  "detail": {
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
  },
  "evidence": [
    {
      "id": "ev-pub-2024-demo-url",
      "label": "Synthetic publication landing page",
      "reference_type": "URL",
      "external_url": "https://example.edu/cs361-demo/privacy-edge-analytics",
      "mime_type": "text/html",
      "visibility": "PUBLIC"
    }
  ],
  "updated_at": "2026-09-12T17:15:44.616344Z"
}
```

หมายเหตุเรื่อง period:

- `academic_periods` และ `evaluation_periods` เป็น aggregate จาก `faculty_work_item` ของ work item นี้
- `faculty[].academic_period` และ `faculty[].evaluation_period` คือ period ของ relation ของ contributor คนนั้น
- ถ้าอนาคต work item เดียวมี contributors ที่อยู่คนละ period ให้ frontend แสดง aggregate chips จาก top-level arrays และแสดง relation-level period ใน contributor row ได้

## Expected UI Usage

API นี้ถูกออกแบบมาให้ frontend ใช้ทำหน้า “รายละเอียดผลงาน” หลังจากผู้ใช้กด `ดูรายละเอียด` จาก #66 หรือ #67

ภาพที่คาดหวังใน UI:

- header ชื่อผลงาน
- badges หมวดงาน ประเภทงาน ปีการศึกษา รอบประเมิน และ visibility
- summary/description
- section “ผู้เกี่ยวข้อง” แสดงอาจารย์ บทบาท ลำดับ และ contribution percent
- section “รายละเอียด” เปลี่ยน field ตาม `detail.kind`
- section “หลักฐาน/อ้างอิง” แสดงเฉพาะ public evidence metadata หรือ public external URL
- ถ้า item ไม่ public ให้ไม่แสดง detail และปล่อยให้ API return `404`

ต่างจาก #66/#67:

- #66 คือ list ทั้ง repository
- #67 คือ list เฉพาะ faculty
- #68 คือ detail ของ work item เดียว และต้องรวม subtype detail + evidence metadata

## Expected UI Fields

| UI field | ใช้แสดงในหน้าเว็บ | จำเป็นไหม | หมายเหตุ |
|---|---|---|---|
| `id` | key และ route `/outputs/{id}` | จำเป็น | มาจาก `work_item.id` |
| `title` | heading หลักของ detail page | จำเป็น | มาจาก `work_item.title` |
| `description` | summary ใต้ heading | ควรมี | UI แสดงเป็น paragraph |
| `category.code` | badge/filter code | จำเป็น | เช่น `RESEARCH` |
| `category.label_th` | label หมวดงานไทย | ควรมี | เช่น `งานวิชาการ/วิจัย` |
| `type.code` | badge/filter code | จำเป็น | เช่น `PUBLICATION` |
| `type.label_th` | label ประเภทงานไทย | ควรมี | เช่น `ผลงานตีพิมพ์` |
| `visibility` | badge visibility | จำเป็น | public route ต้องได้ `PUBLIC` เท่านั้น |
| `start_date`, `end_date` | วันที่/ช่วงเวลาของงาน | optional | ใช้แสดง timeline |
| `academic_periods[]` | chips ปีการศึกษา | ควรมี | aggregate จาก `faculty_work_item` |
| `evaluation_periods[]` | chips รอบประเมิน | ควรมี | aggregate จาก `faculty_work_item` |
| `faculty[].id` | key ของ contributor | จำเป็น | ใช้ link ไปหน้า faculty |
| `faculty[].display_name` | ชื่ออาจารย์ | จำเป็น | ใช้ `name_th` fallback `name_en` |
| `faculty[].slug` | public profile route | จำเป็น | ใช้ link `/faculties/{slug}` |
| `faculty[].role` | บทบาทในงาน | จำเป็น | เช่น `AUTHOR`, `CORRESPONDING_AUTHOR` |
| `faculty[].contribution_order` | ลำดับผู้มีส่วนร่วม | ควรมี | ใช้ sort contributors |
| `faculty[].contribution_percent` | สัดส่วนผลงาน | ควรมี | แสดงเมื่อ public-safe |
| `detail.kind` | subtype renderer key | จำเป็น | เช่น `publication`, `service` |
| `detail.*` | รายละเอียดตาม subtype | ควรมี | field เปลี่ยนตามชนิดงาน |
| `evidence[].id` | evidence key | ควรมี | metadata เท่านั้น |
| `evidence[].label` | ชื่อหลักฐาน/อ้างอิง | ควรมี | แสดงเป็น link/row |
| `evidence[].reference_type` | ประเภทหลักฐาน | ควรมี | เช่น `URL`, `TEXT_NOTE` |
| `evidence[].external_url` | public URL | optional | แสดง link ถ้าเป็น public URL |
| `evidence[].mime_type` | ชนิดไฟล์/URL | optional | แสดง icon/metadata ได้ |
| `updated_at` | อัปเดตล่าสุด | ควรมี | ใช้ display/debug |

## Data Source / Table Mapping

| Response field | Source table | Source attribute | วิธี join / หมายเหตุ |
|---|---|---|---|
| `id` | `work_item` | `id` | path parameter |
| `title` | `work_item` | `title` | core row |
| `description` | `work_item` | `description` | core row |
| `category.code` | `work_item` | `category_code` | FK ไป `work_category.code` |
| `category.label_th` | `work_category` | `label_th` | join `work_category.code = work_item.category_code` |
| `category.label_en` | `work_category` | `label_en` | join `work_category.code = work_item.category_code` |
| `type.code` | `work_item` | `work_type_code` | FK ไป `work_type.code` |
| `type.label_th` | `work_type` | `label_th` | join ด้วย `(category_code, code)` |
| `type.label_en` | `work_type` | `label_en` | join ด้วย `(category_code, code)` |
| `visibility` | `work_item` | `visibility` | public route ต้องเป็น `PUBLIC` |
| `start_date` | `work_item` | `start_date` | optional |
| `end_date` | `work_item` | `end_date` | optional |
| `updated_at` | `work_item` | `updated_at` | convert เป็น ISO string |
| `academic_periods[]` | `faculty_work_item` + `academic_period` | `academic_period_id`, labels | distinct aggregate ต่อ work item |
| `evaluation_periods[]` | `faculty_work_item` + `evaluation_period` | `evaluation_period_id`, labels | distinct aggregate ต่อ work item |
| `faculty[].id` | `faculty` | `id` | join ผ่าน `faculty_work_item.faculty_id` |
| `faculty[].display_name` | `faculty` | `name_th`, fallback `name_en` | `COALESCE(name_th, name_en)` |
| `faculty[].slug` | `faculty` | `public_slug` | public route |
| `faculty[].role` | `faculty_work_item` | `role` | relation-level role |
| `faculty[].contribution_order` | `faculty_work_item` | `contribution_order` | sort contributors |
| `faculty[].contribution_percent` | `faculty_work_item` | `contribution_percent` | relation-level percent |
| `faculty[].academic_period` | `faculty_work_item` + `academic_period` | `academic_period_id`, labels | relation-level period |
| `faculty[].evaluation_period` | `faculty_work_item` + `evaluation_period` | `evaluation_period_id`, labels | relation-level evaluation |
| `detail.kind` | mapper decision | derived | จาก `work_type_code` / subtype table |
| `detail.*` | subtype table | subtype columns | ดู Detail Kind Mapping |
| `evidence[]` | `evidence_reference` | public-safe columns | เฉพาะ `visibility = PUBLIC` |

## Detail Kind Mapping

| Category / Work types | Detail table | `detail.kind` | Public fields ที่ส่งออก |
|---|---|---|---|
| `TEACHING`: `LECTURE`, `LAB`, `SEMINAR` | `teaching_detail` | `teaching` | `course_code`, `course_title`, `degree_level`, `teaching_mode`, `section_count`, `student_count`, `credits`, `lecture_hours`, `lab_hours`, `workload_hours`, `reference_label` |
| `RESEARCH`: `PUBLICATION` | `publication_detail` | `publication` | `publication_title`, `venue`, `publisher`, `publication_year`, `publication_date`, `doi`, `isbn`, `issn`, `quartile`, `indexing_database`, `publication_kind`, `external_url` |
| `RESEARCH`: `RESEARCH_PROJECT`, `RESEARCH_GRANT` | `research_project_detail` | `research_project` | `project_title`, `funding_source`, `funding_type`, `budget_amount`, `currency`, `project_status`, `contract_number`, `principal_investigator`, `project_start_date`, `project_end_date` |
| `SUPERVISION`: `SENIOR_PROJECT`, `COOPERATIVE_EDUCATION`, `THESIS`, `GENERAL_ADVISOR` | `supervision_detail` | `supervision` | `supervision_type`, `supervision_role`, `degree_level`, `program_name`, `course_code`, `student_count`, `credits`, `student_identifier_policy` |
| `ACADEMIC_SERVICE`: `COMMITTEE`, `ACADEMIC_REVIEWER`, `EDITOR`, `INVITED_SPEAKER`, `EXTERNAL_SERVICE` | `service_detail` | `service` | `service_scope`, `organization_name`, `service_role`, `committee_name`, `order_reference`, `service_date`, `service_end_date` |
| `ADMINISTRATION`: `COURSE_COORDINATOR`, `ADMIN_POSITION`, `PROGRAM_ADMINISTRATION`, `INTERNSHIP_COORDINATOR` | `administration_detail` | `administration` | `position_title`, `organization_unit`, `appointment_type`, `appointed_from`, `appointed_to`, `appointment_reference` |

ถ้า work type ในอนาคตอยู่ใน master data แต่ยังไม่มี subtype table ที่รองรับ ให้ return `detail.kind = "unknown"` หรือ `detail = null` พร้อม log warning ตาม convention ที่ทีมเลือก แต่ห้าม crash

## Evidence Mapping

Public response ของ #68 แสดง evidence เป็น metadata/reference เท่านั้น:

| Response field | Source table | Source attribute | กติกา |
|---|---|---|---|
| `evidence[].id` | `evidence_reference` | `id` | public-safe key |
| `evidence[].label` | `evidence_reference` | `label` | ชื่อหลักฐาน |
| `evidence[].reference_type` | `evidence_reference` | `reference_type` | `URL`, `S3_OBJECT`, `DOCUMENT_ID`, `TEXT_NOTE`, `OTHER` |
| `evidence[].external_url` | `evidence_reference` | `external_url` | ส่งได้เฉพาะ row ที่ `visibility = PUBLIC` และเป็น URL ที่ตั้งใจเปิด public |
| `evidence[].mime_type` | `evidence_reference` | `mime_type` | metadata |
| `evidence[].visibility` | `evidence_reference` | `visibility` | public route ต้องเป็น `PUBLIC` เท่านั้น |

ห้ามส่งออก:

- `evidence_reference.s3_key`
- `evidence_reference.checksum_sha256`
- private/internal document id ที่นำไปเข้าถึงไฟล์ได้โดยตรง
- signed URL เพราะไม่อยู่ใน scope การ์ดนี้

## Public-Safe Fields

ต้องส่งออกใน public response:

- `work_item.id`, `title`, `description`, `start_date`, `end_date`, `visibility`, `updated_at`
- `work_category.code`, `label_th`, `label_en`
- `work_type.code`, `label_th`, `label_en`
- public faculty summary: `id`, `public_slug`, `name_th`, `name_en`, `academic_position`, `department`, `profile_image_url`, `profile_image_alt`
- relation-level public-safe fields: `role`, `contribution_order`, `contribution_percent`, `academic_period_id`, `evaluation_period_id`
- public subtype fields ตาม Detail Kind Mapping
- public evidence metadata ตาม Evidence Mapping

ห้ามส่งออกใน public response ของ #68:

- `work_item.status`
- `work_item.source_score`
- `work_item.source_weight`
- `work_item.source_section_code`
- `work_item.import_batch_id`
- `work_item.source_record_id`
- `faculty_work_item.contribution_note`
- `faculty_work_item.quantity`
- `faculty_work_item.credits`
- `faculty_work_item.hours`
- `faculty_work_item.source_section_code`
- `source_record.raw_record`
- `audit_event`
- `app_user` / `app_role` / auth data
- `evidence_reference.s3_key`
- `evidence_reference.checksum_sha256`
- Secrets Manager ARN/value หรือ private AWS resource detail

## Visibility Rules

- public route return ได้เฉพาะ `work_item.status = ACTIVE` และ `work_item.visibility = PUBLIC`
- `INTERNAL` หรือ `RESTRICTED` work item ต้อง return `404` ไม่ใช่ `403` เพื่อไม่เปิดเผยว่ามี record อยู่
- evidence ที่ไม่ `PUBLIC` ต้องถูก omit
- faculty ที่ไม่ `PUBLIC` หรือไม่ `ACTIVE` ถ้าอนาคตมี ต้องไม่ถูกเปิดใน public response
- source/provenance/audit/auth fields ห้ามออก public response

## Expected Demo Result Baseline

ถ้าใช้ Aurora dev/demo data ปัจจุบัน public route ของ #68 ควรเปิด detail ได้เฉพาะ work items ที่ public:

| Work item id | Category | Type | Expected detail kind | Public evidence |
|---|---|---|---|---|
| `wi-pub-2019-multi-container` | `RESEARCH` | `PUBLICATION` | `publication` | `ev-pub-2019-doi` |
| `wi-pub-2024-privacy-edge` | `RESEARCH` | `PUBLICATION` | `publication` | `ev-pub-2024-demo-url` |
| `wi-pub-2025-hci-agent` | `RESEARCH` | `PUBLICATION` | `publication` | none expected from current demo |
| `wi-service-2568-speaker` | `ACADEMIC_SERVICE` | `INVITED_SPEAKER` | `service` | `ev-service-2568-speaker` |

Smoke tests ที่ควรมี:

- `GET /api/v2/work-items/wi-pub-2024-privacy-edge` ได้ `200`
- response ของ `wi-pub-2024-privacy-edge` มี `detail.kind = publication`
- response ของ `wi-pub-2024-privacy-edge` มี faculty 2 คน เรียงตาม `contribution_order`
- response ของ `wi-pub-2024-privacy-edge` มี evidence `ev-pub-2024-demo-url`
- response ของ `wi-service-2568-speaker` มี `detail.kind = service`
- `GET /api/v2/work-items/wi-teach-2567-2-cs333` ต้องได้ `404` ใน public route เพราะเป็น `INTERNAL`
- `GET /api/v2/work-items/wi-supervision-2567-phd-thesis` ต้องได้ `404` ใน public route เพราะเป็น `RESTRICTED`
- `GET /api/v2/work-items/not-found-id` ต้องได้ `404`
- public response ต้องไม่มี `source_score`, `source_weight`, `source_record_id`, `s3_key`, `checksum_sha256`

## Database Verification / SQL Baseline

ก่อน implement หรือก่อนปิดการ์ด ให้ตรวจ Aurora dev ด้วย RDS Data API หรือ RDS Query Editor โดยใช้ SQL ลักษณะนี้

เช็ก core/detail ของตัวอย่างหลัก:

```sql
SELECT
  wi.id,
  wi.title,
  wi.description,
  wi.category_code,
  wc.label_th AS category_label_th,
  wi.work_type_code,
  wt.label_th AS type_label_th,
  wi.visibility,
  wi.status,
  wi.start_date,
  wi.end_date,
  pd.publication_title,
  pd.venue,
  pd.publisher,
  pd.publication_year,
  pd.publication_date,
  pd.doi,
  pd.quartile,
  pd.indexing_database,
  pd.publication_kind,
  pd.external_url
FROM work_item wi
JOIN work_category wc
  ON wc.code = wi.category_code
JOIN work_type wt
  ON wt.category_code = wi.category_code
  AND wt.code = wi.work_type_code
LEFT JOIN publication_detail pd
  ON pd.work_item_id = wi.id
WHERE wi.id = 'wi-pub-2024-privacy-edge';
```

ผลสำคัญที่คาดหวัง:

| Field | Expected value |
|---|---|
| `id` | `wi-pub-2024-privacy-edge` |
| `category_code` | `RESEARCH` |
| `work_type_code` | `PUBLICATION` |
| `visibility` | `PUBLIC` |
| `status` | `ACTIVE` |
| `publication_year` | `2024` |
| `doi` | `10.0000/cs361.demo.privacy-edge.2024` |
| `quartile` | `Q2` |

เช็ก contributors/period:

```sql
SELECT
  f.id,
  f.public_slug,
  COALESCE(f.name_th, f.name_en) AS display_name,
  fwi.role,
  fwi.contribution_order,
  fwi.contribution_percent,
  ap.id AS academic_period_id,
  ap.label AS academic_period_label,
  ep.id AS evaluation_period_id,
  ep.code AS evaluation_period_code,
  ep.label AS evaluation_period_label
FROM faculty_work_item fwi
JOIN faculty f
  ON f.id = fwi.faculty_id
LEFT JOIN academic_period ap
  ON ap.id = fwi.academic_period_id
LEFT JOIN evaluation_period ep
  ON ep.id = fwi.evaluation_period_id
WHERE fwi.work_item_id = 'wi-pub-2024-privacy-edge'
ORDER BY fwi.contribution_order NULLS LAST, f.id;
```

ผลสำคัญที่คาดหวัง:

| Faculty | Role | Order | Percent | Period |
|---|---|---:|---:|---|
| `prapaporn-rattanatamrong` | `CORRESPONDING_AUTHOR` | 1 | `60.00` | `1/2567` |
| `kasidit-chanchio` | `AUTHOR` | 2 | `40.00` | `1/2567` |

เช็ก public evidence:

```sql
SELECT
  id,
  reference_type,
  label,
  external_url,
  mime_type,
  visibility
FROM evidence_reference
WHERE work_item_id = 'wi-pub-2024-privacy-edge'
  AND visibility = 'PUBLIC'
ORDER BY id;
```

ผลสำคัญที่คาดหวัง:

| `id` | `reference_type` | `label` | `visibility` |
|---|---|---|---|
| `ev-pub-2024-demo-url` | `URL` | `Synthetic publication landing page` | `PUBLIC` |

## Validation / Error Rules

- `{id}` ต้องเป็น non-empty string
- ถ้า id ไม่มีอยู่ ให้ `404`
- ถ้า id มีอยู่แต่ `work_item.status != ACTIVE` ให้ `404`
- ถ้า id มีอยู่แต่ `work_item.visibility != PUBLIC` ใน public route ให้ `404`
- ถ้า subtype detail row ไม่มี ให้ยัง return core response ได้ แต่ `detail` เป็น `null` หรือ `detail.kind = "unknown"` พร้อม log warning
- ถ้า evidence มีแต่ internal/restricted ให้ return `evidence: []`
- error response shape ควร consistent กับ #64/#66/#67

## Acceptance Criteria

- [ ] `GET /api/v2/work-items/{id}` return public detail ได้จาก Aurora จริง
- [ ] response มี core work item, category/type labels, contributors, periods, detail object, evidence metadata
- [ ] `detail.kind` ถูกต้องตาม subtype table
- [ ] faculty contributors เรียงตาม `contribution_order`
- [ ] public evidence metadata แสดงได้
- [ ] internal/restricted evidence ไม่ leak
- [ ] internal/restricted work item return public-safe `404`
- [ ] missing id return `404`
- [ ] response ไม่ส่ง raw/source/audit/auth/private storage fields
- [ ] มี tests ครอบคลุม subtype หลักจาก V2 demo dataset
- [ ] API Gateway route deploy แล้ว
- [ ] Lambda อ่าน Aurora subtype/evidence tables ผ่าน RDS Data API จริง
- [ ] CloudWatch logs แสดง request/success/error ของ endpoint นี้
- [ ] smoke test ผ่าน AWS endpoint อย่างน้อย public detail, not found และ restricted/internal case

## Review Checklist

Backend:

- [ ] ใช้ `work_item.id` จาก path parameter ไม่ hardcode demo id
- [ ] query ไม่อ่าน fixture file ใน production path
- [ ] mapper แยก subtype ชัดเจนและเพิ่ม category ใหม่ได้ภายหลัง
- [ ] contributor query ใช้ `faculty_work_item` ไม่ใช้ `work_item.created_by`
- [ ] response shape consistent กับ #66/#67
- [ ] sorting contributors ใช้ `contribution_order NULLS LAST, faculty.id`

QA:

- [ ] ใช้ `wi-pub-2024-privacy-edge` เป็น happy path
- [ ] ใช้ `wi-service-2568-speaker` ตรวจ non-publication public subtype
- [ ] ใช้ `wi-teach-2567-2-cs333` ตรวจ internal `404`
- [ ] ใช้ `wi-supervision-2567-phd-thesis` ตรวจ restricted `404`
- [ ] ตรวจว่า public response ไม่มี `s3_key` และ source/provenance fields

Security:

- [ ] public API ไม่เปิด storage key/private path
- [ ] public API ไม่เปิด source/import/audit/auth fields
- [ ] public API ไม่บอกว่า internal/restricted record มีอยู่จริง
- [ ] Lambda role ใช้สิทธิ์ Data API/Secrets เท่าที่จำเป็น

## Dependencies

Blocked by:

- #64 Build Master Data API
- #66 Build Work Item List/Search/Filter API
- #67 Build Faculty Work Items API

Blocks:

- #74 Build Work Item Detail UI
- #75 Integrate Repository UI with Real API

Related:

- #50 Prepare Multi-Year Demo Dataset
- #80 Execute Migration & Preserve V1 Compatibility
- #81 Final Integration, Deploy, Demo & Docs

## Suggested Labels

- `v2`
- `backend`
- `api`
- `detail`
- `ready-for-agent`

## Suggested Owner

Backend Developer

Reviewers:

- Tech Lead
- Data Developer
- Frontend Developer
- QA / Integration

## Estimate

1-1.5 days

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อ V2 มี Work Item Detail API ที่ deploy บน AWS จริงผ่าน API Gateway + Lambda + RDS Data API + Aurora, แสดง work item รายการเดียวได้ครบตาม subtype พร้อม faculty contributors, academic/evaluation periods, public evidence metadata, public-safe redaction, CloudWatch logs และ AWS smoke evidence ที่ตรวจสอบได้
