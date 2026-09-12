# [V2] Integrate Admin UI with Auth & CRUD API #79

## สรุป

เชื่อม Admin UI กับ Cognito auth และ Admin CRUD APIs เพื่อให้ Admin pilot login, browse, create, edit, soft delete และ restore work items ได้ end-to-end

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #65 แต่ GitHub issue จริงใช้ #79

## Production AWS Requirement

การ์ดนี้เป็น admin E2E integration gate ต้องทดสอบ frontend กับ Cognito และ deployed AWS admin APIs จริง:

```text
Frontend admin deployment
→ Cognito
→ API Gateway admin routes
→ Admin Lambda
→ RDS Data API transactions
→ Aurora
```

ห้ามปิดด้วย local/mock API เท่านั้น

## Background

การ์ด #69-#71 สร้าง backend admin foundation ส่วน #76-#78 สร้าง UI surface การ์ดนี้รวมทุกอย่างให้เป็น flow ที่ demo ได้จริง

## เป้าหมาย

ทำให้ Admin pilot:

- login ผ่าน Cognito
- เปิด `/admin/work-items`
- สร้าง work item ใหม่
- แก้ work item เดิม
- soft delete work item
- restore ถ้า route เปิดใช้
- เห็น error/validation จาก backend อย่างเข้าใจได้
- ไม่เห็นหรือใช้ admin routes เมื่อไม่มีสิทธิ์

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- user/role management UI
- faculty self-service
- reviewer workflow
- official workload approval
- evidence file upload/download
- production-grade audit dashboard

## Scope

### ต้องทำ

- wire Cognito token/session จาก #76 เข้า API client
- connect admin list/detail/form UI กับ APIs จาก #70/#71
- handle `401`, `403`, `400`, `404`, `409`, `500`
- map backend validation errors เข้า form fields
- after create redirect ไป edit/detail/list ตาม UX ที่ทีมเลือก
- after update แสดง success และ refresh data
- after soft delete record หายจาก active list หรือแสดง status ตาม admin filter
- add integration tests/manual QA script
- update docs/env ถ้ามีค่า config เพิ่ม
- บันทึก deployed frontend/admin URL, API Gateway stage และ Cognito user pool/app client ที่ใช้ทดสอบ
- ตรวจ CloudWatch logs และ Aurora result หลัง create/update/delete

### ไม่ต้องทำ

- สร้าง API route ใหม่ที่ไม่ได้อยู่ใน contract โดยไม่บันทึก decision
- full audit viewer
- multi-role workspace

## End-to-End Admin Scenarios

- Admin login สำเร็จแล้วเข้า `/admin/work-items`
- Create teaching work item พร้อม faculty contributor
- Edit visibility/title ของ work item
- Soft delete work item แล้ว public `/outputs` ไม่แสดง
- Restore work item ถ้า route เปิดใช้
- Logout แล้วกลับ admin route ต้องโดน redirect

## Acceptance Criteria

- [ ] Admin login -> list -> create -> edit -> delete flow ใช้งานได้
- [ ] API calls แนบ auth token ถูกต้อง
- [ ] `401/403` redirect หรือแสดง message เหมาะสม
- [ ] backend validation errors map เข้า form ได้
- [ ] create/update/delete สร้างผลลัพธ์ใน repository จริง
- [ ] audit event เกิดจาก mutation APIs
- [ ] public UI ไม่เห็น deleted/restricted data โดยไม่ตั้งใจ
- [ ] มี QA evidence/checklist สำหรับ demo flow
- [ ] full admin flow ผ่าน deployed frontend + Cognito + AWS APIs จริง
- [ ] Aurora มีผลลัพธ์ mutation จริงหลัง create/update/delete
- [ ] CloudWatch logs มีหลักฐาน auth/mutation flow

## Review Checklist

Frontend:

- [ ] API client แยก public/admin client ชัดเจน
- [ ] token ไม่ถูก log หรือ expose
- [ ] form state refresh หลัง mutation ถูกต้อง

Backend:

- [ ] admin endpoints รับ token/role guard ถูกต้อง
- [ ] mutation response พอให้ UI update state ได้

Security:

- [ ] unauthenticated user เข้า admin flow ไม่ได้
- [ ] non-admin user ถูก block
- [ ] public API ไม่ถูกใช้เป็นช่องทางแก้ข้อมูล

QA:

- [ ] test happy path ครบ
- [ ] test validation error
- [ ] test unauthorized/expired session
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

- #80 Execute Migration & Preserve V1 Compatibility

## Suggested Labels

- `v2`
- `frontend`
- `backend`
- `admin`
- `integration`

## Suggested Owner

Full-stack Developer

Reviewers:

- Tech Lead
- Security Reviewer
- QA / Integration

## Estimate

1-2 days

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อ Admin pilot ทำงานกับ repository จริงได้ end-to-end ผ่าน deployed frontend, Cognito และ AWS CRUD APIs โดย mutation เขียน Aurora จริง มี error handling, validation mapping, CloudWatch evidence และ security boundary ครบพอสำหรับ V2 demo
