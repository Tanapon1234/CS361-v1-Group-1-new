# โครงสร้างโฟลเดอร์ GitHub และวิธีเริ่มงาน

ไฟล์นี้อธิบายว่า repository นี้มีโฟลเดอร์อะไรบ้าง แต่ละส่วนใช้ทำอะไร และถ้าเพื่อนในทีมได้รับ issue card แล้วควรเริ่มอ่านจากตรงไหนก่อน

เนื้อหาหลักเขียนเป็นภาษาไทยเพื่อให้คนในทีมอ่านแล้วทำต่อได้ทันที ส่วนชื่อไฟล์ โฟลเดอร์ command route และ AWS service ยังคงเป็นภาษาอังกฤษตามของจริง

## อ่านอะไรก่อนเมื่อเพิ่งเข้ามาในโปรเจกต์

ลำดับที่แนะนำ:

1. อ่าน `README.md` ที่ root repo เพื่อเข้าใจภาพรวม V1/V2 และสถานะปัจจุบัน
2. อ่าน `docs/v2/team-handbook/README.md` เพื่อเข้าหน้าสารบัญคู่มือกลางทีม
3. อ่าน `docs/v2/team-handbook/01-system-overview.md` เพื่อเข้าใจโจทย์ V2 และ architecture
4. อ่าน `docs/v2/team-handbook/02-database-guide.md` ถ้างานเกี่ยวกับ schema, query, API หรือ migration
5. อ่าน `docs/v2/team-handbook/03-aws-access-and-setup.md` ถ้างานต้องใช้ AWS จริง
6. อ่าน `docs/v2/team-handbook/04-development-workflow-and-issue-cards.md` เพื่อดู flow การทำงานและ dependency ของการ์ด
7. อ่าน issue card ของตัวเองใน `docs/v2/issues/`
8. อ่าน `docs/v2/team-handbook/05-testing-verification-and-evidence.md` ก่อนปิดการ์ด

หลักคิดคือ อย่าเริ่มเขียนโค้ดจากการเดา ให้เริ่มจาก issue card แล้วค่อยตาม link ไปยัง database/API/AWS docs ที่เกี่ยวข้อง

## ภาพรวมโฟลเดอร์หลัก

```text
CS361-v1-Group-1/
├── README.md
├── backend/
├── build/
├── data/
├── database/
├── docs/
├── evidence/
├── fixtures/
├── frontend/
├── infra/
└── scripts/
```

## `README.md`

เป็นประตูหน้า repo สำหรับคนที่เข้ามาครั้งแรก

ใช้เพื่อ:

- เข้าใจว่า project นี้คือ Faculty Output & Workload Management System
- แยกให้ออกว่า V1 ทำอะไร และ V2 กำลังทำอะไรเพิ่ม
- ดูลิงก์เอกสารหลักของทีม
- ดูสถานะระบบที่ deploy แล้วบน AWS
- ดูวิธีเริ่มทำงานแบบสั้น

ไม่ควรใส่:

- secret value
- database password
- AWS access key
- รายละเอียดลึกทุกอย่างที่ควรอยู่ใน handbook เฉพาะเรื่อง

## `backend/`

เป็นโค้ด backend สำหรับ V2 ที่ต้อง deploy เป็น Lambda จริง

ตอนนี้โฟลเดอร์สำคัญคือ:

```text
backend/v2/query/
```

ใช้เพื่อ:

- เขียน Lambda handler สำหรับ public/read API
- เชื่อม API Gateway -> Lambda -> RDS Data API -> Aurora
- แยก validation, response shape และ data access ให้ test ได้
- ใช้เป็น pattern สำหรับการ์ดถัดไป เช่น #66, #67, #68

ตัวอย่างที่มีแล้ว:

- #64 Master Data API
- อ่าน master data จาก Aurora จริง
- มี unit tests
- deploy แล้วผ่าน API Gateway

งานที่มักแตะโฟลเดอร์นี้:

- #66 Build Work Item List/Search/Filter API
- #67 Build Faculty Work Items API
- #68 Build Work Item Detail API
- #70/#71 ถ้าแยก admin handler ไว้ใน `backend/v2/admin/`

ข้อควรระวัง:

- ห้าม hardcode secret value
- ห้าม query โดยต่อ public DB port เองถ้า issue ไม่ได้ออกแบบไว้
- ให้ใช้ RDS Data API pattern ตาม #64
- response error ควรใช้รูปแบบมาตรฐานใน `05-testing-verification-and-evidence.md`

## `frontend/`

เป็น Next.js frontend ของระบบ

ใช้เพื่อ:

- แสดง V1 public faculty information
- พัฒนา V2 public repository UI
- พัฒนา V2 admin UI ในอนาคต
- เชื่อม frontend กับ deployed AWS API

งานที่มักแตะโฟลเดอร์นี้:

- #72 Repository Page Shell & Filter UI
- #73 Repository Result List & Pagination UI
- #74 Work Item Detail UI
- #75 Integrate Repository UI with Real API
- #76 Admin Login UI
- #77 Admin Work Item List UI
- #78 Admin Create/Edit Form UI
- #79 Integrate Admin UI with Auth & CRUD API

สิ่งที่ต้องแยกให้ชัด:

- local route หรือ mock ใน frontend ใช้ช่วยพัฒนาได้ แต่ปิด production API card ไม่ได้
- การ์ด V2 ที่เป็น production ต้องเชื่อม AWS API จริงถ้าการ์ดระบุว่า integration
- ถ้าใช้ environment variable เช่น API base URL ต้อง document ให้ทีมรู้

## `infra/`

เป็น Infrastructure as Code ของระบบ

ตอนนี้โฟลเดอร์สำคัญคือ:

```text
infra/v2/
```

ใช้เพื่อ:

- สร้าง Aurora Serverless v2
- เปิด RDS Data API
- สร้าง Secrets Manager secret
- สร้าง IAM roles/policies
- สร้าง API Gateway
- สร้าง Lambda resources
- ตั้งค่า CloudWatch log groups

ไฟล์สำคัญที่มี:

- `infra/v2/aws-foundation.yaml`
- `infra/v2/master-data-api.yaml`

งานที่มักแตะโฟลเดอร์นี้:

- #48 Provision Aurora / Data API / Secret / IAM
- #64 Build Master Data API
- #66-#68 เมื่อเพิ่ม public API routes
- #69-#71 เมื่อเพิ่ม Cognito/admin/protected API
- #81 Final Integration / Deploy / Demo Docs

ข้อควรระวัง:

- ถ้าแก้ CloudFormation ต้อง deploy และดู stack event เมื่อ fail
- ห้ามลบ resource จริงโดยไม่ตกลงกับทีม
- ถ้าเพิ่ม Lambda ที่ต้องใช้ role ให้เช็ค `iam:PassRole`
- output ของ stack ควรช่วยให้คนอื่นทำต่อได้ เช่น API endpoint, Lambda name, log group

## `database/`

เป็น source of truth ของ schema และ seed พื้นฐาน

โครงสร้าง:

```text
database/
├── migrations/
└── seeds/
```

ใช้เพื่อ:

- เก็บ SQL migration สำหรับสร้างตาราง
- เก็บ seed/master data พื้นฐาน
- อธิบายว่าฐานข้อมูล V2 ควรหน้าตาเป็นอย่างไร
- ใช้เป็น reference ของ ERD และ API

ไฟล์สำคัญ:

- `database/migrations/001_base.sql`
- `database/seeds/001_master_data.sql`

งานที่มักแตะโฟลเดอร์นี้:

- #47 Design Relational Schema & SQL Migration
- #50 Prepare Multi-Year Demo Dataset
- #66-#68 ถ้าต้องปรับ index/query support
- #70-#71 ถ้าต้องรองรับ audit/admin mutation เพิ่ม
- #80 Execute Migration & Preserve V1 Compatibility

ข้อควรระวัง:

- การแก้ schema ต้องคิดถึงข้อมูลเดิมใน Aurora
- ห้ามแก้ migration แบบทำลายข้อมูลโดยไม่เขียน migration ใหม่หรือบอก reset path
- ถ้าเพิ่ม column/table ต้องอัปเดต database guide และ ERD/DBML ถ้าเกี่ยวข้อง

## `data/`

เป็นข้อมูลตัวอย่าง mapping และ fixture ที่ใช้พัฒนา V2

โครงสร้างที่เกี่ยวข้อง:

```text
data/v1/
data/v2/
```

ใน `data/v2/` มีข้อมูลสำคัญ เช่น:

- fixture dataset หลายปีการศึกษา
- mapping จาก V1 ไป V2
- summary/count ที่ใช้ตรวจสอบ seed/import

ใช้เพื่อ:

- เตรียม demo dataset
- ทดสอบ API search/filter
- ตรวจว่า V2 รองรับหลายปีการศึกษาและหลายประเภทผลงานจริง
- ใช้อ้างอิงตอนทำ migration/import

งานที่มักแตะโฟลเดอร์นี้:

- #49 Define V1 to V2 Data Mapping
- #50 Prepare Multi-Year Demo Dataset
- #80 Execute Migration & Preserve V1 Compatibility

