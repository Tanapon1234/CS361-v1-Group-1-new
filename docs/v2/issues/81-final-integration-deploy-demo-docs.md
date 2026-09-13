# [V2] Final Integration / Deploy / Demo Docs #81

## สรุป

รวมงาน V2 ทั้งหมดให้พร้อมส่งงานจริงบน deployed AWS-connected environment โดยตรวจ public repository, admin pilot, database state, AWS foundation, S3, V1 compatibility, evidence และเอกสาร demo/deploy/check ให้ครบ

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #67 แต่ GitHub issue จริงใช้ #81

## Production AWS Requirement

การ์ดนี้เป็น final production integration gate ของ V2 ต้องตรวจระบบที่ deploy แล้วจริง:

```text
Public flow:
Deployed frontend
→ Amazon API Gateway public routes
→ AWS Lambda read handlers
→ Amazon RDS Data API
→ Aurora PostgreSQL Serverless v2

Admin flow:
Deployed frontend
→ Amazon Cognito
→ protected API Gateway admin routes
→ Admin Lambda
→ RDS Data API transactions
→ Aurora

Supporting services:
Amazon S3 private buckets/object paths
AWS Secrets Manager
AWS IAM roles/policies
Amazon CloudWatch log groups/metrics
```

ห้ามปิดการ์ดด้วย local run, mock API, fixture response, dbdiagram, หรือ screenshot จากเครื่องอย่างเดียว ต้องมี URL/resource/evidence จาก AWS environment จริงที่ทีมใช้ส่งงาน

## Background

V2 จะถือว่าพร้อมส่งเมื่อทีมพิสูจน์ได้ว่า:

- V1 เดิมยังใช้ได้
- V2 public repository ค้นหา/กรอง/ดู detail ได้
- Admin pilot login และจัดการ work item ได้
- Aurora/Data API/Secrets/IAM/S3 foundation ใช้งานได้
- API Gateway/Lambda/Cognito เชื่อมกันครบตาม production path
- มี demo dataset ใน Aurora
- มี docs ให้เพื่อนในทีมและผู้ตรวจอ่านแล้ว run/check/demo ต่อได้

การ์ดนี้เป็น integration gate ไม่ใช่ที่สำหรับเพิ่ม feature ใหม่ก้อนใหญ่ ถ้ามี bug เล็กที่ block demo สามารถแก้ได้ แต่ถ้าเป็น capability ใหม่ควรเปิด follow-up issue แทน

## ความเกี่ยวข้องกับโจทย์

โจทย์ V2 ต้องการระบบจัดเก็บและเรียกใช้ข้อมูลอาจารย์ การสอน งานวิจัย งานบริการ การดูแลนักศึกษา และผลงาน/ภาระงานที่เกี่ยวข้องแบบเป็นระบบ รองรับหลายปีการศึกษา และค้นหา/กรอง/เรียกดูตามเงื่อนไขได้

การ์ด #81 คือหลักฐานสุดท้ายว่า V2 ตอบโจทย์จริง เพราะตรวจครบตั้งแต่:

- ข้อมูลอยู่ใน Aurora จริง
- APIs อ่าน/เขียนข้อมูลจริงผ่าน AWS
- public UI ใช้ค้นหา/กรอง/ดูรายละเอียดได้
- admin pilot ใช้จัดการข้อมูลได้
- V1 public experience ยังไม่พัง
- เอกสารส่งงานและ demo script มีพอให้ทีมอธิบายระบบได้

## เป้าหมาย

ทำ final verification และเอกสารส่งมอบ V2:

- run tests/checks หลัก
- deploy และตรวจ deployed frontend/API/backend ตาม environment ที่ทีมใช้ส่งงาน
- เก็บ evidence/screenshots/links/resource names แบบไม่เปิด secret
- เขียน demo script สำหรับนำเสนอ
- เขียน issue closing comments template
- ยืนยัน deferred/non-goals ไม่ถูกนับเป็น blocker
- update docs index/README ให้คนในทีมตามอ่านได้

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- สร้าง feature ใหม่ที่ไม่อยู่ในการ์ดก่อนหน้า
- ทำ V3 Secure Faculty Workspace
- ทำ official workload scoring/report
- ทำ faculty self-service login
- ทำ reviewer/approval workflow
- ทำ evidence file upload/download แบบ production เต็ม
- ทำ enterprise-grade monitoring ครบทุกมิติ เช่น alarm ทุก metric, synthetic monitoring, on-call workflow
- ทำ data migration จากข้อมูลจริงทั้งหมดนอก demo dataset
- เปลี่ยน schema โดยไม่มี migration card แยก

