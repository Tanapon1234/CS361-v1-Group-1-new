# [V2] Execute Migration & Preserve V1 Compatibility #80

## สรุป

ทำให้การสร้าง schema, seed master data, import demo dataset เข้า Aurora และ compatibility verification ของ V1 เป็นขั้นตอน production-ready ที่ทำซ้ำได้ พร้อมยืนยันว่า V1 public routes/API ไม่พังหลัง V2 ใช้ AWS database จริง

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #66 แต่ GitHub issue จริงใช้ #80

## Production AWS Requirement

การ์ดนี้ต้องรันกับ target AWS environment จริงที่เตรียมไว้แล้วจาก #48:

```text
Migration / seed / import command
→ Amazon RDS Data API หรือ controlled migration runner
→ Aurora PostgreSQL Serverless v2
→ deployed V2 APIs สำหรับตรวจผล
→ deployed V1 public routes/API สำหรับ regression check
```

ห้ามปิดการ์ดด้วย local database, dbdiagram, SQL file ที่ยังไม่ได้รันจริง, หรือ screenshot จากเครื่องอย่างเดียว ต้องมีหลักฐานว่า schema/master/demo data อยู่ใน Aurora และ V2/V1 endpoints ตรวจผ่านจาก environment จริง

## Background

ตอนนี้ repo มีฐานสำหรับ migration แล้ว:

- `database/migrations/001_base.sql`
- `database/seeds/001_master_data.sql`
- `data/v2/fixtures/`
- `data/v2/fixtures/dataset-summary.json`
- `data/v2/mappings/v1-to-v2-field-mapping.csv`
- `docs/v2/v1-to-v2-mapping.md`
- AWS foundation/Aurora/Data API/Secrets/IAM environment จาก #48

Aurora environment ถูกเตรียมไว้สำหรับ V2 แล้ว แต่เพื่อให้ทีมคนอื่นทำต่อได้ งานนี้ต้องทำให้ขั้นตอน migration/seed/import/verify เป็น repeatable ไม่ใช่ทำครั้งเดียวใน terminal แล้วจบ

V1 compatibility ต้อง preserve:

- `/faculties`
- `/faculties/{slug}`
- `/api/v1/faculties`
- `/api/v1/faculties/{slug}`
- public slug เดิม เช่น `prapaporn-rattanatamrong`
- V1 serving contract จาก `build/v1/serving/faculties.json`
- V1 detail contract จาก `build/v1/serving/faculties/{slug}.json`

## ความเกี่ยวข้องกับโจทย์

โจทย์ V2 ต้องมีข้อมูลอาจารย์ การสอน งานวิจัย งานบริการ การดูแลนักศึกษา และผลงาน/ภาระงานที่เกี่ยวข้องเก็บในแหล่งข้อมูลที่จัดการได้อย่างเป็นระบบ

การ์ด #80 คือจุดที่ทำให้ design และ fixtures กลายเป็น database state จริงใน Aurora และพิสูจน์ว่า:

- V2 repository มีข้อมูลจริงให้ APIs/UI ใช้ต่อ
- search/filter/detail ใช้ข้อมูลจาก Aurora จริง
- V1 เดิมยังเปิดใช้งานได้ ไม่เสีย public route หรือ slug เดิม
- ทีมสามารถ reset/rebuild/demo environment ได้ซ้ำ

## เป้าหมาย

สร้าง migration/compatibility process ที่:

- รัน schema migration เข้า Aurora target environment ได้อย่างควบคุม
- seed master data เข้า Aurora ได้
- import demo fixtures เข้า V2 repository ใน Aurora ได้
- verify table counts/search matrix จาก Aurora ได้
- verify deployed V2 APIs อ่านข้อมูลจาก Aurora ได้จริง
- verify V1 public experience ไม่พังหลังเปิด V2 repository
- มี rollback/reset guidance สำหรับ environment ที่ทีมใช้ส่งงาน/demo
- ไม่เปิด secret value, DB password, AWS key หรือ raw credential ใน docs/evidence

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- migrate ข้อมูล production จริงทั้งหมดจากทุกแหล่งภายนอก
- parse PDF workload form อัตโนมัติ
- ทำ official ETL pipeline ระยะยาว
- เปลี่ยน V1 ให้ใช้ Aurora เป็น source ทันทีถ้ายังไม่พร้อม
- ทำ V3 workflow/approval
- ทำ admin UI final demo docs
- สร้าง AWS foundation ใหม่ซ้ำ ถ้า #48 เตรียมไว้แล้ว
- ทำ S3 evidence file upload จริง

