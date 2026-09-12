# Development Workflow And Issue Cards

ไฟล์นี้คือคู่มือทำงานราย issue card สำหรับทีม V2

## Branch Naming Standard

ใช้ branch ต่อหนึ่ง issue card:

```text
CS361-<issue-number>
```

ตัวอย่าง:

```bash
git checkout main
git pull
git checkout -b CS361-66
```

ถ้าเริ่มจาก branch integration ปัจจุบันของ V2 ให้ทีมตกลงกันก่อน เช่น `CS361-64` หรือ branch ที่ merge #64 แล้ว

ห้ามทำหลายการ์ดใหญ่ใน branch เดียว ถ้าไม่ใช่ integration card

## Basic Work Loop

ทุกคนควรทำตาม flow นี้:

1. อ่าน issue card ของตัวเองใน `docs/v2/issues/`
2. อ่าน `Blocked by` ว่าการ์ดก่อนหน้าทำเสร็จหรือยัง
3. อ่าน docs ที่เกี่ยวข้อง เช่น database/API/AWS docs
4. สร้าง branch ตามเลข issue
5. implement เฉพาะ scope ของการ์ด
6. run local tests
7. deploy/smoke test กับ AWS จริงถ้าเป็น production card
8. update docs/evidence
9. tick checklist ใน issue card docs เฉพาะข้อที่ทำจริง
10. commit และ push
11. comment หลักฐานใน GitHub issue
12. เปิด PR หรือให้ทีม review

## What Every Card Must Produce

Backend/API card ควรมี:

- Lambda handler / route logic
- repository/data access boundary
- validation and error shape
- tests
- CloudFormation/API Gateway route if needed
- deploy or update script if needed
- AWS smoke test
- docs/evidence

Frontend card ควรมี:

- usable page/component
- loading/empty/error states
- API client pointing to deployed AWS API
- tests or manual QA evidence
- screenshot/evidence where useful
- docs/env update

Database/migration card ควรมี:

- repeatable command/script
- idempotency or reset path
- Data API verification
- table counts
- compatibility evidence

Admin/auth card ควรมี:

- Cognito/admin auth integration
- role check with `app_user` / `app_user_role`
- protected API route
- 401/403/success tests
- CloudWatch/auth evidence

## Production Rule

Do not close a card with only local mock/fixture unless the card explicitly says it is a prototype.

For V2 cards:

```text
API Gateway -> Lambda -> RDS Data API -> Aurora
```

is the expected public/backend production path.

For admin:

```text
Cognito -> protected API Gateway -> Admin Lambda -> RDS Data API transaction -> Aurora
```

is expected.

## Current Card Status

Status here means repo/project status, not necessarily GitHub issue UI status.

| Issue | Title | Status | Notes |
|---:|---|---|---|
| #46 | Freeze Scope, Architecture & Interface Contracts | Done | Scope and architecture baseline exist |
| #47 | Design Relational Schema & SQL Migration | Done | SQL, ERD, DBML, table attribute guide exist |
| #48 | Provision Aurora / Data API / Secret / IAM | Done | AWS foundation deployed and documented |
| #49 | Define V1 to V2 Data Mapping | Done | Mapping docs/CSV exist |
| #50 | Prepare Multi-Year Demo Dataset | Done | Fixture dataset exists and Aurora currently has demo data |
| #64 | Build Master Data API | Done | Deployed API Gateway + Lambda + RDS Data API + Aurora; smoke test passed |
| #66 | Build Work Item List/Search/Filter API | Not done | Ready to start after #64 |
| #67 | Build Faculty Work Items API | Not done | Start after #66 |
| #68 | Build Work Item Detail API | Not done | Start after #66/#67 |
| #69 | Configure Admin Authentication | Not done | Ready to start in parallel with #66 |
| #70 | Build Admin Create Work Item API | Not done | Start after #69 |
| #71 | Build Admin Update / Soft Delete API | Not done | Start after #70 |
| #72 | Build Repository Page Shell & Filter UI | Not done | Ready to start after #64 |
| #73 | Build Repository Result List & Pagination UI | Not done | Start after #66 and #72 |
| #74 | Build Work Item Detail UI | Not done | Start after #68 and #73 |
| #75 | Integrate Repository UI with Real API | Not done | Start after #66/#68/#72/#73/#74 |
| #76 | Build Admin Login UI | Not done | Start after #69 |
| #77 | Build Admin Work Item List UI | Not done | Start after #76 and #71 |
| #78 | Build Admin Create/Edit Form UI | Not done | Start after #70/#71/#76/#77 |
| #79 | Integrate Admin UI with Auth & CRUD API | Not done | Start after #69-#78 |
| #80 | Execute Migration & Preserve V1 Compatibility | Not done | Start after #66 and #68; even though DB has data, repeatable process still needed |
| #81 | Final Integration / Deploy / Demo Docs | Not done | Last card after #75/#79/#80 |

## Recommended Parallel Work Plan

### Track A: Public API

Do first:

```text
#66 Work Item List/Search/Filter API
```

Then:

```text
#67 Faculty Work Items API
#68 Work Item Detail API
```

Why:

- #66 defines list/search validation, pagination, response shape
- #67 reuses #66 filter/pagination style but scopes by faculty
- #68 depends on list/faculty behavior and adds subtype/evidence details

### Track B: Public UI

Can start now:

```text
#72 Repository Page Shell & Filter UI
```

Then:

```text
#73 Result List & Pagination UI
#74 Work Item Detail UI
#75 Integrate Repository UI with Real API
```

Why:

- #72 can use #64 Master Data API now
- #73 waits for #66 list API
- #74 waits for #68 detail API
- #75 proves public repository works end-to-end

