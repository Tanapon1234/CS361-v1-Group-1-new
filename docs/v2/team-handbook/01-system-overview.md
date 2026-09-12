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

Aurora Serverless/Express สามารถ auto-pause เมื่อไม่มีการใช้งานได้ request แรกหลังจากระบบนิ่งไปนานอาจล้มเหลวชั่วคราวด้วย:

```text
DatabaseResumingException
```

ถ้าเกิดกรณีนี้:

1. รอ 15-30 วินาที
2. รัน smoke test ซ้ำ
3. ถ้ายังล้มเหลว ให้ดู CloudWatch logs ของ `cs361-v2-dev-query`

พฤติกรรมนี้คาดหวังได้ใน environment dev/demo ที่ตั้งใจประหยัดค่าใช้จ่าย และควรบันทึกไว้ใน issue evidence ถ้าเจอระหว่างทดสอบ

## สิ่งที่ V2 ยังไม่รวมในรอบนี้

V2 รอบนี้ยังไม่รวม:

- faculty self-service workspace
- reviewer/approver workflow
- official workload scoring
- official annual report generation
- multi-role workspace beyond Admin pilot
- full production-grade monitoring/alarming
- OpenSearch/full text search service
- evidence file upload/download with signed URLs

สิ่งเหล่านี้ถูกเลื่อนไปเวอร์ชันถัดไป เช่น V3/V4/V7 เว้นแต่ทีมจะมี decision ใหม่ที่เปลี่ยน scope อย่างชัดเจน

## ผลลัพธ์เมื่อทำ V2 ครบทุกการ์ด

ถ้าทำครบทุกการ์ด V2 ตั้งแต่ #46 ถึง #81 ผลลัพธ์สุดท้ายจะไม่ใช่แค่ “มี database และ design” แต่จะกลายเป็น Faculty Output Repository ที่ใช้งานจริงบน AWS ในระดับ demo/production-connected

### 1. มีฐานข้อมูลกลางของผลงานและภาระงานอาจารย์

Aurora PostgreSQL จะเป็น repository กลางสำหรับข้อมูล V2 โดยมี schema ชัดเจนและ query ได้จริง

สิ่งที่ระบบจะเก็บได้:

- ข้อมูลอาจารย์และ profile พื้นฐาน
- ประวัติการศึกษาและความเชี่ยวชาญ
- งานสอน
- publication / research project / grant
- supervision / thesis / senior project
- academic service
- administration workload
- evidence/reference metadata
- import provenance
- audit events สำหรับการแก้ไขข้อมูลฝั่ง admin

ผลลัพธ์คือทีมไม่ต้องอิงไฟล์กระจัดกระจายอย่างเดียว แต่มีฐานข้อมูลกลางที่รองรับหลายปีการศึกษาและตรวจสอบย้อนกลับได้

### 2. มี Public APIs ที่อ่านข้อมูลจริงจาก Aurora

ฝั่ง public API จะทำงานผ่านเส้นทางจริง:

```text
API Gateway -> Lambda -> RDS Data API -> Aurora PostgreSQL
```

เมื่อครบ #64, #66, #67 และ #68 ระบบจะมี API สำหรับ:

- โหลด master data สำหรับ filter เช่น ปีการศึกษา รอบประเมิน หมวดงาน ประเภทงาน และอาจารย์
- ค้นหา/กรองรายการผลงานและภาระงาน
- ดูผลงานของอาจารย์แต่ละคน
- ดูรายละเอียดผลงานแต่ละรายการ
- ซ่อนข้อมูลที่เป็น internal/restricted ไม่ให้ public path เห็น

ผลลัพธ์คือ frontend หรือระบบอื่นสามารถเรียกข้อมูลจาก backend จริงได้ ไม่ใช่ mock/local fixture

### 3. มีหน้า Public Repository ให้ผู้ใช้ทั่วไปใช้งานได้

เมื่อครบ #72 ถึง #75 ผู้ใช้ทั่วไปจะมีหน้าเว็บสำหรับค้นหาและดูผลงานอาจารย์

สิ่งที่ผู้ใช้จะทำได้:

- เปิดหน้า repository
- เลือก filter จาก master data จริง
- ค้นหาด้วย keyword
- กรองตามปีการศึกษา อาจารย์ หมวดงาน และประเภทงาน
- ดูรายการผลลัพธ์พร้อม pagination
- กดเข้าไปดูรายละเอียดผลงาน
- เห็นเฉพาะข้อมูลที่เปิดเผยได้

ผลลัพธ์คือ V2 จะตอบโจทย์ “ค้นหา กรอง หรือเรียกดูตามเงื่อนไข” ได้จากหน้าเว็บจริง

### 4. มีระบบ Admin สำหรับจัดการข้อมูลจริง