ข้อควรระวัง:

- ข้อมูลตัวอย่างควรไม่มีข้อมูลส่วนตัวที่ไม่ควรเปิดเผย
- ถ้าแก้ fixture ต้องอัปเดต expected count
- แยกให้ชัดระหว่างข้อมูลตัวอย่างกับข้อมูลจริงใน Aurora

## `docs/`

เป็นเอกสารออกแบบและคู่มือทีม

โครงสร้างที่เกี่ยวข้อง:

```text
docs/v1/
docs/v2/
docs/v2/issues/
docs/v2/team-handbook/
```

ใช้เพื่อ:

- อธิบายโจทย์และขอบเขต
- เก็บ architecture/design decisions
- เก็บ issue card รายละเอียดงาน
- เก็บคู่มือกลางให้ทีมพัฒนาต่อได้
- บันทึก API contract และ database guide

ไฟล์ที่ควรอ่านบ่อย:

- `docs/v2/team-handbook/README.md`
- `docs/v2/team-handbook/01-system-overview.md`
- `docs/v2/team-handbook/02-database-guide.md`
- `docs/v2/team-handbook/03-aws-access-and-setup.md`
- `docs/v2/team-handbook/04-development-workflow-and-issue-cards.md`
- `docs/v2/team-handbook/05-testing-verification-and-evidence.md`
- `docs/v2/issues/*.md`

ข้อควรระวัง:

- เอกสารใน `docs/v2/issues/` เป็นรายละเอียดการ์ด ไม่ใช่ code implementation
- ถ้าการ์ดทำเสร็จ ต้อง tick checklist เฉพาะข้อที่ทำจริง
- ถ้า behavior เปลี่ยน ต้องอัปเดต docs ที่เกี่ยวข้อง ไม่ใช่อัปเดตแต่โค้ด

## `evidence/`

เป็นที่เก็บหลักฐานการทำงานและการทดสอบ

ใช้เพื่อ:

- เก็บ smoke test output
- เก็บผล deploy
- เก็บลิงก์/ชื่อ resource ที่เกี่ยวข้อง
- เก็บ checklist การปิดการ์ด
- ช่วยให้ GitHub issue comment มีหลักฐานจริง

สำหรับ V2 แนะนำใช้:

```text
evidence/v2/<issue-or-feature>/README.md
```

ตัวอย่าง:

```text
evidence/v2/aws-foundation/README.md
evidence/v2/master-data-api/README.md
```

ข้อควรระวัง:

- ห้ามใส่ secret value
- screenshot ต้องไม่เห็น access key/password
- ถ้ามี ARN จริง ให้ใช้เฉพาะที่จำเป็น หรือ redacted account id

## `scripts/`

เป็น script ช่วย deploy, smoke test, import และตรวจระบบ

ใช้เพื่อ:

- ทำขั้นตอนซ้ำๆ ให้เป็นมาตรฐาน
- ลดความผิดพลาดจากการพิมพ์ command เอง
- ให้คนอื่นรันซ้ำได้
- ใช้เป็นหลักฐานว่า deploy/test reproducible

ตัวอย่างที่เกี่ยวข้องกับ V2:

- deploy Master Data API
- smoke test Master Data API
- ในอนาคตอาจมี migration/import scripts สำหรับ #80

งานที่มักแตะโฟลเดอร์นี้:

- #64 Build Master Data API
- #66-#68 เมื่อเพิ่ม smoke test API ใหม่
- #70-#71 เมื่อเพิ่ม admin smoke test
- #80 Execute Migration & Preserve V1 Compatibility
- #81 Final Integration / Deploy / Demo Docs

ข้อควรระวัง:

- script ที่ deploy จริงต้องรับค่าจาก env/stack output ไม่ hardcode secret
- ถ้า script ลบหรือ reset ข้อมูล ต้องมีคำเตือนชัดเจน
- ถ้า script ใช้ AWS ต้องบอก region/stack ที่ใช้

## `build/`

เป็นพื้นที่สำหรับไฟล์ที่ถูก build หรือ package แล้ว

ใช้เพื่อ:

- เก็บ artifact ชั่วคราวจาก build/package
- บางไฟล์อาจถูกสร้างโดย script ก่อน upload ไป S3 หรือ deploy

ข้อควรระวัง:

- โดยทั่วไปไม่ควรแก้ไฟล์ใน `build/` ด้วยมือ
- อย่าใช้ `build/` เป็น source of truth
- ถ้ามีไฟล์ build ใหม่ ควรเช็คก่อนว่า project ต้อง commit หรือ ignore

