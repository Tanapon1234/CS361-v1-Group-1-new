# CS361 Faculty Output & Workload Management System

ระบบจัดเก็บ ค้นหา แสดงผล และบริหารข้อมูลผลงาน/ภาระงานของอาจารย์ สำหรับโปรเจกต์ CS361 Cloud Projects

เอกสารนี้เป็นหน้าแรกของ repository สำหรับคนในทีมที่เพิ่งเข้ามาอ่าน ให้เริ่มจากไฟล์นี้ก่อน แล้วค่อยตามลิงก์ไปยังคู่มือ V2 รายละเอียดด้านล่าง

## สถานะปัจจุบันแบบสั้น

| ส่วน | สถานะ |
|---|---|
| V1 | ทำระบบ public read-only faculty information service แล้ว |
| V2 | กำลังพัฒนา Faculty Output Repository บน AWS จริง |
| Database | มี Aurora PostgreSQL Serverless v2 แล้ว และมีตาราง/ข้อมูล demo dataset แล้ว |
| Production path แรกของ V2 | Issue #64 Master Data API deploy แล้ว: API Gateway -> Lambda -> RDS Data API -> Aurora |
| AWS Region | `ap-southeast-1` |
| V2 API endpoint ปัจจุบัน | `https://n89gqgnqw2.execute-api.ap-southeast-1.amazonaws.com` |

## โปรเจกต์นี้ทำอะไร

โจทย์หลักคือระบบผลงานและภาระงานอาจารย์ หรือ Faculty Output & Workload Management System

เป้าหมายปลายทางคือมีระบบกลางที่:

- เก็บข้อมูลอาจารย์
- เก็บข้อมูลการสอน งานวิจัย งานบริการ การดูแลนักศึกษา และภาระงานที่เกี่ยวข้อง
- รองรับหลายปีการศึกษา
- ค้นหา กรอง และเรียกดูข้อมูลตามเงื่อนไขได้
- มี role/login/admin workflow สำหรับข้อมูลภายใน
- ใช้ข้อมูลเพื่อสรุปรายงานและ workload sheet ได้ในระยะถัดไป

## V1 คืออะไร

V1 เป็นระบบอ่านข้อมูลสาธารณะแบบ read-only

สิ่งที่ V1 ทำ:

- แสดงรายชื่ออาจารย์
- แสดง profile อาจารย์
- แสดงผลงานที่เปิดเผยได้
- ค้นหา/กรองจากข้อมูลที่เตรียมไว้
- ไม่ต้อง login
- ใช้สำหรับผู้ใช้ทั่วไป เช่น นักศึกษาที่อยากหาอาจารย์ที่ปรึกษา

V1 ยังไม่ทำ:

- login/role
- admin edit
- workflow ตรวจสอบข้อมูล
- database กลางแบบหลายปีเต็มรูปแบบ
- workload/report generation

## V2 คืออะไร

V2 คือ Faculty Output Repository

เป้าหมายของ V2 คือย้ายจากข้อมูลแบบอ่านอย่างเดียว ไปสู่แหล่งข้อมูลกลางที่จัดการได้จริง รองรับข้อมูลหลายปี และใช้ต่อยอดเป็น API/UI/admin workflow ได้

สิ่งที่ V2 ต้องตอบโจทย์:

- ข้อมูลอาจารย์ การสอน งานวิจัย งานบริการ การดูแลนักศึกษา และภาระงานที่เกี่ยวข้องถูกจัดเก็บเป็น schema ชัดเจน
- รองรับหลายปีการศึกษาและหลายรอบประเมิน
- ค้นหา กรอง และดูรายละเอียดผลงานได้
- เชื่อมกับ AWS จริง ไม่ใช่ mock อย่างเดียว
- มีเส้นทางสำหรับ public read API
- มีเส้นทางสำหรับ admin/auth/mutation ในการ์ดถัดไป
- มีหลักฐานการ deploy/test ที่ตรวจสอบย้อนกลับได้

## เริ่มอ่านจากตรงไหน

แนะนำอ่านตามลำดับนี้:

1. [คู่มือกลางทีม V2](docs/v2/team-handbook/README.md)
2. [ภาพรวมระบบ: จาก V1 ไป V2](docs/v2/team-handbook/01-system-overview.md)
3. [คู่มือฐานข้อมูล V2](docs/v2/team-handbook/02-database-guide.md)
4. [คู่มือ AWS Access และการ Setup โปรเจกต์](docs/v2/team-handbook/03-aws-access-and-setup.md)
5. [คู่มือ Workflow และ Issue Cards ของ V2](docs/v2/team-handbook/04-development-workflow-and-issue-cards.md)
6. [คู่มือการทดสอบ การตรวจสอบ และหลักฐาน](docs/v2/team-handbook/05-testing-verification-and-evidence.md)
7. [โครงสร้างโฟลเดอร์ GitHub และวิธีเริ่มงาน](docs/v2/team-handbook/06-github-folder-structure.md)
8. [Issue cards ทั้งหมดของ V2](docs/v2/issues/)

