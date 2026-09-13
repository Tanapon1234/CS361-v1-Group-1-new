# [V2] Integrate Repository UI with Real API #75

## สรุป

เชื่อมหน้า public V2 repository (`/outputs` และ `/outputs/{id}`) กับ deployed V2 APIs จริงบน AWS แทน mock/fixture เพื่อให้ flow ค้นหา กรอง แสดงรายการ แบ่งหน้า และเปิดรายละเอียด ทำงาน end-to-end กับข้อมูลใน Aurora ได้จริง

หมายเหตุเลขการ์ด: การ์ดนี้เทียบกับ design baseline เดิม #61 แต่ GitHub issue จริงใช้ #75

## Production AWS Requirement

การ์ดนี้เป็น public repository E2E integration gate ต้องทดสอบ frontend กับ deployed AWS APIs จริงทั้งหมด:

```text
Frontend deployment
→ API Gateway public routes
→ Lambda read handlers
→ RDS Data API
→ Aurora PostgreSQL Serverless v2
```

ห้ามปิดการ์ดด้วย local/mock API เท่านั้น

ต้องใช้ API Gateway base URL จริง เช่น:

```text
NEXT_PUBLIC_V2_API_BASE_URL=https://n89gqgnqw2.execute-api.ap-southeast-1.amazonaws.com
```

AWS baseline ที่มีอยู่จาก #64:

| Resource | Value |
|---|---|
| Region | `ap-southeast-1` |
| Foundation stack | `cs361-v2-aws-foundation-dev` |
| API stack | `cs361-v2-master-data-api-dev` |
| API endpoint | `https://n89gqgnqw2.execute-api.ap-southeast-1.amazonaws.com` |
| Lambda function | `cs361-v2-dev-query` |
| CloudWatch log group | `/aws/lambda/cs361-v2-dev-query` |

ถ้า backend read APIs #66/#68 ใช้ stack/function ชื่อใหม่ ให้บันทึกชื่อจริงเพิ่มใน QA evidence ของการ์ดนี้

## Background

การ์ด #72-#74 สร้าง UI surface:

- #72: หน้า `/outputs` และ filter shell
- #73: result list + pagination
- #74: detail page `/outputs/{id}`

การ์ด #64-#68 สร้าง read APIs:

- #64: Master Data API
- #66: Work Item List/Search/Filter API
- #68: Work Item Detail API

การ์ด #75 คือจุดรวมที่พิสูจน์ว่า public V2 repository ใช้งานกับข้อมูลจริงใน Aurora ผ่าน API Gateway/Lambda ได้ครบ flow ไม่ใช่แค่ UI ที่ต่อ fixture หรือ backend ที่ test แยกกัน

## ความเกี่ยวข้องกับโจทย์

โจทย์ V2 ต้องรองรับการจัดเก็บและเรียกดูข้อมูลผลงาน/ภาระงานอาจารย์อย่างเป็นระบบ หลายปีการศึกษา และค้นหา/กรอง/เรียกดูตามเงื่อนไขได้จริง

การ์ดนี้คือหลักฐาน end-to-end ว่า repository public ทำงานครบ:

- ผู้ใช้เปิดหน้า repository
- filter options มาจาก master data จริง
- search/filter ส่งไป API จริง
- result list มาจาก work items ใน Aurora จริง
- detail page เปิดข้อมูลรายการเดียวจาก Aurora จริง
- internal/restricted data ไม่หลุดออก public UI
- V1 faculty public pages ยังไม่พัง

## เป้าหมาย

ทำให้ public V2 repository:

- โหลด master data options จาก API #64
- ส่ง URL query/filter ไป `GET /api/v2/work-items` จาก #66
- แสดง result list/pagination จาก real response
- เปิด detail จาก `GET /api/v2/work-items/{id}` จาก #68
- preserve filter/page state ระหว่าง list/detail/back navigation
- handle loading, error, empty, retry และ not found states ด้วยข้อมูลจริง
- ใช้ API error shape มาตรฐานโดยไม่เปิด stack trace/secret
- ไม่แสดง internal/restricted/admin-only fields
- ไม่กระทบ V1 public faculty pages

## Non-Goals

การ์ดนี้ยังไม่ต้อง:

- admin login integration
- admin CRUD integration
- auth token management
- evidence download
- S3 signed URL
- official reporting/export
- backend API implementation ใหม่
- database migration/seeding ใหม่
- เปลี่ยน contract ของ #64/#66/#68 โดยไม่มีการ์ด backend รองรับ

## User Stories

