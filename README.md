# CS361 Faculty Output & Workload Management System

ระบบจัดเก็บ ค้นหา แสดงผล และบริหารข้อมูลผลงาน/ภาระงานของอาจารย์ สำหรับโปรเจกต์ CS361 Cloud Projects

เอกสารนี้เป็นหน้าแรกของ repository เริ่มอ่านจากไฟล์นี้ แล้วตามลิงก์ไปยังรายละเอียดของแต่ละส่วน

## สถานะปัจจุบัน

| เวอร์ชัน | เป้าหมาย | สถานะ |
|---|---|---|
| V1 | เว็บอ่านข้อมูลอาจารย์แบบสาธารณะ (read-only) | เสร็จ ใช้งานอยู่ |
| V2 | Faculty Output Repository: FastAPI backend, Aurora, หน้า back-office | โค้ดครบ รอ deploy และทดสอบบน AWS |
| V3 | Secure Faculty Workspace: login, role, ตรวจสอบข้อมูล, audit log | โค้ดครบ รอตั้ง Cognito และทดสอบบน AWS |

ที่ยังไม่ได้ทำ (ต้องใช้ AWS credentials): รัน migration บน Aurora, deploy backend, deploy frontend, สร้าง Cognito user pool, smoke test, ซ้อม peer test ติดตามได้ที่ GitHub issues ที่ยังเปิดอยู่

## แต่ละเวอร์ชันทำอะไร

**V1**: แสดงรายชื่อ โปรไฟล์ และผลงานที่เปิดเผยได้ ไม่ต้อง login ไม่มีการแก้ข้อมูล

**V2**: ย้ายเป็นฐานข้อมูลกลางที่แก้ไขได้ผ่าน API

- โปรไฟล์อาจารย์: ประวัติการศึกษา ความสนใจ ความเชี่ยวชาญ ผลงานตีพิมพ์ รูปโปรไฟล์ CV
- ภาระงานประจำภาค (workload / SemesterReport): ใบรายงาน รายการงาน หลักฐาน การประเมิน การอนุมัติ
- หน้า "ผลงานตามปี" ดูงานของอาจารย์แต่ละคนแยกตามปีการศึกษาและหมวด
- หน้า back-office ที่ `/manage`

**V3**: ทำให้ใช้งานจริงได้อย่างปลอดภัย

- login ด้วย Amazon Cognito backend ตรวจ ID token และเชื่อมผู้ใช้กับ record อาจารย์
- บทบาท `lecturer`, `staff`, `reviewer`, `executive`, `admin` และตำแหน่งหัวหน้า/กรรมการสาขา ตรวจสิทธิ์ที่ router และ service ทุก endpoint
- front-end แสดงเฉพาะปุ่มที่ผู้ใช้ทำได้
- ผู้ตรวจ (reviewer) รับรองผลงานตีพิมพ์และไฟล์หลักฐาน (`pending` / `verified` / `rejected`) โดยรับรองงานของตัวเองไม่ได้
- audit log บันทึกทุกการเพิ่ม แก้ ลบ (ใคร บทบาท request ค่าที่เปลี่ยน) admin เปิดดูได้
- `/api/v3` เป็นสำเนาของ `/api/v2` เพื่อให้พัฒนา V3 ต่อโดยไม่กระทบ V2

## สถาปัตยกรรม

```text
Browser
  -> Next.js (frontend/)  Server Actions + httpOnly cookie, Cognito login ฝั่ง server
  -> API Gateway
  -> Lambda (Mangum + FastAPI, backend/)  อยู่ใน VPC
  -> Aurora PostgreSQL Serverless v2
              |-> Secrets Manager (รหัสผ่าน database)
              |-> S3 (รูปโปรไฟล์ CV ไฟล์หลักฐาน ผ่าน presigned URL)
Cognito User Pool  -> ออก ID token ให้ backend ตรวจ (RS256, JWKS)
```

backend แบ่งชั้น controller -> service -> DAO -> model และ DTO แยกต่างหาก error ตอบเป็น `application/problem+json`

## โครงสร้างโฟลเดอร์

| Folder | ใช้ทำอะไร |
|---|---|
| `backend/` | FastAPI: `app/v2` และ `app/v3` (แต่ละชุดมี controller, service, DAO, DTO), tests, scripts |
| `frontend/` | Next.js 16: หน้า public, `/login`, `/manage` |
| `database/` | SQL migrations 001-006 และ seed |
| `infra/v2/` | CloudFormation: foundation, backend API, Cognito |
| `scripts/` | deploy, smoke test, import/migrate ข้อมูล V1 |
| `data/` | mapping, fixture, demo dataset |
| `docs/` | เอกสารออกแบบ ข้อตัดสินใจ คู่มือทีม |
| `evidence/` | หลักฐาน deploy/test |
| `postman/` | collection สำหรับลองยิง API |

