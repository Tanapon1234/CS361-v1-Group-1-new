# [V2] Build Repository Result List & Pagination UI #73

## สรุป

สร้างส่วนแสดงผลรายการ work items และ pagination บนหน้า `/outputs` ตาม response shape ของ `GET /api/v2/work-items` จาก #66 ให้ผู้ใช้ scan รายการผลงาน/ภาระงานได้ง่าย กดเข้า `/outputs/{id}` ได้ และเปลี่ยนหน้าโดยยังรักษา filter/query state จาก #72

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #59 แต่ GitHub issue จริงใช้ #73

## Production AWS Requirement

result list ต้องอ่านข้อมูลจาก deployed Work Item List API จาก #66 จริง ไม่ใช่ fixture/mock:

```text
Frontend /outputs
→ deployed API Gateway GET /api/v2/work-items
→ Lambda query handler
→ RDS Data API
→ Aurora PostgreSQL Serverless v2
```

ต้องใช้ frontend API base URL/config เดียวกับ #72 เช่น:

```text
NEXT_PUBLIC_V2_API_BASE_URL=https://n89gqgnqw2.execute-api.ap-southeast-1.amazonaws.com
```

แล้วเรียก:

```text
GET ${NEXT_PUBLIC_V2_API_BASE_URL}/api/v2/work-items
```

fixture/mock ใช้ได้เฉพาะ component test หรือ local fallback เท่านั้น ไม่ถือว่าเพียงพอสำหรับปิดการ์ดนี้

## Background

หลัง #72 สร้าง shell/filter UI แล้ว หน้า `/outputs` ยังต้องมีส่วนแสดงผลรายการจริงที่อ่านจาก Work Item List API จาก #66

หน้า result list นี้เป็นส่วนที่ผู้ใช้จะใช้ตัดสินใจว่า:

- รายการนี้คือผลงานหรือภาระงานอะไร
- อยู่ในหมวด/ประเภทไหน
- เกี่ยวข้องกับอาจารย์คนใด
- อยู่ในปีการศึกษา/รอบประเมินใด
- ควรกดเข้าไปดูรายละเอียดหรือไม่

การ์ดนี้จึงเป็นสะพานระหว่าง:

- #72: filter shell + URL query state
- #66: backend list/search/filter API
- #74: detail page `/outputs/{id}`
- #75: integration end-to-end ของ repository UI กับ real API

## ความเกี่ยวข้องกับโจทย์

โจทย์ V2 ต้องรองรับการค้นหา กรอง และเรียกดูผลงาน/ภาระงานตามเงื่อนไข การ์ด #73 คือส่วนที่ทำให้ผู้ใช้ “เห็นผลลัพธ์จริง” จาก repository หลังจากเลือก filter แล้ว

ถ้าไม่มีการ์ดนี้ หน้า `/outputs` จะมีแค่ filter แต่ยังไม่ตอบโจทย์การ browse repository เพราะผู้ใช้ยังไม่เห็นรายการผลงาน/ภาระงานที่ค้นหาได้

## เป้าหมาย

สร้าง UI list/pagination ที่:

- render response shape จาก #66 ได้ตรง contract
- map filter URL query จาก #72 ไป API query จริง
- รองรับ loading, empty, error และ pagination states
- แสดงข้อมูลพอให้ผู้ใช้ตัดสินใจกดเข้า detail
- link item ไป `/outputs/{id}` สำหรับ #74
- รักษา filter/query state ระหว่างเปลี่ยนหน้า
- ไม่เปิด internal/restricted/admin-only fields ใน public UI
- ใช้งานได้บน mobile/desktop

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- implement detail page `/outputs/{id}`
- render subtype detail แบบเต็ม เช่น publication detail, teaching detail
- ทำ admin list
- ทำ export/download
- ทำ saved search
- ทำ compare view
- ทำ chart/dashboard
- ทำ write/mutation/admin action
- แก้ backend Work Item List API
- แก้ Master Data API

## User Stories

