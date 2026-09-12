# [V2] Prepare Multi-Year Demo Dataset

## สรุป

เตรียมชุดข้อมูลตัวอย่างสำหรับ V2 ที่ครอบคลุมหลายปีการศึกษา หลายหมวดงาน และใช้ทดสอบ search/filter/detail/admin/migration demo ได้จริง

การ์ดนี้ทำให้ทีมมี dataset กลางสำหรับพัฒนาและ demo V2 โดยไม่ต้องรอข้อมูลจริงครบทุกส่วน และไม่ต้องเดาว่าควรมี record ประเภทไหนบ้าง

## Background

V2 ต้องพิสูจน์ว่าเป็น **Managed Multi-year Faculty Output Repository** ไม่ใช่แค่ V1 public faculty profile

ดังนั้น demo dataset ต้องครอบคลุมมากกว่า faculty profile และ selected publications ต้องมีตัวอย่างของ:

- งานสอน
- งานวิจัย
- publication
- งานบริการวิชาการ
- supervision / การดูแลนักศึกษา
- งานบริหาร
- evidence reference
- หลาย academic years
- หลาย semesters
- หลาย faculty

Dataset นี้จะถูกใช้ต่อโดย:

- #51 Master Data API
- #52 Work Item Search/Filter API
- #53 Faculty Work Items API
- #54 Work Item Detail API
- #58-#61 Repository UI
- #66 Migration / Seed Repository / V1 Compatibility
- #67 Final Demo

## เป้าหมาย

สร้าง V2 demo dataset ที่เพียงพอสำหรับพิสูจน์ requirement หลักของ V2:

- เก็บข้อมูลหลายประเภท
- รองรับหลายปีการศึกษา
- filter/search ตาม faculty, academic year, semester, category, type, keyword ได้
- เปิด work item detail ได้
- มี evidence reference
- แยก public/internal/restricted ได้
- preserve V1 faculty slug ได้
- ใช้เป็น seed/migration input สำหรับ #66 ได้

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- เขียน migration runner จริง
- insert ข้อมูลเข้า Aurora จริง
- build API
- build frontend
- ทำ admin CRUD
- ทำ official workload scoring
- ทำ official workload sheet/report
- ใช้ข้อมูลจริงทุก record
- extract ข้อมูลจาก PDF แบบ automated เต็มรูปแบบ

ถ้าใช้ synthetic data ต้อง label ชัดเจน

## Scope

### ต้องทำ

- กำหนด demo dataset structure
- สร้างหรือเตรียม fixture/source files สำหรับ V2
- ครอบคลุม faculty อย่างน้อย 2 คน
- ครอบคลุม academic years อย่างน้อย 2 ปี
- ครอบคลุม academic periods อย่างน้อย 3 period
- ครอบคลุม work categories หลัก
- เพิ่ม evidence reference ตัวอย่าง
- ระบุ visibility ของแต่ละ record
- ระบุ source/provenance ของ record
- ระบุ synthetic/test data ให้ชัดเจน
- เขียน validation summary ของ dataset

### ไม่ต้องทำ

- deploy data เข้า AWS
- run migration เข้า Aurora
- สร้าง Lambda หรือ API
- ทำ UI demo

## Minimum Dataset Requirements

Dataset ขั้นต่ำต้องมี:

```text
Faculty              >= 2
Academic Years       >= 2
Academic Periods     >= 3
Teaching Records     >= 3
Research Records     >= 3
Publication Records  >= 3
Service Records      >= 3
Supervision Records  >= 3
Administration       >= 2
Evidence References  >= 3
```

ควรมี record ที่ครอบคลุม:

- อย่างน้อย 1 public publication
- อย่างน้อย 1 internal teaching record
- อย่างน้อย 1 restricted supervision/evidence case
- อย่างน้อย 1 record ที่มีหลาย faculty ร่วมกัน
- อย่างน้อย 1 record ที่มี contribution percent
- อย่างน้อย 1 record ที่มี external evidence URL
- อย่างน้อย 1 record ที่มี source section code จากแบบฟอร์มภาระงาน

## Suggested File Structure

เตรียมไฟล์ไว้ใน:

```text
data/v2/fixtures/
├── README.md
├── faculties.json
├── academic-periods.json
├── work-categories.json
├── work-types.json
├── work-items.json
├── faculty-work-items.json
├── teaching-details.json
├── publication-details.json
├── research-project-details.json
├── supervision-details.json
├── service-details.json
├── administration-details.json
├── evidence-references.json
└── dataset-summary.json
```

หรือถ้าทีมเลือก format อื่น เช่น CSV ต้องระบุเหตุผลและ mapping ให้ชัดเจน

## Data Categories Required

### Faculty

ต้อง reuse faculty จาก V1 อย่างน้อย 2 คน

ต้อง preserve:

- `public_slug`
- ชื่อไทย/อังกฤษ
- academic position ถ้ามี
- public fields ที่ต้องใช้ใน UI

Rule:

- ห้ามสร้าง slug ใหม่แทน V1 slug
- ถ้าใช้ synthetic faculty เพิ่ม ต้อง label ว่า `SYNTHETIC TEST DATA`

### Academic Period

ต้องมีอย่างน้อย 3 academic periods เช่น:

```text
1/2566
2/2566
2/2567
```

ต้องแยกจาก evaluation period

ตัวอย่าง:

```text
academic_year = 2567
semester = 2
label = 2/2567
```

### Teaching

ต้องมี record ตัวอย่าง เช่น:

- lecture course
- lab course
- seminar หรือ project course

ควรมี field เช่น:

- course code
- course name
- degree level
- lecture hours
- lab hours
- credits
- student count
- teaching role

### Research / Research Project

ต้องมี record ตัวอย่าง เช่น:

- funded research project
- progress/report item
- research grant item

ควรมี field เช่น:

- project name
- funding source
- funding type
- budget ถ้ามี
- project start/end

### Publication

ต้องมี publication อย่างน้อย 3 รายการ

ควรมี:

- title
- authors
- publication year
- venue
- DOI หรือ URL ถ้ามี
- citation text
- quartile / indexing database / TCI group ถ้ามี
- contribution percent ถ้ามี

Rule:

- DOI duplicate ต้องใช้ทดสอบ duplicate handling ได้
- ถ้าไม่มี DOI ให้ใช้ normalized title + year เป็น duplicate fallback

### Supervision

ต้องมีตัวอย่าง:

- senior project
- thesis
- cooperative education หรือ special project

ควรระวัง:

- หลีกเลี่ยงข้อมูลระบุตัวนักศึกษาจริง
- ถ้าต้องมี student reference ให้ใช้ synthetic/non-identifying reference
- record ที่มี student-related data ต้อง classify เป็น `RESTRICTED` ถ้าไม่ public-safe

### Academic Service

ต้องมีตัวอย่าง:

- committee
- reviewer
- invited speaker
- academic service activity

ควรมี:

- organization
- scope
- role
- evidence reference

### Administration

ต้องมีตัวอย่าง:

- course coordinator
- department/faculty committee
- administrative position

ควรมี:

- position name
- organization unit
- start/end date

### Evidence Reference

ต้องมีอย่างน้อย 3 รายการ

ตัวอย่าง:

- external URL
- internal reference label
- synthetic S3 key placeholder
- source section code จาก workload form

Rule:

- ห้ามใส่ secret/private URL จริงที่ไม่ควรเผยแพร่
- S3 key ถ้าเป็นตัวอย่างต้องเป็น placeholder ที่ไม่ทำให้เข้าใจว่าเป็น credential
- visibility ต้องชัดเจน

## Visibility Requirements

Dataset ต้องมี visibility อย่างน้อย:

- `PUBLIC`
- `INTERNAL`
- `RESTRICTED`

ต้องมี test data ที่ใช้ตรวจว่า:

- public query เห็นเฉพาะ `PUBLIC`
- internal/restricted ไม่หลุดไป public response
- restricted supervision/evidence ไม่แสดงใน public projection

## Synthetic Data Rule

ถ้า record ใดไม่ใช่ข้อมูลจริง ต้อง label ให้ชัดเจน:

```text
synthetic: true
source_system: SYNTHETIC_TEST_DATA
```

หรือใช้ field equivalent ที่ทีมตกลง

เอกสาร README ของ dataset ต้องบอกว่า:

- record ไหนมาจาก V1 จริง
- record ไหน synthetic
- record ไหน derived จาก workload form เพื่อ domain discovery
- record ไหนใช้สำหรับ demo/search/filter test

## Source / Provenance Rule

ทุก record ควรมี source metadata ขั้นต่ำ:

- source system
- source record key
- source type
- source note
- synthetic flag ถ้ามี
- related V1 slug หรือ workload form section ถ้ามี

ตัวอย่าง:

```text
source_system = V1_PUBLIC_PROFILE
source_record_key = prapaporn-rattanatamrong:selected-publication:doi:...
```

หรือ:

```text
source_system = SYNTHETIC_TEST_DATA
source_record_key = demo-teaching-2567-001
```

## Search/Filter Test Matrix

Dataset ต้องรองรับการทดสอบ query ต่อไปนี้:

### Query 1

```text
Faculty = A
Academic Year = 2567
```

### Query 2

```text
Academic Year = 2567
Category = TEACHING
```

### Query 3

```text
Faculty = A
Category = RESEARCH
Type = PUBLICATION
```

### Query 4

```text
Academic Year 2566-2568
Keyword = privacy
```

### Query 5

```text
Category = SUPERVISION
Degree Level = PhD หรือ equivalent
```

### Query 6

