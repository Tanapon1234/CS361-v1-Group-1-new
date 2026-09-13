# [V2] Configure Admin Authentication #69

## สรุป

ตั้งค่า Admin pilot authentication ด้วย Amazon Cognito และเชื่อมกับ V2 backend เพื่อป้องกัน `/api/v2/admin/*` โดยใช้ human role เดียวคือ `ADMIN` เท่านั้น

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #55 แต่ GitHub issue จริงใช้ #69

## Production AWS Requirement

การ์ดนี้ต้องตั้งค่า Cognito และ admin auth boundary ใน AWS จริง ไม่ใช่ mock auth:

```text
Amazon Cognito User Pool / App Client
→ API Gateway v2 JWT Authorizer หรือ Lambda token verification
→ Admin Lambda reusable guard
→ Amazon RDS Data API
→ Aurora app_user/app_user_role/auth_login_event
```

ต้องมี admin user ที่ใช้ทดสอบได้จริง, token validation จริง และ CloudWatch/auth evidence สำหรับ `401`, `403`, และ admin success

## Background

V2 มี Admin pilot สำหรับจัดการ repository ขั้นต้น แต่ยังไม่ใช่ V3 Secure Faculty Workspace เต็มรูปแบบ ดังนั้น auth boundary ต้องเรียบง่าย ชัดเจน และตรวจสอบย้อนหลังได้

V2 public read APIs เช่น #64/#66/#67/#68 ไม่ต้อง login แต่ admin routes เช่น #70/#71 ต้อง protected:

```text
POST   /api/v2/admin/work-items
GET    /api/v2/admin/work-items/{id}
PATCH  /api/v2/admin/work-items/{id}
DELETE /api/v2/admin/work-items/{id}
POST   /api/v2/admin/work-items/{id}/restore
```

Schema มี auth/audit tables แล้ว:

- `app_user`
- `app_role`
- `app_user_role`
- `auth_login_event`
- `audit_event`

V2 human login role มีเพียง `ADMIN`; ส่วน `SYSTEM` ใช้สำหรับ import/projection/migration actor เท่านั้น ไม่ใช่ user ที่ login ผ่านหน้า admin

## Database Alignment Check

เช็กกับไฟล์ `database/migrations/001_base.sql`, `database/seeds/001_master_data.sql` และ Aurora dev แล้ว การ์ดนี้ต้องใช้ table/attribute ที่มีอยู่จริงดังนี้:

- `app_user`: `id`, `cognito_sub`, `email`, `display_name`, `identity_provider`, `status`, `last_login_at`, `created_at`, `updated_at`, `deleted_at`
- `app_role`: `code`, `label`, `description`, `is_active`, `created_at`, `updated_at`
- `app_user_role`: `id`, `user_id`, `role_code`, `assigned_by_user_id`, `assigned_at`, `revoked_at`, `revoke_reason`
- `auth_login_event`: `id`, `user_id`, `cognito_sub`, `email`, `login_status`, `failure_reason`, `ip_address`, `user_agent`, `request_id`, `occurred_at`
- `audit_event`: `id`, `actor_user_id`, `actor_subject`, `action`, `entity_type`, `entity_id`, `before_json`, `after_json`, `request_id`, `occurred_at`

Aurora dev live check วันที่ 2026-09-13:

| Table | Row count |
|---|---:|
| `app_role` | 2 |
| `app_user` | 0 |
| `app_user_role` | 0 |
| `auth_login_event` | 0 |
| `audit_event` | 0 |

Seeded roles ตอนนี้มี:

| Role code | Meaning | ใช้ยังไง |
|---|---|---|
| `ADMIN` | human admin pilot user | อนุญาตเรียก `/api/v2/admin/*` |
| `SYSTEM` | non-human system actor | ใช้กับ import/projection/migration/audit เท่านั้น ห้าม login เป็นคน |

ดังนั้น scope ของการ์ดนี้คือสร้าง Cognito จริงและ bootstrap `app_user` + `app_user_role` สำหรับ admin คนแรกเข้า Aurora ให้เรียบร้อย

## เป้าหมาย

ทำให้ backend มี auth foundation ที่:

- ใช้ Cognito สำหรับ admin login
- verify JWT token จาก Cognito จริง
- map Cognito `sub` กับ `app_user.cognito_sub`
- ตรวจ active `ADMIN` role ผ่าน `app_user_role`
- แยก `401` กับ `403` ได้ถูกต้อง
- บันทึก `auth_login_event` สำหรับ success/failure paths ที่ backend เห็นได้
- ไม่เก็บ password/session secret ใน database
- ไม่กระทบ public `/api/v1/*` และ public `/api/v2/*` read routes
- พร้อมให้ #70/#71 admin CRUD ใช้ reusable guard เดียวกัน

## User Stories

1. As an admin pilot user, I want to log in with Cognito, so that I can access protected admin APIs without sharing database credentials.
2. As a backend developer, I want a reusable admin auth guard, so that #70/#71 do not copy-paste token and role checks.
3. As a security reviewer, I want invalid or missing tokens to return `401`, so that unauthenticated requests are blocked clearly.
4. As a security reviewer, I want authenticated non-admin users to return `403`, so that Cognito identity alone is not enough to mutate repository data.
5. As a project maintainer, I want Cognito users mapped to `app_user`, so that admin mutations can be audited.
6. As a QA reviewer, I want CloudWatch and DB evidence for success/failure paths, so that the card can be closed with proof.
7. As a frontend developer, I want documented Cognito env values, so that #76 Admin Login UI can connect to the same User Pool/App Client.
8. As a public visitor, I want public V1/V2 read routes to stay open, so that admin auth does not break existing public behavior.

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- ทำ full RBAC หลาย role
- ทำ faculty self-service login
- ทำ reviewer/approver workflow
- ทำ user management UI
- ทำ password/session storage ใน database
- ทำ admin CRUD API เอง
- ทำ admin login UI
- ทำ user invite workflow
- ทำ advanced MFA policy ถ้าไม่ใช่ requirement ของทีม

## Architecture Decision

เนื่องจาก production API ปัจจุบันใช้ `AWS::ApiGatewayV2::Api` แบบ HTTP API ใน `infra/v2/master-data-api.yaml` baseline ที่แนะนำคือ:

```text
API Gateway v2 JWT Authorizer
→ validates Cognito issuer/audience
→ forwards verified claims to Admin Lambda
→ Admin Lambda resolves app_user by cognito_sub
→ Admin Lambda checks active ADMIN role in Aurora
```

เหตุผล:

- missing/invalid/expired token ถูก reject เป็น `401` ที่ API Gateway boundary ได้เร็ว
- Lambda ยังต้องเช็ค `app_user` และ `ADMIN` role ใน Aurora เพื่อให้ Cognito user ที่ไม่มี role ไม่ผ่าน
- #70/#71 สามารถ reuse admin guard เดียวกันได้
- public routes ไม่ต้องผูก authorizer

Fallback ที่ยอมรับได้:

- ถ้า API Gateway route setup ทำ JWT Authorizer ไม่ทัน ให้ Lambda verify JWT เองด้วย Cognito JWKS ได้ แต่ต้องยังใช้ issuer/audience จริง และต้องมี tests/evidence เหมือนกัน

## Scope

### ต้องทำ

- สร้างหรือ document Cognito User Pool สำหรับ Admin pilot
- สร้าง App Client สำหรับ Admin UI/API test โดยไม่ใช้ client secret ใน browser flow
- ตั้งค่า Cognito domain หรือ login flow ที่ทีมใช้ทดสอบ token ได้จริง
- เพิ่ม API Gateway v2 JWT Authorizer สำหรับ admin routes หรือเพิ่ม Lambda JWT verification ที่เทียบเท่า
- เพิ่ม reusable backend guard สำหรับ `/api/v2/admin/*`
- guard ต้องอ่าน claims จาก Cognito token เช่น `sub`, `email`, `username`
- guard ต้อง resolve `app_user` ด้วย `app_user.cognito_sub`
- guard ต้องตรวจ `app_user.status = ACTIVE`
- guard ต้องตรวจ active `ADMIN` role จาก `app_user_role` โดย `role_code = ADMIN` และ `revoked_at IS NULL`
- เพิ่ม bootstrap/admin user mapping process สำหรับ demo/dev
- sync/map Cognito user กับ `app_user` และ `app_user_role` ใน Aurora
- บันทึก `auth_login_event` สำหรับ success/failure paths เท่าที่ backend เห็นได้
- update `app_user.last_login_at` เมื่อ admin auth success
- เพิ่ม CloudWatch structured logs สำหรับ request id, cognito sub, auth result, role decision
- เพิ่ม environment variables ที่ frontend/backend ต้องใช้
- เพิ่ม tests สำหรับ unauthenticated, invalid token, valid non-admin, disabled user, revoked role, admin success
- เพิ่ม smoke test กับ deployed AWS endpoint จริง
- อัปเดต docs สำหรับทีมที่ต้องสร้าง/เช็ค admin user