## User Stories

1. As a backend developer, I want a repeatable migration command, so that I can recreate the V2 schema in Aurora safely.
2. As a data developer, I want demo fixtures imported into Aurora, so that APIs can read realistic V2 data.
3. As a QA reviewer, I want table counts from Aurora, so that I can confirm the target database has expected data.
4. As a frontend developer, I want deployed V2 APIs to read imported data, so that UI work can use real endpoints.
5. As a V1 user, I want existing `/faculties` routes to keep working, so that V2 migration does not break the old public experience.
6. As a project maintainer, I want reset/rerun guidance, so that demo environments can be rebuilt before presentation.
7. As a security reviewer, I want secrets redacted from docs/evidence, so that migration proof does not leak credentials.
8. As a future teammate, I want resource names and env variables documented, so that I can rerun checks without asking around.

## Scope

### ต้องทำ

- เพิ่มหรือปรับ script/document สำหรับ:
  - run `database/migrations/001_base.sql`
  - run `database/seeds/001_master_data.sql`
  - import `data/v2/fixtures/` เข้า Aurora target environment
  - verify table counts
  - verify visibility counts
  - verify search/filter matrix
  - verify V2 public APIs
  - verify V1 routes/API compatibility
- ใช้ RDS Data API, AWS CLI, หรือ migration runner ที่ทีมตกลง
- อ้างอิง Secret/Cluster ARN ผ่าน environment variables เท่านั้น
- บันทึก resource names ที่ต้องใช้ เช่น stack name, database name, cluster ARN placeholder, secret ARN placeholder และ region โดยไม่ใส่ secret value จริง
- ตรวจ deployed V2 API endpoints ว่าอ่านข้อมูลที่ import แล้วจาก Aurora
- เพิ่ม compatibility checks สำหรับ V1 routes/API
- เพิ่ม evidence checklist สำหรับปิดการ์ด
- ถ้ามี DB/table/data อยู่แล้ว ต้อง handle rerun/idempotency หรือบอก reset path ชัดเจน
- เพิ่มคำแนะนำ rollback/reset สำหรับ dev/demo environment

### ไม่ต้องทำ

- frontend/admin final demo docs ของ #81
- data extraction จาก PDF/source จริง
- production data migration เต็ม
- long-running scheduled import pipeline
- change schema โดยไม่มี migration ใหม่

## Required AWS / Env Configuration

ใช้ค่าจริงจาก CloudFormation outputs หรือ AWS Console แต่ห้าม commit secret value:

| Env var | ใช้ทำอะไร | Secret? |
|---|---|---|
| `AWS_REGION` | region AWS เช่น `ap-southeast-1` | no |
| `DB_CLUSTER_ARN` | RDS Data API resource ARN | no แต่ไม่ควรโชว์ใน UI |
| `DB_SECRET_ARN` | Secrets Manager ARN | no value, but backend-only |
| `DB_NAME` | database name เช่น `cs361v2` | no |
| `API_BASE_URL` | deployed API Gateway base URL สำหรับ V2 APIs | no |
| `FRONTEND_BASE_URL` | deployed frontend base URL ถ้ามี | no |
| `V1_BASE_URL` | deployed V1/frontend base URL ถ้าแยกจาก frontend | no |

Resource baseline จาก #48:

| Resource | Value |
|---|---|
| Region | `ap-southeast-1` |
| Foundation stack | `cs361-v2-aws-foundation-dev` |
| Aurora cluster | `cs361-v2-dev-aurora` |
| Database name | `cs361v2` |
| Secret name | `cs361-v2/dev/aurora/master` |

ดู ARN exact จาก CloudFormation stack outputs เท่านั้น:

```bash
aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-aws-foundation-dev \
  --query 'Stacks[0].Outputs' \
  --output table
```

## Expected Execution Order

การ์ดนี้ควรทำเป็นลำดับนี้:

1. Check AWS identity/region
2. Check Aurora/Data API connection
3. Run schema migration
4. Run master data seed
5. Import V2 fixture data
6. Verify Aurora table counts
7. Verify V2 API smoke tests
8. Verify V1 compatibility
9. Save evidence to issue/PR comment

## Migration / Seed / Import Inputs

### Schema

```text
database/migrations/001_base.sql
```

สร้างตารางหลักของ V2 เช่น:

- `faculty`
- `faculty_education`
- `faculty_interest`
- `academic_period`
- `evaluation_period`
- `work_category`
- `work_type`
- `work_item`
- `faculty_work_item`
- subtype detail tables
- `evidence_reference`
- `import_batch`
- `source_record`
- `app_user`, `app_role`, `app_user_role`
- `auth_login_event`
- `audit_event`

### Master Seed

```text
database/seeds/001_master_data.sql
```

Seed นี้ใช้ `ON CONFLICT` สำหรับ master data/roles และควรรันซ้ำได้ในระดับ seed

หมายเหตุ: `001_master_data.sql` อาจมี master data มากกว่า fixture demo เช่น `work_category = 6`, `work_type = 26` ใน environment ปัจจุบัน ขณะที่ `data/v2/fixtures/dataset-summary.json` ระบุ fixture categories/types เป็น 5/14 ดังนั้น verification ต้องแยก:

- master data seed count
- demo fixture data count

### Demo Fixtures

```text
data/v2/fixtures/faculties.json
data/v2/fixtures/academic-periods.json
data/v2/fixtures/evaluation-periods.json
data/v2/fixtures/work-items.json
data/v2/fixtures/faculty-work-items.json
data/v2/fixtures/teaching-details.json
data/v2/fixtures/publication-details.json
data/v2/fixtures/research-project-details.json
data/v2/fixtures/supervision-details.json
data/v2/fixtures/service-details.json
data/v2/fixtures/administration-details.json
data/v2/fixtures/evidence-references.json
data/v2/fixtures/dataset-summary.json
```

Fixture import order ที่แนะนำ:

1. faculty
2. academic periods
3. evaluation periods
4. work items
5. subtype detail tables
6. faculty work items
7. evidence references
8. import/source metadata ถ้า runner รองรับ

## Expected Demo Dataset Baseline

จาก `data/v2/fixtures/dataset-summary.json`:

| Metric | Expected |
|---|---:|
| faculties | 3 |
| academic years | 3 |
| academic periods | 5 |
| evaluation periods | 3 |
| fixture work categories | 5 |
| fixture work types | 14 |
| work items | 18 |
| faculty work items | 20 |
| teaching details | 4 |
| research project details | 3 |
| publication details | 3 |
| supervision details | 3 |
| service details | 3 |
| administration details | 2 |
| evidence references | 8 |

Work item visibility baseline:

| Visibility | Expected |
|---|---:|
| `PUBLIC` | 4 |
| `INTERNAL` | 12 |
| `RESTRICTED` | 2 |

Evidence visibility baseline:

| Visibility | Expected |
|---|---:|
| `PUBLIC` | 3 |
| `INTERNAL` | 3 |
| `RESTRICTED` | 2 |

Source baseline:

| Source | Expected |
|---|---:|
| faculty from V1 public profile | 3 |
| work items from V1 public profile | 1 |
| synthetic work items | 17 |

## Suggested Scripts / Commands

ถ้ายังไม่มี scripts เหล่านี้ ให้เพิ่มหรือ document equivalent commands:

```text
scripts/run-v2-db-migration.sh
scripts/run-v2-master-seed.sh
scripts/import-v2-demo-fixtures.sh
scripts/verify-v2-db-state.sh
scripts/smoke-v2-repository-api.sh
scripts/smoke-v1-compatibility.sh
```

ทุก script ควรใช้ env vars:

```bash
AWS_REGION=ap-southeast-1
DB_CLUSTER_ARN=<CloudFormation output DBClusterArn>
DB_SECRET_ARN=<CloudFormation output DBSecretArn>
DB_NAME=cs361v2
API_BASE_URL=<deployed API Gateway URL>
FRONTEND_BASE_URL=<deployed frontend URL>
```

Repo มี script foundation check อยู่แล้ว:

```bash
AWS_REGION=ap-southeast-1 \
DB_CLUSTER_ARN=<CloudFormation output DBClusterArn> \
DB_SECRET_ARN=<CloudFormation output DBSecretArn> \
DB_NAME=cs361v2 \
scripts/check-v2-aws-foundation.sh
```

## Idempotency / Rerun Rules

ต้องระบุให้ชัดว่ารันซ้ำได้อย่างไร:

- schema migration `001_base.sql` ใช้ `CREATE TABLE` baseline จึงอาจรันซ้ำไม่ได้ถ้าตารางมีอยู่แล้ว
- seed master data ใช้ `ON CONFLICT` และควรรันซ้ำได้
- fixture import ต้องเลือก strategy:
  - upsert โดยใช้ stable ids จาก fixture, หรือ
  - reset demo data ก่อน import
- reset path ต้องจำกัดเฉพาะ dev/demo environment เท่านั้น
- ห้าม reset production/unknown environment โดยไม่มี confirmation

Recommended dev/demo reset strategy:

```text
1. ยืนยันว่าเป็น dev/demo environment
2. backup หรือ export evidence ที่จำเป็น
3. truncate child tables ก่อน parent tables หรือ drop/recreate schema ตาม script ที่ทีมกำหนด
4. rerun migration
5. rerun seed
6. rerun fixture import
7. rerun verification
```

ห้ามใช้ destructive reset กับ environment ที่ไม่แน่ใจว่าเป็น dev/demo

## Database Verification SQL

### Core Counts

```sql
SELECT 'faculty' AS table_name, COUNT(*)::int AS row_count FROM faculty
UNION ALL SELECT 'academic_period', COUNT(*)::int FROM academic_period
UNION ALL SELECT 'evaluation_period', COUNT(*)::int FROM evaluation_period
UNION ALL SELECT 'work_category', COUNT(*)::int FROM work_category
UNION ALL SELECT 'work_type', COUNT(*)::int FROM work_type
UNION ALL SELECT 'work_item', COUNT(*)::int FROM work_item
UNION ALL SELECT 'faculty_work_item', COUNT(*)::int FROM faculty_work_item
UNION ALL SELECT 'teaching_detail', COUNT(*)::int FROM teaching_detail
UNION ALL SELECT 'publication_detail', COUNT(*)::int FROM publication_detail
UNION ALL SELECT 'research_project_detail', COUNT(*)::int FROM research_project_detail
UNION ALL SELECT 'supervision_detail', COUNT(*)::int FROM supervision_detail
UNION ALL SELECT 'service_detail', COUNT(*)::int FROM service_detail
UNION ALL SELECT 'administration_detail', COUNT(*)::int FROM administration_detail
UNION ALL SELECT 'evidence_reference', COUNT(*)::int FROM evidence_reference
ORDER BY table_name;
```

### Visibility Counts

```sql
SELECT visibility, COUNT(*)::int AS count
FROM work_item
GROUP BY visibility
ORDER BY visibility;
```

### Public Slug Compatibility

```sql
SELECT id, public_slug, name_th, status, visibility
FROM faculty
WHERE public_slug IN (
  'prapaporn-rattanatamrong',
  'kasidit-chanchio',
  'nuttanont-hongwarittorrn'
)
ORDER BY public_slug;
```

### Public Work Item Baseline

```sql
SELECT id, title, category_code, work_type_code, visibility, status
FROM work_item
WHERE visibility = 'PUBLIC'
  AND status = 'ACTIVE'
ORDER BY id;
```

Expected public work items from demo baseline:

- `wi-pub-2019-multi-container`
- `wi-pub-2024-privacy-edge`
- `wi-pub-2025-hci-agent`
- `wi-service-2568-speaker`

## V2 API Smoke Matrix

ต้อง smoke test deployed API Gateway URL จริง:

```text
GET /api/v2/academic-periods
GET /api/v2/evaluation-periods
GET /api/v2/work-categories
GET /api/v2/work-types
GET /api/v2/faculties
GET /api/v2/work-items
GET /api/v2/work-items?category=RESEARCH
GET /api/v2/work-items?type=PUBLICATION
GET /api/v2/work-items?q=privacy
GET /api/v2/work-items?category=TEACHING
GET /api/v2/work-items/wi-pub-2024-privacy-edge
GET /api/v2/work-items/wi-teach-2567-2-cs333
GET /api/v2/faculties/prapaporn-rattanatamrong/work-items
```

