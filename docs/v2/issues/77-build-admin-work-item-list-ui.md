# [V2] Build Admin Work Item List UI #77

## สรุป

สร้างหน้า `/admin/work-items` สำหรับ Admin pilot browse/manage work items พร้อม filter, status visibility, action links และ loading/empty/error states

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #63 แต่ GitHub issue จริงใช้ #77

## Background

Admin pilot ต้องเห็นรายการ work items เพื่อเลือกแก้ไข ลบ หรือเปิดดูรายละเอียด admin ได้ แต่ต้องอยู่ใน boundary ของ V2 ไม่ใช่ระบบ workflow เต็มรูปแบบ

การ์ดนี้เน้น UI surface ก่อน integration เต็มกับ CRUD API ใน #79

## เป้าหมาย

สร้าง admin list UI ที่:

- เปิด route `/admin/work-items`
- require admin login จาก #76
- แสดง list/table ของ work items สำหรับจัดการ
- มี filter/search ที่เหมาะกับ admin
- มี action ไป edit/delete/detail
- แสดง status/visibility ให้ admin เข้าใจ
- พร้อมต่อ real CRUD API ใน #79

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- create/edit form
- connect mutation API เต็มรูปแบบ
- ทำ approval workflow
- ทำ bulk operation
- ทำ user/role management

## Scope

### ต้องทำ

- เพิ่ม route `/admin/work-items`
- protect route ด้วย admin auth helper จาก #76
- สร้าง admin work item list component
- แสดง fields สำคัญ:
  - title
  - category/type
  - academic/evaluation period
  - visibility
  - status
  - updated_at
  - primary faculty/contributors
- เพิ่ม action links:
  - New work item
  - Edit
  - View detail
  - Soft delete placeholder/action hook
- เพิ่ม loading/empty/error states
- เพิ่ม filter/search controls ขั้นต้น

### ไม่ต้องทำ

- final API integration ถ้า #79 จะทำ
- submit delete จริง
- create/edit form
- restore flow เต็ม

## Data Contract

ถ้ามี admin list endpoint ชัดเจนแล้วให้ใช้ endpoint นั้น แต่ถ้ายังไม่มี contract ให้ใช้ adapter/mock ที่ shape ใกล้กับ #66 และบันทึก open question ไว้ใน card/PR:

```text
Open question: Admin list should either reuse GET /api/v2/work-items with admin auth context or add GET /api/v2/admin/work-items for internal/restricted/deleted records.
```

ห้ามแอบเปิด internal/restricted records ผ่าน public API โดยไม่มี admin auth boundary

## Acceptance Criteria

- [ ] `/admin/work-items` เปิดได้เมื่อ login เป็น admin
- [ ] ไม่ login แล้วถูก redirect ไป `/admin/login`
- [ ] list/table แสดง work item management fields ได้
- [ ] มี search/filter UI ขั้นต้น
- [ ] มี action link ไป create/edit route
- [ ] loading/empty/error states ครบ
- [ ] ไม่ใช้ public API เพื่อเปิด internal/restricted/deleted โดยไม่มี auth

## Review Checklist

Frontend:

- [ ] admin list component แยกจาก public repository list
- [ ] action links ใช้ route ที่ตรงกับ baseline
- [ ] UI ไม่สับสนกับ public `/outputs`

Security:

- [ ] protected route ทำงานจริง
- [ ] ไม่ render admin content ก่อน auth check สำเร็จแบบเห็นข้อมูลชั่วคราว

QA:

- [ ] test logged out redirect
- [ ] test empty list
- [ ] test action links

## Dependencies

Blocked by:

- #76 Build Admin Login UI
- #71 Build Admin Update / Soft Delete API

Blocks:

- #78 Build Admin Create/Edit Form UI
- #79 Integrate Admin UI with Auth & CRUD API

Related:

- #70 Build Admin Create Work Item API

## Suggested Labels

- `v2`
- `frontend`
- `admin`
- `ui`
- `ready-for-agent`

## Suggested Owner

Frontend Developer

Reviewers:

- Tech Lead
- Backend Developer
- Security Reviewer
- QA / Integration

## Estimate

0.5-1 day

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อ Admin มีหน้า browse/manage work items ที่ protected แล้ว พร้อม action paths สำหรับ create/edit/delete และพร้อมต่อ real CRUD integration
