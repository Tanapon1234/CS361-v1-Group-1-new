# [V2] Build Faculty Work Items API #67

## สรุป

สร้าง `GET /api/v2/faculties/{faculty_id}/work-items` เพื่อเรียกดูผลงาน/ภาระงานที่เกี่ยวข้องกับอาจารย์คนใดคนหนึ่ง โดยใช้ `faculty_work_item` เป็นตัวเชื่อมหลัก

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #53 แต่ GitHub issue จริงใช้ #67

## Background

V1 มี faculty profile เป็นศูนย์กลาง แต่ V2 ต้องแสดงผลงาน/ภาระงานของอาจารย์หลายปี หลายหมวดงาน และรองรับงานที่มีอาจารย์หลายคนร่วมกัน

`faculty_work_item` จึงเป็น table สำคัญสำหรับ:

- ผูก faculty กับ work item
- เก็บ role/contribution
- รองรับ many-to-many contribution
- filter ตาม academic/evaluation period ของ faculty แต่ละคน

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
- เพิ่ม tests สำหรับ faculty not found, no work items, multi-faculty work item, visibility

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
/api/v2/faculties/fac_prapaporn/work-items?academic_period_id=ap_2567_2&category=RESEARCH&page=1&page_size=20
```

Response:

```json
{
  "faculty": {
    "id": "fac_prapaporn",
    "public_slug": "prapaporn-rattanatamrong",
    "display_name": "ผศ. ดร. ประภาภรณ์ รัตนธรรมรงค์"
  },
  "items": [
    {
      "id": "wi-research-2567-privacy-platform",
      "title": "Privacy Platform Research Project",
      "category": "RESEARCH",
      "type": "RESEARCH_PROJECT",
      "faculty_role": "PI",
      "contribution_order": 1,
      "contribution_percent": 60,
      "academic_period": {
        "id": "ap_2567_2",
        "label": "2/2567"
      },
      "visibility": "PUBLIC",
      "updated_at": "2026-09-12T00:00:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

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

## Review Checklist

Backend:

- [ ] ใช้ `faculty_work_item` ไม่ shortcut จาก `work_item.created_by`
- [ ] query ไม่ hardcode faculty demo ids
- [ ] response shape ใช้ชื่อ field consistent กับ #66

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

การ์ดนี้ถือว่าเสร็จเมื่อ V2 เรียกผลงาน/ภาระงานของอาจารย์รายคนได้จาก relation จริง พร้อม filter, pagination, contribution fields และ public visibility rule ที่ตรวจสอบได้
