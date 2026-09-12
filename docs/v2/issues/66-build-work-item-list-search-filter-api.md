# [V2] Build Work Item List/Search/Filter API #66

## สรุป

สร้าง `GET /api/v2/work-items` สำหรับค้นหา กรอง และแบ่งหน้า work items ของ V2 repository โดยอ่านจาก Aurora/fixture adapter และ enforce public-safe visibility ที่ backend

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #52 แต่ GitHub issue จริงใช้ #66

## Background

V2 ต้องให้ผู้ใช้ค้นหาและกรองข้อมูลผลงาน/ภาระงานอาจารย์ได้จาก repository กลาง ไม่ใช่อ่านไฟล์ public faculty profile แบบ V1 เท่านั้น

ตอนนี้มี baseline แล้ว:

- schema และ indexes ใน `database/migrations/001_base.sql`
- master data seed ใน `database/seeds/001_master_data.sql`
- demo dataset ใน `data/v2/fixtures/`
- Master Data API จาก #64 สำหรับ filter options

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
- เพิ่ม input validation และ response envelope
- เพิ่ม tests สำหรับ success, empty state, invalid query, pagination และ visibility
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
/api/v2/work-items?faculty_id=fac_prapaporn&academic_period_id=ap_2567_2&category=TEACHING&page=1&page_size=20
```

Response:

```json
{
  "items": [
    {
      "id": "wi-teach-2567-2-cs333",
      "title": "CS333 Software Engineering Lecture",
      "category": "TEACHING",
      "type": "TEACHING_LECTURE",
      "academic_period": {
        "id": "ap_2567_2",
        "label": "2/2567"
      },
      "faculty": [
        {
          "id": "fac_prapaporn",
          "display_name": "ผศ. ดร. ประภาภรณ์ รัตนธรรมรงค์",
          "slug": "prapaporn-rattanatamrong",
          "role": "INSTRUCTOR"
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

## Review Checklist

Backend:

- [ ] SQL/query ไม่เกิด N+1 แบบชัดเจน
- [ ] query มี sorting ที่ stable เช่น `updated_at desc, id asc`
- [ ] DTO ไม่ expose raw/provenance/admin fields

QA:

- [ ] ใช้ `data/v2/fixtures/dataset-summary.json` เป็น expected baseline ได้
- [ ] test matrix จาก `docs/v2/demo-dataset.md` ผ่าน

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

การ์ดนี้ถือว่าเสร็จเมื่อ V2 มี Work Item List/Search/Filter API ที่ค้นหา กรอง แบ่งหน้า และ enforce public visibility ได้จริง พร้อม contract และ tests ที่ frontend ใช้สร้างหน้า repository ต่อได้โดยไม่ต้องเดา response shape เอง
