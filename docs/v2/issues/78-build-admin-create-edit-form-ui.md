# [V2] Build Admin Create/Edit Form UI #78

## สรุป

สร้างหน้า `/admin/work-items/new` และ `/admin/work-items/{id}` สำหรับ Admin pilot create/edit work item พร้อม form validation, faculty assignment, subtype detail และ evidence metadata

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #64 ในเอกสาร design แต่ GitHub issue จริงใช้ #78 เพราะ #64 ปัจจุบันถูกใช้กับ Master Data API แล้ว

## Background

Admin Create/Update APIs จาก #70 และ #71 ต้องมี form UI ที่ช่วยให้ทีมจัดการ repository ได้จริงในการ demo V2

Form ต้องรองรับข้อมูลหลายหมวดงานโดยไม่ทำให้ผู้ใช้กรอกผิด category/type หรือ period

## เป้าหมาย

สร้าง admin form UI ที่:

- create/edit work item ได้ในระดับ UI
- ใช้ master data options จาก #64
- validate field หลักก่อน submit
- รองรับ subtype fields ตาม category/type
- รองรับ faculty contributors หลายคน
- รองรับ evidence reference metadata
- พร้อมเชื่อม API จริงใน #79

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- integrate submit API เต็มถ้า #79 แยกไว้
- evidence file upload
- official workload scoring
- approval workflow
- dynamic custom field builder

## Scope

### ต้องทำ

- เพิ่ม route `/admin/work-items/new`
- เพิ่ม route `/admin/work-items/{id}`
- form fields หลัก:
  - title
  - description
  - category
  - work type
  - visibility
  - academic period
  - evaluation period
  - dates
- faculty assignment section:
  - faculty
  - role
  - contribution order
  - contribution percent/note ถ้ามีใน contract
- subtype detail section:
  - teaching
  - publication
  - research project
  - supervision
  - service
  - administration
- evidence metadata section:
  - label
  - reference type
  - reference value
  - visibility
- client-side validation ที่สอดคล้องกับ backend
- loading/error/dirty form states

### ไม่ต้องทำ

- binary evidence upload
- hard delete
- role management
- full API submission ถ้า #79 จะทำ

## UX Requirements

- category/type เปลี่ยนแล้ว subtype fields ต้องชัดเจน
- faculty contributor rows เพิ่ม/ลบ/เรียงได้
- form ไม่ควรทำให้ผู้ใช้คิดว่ากำลังสร้าง official report
- validation error ต้องบอก field ที่ต้องแก้
- edit mode ต้องโหลด existing values ได้หรือมี placeholder adapter จนกว่า #79 เชื่อมจริง

## Acceptance Criteria

- [ ] `/admin/work-items/new` เปิดได้เฉพาะ admin
- [ ] `/admin/work-items/{id}` เปิดได้เฉพาะ admin
- [ ] form แสดง field หลักครบ
- [ ] category/type options ใช้ master data contract
- [ ] subtype fields เปลี่ยนตาม category/type
- [ ] faculty contributors รองรับหลายคน
- [ ] evidence metadata section ทำงานได้
- [ ] validation error ชัดเจน
- [ ] form payload shape ตรงกับ #70/#71

## Review Checklist

Frontend:

- [ ] form state ไม่ซับซ้อนเกินดูแล
- [ ] payload mapper แยกจาก UI component
- [ ] optional fields ไม่ทำให้ submit payload สกปรก

Backend:

- [ ] payload shape match create/update API
- [ ] validation rules ไม่ขัดกับ backend

UX:

- [ ] form ใช้งานได้จริงกับ demo dataset
- [ ] mobile/desktop ไม่ล้นจนใช้งานไม่ได้

## Dependencies

Blocked by:

- #64 Build Master Data API
- #70 Build Admin Create Work Item API
- #71 Build Admin Update / Soft Delete API
- #76 Build Admin Login UI
- #77 Build Admin Work Item List UI

Blocks:

- #79 Integrate Admin UI with Auth & CRUD API

Related:

- #68 Build Work Item Detail API

## Suggested Labels

- `v2`
- `frontend`
- `admin`
- `form`
- `ready-for-agent`

## Suggested Owner

Frontend Developer

Reviewers:

- Tech Lead
- Backend Developer
- QA / Integration

## Estimate

1-1.5 days

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อ Admin มี create/edit form ที่สร้าง payload สำหรับ V2 work item ได้ครบตาม contract พร้อม validation และพร้อมต่อ API จริงในการ์ด integration
