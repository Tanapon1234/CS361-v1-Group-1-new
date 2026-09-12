# ภาพรวมระบบ: จาก V1 ไป V2

ไฟล์นี้อธิบายภาพรวมโจทย์ที่ทีมกำลังทำ ตั้งแต่ V1 ที่มีอยู่แล้ว ไปจนถึง V2 ที่กำลังพัฒนาเป็น Faculty Output Repository จริงบน AWS

เอกสารนี้เขียนเป็นภาษาไทยเป็นหลัก ส่วนคำอังกฤษที่ยังคงไว้คือชื่อ version, service, route, table หรือคำใน code ที่ต้องใช้ตรงกับของจริง

## วิสัยทัศน์ของโปรเจกต์

ระบบ Faculty Output & Workload Management System คือระบบกลางสำหรับจัดเก็บและเรียกใช้ข้อมูลอาจารย์ การสอน งานวิจัย งานบริการวิชาการ การดูแลนักศึกษา และผลงาน/ภาระงานที่เกี่ยวข้อง

เป้าหมายระยะยาวคือให้สาขาวิชามีข้อมูลกลางที่:

- ตรวจสอบย้อนกลับได้ว่าข้อมูลมาจากไหน
- รองรับหลายปีการศึกษา
- ค้นหา/กรอง/เรียกดูรายละเอียดได้
- แยกข้อมูล public/internal/restricted ได้
- ต่อไปสามารถใช้ทำ workload sheet หรือรายงานประจำปีได้

## V1 คืออะไร

V1 คือ Public Read-only Faculty Information Service

ลักษณะหลัก:

- ผู้ใช้ทั่วไปเปิดดูได้โดยไม่ต้อง login
- แสดงรายชื่ออาจารย์และ profile รายบุคคล
- ใช้ข้อมูลที่เตรียมจาก source แล้ว publish เป็น serving JSON
- เน้น public information เท่านั้น
- ไม่มี database กลางแบบ relational
- ไม่มี admin CRUD
- ไม่มี Cognito/admin login
- ไม่มี workflow รับรองข้อมูล

V1 ตอบโจทย์แรกของระบบ: ให้คนทั่วไปหาข้อมูลอาจารย์และผลงานที่เปิดเผยได้จากที่เดียว

V1 routes สำคัญ:

```text
/faculties
/faculties/{slug}
/api/v1/faculties
/api/v1/faculties/{slug}
```

V1 data/output สำคัญ:

```text
build/v1/serving/faculties.json
build/v1/serving/faculties/{public_slug}.json
data/v1/source/faculty_profiles.json
```

## V2 คืออะไร

V2 คือ Managed Multi-year Faculty Output Repository

V2 ยกระบบจาก “หน้า profile public” ไปเป็น “repository กลาง” ที่มี schema ชัดเจนและรองรับข้อมูลหลายประเภท เช่น:

- ข้อมูลอาจารย์
- ประวัติการศึกษา/ความเชี่ยวชาญ
- การสอน
- publication / research project / grant
- supervision / thesis / senior project
- academic service
- administration
- evidence/reference metadata
- import provenance
- audit/auth foundation สำหรับ admin pilot

V2 ต้องรองรับหลายปีการศึกษาและค้นหา/กรองตามเงื่อนไข เช่น:

- academic year / semester
- evaluation period
- faculty
- category
- work type
- keyword
- visibility

## ขอบเขต V2 ที่ต้องส่ง

V2 ต้องส่งระบบ foundation ที่ใช้งานจริงได้ในระดับ demo/production-connected:

1. Relational schema บน Aurora PostgreSQL
2. Data API/IAM/Secrets/S3/CloudWatch foundation
3. Master data API จริงบน AWS
4. Work item read APIs จริงบน AWS
5. Public repository UI ที่เรียก API จริง
6. Cognito admin authentication foundation
7. Admin CRUD APIs ที่เขียน Aurora จริง
8. Admin UI ที่ login และจัดการ work item ได้
9. Repeatable migration/seed/import/verification process
10. Final integration evidence และ demo docs

## สถาปัตยกรรม V2

Production path ของ V2 แยกเป็น 3 ส่วนหลัก

### เส้นทางการอ่านข้อมูลสาธารณะ

```text
User
-> Frontend
-> API Gateway
-> Query Lambda
-> RDS Data API
-> Aurora PostgreSQL
```

ใช้กับ:

- Master Data API #64
- Work Item List/Search API #66
- Faculty Work Items API #67
- Work Item Detail API #68
- Public repository UI #72-#75

### เส้นทางของผู้ดูแลระบบ

```text
Admin User
-> Frontend Admin UI
-> Cognito
-> protected API Gateway admin route
-> Admin Lambda
-> RDS Data API transaction
-> Aurora PostgreSQL
```

