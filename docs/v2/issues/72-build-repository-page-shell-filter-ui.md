# [V2] Build Repository Page Shell & Filter UI #72

## สรุป

สร้างหน้า `/outputs` สำหรับ V2 Faculty Output Repository ให้เป็น public entry point สำหรับค้นหา/กรองผลงานและภาระงานอาจารย์ พร้อม layout, filter controls, URL query state, loading/empty/error states และพื้นที่ placeholder สำหรับ result list/pagination ที่การ์ด #73 จะมาต่อ

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #58 แต่ GitHub issue จริงใช้ #72

## Production AWS Requirement

หน้า `/outputs` ต้องใช้ Master Data API จาก #64 ที่ deploy บน AWS จริงสำหรับ filter options:

```text
Frontend /outputs
→ deployed API Gateway URL
→ Lambda query handler
→ RDS Data API
→ Aurora PostgreSQL Serverless v2
```

fixture/mock ใช้ได้เฉพาะ component test หรือ local fallback เท่านั้น ไม่ถือว่าเพียงพอสำหรับปิดการ์ดนี้

Production endpoint ที่ #64 document ไว้:

```text
https://n89gqgnqw2.execute-api.ap-southeast-1.amazonaws.com
```

ต้องตั้งผ่าน frontend env/config เช่น:

```text
NEXT_PUBLIC_V2_API_BASE_URL=https://n89gqgnqw2.execute-api.ap-southeast-1.amazonaws.com
```

ห้าม hardcode endpoint ลง component ตรง ๆ และห้ามใช้ AWS secret/ARN ใน frontend

## Background

V1 มีหน้า `/faculties` เป็น public faculty directory เป็นหลัก แต่โจทย์ V2 ต้องมี repository สำหรับ “ผลงานและภาระงานอาจารย์” ที่รองรับหลายปีการศึกษา ค้นหา กรอง และเรียกดูตามเงื่อนไขได้

หน้า `/outputs` จึงเป็นหน้าทางเข้าของ public V2 repository:

- ผู้ใช้ทั่วไปใช้ค้นหาผลงาน/ภาระงานที่เปิดเผยได้
- ทีม frontend ใช้ต่อกับ result list จาก #73
- ทีม backend ใช้ยืนยันว่า Master Data API จาก #64 ใช้กับ UI จริงได้
- V1 routes เดิม เช่น `/faculties` ต้องไม่พัง

การ์ดนี้ยังไม่ต้อง render result cards จริงแบบ production เต็ม เพราะหน้าที่นั้นอยู่ในการ์ด #73 และการผูก real work item API อยู่ในการ์ด #75

## ความเกี่ยวข้องกับโจทย์

โจทย์ต้องการระบบที่จัดเก็บและเรียกใช้ข้อมูล:

- ข้อมูลอาจารย์
- การสอน
- งานวิจัย
- งานบริการวิชาการ
- การดูแลนักศึกษา
- ผลงานหรือภาระงานที่เกี่ยวข้อง
- รองรับหลายปีการศึกษา
- ค้นหา/กรอง/เรียกดูตามเงื่อนไขได้

การ์ด #72 ตอบโจทย์ฝั่ง UI โดยสร้างหน้าที่ผู้ใช้จะเริ่ม “ค้นหาและกรอง” repository ได้ ถึงแม้ผลลัพธ์จริงจะมาต่อในการ์ดถัดไป

## เป้าหมาย

สร้าง UI shell ที่:

- เปิด route `/outputs`
- อธิบายบริบทชัดเจนว่านี่คือ “คลังผลงานและภาระงานอาจารย์”
- มี filter controls สำหรับ keyword, academic period, evaluation period, category, type, faculty
- โหลด filter options จาก deployed Master Data API จริง
- sync filter state กับ URL query เพื่อ share/reload ได้
- มี responsive layout สำหรับ desktop/mobile
- เตรียมพื้นที่ result list/pagination ให้ #73 ใช้ต่อ
- มี loading/empty/error placeholder states ที่ไม่ทำให้ layout กระโดดแรง
- เพิ่ม navigation entry อย่างไม่ทำให้ V1 `/faculties` เสีย

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- render result cards/table แบบ final
- integrate `GET /api/v2/work-items` เต็มรูปแบบ
- ทำ pagination behavior จริง
- ทำ work item detail page
- ทำ admin UI
- ทำ auth
- ทำ export/report
- ทำ saved search
- ทำ analytics/dashboard
- แก้ backend Master Data API