```text
Faculty A
Year 2567
Semester 2
Category = TEACHING
```

ถ้า dataset ยังไม่รองรับ query ใด ต้องบันทึก gap และเหตุผล

## Expected Deliverables

ต้องมี:

```text
data/v2/fixtures/README.md
data/v2/fixtures/dataset-summary.json
data/v2/fixtures/*.json หรือ *.csv ตาม format ที่ทีมเลือก
docs/v2/demo-dataset.md
```

เอกสารควรบอก:

- จำนวน record ต่อ entity
- academic years/periods ที่ครอบคลุม
- categories/types ที่ครอบคลุม
- visibility coverage
- synthetic vs real data
- search/filter matrix coverage
- known limitations

## Acceptance Criteria

- [ ] มี V2 demo dataset structure แล้ว
- [ ] มี faculty อย่างน้อย 2 คน
- [ ] preserve V1 public slug สำหรับ faculty ที่มาจาก V1
- [ ] มี academic years อย่างน้อย 2 ปี
- [ ] มี academic periods อย่างน้อย 3 period
- [ ] มี teaching records อย่างน้อย 3 รายการ
- [ ] มี research records อย่างน้อย 3 รายการ
- [ ] มี publication records อย่างน้อย 3 รายการ
- [ ] มี service records อย่างน้อย 3 รายการ
- [ ] มี supervision records อย่างน้อย 3 รายการ
- [ ] มี administration records อย่างน้อย 2 รายการ
- [ ] มี evidence references อย่างน้อย 3 รายการ
- [ ] มีอย่างน้อย 1 many-faculty work item
- [ ] มีอย่างน้อย 1 contribution percent example
- [ ] มี visibility ครบ `PUBLIC`, `INTERNAL`, `RESTRICTED`
- [ ] public-safe และ restricted examples แยกชัดเจน
- [ ] synthetic data ถูก label ชัดเจน
- [ ] source/provenance metadata มีใน record สำคัญ
- [ ] dataset รองรับ search/filter matrix ที่กำหนด
- [ ] มี dataset summary
- [ ] มี README อธิบายวิธีใช้ dataset
- [ ] ไม่มี secret/private credential ใน dataset
- [ ] ไม่มี student-identifying real data ใน demo dataset

## Review Checklist

Data / Database:

- [ ] dataset ตรงกับ schema จาก #47
- [ ] data type เหมาะกับ migration/seed
- [ ] required fields ครบ
- [ ] source/provenance เพียงพอ

Backend:

- [ ] dataset ใช้ทดสอบ master data API ได้
- [ ] dataset ใช้ทดสอบ search/filter API ได้
- [ ] dataset ใช้ทดสอบ detail API ได้
- [ ] dataset มี edge cases พอสมควร

Frontend:

- [ ] dataset มีข้อมูลพอสำหรับ filter dropdown
- [ ] dataset มี result list ที่หลากหลาย
- [ ] dataset มี detail pages ที่แสดง subtype ต่างกันได้
- [ ] long title/empty optional fields มีตัวอย่างให้ทดสอบ UI

QA / Integration:

- [ ] dataset รองรับ smoke test V2 core
- [ ] visibility leak test ทำได้
- [ ] V1 compatibility test ทำได้
- [ ] known limitations ถูกบันทึก

Tech Lead:

- [ ] dataset ไม่ขยาย scope เกิน V2
- [ ] synthetic data label ชัดเจน
- [ ] dataset เหมาะกับ final demo story

## Dependencies

Blocked by:

- #46 Freeze V2 Scope, Architecture & Interface Contracts
- #47 Design Relational Schema & SQL Migration
- #49 Define V1 to V2 Data Mapping

Blocks:

- #52 Build Work Item List/Search/Filter API
- #53 Build Faculty Work Items API
- #54 Build Work Item Detail API
- #58 Build Repository Page Shell & Filter UI
- #59 Build Repository Result List & Pagination UI
- #60 Build Work Item Detail UI
- #61 Integrate Repository UI with Real API
- #66 Execute Migration & Preserve V1 Compatibility
- #67 Final Integration / Deploy / Demo Docs

Related:

- #51 Build Master Data API
- #56 Build Admin Create Work Item API
- #57 Build Admin Update / Soft Delete API

## Suggested Labels

- `v2`
- `data`
- `fixtures`
- `demo`
- `migration`
- `blocking`
- `ready-for-review`

## Suggested Owner

Data Developer

Reviewers:

- Tech Lead
- Backend Developer
- Frontend Developer
- QA / Integration

## Estimate

0.5-1 day

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อทีมมี V2 demo dataset หลายปีที่ครอบคลุม faculty, teaching, research, publication, service, supervision, administration และ evidence เพียงพอสำหรับทดสอบ search/filter/detail และใช้เป็นฐานสำหรับ #66 migration กับ #67 final demo ได้