### Track C: Admin Backend/Auth

Can start now:

```text
#69 Configure Admin Authentication
```

Then:

```text
#70 Admin Create Work Item API
#71 Admin Update / Soft Delete API
```

Why:

- #70/#71 need a real admin identity/role boundary
- Admin mutation must write Aurora and audit events

### Track D: Admin UI

After #69:

```text
#76 Admin Login UI
```

Then after backend CRUD:

```text
#77 Admin Work Item List UI
#78 Admin Create/Edit Form UI
#79 Admin Integration
```

### Track E: Finalization

Near the end:

```text
#80 Migration & V1 Compatibility
#81 Final Integration / Demo Docs
```

## What To Read For Each Card

### #66 Work Item List/Search/Filter API

Read:

- `docs/v2/issues/66-build-work-item-list-search-filter-api.md`
- `backend/v2/query/master_data.py` for Lambda/Data API pattern
- `database/migrations/001_base.sql`
- `docs/v2/demo-dataset.md`
- `data/v2/fixtures/dataset-summary.json`

Do:

- add `GET /api/v2/work-items`
- query Aurora real `work_item` data
- filter by faculty/period/category/type/q/page
- enforce `status = ACTIVE` and `visibility = PUBLIC`
- deploy route and smoke test

### #67 Faculty Work Items API

Read:

- #67 issue file
- #66 implementation
- `faculty`, `faculty_work_item`, `work_item` schema

Do:

- add `GET /api/v2/faculties/{faculty_id}/work-items`
- support faculty id or public slug if contract decides
- reuse filters/pagination
- include faculty contribution fields

### #68 Work Item Detail API

Read:

- #68 issue file
- subtype detail tables in database guide
- evidence visibility rules

Do:

- add `GET /api/v2/work-items/{id}`
- join core work item, faculty contributors, subtype detail, evidence metadata
- enforce public visibility and safe redaction

### #69 Admin Authentication

Read:

- #69 issue file
- AWS Cognito docs in AWS console
- `app_user`, `app_role`, `app_user_role`, `auth_login_event`

Do:

- create/document Cognito User Pool/App Client
- implement token verification or API Gateway authorizer
- map Cognito user to Aurora `app_user`
- enforce active `ADMIN` role
- test 401/403/success

### #70 Admin Create Work Item API

Read:

- #70 issue file
- #69 implementation
- #64 master data validation patterns
- subtype detail tables

Do:

- add protected `POST /api/v2/admin/work-items`
- validate payload
- insert `work_item`, `faculty_work_item`, subtype detail, `evidence_reference`
- write `audit_event`
- use Data API transaction

### #71 Admin Update / Soft Delete API

Read:

- #71 issue file
- #70 transaction pattern

Do:

- implement admin detail/load/update/delete/restore routes
- update relevant subtype/evidence rows
- soft delete using `status`/`deleted_at`
- write audit events

### #72 Repository Page Shell & Filter UI

Read:

- #72 issue file
- `docs/v2/master-data-api.md`
- current frontend layout/components

Do:

- create `/outputs`
- load filter options from deployed #64 endpoint
- preserve URL query state
- show loading/error/empty states

### #73 Result List & Pagination UI

Read:

- #73 issue file
- #66 API contract

Do:

- render results from `GET /api/v2/work-items`
- support pagination/filter changes
- link to detail page

### #74 Work Item Detail UI

Read:

- #74 issue file
- #68 detail API contract

Do:

- create `/outputs/{id}`
- render detail, contributors, subtype, evidence metadata
- handle 404/restricted/public-safe state

### #75 Public Integration

Read:

- #75 issue file
- #64/#66/#68 deployed endpoints
- #72/#73/#74 UI

Do:

- wire public UI to real AWS APIs
- verify deployed frontend/API flow
- document evidence

### #76 Admin Login UI

Read:

- #76 issue file
- #69 Cognito config

Do:

- create `/admin/login`
- login through Cognito
- store/forward token safely to admin API client
- handle expired/login fail states

### #77 Admin Work Item List UI

Read:

- #77 issue file
- #71 admin list/detail route

Do:

- create `/admin/work-items`
- require admin login
- call protected admin endpoint with Cognito token
- show status/visibility/action links

### #78 Admin Create/Edit Form UI

Read:

- #78 issue file
- #64 master data endpoint
- #70/#71 admin APIs

Do:

- create `/admin/work-items/new`
- create edit route
- build form for category/type/faculty/period/subtype/evidence
- submit to real admin API

### #79 Admin Integration

Read:

- #79 issue file
- all admin cards #69-#78

Do:

- verify login/list/create/edit/delete/restore end-to-end
- record CloudWatch and Aurora evidence

### #80 Migration & V1 Compatibility

Read:

- #80 issue file
- DB/mapping/demo docs
- V1 routes/docs

Do:

- make migration/seed/import repeatable
- verify table counts
- verify V2 APIs read data
- verify V1 routes still work

### #81 Final Integration

Read:

- #81 issue file
- evidence folders
- all route/API/docs

Do:

- run final public/admin/data/AWS checks
- prepare demo script
- prepare closing comments for main issues

## Commit Message Standard

Use clear messages:

```text
feat: add V2 work item list API
feat: configure V2 admin Cognito auth
docs: add V2 migration evidence
test: add work item search smoke checks
```

Avoid vague messages:

```text
fix stuff
update
final
```

## GitHub Issue Closing Comment Pattern

Every closing comment should include:

- what was implemented
- deployed resource names/URLs if applicable
- test commands and results
- smoke test results
- evidence docs/files
- commit hash
- known limitations if any

Use `05-testing-verification-and-evidence.md` for templates.