1. As a public user, I want to open `/outputs`, so that I can browse faculty outputs and workload records.
2. As a public user, I want filter options to load from real master data, so that the filters match backend data.
3. As a public user, I want to search by keyword, so that I can find records such as privacy-related publications.
4. As a public user, I want to filter by category/type/period/faculty, so that I can narrow the repository results.
5. As a public user, I want pagination to preserve my filters, so that I can browse many records without losing context.
6. As a public user, I want to click a result and open `/outputs/{id}`, so that I can read the full public detail.
7. As a public user, I want refresh on detail page to still load data, so that deep links work.
8. As a public user, I want restricted/internal records to be hidden, so that private data is not exposed.
9. As a public user, I want clear empty/error states, so that I understand whether there are no results or the API failed.
10. As a QA reviewer, I want evidence from deployed frontend and AWS endpoints, so that the team can prove the flow is production-connected.
11. As a V1 user, I want existing `/faculties` pages to keep working, so that V2 integration does not regress V1.
12. As a developer, I want API clients and config centralized, so that future frontend cards do not duplicate fetch logic.

## Scope

### ต้องทำ

- เพิ่มหรือปรับ API client/data fetching สำหรับ:
  - Master Data API จาก #64
  - Work Item List API จาก #66
  - Work Item Detail API จาก #68
- ใช้ API Gateway base URL จริงผ่าน env/config:
  - `NEXT_PUBLIC_V2_API_BASE_URL`
  - หรือชื่อ config equivalent ที่ repo ใช้อยู่
- map URL query จาก `/outputs` ไป API query จริง
- map API response กลับเข้า UI components จาก #72-#74
- handle API error shape มาตรฐาน
- preserve filter/page state ระหว่าง:
  - เลือก filter
  - search keyword
  - pagination
  - click item ไป detail
  - กลับจาก detail ไป list
- เพิ่ม loading/empty/error/retry states ที่ใช้กับ real API
- เพิ่ม not found/restricted-safe state สำหรับ detail route
- เพิ่ม integration tests หรือ manual QA steps
- เพิ่ม env/config docs ถ้าต้องตั้ง `NEXT_PUBLIC_V2_API_BASE_URL` หรือ route proxy เพิ่ม
- บันทึก deployed frontend URL และ API Gateway base URL ที่ใช้ทดสอบ
- ตรวจ CloudWatch/API logs เมื่อเกิด error จาก flow หลัก
- smoke test ว่า V1 `/faculties` และ `/api/v1/faculties` ยังไม่พัง

### ไม่ต้องทำ

- admin API integration
- admin auth/token flow
- backend read API implementation ใหม่
- schema migration ใหม่
- seed/import dataset ใหม่
- evidence file download
- private evidence viewer
- official report/export

## API Endpoints ที่ต้องเชื่อม

ใช้ base URL จาก env:

```text
NEXT_PUBLIC_V2_API_BASE_URL=https://n89gqgnqw2.execute-api.ap-southeast-1.amazonaws.com
```

Master data endpoints จาก #64:

```http
GET /api/v2/academic-periods
GET /api/v2/evaluation-periods
GET /api/v2/work-categories
GET /api/v2/work-types
GET /api/v2/faculties
```

Repository list endpoint จาก #66:

```http
GET /api/v2/work-items
```

Detail endpoint จาก #68:

```http
GET /api/v2/work-items/{id}
```

## URL Query → API Query Mapping

หน้า `/outputs` ต้องอ่าน query จาก URL แล้วส่งไป API จริง:

| URL query | API query | Example | หมายเหตุ |
|---|---|---|---|
| `q` | `q` | `privacy` | keyword search |
| `academic_period_id` | `academic_period_id` | `ap-2567-1` | filter ปี/ภาค |
| `evaluation_period_id` | `evaluation_period_id` | `eval-2567-full-year` | filter รอบประเมิน |
| `category` | `category` | `RESEARCH` | `work_category.code` |
| `type` | `type` | `PUBLICATION` | `work_type.code` |
| `faculty_id` | `faculty_id` | `fac_prapaporn-rattanatamrong` | faculty id จริง |
| `page` | `page` | `1` | default = 1 |
| `page_size` | `page_size` | `20` | default = 20 |

ตัวอย่าง:

```text
/outputs?q=privacy&category=RESEARCH&type=PUBLICATION&faculty_id=fac_prapaporn-rattanatamrong&page=1&page_size=20
```

ต้องเรียก:

```text
GET ${NEXT_PUBLIC_V2_API_BASE_URL}/api/v2/work-items?q=privacy&category=RESEARCH&type=PUBLICATION&faculty_id=fac_prapaporn-rattanatamrong&page=1&page_size=20
```