## User Stories

1. As a project evaluator, I want one deployed demo flow, so that I can verify V2 works as an integrated system.
2. As a public user, I want to browse/search/filter faculty outputs, so that I can find relevant public work items.
3. As a public user, I want to open a work item detail page, so that I can understand the selected output without seeing restricted data.
4. As an admin, I want to login through Cognito, so that admin management is protected.
5. As an admin, I want to create, edit, soft delete, and restore work items, so that the repository can be managed in the pilot system.
6. As a QA reviewer, I want API and UI smoke evidence, so that I can confirm the demo does not depend on mocks.
7. As a backend developer, I want database count checks, so that I can confirm Aurora has the expected V2 data.
8. As a security reviewer, I want public/private/admin boundary checks, so that secrets and restricted records are not exposed.
9. As a teammate, I want docs with URLs/resources/check steps, so that I can rerun the demo after the original implementer is unavailable.
10. As a maintainer, I want known limitations recorded, so that unfinished V3/V4 work is transparent and not confused with V2 bugs.

## Scope

### ต้องทำ

- ตรวจ V1 regression
- ตรวจ V2 public repository flow:
  - `/outputs`
  - search/filter/list
  - `/outputs/{id}`
- ตรวจ Admin pilot flow:
  - `/admin/login`
  - `/admin/work-items`
  - `/admin/work-items/new`
  - `/admin/work-items/{id}`
  - create/edit/soft delete/restore ถ้า route เปิดใช้
- ตรวจ database state/counts จาก Aurora
- ตรวจ AWS foundation:
  - API Gateway stages/routes
  - Lambda functions และ execution roles
  - Aurora/Data API
  - Secrets Manager
  - Cognito User Pool/App Client
  - S3 buckets/private object paths ที่เกี่ยวข้อง
  - CloudWatch log groups
  - IAM roles/policies ที่ใช้จริง
- run automated tests เท่าที่ repo มี
- run AWS smoke tests สำหรับ public/admin API paths
- บันทึก deployed frontend URL, API Gateway base URL, Cognito resource ids, Lambda names, CloudWatch log group names, Aurora cluster/database name และ S3 bucket names โดยไม่ใส่ secret value
- บันทึก known limitations และ deferred V3/V4 items
- เพิ่มหรืออัปเดต final demo docs ใน `docs/v2/`
- อัปเดต README/index ให้ชี้เอกสารล่าสุด
- เตรียม closing comment สำหรับ GitHub issues หลัก

### ไม่ต้องทำ

- rewrite architecture ใหม่
- add new auth roles/workflows
- rebuild AWS foundation จากศูนย์ ถ้า resources เดิมใช้ได้
- ทำ frontend redesign ใหญ่ที่ไม่จำเป็นต่อ demo
- เพิ่ม official report/export workflow

## Required Environment / Resource Inventory

ต้องบันทึกค่าต่อไปนี้ใน docs/evidence โดยใช้ placeholder หรือ redact ส่วนที่อ่อนไหว:

| Item | ตัวอย่าง/แหล่งที่มา | ใช้ทำอะไร |
|---|---|---|
| `FRONTEND_BASE_URL` | Vercel/deployed frontend URL | เปิด V1/V2/Admin UI |
| `API_BASE_URL` | API Gateway stage URL | smoke test public/admin APIs |
| `AWS_REGION` | `ap-southeast-1` | AWS CLI/API checks |
| CloudFormation stack | `cs361-v2-aws-foundation-dev` | หา outputs/resources |
| Aurora cluster | `cs361-v2-dev-aurora` | ตรวจ database state |
| Database name | `cs361v2` | Data API query |
| DB cluster ARN | CloudFormation output | backend-only/Data API |
| DB secret ARN | CloudFormation output | backend-only/Data API |
| Cognito User Pool ID | Cognito console/output | admin auth |
| Cognito App Client ID | Cognito console/output | frontend login |
| Lambda function names | AWS Lambda console | API handler checks |
| CloudWatch log groups | `/aws/lambda/...` | debug/evidence |
| S3 bucket names | AWS S3 console/stack output | evidence/private object boundary |

