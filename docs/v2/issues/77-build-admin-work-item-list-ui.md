# [V2] Build Admin Work Item List UI #77

## สรุป

สร้างหน้า `/admin/work-items` สำหรับ Admin pilot ใช้ browse/manage work items ใน repository โดยต้อง protected ด้วย Cognito admin session จาก #76 และอ่านข้อมูลจาก protected Admin API จริง ไม่ใช้ public API เพื่อแอบเปิดข้อมูล `INTERNAL`, `RESTRICTED` หรือ `DELETED`

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #63 แต่ GitHub issue จริงใช้ #77

## Production AWS Requirement

หน้า admin work item list ต้องใช้ admin API ที่ protected ด้วย Cognito จริงและอ่าน Aurora จริง:

```text
Frontend /admin/work-items
→ Cognito token/session จาก #76
→ API Gateway admin route
→ Admin Lambda + ADMIN role guard จาก #69
→ RDS Data API
→ Aurora PostgreSQL Serverless v2
```

adapter/mock ใช้ได้เฉพาะ component test เท่านั้น ไม่ถือว่าเพียงพอสำหรับปิดการ์ดนี้

ต้องส่ง token จริงไปยัง admin endpoint:

```http
Authorization: Bearer <cognito-token>
```

## Background

Admin pilot ต้องเห็นรายการ work items เพื่อเลือกดูรายละเอียดแบบ admin, แก้ไข, soft delete หรือเปิดหน้า create/edit ในการ์ดถัดไป แต่ยังอยู่ใน boundary ของ V2 ไม่ใช่ workflow ใหญ่แบบ approval/reviewer หรือ faculty self-service

การ์ดนี้อยู่ระหว่าง:

- #76: login/protected route foundation
- #70: create work item API
- #71: admin detail/update/soft delete/restore API
- #78: admin create/edit form UI
- #79: admin end-to-end integration

ดังนั้น #77 ต้องสร้างหน้า list ที่ admin ใช้งานได้จริงและต่อทางให้การ์ด #78/#79 โดยไม่ทำ form/mutation เต็มเอง

## ความเกี่ยวข้องกับโจทย์

โจทย์ V2 ต้องมี repository ที่จัดการข้อมูลได้อย่างเป็นระบบ ไม่ใช่แค่ public read-only การ์ด #77 คือหน้า “หลังบ้าน” ที่ให้ admin เห็นข้อมูลทั้งหมดที่ต้องจัดการ เช่น `PUBLIC`, `INTERNAL`, `RESTRICTED`, `ACTIVE`, และ `DELETED` เพื่อดูสถานะและไปแก้ไขต่อได้

ต่างจาก public `/outputs`:

- public `/outputs` เห็นเฉพาะข้อมูลที่เปิดเผยได้
- admin `/admin/work-items` เห็นข้อมูลสำหรับจัดการภายใน หลังผ่าน Cognito + `ADMIN` role guard เท่านั้น

## เป้าหมาย

สร้าง admin list UI ที่:

- เปิด route `/admin/work-items`
- require admin login จาก #76
- แสดง list/table ของ work items สำหรับจัดการ
- ใช้ protected Admin API จริง
- ส่ง Cognito token จริงไป API Gateway
- แสดง fields สำคัญต่อการจัดการ
- มี search/filter ที่เหมาะกับ admin
- มี action links ไป create/edit/detail/delete
- แสดง `status` และ `visibility` ให้ชัด
- handle loading, empty, error, `401`, `403`
- ไม่ render admin data ก่อน auth check ผ่าน
- ไม่กระทบ public `/outputs` หรือ V1 `/faculties`

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- สร้าง create/edit form จริงของ #78
- submit create/update จริง
- submit soft delete จริง ถ้า #79 ยังไม่ผูก mutation
- restore flow เต็ม
- approval workflow
- bulk operation
- user/role management
- evidence upload/download
- audit dashboard
- ใช้ public API เพื่อเปิดข้อมูล internal/restricted/deleted

## User Stories