## User Stories

1. As a public user, I want to open `/outputs`, so that I can understand that this page is the V2 repository for faculty outputs and workload.
2. As a public user, I want to search by keyword, so that I can narrow down work items by title or related text once results are connected.
3. As a public user, I want to filter by academic period, so that I can browse outputs/workload for a specific semester or year.
4. As a public user, I want to filter by evaluation period, so that I can match records to the workload evaluation cycle.
5. As a public user, I want to filter by category and type, so that I can separate teaching, research, service, supervision, administration, and related work.
6. As a public user, I want to filter by faculty member, so that I can browse outputs related to one instructor.
7. As a user sharing a link, I want filter state in the URL, so that another person opening the link sees the same filter selections.
8. As a mobile user, I want filters to be usable without horizontal overflow, so that the repository page works on small screens.
9. As a frontend developer for #73, I want a stable result placeholder area, so that I can add cards/table/pagination without rebuilding the page shell.
10. As a QA reviewer, I want loading/error states for master data, so that AWS/API failures are visible and testable.

## Scope

### ต้องทำ

- เพิ่ม route/page `/outputs`
- เพิ่ม page metadata/title ที่เหมาะสม เช่น “ผลงานและภาระงานอาจารย์”
- เพิ่ม filter UI:
  - keyword search
  - academic period
  - evaluation period
  - work category
  - work type
  - faculty
  - reset filters
- ใช้ deployed Master Data API จาก #64 สำหรับ options:
  - `GET /api/v2/academic-periods`
  - `GET /api/v2/evaluation-periods`
  - `GET /api/v2/work-categories`
  - `GET /api/v2/work-types`
  - `GET /api/v2/faculties`
- เพิ่ม frontend env/config สำหรับ API Gateway base URL ตามที่ deploy จริง
- สร้าง client/helper สำหรับ fetch master data หรือใช้ helper ที่มีอยู่แล้วต่อยอด โดยห้าม hardcode options ใน component
- handle loading/error จาก AWS endpoint จริง
- เมื่อเลือก filter ให้ update URL query อย่าง predictable
- เมื่อ reload URL ที่มี query ให้ restore filter state เดิม
- เลือก category แล้ว type options ต้องถูกกรองให้สัมพันธ์กับ category
- เพิ่ม placeholder result region ที่ #73 เติม result list/pagination ได้
- เพิ่ม loading/empty/error placeholder states
- เพิ่ม navigation entry ถ้าเข้ากับ design ของ frontend
- เพิ่ม basic tests หรือ manual QA checklist ตาม pattern repo
- verify ว่า V1 `/faculties` และ `/faculties/{id}` ยังไม่พัง

### ไม่ต้องทำ

- result cards/table แบบ final
- pagination behavior จริง
- call `GET /api/v2/work-items` จริง
- detail route
- admin route
- Cognito/auth
- mutation/write action
- S3/evidence rendering

## Suggested UI Structure

หน้า `/outputs` ควรมีโครงสร้างประมาณนี้:

```text
Header / existing site nav
└─ Repository page
   ├─ Page heading
   │  ├─ title: ผลงานและภาระงานอาจารย์
   │  └─ short description: ค้นหาและกรองผลงาน/ภาระงานตามปี หมวดงาน ประเภทงาน และอาจารย์
   ├─ Filter bar / filter panel
   │  ├─ Keyword search
   │  ├─ Academic period select
   │  ├─ Evaluation period select
   │  ├─ Category select
   │  ├─ Work type select
   │  ├─ Faculty select
   │  └─ Reset filters
   ├─ Applied filter summary
   ├─ Result placeholder
   │  ├─ loading state
   │  ├─ empty state
   │  ├─ error state
   │  └─ reserved area for #73 result list/pagination
   └─ Footer / existing site footer
```

