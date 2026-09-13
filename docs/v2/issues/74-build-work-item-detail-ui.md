# [V2] Build Work Item Detail UI #74

## สรุป

สร้างหน้า `/outputs/{id}` สำหรับแสดงรายละเอียด work item รายการเดียวแบบ public-safe โดยโหลดข้อมูลจาก Detail API ของ #68 จริง แสดงข้อมูลกลางของผลงาน/ภาระงาน, รายชื่ออาจารย์ที่เกี่ยวข้อง, รายละเอียดตาม subtype, และ evidence metadata ที่เปิดเผยได้

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #60 แต่ GitHub issue จริงใช้ #74

## Production AWS Requirement

หน้า detail ต้องโหลดข้อมูลจาก deployed Work Item Detail API จาก #68 จริง:

```text
Frontend /outputs/{id}
→ deployed API Gateway GET /api/v2/work-items/{id}
→ Lambda detail handler
→ RDS Data API
→ Aurora PostgreSQL Serverless v2
```

ต้องใช้ frontend API base URL/config เดียวกับ #72 และ #73 เช่น:

```text
NEXT_PUBLIC_V2_API_BASE_URL=https://n89gqgnqw2.execute-api.ap-southeast-1.amazonaws.com
```

แล้วเรียก:

```text
GET ${NEXT_PUBLIC_V2_API_BASE_URL}/api/v2/work-items/{id}
```

mock/static detail ใช้ได้เฉพาะ component test หรือ local fallback เท่านั้น ไม่ถือว่าเพียงพอสำหรับปิดการ์ดนี้

## Background

หลังจาก #73 แสดง result list บนหน้า `/outputs` แล้ว ผู้ใช้ต้องสามารถกดรายการหนึ่งเพื่อดูรายละเอียดของผลงาน/ภาระงานนั้นได้ เช่น งานตีพิมพ์, งานสอน, งานวิจัย, งานบริการวิชาการ, งานดูแลนักศึกษา หรือภาระงานบริหาร

หน้า detail นี้เป็นหน้าที่ทำให้ V2 repository “ดูข้อมูลได้จริงเป็นราย record” ไม่ใช่เห็นแค่รายการสรุป ผู้ใช้จะใช้หน้านี้เพื่อตอบคำถามว่า:

- รายการนี้คือผลงาน/ภาระงานอะไร
- อยู่ในหมวดและประเภทใด
- เป็นของปีการศึกษา/รอบประเมินใด
- มีอาจารย์คนใดเกี่ยวข้อง และมีบทบาทอะไร
- มีรายละเอียดเฉพาะประเภทงานอะไรบ้าง
- มีหลักฐานหรือแหล่งอ้างอิง public-safe อะไรให้ตรวจสอบ

Detail API จาก #68 จะ return `detail.kind` เพื่อให้ frontend เลือก component แสดงผลตาม subtype ได้โดยไม่ต้องเดาจากชื่อ category/type เอง

## ความเกี่ยวข้องกับโจทย์

โจทย์ V2 ต้องมีระบบจัดเก็บและเรียกดูข้อมูลผลงาน/ภาระงานอาจารย์อย่างเป็นระบบ รองรับหลายปีการศึกษา และรองรับการค้นหา กรอง หรือเรียกดูตามเงื่อนไข

การ์ด #74 ตอบโจทย์ส่วน “เรียกดูรายละเอียด” หลังผู้ใช้ค้นหาหรือกรองจากหน้า repository แล้วกดเข้าไปดูรายการเดียวแบบละเอียด โดยยังรักษาขอบเขต public-safe ไม่แสดงข้อมูล internal, restricted, source, audit หรือ storage secret

## เป้าหมาย

สร้าง detail UI ที่:

- เปิด route `/outputs/{id}` ได้
- โหลดข้อมูลจาก deployed AWS Detail API จริง
- แสดงข้อมูลกลางของ work item ได้ครบ
- แสดง category/type/period metadata เป็นภาษาไทยเมื่อมี `label_th`
- แสดง faculty contributors พร้อม role/order/percent
- แสดง subtype detail ตาม `detail.kind`
- แสดง evidence metadata เฉพาะ public-safe
- รองรับ loading, not found, restricted-safe, error และ missing optional fields
- link กลับไป `/outputs` และ preserve query state จาก repository page ถ้าทำได้
- ไม่กระทบ V1 routes เช่น `/faculties` และ `/faculties/{id}`

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- ทำ evidence download
- ทำ signed URL จาก S3
- เปิดดู private/restricted evidence file
- ทำ admin edit/delete action
- ทำ official report print/export
- ทำ admin-only detail page
- ทำ mutation API
- ทำ auth
- แก้ Detail API #68
- แก้ Repository List UI #73

