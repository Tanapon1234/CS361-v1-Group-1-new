# CS361 Backend (FastAPI): Lecturer API v2

โครง backend สำหรับ API อาจารย์ (lecturer, education, research interest, expertise, publication, publication profile, profile image, CV)

**สถานะตอนนี้: เป็นโครงหลวม ๆ ให้ทีมเขียน logic ต่อเอง**

- **พร้อมใช้แล้ว**: database schema, model, controller ทุก endpoint, validation, error format, transaction, config
- **ยังเป็น stub** (`raise NotImplementedError  # TODO`): service และ DAO มี method ละ 1 ตัวต่อ endpoint โดยยังไม่ได้กำหนด business rule ไว้ ทุก endpoint ใน `/api/v2` จึงตอบ **501 Not Implemented** จนกว่าจะเขียน logic
- method ของ DAO เป็นแค่จุดเริ่มต้น เพิ่ม ลบ หรือเปลี่ยนชื่อได้ตามที่ service ต้องใช้

---

## เริ่มใช้งาน

ต้องใช้ Python 3.12 ขึ้นไป

```bash
cd backend
cp .env.example .env          # แล้วแก้ค่า DB_* ให้ตรงกับ database ที่จะต่อ

# วิธีที่แนะนำ: uv
uv sync
uv run fastapi dev            # http://127.0.0.1:8000/docs

# หรือใช้ pip (ต้องใช้ pip >= 25.1)
python3 -m venv .venv && source .venv/bin/activate
pip install -e . --group dev
fastapi dev
```

ตรวจว่าต่อ database ได้: `GET /health/ready` ต้องได้ `200` (ถ้าได้ `503` แปลว่าค่า `DB_*` ใน `.env` ยังผิด)

## Database

Schema อยู่ใน 2 ไฟล์ **ทั้งสองไฟล์คือ source of truth** ส่วน model ใน `app/v2/models/` ต้องตรงกับไฟล์เหล่านี้เสมอ

- [002_lecturer_profile.sql](../database/migrations/002_lecturer_profile.sql): ข้อมูลอาจารย์และผลงานวิชาการ (Academic Portfolio)
- [003_faculty_workload.sql](../database/migrations/003_faculty_workload.sql): ภาระงานประจำภาค (SemesterReport) ทำตาม design รวม [FacultyPortfolioWorkload.dbml](../database/data_schema/FacultyPortfolioWorkload/FacultyPortfolioWorkload.dbml) และเพิ่ม `cognito_sub` กับ `department_id` ให้ `lecturer`

สร้างตารางใน PostgreSQL ของตัวเอง (ตัวอย่างเช่น local):

```bash
createdb cs361v2
psql -d cs361v2 -f ../database/migrations/002_lecturer_profile.sql
psql -d cs361v2 -f ../database/migrations/003_faculty_workload.sql   # ต้องรันหลัง 002
```

| ตาราง | Primary key | หมายเหตุ |
|---|---|---|
| `lecturer` | `lecturer_id` uuid | `is_active` ใช้กับ activate/deactivate, ไฟล์เก็บใน `profile_image_url` / `cv_url` |
| `education` | `education_id` smallint | ของอาจารย์ 1 คน |
| `research_interest` + `faculty_research_interest` | `research_interest_id` smallint | master list + ตารางเชื่อมกับอาจารย์ |
| `expertise` + `faculty_expertise` | `expertise_id` smallint | master list + ตารางเชื่อมกับอาจารย์ |
| `publication` + `faculty_publication` | `publication_id` int | ตารางเชื่อมมี `author_order` |
| `publication_profile` | `publication_profile_id` smallint | `provider` เป็น text อิสระ เช่น "Google Scholar" |
| `department` | `id` smallint | master สาขาวิชา `lecturer.department_id` ชี้มาที่นี่ (ตอนนี้ยัง NULL ได้) |
| `member_position` | `id` uuid | ตำแหน่งบริหารของอาจารย์ (`end_date` NULL = ยังดำรงตำแหน่ง) |
| `rubric_version` → `rubric_category` → `rubric_section` → `rubric_item` | `id` smallint | เกณฑ์ภาระงานแบบมีหลายฉบับ |
| `evaluation_round` | `id` smallint | รอบประเมิน ผูกกับฉบับเกณฑ์ |
| `submission` + `submission_entry` | `id` uuid | ใบภาระงานของอาจารย์ 1 คนต่อ 1 รอบ และรายการในใบ |
| `entry_assessment`, `entry_evidence` | `id` uuid | ค่าที่ผู้ประเมินให้ และไฟล์หลักฐานใน S3 ของแต่ละรายการ |
| `submission_category_total`, `submission_approval` | | ยอดรายหมวดที่ freeze ตอนส่ง และประวัติส่ง/ตีกลับ/อนุมัติ |

