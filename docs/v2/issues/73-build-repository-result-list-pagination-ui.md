# [V2] Build Repository Result List & Pagination UI #73

## สรุป

สร้างส่วนแสดงผลรายการ work items และ pagination บนหน้า `/outputs` ตาม response shape ของ `GET /api/v2/work-items`

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #59 แต่ GitHub issue จริงใช้ #73

## Background

หลังจากมี shell/filter UI จาก #72 และ Work Item List API จาก #66 หน้า repository ต้องแสดงรายการผลลัพธ์ที่ผู้ใช้ scan ได้ง่าย เช่น title, category/type, period, faculty contributors และ updated date

## เป้าหมาย

สร้าง UI list/pagination ที่:

- render response shape จาก #66 ได้
- รองรับ loading, empty, error, pagination
- แสดงข้อมูลพอให้ผู้ใช้ตัดสินใจกดเข้า detail
- link ไป `/outputs/{id}` สำหรับ #74
- รักษา filter/query state ระหว่างเปลี่ยนหน้า

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- implement detail page
- integrate API แบบ production เต็มรูปแบบถ้า #75 แยกไว้
- ทำ admin list
- ทำ export/download

## Scope

### ต้องทำ

- สร้าง result list component สำหรับ work item summary
- แสดง:
  - title
  - category/type label
  - academic/evaluation period
  - faculty contributors แบบย่อ
  - visibility badge เฉพาะถ้า public-safe และมีประโยชน์
  - updated date
- เพิ่ม pagination controls
- เพิ่ม empty state เมื่อไม่มีผลลัพธ์
- เพิ่ม loading skeleton/state
- เพิ่ม error state พร้อม retry หรือ clear filter ตาม UX ที่เหมาะสม
- link item ไป `/outputs/{id}`
- เพิ่ม tests หรือ manual QA checklist

### ไม่ต้องทำ

- real data fetching ถ้า #75 จะทำ integration แยก
- admin-only fields
- work item detail content

## UI Data Contract

Component ต้องรองรับ list response:

```json
{
  "items": [
    {
      "id": "wi_001",
      "title": "ตัวอย่างผลงาน",
      "category": "PUBLICATION",
      "type": "JOURNAL_ARTICLE",
      "academic_period": {
        "id": "ap_2567_2",
        "label": "2/2567"
      },
      "faculty": [
        {
          "id": "fac_prapaporn",
          "display_name": "ผศ. ดร. ประภาภรณ์ รัตนธรรมรงค์",
          "slug": "prapaporn-rattanatamrong",
          "role": "AUTHOR"
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

## Acceptance Criteria

- [ ] result list แสดง work item summary ได้
- [ ] item link ไป `/outputs/{id}`
- [ ] pagination update URL/query state ได้
- [ ] loading/empty/error states ทำงานครบ
- [ ] responsive บน mobile/desktop
- [ ] ไม่มี internal/restricted/admin-only field ใน public UI
- [ ] component พร้อมเชื่อม real API ใน #75

## Review Checklist

Frontend:

- [ ] data mapping ไม่ผูกกับ fixture-specific field
- [ ] layout ไม่ shift แรงเมื่อ loading/result เปลี่ยน
- [ ] pagination คิด total/page ถูกต้อง

UX:

- [ ] ข้อมูลที่แสดง scan ได้ง่าย
- [ ] empty state บอกผู้ใช้ว่าควร clear/filter ใหม่อย่างไร

QA:

- [ ] ทดสอบ list มีหลายหน้า
- [ ] ทดสอบ no result
- [ ] ทดสอบ error state

## Dependencies

Blocked by:

- #66 Build Work Item List/Search/Filter API
- #72 Build Repository Page Shell & Filter UI

Blocks:

- #74 Build Work Item Detail UI
- #75 Integrate Repository UI with Real API

Related:

- #64 Build Master Data API

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

การ์ดนี้ถือว่าเสร็จเมื่อหน้า repository มี result list และ pagination ที่รองรับ contract ของ Work Item List API และพร้อมต่อเข้ากับ real API ในการ์ด integration
