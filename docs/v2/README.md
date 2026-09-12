# V2 Documentation Index

เอกสารชุดนี้เป็น baseline สำหรับ **V2 - Faculty Output Repository** ของโปรเจกต์ CS361

V2 มีเป้าหมายเพื่อยกระบบจาก V1 public read-only faculty information service ไปเป็น repository กลางที่จัดเก็บผลงานและภาระงานอาจารย์แบบมีโครงสร้าง รองรับหลายปีการศึกษา และรองรับการค้นหา/กรอง/เรียกดูรายละเอียดตามเงื่อนไข

---

## Current V2 Baseline

| Artifact | Purpose |
|---|---|
| [V2_Central_Design.md](./V2_Central_Design.md) | เอกสาร freeze หลักของ Issue #46: scope, architecture, contracts, routes, entities, V1 compatibility |
| [erd.md](./erd.md) | ERD และ relationship baseline ของ V2 repository สำหรับ Issue #47 |
| [data-contract.md](./data-contract.md) | data dictionary และ query/data contract ขั้นต้นของ schema |
| [schema-decisions.md](./schema-decisions.md) | design decisions สำคัญของ relational schema |
| [v2-repository.dbml](./v2-repository.dbml) | DBML script สำหรับ paste เข้า dbdiagram.io |
| [v2-aws-service-architecture.png](./v2-aws-service-architecture.png) | Architecture diagram แบบ AWS service-icon style |
| [v2-full-architecture-clean.png](./v2-full-architecture-clean.png) | Architecture diagram เวอร์ชัน clean/readable |

---

## Frozen Decisions From Issue #46

- V2 คือ **Managed Multi-year Faculty Output Repository**
- Aurora PostgreSQL Serverless v2 เป็น managed repository หลัก
- Lambda access ฐานข้อมูลผ่าน RDS Data API
- S3 ใช้สำหรับ source landing, archive, evidence metadata/reference, exports และ public-serving projection
- Cognito ใช้เฉพาะ Admin pilot authentication
- Public data ต้อง enforce ที่ backend/API ไม่ใช่แค่ซ่อนที่ frontend
- Visibility baseline คือ `PUBLIC`, `INTERNAL`, `RESTRICTED`
- `work_item` เป็นแกนกลางของผลงาน/ภาระงาน
- `faculty_work_item` ใช้รองรับผลงานที่มีอาจารย์หลายคนและ contribution ต่างกัน
- `academic_period` และ `evaluation_period` เป็นคนละ concept
- V1 routes และ `/api/v1` contract ต้องไม่พัง
- CloudFront, OpenSearch, RDS Proxy, ECS/EKS เป็น deferred/non-core สำหรับ V2

---

## Issue Cards

| Issue | File |
|---|---|
| #46 Freeze Scope, Architecture & Interface Contracts | [issues/46-freeze-v2-scope-architecture-interface-contracts.md](./issues/46-freeze-v2-scope-architecture-interface-contracts.md) |
| #47 Design Relational Schema & SQL Migration | [issues/47-design-relational-schema-and-sql-migration.md](./issues/47-design-relational-schema-and-sql-migration.md) |
| #48 Provision Aurora / Data API / Secret / IAM | [issues/48-provision-aurora-data-api-secret-iam.md](./issues/48-provision-aurora-data-api-secret-iam.md) |
| #49 Define V1 to V2 Data Mapping | [issues/49-define-v1-to-v2-data-mapping.md](./issues/49-define-v1-to-v2-data-mapping.md) |
| #50 Prepare Multi-Year Demo Dataset | [issues/50-prepare-multi-year-demo-dataset.md](./issues/50-prepare-multi-year-demo-dataset.md) |

---

## How To Use This Folder

สำหรับเริ่มงาน V2 ให้ใช้ลำดับนี้:

1. อ่าน [V2_Central_Design.md](./V2_Central_Design.md) เพื่อเข้าใจ scope และ contracts ที่ freeze แล้ว
2. อ่าน [erd.md](./erd.md), [data-contract.md](./data-contract.md), และ [schema-decisions.md](./schema-decisions.md) ก่อนเริ่มงาน database/API
3. ใช้ [v2-aws-service-architecture.png](./v2-aws-service-architecture.png) ในรายงานหรือ slide เพื่ออธิบาย architecture
4. เริ่ม implementation planning จาก issue #48 เป็นต้นไปหลัง schema baseline ผ่าน review
5. ถ้างานถัดไปต้องเปลี่ยนชื่อ entity, route, visibility rule หรือ V1 compatibility rule ให้เปิด decision/update แยกก่อนแก้

---

## Database Baseline

| Artifact | Purpose |
|---|---|
| [../../database/README.md](../../database/README.md) | วิธี review และลำดับการรัน SQL baseline |
| [../../database/migrations/001_base.sql](../../database/migrations/001_base.sql) | SQL migration baseline สำหรับ Aurora PostgreSQL |
| [../../database/seeds/001_master_data.sql](../../database/seeds/001_master_data.sql) | seed master data สำหรับ `work_category` และ `work_type` |

---

## V2 Boundary Reminder

V2 ทำ repository foundation และ Admin pilot

V2 ยังไม่ทำ:

- faculty self-service
- reviewer workflow
- approval process
- official workload scoring
- official annual report generation
- full multi-role workspace

รายการเหล่านี้เป็นทิศทางของ V3/V4/V7 ไม่ใช่ blocker ของ V2