## User Stories

1. As a public user, I want to open a work item detail page, so that I can understand one output/workload record clearly.
2. As a public user, I want to see title, description, category, type, period, and updated date, so that I know the context of the record.
3. As a public user, I want to see faculty contributors and their roles, so that I know who is related to the record.
4. As a public user, I want publication/service/teaching/etc. details to render differently, so that each work type is readable.
5. As a public user, I want to see only public-safe evidence metadata, so that I can verify references without exposing restricted files.
6. As a public user, I want missing optional fields to show gracefully, so that an incomplete imported record does not break the page.
7. As a public user, I want not-found/restricted records to show a safe message, so that the app does not leak private existence.
8. As a frontend developer, I want a stable mapping from API fields to UI sections, so that future categories can be added cleanly.
9. As a QA reviewer, I want clear smoke-test URLs, so that I can prove the page uses deployed AWS API and not mock data.

## Scope

### ต้องทำ

- เพิ่ม route/page `/outputs/{id}`
- ต่อ data fetching กับ deployed `GET /api/v2/work-items/{id}` จาก #68
- ใช้ `NEXT_PUBLIC_V2_API_BASE_URL` หรือ config equivalent เดียวกับ #72/#73
- เพิ่ม detail layout/components:
  - header/title/description
  - category/type badges
  - period metadata
  - faculty contributors
  - subtype detail section
  - evidence metadata section
  - updated date
  - back link ไป repository
- รองรับ subtype display อย่างน้อย:
  - `teaching`
  - `publication`
  - `research_project`
  - `supervision`
  - `service`
  - `administration`
- handle `detail = null`, `detail.kind = unknown` หรือ field บางตัว missing โดยหน้าไม่ crash
- เพิ่ม loading skeleton/state
- เพิ่ม not found state สำหรับ `404`
- เพิ่ม restricted-safe state โดยใช้ข้อความเดียวกับ not found หรือข้อความกลางที่ไม่เปิดเผยว่ามี record อยู่
- เพิ่ม error state พร้อม retry หรือกลับไปหน้า repository
- แสดง evidence metadata เฉพาะ public-safe
- ไม่แสดง admin/source/audit/storage fields
- รองรับ responsive mobile/desktop
- เพิ่ม tests หรือ manual QA checklist สำหรับ demo records
- verify ว่า V1 `/faculties` และ `/faculties/{id}` ไม่พัง

### ไม่ต้องทำ

- admin-only detail
- mutation buttons
- restricted evidence viewer
- S3 signed URL
- file preview/download
- full print/export report
- login/auth UI

## API Contract

```http
GET /api/v2/work-items/{id}
```

ตัวอย่าง request:

```text
/api/v2/work-items/wi-pub-2024-privacy-edge
```

ตัวอย่าง response shape จาก #68 ที่ UI ต้องรองรับ:

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

## Expected UI Layout

หน้า `/outputs/{id}` ควรเป็น layout เรียบง่าย อ่านง่าย ไม่แน่นเกินไป:

```text
Repository / รายละเอียดผลงาน

[กลับไปผลการค้นหา]

Privacy-Preserving Edge Analytics for Smart Campus Workload Signals
Synthetic publication used for keyword search demo. Keyword: privacy.

[งานวิชาการ/วิจัย] [ผลงานตีพิมพ์] [PUBLIC]

ช่วงเวลา
- ปีการศึกษา: 1/2567
- รอบประเมิน: Evaluation 2567
- วันที่เริ่ม: 2024-10-01
- วันที่สิ้นสุด: 2024-10-01
- อัปเดตล่าสุด: 2026-09-12

อาจารย์ที่เกี่ยวข้อง
1. ผศ.ดร.ประภาพร รัตนธำรง
   บทบาท: CORRESPONDING_AUTHOR, สัดส่วน: 60%
2. ผศ.ดร.กษิดิศ ชาญเชี่ยว
   บทบาท: AUTHOR, สัดส่วน: 40%

รายละเอียดผลงานตีพิมพ์
- ชื่อผลงาน: Privacy-Preserving Edge Analytics...
- วารสาร/แหล่งตีพิมพ์: Synthetic Journal of Cloud Education Systems
- ปีที่ตีพิมพ์: 2024
- DOI: 10.0000/cs361.demo.privacy-edge.2024
- Quartile: Q2

หลักฐาน/แหล่งอ้างอิง
- Synthetic publication landing page
  ประเภท: URL, ชนิด: text/html
  เปิดลิงก์ public ได้ถ้ามี external_url
```