1. As an admin user, I want to open `/admin/work-items`, so that I can see records that need management.
2. As an admin user, I want to search work items, so that I can quickly find a record by title or keyword.
3. As an admin user, I want to filter by category/type/period/faculty, so that I can narrow the management list.
4. As an admin user, I want to filter by visibility, so that I can distinguish public/internal/restricted records.
5. As an admin user, I want to filter by status, so that I can see active or deleted records.
6. As an admin user, I want action links for new/edit/detail/delete, so that I can continue the admin workflow.
7. As an admin user, I want loading/empty/error states, so that I understand what is happening with the data fetch.
8. As an unauthenticated user, I should be redirected to login, so that admin data is protected.
9. As a non-admin Cognito user, I should see no-permission state, so that Cognito identity alone is not enough.
10. As a security reviewer, I want the page to use protected admin API only, so that private records are not exposed through public routes.
11. As a QA reviewer, I want evidence from deployed admin API and Cognito token, so that the card is proven against real AWS.
12. As a developer for #78/#79, I want stable action paths, so that create/edit/delete integration can build on this screen.

## Scope

### ต้องทำ

- เพิ่ม route `/admin/work-items`
- protect route ด้วย admin auth/session helper จาก #76
- call `GET /api/v2/admin/auth/check` หรือ reuse verified session จาก #76 ก่อนโหลด admin data
- สร้าง admin work item list component
- ต่อ data fetching กับ protected admin list endpoint จริง:
  - `GET /api/v2/admin/work-items`
- ถ้า endpoint นี้ยังไม่มีใน backend ให้ทำอย่างใดอย่างหนึ่ง:
  - เพิ่ม read-only admin list endpoint ใน scope นี้พร้อม contract ด้านล่าง หรือ
  - สร้าง/อ้าง backend subtask ให้เสร็จก่อนปิดการ์ดนี้
- ส่ง Cognito token จริงใน `Authorization` header
- แสดง fields สำคัญ:
  - `id`
  - `title`
  - `category`
  - `type`
  - `academic_periods`
  - `evaluation_periods`
  - `visibility`
  - `status`
  - `updated_at`
  - `deleted_at`
  - primary faculty/contributors
- เพิ่ม action links:
  - New work item → `/admin/work-items/new`
  - Edit → `/admin/work-items/{id}`
  - View public detail ถ้า `visibility = PUBLIC` และ `status = ACTIVE` → `/outputs/{id}`
  - Soft delete action hook หรือ placeholder ที่ไม่ submit จริงจนกว่า #79 ผูก mutation
  - Restore action hook หรือ placeholder สำหรับ `status = DELETED` ถ้าทีมต้องการให้ #79 ต่อ
- เพิ่ม filter/search controls ขั้นต้น:
  - keyword `q`
  - category
  - type
  - faculty
  - academic period
  - evaluation period
  - visibility
  - status
  - page/page size
- sync filter/page state กับ URL query
- เพิ่ม loading/empty/error states
- handle `401/403` จาก AWS endpoint จริง
- เพิ่ม tests/manual QA checklist
- verify ว่า public pages ยังไม่ต้อง login

### ไม่ต้องทำ

- submit delete จริง
- submit restore จริง
- create/edit form
- full mutation integration
- validation mapping ของ create/edit form
- audit event viewer
- bulk delete/restore

## Admin List API Contract

หน้า admin list ต้องใช้ protected endpoint:

```http
GET /api/v2/admin/work-items
Authorization: Bearer <cognito-token>
```

ห้ามใช้ `GET /api/v2/work-items` เพื่อแสดงข้อมูล admin-only เพราะ public endpoint ต้อง enforce `ACTIVE + PUBLIC` เท่านั้น

### Query Parameters

| Query | Example | ใช้ทำอะไร |
|---|---|---|
| `q` | `privacy` | search title/description |
| `category` | `RESEARCH` | filter `work_item.category_code` |
| `type` | `PUBLICATION` | filter `work_item.work_type_code` |
| `faculty_id` | `fac_prapaporn-rattanatamrong` | filter contributor |
| `academic_period_id` | `ap-2567-1` | filter period |
| `evaluation_period_id` | `eval-2567-full-year` | filter evaluation |
| `visibility` | `PUBLIC` | `PUBLIC`, `INTERNAL`, `RESTRICTED`, หรือ `ALL` |
| `status` | `ACTIVE` | `ACTIVE`, `DELETED`, หรือ `ALL` |
| `page` | `1` | pagination |
| `page_size` | `20` | pagination size |

ตัวอย่าง:

```text
/api/v2/admin/work-items?q=privacy&category=RESEARCH&type=PUBLICATION&visibility=ALL&status=ACTIVE&page=1&page_size=20
```

### Response Shape

UI ควรรองรับ response shape ประมาณนี้:

```json
{
  "items": [
    {
      "id": "wi-pub-2024-privacy-edge",
      "title": "Privacy-Preserving Edge Analytics for Smart Campus Workload Signals",
      "description": "Synthetic publication used for keyword search demo. Keyword: privacy.",
      "category": {
        "code": "RESEARCH",
        "label_th": "งานวิชาการ/วิจัย",
        "label_en": "Research and Academic Output"
      },
      "type": {
        "code": "PUBLICATION",
        "label_th": "ผลงานตีพิมพ์",
        "label_en": "Publication"
      },
      "visibility": "PUBLIC",
      "status": "ACTIVE",
      "academic_periods": [
        {
          "id": "ap-2567-1",
          "label": "1/2567"
        }
      ],
      "evaluation_periods": [
        {
          "id": "eval-2567-full-year",
          "label": "Evaluation 2567"
        }
      ],
      "faculty": [
        {
          "id": "fac_prapaporn-rattanatamrong",
          "display_name": "ผศ.ดร.ประภาพร รัตนธำรง",
          "slug": "prapaporn-rattanatamrong",
          "role": "CORRESPONDING_AUTHOR",
          "contribution_order": 1
        }
      ],
      "updated_at": "2026-09-12T17:15:44.616344Z",
      "deleted_at": null
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

### Error Shape

ควรรองรับ error shape มาตรฐาน:

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

Expected status:

| Case | Expected |
|---|---|
| no token | `401` |
| invalid/expired token | `401` |
| valid Cognito but no active `ADMIN` role | `403` |
| active admin | `200` |
| invalid query | `400` |
| server/data error | `500` |

## UI Field Mapping

| UI label | Response field | Source table / attribute |
|---|---|---|
| ชื่อรายการ | `title` | `work_item.title` |
| คำอธิบายย่อ | `description` | `work_item.description` |
| หมวด | `category.label_th`, fallback `category.code` | `work_category`, `work_item.category_code` |
| ประเภท | `type.label_th`, fallback `type.code` | `work_type`, `work_item.work_type_code` |
| ปีการศึกษา | `academic_periods[].label` | `faculty_work_item` + `academic_period` |
| รอบประเมิน | `evaluation_periods[].label` | `faculty_work_item` + `evaluation_period` |
| อาจารย์ | `faculty[].display_name` | `faculty` + `faculty_work_item` |
| Visibility | `visibility` | `work_item.visibility` |
| Status | `status` | `work_item.status` |
| ลบเมื่อ | `deleted_at` | `work_item.deleted_at` |
| อัปเดตล่าสุด | `updated_at` | `work_item.updated_at` |

## Expected UI Layout

หน้า `/admin/work-items` ควรเป็น admin management screen ไม่ใช่ public browsing page:

```text
Admin / Work Items

[New work item]

Search...
[Category] [Type] [Faculty] [Academic period] [Visibility] [Status]
[Reset filters]

Table/List
--------------------------------------------------------------------------------
Title                              Category/Type       Visibility  Status   Updated
Privacy-Preserving Edge...         Research/Publication PUBLIC      ACTIVE   2026-09-12
CS333 Lecture Assignment           Teaching/Lecture     INTERNAL    ACTIVE   2026-09-13
Deleted demo record                Service/Speaker      PUBLIC      DELETED  2026-09-13

Actions: View admin detail | Edit | Public view | Delete/Restore