1. As a public user, I want to see work item results on `/outputs`, so that I can browse faculty outputs and workload records.
2. As a public user, I want each result to show title, category, type, period, faculty, and updated date, so that I can quickly understand the record.
3. As a public user, I want to click a result, so that I can open the detail page for that work item.
4. As a public user, I want pagination controls, so that I can move through many results without losing my filters.
5. As a public user, I want a clear empty state, so that I know when my filters returned no results and can clear or change filters.
6. As a public user, I want loading skeletons, so that the page feels stable while the AWS endpoint is loading.
7. As a public user, I want a clear error state, so that I know when the result API failed and can retry.
8. As a mobile user, I want result cards and pagination to fit the screen, so that I can browse without horizontal scrolling.
9. As a frontend developer for #74, I want every item link to use a stable `id`, so that the detail route can be implemented consistently.
10. As a QA reviewer, I want evidence that the list uses deployed AWS API, so that we know this is production-connected and not fixture-only.

## Scope

### ต้องทำ

- สร้าง result list component สำหรับ work item summary
- ต่อ data fetching กับ deployed `GET /api/v2/work-items` จาก #66
- ใช้ `NEXT_PUBLIC_V2_API_BASE_URL` หรือ config equivalent จาก #72
- map URL query จาก #72 ไป API query จริง:
  - `q`
  - `academic_period_id`
  - `evaluation_period_id`
  - `category`
  - `type`
  - `faculty_id`
  - `page`
  - `page_size`
- แสดงข้อมูลบน item/card:
  - title
  - description แบบย่อ
  - category label/code
  - type label/code
  - academic period
  - evaluation period ถ้ามี
  - faculty contributors แบบย่อ
  - visibility badge เฉพาะ `PUBLIC` ถ้ามีประโยชน์
  - updated date
- link item ไป `/outputs/{id}`
- เพิ่ม pagination controls:
  - previous/next
  - current page
  - total pages หรือ total result summary
  - page size ถ้า UX เหมาะสม
- pagination ต้อง update URL query โดยรักษา filter เดิมไว้
- เพิ่ม empty state เมื่อไม่มีผลลัพธ์
- เพิ่ม loading skeleton/state
- เพิ่ม error state พร้อม retry หรือ clear filter ตาม UX ที่เหมาะสม
- รองรับ responsive mobile/desktop
- เพิ่ม tests หรือ manual QA checklist ตาม pattern repo
- verify ว่า V1 `/faculties` และ `/faculties/{id}` ไม่พัง

### ไม่ต้องทำ

- admin-only fields
- work item detail content
- subtype detail full rendering
- evidence rendering
- editing/deleting
- auth
- export/download

## API Contract

```http
GET /api/v2/work-items
```

ตัวอย่าง query จากหน้า `/outputs`:

```text
/api/v2/work-items?q=privacy&academic_period_id=ap-2567-1&category=RESEARCH&type=PUBLICATION&faculty_id=fac_prapaporn-rattanatamrong&page=1&page_size=20
```

ตัวอย่าง response shape ที่ต้องรองรับจาก #66:

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

Error shape ที่ควรรองรับ:

```json
{
  "error": {
    "code": "INVALID_QUERY",
    "message": "type must belong to category",
    "details": {
      "field": "type"
    }
  }
}
```

## URL Query Mapping

ต้องใช้ query contract เดียวกับ #72:

| `/outputs` URL key | API query key | Example | Notes |
|---|---|---|---|
| `q` | `q` | `privacy` | keyword search |
| `academic_period_id` | `academic_period_id` | `ap-2567-1` | relation period |
| `evaluation_period_id` | `evaluation_period_id` | `eval-2567-full-year` | optional |
| `category` | `category` | `RESEARCH` | work category code |
| `type` | `type` | `PUBLICATION` | work type code |
| `faculty_id` | `faculty_id` | `fac_prapaporn-rattanatamrong` | faculty id |
| `page` | `page` | `2` | pagination |
| `page_size` | `page_size` | `20` | pagination size |

Rules:

- เปลี่ยน filter ใด ๆ จาก #72 ควร reset `page` กลับเป็น `1`
- เปลี่ยนหน้า pagination ต้อง preserve filter query เดิมทั้งหมด
- ถ้า `page` น้อยกว่า 1 ให้ fallback เป็น 1 หรือแสดง error ตาม convention ที่ทีมเลือก
- ถ้า `page_size` ไม่ส่ง ให้ใช้ default ของ API หรือ default UI = 20
- ไม่ควรส่ง empty/default values ไปใน query
- invalid query จาก API ต้องแสดง error state ที่เข้าใจง่าย ไม่ crash

## UI Rendering Contract

### Result Card / Row Fields

แต่ละ item ควรแสดง:

| UI element | Source field | Display rule |
|---|---|---|
| title | `item.title` | แสดงเป็น heading ของ card/row และเป็น link |
| description | `item.description` | truncate 1-2 บรรทัด ถ้าไม่มีให้ซ่อน |
| category badge | `item.category.label_th` + `item.category.code` | ใช้ label ไทยเป็นหลัก code เป็น secondary หรือ tooltip |
| type badge | `item.type.label_th` + `item.type.code` | อยู่ใกล้ category |
| academic period | `item.academic_period.label` | เช่น `1/2567` |
| evaluation period | `item.evaluation_period.label` | optional ถ้ามี |
| faculty contributors | `item.faculty[]` | แสดง 1-2 คนแรก แล้วบอก `+N` ถ้ามีมากกว่า |
| faculty role | `faculty[].role` | แสดงแบบ compact เช่น `AUTHOR` |
| visibility | `item.visibility` | public endpoint ควรเป็น `PUBLIC`; แสดง badge ได้ถ้าไม่รก |
| updated date | `item.updated_at` | แสดงเป็นวันที่อ่านง่าย เช่น `อัปเดต 12 ก.ย. 2026` |
| detail link | `item.id` | link ไป `/outputs/{id}` |

### Suggested Visual Layout

Desktop:

```text
Result summary: พบ 4 รายการ

[Card]
  Badge: งานวิชาการ/วิจัย • ผลงานตีพิมพ์
  Title
  Description
  Period: 1/2567 • Evaluation 2567
  Faculty: ผศ.ดร.ประภาพร รัตนธำรง (CORRESPONDING_AUTHOR), ผศ.ดร.กษิดิศ ชาญเชี่ยว (AUTHOR)
  Updated date
  Link: ดูรายละเอียด

Pagination
```

Mobile:

```text
Card stack
Title
Badges wrap
Period
Faculty summary
Updated date
```

ไม่ควรใช้ table เป็น layout หลักบน mobile ถ้า table ทำให้ล้นจอ ใช้ card/list ที่ scan ง่ายกว่า

## Pagination Contract

API response:

```json
{
  "page": 1,
  "page_size": 20,
  "total": 4
}
```

Derived UI values:

```text
total_pages = ceil(total / page_size)
has_previous = page > 1
has_next = page < total_pages
```

Controls:

- Previous
- Next
- current page indicator เช่น `หน้า 1 จาก 3`
- total summary เช่น `พบ 42 รายการ`
- optional page size selector ถ้าไม่ทำให้ scope บาน

Rules:

- previous disabled เมื่อ `page = 1`
- next disabled เมื่อ `page >= total_pages`
- clicking pagination updates URL query only, preserving filters
- pagination area must remain stable when loading
- empty result should not show confusing page controls
- if current `page` exceeds `total_pages` after filter change, reset to page 1 or request page 1 again

## Page States

### Loading State

ใช้เมื่อกำลัง fetch `GET /api/v2/work-items`:

- แสดง skeleton cards ประมาณ 3-5 ใบ
- รักษาความสูง result area เพื่อลด layout shift
- filter controls จาก #72 ยังอยู่
- pagination placeholder อาจแสดงเป็น disabled

### Success State

แสดง:

- result summary เช่น `พบ 4 รายการ`
- cards/rows ของ items
- pagination controls ถ้า `total > page_size`
- applied filter summary จาก #72 ถ้ามี

### Empty State

