# [V2] Build Faculty Work Items API #67

## สรุป

สร้าง `GET /api/v2/faculties/{faculty_id}/work-items` เพื่อเรียกดูผลงาน/ภาระงานที่เกี่ยวข้องกับอาจารย์คนใดคนหนึ่ง โดยใช้ `faculty_work_item` เป็นตัวเชื่อมหลัก

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #53 แต่ GitHub issue จริงใช้ #67

## Production AWS Requirement

การ์ดนี้ต้องต่อกับ AWS production path เดียวกับ #66:

```text
Amazon API Gateway
→ AWS Lambda query handler
→ Amazon RDS Data API
→ Aurora PostgreSQL Serverless v2
```

ห้ามปิดการ์ดด้วย fixture/mock result เท่านั้น ต้องมี smoke test จาก deployed AWS endpoint จริง

## Background

V1 มี faculty profile เป็นศูนย์กลาง แต่ V2 ต้องแสดงผลงาน/ภาระงานของอาจารย์หลายปี หลายหมวดงาน และรองรับงานที่มีอาจารย์หลายคนร่วมกัน

`faculty_work_item` จึงเป็น table สำคัญสำหรับ:

- ผูก faculty กับ work item
- เก็บ role/contribution
- รองรับ many-to-many contribution
- filter ตาม academic/evaluation period ของ faculty แต่ละคน

## Database Alignment Check

เช็กกับไฟล์ `database/migrations/001_base.sql`, `database/seeds/001_master_data.sql`, `data/v2/fixtures/` และ Aurora dev แล้ว การ์ดนี้ต้องใช้ table/attribute ที่มีอยู่จริงดังนี้:

- `faculty`: `id`, `public_slug`, `name_th`, `name_en`, `academic_position`, `department`, `profile_image_url`, `profile_image_alt`, `visibility`, `status`
- `faculty_work_item`: `faculty_id`, `work_item_id`, `academic_period_id`, `evaluation_period_id`, `role`, `contribution_order`, `contribution_percent`, `contribution_note`, `quantity`, `credits`, `hours`
- `work_item`: `id`, `category_code`, `work_type_code`, `title`, `description`, `start_date`, `end_date`, `visibility`, `status`, `updated_at`
- `work_category`: `code`, `label_th`, `label_en`, `is_active`
- `work_type`: `code`, `category_code`, `label_th`, `label_en`, `is_active`
- `academic_period`: `id`, `academic_year`, `semester`, `label`
- `evaluation_period`: `id`, `code`, `label`

ตัวอย่าง id/code ที่ต้องใช้ให้ตรงกับฐานข้อมูลจริง:

- faculty id: `fac_prapaporn-rattanatamrong`
- faculty public slug: `prapaporn-rattanatamrong`
- academic period ids: `ap-2567-1`, `ap-2567-2`
- evaluation period id/code: `eval-2567-full-year` / `EVAL-2567`
- public work type examples: `PUBLICATION`, `INVITED_SPEAKER`

Aurora dev ตอนนี้มี public work items ต่ออาจารย์ดังนี้:

| Faculty | Public work item count |
|---|---:|
| `kasidit-chanchio` | 1 |
| `nuttanont-hongwarittorrn` | 2 |
| `prapaporn-rattanatamrong` | 2 |

เช็ก live ผ่าน RDS Data API วันที่ 2026-09-13 แล้ว baseline ข้างบนตรงกับ Aurora dev จริง

ข้อควรระวัง: `wi-research-2567-privacy-platform` เป็น `INTERNAL` ใน demo data จึงห้ามใช้เป็นตัวอย่าง success response ของ public endpoint #67

## เป้าหมาย

สร้าง API สำหรับเรียก work items ตาม faculty ที่:

- preserve V1 public slug compatibility
- รองรับ filter/pagination เหมือน Work Item List API
- แสดง role และ contribution ของ faculty คนนั้น
- ไม่ leak internal/restricted records ผ่าน public route
- ใช้ response shape ใกล้กับ `GET /api/v2/work-items`

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- สร้าง faculty profile API ใหม่แทน V1
- ทำ work item detail/subtype response
- ทำ admin-only faculty workload view
- ทำ official workload summary/scoring
- ทำ UI integration

## Scope

### ต้องทำ

