# [V2] Configure Admin Authentication #69

## สรุป

ตั้งค่า Admin pilot authentication ด้วย Amazon Cognito และเชื่อมกับ V2 backend เพื่อป้องกัน `/api/v2/admin/*` โดยใช้ role `ADMIN` เท่านั้น

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #55 แต่ GitHub issue จริงใช้ #69

## Production AWS Requirement

การ์ดนี้ต้องตั้งค่า Cognito และ admin auth boundary ใน AWS จริง ไม่ใช่ mock auth:

```text
Amazon Cognito User Pool / App Client
→ API Gateway authorizer หรือ Lambda token verification
→ Admin Lambda guards
→ Aurora app_user/app_user_role/auth_login_event
```

ต้องมี admin user ที่ใช้ทดสอบได้จริง, token validation จริง และ CloudWatch/auth evidence สำหรับ `401`, `403`, และ admin success

## Background

V2 มี Admin pilot สำหรับจัดการ repository ขั้นต้น แต่ยังไม่ใช่ V3 Secure Faculty Workspace เต็มรูปแบบ ดังนั้น auth boundary ต้องเรียบง่าย ชัดเจน และตรวจสอบย้อนหลังได้

Schema มี auth/audit tables แล้ว:

- `app_user`
- `app_role`
- `app_user_role`
- `auth_login_event`
- `audit_event`

V2 human login role มีเพียง `ADMIN`; ส่วน `SYSTEM` ใช้สำหรับ import/projection/migration actor เท่านั้น

## เป้าหมาย

ทำให้ backend มี auth foundation ที่:

- ใช้ Cognito สำหรับ admin login
- verify token ใน admin API
- map Cognito subject กับ `app_user`
- ตรวจ role `ADMIN`
- record login/auth events เท่าที่จำเป็น
- ไม่กระทบ public `/api/v1` และ `/api/v2` read routes

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- ทำ full RBAC หลาย role
- ทำ faculty self-service login
- ทำ reviewer/approver workflow
- ทำ user management UI
- ทำ password/session storage ใน database
- ทำ admin CRUD API

## Scope

### ต้องทำ

- สร้างหรือ document Cognito User Pool และ App Client สำหรับ Admin pilot
- เพิ่ม backend token verification utility สำหรับ `/api/v2/admin/*`
- เพิ่ม role check ว่า user มี active `ADMIN`
- เพิ่ม bootstrap/admin user mapping process ที่ปลอดภัยพอสำหรับ demo/dev
- เพิ่ม `auth_login_event` logging สำหรับ success/failure เท่าที่ route รองรับ
- configure API Gateway authorizer หรือ Lambda auth guard ให้ admin routes ใช้จริง
- sync/map Cognito user กับ `app_user` และ `app_user_role` ใน Aurora
- บันทึก CloudWatch log และ `auth_login_event` สำหรับ success/failure paths
- เพิ่ม environment variables ที่ frontend/backend ต้องใช้
- เพิ่ม tests สำหรับ unauthenticated, invalid token, non-admin, admin success
- อัปเดต docs สำหรับทีมที่ต้องสร้าง admin user

### ไม่ต้องทำ

- admin UI login page
- dynamic role assignment UI
- user invite workflow
- MFA policy ขั้นสูง ถ้าไม่ใช่ requirement ของทีม

## Expected Backend Behavior

Protected route behavior:

| Case | Expected |
|---|---|
| No token | `401` |
| Invalid/expired token | `401` |
| Valid Cognito token but no app user | `403` หรือ bootstrap ตาม policy ที่ทีมเลือก |
| Valid app user without ADMIN role | `403` |
| Valid ADMIN | allow request |

## Environment Variables

ต้องระบุชื่อ env ที่ทีมใช้จริงใน docs เช่น:

- `COGNITO_USER_POOL_ID`
- `COGNITO_APP_CLIENT_ID`
- `COGNITO_ISSUER`
- `AWS_REGION`
- `V2_DB_RESOURCE_ARN`
- `V2_DB_SECRET_ARN`

## Acceptance Criteria

- [ ] Cognito admin auth boundary ถูกสร้างหรือระบุขั้นตอนสร้างครบ
- [ ] `/api/v2/admin/*` ตรวจ token ได้
- [ ] role `ADMIN` ถูก enforce
- [ ] public V1/V2 read routes ไม่ต้อง login
- [ ] ไม่มี password/session secret ถูกเก็บใน database
- [ ] login/auth event ถูกบันทึกตามที่ออกแบบ
- [ ] มี tests สำหรับ `401`, `403`, success
- [ ] docs บอกวิธีสร้าง/เช็ค admin user ได้
- [ ] Cognito User Pool/App Client ใช้งานจริงใน AWS environment
- [ ] admin token จาก Cognito ใช้เรียก protected AWS endpoint ได้จริง
- [ ] `auth_login_event` หรือ CloudWatch evidence แสดง success/failure path

## Review Checklist

Security:

- [ ] token verification ใช้ issuer/audience ที่ถูกต้อง
- [ ] frontend ไม่เห็น DB secret หรือ AWS secret
- [ ] `SYSTEM` ไม่สามารถ login เป็น human admin

Backend:

- [ ] auth middleware/reusable guard ไม่ copy-paste ในทุก handler
- [ ] app user mapping ชัดเจนและไม่ผูกกับ email แบบเปราะ

Cloud:

- [ ] Cognito resource names/ids ถูกบันทึกใน docs/env
- [ ] IAM permissions สำหรับ Lambda พอดีกับงาน
- [ ] API Gateway/Lambda auth configuration ถูกผูกกับ admin routes จริง

## Dependencies

Blocked by:

- #47 Design Relational Schema & SQL Migration
- #48 Provision Aurora / Data API / Secret / IAM

Blocks:

- #70 Build Admin Create Work Item API
- #71 Build Admin Update / Soft Delete API
- #76 Build Admin Login UI
- #79 Integrate Admin UI with Auth & CRUD API

Related:

- #80 Execute Migration & Preserve V1 Compatibility

## Suggested Labels

- `v2`
- `auth`
- `backend`
- `aws`
- `ready-for-agent`

## Suggested Owner

Backend/Cloud Developer

Reviewers:

- Tech Lead
- Security Reviewer
- Frontend Developer

## Estimate

1 day

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อ admin API มี Cognito-backed authentication ใน AWS จริง, `ADMIN` role guard ใช้งานซ้ำได้, protected endpoint แยก `401/403/success` ได้จริง พร้อม docs/env/tests/CloudWatch evidence ที่ทีมใช้ต่อกับ admin CRUD และ admin UI ได้ทันที
