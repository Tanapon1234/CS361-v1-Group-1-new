# คู่มือ Workflow และ Issue Cards ของ V2

ไฟล์นี้คือคู่มือทำงานราย issue card สำหรับทีม V2

เนื้อหาหลักเขียนเป็นภาษาไทยเพื่อให้คนในทีมอ่านแล้วเริ่มงานได้ทันที ส่วนชื่อ branch, route, command, file path และ AWS service ยังคงเป็นภาษาอังกฤษตามของจริง

## มาตรฐานการตั้งชื่อ Branch

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

## ขั้นตอนทำงานพื้นฐานต่อหนึ่งการ์ด

ทุกคนควรทำตามลำดับนี้:

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

## แต่ละการ์ดต้องส่งมอบอะไรบ้าง

การ์ด Backend/API ควรมี:

- Lambda handler / route logic
- repository/data access boundary
- validation and error shape
- tests
- CloudFormation/API Gateway route if needed
- deploy or update script if needed
- AWS smoke test
- docs/evidence

การ์ด Frontend ควรมี:

- usable page/component
- loading/empty/error states
- API client pointing to deployed AWS API
- tests or manual QA evidence
- screenshot/evidence where useful
- docs/env update

การ์ด Database/Migration ควรมี:

- repeatable command/script
- idempotency or reset path
- Data API verification
- table counts
- compatibility evidence

การ์ด Admin/Auth ควรมี:

- Cognito/admin auth integration
- role check with `app_user` / `app_user_role`
- protected API route
- 401/403/success tests
- CloudWatch/auth evidence

## กฎสำคัญเรื่อง Production

ห้ามปิดการ์ดด้วย local mock/fixture อย่างเดียว ยกเว้นการ์ดนั้นเขียนชัดว่าเป็น prototype

สำหรับการ์ด V2 ฝั่ง public/backend เส้นทาง production ที่คาดหวังคือ:

```text
API Gateway -> Lambda -> RDS Data API -> Aurora
```

สำหรับฝั่ง admin เส้นทาง production ที่คาดหวังคือ:

```text
Cognito -> protected API Gateway -> Admin Lambda -> RDS Data API transaction -> Aurora
```

ดังนั้นถ้าการ์ดเป็น API จริง ต้องมีหลักฐานว่าเชื่อมกับ AWS และ Aurora จริง ไม่ใช่แค่ frontend mock หรือ local API

## สถานะการ์ดปัจจุบัน

สถานะในตารางนี้หมายถึงสถานะตาม repo/project ไม่ได้แปลว่าสถานะใน GitHub issue UI ถูกปิดแล้วเสมอ

| Issue | ชื่อการ์ด | สถานะ | หมายเหตุ |
|---:|---|---|---|
| #46 | Freeze Scope, Architecture & Interface Contracts | เสร็จแล้ว | มี baseline ของ scope และ architecture |
| #47 | Design Relational Schema & SQL Migration | เสร็จแล้ว | มี SQL, ERD, DBML และ table attribute guide |
| #48 | Provision Aurora / Data API / Secret / IAM | เสร็จแล้ว | AWS foundation deploy แล้วและมีเอกสารอธิบาย |
| #49 | Define V1 to V2 Data Mapping | เสร็จแล้ว | มี mapping docs/CSV |
| #50 | Prepare Multi-Year Demo Dataset | เสร็จแล้ว | มี fixture dataset และ Aurora มี demo data แล้ว |
| #64 | Build Master Data API | เสร็จแล้ว | Deploy API Gateway + Lambda + RDS Data API + Aurora แล้ว และ smoke test ผ่าน |
| #66 | Build Work Item List/Search/Filter API | ยังไม่ทำ | เริ่มได้หลัง #64 |
| #67 | Build Faculty Work Items API | ยังไม่ทำ | เริ่มหลัง #66 |
| #68 | Build Work Item Detail API | ยังไม่ทำ | เริ่มหลัง #66/#67 |
| #69 | Configure Admin Authentication | ยังไม่ทำ | เริ่มขนานกับ #66 ได้ |
| #70 | Build Admin Create Work Item API | ยังไม่ทำ | เริ่มหลัง #69 |
| #71 | Build Admin Update / Soft Delete API | ยังไม่ทำ | เริ่มหลัง #70 |
| #72 | Build Repository Page Shell & Filter UI | ยังไม่ทำ | เริ่มได้หลัง #64 |
| #73 | Build Repository Result List & Pagination UI | ยังไม่ทำ | เริ่มหลัง #66 และ #72 |
| #74 | Build Work Item Detail UI | ยังไม่ทำ | เริ่มหลัง #68 และ #73 |
| #75 | Integrate Repository UI with Real API | ยังไม่ทำ | เริ่มหลัง #66/#68/#72/#73/#74 |
| #76 | Build Admin Login UI | ยังไม่ทำ | เริ่มหลัง #69 |
| #77 | Build Admin Work Item List UI | ยังไม่ทำ | เริ่มหลัง #76 และ #71 |
| #78 | Build Admin Create/Edit Form UI | ยังไม่ทำ | เริ่มหลัง #70/#71/#76/#77 |
| #79 | Integrate Admin UI with Auth & CRUD API | ยังไม่ทำ | เริ่มหลัง #69-#78 |
| #80 | Execute Migration & Preserve V1 Compatibility | ยังไม่ทำ | เริ่มหลัง #66 และ #68 แม้ DB มีข้อมูลแล้ว แต่ยังต้องทำกระบวนการ migration ให้รันซ้ำได้ |
| #81 | Final Integration / Deploy / Demo Docs | ยังไม่ทำ | เป็นการ์ดท้าย หลัง #75/#79/#80 |

