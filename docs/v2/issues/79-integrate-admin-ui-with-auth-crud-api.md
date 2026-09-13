# [V2] Integrate Admin UI with Auth & CRUD API #79

## สรุป

เชื่อม Admin UI กับ Cognito auth และ deployed Admin CRUD APIs จริง เพื่อให้ Admin pilot login, browse, create, edit, soft delete และ restore work items ได้ end-to-end พร้อมหลักฐานว่า mutation เขียน Aurora จริง, public repository ไม่เห็นข้อมูลที่ไม่ควรเห็น, และ CloudWatch/audit logs ตรวจสอบย้อนหลังได้

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #65 แต่ GitHub issue จริงใช้ #79

## Production AWS Requirement

การ์ดนี้เป็น admin E2E integration gate ต้องทดสอบ frontend กับ Cognito และ deployed AWS admin APIs จริง:

```text
Frontend admin deployment
→ Amazon Cognito
→ API Gateway admin routes
→ Admin Lambda + ADMIN role guard
→ RDS Data API transactions
→ Aurora PostgreSQL Serverless v2
→ CloudWatch + audit_event
```

ห้ามปิดด้วย local/mock API เท่านั้น

ต้องมีหลักฐานจาก:

- deployed frontend/admin URL
- Cognito User Pool/App Client จริง
- API Gateway admin routes จริง
- CloudWatch logs จริง
- Aurora rows จริงหลัง create/update/delete/restore
- public `/outputs` visibility check จริง

## Background

การ์ด #69-#71 สร้าง backend admin foundation:

- #69: Cognito + admin auth boundary
- #70: `POST /api/v2/admin/work-items`
- #71: `GET/PATCH/DELETE/restore /api/v2/admin/work-items/{id}`

การ์ด #76-#78 สร้าง UI surface:

- #76: `/admin/login`
- #77: `/admin/work-items`
- #78: `/admin/work-items/new` และ `/admin/work-items/{id}`

การ์ด #79 คือจุดรวมที่พิสูจน์ว่า admin pilot ใช้งานได้จริงครบ flow ไม่ใช่แค่หน้าจอหรือ API แยกกัน

## ความเกี่ยวข้องกับโจทย์

โจทย์ V2 ต้องมี Faculty Output Repository ที่ “จัดการได้” ไม่ใช่แค่ read-only การ์ดนี้พิสูจน์ฝั่งจัดการข้อมูลจริง:

- admin login อย่างปลอดภัย
- admin สร้างข้อมูลใหม่เข้า repository
- admin แก้ไขข้อมูลเดิม
- admin soft delete/restore
- public UI เห็นเฉพาะข้อมูลที่ควรเปิดเผย
- mutation มี audit trail

ถ้า #79 ไม่เสร็จ V2 จะยังขาด demo flow สำคัญของการเป็น repository ที่จัดการข้อมูลได้จริง

## เป้าหมาย

ทำให้ Admin pilot:

- login ผ่าน Cognito จริง
- เปิด `/admin/work-items`
- browse admin work item list จาก protected API
- สร้าง work item ใหม่
- แก้ work item เดิม
- soft delete work item
- restore work item ถ้า route เปิดใช้
- เห็น error/validation จาก backend อย่างเข้าใจได้
- ไม่เห็นหรือใช้ admin routes เมื่อไม่มีสิทธิ์
- ส่ง token ถูกต้องใน admin API client
- สร้าง `audit_event` จาก mutation APIs
- ทำให้ public `/outputs` ไม่เห็น `INTERNAL`, `RESTRICTED`, หรือ `DELETED`

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- user/role management UI
- faculty self-service
- reviewer workflow
- official workload approval
- evidence file upload/download
- production-grade audit dashboard
- full audit viewer
- multi-role workspace
- สร้าง API route ใหม่ที่ไม่ได้อยู่ใน contract โดยไม่บันทึก decision
- เพิ่ม schema/migration ใหม่

## User Stories