ถ้าได้รับการ์ดจาก GitHub ให้เริ่มจาก issue card ของตัวเองใน `docs/v2/issues/` แล้วเปิดคู่มือที่เกี่ยวข้องประกอบ

## สถาปัตยกรรมปัจจุบันของ V2

เส้นทาง public read API:

```text
User / Frontend
  -> API Gateway
  -> Lambda
  -> RDS Data API
  -> Aurora PostgreSQL Serverless v2
```

เส้นทาง admin ที่เตรียมไว้สำหรับการ์ดถัดไป:

```text
Admin User
  -> Cognito
  -> protected API Gateway
  -> Admin Lambda
  -> RDS Data API transaction
  -> Aurora PostgreSQL Serverless v2
  -> audit_event
```

เส้นทางข้อมูล/หลักฐาน:

```text
Data preparation / import scripts
  -> S3 landing/archive
  -> import Lambda หรือ migration script
  -> Aurora
  -> evidence/reference metadata
```

## AWS Resources สำคัญ

| Resource | Name |
|---|---|
| Region | `ap-southeast-1` |
| Foundation stack | `cs361-v2-aws-foundation-dev` |
| Master Data API stack | `cs361-v2-master-data-api-dev` |
| Aurora cluster | `cs361-v2-dev-aurora` |
| Database | `cs361v2` |
| DB secret name | `cs361-v2/dev/aurora/master` |
| Data/artifact bucket | `cs361-v2-aws-foundation-dev-v2databucket-itl5uq2sozge` |
| Query Lambda | `cs361-v2-dev-query` |
| Query log group | `/aws/lambda/cs361-v2-dev-query` |
| Master Data API endpoint | `https://n89gqgnqw2.execute-api.ap-southeast-1.amazonaws.com` |

ห้ามใส่ secret value, database password, AWS access key หรือ session token ลง GitHub

## ฐานข้อมูลปัจจุบันมีอะไร

Aurora ตอนนี้มี schema และ demo data สำหรับ V2 แล้ว

จำนวนข้อมูลล่าสุดที่ใช้เป็น baseline:

| Table | Count |
|---|---:|
| `academic_period` | 5 |
| `evaluation_period` | 3 |
| `work_category` | 6 |
| `work_type` | 26 |
| `faculty` | 3 |
| `work_item` | 18 |
| `faculty_work_item` | 20 |
| `evidence_reference` | 8 |

รายละเอียดทุกตารางและทุก attribute อยู่ที่ [คู่มือฐานข้อมูล V2](docs/v2/team-handbook/02-database-guide.md)

## API ที่ deploy แล้ว

Issue #64 Master Data API deploy แล้วบน AWS จริง

Base URL:

```text
https://n89gqgnqw2.execute-api.ap-southeast-1.amazonaws.com
```

Routes:

```text
GET /api/v2/academic-periods
GET /api/v2/evaluation-periods
GET /api/v2/work-categories
GET /api/v2/work-types
GET /api/v2/faculties
```

คำอธิบาย API อยู่ที่ `docs/v2/master-data-api.md`

## วิธี setup เครื่องแบบสั้น

1. clone หรือ pull repo
2. ตั้งค่า AWS CLI ด้วย account ของตัวเอง
3. ตั้ง region เป็น `ap-southeast-1`
4. เช็คตัวตนด้วย `aws sts get-caller-identity`
5. เข้า `frontend/` แล้วรัน `npm install`
6. รัน test ที่เกี่ยวข้องกับการ์ดของตัวเอง

รายละเอียดเต็มอยู่ที่ [คู่มือ AWS Access และการ Setup โปรเจกต์](docs/v2/team-handbook/03-aws-access-and-setup.md)

## วิธีทำงานตาม Issue Card

มาตรฐาน branch:

```text
CS361-<issue-number>
```

ตัวอย่าง:

```text
CS361-66
```

ลำดับทำงาน:

1. อ่าน issue card ใน `docs/v2/issues/`
2. อ่าน dependency ว่าต้องรอการ์ดไหนก่อน
3. อ่าน database/API/AWS docs ที่เกี่ยวข้อง
4. สร้าง branch ตามเลข issue
5. implement เฉพาะ scope ของการ์ด
6. test local
7. deploy/smoke test บน AWS ถ้าการ์ดเป็น production API/UI/admin
8. update docs/evidence
9. tick checklist ใน issue card เฉพาะข้อที่ทำจริง
10. commit/push
11. comment หลักฐานใน GitHub issue