ใช้เมื่อ API return:

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 0
}
```

ข้อความแนะนำ:

```text
ไม่พบรายการที่ตรงกับตัวกรองนี้
ลองล้างตัวกรองหรือเปลี่ยนคำค้นหา
```

ควรมี action:

- ล้างตัวกรอง
- กลับไป `/outputs`

### Error State

ใช้เมื่อ API request fail หรือ API return error shape:

- แสดงข้อความว่าโหลดรายการไม่ได้
- แสดง error code แบบ user-friendly ถ้ามี เช่น `INVALID_QUERY`
- มีปุ่ม retry
- มี action clear filters ถ้า error มาจาก query/filter
- ห้ามแสดง stack trace, AWS secret, ARN, DB detail

### Invalid Query State

ถ้า URL query มีค่าที่ API reject เช่น:

```text
/outputs?category=TEACHING&type=PUBLICATION
```

UI ควร:

- แสดง error state หรือ clearable warning
- เสนอปุ่มล้างตัวกรอง
- ไม่ crash ทั้งหน้า

## Public-Safe Display Rules

ต้องแสดงเฉพาะข้อมูล public-safe จาก #66:

แสดงได้:

- `id`
- `title`
- `description`
- category/type labels
- academic/evaluation period labels
- public faculty names/slugs
- public-safe role/contribution fields
- `visibility = PUBLIC`
- `start_date`, `end_date`, `updated_at`

ห้ามแสดง:

- `work_item.source_score`
- `work_item.source_weight`
- `work_item.source_section_code`
- `work_item.import_batch_id`
- `work_item.source_record_id`
- `faculty_work_item.contribution_note`
- `faculty_work_item.quantity`
- `faculty_work_item.credits`
- `faculty_work_item.hours`
- `audit_event`
- `app_user`, `app_role`, auth data
- evidence private S3 key/checksum
- INTERNAL/RESTRICTED records

หมายเหตุ: public endpoint จาก #66 ควร enforce visibility ที่ backend แล้ว แต่ frontend ต้องไม่เพิ่ม UI ที่คาดหวัง admin-only fields

## Demo Data Expectations

ถ้า #66 ใช้ demo dataset จาก `data/v2/fixtures/` ตาม contract ควรเห็น public result baseline:

| Work item id | Expected display title | Category | Type |
|---|---|---|---|
| `wi-pub-2019-multi-container` | `Multi-Container Application Migration with Load Balanced and Adaptive Parallel TCP` | `RESEARCH` | `PUBLICATION` |
| `wi-pub-2024-privacy-edge` | `Privacy-Preserving Edge Analytics for Smart Campus Workload Signals` | `RESEARCH` | `PUBLICATION` |
| `wi-pub-2025-hci-agent` | `Adaptive Interface Agents for Computing Education` | `RESEARCH` | `PUBLICATION` |
| `wi-service-2568-speaker` | `Invited Speaker: Responsible AI and Privacy in Education` | `ACADEMIC_SERVICE` | `INVITED_SPEAKER` |

Expected behavior:

- `/outputs` แสดง `total = 4` ถ้าใช้ demo data public baseline
- `/outputs?category=RESEARCH` แสดง 3 รายการ
- `/outputs?type=PUBLICATION` แสดง 3 รายการ
- `/outputs?q=privacy` แสดงรายการ public ที่ match keyword และไม่แสดง internal/restricted
- `/outputs?category=TEACHING` แสดง empty state ถ้า teaching demo data ยังเป็น `INTERNAL`

## Suggested Components / Files

ชื่อไฟล์จริงปรับได้ตาม frontend pattern แต่ควรประมาณนี้:

```text
frontend/components/outputs/work-item-result-list.tsx
frontend/components/outputs/work-item-result-card.tsx
frontend/components/outputs/work-item-pagination.tsx
frontend/components/outputs/work-item-result-states.tsx
frontend/lib/v2/work-items-client.ts
frontend/lib/v2/work-item-query-state.ts หรือ reuse output-query-state จาก #72
```

ถ้า #72 สร้าง `frontend/app/outputs/page.tsx` แล้ว ให้ #73 เติม result area เข้าไปโดยไม่ rewrite filter shell ทั้งหมด

ถ้า #72 ยังไม่ได้ implement จริง ให้ #73 ต้องทำงานบน branch เดียวกันโดยเพิ่ม result area ตาม spec #72 แต่ไม่ลด scope ของ #72

## Data Fetching Notes

Implementation เลือกได้ตาม frontend pattern:

- Server Component fetch โดยอ่าน `searchParams` แล้วเรียก API
- Client Component fetch ถ้าต้องการ retry/loading state แบบ interactive
- Hybrid โดย page server render shell และ result list เป็น client component

Rules:

- production fetch ต้องไป deployed API Gateway URL
- local tests mock network หรือใช้ fixture ได้
- component mapping ต้องไม่ผูกกับ fixture-specific fields
- response validation ขั้นต่ำควรตรวจ `items`, `page`, `page_size`, `total`
- ถ้า API return unexpected shape ให้แสดง error state

## QA Evidence

ต้องมี evidence สำหรับปิดการ์ด:

- screenshot หรือ note ว่า `/outputs` แสดง result list ได้
- Network tab หรือ log ว่าเรียก deployed `GET /api/v2/work-items` จริง
- success state: default list แสดงรายการได้
- filter state: URL query ส่งไป API จริง
- empty state: เช่น `category=TEACHING` หรือ query ที่ไม่มีผลลัพธ์
- error state: ทดสอบ API failure หรือ invalid query
- pagination: page/next/previous update URL และ preserve filters
- link: คลิก item แล้วไป `/outputs/{id}`
- responsive: mobile/desktop ไม่ล้น
- public-safe: ไม่มี internal/restricted/admin-only fields

Example manual QA URLs:

```text
/outputs
/outputs?category=RESEARCH
/outputs?type=PUBLICATION
/outputs?q=privacy
/outputs?faculty_id=fac_prapaporn-rattanatamrong&type=PUBLICATION
/outputs?category=TEACHING
/outputs?page=2&page_size=2
```

## Acceptance Criteria

- [ ] result list แสดง work item summary ได้จาก response shape ของ #66
- [ ] result cards/rows แสดง title, description, category/type, period, faculty, updated date
- [ ] item link ไป `/outputs/{id}` ด้วย `item.id`
- [ ] pagination update URL/query state ได้
- [ ] pagination preserve filters ระหว่างเปลี่ยนหน้า
- [ ] loading state ทำงานและ layout ไม่ shift แรง
- [ ] empty state ทำงานพร้อม action clear/change filters
- [ ] error state ทำงานพร้อม retry หรือ clear filters
- [ ] responsive บน mobile/desktop
- [ ] ไม่มี internal/restricted/admin-only field ใน public UI
- [ ] result list ใช้ deployed Work Item List API จริง
- [ ] pagination/filter ส่ง query ไป AWS endpoint จริง
- [ ] invalid query จาก API ไม่ทำให้หน้า crash
- [ ] V1 `/faculties` และ `/faculties/{id}` ไม่พัง
- [ ] มี QA evidence สำหรับ success, empty, API error และ pagination

## Review Checklist

Frontend:

- [ ] data mapping ไม่ผูกกับ fixture-specific field
- [ ] response shape validation มีพอจับ API contract mismatch
- [ ] layout ไม่ shift แรงเมื่อ loading/result เปลี่ยน
- [ ] pagination คิด `total_pages` ถูกต้อง
- [ ] URL query update ไม่ลบ filter ที่ผู้ใช้เลือกไว้
- [ ] item link ใช้ `id` ที่ stable
- [ ] component ต่อกับ shell จาก #72 โดยไม่ duplicate filter logic

UX:

- [ ] ข้อมูลที่แสดง scan ได้ง่าย
- [ ] badges ไม่รกเกินไปบน mobile
- [ ] faculty contributors แสดงแบบย่อแล้วเข้าใจ
- [ ] empty state บอกผู้ใช้ว่าควร clear/filter ใหม่อย่างไร
- [ ] error state ไม่ technical เกินไป

QA:

- [ ] ทดสอบ list มีหลายหน้า
- [ ] ทดสอบ no result
- [ ] ทดสอบ error state
- [ ] ทดสอบ invalid query
- [ ] ทดสอบ pagination + filters ร่วมกัน
- [ ] smoke test บน deployed frontend/API Gateway ไม่ใช่ mock เท่านั้น

Security / Data:

- [ ] UI ไม่แสดง source/provenance/admin fields
- [ ] UI ไม่แสดง evidence private fields
- [ ] UI ไม่พยายาม query `visibility=INTERNAL` หรือ `RESTRICTED`
- [ ] error state ไม่แสดง secret, ARN, stack trace หรือ raw SQL error

## Dependencies

Blocked by:

- #66 Build Work Item List/Search/Filter API
- #72 Build Repository Page Shell & Filter UI

Blocks:

- #74 Build Work Item Detail UI
- #75 Integrate Repository UI with Real API

Related:

- #64 Build Master Data API
- #67 Build Faculty Work Items API
- #68 Build Work Item Detail API
- #81 Final Integration / Deploy / Demo Docs

## Suggested Labels

- `v2`
- `frontend`
- `ui`
- `repository`
- `ready-for-agent`

## Suggested Owner

Frontend Developer

Reviewers:

- Tech Lead
- Backend Developer
- QA / Integration

## Estimate

0.5-1 day

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อหน้า `/outputs` มี result list และ pagination ที่ใช้ deployed Work Item List API จริงจาก AWS, รองรับ contract ของ #66, map query/filter จาก #72 ได้ถูกต้อง, link ไป `/outputs/{id}` ได้, ไม่เปิดข้อมูล internal/admin-only และมี QA evidence สำหรับ success/empty/error/pagination บน deployed endpoint จริง