เมื่อครบ #69 ถึง #71 และ #76 ถึง #79 ระบบจะมี admin pilot ที่เชื่อมกับ AWS จริง

สิ่งที่ admin จะทำได้:

- login ผ่าน Cognito
- เข้าหน้า admin เฉพาะผู้มีสิทธิ์
- เพิ่ม work item ใหม่
- แก้ไข work item เดิม
- soft delete หรือ restore รายการ
- ผูกผลงานกับอาจารย์ หมวดงาน ประเภทงาน ปีการศึกษา และ evidence metadata
- บันทึก audit event ทุกครั้งที่มี action สำคัญ

ผลลัพธ์คือ V2 ไม่ได้เป็นระบบอ่านอย่างเดียวอีกต่อไป แต่เริ่มมี workflow สำหรับจัดการข้อมูลในฐานข้อมูลกลางอย่างปลอดภัย

### 5. มี migration/import process ที่ทำซ้ำและตรวจสอบได้

เมื่อครบ #80 ทีมจะมีวิธีจัดการข้อมูลจาก V1/demo dataset เข้า V2 อย่างเป็นระบบ

สิ่งที่ต้องได้:

- mapping จากข้อมูลเดิมเข้าสู่ schema ใหม่
- seed/import ที่รันซ้ำได้ หรือมี reset path ชัดเจน
- table counts ที่ตรวจสอบได้
- API smoke test ที่ยืนยันว่า V2 อ่านข้อมูล imported data ได้
- evidence ว่า V1 compatibility ยังไม่พัง

ผลลัพธ์คือคนในทีมสามารถเตรียมข้อมูลหรือย้ายข้อมูลต่อได้โดยไม่ต้องเดาเอง

### 6. มีหลักฐานและเอกสารพร้อมส่งงาน

เมื่อครบ #81 ระบบจะมี final integration evidence และ demo docs ครบ

สิ่งที่ควรมีตอนจบ:

- architecture docs
- database docs
- API contracts
- AWS setup/check guide
- issue card evidence
- smoke test output
- demo script
- known limitations
- commit/branch references

ผลลัพธ์คืออาจารย์หรือคนในทีมสามารถตรวจซ้ำได้ว่าอะไร deploy แล้ว อะไร test แล้ว และระบบตอบโจทย์ V2 อย่างไร

### สรุปปลายทางของ V2

เมื่อทำครบทุกการ์ด V2 จะได้ระบบที่:

- มีฐานข้อมูลกลางบน Aurora
- มี API จริงบน AWS
- มีหน้า public repository สำหรับค้นหา/ดูข้อมูล
- มี admin pilot สำหรับจัดการข้อมูล
- มี migration/import process
- มีเอกสารและหลักฐานครบสำหรับ demo/ส่งงาน

แต่ V2 ยังไม่ใช่ระบบรายงานเชิงบริหารเต็มรูปแบบแบบ V4/V7 เช่น workload sheet อัตโนมัติขั้นสุดท้าย dashboard วิเคราะห์ระดับสาขา หรือ annual report generator เต็มระบบ สิ่งเหล่านั้นเป็นขั้นต่อไปหลังจาก repository foundation ของ V2 เสถียรแล้ว

## แต่ละการ์ด V2 ตอบโจทย์จริงอย่างไร

โจทย์จริงไม่ใช่แค่ “ทำหน้าเว็บ” แต่คือการสร้าง repository กลางที่จัดเก็บและเรียกใช้ข้อมูลผลงาน/ภาระงานอาจารย์ได้อย่างเป็นระบบ

แต่ละการ์ดช่วยตอบโจทย์แบบนี้:

- #46 ล็อก scope เพื่อไม่ให้ทีมเผลอสร้าง V3/V4 เร็วเกินไป
- #47 สร้าง relational schema สำหรับจัดเก็บข้อมูลอย่างเป็นระบบ
- #48 เตรียม AWS infrastructure ที่ใช้กับ backend จริง
- #49 กำหนดว่า data เดิมจาก V1 map เข้าสู่ V2 model อย่างไร
- #50 สร้างข้อมูลหลายปีที่สมจริงสำหรับ demo search/filter/detail
- #64 เตรียม master/reference data สำหรับ filters และ validation
- #66-#68 สร้าง public repository read APIs
- #72-#75 แปลง public APIs ให้เป็นหน้าจอ repository ที่ผู้ใช้ใช้งานได้
- #69-#71 สร้างฐาน admin/auth/write operation
- #76-#79 แปลง admin backend ให้เป็น admin pilot screens
- #80 ทำให้ migration/seed/import รันซ้ำได้ และรักษา V1 compatibility
- #81 ตรวจว่าทุกส่วนทำงานร่วมกัน และเตรียม final demo evidence