## แผนแบ่งงานแบบทำขนาน

### Track A: Public API

ควรทำก่อน:

```text
#66 Work Item List/Search/Filter API
```

จากนั้นทำ:

```text
#67 Faculty Work Items API
#68 Work Item Detail API
```

เหตุผล:

- #66 วางรูปแบบ validation, pagination และ response shape ของ list/search
- #67 ใช้ pattern filter/pagination ต่อจาก #66 แต่จำกัดตามอาจารย์
- #68 ใช้พฤติกรรม list/faculty ต่อ และเพิ่มรายละเอียด subtype/evidence

### Track B: Public UI

เริ่มได้ตอนนี้:

```text
#72 Repository Page Shell & Filter UI
```

จากนั้นทำ:

```text
#73 Result List & Pagination UI
#74 Work Item Detail UI
#75 Integrate Repository UI with Real API
```

เหตุผล:

- #72 ใช้ Master Data API จาก #64 ได้ทันที
- #73 รอ list API จาก #66
- #74 รอ detail API จาก #68
- #75 ใช้พิสูจน์ว่า public repository ทำงานครบ end-to-end

### Track C: Admin Backend/Auth

เริ่มได้ตอนนี้:

```text
#69 Configure Admin Authentication
```

จากนั้นทำ:

```text
#70 Admin Create Work Item API
#71 Admin Update / Soft Delete API
```

เหตุผล:

- #70/#71 ต้องมีขอบเขตตัวตนและ role ของ admin ที่ชัดเจนก่อน
- งานแก้ไขข้อมูลฝั่ง admin ต้องเขียนลง Aurora และบันทึก `audit_event`

### Track D: Admin UI

หลัง #69:

```text
#76 Admin Login UI
```

หลัง backend CRUD พร้อมแล้ว:

```text
#77 Admin Work Item List UI
#78 Admin Create/Edit Form UI
#79 Admin Integration
```

### Track E: Finalization

ทำช่วงท้าย:

```text
#80 Migration & V1 Compatibility
#81 Final Integration / Demo Docs
```

## แต่ละการ์ดควรอ่านอะไรและทำอะไร

### #66 Work Item List/Search/Filter API

ควรอ่าน:

- `docs/v2/issues/66-build-work-item-list-search-filter-api.md`
- `backend/v2/query/master_data.py` เพื่อดู pattern ของ Lambda/Data API
- `database/migrations/001_base.sql`
- `docs/v2/demo-dataset.md`
- `data/v2/fixtures/dataset-summary.json`

สิ่งที่ต้องทำ:

- เพิ่ม `GET /api/v2/work-items`
- query ข้อมูลจริงจากตาราง `work_item` ใน Aurora
- รองรับ filter ตาม faculty/period/category/type/q/page
- บังคับให้ public path เห็นเฉพาะ `status = ACTIVE` และ `visibility = PUBLIC`
- deploy route และทำ smoke test

### #67 Faculty Work Items API

ควรอ่าน:

- issue file ของ #67
- implementation ของ #66
- schema ของ `faculty`, `faculty_work_item`, `work_item`

สิ่งที่ต้องทำ:

- เพิ่ม `GET /api/v2/faculties/{faculty_id}/work-items`
- รองรับ faculty id หรือ public slug ตาม contract ที่สรุปใน issue
- ใช้ pattern filter/pagination ต่อจาก #66
- แสดงข้อมูล contribution ของอาจารย์ในรายการผลงาน

### #68 Work Item Detail API

ควรอ่าน:

- issue file ของ #68
- ตาราง subtype detail ใน database guide
- กฎการเปิดเผย evidence

สิ่งที่ต้องทำ:

- เพิ่ม `GET /api/v2/work-items/{id}`
- join ข้อมูลหลักของ work item, faculty contributors, subtype detail และ evidence metadata
- บังคับกฎ public visibility และ redact ข้อมูลที่ไม่ควรเปิดเผย

### #69 Admin Authentication

ควรอ่าน:

- issue file ของ #69
- AWS Cognito docs หรือหน้าจอใน AWS Console
- `app_user`, `app_role`, `app_user_role`, `auth_login_event`

สิ่งที่ต้องทำ:

- สร้างและ document Cognito User Pool/App Client
- ทำ token verification หรือ API Gateway authorizer
- map Cognito user เข้ากับ `app_user` ใน Aurora
- บังคับว่า user ต้องมี role `ADMIN` ที่ active
- ทดสอบกรณี 401/403/success

### #70 Admin Create Work Item API

