# [V2] Execute Migration & Preserve V1 Compatibility #80

## สรุป

ทำให้การสร้าง schema, seed master data, import demo dataset และ compatibility verification ของ V1 เป็นขั้นตอนที่ทำซ้ำได้ พร้อมยืนยันว่า V1 public routes/API ไม่พัง

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #66 แต่ GitHub issue จริงใช้ #80

## Background

ตอนนี้ repo มี:

- `database/migrations/001_base.sql`
- `database/seeds/001_master_data.sql`
- `data/v2/fixtures/`
- AWS foundation/Aurora dev environment

และ dev Aurora เคยถูกลองรัน table/master/demo data แล้ว แต่เพื่อให้ทีมคนอื่นทำต่อได้ งานนี้ต้องทำให้ขั้นตอน migration/seed/import/verify เป็น repeatable ไม่ใช่ทำครั้งเดียวใน terminal แล้วจบ

V1 compatibility ต้อง preserve:

- `/faculties`
- `/faculties/{id}`
- `/api/v1/faculties`
- `/api/v1/faculties/{id}`
- public slug เช่น `prapaporn-rattanatamrong`

## เป้าหมาย

สร้าง migration/compatibility process ที่:

- รัน schema migration ได้ซ้ำอย่างควบคุม
- seed master data ได้
- load demo fixtures เข้า V2 repository ได้หรือมี documented import command
- verify counts/search matrix ได้
- verify V1 public experience ไม่พัง
- มี rollback/reset guidance สำหรับ dev/demo

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- ทำ production data migration เต็ม
- parse PDF workload form อัตโนมัติ
- ทำ official ETL pipeline
- เปลี่ยน V1 ให้ใช้ Aurora เป็น source ทันทีถ้ายังไม่พร้อม
- ทำ V3 workflow/approval

## Scope

### ต้องทำ

- เพิ่มหรือปรับ script/document สำหรับ:
  - run `database/migrations/001_base.sql`
  - run `database/seeds/001_master_data.sql`
  - import `data/v2/fixtures/` เข้า Aurora dev/demo
  - verify table counts
  - verify search/filter matrix
- เพิ่ม compatibility checks สำหรับ V1 routes/API
- บันทึก required env/ARN/secret ใน docs โดยไม่ใส่ secret value จริง
- เพิ่ม evidence checklist สำหรับปิดการ์ด
- ถ้ามี DB อยู่แล้ว ต้อง handle rerun/idempotency หรือบอก reset path ชัดเจน

### ไม่ต้องทำ

- frontend/admin final demo docs
- production deployment
- data extraction จาก PDF/source จริง

## Required Verification

Database checks:

- faculty count
- academic/evaluation period count
- work item count
- category/type count
- visibility count
- evidence count

API checks:

- `GET /api/v2/work-items`
- `GET /api/v2/work-items/{id}`
- `GET /api/v2/faculties/{faculty_id}/work-items`

V1 checks:

- `/api/v1/faculties`
- `/api/v1/faculties/prapaporn-rattanatamrong`
- `/faculties`
- `/faculties/prapaporn-rattanatamrong`

## Acceptance Criteria

- [ ] มีขั้นตอน repeatable สำหรับ schema migration
- [ ] มีขั้นตอน repeatable สำหรับ master seed
- [ ] มีขั้นตอน repeatable หรือ documented process สำหรับ demo fixture import
- [ ] มี verification counts เทียบกับ `data/v2/fixtures/dataset-summary.json`
- [ ] V2 API อ่าน demo data ได้
- [ ] V1 public API/routes ยังทำงานและ response shape ไม่ breaking
- [ ] public slug เดิมยังใช้ได้
- [ ] มี docs/evidence สำหรับคนอื่นทำซ้ำ

## Review Checklist

Data:

- [ ] fixture import map เข้าตารางถูกต้อง
- [ ] source/provenance fields ถูกเก็บพอสำหรับ trace
- [ ] idempotency/rerun behavior ชัดเจน

Backend:

- [ ] API compatibility checks ผ่าน
- [ ] V1 adapter/projection ไม่เปลี่ยน contract เดิม

QA:

- [ ] test matrix จาก `docs/v2/demo-dataset.md` ผ่าน
- [ ] V1 regression checks ผ่าน

Security:

- [ ] docs ไม่เปิด secret value
- [ ] restricted demo records ไม่โผล่ public

## Dependencies

Blocked by:

- #47 Design Relational Schema & SQL Migration
- #48 Provision Aurora / Data API / Secret / IAM
- #49 Define V1 to V2 Data Mapping
- #50 Prepare Multi-Year Demo Dataset
- #64 Build Master Data API
- #66 Build Work Item List/Search/Filter API
- #68 Build Work Item Detail API

Blocks:

- #81 Final Integration / Deploy / Demo Docs

Related:

- #75 Integrate Repository UI with Real API
- #79 Integrate Admin UI with Auth & CRUD API

## Suggested Labels

- `v2`
- `database`
- `migration`
- `qa`
- `compatibility`

## Suggested Owner

Data/Backend Developer

Reviewers:

- Tech Lead
- Backend Developer
- QA / Integration

## Estimate

1-2 days

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อทีมสามารถสร้าง V2 database state ใหม่จาก repo ได้ ตรวจข้อมูล demo ได้ และพิสูจน์ได้ว่า V1 public routes/API ยังไม่พังหลังมี V2 repository