### ไม่ต้องทำ

- สร้าง admin CRUD route จริงของ #70/#71
- สร้างหน้า `/admin/login` ของ #76
- เพิ่ม UI สำหรับ assign/revoke role
- เก็บ password, refresh token, access token หรือ session secret ใน Aurora
- เปิด admin auth ให้ public route

## AWS Resources / Configuration

ควรมี resource หรือ documented manual setup อย่างน้อย:

| Resource | Suggested name | Purpose |
|---|---|---|
| Cognito User Pool | `cs361-v2-dev-admin-users` | เก็บ admin pilot users |
| Cognito App Client | `cs361-v2-dev-admin-web` | ให้ frontend/admin test ขอ token |
| API Gateway Authorizer | `cs361-v2-dev-admin-jwt-authorizer` | verify Cognito JWT ที่ `/api/v2/admin/*` |
| Admin Lambda | `cs361-v2-dev-admin` หรือ reuse ตาม stack | protected admin routes |
| Admin Lambda role | `CS361V2AdminLambdaRole-dev` | Data API transaction + Secrets read |
| CloudWatch log group | `/aws/lambda/cs361-v2-dev-admin` | auth/admin logs |

ถ้าสร้างผ่าน CloudFormation/SAM/CDK ให้ commit template ใน `infra/v2/` และ document stack outputs เช่น:

- `CognitoUserPoolId`
- `CognitoUserPoolArn`
- `CognitoAppClientId`
- `CognitoIssuer`
- `AdminApiEndpoint`
- `AdminLambdaName`
- `AdminLogGroupName`

## Database Mapping

### `app_user`

ใช้ map Cognito identity เป็น application user:

| DB field | Source | ตัวอย่าง | หมายเหตุ |
|---|---|---|---|
| `id` | generated by bootstrap script | `usr_admin_suphanat` | stable app user id |
| `cognito_sub` | Cognito token claim `sub` | `aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee` | unique |
| `email` | Cognito token claim `email` | `suphanatchanlek@gmail.com` | optional แต่ควรมี |
| `display_name` | Cognito name/email/manual | `Suphanat Chanlek` | ใช้ใน audit/admin UI |
| `identity_provider` | constant | `COGNITO` | human admin ต้องเป็น `COGNITO` |
| `status` | bootstrap/admin process | `ACTIVE` | `SUSPENDED` ต้อง 403 |
| `last_login_at` | auth success | current timestamp | update เมื่อผ่าน guard |

### `app_user_role`

ใช้ grant role ให้ app user:

| DB field | Source | ตัวอย่าง | หมายเหตุ |
|---|---|---|---|
| `id` | generated by bootstrap script | `aur_admin_suphanat_admin` | stable id |
| `user_id` | `app_user.id` | `usr_admin_suphanat` | FK |
| `role_code` | constant | `ADMIN` | human admin เท่านั้น |
| `assigned_by_user_id` | optional | null for bootstrap | หลังมี admin UI ค่อยใช้ |
| `assigned_at` | bootstrap time | timestamp | |
| `revoked_at` | revoke process | null | active role ต้อง null |
| `revoke_reason` | revoke process | null | |

### `auth_login_event`

ใช้ record auth decisions ที่ backend เห็น:

| Case | `login_status` | `failure_reason` |
|---|---|---|
| Valid ADMIN | `SUCCESS` | null |
| Valid Cognito but no `app_user` | `FAILED` | `APP_USER_NOT_FOUND` |
| Suspended app user | `FAILED` | `APP_USER_NOT_ACTIVE` |
| No active ADMIN role | `FAILED` | `ADMIN_ROLE_REQUIRED` |
| Invalid token in Lambda verification mode | `FAILED` | `INVALID_TOKEN` |

หมายเหตุ: ถ้าใช้ API Gateway JWT Authorizer, missing/invalid/expired token อาจไม่ถึง Lambda จึงอาจไม่มี `auth_login_event` สำหรับ `401`; ต้องมี API Gateway/CloudWatch/access log evidence แทน

## Bootstrap Admin User Process