ควรอ่าน:

- issue file ของ #70
- implementation ของ #69
- #64 master data validation patterns
- ตาราง subtype detail

สิ่งที่ต้องทำ:

- เพิ่ม protected route `POST /api/v2/admin/work-items`
- validate payload
- insert `work_item`, `faculty_work_item`, subtype detail และ `evidence_reference`
- เขียน `audit_event`
- ใช้ Data API transaction

### #71 Admin Update / Soft Delete API

ควรอ่าน:

- issue file ของ #71
- transaction pattern ของ #70

สิ่งที่ต้องทำ:

- ทำ admin detail/load/update/delete/restore routes
- update แถว subtype/evidence ที่เกี่ยวข้อง
- soft delete ด้วย `status`/`deleted_at`
- เขียน audit events

### #72 Repository Page Shell & Filter UI

ควรอ่าน:

- issue file ของ #72
- `docs/v2/master-data-api.md`
- layout/components ปัจจุบันของ frontend

สิ่งที่ต้องทำ:

- สร้างหน้า `/outputs`
- โหลด filter options จาก endpoint #64 ที่ deploy แล้ว
- เก็บสถานะ filter ไว้ใน URL query
- แสดง loading/error/empty states

### #73 Result List & Pagination UI

ควรอ่าน:

- issue file ของ #73
- #66 API contract

สิ่งที่ต้องทำ:

- render ผลลัพธ์จาก `GET /api/v2/work-items`
- รองรับการเปลี่ยน pagination/filter
- link ไปหน้ารายละเอียด

### #74 Work Item Detail UI

ควรอ่าน:

- issue file ของ #74
- #68 detail API contract

สิ่งที่ต้องทำ:

- สร้างหน้า `/outputs/{id}`
- render รายละเอียด, contributors, subtype และ evidence metadata
- รองรับ 404/restricted/public-safe state

### #75 Public Integration

ควรอ่าน:

- issue file ของ #75
- deployed endpoints ของ #64/#66/#68
- #72/#73/#74 UI

สิ่งที่ต้องทำ:

- เชื่อม public UI กับ AWS APIs จริง
- ตรวจ deployed frontend/API flow
- บันทึก evidence

### #76 Admin Login UI

ควรอ่าน:

- issue file ของ #76
- #69 Cognito config

สิ่งที่ต้องทำ:

- สร้างหน้า `/admin/login`
- login ผ่าน Cognito
- เก็บ/ส่งต่อ token ไป admin API client อย่างปลอดภัย
- รองรับ expired/login fail states

### #77 Admin Work Item List UI

ควรอ่าน:

- issue file ของ #77
- #71 admin list/detail route

สิ่งที่ต้องทำ:

- สร้างหน้า `/admin/work-items`
- บังคับ admin login
- call protected admin endpoint ด้วย Cognito token
- แสดง status/visibility/action links

### #78 Admin Create/Edit Form UI

ควรอ่าน:

- issue file ของ #78
- #64 master data endpoint
- #70/#71 admin APIs

สิ่งที่ต้องทำ:

- สร้างหน้า `/admin/work-items/new`
- สร้าง edit route
- สร้าง form สำหรับ category/type/faculty/period/subtype/evidence
- submit ไป real admin API

### #79 Admin Integration

ควรอ่าน:

- issue file ของ #79
- admin cards ทั้งหมด #69-#78

สิ่งที่ต้องทำ:

- ตรวจ login/list/create/edit/delete/restore แบบ end-to-end
- เก็บหลักฐานจาก CloudWatch และ Aurora

### #80 Migration & V1 Compatibility

ควรอ่าน:

- issue file ของ #80
- DB/mapping/demo docs
- V1 routes/docs

สิ่งที่ต้องทำ:

- ทำให้ migration/seed/import รันซ้ำได้อย่างมีขั้นตอน
- ตรวจ table counts
- ตรวจว่า V2 APIs อ่านข้อมูลได้จริง
- ตรวจว่า V1 routes ยังทำงานได้

### #81 Final Integration

ควรอ่าน:

- issue file ของ #81
- evidence folders
- route/API/docs ทั้งหมด

สิ่งที่ต้องทำ:

- รัน final checks ของ public/admin/data/AWS
- เตรียม demo script
- เตรียม closing comments สำหรับ issue หลัก

## มาตรฐานข้อความ Commit

ใช้ข้อความที่อ่านแล้วรู้ว่าทำอะไร:

```text
feat: add V2 work item list API
feat: configure V2 admin Cognito auth
docs: add V2 migration evidence
test: add work item search smoke checks
```

หลีกเลี่ยงข้อความกำกวม:

```text
fix stuff
update
final
```

## รูปแบบ Comment สำหรับปิด GitHub Issue

ทุก comment สำหรับปิดการ์ดควรมี:

- สิ่งที่ implement
- ชื่อ resource/URL ที่ deploy ถ้ามี
- commands และผล test
- ผล smoke test
- docs/evidence files
- commit hash
- known limitations ถ้ามี

ดู template เพิ่มเติมใน `05-testing-verification-and-evidence.md`