- implement `GET /api/v2/faculties/{faculty_id}/work-items`
- รองรับ `{faculty_id}` เป็น stable id และพิจารณารองรับ `public_slug` ถ้า route layer เหมาะสม
- รองรับ query parameters:
  - `academic_period_id`
  - `evaluation_period_id`
  - `category`
  - `type`
  - `q`
  - `page`
  - `page_size`
- include faculty contribution fields ของ faculty ที่อยู่ใน route
- reuse validation/sorting/pagination pattern จาก #66
- เพิ่ม Lambda route/handler สำหรับ `GET /api/v2/faculties/{faculty_id}/work-items`
- เพิ่ม Data API query ที่ join `faculty`, `faculty_work_item`, `work_item` และ period tables จาก Aurora จริง
- configure API Gateway path parameter ให้ route นี้
- เพิ่ม CloudWatch logs สำหรับ faculty id, filters, not-found และ errors
- เพิ่ม tests สำหรับ faculty not found, no work items, multi-faculty work item, visibility
- เพิ่ม AWS smoke test ด้วย faculty demo slug/id จริง

### ไม่ต้องทำ

- aggregate workload score
- official report export
- evidence download
- admin edit/create flow

## API Contract

```http
GET /api/v2/faculties/{faculty_id}/work-items
```

ตัวอย่าง:

```text
/api/v2/faculties/prapaporn-rattanatamrong/work-items?category=RESEARCH&type=PUBLICATION&page=1&page_size=20
```

หมายเหตุ: ถึง route parameter จะชื่อ `{faculty_id}` แต่ implementation ควร resolve ได้ทั้ง `faculty.id` และ `faculty.public_slug` เพื่อรองรับ URL public แบบเดิมจาก V1

ตัวอย่าง response จาก public data จริงของ `prapaporn-rattanatamrong`:

```json
{
  "faculty": {
    "id": "fac_prapaporn-rattanatamrong",
    "public_slug": "prapaporn-rattanatamrong",
    "display_name": "ผศ.ดร.ประภาพร รัตนธำรง",
    "name_th": "ผศ.ดร.ประภาพร รัตนธำรง",
    "name_en": "Asst.Prof.Dr. Prapaporn Rattanatamrong",
    "academic_position": "ผู้ช่วยศาสตราจารย์",
    "department": "Computer Science"
  },
  "items": [
    {
      "id": "wi-pub-2019-multi-container",
      "title": "Multi-Container Application Migration with Load Balanced and Adaptive Parallel TCP",
      "description": "Thongthavorn, Wongsatorn & Rattanatamrong, Prapaporn. (2019). Multi-Container Application Migration with Load Balanced and Adaptive Parallel TCP. 55-62. 10.1109/HPCS48598.2019.9188218.",
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
      "academic_period": {
        "id": "ap-2567-2",
        "label": "2/2567",
        "academic_year": 2567,
        "semester": "2"
      },
      "evaluation_period": {
        "id": "eval-2567-full-year",
        "code": "EVAL-2567",
        "label": "Evaluation 2567"
      },
      "faculty_contribution": {
        "role": "AUTHOR",
        "contribution_order": 1,
        "contribution_percent": 100
      },
      "visibility": "PUBLIC",
      "start_date": "2019-01-01",
      "end_date": "2019-12-31",
      "updated_at": "2026-09-12T00:00:00Z"
    },
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
      "academic_period": {
        "id": "ap-2567-1",
        "label": "1/2567",
        "academic_year": 2567,
        "semester": "1"
      },
      "evaluation_period": {
        "id": "eval-2567-full-year",
        "code": "EVAL-2567",
        "label": "Evaluation 2567"
      },
      "faculty_contribution": {
        "role": "CORRESPONDING_AUTHOR",
        "contribution_order": 1,
        "contribution_percent": 60
      },
      "visibility": "PUBLIC",
      "start_date": "2024-10-01",
      "end_date": "2024-10-01",
      "updated_at": "2026-09-12T00:00:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 2
}
```

## Expected UI Usage

API นี้ถูกออกแบบมาให้ frontend ใช้ทำหน้า “ผลงานของอาจารย์คนนี้” เช่น tab `ผลงาน` ในหน้า faculty profile หรือ route เช่น `/faculties/{slug}/outputs`

ภาพที่คาดหวังใน UI:

- header แสดงอาจารย์คนเดียว เช่น ชื่อ ตำแหน่ง สาขา
- filter เฉพาะผลงานของอาจารย์คนนี้ เช่น ปีการศึกษา หมวดงาน ประเภทงาน keyword
- list/card ของ work items ที่อาจารย์คนนี้เกี่ยวข้อง
- แต่ละ card แสดงบทบาทของอาจารย์คนนั้นในผลงานนั้นโดยเฉพาะ
- แสดงสัดส่วน contribution ของอาจารย์คนนั้นถ้า public-safe
- ปุ่ม `ดูรายละเอียด` เพื่อไปหน้า detail ของ work item ซึ่งจะใช้ #68

ต่างจาก #66:

- #66 แสดง work items ทั้ง repository
- #67 แสดง work items ของ faculty คนเดียว
- #67 ไม่จำเป็นต้องแสดง contributors ทุกคน แต่ต้องแสดง contribution ของ faculty ที่ request ให้ถูกต้อง

## Expected UI Fields

| UI field | ใช้แสดงในหน้าเว็บ | จำเป็นไหม | หมายเหตุ |
|---|---|---|---|
| `faculty.id` | key ของอาจารย์ | จำเป็น | ใช้ internal reference |
| `faculty.public_slug` | URL/public slug | จำเป็น | ใช้ link/profile route |
| `faculty.display_name` | ชื่ออาจารย์บน header | จำเป็น | ใช้ `name_th` fallback `name_en` |
| `faculty.name_th` | ชื่อไทย | ควรมี | สำหรับ UI ภาษาไทย |
| `faculty.name_en` | ชื่ออังกฤษ | optional | ใช้ใน profile strip |
| `faculty.academic_position` | ตำแหน่งทางวิชาการ | ควรมี | เช่น `ผู้ช่วยศาสตราจารย์` |
| `faculty.department` | สาขา/ภาควิชา | ควรมี | เช่น `Computer Science` |
| `items[].id` | key และ link ไป detail | จำเป็น | ใช้กับ #68 |
| `items[].title` | ชื่อผลงานบน card | จำเป็น | ไม่ควรว่าง |
| `items[].description` | summary ใต้ชื่อผลงาน | ควรมี | UI truncate ได้ |
| `items[].category.code` | badge/filter code | จำเป็น | เช่น `RESEARCH` |
| `items[].category.label_th` | label หมวดงานไทย | ควรมี | เช่น `งานวิชาการ/วิจัย` |
| `items[].type.code` | badge/filter code | จำเป็น | เช่น `PUBLICATION` |
| `items[].type.label_th` | label ประเภทงานไทย | ควรมี | เช่น `ผลงานตีพิมพ์` |
| `items[].academic_period.id` | filter/key ปีการศึกษา | จำเป็น | มาจาก `faculty_work_item` |
| `items[].academic_period.label` | label ปี/เทอม | จำเป็น | เช่น `2/2567` |
| `items[].evaluation_period.id` | filter/key รอบประเมิน | ควรมี | มาจาก `faculty_work_item` |
| `items[].evaluation_period.label` | label รอบประเมิน | ควรมี | เช่น `Evaluation 2567` |
| `items[].faculty_contribution.role` | บทบาทของอาจารย์ที่ request | จำเป็น | เช่น `AUTHOR`, `CORRESPONDING_AUTHOR` |
| `items[].faculty_contribution.contribution_order` | ลำดับผู้มีส่วนร่วม | ควรมี | ใช้กับงานหลายอาจารย์ |
| `items[].faculty_contribution.contribution_percent` | สัดส่วนผลงาน | ควรมี | แสดงเฉพาะ public-safe |
| `items[].visibility` | badge `PUBLIC` | จำเป็น | public endpoint ต้องคืนเฉพาะ `PUBLIC` |
| `items[].start_date`, `end_date` | ช่วงเวลางาน | optional | ใช้ sort/display ถ้ามี |
| `items[].updated_at` | อัปเดตล่าสุด | ควรมี | ใช้ sort default |
| `page`, `page_size`, `total` | pagination | จำเป็น | ใช้ render pagination |

## Data Source / Table Mapping

