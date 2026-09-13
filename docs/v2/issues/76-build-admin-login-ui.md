# [V2] Build Admin Login UI #76

## สรุป

สร้างหน้า `/admin/login` สำหรับ Admin pilot login ผ่าน Amazon Cognito จริง และเตรียม protected admin route foundation ให้หน้า admin ถัดไป (#77/#78/#79) ใช้ต่อได้ โดยต้องตรวจ session/token กับ protected admin endpoint จริง ไม่ใช้ mock login หรือ hardcoded token

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #62 แต่ GitHub issue จริงใช้ #76

## Production AWS Requirement

หน้า admin login ต้องใช้ Cognito User Pool/App Client จริงจาก #69:

```text
Frontend /admin/login
→ Amazon Cognito User Pool / App Client
→ token/session
→ API Gateway protected admin route
→ Admin Lambda auth guard
→ Aurora app_user/app_user_role
```

mock login, fake session, fixture user, หรือ hardcoded token ไม่ถือว่าเพียงพอสำหรับปิดการ์ดนี้

ต้องมีหลักฐานว่า admin token จาก Cognito ใช้เรียก protected AWS endpoint จริงได้อย่างน้อย:

```http
GET /api/v2/admin/auth/check
```

## Background

V2 มี Admin pilot role เดียวคือ `ADMIN` ใช้สำหรับจัดการ repository ขั้นต้น เช่น create/edit/soft delete work items ใน #70/#71 ไม่ใช่ faculty self-service, reviewer workflow หรือระบบ RBAC เต็มรูปแบบ

หลัง #69 ตั้งค่า Cognito/auth guard แล้ว frontend ต้องมี login UI ที่:

- พา admin เข้า Cognito login flow
- ได้ token/session จริง
- เช็คสิทธิ์กับ protected admin endpoint
- redirect เข้า `/admin/work-items`
- block admin route เมื่อยังไม่ login หรือไม่มีสิทธิ์

การ์ดนี้เป็น frontend auth foundation สำหรับ:

- #77 Build Admin Work Item List UI
- #78 Build Admin Create/Edit Form UI
- #79 Integrate Admin UI with Auth & CRUD API

## ความเกี่ยวข้องกับโจทย์

โจทย์ V2 ต้องมี repository ที่จัดการข้อมูลได้อย่างเป็นระบบ ไม่ใช่ public read-only อย่างเดียว ฝั่ง admin จึงต้องมีทางเข้าแบบปลอดภัยเพื่อให้ผู้ดูแลระบบเพิ่ม/แก้/ลบข้อมูลใน repository ได้

การ์ด #76 ตอบโจทย์ “ใครมีสิทธิ์เข้า admin” โดยเชื่อม frontend กับ Cognito และ admin auth boundary ของ #69 ก่อนจะไปทำ list/form/CRUD ในการ์ดถัดไป

## เป้าหมาย

สร้าง login UI ที่:

- เปิด route `/admin/login`
- ใช้ Cognito config จาก environment จริง
- รองรับ login flow ที่ปลอดภัยสำหรับ browser
- แสดง loading/error/success states
- redirect admin ที่ login สำเร็จไป `/admin/work-items`
- ตรวจ token/session กับ protected admin endpoint จริง
- ป้องกัน admin pages เมื่อยังไม่ login
- handle `401`, `403`, expired/cleared session อย่างสุภาพ
- มี logout หรือ session clear entry point
- ไม่เก็บ credential secret, DB secret หรือ AWS secret ใน frontend
- ไม่ทำให้ V1/V2 public pages ต้อง login

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- สร้าง admin work item list/table จริงของ #77
- สร้าง admin create/edit form ของ #78
- เชื่อม admin CRUD ทั้งหมดของ #79
- ทำ role management UI
- ทำ faculty login
- ทำ reviewer/approval flow
- implement backend auth guard ใหม่ของ #69
- สร้าง Cognito resource ใหม่ ถ้า #69 ทำแล้ว
- ทำ user invite/reset password flow ขั้นสูง
- ทำ MFA policy ขั้นสูง ถ้าไม่ได้อยู่ใน requirement ทีม

## User Stories

1. As an admin pilot user, I want to open `/admin/login`, so that I can sign in before managing repository data.
2. As an admin pilot user, I want to log in through Cognito, so that I do not share or store database credentials in the frontend.
3. As an admin pilot user, I want to be redirected to `/admin/work-items` after login, so that I can continue to admin work.
4. As an admin pilot user, I want clear login error messages, so that I understand when credentials/session are invalid.
5. As an admin pilot user, I want logout/session clear, so that I can safely leave the admin area.
6. As a security reviewer, I want admin pages protected, so that unauthenticated users cannot see admin content.
7. As a security reviewer, I want non-admin Cognito users blocked, so that Cognito identity alone is not enough.
8. As a frontend developer for #77/#78, I want a reusable auth client/provider, so that admin pages can attach token to API calls consistently.
9. As a QA reviewer, I want proof from Cognito and protected AWS endpoint, so that the issue is not closed with mock auth.
10. As a public visitor, I want `/faculties` and `/outputs` to remain public, so that admin auth does not break public browsing.

## Scope

### ต้องทำ

- เพิ่ม route `/admin/login`
- เลือกและ document Cognito browser login approach ที่ repo ใช้จริง:
  - recommended: Cognito Hosted UI with Authorization Code + PKCE, หรือ
  - Cognito SDK/SRP login ถ้าทีมเลือกแนวนี้
- ถ้าใช้ Hosted UI ให้เพิ่ม callback/logout handling ที่จำเป็น เช่น:
  - `/admin/auth/callback`
  - `/admin/logout`
- เพิ่ม auth client/provider/session helper สำหรับ admin UI
- เพิ่ม protected route helper สำหรับ admin pages
- admin pages ต้อง redirect ไป `/admin/login` เมื่อไม่มี session
- already logged in แล้วเข้า `/admin/login` ให้ redirect ไป `/admin/work-items`
- login success ต้องเรียก protected endpoint จริง เช่น `GET /api/v2/admin/auth/check`
- ถ้า `auth/check` ได้ `200` ให้ถือว่าเป็น valid admin session
- ถ้า `auth/check` ได้ `401` ให้ clear session และกลับ login
- ถ้า `auth/check` ได้ `403` ให้แสดงข้อความว่าไม่มีสิทธิ์ admin และไม่ให้เข้า admin area
- handle login failure/loading/expired session/cleared session
- เพิ่ม logout หรือ session clear entry point
- เพิ่ม frontend env/config docs สำหรับ Cognito
- update `frontend/.env.example` ถ้าการ์ดนี้ลงมือ implement จริง
- ผูก frontend env กับ Cognito User Pool/App Client จริงจาก #69
- ส่ง token จริงไปยัง protected API Gateway admin route
- เพิ่ม tests หรือ manual QA checklist
- verify ว่า V1/V2 public routes ยังไม่ต้อง login

### ไม่ต้องทำ

- admin work item list UI แบบเต็ม
- admin create/edit form
- admin mutation integration
- backend admin guard
- user/role management UI
- เก็บ password/session secret ใน Aurora

## Auth Flow Decision

ให้เลือกแนวทางใดแนวทางหนึ่งและบันทึกไว้ใน PR/issue comment

### Option A: Cognito Hosted UI + Authorization Code + PKCE

เหมาะสำหรับ production browser flow เพราะ frontend ไม่ต้องรับ password โดยตรง

```text
/admin/login
→ redirect to Cognito Hosted UI
→ Cognito redirects back /admin/auth/callback?code=...
→ app exchanges code with Cognito token endpoint
→ store session safely
→ call /api/v2/admin/auth/check with Bearer token
→ redirect /admin/work-items
```

ข้อกำหนด:

- Cognito App Client ต้องเป็น public client หรือไม่มี client secret สำหรับ browser flow
- callback URL ต้องตรงกับ Cognito App Client settings
- logout URL ต้องตรงกับ Cognito App Client settings
- ใช้ PKCE state/nonce เพื่อลด CSRF/session mix-up

### Option B: Cognito SDK/SRP Login

ใช้ได้ถ้าทีมต้องการ login form ในหน้า `/admin/login` เอง

```text
/admin/login form
→ Cognito SDK authenticate user
→ receive tokens
→ store session safely
→ call /api/v2/admin/auth/check with Bearer token
→ redirect /admin/work-items
```

ข้อกำหนด:

- ห้ามใช้ App Client secret ใน browser
- ห้าม log password/token ลง console
- ต้อง handle temporary password/new password challenge ถ้า Cognito user ยังอยู่ในสถานะบังคับเปลี่ยนรหัสผ่าน หรือ document ว่ายังไม่อยู่ใน scope

## Session / Token Handling

กติกาขั้นต่ำ:

- ไม่ hardcode token
- ไม่ commit token
- ไม่ log token ลง console
- ไม่ใส่ DB secret, AWS access key, Secrets Manager secret value ใน frontend
- token ที่ใช้เรียก admin API ต้องเป็น token type ที่ #69/API Gateway authorizer รองรับจริง
- ถ้าใช้ cookie ควรใช้ `HttpOnly`, `Secure`, `SameSite=Lax` หรือเข้มกว่าเมื่อ deploy production
- ถ้าใช้ browser storage ใน demo/dev ต้อง document risk และห้ามเก็บ password
- token expired ต้อง clear session แล้วพากลับ `/admin/login`
- logout ต้อง clear local/session/cookie state ที่เกี่ยวข้อง

## Environment Variables

Frontend/Admin UI env ที่ควรมี:

| Env var | ใช้ทำอะไร | Secret? |
|---|---|---|
| `NEXT_PUBLIC_COGNITO_USER_POOL_ID` | Cognito User Pool สำหรับ admin login | no |
| `NEXT_PUBLIC_COGNITO_CLIENT_ID` | Cognito App Client ID | no |
| `NEXT_PUBLIC_COGNITO_REGION` | AWS region เช่น `ap-southeast-1` | no |
| `NEXT_PUBLIC_COGNITO_DOMAIN` | Hosted UI domain ถ้าใช้ Hosted UI | no |
| `NEXT_PUBLIC_ADMIN_API_BASE_URL` | API Gateway base URL สำหรับ `/api/v2/admin/*` | no |
| `NEXT_PUBLIC_ADMIN_REDIRECT_URI` | callback URL เช่น `/admin/auth/callback` | no |
| `NEXT_PUBLIC_ADMIN_LOGOUT_URI` | logout redirect URL | no |

Backend-only values ห้ามใส่ใน `NEXT_PUBLIC_*`:

- `V2_DB_SECRET_ARN`
- Secrets Manager secret value
- AWS access key / secret key
- RDS Data API credentials
- raw JWT token
- Cognito temporary password

หมายเหตุ: `frontend/.env.example` ตอนนี้มี `NEXT_PUBLIC_API_BASE_URL` อยู่แล้ว ถ้าทีมใช้ชื่อแยกสำหรับ admin API ให้ update example ให้ชัดเจน หรือ document ว่า admin/public ใช้ base URL เดียวกัน

## Protected Admin Route Behavior

| Case | Expected UI behavior | Expected API behavior |
|---|---|---|
| เปิด `/admin/login` ยังไม่ login | แสดง login CTA/form | ไม่เรียก admin content |
| login สำเร็จและ `auth/check` ได้ `200` | redirect `/admin/work-items` | token valid + active `ADMIN` |
| already logged in เข้า `/admin/login` | redirect `/admin/work-items` | optional `auth/check` |
| เปิด `/admin/work-items` ยังไม่ login | redirect `/admin/login` | no admin API data rendered |
| token expired | clear session, redirect login พร้อมข้อความสุภาพ | `401` |
| valid Cognito แต่ไม่มี `ADMIN` role | แสดง no permission / contact admin | `403` |
| logout | clear session แล้วกลับ `/admin/login` | admin route access หลัง logout ต้องโดน redirect |

## API Contract สำหรับเช็ค Session

ใช้ protected endpoint จาก #69:

```http
GET /api/v2/admin/auth/check
Authorization: Bearer <cognito-token>
```

Response เมื่อเป็น valid admin:

```json
{
  "authenticated": true,
  "user": {
    "id": "usr_admin_suphanat",
    "email": "suphanatchanlek@gmail.com",
    "display_name": "Suphanat Chanlek",
    "roles": ["ADMIN"]
  }
}
```

UI ควรใช้ response นี้เพื่อ:

- ยืนยันว่า session เป็น admin จริง
- แสดงชื่อ admin ใน admin shell ถ้ามี
- เตรียม auth context ให้ #77/#78/#79

ห้ามใช้ response นี้เพื่อ:

- เก็บ password
- แสดง raw token
- เปิด public routes ให้ต้อง login

## Expected UI Layout

หน้า `/admin/login` ควรเรียบง่ายและชัดเจนว่าเป็น admin เท่านั้น:

```text
CS361 V2 Admin Pilot

เข้าสู่ระบบสำหรับผู้ดูแลระบบ
ใช้บัญชี admin ที่ได้รับสิทธิ์ผ่าน Amazon Cognito

[เข้าสู่ระบบด้วย Cognito]

สถานะ:
- กำลังพาไปหน้าเข้าสู่ระบบ...
- เข้าสู่ระบบไม่สำเร็จ กรุณาตรวจสอบบัญชีหรือสิทธิ์ admin
- session หมดอายุ กรุณาเข้าสู่ระบบใหม่
```

ถ้าใช้ SDK/SRP login form:

```text
อีเมล
รหัสผ่าน
[เข้าสู่ระบบ]
```

ข้อความบนหน้าไม่ควรแสดงรายละเอียดลึกเกินไป เช่น token invalid reason, Cognito internal error, stack trace หรือ request secret

## Suggested Frontend Files

ปรับตาม pattern repo ได้ แต่ควรมี responsibility ประมาณนี้:

```text
frontend/app/admin/login/page.tsx
frontend/app/admin/auth/callback/route.ts
frontend/app/admin/logout/route.ts
frontend/app/admin/layout.tsx
frontend/lib/admin-auth/config.ts
frontend/lib/admin-auth/session.ts
frontend/lib/admin-auth/client.ts
frontend/lib/admin-auth/protected-route.ts
frontend/lib/admin-api/client.ts
frontend/middleware.ts
```

หมายเหตุ:

- ถ้าไม่ได้ใช้ Hosted UI อาจไม่ต้องมี callback route
- ถ้าใช้ middleware ต้องระวังอย่า block public routes เช่น `/faculties`, `/outputs`, `/api/v1/*`, `/api/v2/work-items`
- ถ้า route protection ทำใน layout/page แทน middleware ต้องป้องกันไม่ให้ admin data render ก่อน auth check

## UX Requirements

- หน้า login ต้องชัดเจนว่าเป็น Admin pilot
- ไม่ทำให้ public user คิดว่านี่คือ faculty login
- error message ต้องช่วยแก้ปัญหาได้แต่ไม่เปิดรายละเอียด security มากเกินไป
- ถ้า already logged in ให้ redirect ไป `/admin/work-items`
- ถ้า token expired ให้กลับ login อย่างสุภาพ
- ถ้าไม่มีสิทธิ์ admin ให้บอกว่า “บัญชีนี้ไม่มีสิทธิ์ผู้ดูแลระบบ”
- logout ต้องหาเจอง่ายใน admin shell หรือมี route ชัดเจน
- loading state ต้องไม่แสดง admin content ชั่วคราวก่อน auth check ผ่าน

## QA / Smoke Test Checklist

ต้องทดสอบกับ Cognito จริงและ protected AWS endpoint จริง:

- เปิด `/admin/login` ได้
- login ด้วย Cognito admin user จริงได้
- หลัง login เรียก `GET /api/v2/admin/auth/check` พร้อม `Authorization` header จริง
- `auth/check` ได้ `200` แล้ว redirect ไป `/admin/work-items`
- เปิด `/admin/work-items` แบบไม่ login แล้วถูก redirect ไป `/admin/login`
- invalid credential หรือ login cancel แสดง error state
- cleared session/token แล้วกลับ login
- expired token ได้ `401` แล้วกลับ login
- valid Cognito user ที่ไม่มี `ADMIN` role ได้ `403` และไม่เข้า admin area
- logout แล้วเข้า admin route ไม่ได้
- public `/faculties` ยังเปิดได้โดยไม่ login
- public `/outputs` ยังเปิดได้โดยไม่ login ถ้ามี route แล้ว
- frontend ไม่มี DB secret/AWS secret/token ใน source, console log หรือ screenshot evidence

## QA Evidence ที่ต้องแนบตอนปิดการ์ด

ควรมี:

- screenshot `/admin/login`
- screenshot หลัง login สำเร็จหรือ redirect ไป `/admin/work-items`
- Network tab หรือ log ว่าเรียก Cognito จริง
- Network tab หรือ log ว่าเรียก `/api/v2/admin/auth/check` จริง
- evidence `200` valid admin โดยไม่แปะ raw token
- evidence `401` no/expired token
- evidence `403` valid Cognito but not admin ถ้าทดสอบได้
- screenshot/error state invalid login
- screenshot/logout หรือ session clear
- note ว่า public `/faculties` และ `/outputs` ยังไม่ต้อง login
- env names ที่ใช้จริง โดย redact ค่าอ่อนไหว

ห้ามแนบ:

- raw JWT token
- password
- Cognito temporary password
- AWS access key/secret key
- Secrets Manager secret value

## Acceptance Criteria

- [ ] `/admin/login` เปิดได้
- [ ] ใช้ Cognito User Pool/App Client จริงจาก AWS
- [ ] login ด้วย Cognito admin user ได้
- [ ] login fail/cancel แสดง error state
- [ ] login success เรียก protected admin endpoint จริง
- [ ] `GET /api/v2/admin/auth/check` ใช้ token จริงและได้ `200` สำหรับ admin
- [ ] login success redirect ไป `/admin/work-items`
- [ ] admin route ถูก protect เมื่อยังไม่ login
- [ ] valid Cognito user ที่ไม่มี `ADMIN` role ถูก block ด้วย `403`
- [ ] token expired/cleared session กลับ login อย่างสุภาพ
- [ ] logout/session clear ทำงานหรือมีทางออกชัดเจน
- [ ] frontend ไม่มี DB secret/AWS secret/raw token
- [ ] V1/V2 public pages ไม่ต้อง login
- [ ] env/config สำหรับ Cognito ถูก document และ update example ถ้าจำเป็น
- [ ] มี QA evidence สำหรับ valid login, invalid login, `401`, `403`, logout/cleared session

## Review Checklist

Frontend:

- [ ] auth client/provider แยกจาก component พอสมควร
- [ ] protected route logic reuse ได้ใน #77/#78/#79
- [ ] env naming ตรง docs และ #69
- [ ] loading/error states ไม่ทำให้ layout กระโดดแรง
- [ ] admin content ไม่ render ก่อน auth check ผ่าน
- [ ] token attach กับ admin API client ได้แบบ reusable

Security:

- [ ] ไม่ hardcode credential
- [ ] ไม่ log token/password ลง console
- [ ] ไม่เก็บ DB secret/AWS secret ใน frontend
- [ ] App Client สำหรับ browser flow ไม่ใช้ client secret ใน browser
- [ ] public route ไม่ถูกบังคับ login โดยไม่ตั้งใจ
- [ ] logout clear session จริง
- [ ] `SYSTEM` role ไม่ถูกใช้เป็น human admin login

QA:

- [ ] test valid admin
- [ ] test invalid credential/cancel
- [ ] test no session redirect
- [ ] test expired/cleared session
- [ ] test non-admin Cognito user หรือ mocked role failure ผ่าน real protected endpoint ถ้าทำได้
- [ ] test กับ Cognito จริง ไม่ใช่ mock auth
- [ ] test public routes หลังเพิ่ม auth middleware/helper

## Dependencies

Blocked by:

- #69 Configure Admin Authentication

Blocks:

- #77 Build Admin Work Item List UI
- #78 Build Admin Create/Edit Form UI
- #79 Integrate Admin UI with Auth & CRUD API

Related:

- #70 Build Admin Create Work Item API
- #71 Build Admin Update / Soft Delete API
- #81 Final Integration / Deploy / Demo Docs

## Suggested Labels

- `v2`
- `frontend`
- `admin`
- `auth`
- `security`
- `ready-for-agent`

## Suggested Owner

Frontend Developer

Reviewers:

- Tech Lead
- Security Reviewer
- Backend Developer
- QA / Integration

## Estimate

0.5-1 day

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อ Admin pilot login ผ่าน Cognito จริงได้ มี `/admin/login` และ protected admin route foundation ที่ใช้ token/session จริงกับ AWS protected admin endpoint, แยก `401/403/success` ได้, logout/session clear ทำงาน, public pages ยังไม่ถูกบังคับ login และมี QA evidence ที่ใช้ต่อกับ #77/#78/#79 ได้ทันที