## Data Flow ที่คาดหวัง

### เปิดหน้า `/outputs`

```text
Browser /outputs
→ fetch master data endpoints
→ render filter options
→ fetch GET /api/v2/work-items with current URL query
→ render list + pagination
```

### เลือก filter/search

```text
User changes filter/search
→ update URL query
→ fetch GET /api/v2/work-items with query
→ render success/empty/error state
```

### เปิด detail

```text
User clicks work item
→ navigate /outputs/{id}
→ fetch GET /api/v2/work-items/{id}
→ render detail sections
```

### กลับจาก detail

```text
User clicks back to repository
→ return /outputs with previous query if available
→ list reloads same filter/page state
```

## Expected Demo Result Baseline

ถ้าใช้ demo dataset ตาม #66 public route ควรเห็นเฉพาะ work items ที่ `status = ACTIVE` และ `visibility = PUBLIC`

Expected public work items:

| Work item id | Title | Category | Type | Expected faculty |
|---|---|---|---|---|
| `wi-pub-2019-multi-container` | `Multi-Container Application Migration with Load Balanced and Adaptive Parallel TCP` | `RESEARCH` | `PUBLICATION` | `prapaporn-rattanatamrong` |
| `wi-pub-2024-privacy-edge` | `Privacy-Preserving Edge Analytics for Smart Campus Workload Signals` | `RESEARCH` | `PUBLICATION` | `prapaporn-rattanatamrong`, `kasidit-chanchio` |
| `wi-pub-2025-hci-agent` | `Adaptive Interface Agents for Computing Education` | `RESEARCH` | `PUBLICATION` | `nuttanont-hongwarittorrn` |
| `wi-service-2568-speaker` | `Invited Speaker: Responsible AI and Privacy in Education` | `ACADEMIC_SERVICE` | `INVITED_SPEAKER` | `nuttanont-hongwarittorrn` |

Expected list API checks:

- `/outputs` แสดงรายการ public baseline ได้
- `/outputs?category=RESEARCH` แสดง public research/publication records
- `/outputs?type=PUBLICATION` แสดง publication records
- `/outputs?q=privacy` แสดง `wi-pub-2024-privacy-edge`
- `/outputs?faculty_id=fac_prapaporn-rattanatamrong&type=PUBLICATION` แสดง publication records ของอาจารย์คนนี้
- `/outputs?category=TEACHING` ควรเป็น empty state ถ้า teaching demo data ยังเป็น `INTERNAL`

Expected detail checks:

- `/outputs/wi-pub-2024-privacy-edge` แสดง publication detail และ evidence `ev-pub-2024-demo-url`
- `/outputs/wi-service-2568-speaker` แสดง service detail
- `/outputs/wi-pub-2025-hci-agent` แสดง publication detail ได้ แม้ไม่มี public evidence
- `/outputs/wi-teach-2567-2-cs333` แสดง not found/restricted-safe state เพราะเป็น `INTERNAL`
- `/outputs/wi-supervision-2567-phd-thesis` แสดง not found/restricted-safe state เพราะเป็น `RESTRICTED`
- `/outputs/not-found-id` แสดง not found state

## Error Handling Contract

Frontend ควรรองรับ error shape จาก #64/#66/#68 เช่น:

```json
{
  "error": {
    "code": "INVALID_QUERY",
    "message": "Invalid query parameter"
  }
}
```

กติกา:

- invalid query แสดงข้อความที่ผู้ใช้เข้าใจได้ และอาจให้ clear filters
- network error แสดง retry
- API 404 detail แสดง not found/restricted-safe state
- API 5xx แสดง error state ทั่วไปและไม่โชว์ raw stack trace
- ห้ามโชว์ secret, ARN, SQL, stack trace หรือ raw Lambda error ต่อผู้ใช้
- log/debug detail เก็บไว้ใน developer console ได้เท่าที่ไม่เปิด secret

## Public Safety Rules

การ์ดนี้ต้องตรวจว่า public UI ไม่แสดง:

- internal/restricted work items
- admin-only fields
- source/provenance fields เช่น `source_score`, `source_weight`, `source_record_id`
- audit fields
- auth/user fields
- `s3_key`
- `checksum_sha256`
- signed URL
- raw DB secret, AWS key, ARN ที่ไม่จำเป็นต่อผู้ใช้

## Suggested Frontend Files

ปรับชื่อไฟล์ตาม pattern จริงของ repo ได้ แต่ควรมี responsibility ประมาณนี้:

```text
frontend/lib/v2/api-client.ts
frontend/lib/v2/master-data-client.ts
frontend/lib/v2/work-items-client.ts
frontend/lib/v2/errors.ts
frontend/app/outputs/page.tsx
frontend/app/outputs/[id]/page.tsx
frontend/components/outputs/*
```

ถ้า #72-#74 สร้างไฟล์ไว้แล้ว ให้ reuse/ปรับต่อ ไม่สร้าง client ซ้ำหลายชุด

## Configuration / Environment

ต้อง document env ที่ใช้จริง เช่น:

```text
NEXT_PUBLIC_V2_API_BASE_URL=https://n89gqgnqw2.execute-api.ap-southeast-1.amazonaws.com
```

กติกา:

- frontend เห็นได้เฉพาะ public API base URL
- ห้ามใส่ DB secret, Secret ARN, AWS access key หรือ RDS Data API credentials ใน frontend env
- ถ้าใช้ server-side proxy ให้ document route และ CORS behavior ชัดเจน
- ถ้า env missing ใน dev ให้ error แบบเข้าใจง่าย ไม่ fail เงียบ

## End-to-End Scenarios

ต้อง verify อย่างน้อย:

1. เปิด `/outputs` แล้ว filter options โหลดจาก Master Data API จริง
2. เปิด `/outputs` แล้ว result list โหลดจาก Work Item List API จริง
3. search keyword `privacy` แล้วเห็น `wi-pub-2024-privacy-edge`
4. filter category `RESEARCH` แล้วเห็น public research/publication records
5. filter type `PUBLICATION` แล้วเห็น publication records
6. filter faculty `fac_prapaporn-rattanatamrong` พร้อม type `PUBLICATION` แล้วเห็น records ที่เกี่ยวข้อง
7. filter category `TEACHING` แล้วเห็น empty state ถ้า teaching public route ยังไม่มีรายการ public
8. pagination เปลี่ยนหน้าแล้ว URL query และ filter เดิมยังอยู่
9. กด item แล้วเปิด `/outputs/{id}`
10. refresh detail page แล้วยังโหลดข้อมูลได้จาก API จริง
11. เปิด restricted/internal ids แล้วไม่แสดงข้อมูล public
12. API error หรือ invalid query แสดง error state ที่ไม่ leak technical detail
13. V1 `/faculties` ยังเปิดได้
14. V1 `/api/v1/faculties` ยังตอบได้ถ้า endpoint นั้นมีใน environment

## QA Evidence ที่ต้องแนบตอนปิดการ์ด

ควรมีอย่างน้อย:

- deployed frontend URL ที่ใช้ทดสอบ
- API Gateway base URL ที่ frontend ใช้จริง
- screenshot หรือ video สั้นของ `/outputs`
- screenshot หรือ note ว่า filter options โหลดจาก API จริง
- Network tab หรือ log ว่าเรียก master data endpoints จริง
- Network tab หรือ log ว่าเรียก `GET /api/v2/work-items` จริง
- Network tab หรือ log ว่าเรียก `GET /api/v2/work-items/{id}` จริง
- screenshot ของ search `privacy`
- screenshot ของ filter `RESEARCH` หรือ `PUBLICATION`
- screenshot ของ empty state เช่น `category=TEACHING`
- screenshot ของ detail `wi-pub-2024-privacy-edge`
- screenshot ของ not found/restricted-safe state
- CloudWatch log note ว่าไม่มี error ที่ block demo flow
- smoke note ว่า V1 `/faculties` และ `/api/v1/faculties` ไม่พัง

## Manual QA URLs

ใช้กับ deployed frontend:

```text
/outputs
/outputs?q=privacy
/outputs?category=RESEARCH
/outputs?type=PUBLICATION
/outputs?faculty_id=fac_prapaporn-rattanatamrong&type=PUBLICATION
/outputs?category=TEACHING
/outputs/wi-pub-2024-privacy-edge
/outputs/wi-service-2568-speaker
/outputs/wi-pub-2025-hci-agent
/outputs/wi-teach-2567-2-cs333
/outputs/wi-supervision-2567-phd-thesis
/outputs/not-found-id
/faculties
```

ใช้กับ API Gateway โดยตรง:

```text
GET /api/v2/academic-periods
GET /api/v2/evaluation-periods
GET /api/v2/work-categories
GET /api/v2/work-types
GET /api/v2/faculties
GET /api/v2/work-items
GET /api/v2/work-items?q=privacy
GET /api/v2/work-items?category=RESEARCH
GET /api/v2/work-items?type=PUBLICATION
GET /api/v2/work-items?category=TEACHING
GET /api/v2/work-items/wi-pub-2024-privacy-edge
GET /api/v2/work-items/wi-teach-2567-2-cs333
GET /api/v2/work-items/not-found-id
```