หลังสร้าง Cognito user แล้ว ให้ map user เข้าฐานข้อมูลด้วยขั้นตอนที่ reproducible และไม่ใส่ secret ลง repo

Inputs ที่ต้องใช้:

- Cognito User Pool ID
- Cognito username/email
- Cognito `sub`
- admin display name
- Aurora `DBClusterArn`
- Aurora `DBSecretArn`
- `DBName`

ตัวอย่าง DB records ที่ควรเกิด:

```sql
INSERT INTO app_user (
  id,
  cognito_sub,
  email,
  display_name,
  identity_provider,
  status
) VALUES (
  'usr_admin_<name>',
  '<cognito-sub>',
  '<admin-email>',
  '<admin-display-name>',
  'COGNITO',
  'ACTIVE'
);

INSERT INTO app_user_role (
  id,
  user_id,
  role_code
) VALUES (
  'aur_admin_<name>',
  'usr_admin_<name>',
  'ADMIN'
);
```

Implementation จริงควรทำเป็น script หรือ migration helper ที่ idempotent เช่น `ON CONFLICT` เพื่อรันซ้ำได้โดยไม่สร้าง role ซ้ำ

ห้าม commit:

- Cognito temporary password
- real token
- refresh token
- access key/secret key
- Secrets Manager secret value

## Expected Backend Behavior

Protected route behavior:

| Case | Expected | Evidence |
|---|---|---|
| No token | `401` | API Gateway response/access log |
| Invalid token | `401` | API Gateway response/access log หรือ Lambda log ถ้า verify ใน Lambda |
| Expired token | `401` | API Gateway response/access log |
| Valid Cognito token but no `app_user` | `403` | Lambda log + optional `auth_login_event` |
| Valid app user but `status != ACTIVE` | `403` | Lambda log + `auth_login_event` |
| Valid app user without active `ADMIN` role | `403` | Lambda log + `auth_login_event` |
| Valid `ADMIN` | allow request | Lambda log + `auth_login_event.SUCCESS` |

Recommended test endpoint สำหรับการ์ดนี้:

```http
GET /api/v2/admin/auth/check
```

Response สำหรับ valid admin:

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

หมายเหตุ: endpoint นี้ใช้เป็น smoke/auth check สำหรับ #69 เท่านั้น และช่วยให้ #76/#79 ตรวจ login state ได้ง่าย

## Environment Variables

Backend Lambda/admin API:

| Env var | ใช้ทำอะไร | Secret? |
|---|---|---|
| `AWS_REGION` | region ของ Cognito/Aurora | no |
| `COGNITO_USER_POOL_ID` | validate issuer / docs/debug | no |
| `COGNITO_APP_CLIENT_ID` | validate audience/client id | no |
| `COGNITO_ISSUER` | expected issuer เช่น `https://cognito-idp.ap-southeast-1.amazonaws.com/<pool-id>` | no |
| `V2_DB_RESOURCE_ARN` หรือ `DB_CLUSTER_ARN` | RDS Data API resource ARN | no แต่ไม่ควร expose frontend |
| `V2_DB_SECRET_ARN` หรือ `DB_SECRET_ARN` | Secrets Manager ARN | no value, but backend-only |
| `V2_DB_NAME` หรือ `DB_NAME` | database name | no |
| `LOG_LEVEL` | logging level | no |

Frontend/Admin UI:

| Env var | ใช้ทำอะไร | Secret? |
|---|---|---|
| `NEXT_PUBLIC_COGNITO_USER_POOL_ID` | Cognito login config | no |
| `NEXT_PUBLIC_COGNITO_CLIENT_ID` | Cognito app client id | no |
| `NEXT_PUBLIC_COGNITO_REGION` | region | no |
| `NEXT_PUBLIC_ADMIN_API_BASE_URL` | API Gateway base URL | no |

ห้ามใส่ backend-only values ใน `NEXT_PUBLIC_*`:

- DB secret ARN
- Secrets Manager secret value
- AWS access key/secret key
- RDS Data API credentials

## API Gateway / Route Rules

ต้องผูก authorizer เฉพาะ admin routes:

| Route group | Auth |
|---|---|
| `/api/v1/*` | public, no Cognito |
| `/api/v2/academic-periods` | public, no Cognito |
| `/api/v2/evaluation-periods` | public, no Cognito |
| `/api/v2/work-categories` | public, no Cognito |
| `/api/v2/work-types` | public, no Cognito |
| `/api/v2/faculties` | public, no Cognito |
| `/api/v2/work-items` | public, no Cognito |
| `/api/v2/work-items/{id}` | public, no Cognito |
| `/api/v2/faculties/{faculty_id}/work-items` | public, no Cognito |
| `/api/v2/admin/*` | Cognito JWT required + `ADMIN` role guard |

## Admin Guard Logic

Reusable guard should do this order:

1. Read verified claims from API Gateway authorizer context, or verify JWT in Lambda fallback mode.
2. Extract `sub`, `email`, and request id.
3. Query `app_user` by `cognito_sub = sub`.
4. If no active app user, log failure and return `403`.
5. Query active role:
   - `app_user_role.user_id = app_user.id`
   - `app_user_role.role_code = 'ADMIN'`
   - `app_user_role.revoked_at IS NULL`
   - `app_role.is_active = true`
6. If no active admin role, log failure and return `403`.
7. Write/update success event:
   - insert `auth_login_event`
   - update `app_user.last_login_at`
8. Return admin context to route handler:
   - `actor_user_id`
   - `actor_subject`
   - `email`
   - `roles`

