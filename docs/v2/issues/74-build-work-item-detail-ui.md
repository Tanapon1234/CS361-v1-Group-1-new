# [V2] Build Work Item Detail UI #74

## สรุป

สร้างหน้า `/outputs/{id}` สำหรับแสดงรายละเอียด work item รายการเดียวตาม Detail API contract พร้อม subtype detail, faculty contributors และ evidence metadata แบบ public-safe

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #60 แต่ GitHub issue จริงใช้ #74

## Background

ผู้ใช้ต้องสามารถกดจาก result list เข้าไปดูรายละเอียดของผลงาน/ภาระงานแต่ละรายการได้ โดยหน้า detail ต้องรองรับหลาย category ที่มีข้อมูลไม่เหมือนกัน

Detail API จาก #68 จะ return `detail.kind` เพื่อบอก subtype เช่น teaching, publication, research project, supervision, service หรือ administration

## เป้าหมาย

สร้าง detail UI ที่:

- เปิด route `/outputs/{id}`
- แสดงข้อมูลกลางของ work item
- แสดง faculty contributors และ contribution role/order
- แสดง subtype detail ตาม `detail.kind`
- แสดง evidence metadata เฉพาะ public-safe
- มี loading/not found/error states
- link กลับไป `/outputs` พร้อม preserve query ถ้าเป็นไปได้

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- evidence download/signed URL
- admin edit/delete action
- official report print/export
- real API integration เต็มรูปแบบถ้า #75 แยกไว้

## Scope

### ต้องทำ

- เพิ่ม route `/outputs/{id}`
- เพิ่ม detail layout/components:
  - header/title/status
  - category/type/period metadata
  - faculty contributors
  - subtype detail section
  - evidence metadata section
- รองรับ subtype display อย่างน้อย:
  - teaching
  - publication
  - research project
  - supervision
  - service
  - administration
- เพิ่ม loading/not found/error states
- เพิ่ม tests หรือ manual QA checklist สำหรับ demo records

### ไม่ต้องทำ

- admin-only detail
- mutation buttons
- restricted evidence viewer

## UI Contract

ใช้ response จาก #68:

```json
{
  "id": "wi_001",
  "title": "ตัวอย่างผลงาน",
  "category": "PUBLICATION",
  "type": "JOURNAL_ARTICLE",
  "faculty": [],
  "detail": {
    "kind": "publication"
  },
  "evidence": []
}
```

UI ต้อง handle `detail` missing/null ได้อย่างสุภาพ เพราะบาง work item อาจมีเฉพาะ core fields ในช่วงเริ่ม import

## Acceptance Criteria

- [ ] `/outputs/{id}` เปิดได้
- [ ] แสดง title/category/type/period/faculty ได้
- [ ] แสดง subtype detail ตาม `detail.kind`
- [ ] evidence metadata public-safe แสดงได้
- [ ] loading/error/not found states ครบ
- [ ] link กลับ repository page ได้
- [ ] responsive บน mobile/desktop
- [ ] ไม่มี admin-only/source/audit fields ใน public UI

## Review Checklist

Frontend:

- [ ] subtype rendering แยกเป็น component ที่ดูแลต่อได้
- [ ] missing optional fields ไม่ทำให้หน้า crash
- [ ] date/number formatting consistent

UX:

- [ ] detail hierarchy อ่านง่าย
- [ ] evidence section ไม่ทำให้ผู้ใช้คิดว่าดาวน์โหลด restricted file ได้

QA:

- [ ] ทดสอบ demo records ครบหลาย category
- [ ] ทดสอบ not found และ restricted item

## Dependencies

Blocked by:

- #68 Build Work Item Detail API
- #73 Build Repository Result List & Pagination UI

Blocks:

- #75 Integrate Repository UI with Real API

Related:

- #67 Build Faculty Work Items API

## Suggested Labels

- `v2`
- `frontend`
- `ui`
- `detail`
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

การ์ดนี้ถือว่าเสร็จเมื่อผู้ใช้สามารถเปิดหน้า detail ของ work item ได้ และเห็นข้อมูลกลาง/subtype/faculty/evidence metadata แบบ public-safe ตาม contract ของ V2