## เริ่มรันในเครื่อง

ต้องมี Python 3.12+, Node.js และ PostgreSQL

**1. Database**

```bash
createdb cs361v2
cd backend
uv sync
uv run python -m scripts.apply_migrations --database-url postgresql://postgres@localhost/cs361v2
```

**2. Backend** (http://127.0.0.1:8000/docs)

```bash
cd backend
cp .env.example .env      # แก้ DB_* ให้ตรงกับ database
uv run fastapi dev
```

โหมดพัฒนาใช้ header `X-Lecturer-Id` และ `X-Dev-Roles` แทน token (ใช้ได้เมื่อ `ENVIRONMENT` ไม่ใช่ `prod` และ `DEV_AUTH_HEADER_ENABLED=true`)

**3. Frontend** (http://localhost:3000)

```bash
cd frontend
npm install
npm run dev
```

ถ้าไม่ตั้ง `COGNITO_CLIENT_ID` จะเป็นโหมดพัฒนา เลือกผู้ใช้ได้ที่ `/manage/switch-user` ตัวแปรทั้งหมดดูใน [frontend/README.md](frontend/README.md)

## ทดสอบ

```bash
cd backend
uv run pytest             # unit + permission tests ของ v2 และ v3
uv run ruff check
```

integration test ต้องตั้ง `TEST_DATABASE_URL` ชี้ไป PostgreSQL ที่ใช้ทดสอบเท่านั้น เพราะเทสต์จะลบ schema `public` แล้วสร้างใหม่ รายละเอียดดู [backend/README.md](backend/README.md)

## Deploy บน AWS

region `ap-southeast-1` ลำดับคือ foundation (Aurora, S3, secret) -> migration -> Cognito -> backend API -> frontend

```bash
scripts/setup-v2-aws-foundation.sh
scripts/deploy-v2-cognito.sh
scripts/deploy-v2-backend-api.sh
scripts/smoke-v2-backend-api.sh
```

รายละเอียดและค่าพารามิเตอร์ดู [infra/v2/README.md](infra/v2/README.md) และ [docs/v2/deployment-env.md](docs/v2/deployment-env.md)

ก่อน deploy จริงต้องตั้ง `DEV_AUTH_HEADER_ENABLED=false` ไม่เช่นนั้นใครก็ปลอมตัวด้วย header ได้ (backend ปิดให้เองเมื่อ `ENVIRONMENT=prod`)

ห้ามใส่ secret, รหัสผ่าน database, AWS access key หรือ session token ลง GitHub

## วิธีทำงาน

- ทุกงานมี GitHub issue (milestone V2 หรือ V3) แตก branch จาก `develop` ชื่อ `<เลข issue>-<หัวข้อสั้นๆ>`
- เปิด PR เข้า `develop` ใส่ `Closes #<เลข>` ถ้างานเสร็จจริง ใส่ `Refs #<เลข>` ถ้ายังต้องทดสอบบน AWS
- `develop` -> `main` ทำเมื่อทีมตรวจแล้วเท่านั้น
- แก้ schema ต้องเพิ่มไฟล์ migration ใหม่ ห้ามแก้ไฟล์เดิมที่รันไปแล้ว และอัปเดต model กับเอกสาร

## เอกสารที่ควรรู้จัก

| เรื่อง | ไฟล์ |
|---|---|
| backend, API, schema, ตัวอย่างเรียกใช้ | [backend/README.md](backend/README.md) |
| frontend และตัวแปร environment | [frontend/README.md](frontend/README.md) |
| บทบาทและตารางสิทธิ์ | [docs/v2/permissions.md](docs/v2/permissions.md) |
| ความปลอดภัย | [docs/v2/security.md](docs/v2/security.md) |
| ต่อ database จาก Lambda | [docs/v2/backend-db-connection-decision.md](docs/v2/backend-db-connection-decision.md) |
| เคสทดสอบ peer test V3 | [docs/v2/peer-test-v3.md](docs/v2/peer-test-v3.md) |
| ซ้อม peer test V2 | [docs/v2/peer-test-rehearsal.md](docs/v2/peer-test-rehearsal.md) |
| ภาพรวมการออกแบบ V2 | [docs/v2/V2_Central_Design.md](docs/v2/V2_Central_Design.md) |
| ERD และคู่มือตาราง | [docs/v2/erd.md](docs/v2/erd.md), [docs/v2/erd-table-attribute-guide.md](docs/v2/erd-table-attribute-guide.md) |
| คู่มือกลางทีม (AWS access, workflow, หลักฐาน) | [docs/v2/team-handbook/](docs/v2/team-handbook/README.md) |
| V1 | [docs/v1/](docs/v1/) |