ห้ามบันทึก:

- AWS access key
- AWS secret access key
- session token
- Secrets Manager secret value
- database password
- Cognito user password
- raw JWT token

## Expected Final System State

เมื่อการ์ดนี้เสร็จ ระบบ V2 ควรมี state ประมาณนี้:

| Layer | Expected Result |
|---|---|
| Frontend | V1 pages, V2 public repository, Admin pilot pages deploy แล้ว |
| API Gateway | มี public routes และ admin protected routes |
| Lambda | read handlers/admin handlers ใช้ env/resource ถูกต้อง |
| Aurora | มี schema, master data, demo fixtures, auth/audit tables |
| Cognito | admin user login ได้และ token ใช้เรียก admin API ได้ |
| S3 | bucket/path ที่เกี่ยวข้อง private และไม่เปิด public โดยไม่ตั้งใจ |
| CloudWatch | มี logs จาก public/admin/API smoke flow |
| IAM | roles/policies ให้ Lambda และทีมทำงานพอเหมาะ |
| Docs | มีคู่มือ run/check/demo/known limitations |

## Integration Inputs จากการ์ดก่อนหน้า

การ์ดนี้ต้องรวบรวมผลจาก:

| Issue | ผลลัพธ์ที่ต้องใช้ใน #81 |
|---|---|
| #46 | scope/architecture/interface contracts ที่ freeze แล้ว |
| #47 | schema/migration/ERD/database docs |
| #48 | Aurora/Data API/Secret/IAM foundation |
| #49 | V1 to V2 data mapping |
| #50 | multi-year demo dataset |
| #64 | Master Data API |
| #66 | Work Item List/Search/Filter API |
| #67 | Faculty Work Items API |
| #68 | Work Item Detail API |
| #69 | Cognito/Admin auth boundary |
| #70 | Admin create API |
| #71 | Admin update/soft delete API |
| #72 | Repository page shell/filter UI |
| #73 | Repository result list/pagination UI |
| #74 | Work item detail UI |
| #75 | Public repository real API integration |
| #76 | Admin login UI |
| #77 | Admin work item list UI |
| #78 | Admin create/edit form UI |
| #79 | Admin UI + auth + CRUD E2E |
| #80 | Migration/import/V1 compatibility verification |

## Final Demo Flow

ใช้ flow นี้เป็น script ตอนนำเสนอ:

1. เปิด V1 `/faculties`
2. เปิด V1 `/faculties/prapaporn-rattanatamrong`
3. อธิบายว่า V1 public route ยังทำงานเหมือนเดิม
4. เปิด V2 `/outputs`
5. แสดง filter options ที่โหลดจาก Master Data API จริง
6. filter/search ด้วยคำว่า `privacy`
7. เปิด result `wi-pub-2024-privacy-edge`
8. อธิบาย category/type/period/faculty/evidence metadata
9. กลับไป `/outputs` แล้วทดสอบ filter หมวดงานอื่น
10. Login `/admin/login` ด้วย admin Cognito user
11. เปิด `/admin/work-items`
12. สร้าง work item ใหม่หนึ่งรายการสำหรับ demo
13. แก้ title/visibility/status หรือ field ที่เหมาะสม
14. soft delete รายการ demo
15. ตรวจ public `/outputs` ว่าไม่เห็นรายการที่ถูกลบหรือ restricted
16. restore ถ้า route เปิดใช้
17. เปิด CloudWatch log group ให้เห็น request flow
18. เปิด Aurora count/verification output เพื่อยืนยันว่า mutation เกิดจริง
19. สรุป known limitations และสิ่งที่ deferred ไป V3/V4