## UI Field Mapping

| UI section | UI label | Response field | Source table / attribute |
|---|---|---|---|
| Header | ชื่อรายการ | `title` | `work_item.title` |
| Header | คำอธิบาย | `description` | `work_item.description` |
| Header badge | หมวดงาน | `category.label_th`, fallback `category.code` | `work_category.label_th`, `work_item.category_code` |
| Header badge | ประเภทงาน | `type.label_th`, fallback `type.code` | `work_type.label_th`, `work_item.work_type_code` |
| Header badge | การมองเห็น | `visibility` | `work_item.visibility` |
| Period | ปีการศึกษา | `academic_periods[].label` | `faculty_work_item` + `academic_period` |
| Period | รอบประเมิน | `evaluation_periods[].label` | `faculty_work_item` + `evaluation_period` |
| Period | วันที่เริ่ม | `start_date` | `work_item.start_date` |
| Period | วันที่สิ้นสุด | `end_date` | `work_item.end_date` |
| Contributors | ชื่ออาจารย์ | `faculty[].display_name` | `faculty.name_th`, fallback `faculty.name_en` |
| Contributors | link profile | `faculty[].slug` | `faculty.public_slug` |
| Contributors | บทบาท | `faculty[].role` | `faculty_work_item.role` |
| Contributors | ลำดับ | `faculty[].contribution_order` | `faculty_work_item.contribution_order` |
| Contributors | สัดส่วน | `faculty[].contribution_percent` | `faculty_work_item.contribution_percent` |
| Subtype detail | ประเภท detail | `detail.kind` | derived จาก subtype table |
| Subtype detail | รายละเอียดเฉพาะงาน | `detail.*` | `publication_detail`, `teaching_detail`, `research_project_detail`, `supervision_detail`, `service_detail`, `administration_detail` |
| Evidence | ชื่อหลักฐาน | `evidence[].label` | `evidence_reference.label` |
| Evidence | ประเภทหลักฐาน | `evidence[].reference_type` | `evidence_reference.reference_type` |
| Evidence | public URL | `evidence[].external_url` | `evidence_reference.external_url` เฉพาะ public-safe |
| Evidence | MIME type | `evidence[].mime_type` | `evidence_reference.mime_type` |
| Footer | อัปเดตล่าสุด | `updated_at` | `work_item.updated_at` |

## Subtype Detail Rendering

Frontend ควรแยก renderer ตาม `detail.kind` เพื่อให้ง่ายต่อการดูแลต่อ:

| `detail.kind` | ใช้กับ table | Field ที่ควรแสดง |
|---|---|---|
| `teaching` | `teaching_detail` | `course_code`, `course_title`, `degree_level`, `teaching_mode`, `section_count`, `student_count`, `credits`, `lecture_hours`, `lab_hours`, `workload_hours`, `reference_label` |
| `publication` | `publication_detail` | `publication_title`, `venue`, `publisher`, `publication_year`, `publication_date`, `doi`, `isbn`, `issn`, `quartile`, `indexing_database`, `publication_kind`, `external_url` |
| `research_project` | `research_project_detail` | `project_title`, `funding_source`, `funding_type`, `budget_amount`, `currency`, `project_status`, `contract_number`, `principal_investigator`, `project_start_date`, `project_end_date` |
| `supervision` | `supervision_detail` | `supervision_type`, `supervision_role`, `degree_level`, `program_name`, `course_code`, `student_count`, `credits`, `student_identifier_policy` |
| `service` | `service_detail` | `service_scope`, `organization_name`, `service_role`, `committee_name`, `order_reference`, `service_date`, `service_end_date` |
| `administration` | `administration_detail` | `position_title`, `organization_unit`, `appointment_type`, `appointed_from`, `appointed_to`, `appointment_reference` |

ถ้า `detail` เป็น `null`, ไม่มี field บางตัว, หรือ `detail.kind` ยังไม่รู้จัก ให้แสดงข้อความสุภาพ เช่น “ยังไม่มีรายละเอียดเพิ่มเติมสำหรับรายการนี้” และยังต้องแสดง core fields ได้

## Evidence Display Rules

หน้า detail แสดง evidence เป็น metadata/reference เท่านั้น:

- แสดง `label`
- แสดง `reference_type`
- แสดง `mime_type` ถ้ามี
- แสดง `visibility` ได้เฉพาะกรณีมีประโยชน์ต่อ QA หรือ UI
- แสดง `external_url` เป็น link ได้เฉพาะ row ที่ API ส่งมาและเป็น public-safe
- ถ้า `evidence` เป็น empty array ให้แสดง empty state สั้นๆ เช่น “ยังไม่มีหลักฐาน public สำหรับรายการนี้”