Pagination
```

บน mobile ให้เปลี่ยนเป็น stacked rows/cards ได้ แต่ยังต้องเห็น status/visibility/action สำคัญ

## Action Behavior

| Action | Route / Behavior | Scope ตอนนี้ |
|---|---|---|
| New work item | `/admin/work-items/new` | link ไป #78 |
| Edit | `/admin/work-items/{id}` | link ไป #78 |
| Admin detail | `/admin/work-items/{id}` | ใช้ route เดียวกับ edit/detail ของ #78 |
| Public view | `/outputs/{id}` | แสดงเฉพาะ `visibility = PUBLIC` และ `status = ACTIVE` |
| Soft delete | action hook/disabled placeholder หรือ confirm shell | ยังไม่ต้อง submit จริงถ้า #79 ยังไม่ทำ |
| Restore | action hook/disabled placeholder สำหรับ `DELETED` | ยังไม่ต้อง submit จริงถ้า #79 ยังไม่ทำ |

ถ้าจะต่อ soft delete/restore จริงในการ์ดนี้ ต้องใช้ endpoints จาก #71:

```http
DELETE /api/v2/admin/work-items/{id}
POST /api/v2/admin/work-items/{id}/restore
```

แต่ default scope ของ #77 คือ list + action path/hook ไม่ใช่ mutation integration เต็ม

## State Handling

### Loading

- แสดง skeleton/table loading state
- ไม่ render admin data เก่าหรือ mock data เป็นของจริง

### Empty

- แสดงข้อความว่าไม่มีรายการตาม filter
- มี action clear filters
- ถ้าไม่มีข้อมูลเลย ให้ยังมีปุ่ม New work item

### Error

- `401`: clear session หรือ redirect `/admin/login`
- `403`: แสดง no permission state และไม่ render data
- `400`: แสดง filter/query error พร้อม clear filters
- `500/network`: แสดง retry
- ห้ามแสดง raw stack trace, SQL error, token, ARN หรือ secret

### Deleted Records

- ถ้า `status = DELETED` ให้แสดง badge ชัดเจน
- deleted record ไม่ควรมี public view link
- restore action เป็น hook สำหรับ #79 หรือทำจริงเฉพาะถ้า mutation integration ถูกเลือกใน scope

## Suggested Frontend Files

ปรับตาม pattern repo ได้ แต่ควรมี responsibility ประมาณนี้:

```text
frontend/app/admin/work-items/page.tsx
frontend/app/admin/work-items/loading.tsx
frontend/app/admin/work-items/error.tsx
frontend/components/admin/admin-work-item-list.tsx
frontend/components/admin/admin-work-item-filters.tsx
frontend/components/admin/admin-work-item-actions.tsx
frontend/components/admin/admin-pagination.tsx
frontend/lib/admin-api/work-items-client.ts
frontend/lib/admin-auth/protected-route.ts
```

ควร reuse admin auth/session helper จาก #76 และไม่สร้าง token handling ซ้ำ

## URL Query / Filter Behavior

Admin list query state ควรอยู่ใน URL เพื่อ share/debug ได้:

```text
/admin/work-items?q=privacy&visibility=ALL&status=ACTIVE&page=1
/admin/work-items?category=TEACHING&visibility=INTERNAL&status=ACTIVE
/admin/work-items?status=DELETED
```

กติกา:

- เปลี่ยน filter แล้ว reset `page` กลับ 1
- pagination ต้อง preserve filter เดิม
- reset filter ต้อง clear URL query ที่เกี่ยวข้อง
- invalid query จาก API ต้องไม่ทำให้หน้า crash

## Security / Public Safety Rules

- ห้ามใช้ public `/api/v2/work-items` เพื่อโหลด admin list
- ห้ามเปิด `INTERNAL`, `RESTRICTED`, `DELETED` ผ่าน public endpoint
- admin data ต้องโหลดหลัง auth/session ผ่านแล้วเท่านั้น
- token ต้องไม่ถูก log ลง console
- frontend ต้องไม่มี DB secret, AWS secret, RDS secret, raw token
- public `/outputs` และ `/faculties` ต้องยังไม่ต้อง login
- ถ้า admin API return fields ที่ sensitive เกิน UI ต้องไม่ render โดยอัตโนมัติ

## QA / Smoke Test Checklist

ต้องทดสอบกับ Cognito admin user จริงและ deployed AWS admin endpoint จริง:

- เปิด `/admin/work-items` แบบไม่ login แล้ว redirect `/admin/login`
- login admin จาก #76 แล้วเปิด `/admin/work-items` ได้
- Network tab/log แสดงว่าเรียก `GET /api/v2/admin/work-items` พร้อม `Authorization` header จริง
- list แสดง records จาก Aurora จริง
- เห็น `visibility` และ `status` badges
- filter `visibility=INTERNAL` หรือ `visibility=RESTRICTED` แสดงเฉพาะเมื่อ admin ผ่าน auth
- filter `status=DELETED` แสดง deleted records ถ้ามีใน data
- search keyword ทำงานกับ admin endpoint จริง
- pagination update URL และ preserve filters
- action New ไป `/admin/work-items/new`
- action Edit ไป `/admin/work-items/{id}`
- public view link แสดงเฉพาะ public active records
- no token ได้ `401` behavior
- non-admin token ได้ `403` behavior ถ้าทดสอบได้
- API error แสดง retry/error state
- public `/outputs` ไม่เห็น internal/restricted/deleted records
- public `/faculties` ยังเปิดได้โดยไม่ login

## QA Evidence ที่ต้องแนบตอนปิดการ์ด

ควรมี:

- screenshot `/admin/work-items` หลัง login admin
- screenshot logged-out redirect ไป `/admin/login`
- Network tab หรือ log ว่าเรียก `GET /api/v2/admin/work-items` จริง
- evidence ว่า request มี Authorization header โดยไม่แปะ raw token
- screenshot filter/search
- screenshot status/visibility badges
- screenshot empty state
- screenshot `401` หรือ logged-out state
- screenshot/no-permission หรือ note `403` ถ้าทดสอบได้
- CloudWatch log note ของ admin list request
- note ว่า public `/outputs` และ `/faculties` ไม่โดนบังคับ login

ห้ามแนบ:

- raw JWT token
- password
- Cognito temporary password
- AWS access key/secret key
- Secrets Manager secret value

## Acceptance Criteria

- [ ] `/admin/work-items` เปิดได้เมื่อ login เป็น admin
- [ ] ไม่ login แล้วถูก redirect ไป `/admin/login`
- [ ] valid Cognito แต่ไม่มี `ADMIN` role ถูก block ด้วย `403`
- [ ] list/table แสดง work item management fields ได้
- [ ] แสดง `visibility` และ `status` ชัดเจน
- [ ] มี search/filter UI ขั้นต้น
- [ ] filter/page state sync กับ URL query
- [ ] มี action link ไป create/edit/admin detail route
- [ ] public view link แสดงเฉพาะ public active records
- [ ] loading/empty/error states ครบ
- [ ] handle `401/403/400/500` จาก AWS endpoint จริง
- [ ] ไม่ใช้ public API เพื่อเปิด internal/restricted/deleted โดยไม่มี auth
- [ ] ใช้ protected AWS admin endpoint จริง ไม่ใช่ mock data
- [ ] ส่ง Cognito token จริงไปยัง API Gateway admin route
- [ ] ไม่ render admin content ก่อน auth check สำเร็จ
- [ ] มี QA evidence จาก admin user จริง
- [ ] public `/outputs` และ `/faculties` ไม่พัง/ไม่ต้อง login

## Review Checklist

Frontend:

- [ ] admin list component แยกจาก public repository list
- [ ] API client แยก public/admin ชัดเจน
- [ ] action links ใช้ route ที่ตรงกับ baseline
- [ ] UI ไม่สับสนกับ public `/outputs`
- [ ] loading/empty/error states อ่านง่าย
- [ ] query serialization stable
- [ ] mobile ไม่ล้นจอ

Security:

- [ ] protected route ทำงานจริง
- [ ] ไม่ render admin content ก่อน auth check สำเร็จ
- [ ] ไม่ log token/password
- [ ] ไม่เก็บ DB/AWS secret ใน frontend
- [ ] public API ไม่ถูกใช้เป็นช่องทางดู internal/restricted/deleted records

Backend/API:

- [ ] `GET /api/v2/admin/work-items` enforce Cognito + `ADMIN`
- [ ] admin endpoint อ่าน Aurora จริง
- [ ] admin endpoint return `401/403` ถูกต้อง
- [ ] response shape ตรงกับ UI
- [ ] CORS/env ใช้กับ deployed frontend ได้

QA:

- [ ] test logged out redirect
- [ ] test valid admin list
- [ ] test empty list/filter empty
- [ ] test action links
- [ ] test `401/403`
- [ ] test กับ deployed admin API และ Cognito token จริง

## Dependencies

Blocked by:

- #69 Configure Admin Authentication
- #76 Build Admin Login UI

Blocks:

- #78 Build Admin Create/Edit Form UI
- #79 Integrate Admin UI with Auth & CRUD API

Related:

- #70 Build Admin Create Work Item API
- #71 Build Admin Update / Soft Delete API

## Suggested Labels

- `v2`
- `frontend`
- `admin`
- `ui`
- `api`
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

การ์ดนี้ถือว่าเสร็จเมื่อ Admin มีหน้า `/admin/work-items` สำหรับ browse/manage work items ที่ protected ด้วย Cognito จริง อ่านข้อมูลจาก protected AWS Admin API จริง เห็น `visibility/status` และ action paths ชัดเจน รองรับ loading/empty/error/401/403 และมีหลักฐานว่า auth/data path ใช้งานกับ Cognito + API Gateway + Lambda + Aurora ได้โดยไม่ทำให้ public V1/V2 pages พัง