1. As an admin user, I want to log in with Cognito, so that I can access protected admin tools.
2. As an admin user, I want to browse work items, so that I can find records to manage.
3. As an admin user, I want to create a work item, so that new faculty output/workload data enters the repository.
4. As an admin user, I want to edit an existing work item, so that incorrect or incomplete data can be corrected.
5. As an admin user, I want to soft delete a work item, so that it disappears from public repository without being hard-deleted.
6. As an admin user, I want to restore a soft-deleted work item, so that accidental deletion can be recovered.
7. As an admin user, I want backend validation errors shown in the form, so that I can fix payload issues.
8. As a security reviewer, I want unauthenticated and non-admin users blocked, so that admin mutation is protected.
9. As a QA reviewer, I want deployed frontend + Cognito + AWS API evidence, so that the full admin flow is proven.
10. As a maintainer, I want Aurora and audit evidence after mutation, so that admin actions are traceable.
11. As a public user, I want public repository pages to hide deleted/restricted records, so that admin changes do not leak private data.

## Scope

### ต้องทำ

- wire Cognito token/session จาก #76 เข้า admin API client
- แยก public API client กับ admin API client ชัดเจน
- connect admin login/session flow กับ:
  - `GET /api/v2/admin/auth/check`
- connect admin list UI จาก #77 กับ:
  - `GET /api/v2/admin/work-items`
- connect admin create/edit form UI จาก #78 กับ:
  - `POST /api/v2/admin/work-items`
  - `GET /api/v2/admin/work-items/{id}`
  - `PATCH /api/v2/admin/work-items/{id}`
- connect soft delete/restore actions กับ:
  - `DELETE /api/v2/admin/work-items/{id}`
  - `POST /api/v2/admin/work-items/{id}/restore`
- handle `401`, `403`, `400`, `404`, `409`, `500`
- map backend validation errors เข้า form fields
- after create redirect ไป edit/detail/list ตาม UX ที่ทีมเลือก
- after update แสดง success และ refresh data
- after soft delete record หายจาก active list หรือแสดง `DELETED` ตาม admin filter
- after restore record กลับมา `ACTIVE`
- verify public visibility หลัง mutation:
  - `PUBLIC + ACTIVE` อ่านผ่าน public API ได้
  - `INTERNAL`, `RESTRICTED`, `DELETED` ไม่แสดงใน public `/outputs`
- add integration tests หรือ manual QA script
- update docs/env ถ้ามีค่า config เพิ่ม
- บันทึก deployed frontend/admin URL, API Gateway stage, Cognito user pool/app client ที่ใช้ทดสอบ
- ตรวจ CloudWatch logs และ Aurora result หลัง create/update/delete/restore
- ตรวจ `audit_event` หลัง create/update/delete/restore

### ไม่ต้องทำ

- สร้าง route/API ใหม่นอก contract โดยไม่บันทึก decision
- user/role management
- full audit viewer
- evidence upload/download
- scoring/report approval workflow
- bulk operation

## Integrated Endpoint Matrix

| Flow | Frontend route | API endpoint | Expected |
|---|---|---|---|
| Auth check | `/admin/login`, admin layout | `GET /api/v2/admin/auth/check` | `200` admin, `401/403` blocked |
| Admin list | `/admin/work-items` | `GET /api/v2/admin/work-items` | protected list including admin-visible statuses |
| Create | `/admin/work-items/new` | `POST /api/v2/admin/work-items` | create rows + audit event |
| Load edit | `/admin/work-items/{id}` | `GET /api/v2/admin/work-items/{id}` | load internal/restricted/deleted for admin |
| Update | `/admin/work-items/{id}` | `PATCH /api/v2/admin/work-items/{id}` | update rows + audit event |
| Soft delete | list/detail action | `DELETE /api/v2/admin/work-items/{id}` | `status = DELETED`, `deleted_at IS NOT NULL` |
| Restore | list/detail action | `POST /api/v2/admin/work-items/{id}/restore` | `status = ACTIVE`, `deleted_at IS NULL` |
| Public verify | `/outputs`, `/outputs/{id}` | `GET /api/v2/work-items`, `GET /api/v2/work-items/{id}` | enforce public visibility |