ห้ามแสดง:

- `s3_key`
- `checksum_sha256`
- private/internal document id
- signed URL
- source/provenance fields
- audit fields
- admin-only notes

## State Handling

### Loading

- แสดง skeleton หรือ loading state ที่โครงหน้าไม่กระโดดแรง
- ไม่แสดง placeholder text ที่ดูเหมือนข้อมูลจริง

### Success

- แสดง header, metadata, contributors, subtype detail และ evidence sections
- optional/null fields ต้องไม่ทำให้หน้า crash

### Not Found

- เมื่อ API ตอบ `404` ให้แสดงหน้าว่าไม่พบรายการ หรือรายการนี้ไม่เปิดเผยต่อสาธารณะ
- มีปุ่ม/link กลับไป `/outputs`

### Restricted/Internal

- Public API ของ #68 จะตอบ `404` สำหรับ `INTERNAL` หรือ `RESTRICTED`
- UI ไม่ควรบอกว่า record นี้มีอยู่จริงแต่ไม่มีสิทธิ์
- ใช้ not found state เดียวกันได้

### Error

- เมื่อ network/API error ให้แสดง error state พร้อม retry
- ถ้ามี API base URL ผิด ควรเห็นข้อความที่ช่วย QA ตรวจ env ได้โดยไม่เปิด secret

## Suggested Frontend Files

ปรับชื่อไฟล์ตาม pattern จริงของ repo ได้ แต่ควรแยก responsibility ประมาณนี้:

```text
frontend/app/outputs/[id]/page.tsx
frontend/app/outputs/[id]/loading.tsx
frontend/app/outputs/[id]/error.tsx
frontend/app/outputs/[id]/not-found.tsx
frontend/components/outputs/work-item-detail-header.tsx
frontend/components/outputs/work-item-detail-sections.tsx
frontend/components/outputs/work-item-faculty-contributors.tsx
frontend/components/outputs/work-item-evidence-section.tsx
frontend/lib/v2/work-item-detail-client.ts
```

ถ้า frontend ใช้ Pages Router หรือ structure อื่น ให้ยึด pattern repo เป็นหลัก แต่ route public ต้องยังเป็น `/outputs/{id}`

## URL / Navigation Behavior

- กด item จาก #73 แล้วไป `/outputs/{id}`
- back link ควรกลับไป `/outputs`
- ถ้าทำได้ ให้ preserve query เดิม เช่นกลับไป `/outputs?q=privacy&category=RESEARCH&page=1`
- direct open `/outputs/wi-pub-2024-privacy-edge` ต้องทำงานได้ แม้ไม่มี previous query
- ไม่ควร require login สำหรับ public detail

## Demo Records สำหรับ QA

ใช้ demo ids จาก #68 เป็น baseline:

| Work item id | Expected UI result |
|---|---|
| `wi-pub-2024-privacy-edge` | แสดง public publication detail, faculty 2 คน, evidence `ev-pub-2024-demo-url` |
| `wi-pub-2019-multi-container` | แสดง public publication detail และ evidence DOI |
| `wi-pub-2025-hci-agent` | แสดง publication detail ได้ แม้ไม่มี public evidence |
| `wi-service-2568-speaker` | แสดง service detail |
| `wi-teach-2567-2-cs333` | แสดง not found/restricted-safe state เพราะเป็น `INTERNAL` ใน public route |
| `wi-supervision-2567-phd-thesis` | แสดง not found/restricted-safe state เพราะเป็น `RESTRICTED` ใน public route |
| `not-found-id` | แสดง not found state |

## QA / Smoke Test Checklist

หลัง deploy หรือ run frontend ที่ชี้ไป AWS endpoint จริง ให้เก็บ evidence อย่างน้อย:

- เปิด `/outputs/wi-pub-2024-privacy-edge` แล้วเห็น title จริงจาก API
- หน้า `wi-pub-2024-privacy-edge` แสดง category/type label, academic period, evaluation period
- หน้า `wi-pub-2024-privacy-edge` แสดง faculty 2 คน เรียงตาม `contribution_order`
- หน้า `wi-pub-2024-privacy-edge` แสดง `detail.kind = publication` ในรูปแบบ UI ที่อ่านได้
- หน้า `wi-pub-2024-privacy-edge` แสดง evidence `Synthetic publication landing page`
- เปิด `/outputs/wi-service-2568-speaker` แล้วเห็น service detail ไม่ใช่ publication layout
- เปิด `/outputs/wi-teach-2567-2-cs333` แล้วได้ not found/restricted-safe state
- เปิด `/outputs/wi-supervision-2567-phd-thesis` แล้วได้ not found/restricted-safe state
- เปิด `/outputs/not-found-id` แล้วได้ not found state
- ปิด mock/fixture แล้วหน้ายังโหลดจาก AWS endpoint ได้
- response/public UI ไม่มี `s3_key`, `checksum_sha256`, `source_score`, `source_weight`, `source_record_id`
- mobile viewport ไม่มี horizontal scroll หรือข้อมูลล้น
- V1 `/faculties` และ `/faculties/{id}` ยังเปิดได้