Admin CRUD cards (#70/#71) must use `actor_user_id` and `actor_subject` for `audit_event`

## Database Verification / SQL Baseline

เช็ก auth table counts:

```sql
SELECT 'app_user' AS table_name, COUNT(*)::int AS row_count FROM app_user
UNION ALL SELECT 'app_role', COUNT(*)::int FROM app_role
UNION ALL SELECT 'app_user_role', COUNT(*)::int FROM app_user_role
UNION ALL SELECT 'auth_login_event', COUNT(*)::int FROM auth_login_event
UNION ALL SELECT 'audit_event', COUNT(*)::int FROM audit_event
ORDER BY table_name;
```

ก่อนทำ #69 ใน Aurora dev ตอนนี้คาดหวัง:

| Table | Expected before #69 |
|---|---:|
| `app_role` | 2 |
| `app_user` | 0 |
| `app_user_role` | 0 |
| `auth_login_event` | 0 |
| `audit_event` | 0 |

หลังทำ #69 สำเร็จ ควรเห็นอย่างน้อย:

| Table | Expected after #69 |
|---|---:|
| `app_role` | 2 |
| `app_user` | `>= 1` |
| `app_user_role` | `>= 1` |
| `auth_login_event` | `>= 1` หลัง smoke success/failure |

เช็ก admin mapping:

```sql
SELECT
  au.id,
  au.email,
  au.display_name,
  au.identity_provider,
  au.status,
  aur.role_code,
  aur.revoked_at
FROM app_user au
JOIN app_user_role aur
  ON aur.user_id = au.id
WHERE au.identity_provider = 'COGNITO'
  AND au.status = 'ACTIVE'
  AND aur.role_code = 'ADMIN'
  AND aur.revoked_at IS NULL
ORDER BY au.email;
```

เช็ก auth events:

```sql
SELECT
  login_status,
  failure_reason,
  COUNT(*)::int AS count
FROM auth_login_event
GROUP BY login_status, failure_reason
ORDER BY login_status, failure_reason;
```

## Test / Smoke Matrix

Local/unit tests:

| Case | Input | Expected |
|---|---|---|
| no token | no `Authorization` header | `401` |
| malformed token | `Authorization: Bearer bad-token` | `401` |
| valid Cognito token but no app user | real token, no DB mapping | `403` |
| suspended app user | `app_user.status = SUSPENDED` | `403` |
| no ADMIN role | app user exists, no active role | `403` |
| revoked ADMIN role | `revoked_at IS NOT NULL` | `403` |
| active ADMIN | valid token + active role | `200` |

AWS smoke tests:

- call `/api/v2/admin/auth/check` without token and capture `401`
- call `/api/v2/admin/auth/check` with invalid token and capture `401`
- call with valid Cognito token before DB role mapping and capture `403`
- call with valid admin token after DB role mapping and capture `200`
- verify CloudWatch logs show request id and auth result
- verify `auth_login_event` has success/failure rows where applicable
- verify public endpoint such as `/api/v2/work-categories` still returns `200` without token

## Evidence To Attach To GitHub Issue

หลักฐานปิดการ์ดควรมี:

- Cognito User Pool/App Client screenshots หรือ AWS CLI output ที่ redact ค่าอ่อนไหว
- API Gateway route/authorizer configuration screenshot หรือ stack output
- CloudWatch log snippets:
  - `401` no token / invalid token
  - `403` valid Cognito but not admin
  - `200` valid admin
- SQL output showing `app_user` + `app_user_role.ADMIN`
- SQL output showing `auth_login_event` success/failure count
- curl/httpie commands ที่ใช้ smoke test โดยไม่แปะ token จริง
- ยืนยันว่า public routes ยังไม่ต้อง login

ห้ามแนบ:

- raw JWT token
- Cognito temporary password
- AWS access key/secret key
- Secrets Manager secret value

## Acceptance Criteria

- [ ] Cognito User Pool/App Client สำหรับ Admin pilot ถูกสร้างหรือมีขั้นตอนสร้างครบ
- [ ] มี admin user ที่ login/get token ได้จริง
- [ ] `app_user` map กับ Cognito `sub` จริง
- [ ] `app_user_role` grant active `ADMIN` role ให้ admin user
- [ ] `/api/v2/admin/*` หรือ `/api/v2/admin/auth/check` ตรวจ token ได้
- [ ] role `ADMIN` ถูก enforce ใน Lambda reusable guard
- [ ] no token / invalid token ได้ `401`
- [ ] valid Cognito user ที่ไม่มี role ได้ `403`
- [ ] valid active `ADMIN` ได้ success
- [ ] public V1/V2 read routes ไม่ต้อง login
- [ ] ไม่มี password/session secret/token ถูกเก็บใน database หรือ docs
- [ ] `auth_login_event` หรือ CloudWatch evidence แสดง success/failure path
- [ ] docs บอกวิธีสร้าง/เช็ค admin user ได้
- [ ] Cognito resource ids/env names ถูกบันทึกโดยไม่เปิด secret
- [ ] tests ครอบคลุม `401`, `403`, success
- [ ] smoke test ผ่าน AWS endpoint จริง

## Review Checklist

Security:

- [ ] token verification ใช้ `issuer` ถูกต้อง
- [ ] token verification ใช้ `audience/client_id` ถูกต้อง
- [ ] frontend ไม่เห็น DB secret หรือ AWS secret
- [ ] `SYSTEM` ไม่สามารถ login เป็น human admin
- [ ] no token/invalid token ไม่ถึง admin mutation logic
- [ ] valid Cognito แต่ไม่มี `ADMIN` role ไม่ผ่าน
- [ ] ไม่มี raw token/password ใน logs/docs

Backend:

- [ ] auth middleware/reusable guard ไม่ copy-paste ในทุก handler
- [ ] app user mapping ใช้ `cognito_sub` เป็นหลัก ไม่ผูกกับ email อย่างเดียว
- [ ] role check ใช้ `app_user_role.revoked_at IS NULL`
- [ ] disabled/suspended user ถูก block
- [ ] `auth_login_event` insert failure/success ตามที่ backend เห็น
- [ ] admin context ส่งต่อให้ #70/#71 เพื่อเขียน `audit_event`

Cloud:

- [ ] Cognito resource names/ids ถูกบันทึกใน docs/env
- [ ] API Gateway authorizer ผูกเฉพาะ admin routes
- [ ] public routes ไม่ผูก authorizer
- [ ] IAM permissions สำหรับ Admin Lambda พอดีกับงาน
- [ ] CloudWatch logs เปิดพอ debug auth decision ได้

QA:

- [ ] smoke test `401`, `403`, `200` ผ่าน deployed endpoint
- [ ] SQL verification หลัง smoke test ผ่าน
- [ ] test token หมดอายุ/invalid signature ถ้าทำได้
- [ ] public endpoint ไม่พังหลัง deploy auth

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
- #81 Final Integration, Deploy, Demo & Docs

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
- QA / Integration

## Estimate

1-1.5 days

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อ admin API มี Cognito-backed authentication ใน AWS จริง, `/api/v2/admin/*` ถูกป้องกันด้วย JWT + reusable `ADMIN` role guard, มี admin user ที่ map กับ `app_user/app_user_role` ใน Aurora, protected endpoint แยก `401/403/success` ได้จริง, public routes ยังเปิดตามเดิม และมี docs/env/tests/CloudWatch/SQL evidence ที่ทีมใช้ต่อกับ admin CRUD และ admin UI ได้ทันที
