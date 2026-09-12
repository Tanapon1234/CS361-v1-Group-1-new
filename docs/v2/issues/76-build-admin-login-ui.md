# [V2] Build Admin Login UI #76

## สรุป

สร้างหน้า `/admin/login` สำหรับ Admin pilot login ผ่าน Cognito และเตรียม protected admin route flow ให้การ์ด admin UI ถัดไปใช้ต่อ

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #62 แต่ GitHub issue จริงใช้ #76

## Background

V2 มี Admin pilot role เดียวคือ `ADMIN` ใช้สำหรับจัดการ repository ขั้นต้น ไม่ใช่ faculty self-service หรือ reviewer workflow

หลัง #69 ตั้งค่า Cognito/auth guard แล้ว frontend ต้องมี login UI ที่เชื่อมกับ Cognito และพาผู้ใช้เข้า admin area ได้อย่างปลอดภัย

## เป้าหมาย

สร้าง login UI ที่:

- เปิด route `/admin/login`
- ใช้ Cognito config จาก environment
- แสดง login/error/loading states
- redirect admin ที่ login สำเร็จไป `/admin/work-items`
- ป้องกัน admin pages เมื่อยังไม่ login
- ไม่เก็บ credential secret ใน frontend

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- สร้าง admin work item list/form
- ทำ role management UI
- ทำ faculty login
- ทำ reviewer/approval flow
- implement backend auth guard ใหม่

## Scope

### ต้องทำ

- เพิ่ม route `/admin/login`
- เพิ่ม auth client/provider หรือใช้ library/pattern ที่ repo เลือก
- เพิ่ม protected route helper สำหรับ admin pages
- handle login success/failure/loading
- เพิ่ม logout หรือ session clear entry point ถ้าจำเป็น
- เพิ่ม docs/env สำหรับ Cognito frontend config
- เพิ่ม tests/manual QA checklist

### ไม่ต้องทำ

- สร้าง Cognito resource ใหม่ถ้า #69 ทำแล้ว
- admin CRUD integration
- user invite/reset password flow ขั้นสูง

## UX Requirements

- หน้า login ต้องชัดเจนว่าเป็น Admin pilot
- error message ต้องช่วยแก้ปัญหาได้แต่ไม่เปิดรายละเอียด security มากเกินไป
- ถ้า already logged in ให้ redirect ไป `/admin/work-items`
- ถ้า token expired ให้กลับ login อย่างสุภาพ

## Acceptance Criteria

- [ ] `/admin/login` เปิดได้
- [ ] login ด้วย Cognito admin user ได้
- [ ] login fail แสดง error state
- [ ] login success redirect ไป `/admin/work-items`
- [ ] admin route ถูก protect เมื่อยังไม่ login
- [ ] logout/session clear ทำงานหรือมีทางออกชัดเจน
- [ ] frontend ไม่มี DB secret/AWS secret
- [ ] V1/V2 public pages ไม่ต้อง login

## Review Checklist

Frontend:

- [ ] token/session handling อยู่ในที่เหมาะสม
- [ ] protected route logic reuse ได้
- [ ] env naming ตรง docs

Security:

- [ ] ไม่ hardcode credential
- [ ] ไม่ log token ลง console
- [ ] public route ไม่ถูกบังคับ login โดยไม่ตั้งใจ

QA:

- [ ] test valid admin
- [ ] test invalid credential
- [ ] test expired/cleared session

## Dependencies

Blocked by:

- #69 Configure Admin Authentication

Blocks:

- #77 Build Admin Work Item List UI
- #78 Build Admin Create/Edit Form UI
- #79 Integrate Admin UI with Auth & CRUD API

Related:

- #81 Final Integration / Deploy / Demo Docs

## Suggested Labels

- `v2`
- `frontend`
- `admin`
- `auth`
- `ready-for-agent`

## Suggested Owner

Frontend Developer

Reviewers:

- Tech Lead
- Security Reviewer
- Backend Developer

## Estimate

0.5-1 day

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อ Admin pilot login ผ่าน Cognito ได้ มี protected route foundation และพร้อมให้ admin work item pages ต่อเข้ากับ CRUD API