Expected:

- master data endpoints return `200`
- `GET /api/v2/faculties` returns faculty options with preserved public slugs
- `GET /api/v2/work-items` returns only `PUBLIC + ACTIVE`
- `category=RESEARCH` returns public research/publication records
- `type=PUBLICATION` returns public publications
- `q=privacy` returns `wi-pub-2024-privacy-edge` but not restricted/internal rows
- `category=TEACHING` returns empty list if teaching fixture remains `INTERNAL`
- detail `wi-pub-2024-privacy-edge` returns `200`
- detail `wi-teach-2567-2-cs333` returns public-safe `404`
- faculty work items route supports `prapaporn-rattanatamrong` slug

## V1 Compatibility Smoke Matrix

ต้องตรวจ deployed V1 routes/API จริง:

```text
GET /api/v1/faculties
GET /api/v1/faculties/prapaporn-rattanatamrong
GET /faculties
GET /faculties/prapaporn-rattanatamrong
```

Expected:

- HTTP `200`
- public slug เดิมยังใช้ได้
- list shape เดิมไม่ breaking
- detail shape เดิมไม่ breaking
- V1 route ไม่ต้อง login
- V1 response ไม่เริ่ม expose V2 internal/restricted fields

ถ้า environment ยังไม่มี deployed frontend route ให้บันทึกเหตุผลและตรวจ API/serving JSON compatibility แทน:

```text
build/v1/serving/faculties.json
build/v1/serving/faculties/prapaporn-rattanatamrong.json
```

แต่การปิดการ์ด production ควรมี deployed route evidence ถ้า deployment มีอยู่แล้ว

## Search / Filter Matrix จาก Demo Dataset

ใช้ `dataset-summary.json` เป็น baseline:

| Query | Expected IDs |
|---|---|
| Faculty `prapaporn-rattanatamrong`, Academic Year `2567` | teaching/research/service/admin records ของ prapaporn ในปี 2567 ตาม fixture |
| Academic Year `2567`, Category `TEACHING` | `wi-teach-2567-2-cs333`, `wi-teach-2567-2-cs333-lab` ใน DB/admin scope |
| Faculty `prapaporn-rattanatamrong`, Category `RESEARCH`, Type `PUBLICATION` | `wi-pub-2019-multi-container`, `wi-pub-2024-privacy-edge` |
| Keyword `privacy` | `wi-pub-2024-privacy-edge`, `wi-research-2567-privacy-platform`, `wi-supervision-2567-phd-thesis`, `wi-service-2568-speaker` in DB/admin scope |

หมายเหตุ: public APIs ต้องกรองตาม visibility/status ดังนั้นบาง expected IDs ใน dataset matrix จะไม่ออก public route ถ้าเป็น `INTERNAL` หรือ `RESTRICTED`

## Rollback / Reset Guidance

สำหรับ dev/demo เท่านั้น:

- ถ้า migration fail ก่อนสร้าง table ครบ ให้แก้ script แล้ว rerun หลัง reset schema
- ถ้า seed fail ให้ rerun seed ได้ถ้าใช้ `ON CONFLICT`
- ถ้า fixture import fail กลางทาง ควรใช้ transaction ต่อ batch หรือ reset fixture ids ก่อน import ซ้ำ
- ถ้า API smoke fail หลัง import ให้ตรวจ:
  - table counts
  - Lambda env vars
  - DB secret/cluster ARN
  - API Gateway route mapping
  - CloudWatch logs
- ถ้า V1 route fail ให้ rollback frontend/API deploy หรือ fix route config ก่อนปิด #80

## Security Rules

- ห้าม commit DB password
- ห้ามแปะ Secrets Manager secret value
- ห้ามแปะ AWS access key/secret key/session token
- ห้ามแปะ raw DB connection string ที่มี password
- ARN/resource names แนบได้เฉพาะเมื่อไม่ใช่ secret value
- evidence ต้อง redact account-sensitive/token/password fields
- restricted demo records ต้องไม่โผล่ public API

## QA Evidence ที่ต้องแนบตอนปิดการ์ด

ควรมี:

- AWS account/role identity แบบไม่เปิด key
- CloudFormation output names หรือ screenshot outputs ที่ redact ค่าอ่อนไหว
- Data API `SELECT 1` success
- command/log ว่า run migration สำเร็จ
- command/log ว่า run seed สำเร็จ
- command/log ว่า import fixtures สำเร็จ
- Aurora table count output
- visibility count output
- public slug compatibility output
- V2 API smoke output
- V1 API/route smoke output
- CloudWatch log group note สำหรับ API/import verification
- note เรื่อง rerun/reset/idempotency

## Acceptance Criteria

- [ ] schema migration ถูกรันกับ Aurora target environment แล้ว
- [ ] rerun/reset behavior ชัดเจน
- [ ] master seed ถูกรันกับ Aurora target environment แล้ว
- [ ] demo fixture import ถูกรันหรือมี command ที่ทำซ้ำได้กับ Aurora target environment
- [ ] มี verification counts จาก Aurora เทียบกับ `data/v2/fixtures/dataset-summary.json`
- [ ] visibility counts ตรงกับ expected baseline หรือมี explanation
- [ ] public slug เดิมยังอยู่ใน `faculty.public_slug`
- [ ] deployed V2 master data APIs อ่านจาก Aurora ได้จริง
- [ ] deployed V2 work item list/detail/faculty work-items APIs อ่าน demo data จาก Aurora ได้จริง
- [ ] public V2 APIs ไม่เปิด `INTERNAL`, `RESTRICTED`, หรือ `DELETED`
- [ ] deployed V1 public API/routes ยังทำงานและ response shape ไม่ breaking
- [ ] V1 public slug เดิมยังใช้ได้
- [ ] มี CloudWatch/API/Data API evidence สำหรับ migration/import/verification
- [ ] มี docs/evidence สำหรับคนอื่นที่มี IAM สิทธิ์เหมาะสมทำซ้ำได้
- [ ] docs/evidence ไม่เปิด secret value

## Review Checklist

Data:

- [ ] fixture import map เข้าตาราง Aurora ถูกต้อง
- [ ] source/provenance fields ถูกเก็บพอสำหรับ trace
- [ ] idempotency/rerun behavior ชัดเจน
- [ ] dataset count เทียบ `dataset-summary.json` แล้วอธิบาย difference ได้

Backend:

- [ ] API compatibility checks ผ่านบน deployed endpoints
- [ ] V1 adapter/projection ไม่เปลี่ยน contract เดิม
- [ ] Lambda/RDS Data API env ใช้ resource ARN ถูก environment
- [ ] CloudWatch logs พอ debug migration/import/API smoke ได้

QA:

- [ ] test matrix จาก `docs/v2/demo-dataset.md` หรือ `data/v2/fixtures/dataset-summary.json` ผ่านตาม public/admin scope
- [ ] V1 regression checks ผ่าน
- [ ] V2 public visibility checks ผ่าน
- [ ] Aurora counts แนบเป็น evidence

Security:

- [ ] docs ไม่เปิด secret value
- [ ] restricted demo records ไม่โผล่ public
- [ ] IAM ที่ใช้ migration/import มีสิทธิ์เท่าที่จำเป็นต่อ Data API/Secrets/S3 เท่านั้น
- [ ] reset/destructive command จำกัดเฉพาะ dev/demo และมี confirmation

## Dependencies

Blocked by:

- #47 Design Relational Schema & SQL Migration
- #48 Provision Aurora / Data API / Secret / IAM
- #49 Define V1 to V2 Data Mapping
- #50 Prepare Multi-Year Demo Dataset
- #64 Build Master Data API
- #66 Build Work Item List/Search/Filter API
- #67 Build Faculty Work Items API
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
- `aws`
- `ready-for-agent`

## Suggested Owner

Data/Backend Developer

Reviewers:

- Tech Lead
- Backend Developer
- QA / Integration
- Security Reviewer

## Estimate

1-2 days

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อทีมสามารถสร้าง V2 database state ใหม่ใน Aurora จาก repo ได้จริง, seed/import/verify ได้แบบทำซ้ำได้, deployed V2 APIs อ่านข้อมูลจาก Aurora ได้, public visibility rule ทำงานถูกต้อง, และพิสูจน์ด้วย evidence ว่า V1 public routes/API ยังไม่พังหลังเปิด V2 repository โดยไม่มี secret value หลุดใน docs หรือ GitHub issue
