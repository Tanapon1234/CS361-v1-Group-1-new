# [V2] Build Work Item List/Search/Filter API #66

## สรุป

สร้าง `GET /api/v2/work-items` สำหรับค้นหา กรอง และแบ่งหน้า work items ของ V2 repository โดยอ่านจาก Aurora ผ่าน AWS Lambda + RDS Data API และ enforce public-safe visibility ที่ backend

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #52 แต่ GitHub issue จริงใช้ #66

## Production AWS Requirement

การ์ดนี้ต้อง implement เป็น production AWS API จริง:

```text
Amazon API Gateway
→ AWS Lambda query handler
→ Amazon RDS Data API
→ Aurora PostgreSQL Serverless v2
```

fixture/mock ใช้ได้เฉพาะ unit test หรือ local fallback เท่านั้น ไม่ถือว่าเพียงพอสำหรับปิดการ์ดนี้

## Background

V2 ต้องให้ผู้ใช้ค้นหาและกรองข้อมูลผลงาน/ภาระงานอาจารย์ได้จาก repository กลาง ไม่ใช่อ่านไฟล์ public faculty profile แบบ V1 เท่านั้น

ตอนนี้มี baseline แล้ว:

- schema และ indexes ใน `database/migrations/001_base.sql`
- master data seed ใน `database/seeds/001_master_data.sql`
- demo dataset ใน `data/v2/fixtures/`
- Master Data API จาก #64 สำหรับ filter options

## Database Alignment Check

เช็กกับไฟล์ใน `database/` แล้ว การ์ดนี้อ้างอิง table/attribute ที่มีอยู่จริงใน schema:

- `work_item`: `id`, `category_code`, `work_type_code`, `title`, `description`, `start_date`, `end_date`, `visibility`, `status`, `updated_at`
- `work_category`: `code`, `label_th`, `label_en`, `is_active`
- `work_type`: `code`, `category_code`, `label_th`, `label_en`, `is_active`
- `faculty_work_item`: `faculty_id`, `work_item_id`, `academic_period_id`, `evaluation_period_id`, `role`, `contribution_order`, `contribution_percent`
- `faculty`: `id`, `public_slug`, `name_th`, `name_en`, `visibility`, `status`
- `academic_period`: `id`, `academic_year`, `semester`, `label`
- `evaluation_period`: `id`, `code`, `label`

ตัวอย่าง id ในการ์ดนี้ต้องใช้รูปแบบจริงจาก demo/Aurora dev:

- faculty id: `fac_prapaporn-rattanatamrong`
- academic period id: `ap-2567-1`, `ap-2567-2`
- evaluation period id/code: `eval-2567-full-year` / `EVAL-2567`
- work type code: `PUBLICATION`, `INVITED_SPEAKER`, `LECTURE`, ไม่ใช้ชื่อเก่าแบบ `TEACHING_LECTURE`

หมายเหตุ: `database/seeds/001_master_data.sql` มี master data มากกว่า fixture demo บางส่วน เช่น `OTHER` category และ work types เพิ่มเติม รวมปัจจุบันใน Aurora dev คือ `work_category = 6`, `work_type = 26` แต่ public work item demo ที่ #66 ต้องเห็นมี 4 รายการตาม visibility rule

## เป้าหมาย

สร้าง read API สำหรับ list/search ที่:

- รองรับ filter หลักตาม contract ใน `docs/v2/V2_Central_Design.md`
- return list response shape ที่ frontend ใช้ทำ result list/pagination ได้
- ไม่เปิด `INTERNAL` หรือ `RESTRICTED` ผ่าน public API โดยไม่ได้รับอนุญาต
- มี validation และ error shape ที่ consistent
- มี test ครอบคลุม search/filter/pagination/visibility

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- ทำ work item detail API
- ทำ faculty-specific work item endpoint
- ทำ admin CRUD API
- ทำ UI หน้า `/outputs`
- ทำ full text search ด้วย OpenSearch
- ทำ scoring/official workload calculation

## Scope

### ต้องทำ