## Public Flow Smoke Matrix

ต้องทดสอบผ่าน deployed frontend และ API Gateway จริง:

| Check | URL/Action | Expected |
|---|---|---|
| V1 list page | `GET /faculties` | `200`, หน้าเดิมเปิดได้ |
| V1 detail page | `GET /faculties/prapaporn-rattanatamrong` | `200`, slug เดิมใช้ได้ |
| V1 list API | `GET /api/v1/faculties` | `200`, response shape เดิมไม่ breaking |
| V1 detail API | `GET /api/v1/faculties/prapaporn-rattanatamrong` | `200`, ไม่ต้อง login |
| V2 repository page | `GET /outputs` | filter UI โหลดได้ |
| Master data | `GET /api/v2/work-categories`, `/work-types`, `/faculties`, `/academic-periods` | `200`, options จาก Aurora |
| Work item list | `GET /api/v2/work-items` | เฉพาะ `PUBLIC + ACTIVE` |
| Search | `GET /api/v2/work-items?q=privacy` | เห็น public privacy item |
| Category filter | `GET /api/v2/work-items?category=RESEARCH` | เห็น public research/publication records |
| Restricted detail | `GET /api/v2/work-items/wi-teach-2567-2-cs333` | public-safe `404` หรือไม่ expose |
| Public detail | `GET /api/v2/work-items/wi-pub-2024-privacy-edge` | `200`, detail/evidence metadata public-safe |
| Faculty work items | `GET /api/v2/faculties/prapaporn-rattanatamrong/work-items` | public-safe list |

## Admin Flow Smoke Matrix

ต้องทดสอบด้วย Cognito admin user จริง:

| Check | Action | Expected |
|---|---|---|
| Login success | `/admin/login` ด้วย admin user | redirect ไป `/admin/work-items` |
| Login failure | password/token ผิด | error state, ไม่เปิด admin content |
| Logged out guard | เปิด `/admin/work-items` โดยไม่มี session | redirect/login required |
| Admin list | เปิด `/admin/work-items` | list จาก protected API |
| Create | submit `/admin/work-items/new` | record ถูกเขียนเข้า Aurora |
| Edit | แก้ existing work item | Aurora update จริง |
| Soft delete | soft delete record | public API ไม่แสดง record |
| Restore | restore record ถ้า route เปิดใช้ | record กลับมาตาม expected scope |
| Non-admin | token user ที่ไม่มี `ADMIN` ถ้ามี test user | `403` |
| Expired token | clear/expire session | กลับ login หรือ error สุภาพ |

## Database Verification

ต้องใช้ผลจาก #80 และแนบ summary ใน #81:

- table counts จาก Aurora
- visibility counts
- public slug compatibility
- public work item baseline
- master data counts
- demo fixture counts
- mutation result หลัง admin create/edit/delete
- audit/auth events ถ้า admin mutation flow ทำไว้แล้ว

Minimum count evidence:

```text
faculty
academic_period
evaluation_period
work_category
work_type
work_item
faculty_work_item
teaching_detail
publication_detail
research_project_detail
supervision_detail
service_detail
administration_detail
evidence_reference
app_user
app_role
app_user_role
auth_login_event
audit_event
```

## AWS Service Verification

### API Gateway

- ตรวจ stage ที่ใช้ส่งงาน
- ตรวจ public routes:
  - `/api/v2/academic-periods`
  - `/api/v2/evaluation-periods`
  - `/api/v2/work-categories`
  - `/api/v2/work-types`
  - `/api/v2/faculties`
  - `/api/v2/work-items`
  - `/api/v2/work-items/{id}`
  - `/api/v2/faculties/{slug}/work-items`
- ตรวจ admin routes:
  - `/api/v2/admin/*`
- ตรวจ CORS สำหรับ deployed frontend
- ตรวจว่า admin routes มี authorizer/guard จริง

### Lambda

- ตรวจ function names ตรง docs
- ตรวจ env vars ไม่ชี้ผิด environment
- ตรวจ execution roles
- ตรวจ CloudWatch logs หลัง smoke test
- ตรวจ error logs ไม่มี blocker สำหรับ demo path

