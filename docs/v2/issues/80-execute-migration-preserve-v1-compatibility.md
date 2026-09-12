# [V2] Execute Migration & Preserve V1 Compatibility #80

## สรุป

ทำให้การสร้าง schema, seed master data, import demo dataset เข้า Aurora และ compatibility verification ของ V1 เป็นขั้นตอน production-ready ที่ทำซ้ำได้ พร้อมยืนยันว่า V1 public routes/API ไม่พังหลัง V2 ใช้ AWS database จริง

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #66 แต่ GitHub issue จริงใช้ #80

## Production AWS Requirement

การ์ดนี้ต้องรันกับ target AWS environment จริงที่เตรียมไว้แล้วจาก #48:

```text
Migration/seed/import command
→ Amazon RDS Data API หรือ controlled migration runner
→ Aurora PostgreSQL Serverless v2
→ deployed V2 APIs สำหรับตรวจผล
→ deployed V1 public routes/API สำหรับ regression check
```

ห้ามปิดการ์ดด้วย local database, dbdiagram, หรือ SQL file ที่ยังไม่ได้รันจริงเท่านั้น ต้องมีหลักฐานว่า schema/master/demo data อยู่ใน Aurora และ V2/V1 endpoints ตรวจผ่านจาก environment จริง

## Background

ตอนนี้ repo มี:

- `database/migrations/001_base.sql`
- `database/seeds/001_master_data.sql`
- `data/v2/fixtures/`
- AWS foundation/Aurora/Data API/Secrets/IAM environment

และ Aurora environment ถูกเตรียมไว้สำหรับ V2 แล้ว แต่เพื่อให้ทีมคนอื่นทำต่อได้ งานนี้ต้องทำให้ขั้นตอน migration/seed/import/verify เป็น repeatable ไม่ใช่ทำครั้งเดียวใน terminal แล้วจบ

V1 compatibility ต้อง preserve:

- `/faculties`
- `/faculties/{id}`
- `/api/v1/faculties`
- `/api/v1/faculties/{id}`
- public slug เช่น `prapaporn-rattanatamrong`

## เป้าหมาย

สร้าง migration/compatibility process ที่:

- รัน schema migration เข้า Aurora target environment ได้ซ้ำอย่างควบคุม
- seed master data เข้า Aurora ได้
- load demo fixtures เข้า V2 repository ใน Aurora ได้
- verify table counts/search matrix จาก Aurora ได้
- verify deployed V2 APIs อ่านข้อมูลจาก Aurora ได้จริง
- verify V1 public experience ไม่พังหลังเปิด V2 repository
- มี rollback/reset guidance สำหรับ environment ที่ทีมใช้ส่งงาน/demo

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- migrate ข้อมูล production จริงทั้งหมดจากทุกแหล่งภายนอกนอกเหนือจาก scope/dataset ที่ freeze ไว้
- parse PDF workload form อัตโนมัติ
- ทำ official ETL pipeline
- เปลี่ยน V1 ให้ใช้ Aurora เป็น source ทันทีถ้ายังไม่พร้อม
- ทำ V3 workflow/approval

## Scope

### ต้องทำ

- เพิ่มหรือปรับ script/document สำหรับ:
  - run `database/migrations/001_base.sql`
  - run `database/seeds/001_master_data.sql`
  - import `data/v2/fixtures/` เข้า Aurora target environment
  - verify table counts
  - verify search/filter matrix
- ใช้ RDS Data API, AWS CLI, หรือ migration runner ที่ทีมตกลง โดยอ้างอิง Secret/Cluster ARN ผ่าน environment variable เท่านั้น
- บันทึก resource names ที่ต้องใช้ เช่น stack name, database name, cluster ARN placeholder, secret ARN placeholder และ region โดยไม่ใส่ secret value จริง
- ตรวจ deployed V2 API endpoints ว่าอ่านข้อมูลที่ import แล้วจาก Aurora
- เพิ่ม compatibility checks สำหรับ V1 routes/API
- บันทึก required env/ARN/secret placeholders ใน docs โดยไม่ใส่ secret value จริง
- เพิ่ม evidence checklist สำหรับปิดการ์ด
- ถ้ามี DB/table/data อยู่แล้ว ต้อง handle rerun/idempotency หรือบอก reset path ชัดเจน

### ไม่ต้องทำ

- frontend/admin final demo docs
- สร้าง AWS foundation ใหม่ซ้ำ ถ้า #48 เตรียมไว้แล้ว
- data extraction จาก PDF/source จริง

## Required Verification

AWS environment checks:

- CloudFormation stack/resource outputs ที่ใช้จริง
- Aurora database reachable ผ่าน Data API
- Secrets Manager secret ใช้ได้โดยไม่เปิด secret value
- CloudWatch logs ของ migration/import หรือ API smoke test มีหลักฐานตรวจสอบได้

Database checks:

- faculty count
- academic/evaluation period count
- work item count
- category/type count
- visibility count
- evidence count

API checks:

- deployed `GET /api/v2/work-items`
- deployed `GET /api/v2/work-items/{id}`
- deployed `GET /api/v2/faculties/{faculty_id}/work-items`

V1 checks:

- deployed `/api/v1/faculties`
- deployed `/api/v1/faculties/prapaporn-rattanatamrong`
- deployed `/faculties`
- deployed `/faculties/prapaporn-rattanatamrong`

## Acceptance Criteria

- [ ] schema migration ถูกรันกับ Aurora target environment แล้ว และ rerun/reset behavior ชัดเจน
- [ ] master seed ถูกรันกับ Aurora target environment แล้ว
- [ ] demo fixture import ถูกรันหรือมี command ที่ทำซ้ำได้กับ Aurora target environment
- [ ] มี verification counts จาก Aurora เทียบกับ `data/v2/fixtures/dataset-summary.json`
- [ ] deployed V2 APIs อ่าน demo data จาก Aurora ได้จริง
- [ ] deployed V1 public API/routes ยังทำงานและ response shape ไม่ breaking
- [ ] public slug เดิมยังใช้ได้
- [ ] มี CloudWatch/API/Data API evidence สำหรับ migration/import/verification
- [ ] มี docs/evidence สำหรับคนอื่นที่มี IAM สิทธิ์เหมาะสมทำซ้ำได้

## Review Checklist

Data:

- [ ] fixture import map เข้าตาราง Aurora ถูกต้อง
- [ ] source/provenance fields ถูกเก็บพอสำหรับ trace
- [ ] idempotency/rerun behavior ชัดเจน

Backend:

- [ ] API compatibility checks ผ่านบน deployed endpoints
- [ ] V1 adapter/projection ไม่เปลี่ยน contract เดิม

QA:

- [ ] test matrix จาก `docs/v2/demo-dataset.md` ผ่าน
- [ ] V1 regression checks ผ่าน

Security:

- [ ] docs ไม่เปิด secret value
- [ ] restricted demo records ไม่โผล่ public
- [ ] IAM ที่ใช้ migration/import มีสิทธิ์เท่าที่จำเป็นต่อ Data API/Secrets/S3 เท่านั้น

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

การ์ดนี้ถือว่าเสร็จเมื่อทีมสามารถสร้าง V2 database state ใหม่ใน Aurora จาก repo ได้จริง, seed/import/verify ได้แบบทำซ้ำได้, deployed V2 APIs อ่านข้อมูลจาก Aurora ได้, และพิสูจน์ด้วย evidence ว่า V1 public routes/API ยังไม่พังหลังเปิด V2 repository