## Acceptance Criteria

- [ ] `/outputs` ใช้ real Master Data API สำหรับ filter options
- [ ] `/outputs` ใช้ real Work Item List API
- [ ] `/outputs/{id}` ใช้ real Detail API
- [ ] frontend ใช้ API Gateway base URL จริงผ่าน env/config
- [ ] loading/error/empty states ทำงานกับ real API response/error
- [ ] URL query แปลงเป็น API query ถูกต้อง
- [ ] filter/page state ถูก preserve ระหว่าง interaction หลัก
- [ ] pagination ส่ง query ไป API จริงและ update URL ถูกต้อง
- [ ] detail page refresh แล้วโหลดข้อมูลได้
- [ ] restricted/internal records ไม่แสดงใน public UI
- [ ] not found/restricted-safe detail state ทำงาน
- [ ] ไม่มี admin-only/source/audit/storage fields ใน public UI
- [ ] no V1 regression บน `/faculties`
- [ ] no V1 regression บน `/api/v1/faculties` ถ้ามี endpoint ใน environment
- [ ] มี QA evidence สำหรับ demo dataset
- [ ] มี deployed frontend URL และ API Gateway base URL ใน evidence
- [ ] smoke test public flow ผ่าน deployed frontend ไม่ใช่ local/mock เท่านั้น
- [ ] CloudWatch/API evidence ไม่มี error ที่ block demo flow

## Review Checklist

Frontend:

- [ ] API client แยกจาก component พอสมควร
- [ ] ไม่ duplicate fetch logic หลายที่โดยไม่จำเป็น
- [ ] cache/revalidate behavior เหมาะกับ Next.js pattern ใน repo
- [ ] error handling ไม่เปิด raw stack trace
- [ ] query serialization stable
- [ ] response mapping รองรับ optional/null fields
- [ ] loading state ไม่ทำให้ layout shift แรง
- [ ] mobile/desktop ใช้งานได้

Backend/API Contract:

- [ ] API response shape ตรงกับ frontend expectation
- [ ] CORS/proxy/env path ทำงานกับ deployed frontend และ API Gateway
- [ ] invalid query/error shape consistent กับ #64/#66/#68
- [ ] public route enforce `ACTIVE` + `PUBLIC`
- [ ] detail route return `404` สำหรับ missing/internal/restricted

Security/Public Safety:

- [ ] frontend ไม่เห็น DB secret หรือ AWS secret
- [ ] ไม่ hardcode credentials
- [ ] ไม่แสดง `s3_key`, `checksum_sha256`, signed URL
- [ ] restricted/internal data ไม่ leak ผ่าน list, detail, error message หรือ URL state

QA:

- [ ] ทดสอบ search/filter matrix จาก `docs/v2/demo-dataset.md`
- [ ] ทดสอบ public baseline 4 รายการจาก #66
- [ ] ทดสอบ restricted/internal visibility
- [ ] ทดสอบ detail public, no evidence, not found
- [ ] ทดสอบ V1 public routes
- [ ] แนบ screenshot/log/network evidence ใน GitHub issue

## Dependencies

Blocked by:

- #64 Build Master Data API
- #66 Build Work Item List/Search/Filter API
- #68 Build Work Item Detail API
- #72 Build Repository Page Shell & Filter UI
- #73 Build Repository Result List & Pagination UI
- #74 Build Work Item Detail UI

Blocks:

- #81 Final Integration / Deploy / Demo Docs

Related:

- #67 Build Faculty Work Items API
- #80 Execute Migration & Preserve V1 Compatibility

## Suggested Labels

- `v2`
- `frontend`
- `integration`
- `api`
- `repository`
- `ready-for-agent`

## Suggested Owner

Frontend Developer

Reviewers:

- Tech Lead
- Backend Developer
- QA / Integration

## Estimate

1 day

## Definition Of Done

การ์ดนี้ถือว่าเสร็จเมื่อ public V2 repository ที่ deploy แล้วใช้ AWS API Gateway/Lambda/Aurora ได้ครบตั้งแต่ master data filter options, search/filter/list/pagination ไปจนถึง detail page โดยมี QA evidence จาก deployed frontend และ AWS endpoint จริง ยืนยันว่า restricted/internal data ไม่รั่ว และ V1 public faculty pages ยังไม่พัง