- FK ใน 002 เป็น `ON DELETE CASCADE` ทุกตัว ถ้าลบอาจารย์หรือลบ master จะลบแถวในตารางเชื่อมไปด้วย
- FK ใน 003 **ไม่ cascade** ยกเว้น entry ที่ตามใบ (`submission_entry`) และ assessment/evidence ที่ตาม entry เพราะฉะนั้นอาจารย์ที่มีใบภาระงานหรือตำแหน่งแล้วจะลบไม่ได้ (ใช้ deactivate แทน)
- enum ของ PostgreSQL (เช่น `position_code`, `submission_status`) อยู่ใน `app/v2/models/enums.py`
- 003 มี trigger ที่ไม่ให้เพิ่ม แก้ หรือลบ `submission_entry` เมื่อใบไม่ได้อยู่ในสถานะ `draft` (DB จะตอบ error `check_violation`) และมี view `v_section_total` ที่คิดยอดรายข้อย่อยหลังตัดเพดานแล้ว
- ถ้าจะแก้ schema: แก้ไฟล์ SQL และ model ให้ตรงกัน เทสต์ `tests/v2/unit/test_models.py` จะ fail ถ้าชื่อตารางหรือ column ไม่ตรงกัน

## รันเทสต์และ lint

```bash
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

เทสต์ไม่ต้องใช้ database จริง ผลรันตอนนี้คือ `passed` + `xfailed`

- **passed**: เทสต์ controller (routing, validation, status code), error handler, config, transaction และความตรงกันของ model กับ SQL
- **xfailed**: service ละ 1 เทสต์ตัวอย่างใน `tests/v2/unit/services/` ใช้เป็นแบบเวลาเขียนเทสต์ของตัวเอง
  - ตอน service ยัง `raise NotImplementedError` จะนับเป็น XFAIL (ถือว่าผ่าน)
  - พอ implement แล้วเทสต์ผ่าน จะขึ้นเป็น **XPASS แล้ว fail ทันที** เพื่อเตือนให้ลบบรรทัด `pytestmark = pytest.mark.xfail(...)` ออก
  - เทสต์ตัวอย่างไม่ตรงกับวิธีที่เราออกแบบ? แก้หรือลบได้เลย

---

## โครงสร้าง

```text
backend/
├── pyproject.toml              dependencies, pytest, ruff, entrypoint ของ `fastapi dev`
├── .env.example                ตัวอย่าง env (copy ไปเป็น .env ห้าม commit .env)
├── app/
│   ├── main.py                 สร้าง FastAPI app: CORS, error handlers, include router ของแต่ละ version
│   ├── core/                   ส่วนกลาง ใช้ร่วมกันทุก version (ห้าม import จาก app/v2)
│   │   ├── config.py           Settings (pydantic-settings) + SettingsDep
│   │   ├── database.py         engine + session ต่อ 1 request (commit/rollback อัตโนมัติ) + SessionDep
│   │   ├── exceptions.py       NotFoundError, ConflictError, BadRequestError, ...
│   │   ├── error_handlers.py   แปลงทุก error เป็น application/problem+json
│   │   ├── problem.py          ProblemDetail (รูปแบบ error body)
│   │   └── health.py           GET /health, GET /health/ready
│   └── v2/                     ทุกอย่างของ API v2 (URL: /api/v2/...)
│       ├── router.py           รวม controller ทั้งหมดไว้ใต้ /api/v2
│       ├── dependencies.py     ประกอบ Session -> DAO -> Service (composition root)
│       ├── models/             [M] ตารางใน database ตรงกับ migration 002 + 003
│       ├── dtos/               [V] รูปร่าง request/response ของ API (Pydantic)
│       ├── controllers/        [C] path operations (APIRouter) บางที่สุด  (เสร็จแล้ว)
│       ├── services/           business logic  (TODO)
│       ├── daos/               DAO interface (ABC)  (เพิ่ม/แก้ method ได้)
│       │   └── sql/            DAO implementation ด้วย SQLModel  (TODO)
│       └── storage/            ObjectStorage interface + S3 implementation  (TODO)
├── tests/
│   ├── conftest.py             app/client fixtures (mock DB session)
│   ├── core/                   เทสต์ config, error handler, transaction, health
│   └── v2/
│       ├── test_api_contract.py  รายการ endpoint ของ v2 ที่ตกลงกันไว้ (ห้ามเกิน ห้ามขาด)
│       ├── api/                เทสต์ controller (mock service); test_lecturer_api.py เป็นตัวอย่างที่ละเอียดสุด
│       └── unit/
│           ├── services/       เทสต์ service (mock DAO) มีตัวอย่างไว้ 1 ตัวต่อไฟล์
│           └── test_models.py  model กับ SQL ต้องตรงกัน
└── v2/query/                   (ของเดิม) V2 master-data Lambda ไม่เกี่ยวกับโปรเจกต์นี้
```

### การแยก version

- โค้ดของแต่ละ API version อยู่ในโฟลเดอร์ของตัวเอง (`app/v2/`, `tests/v2/`) ส่วน `app/core/` ใช้ร่วมกันทุก version
- `app/core/` ห้าม import จาก `app/v2/` เพื่อให้เพิ่มหรือลบ version ได้โดยไม่กระทบส่วนกลาง
- ถ้าจะทำ v3: สร้าง `app/v3/` ที่มี `router.py` (prefix `/api/v3`) แล้ว include ใน `app/main.py` คู่กับ v2
  - ตารางใน database มีชุดเดียว ถ้า v3 ใช้ตารางเดิมให้ import model จาก `app.v2.models` ห้ามประกาศตารางชื่อเดิมซ้ำ (SQLModel จะ error)

### ลำดับการทำงานของ 1 request

```text
HTTP request
  -> controllers/   รับ path/query/body ที่ validate แล้วเป็น DTO, เรียก service
  -> services/      ตรวจกฎ, เรียก DAO, แปลง model -> response DTO
  -> daos/          (interface) <- daos/sql/ (SQLModel query)
  -> PostgreSQL
