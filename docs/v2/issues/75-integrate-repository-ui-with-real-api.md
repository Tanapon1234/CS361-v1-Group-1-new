# [V2] Integrate Repository UI with Real API #75

## สรุป

เชื่อมหน้า public V2 repository (`/outputs` และ `/outputs/{id}`) กับ real V2 APIs แทน mock/fixture เพื่อให้ search/filter/list/detail ทำงาน end-to-end

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #61 แต่ GitHub issue จริงใช้ #75

## Background

การ์ด #72-#74 สร้าง UI surface ส่วน #64-#68 สร้าง read APIs การ์ดนี้คือจุดรวมที่พิสูจน์ว่า public repository ใช้งานกับข้อมูลจริงใน Aurora/API ได้ครบ flow

## เป้าหมาย

ทำให้ public V2 repository:

- โหลด master data options จาก API
- ส่ง query filter ไป `GET /api/v2/work-items`
- แสดง result list/pagination จาก real response
- เปิด detail จาก `GET /api/v2/work-items/{id}`
- handle loading/error/empty/retry
- ไม่กระทบ V1 public faculty pages

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- admin login/CRUD integration
- deploy production จริงถ้ายังอยู่ใน dev
- evidence download
- official reporting/export

## Scope

### ต้องทำ

- เพิ่ม API client/data fetching สำหรับ:
  - Master Data API จาก #64
  - Work Item List API จาก #66
  - Work Item Detail API จาก #68
- map URL query -> API query
- handle API error shape มาตรฐาน
- preserve filter/page state ระหว่าง navigation
- เพิ่ม integration tests/manual QA steps
- เพิ่ม env/config docs ถ้าต้องตั้ง `NEXT_PUBLIC_API_BASE_URL` หรือ route proxy เพิ่ม

### ไม่ต้องทำ

- admin API integration
- auth token management
- backend API implementation ใหม่

## End-to-End Scenarios

ต้อง verify อย่างน้อย:

- เปิด `/outputs` เห็น filter options
- filter category `TEACHING` แล้วเห็น teaching records
- search keyword `privacy` แล้วเห็น publication/research records ที่ public-safe
- pagination เปลี่ยนหน้าได้
- กด item แล้วเปิด `/outputs/{id}`
- refresh detail page แล้วยังโหลดข้อมูลได้
- restricted/internal records ไม่แสดงใน public UI

## Acceptance Criteria

- [ ] `/outputs` ใช้ real Master Data API สำหรับ filter options
- [ ] `/outputs` ใช้ real Work Item List API
- [ ] `/outputs/{id}` ใช้ real Detail API
- [ ] loading/error/empty states ทำงานกับ real API error
- [ ] URL query แปลงเป็น API query ถูกต้อง
- [ ] no V1 regression บน `/faculties` และ `/api/v1/faculties`
- [ ] มี QA evidence หรือ checklist สำหรับ demo dataset

## Review Checklist

Frontend:

- [ ] API client แยกจาก component พอสมควร
- [ ] cache/revalidate behavior เหมาะกับ Next.js pattern ใน repo
- [ ] error handling ไม่เปิด raw stack trace

Backend:

- [ ] API response shape ตรงกับ frontend expectation
- [ ] CORS/proxy/env path ทำงานใน local/dev

QA:

- [ ] ทดสอบ search/filter matrix จาก `docs/v2/demo-dataset.md`
- [ ] ทดสอบ restricted/internal visibility

## Dependencies

Blocked by:

- #64 Build Master Data API
- #66 Build Work Item List/Search/Filter API
- #68 Build Work Item Detail API
- #72 Build Repository Page Shell & Filter UI
- #73 Build Repository Result List & Pagination UI
- #74 Build Work Item Detail UI

Blocks:

- #81 Final Integration / Deploy / Demo Docs

Related:

- #67 Build Faculty Work Items API
- #80 Execute Migration & Preserve V1 Compatibility

## Suggested Labels

- `v2`
- `frontend`
- `integration`
- `api`
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

การ์ดนี้ถือว่าเสร็จเมื่อ public V2 repository ใช้ real API ได้ครบตั้งแต่ filter/search/list จนถึง detail และมีหลักฐานว่า V1 public pages ยังไม่พัง
