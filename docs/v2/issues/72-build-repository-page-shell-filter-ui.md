# [V2] Build Repository Page Shell & Filter UI #72

## สรุป

สร้างหน้า `/outputs` สำหรับ V2 Faculty Output Repository พร้อม layout, filter controls, loading/empty/error states และ URL query state โดยยังไม่ต้องผูก real result list แบบเต็ม

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #58 แต่ GitHub issue จริงใช้ #72

## Production AWS Requirement

หน้า `/outputs` ต้องใช้ Master Data API จาก #64 ที่ deploy บน AWS จริงสำหรับ filter options:

```text
Frontend
→ deployed API Gateway URL
→ Lambda
→ RDS Data API
→ Aurora
```

fixture/mock ใช้ได้เฉพาะ component test เท่านั้น ไม่ถือว่าเพียงพอสำหรับปิดการ์ดนี้

## Background

V1 มีหน้า faculty directory เป็นหลัก แต่ V2 ต้องมี repository browsing experience สำหรับค้นหา/กรองผลงานและภาระงานหลายปี

หน้า `/outputs` จะเป็น entry point ของ public V2 repository และต้องใช้ master data จาก #64 เพื่อทำ dropdown/filter ที่ consistent กับ backend

## เป้าหมาย

สร้าง UI shell ที่:

- เปิด route `/outputs`
- มี filter controls สำหรับ year/period/category/type/faculty/search
- sync filter state กับ URL query
- มี responsive layout สำหรับ desktop/mobile
- เตรียมพื้นที่ result list/pagination ให้ #73 ใช้ต่อ
- ไม่กระทบ V1 routes `/faculties`

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- render result list จริงแบบครบ
- integrate `GET /api/v2/work-items` เต็มรูปแบบ
- ทำ detail page
- ทำ admin UI
- ทำ auth

## Scope

### ต้องทำ

- เพิ่ม route/page `/outputs`
- เพิ่ม filter UI:
  - keyword search
  - academic period
  - evaluation period ถ้าเหมาะกับ UX
  - work category
  - work type
  - faculty
- ใช้ deployed Master Data API จาก #64 สำหรับ options
- เพิ่ม frontend env/config สำหรับ API Gateway base URL ตามที่ deploy จริง
- handle loading/error จาก AWS endpoint จริง
- เมื่อเลือก filter ให้ update URL query อย่าง predictable
- เพิ่ม loading/empty/error placeholder states
- เพิ่ม navigation entry ถ้าเข้ากับ design ของ frontend
- เพิ่ม basic tests หรือ component/story/manual QA checklist ตาม pattern repo

### ไม่ต้องทำ

- result cards/table แบบ final
- pagination behavior จริง
- admin route

## UX Requirements

- ผู้ใช้ต้องเข้าใจทันทีว่าหน้านี้คือ repository ผลงาน/ภาระงานอาจารย์
- filter ต้องไม่แน่นหรือซับซ้อนเกินไปบน mobile
- category/type ควรสัมพันธ์กัน: เลือก category แล้ว type options ควรถูกกรอง
- URL query ต้อง share/reload แล้ว state ยังอยู่
- empty/loading/error state ต้องไม่ทำ layout กระโดดแรง

## Acceptance Criteria

- [ ] `/outputs` เปิดได้
- [ ] มี filter controls ครบตาม scope
- [ ] filter state sync กับ URL query
- [ ] options ใช้ข้อมูลจาก deployed Master Data API จริง
- [ ] responsive layout ใช้งานได้บน mobile/desktop
- [ ] V1 `/faculties` และ `/faculties/{id}` ไม่พัง
- [ ] มี placeholder สำหรับ result list/pagination ให้ #73 ต่อได้
- [ ] มี QA evidence ว่า `/outputs` โหลด filter options จาก AWS endpoint ได้

## Review Checklist

Frontend:

- [ ] component structure อ่านง่ายและ reuse ต่อได้
- [ ] ไม่มี hardcoded demo-only labels เกินจำเป็น
- [ ] URL query parsing/serialization stable

UX:

- [ ] mobile ไม่ล้นจอ
- [ ] filter labels เข้าใจง่าย
- [ ] loading/empty/error states ชัดเจน

QA:

- [ ] reload URL ที่มี query แล้วยังเห็น filter state เดิม
- [ ] reset filter ทำงานถูกต้อง
- [ ] ปิด mock/fixture แล้วหน้ายังโหลด filter options จาก AWS ได้

## Dependencies

Blocked by:

- #64 Build Master Data API

Blocks:

- #73 Build Repository Result List & Pagination UI
- #75 Integrate Repository UI with Real API

Related:

- #66 Build Work Item List/Search/Filter API
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

การ์ดนี้ถือว่าเสร็จเมื่อมีหน้า `/outputs` ที่เป็น shell ของ V2 repository พร้อม filter UI, URL state และ filter options ที่โหลดจาก deployed AWS Master Data API จริง พร้อม evidence ว่า V1 routes ไม่พัง
