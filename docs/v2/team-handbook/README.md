# V2 Team Handbook

เอกสารชุดนี้เป็นคู่มือกลางสำหรับทีม CS361 V2 - Faculty Output Repository อ่านเพื่อเข้าใจภาพรวมระบบ, ฐานข้อมูล, AWS resources, วิธี setup, วิธีทำ issue card, วิธีทดสอบ และวิธีเก็บหลักฐานก่อนปิดงาน

ถ้าเพิ่งเข้ามาทำงานต่อ ให้เริ่มอ่านตามลำดับนี้:

1. [01-system-overview.md](./01-system-overview.md) - เข้าใจโจทย์ V1/V2, สิ่งที่ต้องส่ง, architecture และสถานะปัจจุบัน
2. [02-database-guide.md](./02-database-guide.md) - เข้าใจ Aurora database, ตาราง, attributes, ตัวอย่างข้อมูล และวิธีดูข้อมูล
3. [03-aws-access-and-setup.md](./03-aws-access-and-setup.md) - วิธี setup AWS CLI, ดู resources, ใช้ stack outputs, ระวัง secret/access key
4. [04-development-workflow-and-issue-cards.md](./04-development-workflow-and-issue-cards.md) - วิธีสร้าง branch, flow ทำการ์ด, dependency, สถานะ issue cards
5. [05-testing-verification-and-evidence.md](./05-testing-verification-and-evidence.md) - วิธี test, smoke test, เช็ค CloudWatch/API/DB และเขียน evidence ปิดการ์ด

## Current Short Status

V1 เสร็จเป็น public read-only faculty information service แล้ว ใช้ frontend Next.js + API route/Lambda style เดิม + S3 serving data เป็นหลัก

V2 ตอนนี้มีฐานสำคัญแล้ว:

- Scope/architecture/interface contracts ของ V2 freeze แล้ว
- Relational schema และ DBML/ERD พร้อมแล้ว
- Aurora PostgreSQL/Data API/Secrets/IAM/S3/CloudWatch foundation deploy แล้ว
- V1 to V2 mapping พร้อมแล้ว
- Multi-year demo dataset พร้อมแล้ว
- Master Data API #64 deploy แล้วจริงบน AWS และ smoke test ผ่าน

V2 ที่ยังต้องทำต่อ:

- Public Work Item APIs: #66, #67, #68
- Public Repository UI: #72, #73, #74, #75
- Admin auth/CRUD/UI: #69, #70, #71, #76, #77, #78, #79
- Migration repeatability + final integration: #80, #81

## Golden Rule For V2 Implementation

การ์ด V2 implementation ตั้งแต่ #64 และ #66-#81 ต้องทำเป็นงานจริงบน AWS-connected environment ไม่ใช่ mock/local-only:

```text
Public/API read path:
API Gateway -> Lambda -> RDS Data API -> Aurora PostgreSQL

Admin path:
Cognito -> protected API Gateway -> Admin Lambda -> RDS Data API transaction -> Aurora PostgreSQL
```

Fixture/mock ใช้ได้เฉพาะ automated tests, local fallback หรือช่วย validate contract เท่านั้น ไม่ถือว่าเพียงพอสำหรับปิดการ์ด

## Useful Existing Docs

อ่านคู่มือชุดนี้คู่กับเอกสารหลักเดิม:

- [../README.md](../README.md) - V2 documentation index
- [../V2_Central_Design.md](../V2_Central_Design.md) - freeze scope/architecture/contracts
- [../erd-table-attribute-guide.md](../erd-table-attribute-guide.md) - ตารางและ attribute guide ฉบับละเอียด
- [../data-contract.md](../data-contract.md) - data contract และ query baseline
- [../master-data-api.md](../master-data-api.md) - Master Data API #64 contract/deploy/smoke
- [../../database/migrations/001_base.sql](../../database/migrations/001_base.sql) - schema SQL จริง
- [../../database/seeds/001_master_data.sql](../../database/seeds/001_master_data.sql) - master seed SQL จริง
- [../../../evidence/v2/master-data-api/README.md](../../../evidence/v2/master-data-api/README.md) - evidence ล่าสุดของ #64

## Security Reminder

ห้าม commit หรือส่งใน chat:

- AWS Access Key ID
- AWS Secret Access Key
- AWS session token
- database password
- Secrets Manager secret value
- raw private S3 object หรือข้อมูลภายในที่ไม่ควรเปิด public

ARN, stack name, region, API endpoint, Lambda name และ CloudWatch log group ใช้เป็น operational reference ได้ แต่ถ้าเอกสารจะ public มากขึ้นให้ mask AWS account id เป็น `<account-id>`