## Admin E2E Scenario

ใช้ scenario นี้เป็น baseline ปิดการ์ด:

1. Admin เปิด `/admin/login`
2. Login ผ่าน Cognito สำเร็จ
3. Frontend เรียก `GET /api/v2/admin/auth/check` ได้ `200`
4. Redirect เข้า `/admin/work-items`
5. List เรียก `GET /api/v2/admin/work-items` พร้อม token
6. Admin กด New work item
7. Create teaching work item:
   - `category_code = TEACHING`
   - `work_type_code = LECTURE`
   - `visibility = INTERNAL`
   - มี faculty contributor อย่างน้อย 1 คน
   - มี `detail.kind = teaching`
   - มี evidence metadata อย่างน้อย 1 row
8. Submit `POST /api/v2/admin/work-items`
9. Aurora มี rows ใน:
   - `work_item`
   - `faculty_work_item`
   - `teaching_detail`
   - `evidence_reference`
   - `audit_event`
10. เปิด edit page ของ record ที่สร้าง
11. แก้ title/description/visibility ด้วย `PATCH`
12. Aurora และ admin detail reflect update
13. Soft delete ด้วย `DELETE`
14. Aurora เห็น `status = DELETED`, `deleted_at IS NOT NULL`
15. Public `/outputs` และ `/outputs/{id}` ไม่เห็น deleted record
16. Restore ด้วย `POST /restore` ถ้า route เปิดใช้
17. Aurora เห็น `status = ACTIVE`, `deleted_at IS NULL`
18. ถ้า restored record เป็น `PUBLIC` จึงกลับมาเห็นใน public route ตาม visibility rule
19. Logout แล้วกลับ `/admin/work-items` ต้อง redirect `/admin/login`

## Error Handling Matrix

| Status | UI behavior |
|---|---|
| `401` | clear session/redirect `/admin/login` พร้อมข้อความ session หมดอายุ |
| `403` | show no-permission state ไม่ render admin data |
| `400` | map validation errors เข้า form field หรือ filter error |
| `404` | show not found/admin-safe state |
| `409` | show conflict/stale data message และให้ reload |
| `500` | show retry state ไม่โชว์ stack trace |

ห้ามแสดง:

- raw stack trace
- SQL error
- raw JWT token
- AWS access key/secret key
- Secrets Manager secret value
- DB secret/ARN ที่ไม่จำเป็นต่อผู้ใช้

## Backend Validation Mapping