- implement `GET /api/v2/work-items`
- รองรับ query parameters:
  - `faculty_id`
  - `academic_period_id`
  - `evaluation_period_id`
  - `category`
  - `type`
  - `visibility`
  - `q`
  - `page`
  - `page_size`
- join ข้อมูลจาก `work_item`, `work_type`, `work_category`, `faculty_work_item`, `faculty`, `academic_period`, `evaluation_period`
- default public route ต้อง return เฉพาะ `status = ACTIVE` และ `visibility = PUBLIC`
- เพิ่ม mapper/DTO สำหรับ list item
- เพิ่ม Lambda route/handler สำหรับ `GET /api/v2/work-items`
- เพิ่ม Data API query layer ที่อ่าน Aurora จริง
- configure API Gateway route/stage สำหรับ endpoint นี้
- เพิ่ม CloudWatch log สำหรับ request id, query filters, validation failure และ unexpected errors
- เพิ่ม input validation และ response envelope
- เพิ่ม tests สำหรับ success, empty state, invalid query, pagination และ visibility
- เพิ่ม AWS smoke test สำหรับ deployed endpoint
- อัปเดต docs contract ถ้า implementation มีรายละเอียดเพิ่ม

### ไม่ต้องทำ

- subtype detail tables
- evidence detail
- admin-only visibility expansion
- mutation/write operation
- frontend integration

## API Contract

```http
GET /api/v2/work-items
```

ตัวอย่าง query:

```text
/api/v2/work-items?faculty_id=fac_prapaporn-rattanatamrong&academic_period_id=ap-2567-1&category=RESEARCH&type=PUBLICATION&page=1&page_size=20
```

ตัวอย่าง response จากข้อมูล demo/public ที่มีอยู่จริง:

```json
{
  "items": [
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
      "faculty": [
        {
          "id": "fac_prapaporn-rattanatamrong",
          "display_name": "ผศ.ดร.ประภาพร รัตนธำรง",
          "slug": "prapaporn-rattanatamrong",
          "role": "CORRESPONDING_AUTHOR",
          "contribution_order": 1,
          "contribution_percent": 60
        },
        {
          "id": "fac_kasidit-chanchio",
          "display_name": "ผศ.ดร.กษิดิศ ชาญเชี่ยว",
          "slug": "kasidit-chanchio",
          "role": "AUTHOR",
          "contribution_order": 2,
          "contribution_percent": 40
        }
      ],
      "visibility": "PUBLIC",
      "updated_at": "2026-09-12T00:00:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

## Expected UI Usage

API นี้ถูกออกแบบมาให้ frontend ใช้ทำหน้า repository list/search/filter เช่นหน้า `/outputs`

ภาพที่คาดหวังใน UI:

- ช่องค้นหา keyword ด้านบน
- filter ปีการศึกษา / รอบประเมิน / หมวดงาน / ประเภทงาน / อาจารย์
- list หรือ card ของ work items
- badge หมวดงาน เช่น `RESEARCH`, `TEACHING`
- badge ประเภทงาน เช่น `PUBLICATION`, `LECTURE`
- badge visibility เช่น `PUBLIC`
- ชื่อผลงาน
- คำอธิบายสั้น
- ปีการศึกษา
- รายชื่ออาจารย์ที่เกี่ยวข้อง
- บทบาทของอาจารย์ในผลงาน เช่น `AUTHOR`, `INSTRUCTOR`, `PRINCIPAL_INVESTIGATOR`
- pagination เช่น page, page size, total
- ปุ่มหรือ link ไปหน้า detail ของ work item ซึ่งจะใช้ #68 ต่อ

API นี้เป็น public list endpoint ดังนั้นเป้าหมายคือ “เห็นรายการพอให้เลือกและกดดูต่อ” ไม่ใช่ “เห็นข้อมูลลึกทั้งหมดของผลงาน”

## Expected UI Fields

ตารางนี้คือ field ที่ frontend ควรเอาไปแสดงในหน้า list และเหตุผลที่ต้องมี

| UI field | ใช้แสดงในหน้าเว็บ | จำเป็นไหม | หมายเหตุ |
|---|---|---|---|
| `id` | ใช้เป็น key และ link ไป detail | จำเป็น | ใช้กับ #68 เช่น `/outputs/{id}` |
| `title` | ชื่อผลงานบน card/list | จำเป็น | ต้องอ่านง่ายและไม่ว่าง |
| `description` | คำอธิบายสั้นใต้ชื่อผลงาน | ควรมี | UI อาจ truncate เหลือ 1-2 บรรทัด |
| `category.code` | badge/code เช่น `RESEARCH` | จำเป็น | ใช้ filter และสี badge |
| `category.label_th` | label ภาษาไทย เช่น `งานวิชาการ/วิจัย` | ควรมี | ใช้แสดงกับผู้ใช้ไทย |
| `category.label_en` | label อังกฤษ | optional | ใช้ถ้า UI bilingual |
| `type.code` | badge/code เช่น `PUBLICATION` | จำเป็น | ใช้ filter ประเภทงาน |
| `type.label_th` | label ประเภทงานภาษาไทย | ควรมี | เช่น `ผลงานตีพิมพ์` |
| `type.label_en` | label ประเภทงานอังกฤษ | optional | ใช้ถ้า UI bilingual |
| `academic_period.id` | filter/key ของปีการศึกษา | จำเป็น | มาจาก relation `faculty_work_item` |
| `academic_period.label` | label เช่น `2/2567` | จำเป็น | แสดงบน card |
| `academic_period.academic_year` | ปีการศึกษา เช่น `2567` | ควรมี | ช่วย sort/filter |
| `academic_period.semester` | ภาคการศึกษา เช่น `2` | ควรมี | ช่วยแสดงรายละเอียด |
| `evaluation_period.id` | filter/key ของรอบประเมิน | ควรมี | ใช้กับ filter ขั้นสูง |
| `evaluation_period.label` | label รอบประเมิน | ควรมี | แสดงถ้า UI ต้องการ |
| `faculty[].id` | key ของอาจารย์ | จำเป็น | ใช้ link ไปหน้า faculty |
| `faculty[].display_name` | ชื่ออาจารย์ | จำเป็น | เช่น `ผศ.ดร.ประภาพร รัตนธำรง` |
| `faculty[].slug` | public slug | จำเป็น | ใช้ทำ URL หน้าอาจารย์ |
| `faculty[].role` | บทบาทในผลงาน | จำเป็น | เช่น `AUTHOR`, `INSTRUCTOR` |
| `faculty[].contribution_order` | ลำดับผู้มีส่วนร่วม | ควรมี | สำคัญกับงานหลายอาจารย์ |
| `faculty[].contribution_percent` | สัดส่วนผลงาน | ควรมี | แสดงได้เฉพาะ public-safe |
| `visibility` | badge `PUBLIC` | จำเป็น | public endpoint ควรคืนเฉพาะ `PUBLIC` |
| `start_date` | วันที่เริ่มต้นของ work item | optional | ใช้ sort/display ถ้ามี |
| `end_date` | วันที่สิ้นสุดของ work item | optional | ใช้ sort/display ถ้ามี |
| `updated_at` | วันที่ update ล่าสุด | ควรมี | ใช้ sort default และแสดง “อัปเดตล่าสุด” |

## Data Source / Table Mapping

ตารางนี้คือ mapping ระหว่าง response field กับ table/attribute จริง

| Response field | Source table | Source attribute | วิธี join / หมายเหตุ |
|---|---|---|---|
| `items[].id` | `work_item` | `id` | primary id ของรายการ |
| `items[].title` | `work_item` | `title` | title หลักของ work item |
| `items[].description` | `work_item` | `description` | summary สำหรับ list |
| `items[].category.code` | `work_item` | `category_code` | FK ไป `work_category.code` |
| `items[].category.label_th` | `work_category` | `label_th` | join `work_category.code = work_item.category_code` |
| `items[].category.label_en` | `work_category` | `label_en` | join `work_category.code = work_item.category_code` |
| `items[].type.code` | `work_item` | `work_type_code` | FK ไป `work_type.code` |
| `items[].type.label_th` | `work_type` | `label_th` | join ด้วย `(category_code, code)` |
| `items[].type.label_en` | `work_type` | `label_en` | join ด้วย `(category_code, code)` |
| `items[].visibility` | `work_item` | `visibility` | public route ต้องเป็น `PUBLIC` เท่านั้น |
| `items[].status` | `work_item` | `status` | ใช้ filter backend เท่านั้น ไม่จำเป็นต้อง expose |
| `items[].start_date` | `work_item` | `start_date` | optional display/sort |
| `items[].end_date` | `work_item` | `end_date` | optional display/sort |
| `items[].updated_at` | `work_item` | `updated_at` | default sorting |
| `items[].academic_period.id` | `faculty_work_item` | `academic_period_id` | relation-level period |
| `items[].academic_period.label` | `academic_period` | `label` | join `academic_period.id = faculty_work_item.academic_period_id` |
| `items[].academic_period.academic_year` | `academic_period` | `academic_year` | ใช้ filter ปี |
| `items[].academic_period.semester` | `academic_period` | `semester` | ใช้ filter ภาค |
| `items[].evaluation_period.id` | `faculty_work_item` | `evaluation_period_id` | relation-level evaluation period |
| `items[].evaluation_period.code` | `evaluation_period` | `code` | join `evaluation_period.id = faculty_work_item.evaluation_period_id` |
| `items[].evaluation_period.label` | `evaluation_period` | `label` | ใช้แสดงรอบประเมิน |
| `items[].faculty[].id` | `faculty` | `id` | join ผ่าน `faculty_work_item.faculty_id` |
| `items[].faculty[].display_name` | `faculty` | `name_th`, fallback `name_en` | ใช้ `COALESCE(name_th, name_en)` |
| `items[].faculty[].slug` | `faculty` | `public_slug` | ใช้สร้าง link หน้าอาจารย์ |
| `items[].faculty[].role` | `faculty_work_item` | `role` | บทบาทของอาจารย์ใน work item |
| `items[].faculty[].contribution_order` | `faculty_work_item` | `contribution_order` | ใช้เรียง contributor |
| `items[].faculty[].contribution_percent` | `faculty_work_item` | `contribution_percent` | แสดงได้ถ้า public-safe |
| `page` | request/query | `page` | default `1` |
| `page_size` | request/query | `page_size` | default `20`, max `100` |
| `total` | SQL count | `COUNT(DISTINCT work_item.id)` | count หลัง apply filters |

## Recommended Full Response Shape

ให้ implement response แบบมีข้อมูลพอสำหรับ UI ตั้งแต่แรก เพื่อไม่ให้ frontend ต้องเดา field เอง

```json
{
  "items": [
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
      "faculty": [
        {
          "id": "fac_prapaporn-rattanatamrong",
          "display_name": "ผศ.ดร.ประภาพร รัตนธำรง",
          "slug": "prapaporn-rattanatamrong",
          "role": "CORRESPONDING_AUTHOR",
          "contribution_order": 1,
          "contribution_percent": 60
        },
        {
          "id": "fac_kasidit-chanchio",
          "display_name": "ผศ.ดร.กษิดิศ ชาญเชี่ยว",
          "slug": "kasidit-chanchio",
          "role": "AUTHOR",
          "contribution_order": 2,
          "contribution_percent": 40
        }
      ],
      "visibility": "PUBLIC",
      "start_date": "2024-10-01",
      "end_date": "2024-10-01",
      "updated_at": "2026-09-12T00:00:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

หมายเหตุ:

- `academic_period` และ `evaluation_period` มาจาก `faculty_work_item` เพราะ work item หนึ่งรายการอาจผูกกับอาจารย์หลายคนผ่าน relation table
- ถ้า work item มีหลาย faculty relation ที่ period ต่างกัน ให้ implementation ต้องเลือกกติกาให้ชัดเจน เช่นใช้ relation ที่ตรงกับ filter ก่อน หรือ aggregate distinct periods ในอนาคต
- สำหรับ #66 เวอร์ชันแรก ให้ยึด period ที่มาจาก relation ที่ถูกใช้ในผลลัพธ์ และเขียน test ให้ครอบคลุม demo data

## Query / Filter Mapping

| Query parameter | ใช้ filter จาก table | Attribute | กติกา |
|---|---|---|---|
| `faculty_id` | `faculty_work_item` / `faculty` | `faculty_id`, `faculty.id` | คืน work items ที่ผูกกับอาจารย์คนนั้น |
| `academic_period_id` | `faculty_work_item` | `academic_period_id` | filter ตาม period ใน relation |
| `evaluation_period_id` | `faculty_work_item` | `evaluation_period_id` | filter ตาม evaluation period ใน relation |
| `category` | `work_item` / `work_category` | `category_code`, `code` | ต้องเป็น code ที่มีจริงและ active |
| `type` | `work_item` / `work_type` | `work_type_code`, `code` | ต้องเป็น type ที่มีจริงและอยู่ใต้ category ที่เลือกถ้ามี category |
| `visibility` | `work_item` | `visibility` | public route อนุญาตเฉพาะ `PUBLIC` หรือไม่ส่งค่า |
| `q` | `work_item`, `faculty`, `work_category`, `work_type` | `title`, `description`, `name_th`, `name_en`, labels | search แบบ case-insensitive |
| `page` | request | `page` | default `1`, min `1` |
| `page_size` | request | `page_size` | default `20`, max `100` |

## Public-Safe Fields

ต้องส่งออกใน public response:

- `work_item.id`
- `work_item.title`
- `work_item.description`
- `work_item.category_code`
- `work_category.label_th`, `label_en`
- `work_item.work_type_code`
- `work_type.label_th`, `label_en`
- `academic_period.id`, `label`, `academic_year`, `semester`
- `evaluation_period.id`, `code`, `label`
- public faculty id/name/slug
- public-safe role/contribution fields จาก `faculty_work_item`
- `work_item.visibility`
- `work_item.start_date`, `end_date`, `updated_at`

ห้ามส่งออกใน public response ของ #66:

- `work_item.source_score`
- `work_item.source_weight`
- `work_item.source_section_code`
- `work_item.import_batch_id`
- `work_item.source_record_id`
- `faculty_work_item.contribution_note`
- `faculty_work_item.quantity`
- `faculty_work_item.credits`
- `faculty_work_item.hours`
- `source_record.raw_record`
- `audit_event`
- `app_user` / `app_role` / auth data
- evidence detail หรือ private S3 key
- subtype detail tables แบบเต็ม เพราะเป็นหน้าที่ของ #68

## Expected Demo Result Baseline

ถ้าใช้ demo dataset ใน `data/v2/fixtures/` และเรียก public route แบบไม่ส่ง filter เพิ่ม ควรเห็นเฉพาะ work items ที่ `status = ACTIVE` และ `visibility = PUBLIC`

Expected public work items:

| Work item id | Title | Category | Type | Expected faculty |
|---|---|---|---|---|
| `wi-pub-2019-multi-container` | `Multi-Container Application Migration with Load Balanced and Adaptive Parallel TCP` | `RESEARCH` | `PUBLICATION` | `prapaporn-rattanatamrong` |
| `wi-pub-2024-privacy-edge` | `Privacy-Preserving Edge Analytics for Smart Campus Workload Signals` | `RESEARCH` | `PUBLICATION` | `prapaporn-rattanatamrong`, `kasidit-chanchio` |
| `wi-pub-2025-hci-agent` | `Adaptive Interface Agents for Computing Education` | `RESEARCH` | `PUBLICATION` | `nuttanont-hongwarittorrn` |
| `wi-service-2568-speaker` | `Invited Speaker: Responsible AI and Privacy in Education` | `ACADEMIC_SERVICE` | `INVITED_SPEAKER` | `nuttanont-hongwarittorrn` |

ดังนั้น public smoke test พื้นฐานควรตรวจได้อย่างน้อย:

- `GET /api/v2/work-items` ได้ `total = 4` เมื่อใช้ demo data ตาม fixtures
- `GET /api/v2/work-items?category=RESEARCH` ได้ 3 รายการ public
- `GET /api/v2/work-items?type=PUBLICATION` ได้ 3 รายการ public
- `GET /api/v2/work-items?q=privacy` ไม่คืน restricted/internal rows ใน public route
- `GET /api/v2/work-items?faculty_id=fac_prapaporn-rattanatamrong&type=PUBLICATION` ได้ 2 รายการ public
- `GET /api/v2/work-items?category=TEACHING` ได้ `items: []` ใน public route ถ้า teaching demo data ยังเป็น `INTERNAL`

## Validation Rules

- `page` default = `1`, minimum = `1`
- `page_size` default = `20`, maximum = `100`
- `category` ต้องอยู่ใน `work_category.code`
- `type` ต้องอยู่ใน `work_type.code`
- ถ้าส่งทั้ง `category` และ `type`, type ต้องอยู่ใต้ category เดียวกัน
- public request ห้ามขอ `visibility=INTERNAL` หรือ `visibility=RESTRICTED`
- unknown query parameter ควร ignore หรือ reject ให้ consistent กับ API convention ที่ทีมเลือก

## Acceptance Criteria

- [ ] `GET /api/v2/work-items` return list ได้จาก data repository
- [ ] filter ตาม faculty, period, category, type, keyword ได้
- [ ] pagination return `page`, `page_size`, `total` ถูกต้อง
- [ ] default public response ไม่ leak internal/restricted records
- [ ] invalid category/type/page return error shape มาตรฐาน
- [ ] empty result return `items: []` ไม่ crash
- [ ] มี tests ครอบคลุม happy path และ edge cases
- [ ] docs/API contract อัปเดตตาม implementation จริง
- [ ] API Gateway route `GET /api/v2/work-items` deploy แล้ว
- [ ] Lambda query handler อ่าน Aurora ผ่าน RDS Data API จริง
- [ ] CloudWatch logs แสดง request/success/error ของ endpoint นี้
- [ ] smoke test ผ่าน deployed AWS endpoint ด้วย demo data จาก Aurora

## Review Checklist

Backend:

- [ ] SQL/query ไม่เกิด N+1 แบบชัดเจน
- [ ] query มี sorting ที่ stable เช่น `updated_at desc, id asc`
- [ ] DTO ไม่ expose raw/provenance/admin fields
- [ ] Lambda role ใช้สิทธิ์ Data API/Secrets เท่าที่จำเป็น
- [ ] production path ไม่อ่าน fixture file

QA:

- [ ] ใช้ `data/v2/fixtures/dataset-summary.json` เป็น expected baseline ได้
- [ ] test matrix จาก `docs/v2/demo-dataset.md` ผ่าน
- [ ] smoke test ใช้ AWS endpoint จริงและบันทึกผลไว้ใน issue/PR

Security:

- [ ] visibility ถูก enforce ใน backend
- [ ] public API ไม่เปิด source/audit/auth/evidence restricted fields

## Dependencies

Blocked by:

- #47 Design Relational Schema & SQL Migration
- #48 Provision Aurora / Data API / Secret / IAM
- #50 Prepare Multi-Year Demo Dataset
- #64 Build Master Data API

Blocks:

- #67 Build Faculty Work Items API
- #68 Build Work Item Detail API
- #73 Build Repository Result List & Pagination UI
- #75 Integrate Repository UI with Real API

Related:

- #49 Define V1 to V2 Data Mapping
- #80 Execute Migration & Preserve V1 Compatibility

## Suggested Labels

- `v2`
- `backend`
- `api`
- `search`
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

การ์ดนี้ถือว่าเสร็จเมื่อ V2 มี Work Item List/Search/Filter API ที่ deploy บน AWS จริงผ่าน API Gateway + Lambda + RDS Data API + Aurora, ค้นหา กรอง แบ่งหน้า และ enforce public visibility ได้จริง พร้อม contract, tests, CloudWatch/API smoke evidence และ frontend ใช้สร้างหน้า repository ต่อได้โดยไม่ต้องเดา response shape เอง