```

`app/v2/dependencies.py` เป็นที่เดียวที่เลือกว่าจะใช้ implementation ตัวไหน (เช่น `SqlLecturerDAO`, `S3ObjectStorage`) ส่วน controller และ service รู้จักแค่ interface

### กฎของแต่ละ layer

| Layer | ทำ | ห้ามทำ |
|---|---|---|
| controller | รับ DTO, เรียก service 1 method, คืน DTO | business logic, query DB, try/except |
| service | ตรวจกฎ, `raise NotFoundError` / `ConflictError` / `BadRequestError`, แปลง model เป็น DTO | `raise HTTPException`, เขียน SQL, คืน model ออกไป |
| DAO | query / add / flush | `session.commit()` (request เป็นคน commit), business rule |
| DTO | รูปร่าง API + validation ของ field | import table model |
| model | column, constraint, FK ให้ตรงกับ SQL | logic |

Transaction: `get_session` เปิด transaction 1 ครั้งต่อ request จะ commit เมื่อ endpoint ทำงานสำเร็จ และ rollback เมื่อมี error ใด ๆ โดย commit เกิด**ก่อน**ส่ง response (`scope="function"`)

ตัวอย่าง query ใน DAO ดูได้ใน docstring ของ `app/v2/daos/sql/base.py`

---

## สิ่งที่ปล่อยให้ทีมออกแบบเอง

ตัวอย่างคำถามที่ต้องตอบตอน implement (ยังไม่ได้กำหนดไว้ในโค้ด):

- email ซ้ำ, ชื่อ research interest ซ้ำ, หรือ DOI ซ้ำ จะตอบ `409` หรือไม่ (DB มี `UNIQUE` อยู่แล้ว ถ้าไม่ดักไว้จะได้ `500`)
- `q` ของแต่ละ list endpoint ค้นจาก column ไหนบ้าง
- `profile_image_url` / `cv_url` จะเก็บ URL สาธารณะ หรือเก็บ S3 key แล้วให้ `GET /cv` สร้าง presigned URL
- ไฟล์ชนิดไหนที่อนุญาต (ขนาดสูงสุดตั้งไว้แล้วใน `.env`: `PROFILE_IMAGE_MAX_BYTES`, `CV_MAX_BYTES`)
- จะใช้ presigned POST หรือ PUT (`UploadPresignResponse.fields` ปล่อยว่างได้ถ้าใช้ PUT)
- ลบ master (research interest / expertise) ที่ยังมีอาจารย์ใช้อยู่ได้ไหม (schema ตอนนี้เป็น CASCADE ลบตามได้)

## เพิ่ม endpoint ใหม่ (checklist)

1. `tests/v2/test_api_contract.py`: เพิ่ม `(METHOD, path)` ในรายการ
2. `app/v2/dtos/`: request / response DTO
3. ถ้ามีตารางใหม่: แก้ไฟล์ SQL ใน `database/migrations/` แล้วเพิ่ม model ใน `app/v2/models/` (และ import ใน `__init__.py`)
4. `app/v2/daos/xxx_dao.py`: เพิ่ม abstract method แล้ว implement ใน `app/v2/daos/sql/xxx_dao.py`
5. `app/v2/services/`: เพิ่ม method พร้อมเทสต์ใน `tests/v2/unit/services/`
6. `app/v2/controllers/`: เพิ่ม path operation พร้อมเทสต์ใน `tests/v2/api/`
7. ถ้าเป็น service/DAO ใหม่ ให้ wire ใน `app/v2/dependencies.py`; ถ้าเป็น controller ใหม่ ให้เพิ่มใน `app/v2/router.py`

## ข้อตกลงของ API

- **JSON field** ใช้ snake_case ตรงกับชื่อ column ใน database เช่น `lecturer_id`, `name_th`, `is_active`
- **Path parameter** ใช้ `{lecturer_id}` (URL จริงเหมือน `{lecturerId}` ในเอกสารรายการ API)
- **ID**: `lecturer_id` เป็น UUID, ID อื่นเป็นตัวเลข (ตาม schema) ถ้าส่ง ID ผิดรูปแบบหรือเกินช่วงของ smallint จะได้ 422 ก่อนถึง service
- **Status code**: สร้าง = `201`, ลบ = `204` (ไม่มี body), อ่าน/แก้ = `200`
- **List response** มี 2 แบบ ที่หน้าตาเดียวกัน (`items` + `meta`)
  - `PageResponse`: collection ที่โตได้ไม่จำกัด (`/lecturers`, `/publications`, master lists) รับ `?limit=20&offset=0` (limit สูงสุด 100) ได้ `meta: {total, limit, offset}`
  - `ListResponse`: รายการย่อยของอาจารย์ 1 คน (educations, profiles, interests) ได้ `meta: {count}` เหมือน V2 master-data API เดิม
- **PATCH** อัปเดตเฉพาะ field ที่ส่งมา (`model_dump(exclude_unset=True)`) ส่วน **PUT** `/research-interests` และ `/expertise` ของอาจารย์จะแทนที่ทั้งชุด
- **Activate / deactivate** เปลี่ยน `lecturer.is_active`
- **Upload ไฟล์** (profile image / CV) ทำ 3 ขั้น: `presign` ได้ presigned S3 URL, client อัปโหลดตรงไป S3, แล้วเรียก `complete` ให้ server บันทึกลง `lecturer.profile_image_url` / `cv_url` (ตอบกลับเป็น lecturer)

### Error format (RFC 9457 / RFC 7807)

ทุก error ตอบเป็น `Content-Type: application/problem+json`

```json
{
  "type": "urn:cs361:problem:validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "The request contains invalid fields.",
  "instance": "/api/v2/lecturers",
  "errors": [{ "field": "body.email", "message": "value is not a valid email address" }]
}
```

| `type` | Status | ใช้เมื่อ |
|---|---|---|
| `urn:cs361:problem:bad-request` | 400 | `raise BadRequestError(...)` ข้อมูลผิดกฎที่ทีมกำหนด |
| `urn:cs361:problem:not-found` | 404 | `raise NotFoundError(...)` หรือ URL ไม่มีอยู่จริง |
| `urn:cs361:problem:method-not-allowed` | 405 | ใช้ HTTP method ผิด |
| `urn:cs361:problem:conflict` | 409 | `raise ConflictError(...)` เช่น ข้อมูลซ้ำ |
| `urn:cs361:problem:validation-error` | 422 | request field ไม่ถูกต้อง (ดูรายละเอียดใน `errors[]`) |
| `urn:cs361:problem:internal-error` | 500 | error ที่ไม่ได้คาดไว้ (ดูรายละเอียดใน log) |
| `urn:cs361:problem:not-implemented` | 501 | endpoint ยังไม่ได้ implement |
| `urn:cs361:problem:service-unavailable` | 503 | ต่อ database ไม่ได้ |

---

## Environment variables

ดูค่าทั้งหมดและคำอธิบายได้ใน [.env.example](.env.example) ค่าจะถูกโหลดผ่าน `app/core/config.py`

- ถ้า `ENVIRONMENT` ไม่ใช่ `local` แล้ว `DB_PASSWORD` ยังเป็นค่า placeholder แอปจะไม่ยอม start
- ถ้า `ENVIRONMENT=prod` จะปิด `/docs` และ `/openapi.json`
- ต่อ Aurora ให้ตั้ง `DB_SSLMODE=require`
- password จริงเก็บใน AWS Secrets Manager ห้ามใส่ใน repo (ดู `docs/v2/security.md`)

---

## เรื่องที่ยังค้างอยู่

1. **ยังไม่มี authentication**: endpoint ที่แก้ข้อมูล (POST/PATCH/PUT/DELETE) ควรจำกัดให้ admin ผ่าน Cognito JWT เพิ่มเป็น dependency ระดับ router ได้
2. **การต่อ database**: โครงนี้ต่อ PostgreSQL ตรงผ่าน psycopg ขณะที่ V2 Lambda เดิม (`backend/v2/`) ใช้ RDS Data API ถ้าจะใช้ Data API ให้เขียน DAO implementation ชุดใหม่แล้วเปลี่ยนใน `app/v2/dependencies.py` ได้เลย โดยไม่ต้องแก้ service
3. **DAO integration test** กับ PostgreSQL จริงยังไม่มี ควรเพิ่มเมื่อเริ่ม implement DAO (ใช้ database แยกสำหรับเทสต์ ห้ามใช้ dev DB)
4. **Migration `002_lecturer_profile.sql` และ `003_faculty_workload.sql` ยังไม่ได้รันบน Aurora** ต้องให้คนที่ดูแล database รันเอง
