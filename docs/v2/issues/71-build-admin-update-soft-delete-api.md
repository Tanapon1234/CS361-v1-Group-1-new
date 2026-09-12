# [V2] Build Admin Update / Soft Delete API #71

## สรุป

สร้าง Admin API สำหรับดู แก้ไข soft delete และ restore work item ใน V2 repository โดย `DELETE` ต้องไม่ลบข้อมูลถาวร

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #57 แต่ GitHub issue จริงใช้ #71

## Background

Admin pilot ต้องจัดการข้อมูลที่ถูกเพิ่มหรือ import เข้ามาได้ แต่ V2 ต้องรักษาประวัติและ audit trail จึงห้าม hard delete เป็น default

Baseline admin routes:

```http
GET    /api/v2/admin/work-items/{id}
PATCH  /api/v2/admin/work-items/{id}
DELETE /api/v2/admin/work-items/{id}
POST   /api/v2/admin/work-items/{id}/restore
```

## เป้าหมาย

สร้าง mutation API ที่:

- require `ADMIN`
- แก้ข้อมูลกลางและ relation ที่จำเป็นได้
- soft delete ด้วย `status = DELETED` และ `deleted_at`
- restore optional ตาม route baseline
- record audit event ทุก action
- ไม่กระทบ public read API แบบไม่ตั้งใจ

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- สร้าง admin UI
- ทำ approval workflow
- ทำ hard delete
- ทำ evidence file upload/delete
- ทำ full audit viewer
- ทำ dynamic RBAC

## Scope

### ต้องทำ

- implement `GET /api/v2/admin/work-items/{id}`
- implement `PATCH /api/v2/admin/work-items/{id}`
- implement `DELETE /api/v2/admin/work-items/{id}` เป็น soft delete
- implement `POST /api/v2/admin/work-items/{id}/restore` ถ้าทีมเปิด restore ใน V2
- PATCH ต้องรองรับ field หลัก:
  - title/description/date
  - visibility
  - academic/evaluation period
  - faculty contributors
  - subtype detail
  - evidence references metadata
- update `updated_at`, `updated_by`, `deleted_at`
- record `audit_event`
- add tests สำหรับ auth, validation, soft delete, restore, not found

### ไม่ต้องทำ

- list endpoint สำหรับ admin ถ้ายังไม่มี contract ชัดเจน
- user management
- evidence binary management

## API Contract

```http
PATCH /api/v2/admin/work-items/{id}
Authorization: Bearer <admin-token>
```

Response:

```json
{
  "id": "wi-teach-2567-2-cs333",
  "status": "ACTIVE",
  "message": "updated"
}
```

Soft delete:

```http
DELETE /api/v2/admin/work-items/{id}
Authorization: Bearer <admin-token>
```

Response:

```json
{
  "id": "wi-teach-2567-2-cs333",
  "status": "DELETED",
  "message": "soft_deleted"
}
```

Restore:

```http
POST /api/v2/admin/work-items/{id}/restore
Authorization: Bearer <admin-token>
```

## Rules

- `DELETE` ต้องไม่ hard delete
- public read API ต้องไม่ return `status = DELETED`
- PATCH ต้อง validate category/type consistency เหมือน create API
- ถ้า PATCH replace contributors ต้องทำแบบ transaction-safe
- audit event ต้องบอก action เช่น `WORK_ITEM_UPDATED`, `WORK_ITEM_SOFT_DELETED`, `WORK_ITEM_RESTORED`
- restore ต้อง clear `deleted_at` และ set `status = ACTIVE`

## Acceptance Criteria

- [ ] admin detail endpoint return record ได้รวม internal/restricted ตามสิทธิ์ admin
- [ ] PATCH update field หลักได้
- [ ] DELETE ทำ soft delete ไม่ hard delete
- [ ] restore ทำงานถ้าเปิดใช้
- [ ] public API ไม่แสดง deleted record
- [ ] mutation ทุกครั้งมี audit event
- [ ] unauthorized/non-admin ถูกปฏิเสธ
- [ ] tests ครอบคลุม validation และ transaction rollback

## Review Checklist

Backend:

- [ ] patch logic ไม่เขียนทับ field ที่ไม่ได้ส่งมาโดยไม่ตั้งใจ
- [ ] relation update ใช้ transaction
- [ ] updated/deleted metadata ถูกต้อง

Security:

- [ ] route ทั้งหมด require ADMIN
- [ ] admin response ไม่เปิด secret ที่ไม่จำเป็น

QA:

- [ ] สร้างจาก #70 แล้ว update/delete/restore ต่อได้
- [ ] deleted record หายจาก public list/detail

## Dependencies

Blocked by:

- #69 Configure Admin Authentication
- #70 Build Admin Create Work Item API

Blocks:

- #77 Build Admin Work Item List UI
- #78 Build Admin Create/Edit Form UI
- #79 Integrate Admin UI with Auth & CRUD API

Related:

- #68 Build Work Item Detail API
- #80 Execute Migration & Preserve V1 Compatibility

## Suggested Labels

- `v2`
- `backend`
- `admin`
- `api`
- `ready-for-agent`

## Suggested Owner

Backend Developer

Reviewers:

- Tech Lead
- Security Reviewer
- QA / Integration

## Estimate

1-1.5 days

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อ Admin สามารถดู แก้ไข soft delete และ restore work item ได้อย่างปลอดภัย มี audit trail และ public API ไม่เห็น record ที่ถูกลบ