### Aurora / RDS Data API

- ตรวจ cluster available
- ตรวจ Data API enabled
- ตรวจ `SELECT 1` ผ่าน
- ตรวจ schema/tables/data counts
- ตรวจ mutation จาก admin flow เกิดจริง

### Secrets Manager

- ตรวจ secret exists
- ตรวจ Lambda roles อ่าน secret ได้
- ห้ามเปิด secret value ใน docs/evidence

### Cognito

- ตรวจ User Pool/App Client
- ตรวจ admin user exists
- ตรวจ token ใช้เรียก admin API ได้
- ตรวจ invalid/non-admin path ได้ `401/403`

### S3

- ตรวจ bucket/path ที่เกี่ยวข้องกับ V2 evidence หรือ future evidence references
- ตรวจ Block Public Access เปิดอยู่
- ตรวจ public UI ไม่ expose private object URL ตรง ๆ
- ถ้า V2 รอบนี้ยังใช้เฉพาะ metadata/reference ไม่ได้ upload file จริง ให้บันทึก known limitation ชัดเจนว่า S3 เป็น prepared/private storage boundary ไม่ใช่ file upload feature

### IAM

- ตรวจ Lambda execution roles ใช้ policy พอดีกับงาน
- ตรวจทีมที่ต้อง deploy/check มี permission พอ
- ตรวจไม่มี broad secret exposure ใน frontend

### CloudWatch

- ตรวจ log groups ของ public/admin Lambdas
- แนบ log timestamp หรือ screenshot ที่ redact แล้ว
- ตรวจ error rate จาก demo flow ไม่มี blocker

## Automated / Manual Test Expectations

ต้องรันเท่าที่ repo มีจริง:

- frontend build/test/lint ถ้ามี script
- backend/unit tests ถ้ามี script
- API smoke scripts
- database verification scripts
- V1 compatibility smoke
- manual QA checklist สำหรับ deployed UI

ถ้ามี test บางตัวไม่มีใน repo ให้บันทึกว่า:

- ไม่มี script อะไร
- ใช้ manual verification อะไรแทน
- เปิด follow-up issue หรือไม่

## Documentation Deliverables

ต้องมีหรืออัปเดตเอกสารเหล่านี้:

| Doc | Purpose |
|---|---|
| `README.md` | หน้าแรกของ repo ชี้ V1/V2 docs ล่าสุด |
| `docs/v2/README.md` | index ของ V2 docs |
| `docs/v2/deployment-env.md` | env/resource placeholders |
| `docs/v2/aws-foundation-service-check-guide.md` | วิธีตรวจ AWS services |
| `docs/v2/demo-dataset.md` | dataset และ demo cases |
| `docs/v2/master-data-api.md` | master data endpoint guide |
| `docs/v2/data-contract.md` | API/data contract |
| `docs/v2/erd-table-attribute-guide.md` | database table/attribute guide |
| `docs/v2/team-handbook/` | วิธีเริ่มงาน branch/test/check สำหรับทีม |
| final demo/evidence note | สรุป URL/resources/check results สำหรับปิดงาน |

ถ้ามี docs ใหม่สำหรับ #81 แนะนำชื่อ:

```text
docs/v2/final-demo-checklist.md
docs/v2/final-integration-evidence.md
```

## Evidence Package ที่ควรแนบตอนปิดการ์ด

ควรมีอย่างน้อย:

- deployed frontend URL
- API Gateway base URL
- CloudFormation stack name/outputs screenshot แบบ redact
- Aurora table count output
- Data API `SELECT 1` success
- V1 route/API smoke output
- V2 public API smoke output
- V2 public UI screenshots:
  - `/outputs`
  - filtered/search result
  - `/outputs/{id}`
- Admin UI screenshots:
  - login
  - work item list
  - create/edit form
  - success/error state
- Cognito auth evidence:
  - success
  - `401`
  - `403` ถ้ามี non-admin test user