รายละเอียด workflow อยู่ที่ [คู่มือ Workflow และ Issue Cards ของ V2](docs/v2/team-handbook/04-development-workflow-and-issue-cards.md)

## การ์ด V2 ตอนนี้

การ์ดที่ทำเสร็จแล้วตาม repo/project:

- #46 Freeze Scope, Architecture & Interface Contracts
- #47 Design Relational Schema & SQL Migration
- #48 Provision Aurora / Data API / Secret / IAM
- #49 Define V1 to V2 Data Mapping
- #50 Prepare Multi-Year Demo Dataset
- #64 Build Master Data API

การ์ดที่พร้อมให้ทีมทำต่อ:

- #66 Work Item List/Search/Filter API
- #67 Faculty Work Items API
- #68 Work Item Detail API
- #69 Configure Admin Authentication
- #70 Admin Create Work Item API
- #71 Admin Update / Soft Delete API
- #72 Repository Page Shell & Filter UI
- #73 Repository Result List & Pagination UI
- #74 Work Item Detail UI
- #75 Integrate Repository UI with Real API
- #76 Admin Login UI
- #77 Admin Work Item List UI
- #78 Admin Create/Edit Form UI
- #79 Integrate Admin UI with Auth & CRUD API
- #80 Execute Migration & Preserve V1 Compatibility
- #81 Final Integration / Deploy / Demo Docs

รายละเอียด dependency และลำดับแบ่งงานอยู่ที่ [คู่มือ Workflow และ Issue Cards ของ V2](docs/v2/team-handbook/04-development-workflow-and-issue-cards.md)

## คำสั่งตรวจที่ใช้บ่อย

Backend #64 unit tests:

```bash
python3 -m unittest backend.v2.query.test_master_data
```

Frontend master data contract test:

```bash
cd frontend
npm run test:v2:master-data
```

Smoke test Master Data API:

```bash
AWS_REGION=ap-southeast-1 \
API_STACK=cs361-v2-master-data-api-dev \
scripts/smoke-v2-master-data-api.sh
```

รายละเอียดการทดสอบและ template สำหรับ comment ปิด issue อยู่ที่ [คู่มือการทดสอบ การตรวจสอบ และหลักฐาน](docs/v2/team-handbook/05-testing-verification-and-evidence.md)

## โครงสร้างโฟลเดอร์แบบเร็ว

| Folder | ใช้ทำอะไร |
|---|---|
| `backend/` | Lambda/backend code ของ V2 |
| `frontend/` | Next.js UI ทั้ง public และ admin |
| `infra/` | CloudFormation/IaC สำหรับ AWS |
| `database/` | SQL migrations และ seed |
| `data/` | mapping, fixture, demo dataset |
| `docs/` | design docs, issue cards, team handbook |
| `evidence/` | หลักฐาน deploy/test สำหรับปิดการ์ด |
| `scripts/` | deploy/smoke/import/helper scripts |
| `build/` | generated/build artifacts ไม่ใช่ source of truth |
| `fixtures/` | fixture เดิมบางส่วน โดยเฉพาะของ V1/test |

รายละเอียดเต็มอยู่ที่ [โครงสร้างโฟลเดอร์ GitHub และวิธีเริ่มงาน](docs/v2/team-handbook/06-github-folder-structure.md)

## ข้อควรระวัง

- อย่า commit secret หรือ credential ทุกชนิด
- อย่าปิดการ์ด production ด้วย mock/local อย่างเดียว
- ถ้าแก้ API จริง ต้องมีหลักฐานจาก API Gateway/Lambda/Aurora
- ถ้าแก้ database ต้องอัปเดต docs และมีวิธีตรวจ count/query
- ถ้า Aurora หยุดเพราะ auto-pause ให้รอ 15-30 วินาทีแล้ว retry smoke test
- ถ้างานไม่เกี่ยวกับ V1 อย่าแก้ไฟล์ V1 โดยไม่จำเป็น

## เอกสารที่ควรรู้จัก

- `docs/v2/team-handbook/` คือคู่มือกลางทีม
- `docs/v2/issues/` คือรายละเอียด issue card
- `docs/v2/master-data-api.md` คือ contract ของ #64
- `docs/v2/v2-data-mapping.md` และไฟล์ mapping ใน `data/v2/` ใช้กับ migration
- `database/migrations/001_base.sql` คือ schema หลักของ V2
- `database/seeds/001_master_data.sql` คือ master data seed

ถ้าจะพัฒนาต่อ ให้เริ่มจาก issue card ของตัวเอง แล้วตามคู่มือกลางทีมเป็นหลัก