ไม่ควรทำเป็น landing page หรือ hero ใหญ่เกินไป หน้านี้เป็น repository/tool page ควรเน้น scan ง่าย ใช้งานซ้ำได้ และไม่แน่นเกินบน mobile

## Filter Controls

### Keyword Search

UI label:

```text
ค้นหาผลงานหรือภาระงาน
```

URL query:

```text
q=<keyword>
```

Rules:

- trim whitespace
- ถ้า empty ให้ลบ `q` ออกจาก URL
- ยังไม่ต้อง call work item API ในการ์ดนี้ แต่ต้องเก็บ state ให้ #75 ใช้ต่อได้
- อาจ debounce เฉพาะตอน update query ถ้า implementation ใช้ client component

### Academic Period

UI label:

```text
ปี/ภาคการศึกษา
```

Source:

```text
GET /api/v2/academic-periods
```

Option fields:

- `id`
- `label`
- `academic_year`
- `semester`

URL query:

```text
academic_period_id=ap-2567-2
```

Display example:

```text
2/2567
```

### Evaluation Period

UI label:

```text
รอบประเมิน
```

Source:

```text
GET /api/v2/evaluation-periods
```

Option fields:

- `id`
- `code`
- `label`
- `academic_period_id`
- `start_date`
- `end_date`

URL query:

```text
evaluation_period_id=eval-2567-full-year
```

UX rule:

- ถ้าเลือก academic period แล้ว evaluation period options ควรถูก filter ให้สัมพันธ์กันเมื่อทำได้
- ถ้า evaluation period ที่อยู่ใน URL ไม่สัมพันธ์กับ academic period ที่เลือก ให้แสดง fallback state ที่ไม่พัง และ reset ได้

### Work Category

UI label:

```text
หมวดงาน
```

Source:

```text
GET /api/v2/work-categories
```

Option fields:

- `code`
- `label_th`
- `label_en`
- `display_order`

URL query:

```text
category=TEACHING
```

Display examples:

- `งานสอน`
- `งานวิจัย`
- `งานบริการวิชาการ`
- `งานดูแลนักศึกษา`
- `งานบริหาร`

### Work Type

UI label:

```text
ประเภทงานย่อย
```

Source:

```text
GET /api/v2/work-types
GET /api/v2/work-types?category=TEACHING
```

Option fields:

- `code`
- `category_code`
- `label_th`
- `label_en`
- `default_visibility`
- `display_order`

URL query:

```text
type=LECTURE
```

Rules:

- เลือก category แล้ว type dropdown ต้องเหลือเฉพาะ type ที่ `category_code` ตรงกัน
- ถ้าเปลี่ยน category แล้ว `type` เดิมไม่อยู่ใต้ category ใหม่ ต้อง clear `type` จาก state/URL
- ถ้า URL มี `type` แต่ไม่มี category ให้ยังแสดงได้ถ้า type code อยู่ใน master data

### Faculty

UI label:

```text
อาจารย์
```

Source:

```text
GET /api/v2/faculties
```

Option fields:

- `id`
- `public_slug`
- `name_th`
- `name_en`
- `academic_position`
- `department`

URL query:

```text
faculty_id=fac_prapaporn-rattanatamrong
```

Display example:

```text
ผศ.ดร.ประภาพร รัตนธำรง
```

Do not expose:

- internal notes
- audit fields
- source/provenance fields
- private evidence fields

## URL Query Contract

การ์ดนี้ต้องกำหนด query contract ให้ #73/#75 ใช้ต่อได้:

| Filter | URL query key | Example | Notes |
|---|---|---|---|
| keyword | `q` | `privacy` | trim empty value |
| academic period | `academic_period_id` | `ap-2567-2` | selected from master data |
| evaluation period | `evaluation_period_id` | `eval-2567-full-year` | optional |
| category | `category` | `TEACHING` | work_category.code |
| work type | `type` | `LECTURE` | work_type.code |
| faculty | `faculty_id` | `fac_prapaporn-rattanatamrong` | faculty.id |
| page placeholder | `page` | `1` | reserved for #73 |

Example URL:

```text
/outputs?q=software&academic_period_id=ap-2567-2&category=TEACHING&type=LECTURE&faculty_id=fac_prapaporn-rattanatamrong&page=1
```

Rules:

- query serialization ต้อง stable และ predictable
- ไม่ควรเก็บ default/empty values ลง URL
- reset filter ต้องลบ filter query keys และกลับไป `/outputs`
- reload URL แล้ว UI ต้อง restore state เดิม
- invalid query value ที่ไม่อยู่ใน master data ต้องไม่ crash ควรแสดง warning/clearable state หรือ fallback เป็น empty selection

## Data Loading Contract

ต้องโหลด master data จาก AWS endpoint จริงใน production:

```text
NEXT_PUBLIC_V2_API_BASE_URL
```

Expected request examples:

```text
GET ${NEXT_PUBLIC_V2_API_BASE_URL}/api/v2/academic-periods
GET ${NEXT_PUBLIC_V2_API_BASE_URL}/api/v2/evaluation-periods
GET ${NEXT_PUBLIC_V2_API_BASE_URL}/api/v2/work-categories
GET ${NEXT_PUBLIC_V2_API_BASE_URL}/api/v2/work-types
GET ${NEXT_PUBLIC_V2_API_BASE_URL}/api/v2/faculties
```

Expected response envelope:

```json
{
  "items": [],
  "meta": {
    "count": 0
  }
}
```

Error shape:

```json
{
  "error": {
    "code": "INVALID_QUERY",
    "message": "category must be a known work category code",
    "details": {
      "field": "category"
    }
  }
}
```

Implementation notes:

- frontend helper ควร validate envelope ขั้นต่ำก่อนใช้
- ถ้า endpoint ใด fail ให้แสดง error state ของ filter options
- ไม่ควร silently fallback เป็น hardcoded options ใน production เพราะจะทำให้ปิดการ์ดโดยไม่ได้ใช้ AWS จริง
- local/component test ใช้ fixture/mock ได้ แต่ QA evidence ต้องใช้ deployed API Gateway URL

## Page States

### Loading State

ใช้ตอนกำลังโหลด master data:

- แสดง skeleton/placeholder สำหรับ filter controls
- result placeholder ยังรักษาความสูงคร่าว ๆ เพื่อไม่ให้ layout กระโดด
- มีข้อความสั้น ๆ เช่น `กำลังโหลดตัวเลือกตัวกรอง`

### Error State

ใช้เมื่อ Master Data API fail:

- แสดงข้อความว่าโหลดตัวเลือกตัวกรองไม่ได้
- มีปุ่ม retry หรือคำแนะนำ reload
- ไม่แสดง stack trace หรือ endpoint secret
- result placeholder อยู่ได้ แต่ควร disabled filters ที่ไม่มี options

### Empty State

ในการ์ดนี้ empty state หมายถึง:

- master data บาง endpoint return `items: []`
- result list ยังเป็น placeholder เพราะ #73 ยังไม่ทำ full result list

ข้อความควรสื่อว่า:

```text
ยังไม่มีรายการผลลัพธ์ในหน้านี้ Result list จะถูกเติมในการ์ด #73
```

ห้ามทำให้ผู้ใช้เข้าใจผิดว่า repository ไม่มีข้อมูลจริง ถ้าแค่ result API ยังไม่ต่อ

### Ready State

เมื่อ master data โหลดครบ:

- filters ใช้งานได้
- category/type dependency ทำงาน
- URL query sync ทำงาน
- result placeholder แสดงว่า filter state พร้อมส่งต่อให้ #73/#75

## Responsive Requirements

Desktop:

- filter panel อาจเป็น 2-3 columns
- keyword search กว้างกว่าตัวอื่นได้
- result placeholder อยู่ใต้ filters
- applied filters summary อยู่ใกล้ result area

Mobile:

- filters ต้อง stack เป็น single column
- controls ต้องไม่ล้นจอ
- label ต้องอ่านง่าย
- reset/apply controls ต้องกดง่าย
- mobile menu/header เดิมต้องไม่พัง

Accessibility:

- input/select ทุกตัวต้องมี label ที่ชัดเจน
- loading/error ต้องประกาศด้วย text ที่อ่านเข้าใจ ไม่พึ่งสีอย่างเดียว
- keyboard navigation ใช้งานได้
- focus state ไม่หาย

## Navigation Requirement

เพิ่ม navigation entry เฉพาะถ้าเข้ากับ current frontend design:

Suggested label:

```text
ผลงานและภาระงาน
```

Suggested href:

```text
/outputs
```

Rules:

- `/faculties` ยัง active ถูกเมื่ออยู่หน้า faculty directory
- `/outputs` active ถูกเมื่ออยู่หน้า repository
- disabled nav items เดิมไม่ควรถูกทำให้เป็น link โดยไม่ตั้งใจ
- mobile nav ต้องมี entry ใหม่ถ้า desktop nav มี

## Placeholder For #73

การ์ดนี้ต้องเตรียมพื้นที่ให้ #73 ต่อได้ง่าย โดยไม่ต้องรื้อหน้า:

```text
Result summary placeholder
Result list placeholder
Pagination placeholder
```

Suggested placeholder copy:

```text
พื้นที่ผลลัพธ์สำหรับรายการผลงานและภาระงาน
ตัวกรองด้านบนพร้อมส่งต่อให้ Work Item List API ในการ์ด #75
```

Data ที่ควรส่งต่อเป็น object ภายใน component:

```json
{
  "q": "software",
  "academic_period_id": "ap-2567-2",
  "evaluation_period_id": "eval-2567-full-year",
  "category": "TEACHING",
  "type": "LECTURE",
  "faculty_id": "fac_prapaporn-rattanatamrong",
  "page": 1
}
```

## Suggested Implementation Files

ชื่อไฟล์จริงปรับได้ตาม pattern frontend แต่ควรประมาณนี้:

```text
frontend/app/outputs/page.tsx
frontend/app/outputs/loading.tsx
frontend/app/outputs/error.tsx
frontend/components/outputs/repository-page-header.tsx
frontend/components/outputs/repository-filter-panel.tsx
frontend/components/outputs/repository-result-placeholder.tsx
frontend/components/outputs/filter-state-summary.tsx
frontend/lib/v2/master-data-client.ts หรือ reuse frontend/lib/v2/master-data.mjs ตาม pattern ที่ทีมเลือก
frontend/lib/v2/output-query-state.ts
```

ถ้าใช้ `frontend/lib/v2/master-data.mjs` ที่มีอยู่แล้วจาก #64 ให้แยกให้ชัดว่า:

- production UI fetch ใช้ deployed API Gateway
- fixture helper ใช้เฉพาะ local/test

## Environment / Config

ควรเพิ่มตัวอย่างใน frontend env:

```text
NEXT_PUBLIC_V2_API_BASE_URL=https://n89gqgnqw2.execute-api.ap-southeast-1.amazonaws.com
```

Rules:

- ถ้า env missing ให้แสดง error ที่เข้าใจง่ายใน dev
- ห้ามใส่ AWS secret, DB secret, resource ARN ใน frontend env
- base URL ต้องไม่ลงท้าย slash ซ้ำจน request URL ผิด

## QA Evidence

ต้องมี evidence สำหรับปิดการ์ด:

- screenshot หรือ note ว่า `/outputs` เปิดได้
- Network tab หรือ log ว่าเรียก deployed AWS endpoint จริงอย่างน้อย 5 endpoint จาก #64
- reload URL ที่มี query แล้ว state ยังอยู่
- category/type dependency ทำงาน
- reset filters ทำงาน
- mobile viewport ไม่ล้น
- V1 `/faculties` ยังเปิดได้
- V1 `/faculties/{id}` ยังเปิดได้ถ้า route นั้นมีใน repo