- Admin mutation evidence:
  - created record ID
  - updated field
  - soft deleted status
  - restored status ถ้าเปิดใช้
- CloudWatch log timestamp/log group names
- S3 private access/block public access evidence
- known limitations/deferred items

## Known Limitations Template

ใช้รูปแบบนี้ใน docs หรือ GitHub comment:

```text
Known limitations:
- Evidence file upload/download ยังไม่อยู่ใน V2 scope; รอบนี้เก็บ evidence metadata/reference เท่านั้น
- Faculty self-service/reviewer workflow ยังเป็น V3/V4
- Official workload scoring/report export ยังไม่อยู่ใน V2 scope
- S3 storage boundary เตรียมไว้แล้ว แต่ public UI ไม่เปิด private object โดยตรง
- Demo dataset เป็น curated multi-year dataset ไม่ใช่ migration จาก production source ทั้งหมด
```

## Suggested GitHub Closing Comment

ใช้เป็น template ตอนปิด #81:

```markdown
ปิดการ์ด #81: Final Integration / Deploy / Demo Docs

สิ่งที่ตรวจแล้ว:
- V1 public routes/API ยังใช้งานได้
- V2 public repository ใช้ deployed API Gateway/Lambda/Aurora จริง
- Master data/search/filter/detail flow ผ่าน
- Admin pilot login ผ่าน Cognito และเรียก protected API ได้
- Admin create/edit/soft delete flow เขียน Aurora จริง
- Aurora table/data verification ผ่าน
- S3/Secrets/IAM/CloudWatch checks ผ่านตาม V2 scope
- Docs/demo checklist/evidence ถูกอัปเดตแล้ว

Evidence:
- Frontend URL: <redacted-or-link>
- API Gateway URL: <redacted-or-link>
- Aurora/CloudFormation evidence: <link/screenshot>
- Smoke test output: <link/screenshot>
- Demo docs: <repo doc link>

Known limitations:
- <list deferred V3/V4 items>
```

## Final Demo Checklist

Public:

- [ ] deployed `/faculties` ยังเปิดได้
- [ ] deployed `/faculties/{slug}` ยังเปิดได้
- [ ] deployed `/outputs` เปิดได้
- [ ] filter options โหลดจาก Master Data API จริง
- [ ] search/filter ด้วย demo cases ผ่าน API Gateway/Lambda/Aurora ได้
- [ ] deployed `/outputs/{id}` detail เปิดได้
- [ ] restricted/internal data ไม่โผล่ public

Admin:

- [ ] admin login ผ่าน Cognito จริงได้
- [ ] admin list เปิดได้โดยส่ง token ไป protected AWS API
- [ ] create work item เขียน Aurora จริงได้
- [ ] edit work item แก้ Aurora จริงได้
- [ ] soft delete แล้ว public ไม่เห็น
- [ ] restore ได้ถ้า route เปิดใช้
- [ ] logged out user เข้า admin route ไม่ได้
- [ ] non-admin user ถูก block ถ้ามี test user

Cloud/Data:

- [ ] Aurora มี tables/schema ถูกต้อง
- [ ] master data seed มีข้อมูล
- [ ] demo fixture data มี counts ตาม expected
- [ ] Data API query ได้
- [ ] API Gateway routes ผูก Lambda ถูกต้อง
- [ ] Lambda handlers ใช้ role และ secret ที่ถูกต้อง
- [ ] Cognito auth ใช้กับ admin route จริง
- [ ] S3 private buckets/object paths ที่เกี่ยวข้องตรวจได้และไม่เปิด public access โดยไม่ตั้งใจ
- [ ] secrets ไม่เปิดใน repo/docs
- [ ] CloudWatch logs มี log groups ที่ expected

Docs:

- [ ] README.md ชี้ไป V2 docs ล่าสุด
- [ ] docs/v2 README/index อัปเดต
- [ ] deploy/check/demo instructions อ่านแล้วทำตามได้
- [ ] known limitations ถูกบันทึก
- [ ] issue closing comment พร้อมใช้

## Acceptance Criteria