## Acceptance Criteria

- [ ] `/outputs/{id}` เปิดได้
- [ ] หน้า detail โหลดข้อมูลจาก deployed Detail API จริงจาก AWS
- [ ] ใช้ config/API base URL เดียวกับ #72/#73
- [ ] แสดง title/description/category/type/visibility ได้
- [ ] แสดง academic periods และ evaluation periods ได้
- [ ] แสดง faculty contributors พร้อม role/order/percent ได้
- [ ] แสดง subtype detail ตาม `detail.kind` ได้
- [ ] รองรับ `teaching`, `publication`, `research_project`, `supervision`, `service`, `administration`
- [ ] evidence metadata public-safe แสดงได้
- [ ] ไม่มี admin-only/source/audit/storage fields ใน public UI
- [ ] ไม่แสดง `s3_key`, `checksum_sha256` หรือ signed URL
- [ ] loading/error/not found states ครบ
- [ ] internal/restricted ids แสดง public-safe not found state
- [ ] link กลับ repository page ได้
- [ ] responsive บน mobile/desktop
- [ ] missing optional fields ไม่ทำให้หน้า crash
- [ ] มี QA evidence สำหรับ public detail, no evidence, service subtype, not found และ restricted/internal case
- [ ] V1 routes ไม่พัง

## Review Checklist

Frontend:

- [ ] subtype rendering แยกเป็น component ที่ดูแลต่อได้
- [ ] data fetching ไม่ผูกกับ fixture-specific field
- [ ] optional/null field ถูก handle สุภาพ
- [ ] date/number formatting consistent
- [ ] contributor sorting ใช้ `contribution_order`
- [ ] link faculty ใช้ `slug` ถ้ามี
- [ ] error/not-found handling อ่านง่าย

UX:

- [ ] detail hierarchy อ่านง่าย
- [ ] header ไม่ใหญ่เกินจนดัน content สำคัญออกหมด
- [ ] metadata scan ได้เร็ว
- [ ] evidence section ไม่ทำให้ผู้ใช้คิดว่าดาวน์โหลด restricted file ได้
- [ ] mobile ไม่ล้นจอ
- [ ] back navigation เข้าใจง่าย

Security/Public Safety:

- [ ] public UI ไม่แสดง secret, S3 key, checksum, source, audit หรือ admin fields
- [ ] restricted/internal case ไม่เปิดเผยว่า record มีอยู่จริง
- [ ] frontend ไม่เห็น AWS secret หรือ DB secret
- [ ] ไม่ hardcode token หรือ credential ใดๆ

QA:

- [ ] ทดสอบ demo records ครบหลาย category ที่มีในฐานข้อมูล
- [ ] ทดสอบ not found และ restricted item
- [ ] ทดสอบ missing/empty evidence
- [ ] smoke test บน deployed frontend/API Gateway ไม่ใช่ mock เท่านั้น
- [ ] แนบ screenshot หรือ comment หลักฐานใน GitHub issue

## Dependencies

Blocked by:

- #68 Build Work Item Detail API
- #73 Build Repository Result List & Pagination UI

Blocks:

- #75 Integrate Repository UI with Real API

Related:

- #64 Build Master Data API
- #66 Build Work Item List/Search/Filter API
- #67 Build Faculty Work Items API

## Suggested Labels

- `v2`
- `frontend`
- `ui`
- `detail`
- `repository`
- `ready-for-agent`

## Suggested Owner

Frontend Developer

Reviewers:

- Tech Lead
- Backend Developer
- QA / Integration

## Estimate

1 day

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อผู้ใช้สามารถเปิดหน้า detail ของ work item ผ่าน `/outputs/{id}` โดยโหลดจาก deployed AWS Detail API จริง เห็นข้อมูลกลาง, category/type/period, faculty contributors, subtype detail และ evidence metadata แบบ public-safe ตาม contract ของ #68 พร้อม loading/error/not-found states, responsive UI, QA evidence และยืนยันว่า V1 routes ยังไม่พัง