ใช้กับ:

- Admin authentication #69
- Admin create/update/delete APIs #70-#71
- Admin UI #76-#79

### เส้นทางข้อมูล หลักฐาน และการนำเข้า

```text
Project/team data
-> S3 landing/archive/metadata
-> Import or migration command
-> RDS Data API
-> Aurora PostgreSQL
-> CloudWatch evidence/logs
```

ใช้กับ:

- Migration and V1 compatibility #80
- Final integration #81
- future import/projection cards

## AWS resources ปัจจุบัน

Region:

```text
ap-southeast-1
```

Foundation stack:

```text
cs361-v2-aws-foundation-dev
```

Master Data API stack:

```text
cs361-v2-master-data-api-dev
```

Master Data API endpoint:

```text
https://n89gqgnqw2.execute-api.ap-southeast-1.amazonaws.com
```

Current Lambda for #64:

```text
cs361-v2-dev-query
```

CloudWatch log group:

```text
/aws/lambda/cs361-v2-dev-query
```

foundation resources ปัจจุบันมี:

- Aurora PostgreSQL cluster: `cs361-v2-dev-aurora`
- Database name: `cs361v2`
- Secrets Manager secret name: `cs361-v2/dev/aurora/master`
- S3 data bucket: `cs361-v2-aws-foundation-dev-v2databucket-itl5uq2sozge`
- Query Lambda role: `CS361V2QueryLambdaRole-dev`
- Admin Lambda role: `CS361V2AdminLambdaRole-dev`
- Import Lambda role: `CS361V2ImportLambdaRole-dev`
- Projection Lambda role: `CS361V2ProjectionLambdaRole-dev`

ห้ามคัดลอก secret value จริงลง docs, chat, commit, screenshot หรือ GitHub comment

## สิ่งที่ทำงานได้แล้วตอนนี้

### สิ่งที่เสร็จใน repo และเอกสารออกแบบ

- freeze scope และ architecture ของ V2 แล้ว
- ออกแบบ relational schema แล้ว
- สร้าง ERD/DBML docs แล้ว
- สร้าง V1 to V2 mapping แล้ว
- สร้าง demo dataset แล้ว
- deploy AWS foundation แล้ว
- implement, deploy และ smoke test Master Data API #64 แล้ว

### สิ่งที่ deploy แล้วบน AWS

Master Data API ใช้งานได้หลังจาก Aurora พร้อมตอบสนอง:

```text
GET /api/v2/academic-periods
GET /api/v2/evaluation-periods
GET /api/v2/work-categories
GET /api/v2/work-types
GET /api/v2/faculties
```

ผล smoke test ล่าสุดหลัง Aurora resume:

```text
PASS /api/v2/academic-periods count=5
PASS /api/v2/evaluation-periods count=3
PASS /api/v2/work-categories count=6
PASS /api/v2/work-types count=26
PASS /api/v2/faculties count=3
PASS /api/v2/work-types?category=UNKNOWN returned 400 INVALID_QUERY
```

### พฤติกรรม AWS ที่ทีมต้องรู้

Aurora Serverless/Express can auto-pause when idle. First request after a long idle period may fail temporarily with:

```text
DatabaseResumingException
```

If this happens:

1. Wait 15-30 seconds
2. Run the smoke test again
3. If it still fails, check CloudWatch logs for `cs361-v2-dev-query`

This is expected for dev/demo cost saving and should be documented in issue evidence if it appears.

## สิ่งที่ V2 ยังไม่รวมในรอบนี้

V2 does not yet include:

- faculty self-service workspace
- reviewer/approver workflow
- official workload scoring
- official annual report generation
- multi-role workspace beyond Admin pilot
- full production-grade monitoring/alarming
- OpenSearch/full text search service
- evidence file upload/download with signed URLs

These are deferred to future versions such as V3/V4/V7 unless a new decision explicitly changes scope.

## แต่ละการ์ด V2 ตอบโจทย์จริงอย่างไร

The real problem is not just “make pages”. The real problem is making a central repository that stores and retrieves faculty output/workload data systematically.

Each card contributes like this:

- #46 locks scope so the team does not accidentally build V3/V4 early
- #47 creates the relational schema that stores data systematically
- #48 provisions managed AWS infrastructure for real backend usage
- #49 defines how old V1 data maps into the new V2 model
- #50 creates realistic multi-year data for search/filter/detail demo
- #64 provides master/reference data for filters and validation
- #66-#68 provide public repository read APIs
- #72-#75 turn public APIs into usable repository screens
- #69-#71 provide admin/auth/write foundation
- #76-#79 turn admin backend into usable admin pilot screens
- #80 makes migration/seed/import repeatable and protects V1 compatibility
- #81 verifies everything works together and prepares final demo evidence