ถ้า backend return:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid work item payload",
    "details": [
      {
        "field": "faculty[1].faculty_id",
        "message": "faculty_id does not exist"
      },
      {
        "field": "work_type_code",
        "message": "work_type_code must belong to category_code"
      }
    ]
  }
}
```

UI ต้อง:

- แสดง field error ใกล้ field ที่เกี่ยวข้อง
- แสดง form-level error ถ้า field mapping ไม่เจอ
- ไม่ discard user input หลัง validation fail
- ไม่แสดง raw backend/debug detail ที่เป็น secret

## Data Consistency Checks

หลัง mutation ต้องเช็คอย่างน้อย:

### Create

- `work_item.id` มีจริง
- `work_item.status = ACTIVE`
- `faculty_work_item` มี contributor อย่างน้อย 1 row
- subtype table ตรงกับ `detail.kind` มี row
- `evidence_reference` มี row ถ้าส่ง evidence
- `audit_event.action = WORK_ITEM_CREATED` หรือ action name ที่ backend ใช้จริง

### Update

- field ที่แก้ใน UI เปลี่ยนใน admin detail
- field ที่ไม่ได้แก้ไม่ถูกล้างโดยไม่ตั้งใจ
- `audit_event.action = WORK_ITEM_UPDATED`

### Soft Delete

- `work_item.status = DELETED`
- `work_item.deleted_at IS NOT NULL`
- `audit_event.action = WORK_ITEM_SOFT_DELETED`
- public list/detail ไม่เห็น record

### Restore

- `work_item.status = ACTIVE`
- `work_item.deleted_at IS NULL`
- `audit_event.action = WORK_ITEM_RESTORED`
- public route เห็นเฉพาะเมื่อ `visibility = PUBLIC`

## Public Visibility Regression Checks

หลัง admin mutation ต้องเช็ค:

- `PUBLIC + ACTIVE` record แสดงใน `/outputs` และ `/outputs/{id}`
- `INTERNAL` record ไม่แสดงใน public `/outputs`
- `RESTRICTED` record ไม่แสดงใน public `/outputs`
- `DELETED` record ไม่แสดงใน public list/detail
- V1 `/faculties` และ `/api/v1/faculties` ยังไม่ถูกบังคับ login

## Environment / Config

บันทึกค่า config ที่ใช้จริงโดยไม่เปิด secret:

| Config | Purpose | Secret? |
|---|---|---|
| `NEXT_PUBLIC_COGNITO_USER_POOL_ID` | Cognito admin login | no |
| `NEXT_PUBLIC_COGNITO_CLIENT_ID` | Cognito app client | no |
| `NEXT_PUBLIC_COGNITO_REGION` | AWS region | no |
| `NEXT_PUBLIC_ADMIN_API_BASE_URL` | API Gateway admin base URL | no |
| `NEXT_PUBLIC_API_BASE_URL` หรือ `NEXT_PUBLIC_V2_API_BASE_URL` | public/read API base URL ถ้าใช้แยก | no |

ห้ามใส่:

- DB secret ARN ใน frontend
- Secrets Manager secret value
- AWS access key/secret key
- raw JWT token
- Cognito temporary password

## Integration Test / Manual QA Script

อย่างน้อยต้องมี manual QA script หรือ checklist ที่ทำซ้ำได้:

```text
1. Open deployed admin URL.
2. Login with Cognito admin user.
3. Confirm /api/v2/admin/auth/check = 200.
4. Open /admin/work-items and confirm admin list loads.
5. Create a TEACHING / LECTURE work item with one faculty contributor.
6. Confirm create response and admin detail.
7. Edit title/visibility and save.
8. Confirm PATCH response and refreshed admin detail.
9. Soft delete the record.
10. Confirm active list/public /outputs no longer shows it.
11. Restore the record if route is enabled.
12. Confirm Aurora/CloudWatch/audit evidence.
13. Logout and confirm admin route redirects to login.
```

## QA Evidence ที่ต้องแนบตอนปิดการ์ด

ควรมี:

- deployed frontend/admin URL
- API Gateway base URL/stage ที่ใช้ทดสอบ
- Cognito User Pool/App Client id หรือ screenshot ที่ redact ค่าอ่อนไหว
- screenshot login success
- screenshot `/admin/work-items`
- screenshot create form submit success
- screenshot edit form submit success
- screenshot soft delete/restore state
- Network tab/log:
  - `GET /api/v2/admin/auth/check`
  - `GET /api/v2/admin/work-items`
  - `POST /api/v2/admin/work-items`
  - `GET /api/v2/admin/work-items/{id}`
  - `PATCH /api/v2/admin/work-items/{id}`
  - `DELETE /api/v2/admin/work-items/{id}`
  - `POST /api/v2/admin/work-items/{id}/restore` ถ้าเปิดใช้
- evidence ว่า request มี Authorization header โดยไม่แปะ raw token
- CloudWatch log note สำหรับ auth/list/create/update/delete/restore
- Aurora SQL/API evidence หลัง create/update/delete/restore
- `audit_event` evidence สำหรับ mutation actions
- public `/outputs` visibility check หลัง delete/restore
- V1 public route smoke note

ห้ามแนบ:

- raw JWT token
- password
- Cognito temporary password
- AWS access key/secret key
- Secrets Manager secret value

## Acceptance Criteria

- [ ] Admin login -> list -> create -> edit -> delete flow ใช้งานได้
- [ ] restore flow ใช้งานได้ถ้า endpoint เปิดใน #71
- [ ] API calls แนบ auth token ถูกต้อง
- [ ] public/admin API client แยกกันชัดเจน
- [ ] `401/403` redirect หรือแสดง message เหมาะสม
- [ ] `400/404/409/500` ถูก handle โดยไม่โชว์ raw technical detail
- [ ] backend validation errors map เข้า form ได้
- [ ] create/update/delete สร้างผลลัพธ์ใน repository จริง
- [ ] restore เปลี่ยนสถานะกลับเป็น active ได้ถ้า route เปิดใช้
- [ ] audit event เกิดจาก mutation APIs
- [ ] public UI ไม่เห็น deleted/internal/restricted data โดยไม่ตั้งใจ
- [ ] full admin flow ผ่าน deployed frontend + Cognito + AWS APIs จริง
- [ ] Aurora มีผลลัพธ์ mutation จริงหลัง create/update/delete/restore
- [ ] CloudWatch logs มีหลักฐาน auth/list/mutation flow
- [ ] logout แล้วกลับ admin route ต้องโดน redirect
- [ ] V1/V2 public pages ยังไม่ต้อง login
- [ ] มี QA evidence/checklist สำหรับ demo flow

## Review Checklist

Frontend:

- [ ] API client แยก public/admin client ชัดเจน
- [ ] token ไม่ถูก log หรือ expose
- [ ] form state refresh หลัง mutation ถูกต้อง
- [ ] list refresh หลัง create/update/delete/restore ถูกต้อง
- [ ] validation mapping ไม่ล้าง input ผู้ใช้
- [ ] loading/success/error states ใช้งานจริง
- [ ] mobile/desktop ใช้งานได้

Backend/API:

- [ ] admin endpoints รับ token/role guard ถูกต้อง
- [ ] mutation response พอให้ UI update state ได้
- [ ] `audit_event` เกิดใน transaction เดียวกับ mutation
- [ ] public routes enforce visibility/status หลัง mutation
- [ ] CORS/env ใช้งานกับ deployed frontend

Security:

- [ ] unauthenticated user เข้า admin flow ไม่ได้
- [ ] non-admin user ถูก block
- [ ] public API ไม่ถูกใช้เป็นช่องทางแก้ข้อมูล
- [ ] token/password/secret ไม่อยู่ใน logs/docs/evidence
- [ ] `SYSTEM` role ไม่ถูกใช้เป็น human admin

QA:

- [ ] test happy path ครบ
- [ ] test validation error
- [ ] test unauthorized/expired session
- [ ] test non-admin forbidden ถ้าทำได้
- [ ] test public visibility หลัง delete/restore
- [ ] test ด้วย Cognito admin user และ deployed AWS endpoints จริง

## Dependencies

Blocked by:

- #69 Configure Admin Authentication
- #70 Build Admin Create Work Item API
- #71 Build Admin Update / Soft Delete API
- #76 Build Admin Login UI
- #77 Build Admin Work Item List UI
- #78 Build Admin Create/Edit Form UI

Blocks:

- #81 Final Integration / Deploy / Demo Docs

Related:

- #64 Build Master Data API
- #75 Integrate Repository UI with Real API
- #80 Execute Migration & Preserve V1 Compatibility

## Suggested Labels

- `v2`
- `frontend`
- `backend`
- `admin`
- `integration`
- `aws`
- `ready-for-agent`

## Suggested Owner

Full-stack Developer

Reviewers:

- Tech Lead
- Security Reviewer
- Backend Developer
- QA / Integration

## Estimate

1-2 days

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อ Admin pilot ทำงานกับ repository จริงได้ end-to-end ผ่าน deployed frontend, Cognito และ AWS CRUD APIs ตั้งแต่ login/list/create/edit/soft delete/restore โดย mutation เขียน Aurora จริง มี `audit_event`, CloudWatch evidence, validation/error handling, public visibility regression checks และ security boundary ครบพอสำหรับ V2 demo