- [ ] full V2 happy path demo ผ่านบน deployed frontend + AWS APIs จริง
- [ ] V1 compatibility checks ผ่านบน deployed routes/API จริง
- [ ] public visibility/redaction checks ผ่าน
- [ ] admin auth/CRUD checks ผ่านด้วย Cognito + protected API Gateway + Lambda + Aurora
- [ ] database verification ผ่านจาก Aurora target environment
- [ ] S3/Secrets/IAM/CloudWatch resource verification ผ่าน
- [ ] API Gateway/Lambda/CORS/env configuration ใช้งานกับ deployed frontend จริง
- [ ] docs สำหรับ run/check/demo อัปเดตพร้อม resource names/placeholders
- [ ] known limitations ถูกบันทึกและไม่ block V2 scope
- [ ] มี evidence พร้อมใช้ปิด GitHub issues
- [ ] ไม่มี secret/token/password หลุดใน repo, docs, screenshot หรือ issue comment

## Review Checklist

Tech Lead:

- [ ] ไม่มี feature scope ใหม่แอบเข้ามาใน final integration
- [ ] blockers ที่เหลือถูกจัดเป็น known limitation หรือ follow-up ชัดเจน
- [ ] issue dependency chain #46-#80 ถูกปิดหรือมีเหตุผลถ้ายังเปิด

QA:

- [ ] test evidence ครบ public/admin/data/AWS services
- [ ] manual demo script ทำตามได้
- [ ] smoke test ผ่านบน deployed environment ไม่ใช่ local/mock เท่านั้น

Security:

- [ ] secret/ARN sensitive value ไม่ถูกเปิดเกินจำเป็น
- [ ] admin-only data ไม่แสดง public
- [ ] V1 compatibility ไม่เปิดข้อมูลใหม่ผิด boundary
- [ ] S3 private access และ IAM least-privilege ถูกตรวจสำหรับ services ที่ใช้จริง
- [ ] token ไม่ถูก log หรือแปะใน evidence

Documentation:

- [ ] README/index ชี้ไฟล์ล่าสุด
- [ ] closing comment template พร้อม
- [ ] deployment/check instructions อ่านแล้วทำตามได้
- [ ] docs แยกชัดระหว่าง finished V2 scope กับ deferred work

## Dependencies

Blocked by:

- #75 Integrate Repository UI with Real API
- #79 Integrate Admin UI with Auth & CRUD API
- #80 Execute Migration & Preserve V1 Compatibility

Related:

- #46 Freeze Scope, Architecture & Interface Contracts
- #47 Design Relational Schema & SQL Migration
- #48 Provision Aurora / Data API / Secret / IAM
- #49 Define V1 to V2 Data Mapping
- #50 Prepare Multi-Year Demo Dataset
- #64 Build Master Data API
- #66 Build Work Item List/Search/Filter API
- #67 Build Faculty Work Items API
- #68 Build Work Item Detail API
- #69 Configure Admin Authentication
- #70 Build Admin Create Work Item API
- #71 Build Admin Update / Soft Delete API
- #72 Build Repository Page Shell & Filter UI
- #73 Build Repository Result List & Pagination UI
- #74 Build Work Item Detail UI
- #76 Build Admin Login UI
- #77 Build Admin Work Item List UI
- #78 Build Admin Create/Edit Form UI

## Suggested Labels

- `v2`
- `integration`
- `deploy`
- `qa`
- `documentation`
- `aws`
- `ready-for-agent`

## Suggested Owner

Tech Lead / Integration Owner

Reviewers:

- Backend Developer
- Frontend Developer
- Cloud Developer
- QA / Integration
- Security Reviewer

## Estimate

1-2 days

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อ V2 มีหลักฐานจาก deployed environment จริงว่า frontend, API Gateway, Lambda, Cognito, Aurora/Data API, Secrets Manager, S3, CloudWatch/IAM และ V1 compatibility ทำงานร่วมกันได้ครบตาม scope ที่ freeze ไว้ พร้อมเอกสาร demo/deploy/check, known limitations, และ evidence package สำหรับส่งงานและปิดชุด V2 โดยไม่มี secret value หลุดใน docs หรือ GitHub issue