## `fixtures/`

เป็น fixture เก่าหรือ fixture สำหรับ V1/test บางส่วน

ใช้เพื่อ:

- รองรับ test/ตัวอย่างข้อมูลเดิม
- ใช้อ้างอิง V1 ถ้างานต้องรักษา compatibility

ข้อควรระวัง:

- อย่าสับสนกับ `data/v2/fixtures/`
- ถ้างานเป็น V2 demo dataset ให้ดู `data/v2/` เป็นหลัก

## `function_faculties/`

เป็นส่วนของ V1 Lambda เดิมในบาง branch/history ของโปรเจกต์

ใช้เพื่อ:

- อ้างอิงแนวคิด V1 public faculty read service
- ตรวจ compatibility ถ้างานเกี่ยวกับ V1

ข้อควรระวัง:

- งาน V2 production API ใหม่ไม่ควรไปพัฒนาหลักในโฟลเดอร์นี้
- ถ้าเห็นไฟล์ V1 ถูกลบ/ย้ายใน working tree โดยไม่ได้ตั้งใจ อย่า stage รวมกับงาน V2 จนกว่าจะรู้ว่าเป็น scope ของการ์ด
- ถ้าการ์ดไม่ได้เกี่ยวกับ V1 compatibility ให้หลีกเลี่ยงการแก้ส่วนนี้

## โฟลเดอร์ไหนควรแตะตามประเภทการ์ด

| ประเภทงาน | โฟลเดอร์ที่มักแตะ | โฟลเดอร์ที่ต้องอ่านประกอบ |
|---|---|---|
| Public API | `backend/v2/query/`, `infra/v2/`, `scripts/`, `evidence/v2/` | `database/`, `docs/v2/team-handbook/02-database-guide.md` |
| Admin API/Auth | `backend/v2/`, `infra/v2/`, `scripts/`, `evidence/v2/` | `database/`, `docs/v2/team-handbook/03-aws-access-and-setup.md` |
| Public UI | `frontend/`, `docs/`, `evidence/v2/` | API issue card และ API docs |
| Admin UI | `frontend/`, `docs/`, `evidence/v2/` | Cognito/admin API docs |
| Database/Migration | `database/`, `data/v2/`, `scripts/`, `evidence/v2/` | mapping docs และ database guide |
| Documentation/Final Demo | `docs/`, `evidence/`, `README.md` | ทุก issue ที่เกี่ยวข้อง |

## วิธีเริ่มทำงานจาก Issue Card

ตัวอย่างถ้าได้รับ #66:

1. สร้าง branch `CS361-66`
2. อ่าน `docs/v2/issues/66-build-work-item-list-search-filter-api.md`
3. อ่าน `docs/v2/team-handbook/02-database-guide.md`
4. อ่าน pattern #64 ใน `backend/v2/query/`
5. เพิ่ม API route ใน backend/infra ตามการ์ด
6. เพิ่ม test และ smoke script ถ้าจำเป็น
7. deploy ไป AWS dev stack
8. รัน smoke test กับ API Gateway จริง
9. เก็บหลักฐานใน `evidence/v2/work-item-list-api/`
10. tick checklist ใน issue card docs
11. commit/push branch
12. comment หลักฐานใน GitHub issue

## สิ่งที่ห้าม commit

ห้าม commit สิ่งเหล่านี้:

- AWS Access Key ID
- AWS Secret Access Key
- session token
- database password
- secret value จาก Secrets Manager
- `.env` ที่มี secret
- screenshot ที่เห็น secret
- private S3 object ที่ไม่ได้ตั้งใจให้เปิดเผย
- dump ฐานข้อมูลจริงที่มีข้อมูลอ่อนไหว

ถ้าไม่แน่ใจ ให้ใส่ placeholder เช่น:

```text
<account-id>
<secret-arn>
<db-password>
<api-base-url>
```

## เกณฑ์งานเสร็จของ V2

การ์ด V2 จะพร้อมปิดเมื่อมีอย่างน้อย:

- implementation ตรงตาม acceptance criteria
- test ผ่านตามประเภทงาน
- ถ้าเป็น production API/Admin/UI ต้องมีหลักฐานจาก AWS จริง
- docs ที่เกี่ยวข้องอัปเดตแล้ว
- evidence file หรือ GitHub comment มีหลักฐานครบ
- ไม่มี secret ถูก commit
- commit ถูก push แล้ว

ถ้างานยังเป็น local/mock อยู่ ให้เขียนสถานะให้ชัดว่าเป็น prototype หรือยังไม่พร้อมปิด production card