Example manual QA URLs:

```text
/outputs
/outputs?category=TEACHING&type=LECTURE
/outputs?academic_period_id=ap-2567-2&faculty_id=fac_prapaporn-rattanatamrong
/outputs?q=software&category=TEACHING&type=LECTURE&page=1
/faculties
```

## Acceptance Criteria

- [ ] `/outputs` เปิดได้
- [ ] page title/description สื่อว่าเป็น V2 Faculty Output Repository
- [ ] มี filter controls ครบตาม scope
- [ ] filter options โหลดจาก deployed Master Data API จริง
- [ ] ใช้ `NEXT_PUBLIC_V2_API_BASE_URL` หรือ config equivalent ไม่ hardcode endpoint ใน component
- [ ] filter state sync กับ URL query
- [ ] reload URL ที่มี query แล้วยังเห็น filter state เดิม
- [ ] reset filter ทำงานถูกต้อง
- [ ] category/type dependency ทำงาน
- [ ] loading state สำหรับ master data ชัดเจน
- [ ] error state สำหรับ AWS endpoint failure ชัดเจน
- [ ] empty/placeholder state ไม่ทำให้เข้าใจผิดว่า repository ไม่มีข้อมูลจริง
- [ ] responsive layout ใช้งานได้บน mobile/desktop
- [ ] navigation entry ไป `/outputs` ใช้งานได้ถ้าเพิ่ม nav
- [ ] V1 `/faculties` และ `/faculties/{id}` ไม่พัง
- [ ] มี placeholder สำหรับ result list/pagination ให้ #73 ต่อได้
- [ ] มี QA evidence ว่า `/outputs` โหลด filter options จาก AWS endpoint ได้

## Review Checklist

Frontend:

- [ ] component structure อ่านง่ายและ reuse ต่อได้
- [ ] filter state แยกจาก rendering พอให้ #73/#75 ใช้ต่อ
- [ ] ไม่มี hardcoded demo-only labels/options เกินจำเป็น
- [ ] URL query parsing/serialization stable
- [ ] category/type filtering ไม่ duplicate logic กระจายหลายจุด
- [ ] env/config จัดการ missing/invalid base URL ได้

UX:

- [ ] mobile ไม่ล้นจอ
- [ ] filter labels เข้าใจง่าย
- [ ] loading/empty/error states ชัดเจน
- [ ] reset filter หาเจอง่าย
- [ ] page ไม่ดูเป็น landing page แต่เป็น repository/tool page

QA:

- [ ] reload URL ที่มี query แล้วยังเห็น filter state เดิม
- [ ] reset filter ทำงานถูกต้อง
- [ ] ปิด mock/fixture แล้วหน้ายังโหลด filter options จาก AWS ได้
- [ ] test category/type dependency
- [ ] test AWS endpoint failure state
- [ ] test V1 routes smoke

Security / Data:

- [ ] frontend ไม่เห็น DB secret, AWS secret, ARN หรือ private S3 path
- [ ] faculties options ใช้ public-safe fields จาก #64
- [ ] ไม่ expose source/audit/auth fields
- [ ] ไม่มี admin-only route หรือ auth logic ปนในการ์ดนี้

## Dependencies

Blocked by:

- #64 Build Master Data API

Blocks:

- #73 Build Repository Result List & Pagination UI
- #75 Integrate Repository UI with Real API

Related:

- #66 Build Work Item List/Search/Filter API
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

การ์ดนี้ถือว่าเสร็จเมื่อมีหน้า `/outputs` ที่เป็น shell ของ V2 repository พร้อม filter UI, URL query state, responsive states และ placeholder สำหรับ #73 โดย filter options ต้องโหลดจาก deployed AWS Master Data API จริง มี evidence ว่า query reload/reset/category-type dependency ทำงาน และ V1 routes เดิมไม่พัง