| Response field | Source table | Source attribute | วิธี join / หมายเหตุ |
|---|---|---|---|
| `faculty.id` | `faculty` | `id` | resolve จาก `{faculty_id}` |
| `faculty.public_slug` | `faculty` | `public_slug` | resolver ควรรองรับ slug ด้วย |
| `faculty.display_name` | `faculty` | `name_th`, fallback `name_en` | ใช้ `COALESCE(name_th, name_en)` |
| `faculty.name_th` | `faculty` | `name_th` | public-safe |
| `faculty.name_en` | `faculty` | `name_en` | public-safe |
| `faculty.academic_position` | `faculty` | `academic_position` | public-safe |
| `faculty.department` | `faculty` | `department` | public-safe |
| `items[].id` | `work_item` | `id` | join ผ่าน `faculty_work_item.work_item_id` |
| `items[].title` | `work_item` | `title` | title หลัก |
| `items[].description` | `work_item` | `description` | summary |
| `items[].category.code` | `work_item` | `category_code` | FK ไป `work_category.code` |
| `items[].category.label_th` | `work_category` | `label_th` | join `work_category.code = work_item.category_code` |
| `items[].category.label_en` | `work_category` | `label_en` | join `work_category.code = work_item.category_code` |
| `items[].type.code` | `work_item` | `work_type_code` | FK ไป `work_type.code` |
| `items[].type.label_th` | `work_type` | `label_th` | join ด้วย `(category_code, code)` |
| `items[].type.label_en` | `work_type` | `label_en` | join ด้วย `(category_code, code)` |
| `items[].academic_period.id` | `faculty_work_item` | `academic_period_id` | period ของ relation ของ faculty ที่ request |
| `items[].academic_period.label` | `academic_period` | `label` | join `academic_period.id = faculty_work_item.academic_period_id` |
| `items[].academic_period.academic_year` | `academic_period` | `academic_year` | ใช้ filter/sort |
| `items[].academic_period.semester` | `academic_period` | `semester` | ใช้ filter/sort |
| `items[].evaluation_period.id` | `faculty_work_item` | `evaluation_period_id` | evaluation period ของ relation |
| `items[].evaluation_period.code` | `evaluation_period` | `code` | join `evaluation_period.id = faculty_work_item.evaluation_period_id` |
| `items[].evaluation_period.label` | `evaluation_period` | `label` | แสดงใน UI/filter |
| `items[].faculty_contribution.role` | `faculty_work_item` | `role` | ต้องเป็น role ของ faculty ที่ request |
| `items[].faculty_contribution.contribution_order` | `faculty_work_item` | `contribution_order` | ต้องเป็น relation ของ faculty ที่ request |
| `items[].faculty_contribution.contribution_percent` | `faculty_work_item` | `contribution_percent` | ต้องเป็น relation ของ faculty ที่ request |
| `items[].visibility` | `work_item` | `visibility` | public route ต้องเป็น `PUBLIC` |
| `items[].start_date` | `work_item` | `start_date` | optional |
| `items[].end_date` | `work_item` | `end_date` | optional |
| `items[].updated_at` | `work_item` | `updated_at` | default sort |
| `page` | request/query | `page` | default `1` |
| `page_size` | request/query | `page_size` | default `20`, max `100` |
| `total` | SQL count | `COUNT(DISTINCT work_item.id)` | count หลัง apply filters |

## Query / Filter Mapping

| Query parameter | ใช้ filter จาก table | Attribute | กติกา |
|---|---|---|---|
| `{faculty_id}` | `faculty` | `id` หรือ `public_slug` | ต้องเจอ active/public faculty ไม่งั้น `404` |
| `academic_period_id` | `faculty_work_item` | `academic_period_id` | filter เฉพาะ relation ของ faculty ที่ request |
| `evaluation_period_id` | `faculty_work_item` | `evaluation_period_id` | filter เฉพาะ relation ของ faculty ที่ request |
| `category` | `work_item` / `work_category` | `category_code`, `code` | ต้องเป็น active category |
| `type` | `work_item` / `work_type` | `work_type_code`, `code` | ต้องเป็น active type และอยู่ใต้ category ถ้าส่ง category |
| `q` | `work_item` | `title`, `description` | search เฉพาะผลงานของ faculty นี้ |
| `page` | request | `page` | default `1`, min `1` |
| `page_size` | request | `page_size` | default `20`, max `100` |

## Public-Safe Fields

ต้องส่งออกใน public response:

- public faculty summary: `id`, `public_slug`, `name_th`, `name_en`, `academic_position`, `department`, `profile_image_url`, `profile_image_alt`
- `work_item.id`, `title`, `description`
- `work_item.category_code`, `work_category.label_th`, `work_category.label_en`
- `work_item.work_type_code`, `work_type.label_th`, `work_type.label_en`
- `academic_period.id`, `label`, `academic_year`, `semester`
- `evaluation_period.id`, `code`, `label`
- `faculty_work_item.role`, `contribution_order`, `contribution_percent`
- `work_item.visibility`, `start_date`, `end_date`, `updated_at`

ห้ามส่งออกใน public response ของ #67:

- `faculty_work_item.contribution_note`
- `faculty_work_item.quantity`
- `faculty_work_item.credits`
- `faculty_work_item.hours`
- `work_item.source_score`
- `work_item.source_weight`
- `work_item.source_section_code`
- `work_item.import_batch_id`
- `work_item.source_record_id`
- `source_record.raw_record`
- `audit_event`
- `app_user` / `app_role` / auth data
- evidence detail หรือ private S3 key
- subtype detail tables แบบเต็ม เพราะเป็นหน้าที่ของ #68

## Expected Demo Result Baseline

ถ้าใช้ Aurora dev/demo data ปัจจุบัน public route ของ #67 ควรเห็นเฉพาะ `work_item.status = ACTIVE` และ `work_item.visibility = PUBLIC`

Expected baseline:

| Faculty slug | Expected total | Expected public work item ids |
|---|---:|---|
| `prapaporn-rattanatamrong` | 2 | `wi-pub-2019-multi-container`, `wi-pub-2024-privacy-edge` |
| `kasidit-chanchio` | 1 | `wi-pub-2024-privacy-edge` |
| `nuttanont-hongwarittorrn` | 2 | `wi-pub-2025-hci-agent`, `wi-service-2568-speaker` |

Smoke tests ที่ควรมี:

- `GET /api/v2/faculties/prapaporn-rattanatamrong/work-items` ได้ `total = 2`
- `GET /api/v2/faculties/fac_prapaporn-rattanatamrong/work-items` ได้ผลเหมือน slug ถ้ารองรับทั้ง id/slug
- `GET /api/v2/faculties/prapaporn-rattanatamrong/work-items?category=RESEARCH&type=PUBLICATION` ได้ 2 รายการ
- `GET /api/v2/faculties/prapaporn-rattanatamrong/work-items?academic_period_id=ap-2567-1` ได้ `wi-pub-2024-privacy-edge`
- `GET /api/v2/faculties/prapaporn-rattanatamrong/work-items?academic_period_id=ap-2567-2` ได้ `wi-pub-2019-multi-container`
- `GET /api/v2/faculties/prapaporn-rattanatamrong/work-items?category=TEACHING` ได้ `items: []` ใน public route เพราะ teaching demo data เป็น `INTERNAL`
- unknown faculty ต้อง return `404`
- inactive/non-public faculty ถ้ามีในอนาคตต้อง return `404`

## Database Verification / SQL Baseline

ก่อน implement หรือก่อนปิดการ์ด ให้ตรวจ Aurora dev ด้วย RDS Data API หรือ RDS Query Editor โดยใช้ SQL ลักษณะนี้ เพื่อยืนยันว่า API ไม่ได้ทำงานจาก fixture/mock:

```sql
SELECT
  f.public_slug,
  COUNT(wi.id)::int AS public_work_item_count,
  COALESCE(string_agg(wi.id, ', ' ORDER BY wi.id), '') AS public_work_item_ids
FROM faculty f
LEFT JOIN faculty_work_item fwi
  ON fwi.faculty_id = f.id
LEFT JOIN work_item wi
  ON wi.id = fwi.work_item_id
  AND wi.status = 'ACTIVE'
  AND wi.visibility = 'PUBLIC'
WHERE f.status = 'ACTIVE'
  AND f.visibility = 'PUBLIC'
GROUP BY f.public_slug
ORDER BY f.public_slug;
```

ผลที่คาดหวังจาก Aurora dev ปัจจุบัน:

| `public_slug` | `public_work_item_count` | `public_work_item_ids` |
|---|---:|---|
| `kasidit-chanchio` | 1 | `wi-pub-2024-privacy-edge` |
| `nuttanont-hongwarittorrn` | 2 | `wi-pub-2025-hci-agent, wi-service-2568-speaker` |
| `prapaporn-rattanatamrong` | 2 | `wi-pub-2019-multi-container, wi-pub-2024-privacy-edge` |

SQL baseline สำหรับเคสหลักของ endpoint นี้:

```sql
SELECT
  wi.id,
  wi.title,
  wi.category_code,
  wi.work_type_code,
  fwi.academic_period_id,
  fwi.evaluation_period_id,
  fwi.role,
  fwi.contribution_order,
  fwi.contribution_percent,
  wi.visibility
FROM faculty f
JOIN faculty_work_item fwi
  ON fwi.faculty_id = f.id
JOIN work_item wi
  ON wi.id = fwi.work_item_id
WHERE (f.public_slug = 'prapaporn-rattanatamrong'
    OR f.id = 'fac_prapaporn-rattanatamrong')
  AND f.status = 'ACTIVE'
  AND f.visibility = 'PUBLIC'
  AND wi.status = 'ACTIVE'
  AND wi.visibility = 'PUBLIC'
ORDER BY wi.id;
```

ผลที่คาดหวัง:

| `id` | `category_code` | `work_type_code` | `academic_period_id` | `role` | `contribution_percent` |
|---|---|---|---|---|---:|
| `wi-pub-2019-multi-container` | `RESEARCH` | `PUBLICATION` | `ap-2567-2` | `AUTHOR` | `100.00` |
| `wi-pub-2024-privacy-edge` | `RESEARCH` | `PUBLICATION` | `ap-2567-1` | `CORRESPONDING_AUTHOR` | `60.00` |

Implementation query จริงสามารถต่อยอดจาก SQL baseline นี้ โดยเพิ่ม join ไปที่ `work_category`, `work_type`, `academic_period`, `evaluation_period` เพื่อสร้าง response object ให้ครบตาม contract ด้านบน

## Rules

- ถ้า faculty ไม่มีอยู่หรือไม่ public-safe ให้ return `404`
- public response ต้อง return เฉพาะ work item ที่ `status = ACTIVE` และ `visibility = PUBLIC`
- contribution fields ต้องมาจาก relation ของ faculty ที่ request เท่านั้น
- multi-faculty work item ต้องแสดงได้โดยไม่ซ้ำรายการ
- sorting default ควรใช้ period/date/update time ที่ stable และ predictable

## Acceptance Criteria

- [ ] endpoint คืน work items ของ faculty ได้ถูกต้อง
- [ ] รองรับ filter/pagination ตาม contract
- [ ] preserve public slug/id compatibility ตามที่ทีมเลือก
- [ ] multi-faculty work item ไม่ซ้ำและแสดง contribution ของ faculty ที่ถูกต้อง
- [ ] public route ไม่ leak internal/restricted records
- [ ] faculty not found return `404`
- [ ] มี tests สำหรับ demo cases ใน `docs/v2/demo-dataset.md`
- [ ] API Gateway route deploy แล้ว
- [ ] Lambda อ่าน Aurora ผ่าน RDS Data API จริง
- [ ] smoke test ผ่าน AWS endpoint สำหรับ faculty demo case

## Review Checklist

Backend:

- [ ] ใช้ `faculty_work_item` ไม่ shortcut จาก `work_item.created_by`
- [ ] query ไม่ hardcode faculty demo ids
- [ ] response shape ใช้ชื่อ field consistent กับ #66
- [ ] production path ไม่อ่าน fixture file

QA:

- [ ] case `prapaporn-rattanatamrong` academic year 2567 ใช้ตรวจได้
- [ ] many-faculty publication/research project แสดงถูกต้อง

Security:

- [ ] public API ไม่เปิด contribution note ที่ไม่ public-safe ถ้าถูกจัดเป็น internal

## Dependencies

Blocked by:

- #64 Build Master Data API
- #66 Build Work Item List/Search/Filter API

Blocks:

- #74 Build Work Item Detail UI
- #75 Integrate Repository UI with Real API

Related:

- #49 Define V1 to V2 Data Mapping
- #80 Execute Migration & Preserve V1 Compatibility

## Suggested Labels

- `v2`
- `backend`
- `api`
- `faculty`
- `ready-for-agent`

## Suggested Owner

Backend Developer

Reviewers:

- Tech Lead
- Data Developer
- QA / Integration

## Estimate

0.5-1 day

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อ V2 เรียกผลงาน/ภาระงานของอาจารย์รายคนได้จาก Aurora relation จริงผ่าน API Gateway + Lambda + RDS Data API พร้อม filter, pagination, contribution fields, public visibility rule และ AWS smoke evidence ที่ตรวจสอบได้
